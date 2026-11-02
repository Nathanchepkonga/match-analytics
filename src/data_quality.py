"""Data-quality diagnostics for tracking, event, and phase inputs."""

from typing import Any, Dict

import numpy as np
import pandas as pd


def _safe_rate(numerator: int, denominator: int) -> float:
    return float(numerator / denominator) if denominator else 0.0


def tracking_quality(dataset: Any) -> Dict[str, Any]:
    """Return compact, display-ready diagnostics for a Kloppy tracking dataset."""
    frames = list(getattr(dataset, "frames", []) or [])
    if not frames:
        return {
            "frames": 0,
            "duration_seconds": 0.0,
            "timestamp_gaps": 0,
            "max_gap_seconds": 0.0,
            "player_observations": 0,
            "detected_observations": 0,
            "detection_rate": 0.0,
            "status": "empty",
        }

    timestamps = np.asarray([getattr(frame, "timestamp", np.nan) for frame in frames])
    timestamps = pd.to_numeric(pd.Series(timestamps), errors="coerce").dropna().to_numpy()
    gaps = np.diff(timestamps) if len(timestamps) > 1 else np.array([])
    positive_gaps = gaps[gaps > 0]

    observations = 0
    detected = 0
    for frame in frames:
        for player_data in getattr(frame, "players_data", {}).values():
            observations += 1
            if getattr(player_data, "coordinates", None) is not None:
                detected += 1

    max_gap = float(positive_gaps.max()) if len(positive_gaps) else 0.0
    gap_count = int((positive_gaps > 0.2).sum()) if len(positive_gaps) else 0
    detection_rate = _safe_rate(detected, observations)
    status = "good" if detection_rate >= 0.95 and gap_count == 0 else "review"

    return {
        "frames": len(frames),
        "duration_seconds": float(timestamps[-1] - timestamps[0]) if len(timestamps) > 1 else 0.0,
        "timestamp_gaps": gap_count,
        "max_gap_seconds": max_gap,
        "player_observations": observations,
        "detected_observations": detected,
        "detection_rate": detection_rate,
        "status": status,
    }


def dataframe_quality(df: pd.DataFrame, required_columns=None) -> Dict[str, Any]:
    """Validate a tabular artifact without raising on incomplete external data."""
    required_columns = list(required_columns or [])
    missing = [column for column in required_columns if column not in df.columns]
    duplicate_rows = int(df.duplicated().sum()) if not df.empty else 0
    missing_cells = int(df.isna().sum().sum()) if not df.empty else 0
    total_cells = int(df.shape[0] * df.shape[1])

    if missing:
        status = "invalid"
    elif df.empty:
        status = "empty"
    elif duplicate_rows or missing_cells:
        status = "review"
    else:
        status = "good"

    return {
        "rows": int(len(df)),
        "columns": int(len(df.columns)),
        "missing_columns": missing,
        "duplicate_rows": duplicate_rows,
        "missing_cells": missing_cells,
        "missing_rate": _safe_rate(missing_cells, total_cells),
        "status": status,
    }


def match_quality_summary(dataset: Any, events: pd.DataFrame, phases: pd.DataFrame) -> Dict[str, Any]:
    """Combine tracking, event, and phase diagnostics for a match dashboard."""
    return {
        "tracking": tracking_quality(dataset),
        "events": dataframe_quality(events, ["event_type"]),
        "phases": dataframe_quality(phases),
    }
