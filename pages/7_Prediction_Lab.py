"""Prediction, backtesting, and data-quality dashboard."""

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.append(str(Path(__file__).parent.parent))

from src import data_loader, data_quality, prediction, styling
from src.fixture_intel import load_all_fixtures
from src.jackpot_wheel import build_wheel


styling.setup_page("Prediction Lab")


@st.cache_data(show_spinner=False)
def load_prediction_data() -> pd.DataFrame:
    return prediction.load_match_results()


@st.cache_data(show_spinner=False)
def run_backtest(data: pd.DataFrame, min_history: int) -> pd.DataFrame:
    return prediction.rolling_backtest(data, min_history=min_history)


def _probability_table(result):
    outcome = result["outcome"]
    return pd.DataFrame(
        [
            {"Outcome": "Home", "Probability": outcome["H"]},
            {"Outcome": "Draw", "Probability": outcome["D"]},
            {"Outcome": "Away", "Probability": outcome["A"]},
            {"Outcome": "Over 2.5", "Probability": result["over_2_5"]},
            {"Outcome": "Both teams to score", "Probability": result["btts_yes"]},
        ]
    )


def render_prediction_lab(data: pd.DataFrame) -> None:
    st.markdown(
        "<div class='app-header'><div>"
        "<h1 class='app-headline'>Prediction Lab</h1>"
        "<p class='app-subtitle'>Transparent Poisson baselines, chronological backtesting, and calibrated evaluation metrics.</p>"
        "</div></div>",
        unsafe_allow_html=True,
    )

    if data.empty:
        st.error("No compatible football-data CSV files were found in data/football_data.")
        return

    leagues = sorted(data["league"].dropna().unique())
    league = st.sidebar.selectbox("Competition", leagues)
    league_data = data[data["league"] == league].copy()
    teams = sorted(set(league_data["home"]) | set(league_data["away"]))
    if len(teams) < 2:
        st.warning("This competition does not contain enough teams for a prediction.")
        return

    home = st.sidebar.selectbox("Home team", teams)
    away_options = [team for team in teams if team != home]
    away = st.sidebar.selectbox("Away team", away_options)
    history_limit = st.sidebar.slider("Recent matches per team", 5, 50, 20)
    min_history = st.sidebar.slider("Minimum historical matches for backtest", 20, 200, 50)

    result = prediction.predict_match(league_data, home, away, prior_matches=history_limit)
    top_outcome = max(result["outcome"], key=result["outcome"].get)

    st.subheader(f"{home} vs {away}")
    cards = st.columns(4)
    cards[0].metric("Most likely result", {"H": "Home", "D": "Draw", "A": "Away"}[top_outcome])
    cards[1].metric("Most likely score", result["most_likely_score"])
    cards[2].metric("Expected goals", f"{result['expected_home_goals'] + result['expected_away_goals']:.2f}")
    cards[3].metric("Over 2.5", f"{result['over_2_5']:.1%}")

    st.dataframe(
        _probability_table(result).style.format({"Probability": "{:.1%}"}),
        use_container_width=True,
        hide_index=True,
    )
    st.caption("This is a transparent baseline using prior results only. It is not a guaranteed forecast.")

    st.subheader("Chronological backtest")
    backtest = run_backtest(league_data, min_history=min_history)
    summary = prediction.summarize_backtest(backtest)
    metrics = st.columns(4)
    metrics[0].metric("Test matches", summary["matches"])
    metrics[1].metric("Accuracy", f"{summary['accuracy']:.1%}")
    metrics[2].metric("Log loss", f"{summary['log_loss']:.3f}")
    metrics[3].metric("Brier score", f"{summary['brier']:.3f}")
    st.metric("Mean one-unit ROI where odds are available", f"{summary['roi']:.1%}")
    if not backtest.empty:
        st.line_chart(backtest.set_index("date")[["log_loss", "brier"]])
        st.dataframe(backtest.tail(25), use_container_width=True, hide_index=True)


def render_jackpot_wheel() -> None:
    st.subheader("Jackpot wheel")
    fixtures = load_all_fixtures()
    fixtures = [fixture for fixture in fixtures if fixture.analysis and len(fixture.analysis.outcome_estimate) == 3]
    if not fixtures:
        st.info("No fixture-intelligence records with three-way probability estimates are available.")
        return
    slips = st.slider("Number of slips", 1, 50, 5)
    threshold = st.slider("Banker probability threshold", 0.34, 0.70, 0.45, 0.01)
    if st.button("Build wheel", type="primary"):
        wheel = build_wheel(fixtures, num_slips=slips, banker_threshold=threshold)
        st.dataframe(wheel, use_container_width=True, hide_index=True)
        st.caption("Bankers remain fixed; uncertain legs are sampled or exhaustively covered when feasible.")


def render_quality_dashboard() -> None:
    st.subheader("SkillCorner data-quality diagnostics")
    matches = data_loader.get_available_matches()
    selected = st.selectbox("Match to inspect", list(matches), format_func=lambda value: matches[value])
    if not st.button("Load diagnostics", type="primary"):
        st.info("Choose a match and click Load diagnostics. Tracking data may take a moment to download.")
        return

    try:
        with st.spinner("Loading match data and calculating diagnostics..."):
            dataset = data_loader.load_match_data(selected, sample_rate=0.1)
            events = data_loader.load_dynamic_events(selected)
            phases = data_loader.load_phases_of_play(selected)
            summary = data_quality.match_quality_summary(dataset, events, phases)
    except Exception as error:
        st.error(f"Could not load diagnostics: {error}")
        return

    tracking = summary["tracking"]
    columns = st.columns(5)
    columns[0].metric("Frames", f"{tracking['frames']:,}")
    columns[1].metric("Duration", f"{tracking['duration_seconds'] / 60:.1f} min")
    columns[2].metric("Detection rate", f"{tracking['detection_rate']:.1%}")
    columns[3].metric("Timestamp gaps", tracking["timestamp_gaps"])
    columns[4].metric("Status", tracking["status"].title())

    st.dataframe(
        pd.DataFrame(
            [
                {"Artifact": "Tracking", **tracking},
                {"Artifact": "Events", **summary["events"]},
                {"Artifact": "Phases", **summary["phases"]},
            ]
        ),
        use_container_width=True,
        hide_index=True,
    )


def main() -> None:
    styling.load_css()
    data = load_prediction_data()
    tab_prediction, tab_quality, tab_wheel = st.tabs(["Prediction lab", "Data quality", "Jackpot wheel"])
    with tab_prediction:
        render_prediction_lab(data)
    with tab_quality:
        render_quality_dashboard()
    with tab_wheel:
        render_jackpot_wheel()


if __name__ == "__main__":
    main()
