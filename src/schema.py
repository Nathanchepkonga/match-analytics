"""
Author: Tiago Monteiro
Date: 21-12-2025
Schema definitions for data validation and type hinting.
Uses Pydantic for metadata and lightweight TypedDict/Dataclasses for high-frequency tracking frames.
"""

from typing import List, Optional, Dict
from pydantic import BaseModel
from dataclasses import dataclass



class PlayerMetadata(BaseModel):
    player_id: int
    name: str = "Unknown"
    jersey_no: int = 99
    position: Optional[str] = None
    detailed_position: Optional[str] = None
    team_id: int

class TeamMetadata(BaseModel):
    team_id: int
    name: str
    players: List[PlayerMetadata] = []

class MatchMetadata(BaseModel):
    match_id: int
    home_team: TeamMetadata
    away_team: TeamMetadata
    pitch_length: float = 105.0
    pitch_width: float = 68.0





class FixtureForm(BaseModel):
    """Recent form snapshot for one side of a fixture, sourced from public stats sites."""
    results: List[str] = []
    goals_for: Optional[int] = None
    goals_against: Optional[int] = None
    league_position: Optional[int] = None
    points: Optional[int] = None
    note: Optional[str] = None

class FixtureAnalysis(BaseModel):
    """Qualitative tactical read layered on top of the sourced data. Not a statistical model."""
    tactical_read: str
    prediction_lean: str
    outcome_estimate: List[float] = []
    outcome_pick: Optional[str] = None
    confidence_note: Optional[str] = None

class FixtureIntel(BaseModel):
    """Pre-match intelligence for a single fixture, combining external site data with analysis."""
    match_id: str
    kickoff_date: str
    kickoff_time: str
    country: str
    competition: str
    home_team: str
    away_team: str
    home_form: FixtureForm = FixtureForm()
    away_form: FixtureForm = FixtureForm()
    h2h_summary: Optional[str] = None
    key_notes: List[str] = []
    sources: List[str] = []
    confidence: str = "low"
    analysis: Optional[FixtureAnalysis] = None
    external_predictions: Dict[str, str] = {}
    actual_result: Optional[str] = None
    actual_score: Optional[str] = None



@dataclass(slots=True)
class BallData:
    x: float
    y: float
    z: float = 0.0
    is_detected: bool = False

@dataclass(slots=True)
class PlayerTrackingData:
    player_id: int
    x: float
    y: float
    speed: Optional[float] = None
    direction: Optional[float] = None
    
@dataclass(slots=True)
class FrameData:
    frame_id: int
    timestamp: float
    period: int
    ball: Optional[BallData]
    players: List[PlayerTrackingData]
    possession_team_id: Optional[int] = None
    in_possession: bool = False
