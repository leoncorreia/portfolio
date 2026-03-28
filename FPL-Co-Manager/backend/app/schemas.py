"""Pydantic schemas for API requests and responses."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


# --- Core domain ---

PositionCode = Literal["GKP", "DEF", "MID", "FWD"]
RiskProfile = Literal["safe", "balanced", "aggressive"]
Confidence = Literal["low", "medium", "high"]
TransferAction = Literal["roll", "transfer"]


class Player(BaseModel):
    """Normalized player from FPL or manual entry."""

    id: int
    web_name: str
    full_name: str | None = None
    team_id: int  # FPL team (club) id
    team_short: str = ""
    position: PositionCode
    price: float = 0.0  # millions
    total_points: int = 0
    form: float = 0.0  # recent form string parsed to float
    minutes: int = 0  # season minutes
    points_per_game: float = 0.0
    ict_index: float = 0.0
    selected_by_percent: float = 0.0
    # Derived / heuristic fields for scoring
    injury_risk: float = 0.0  # 0 = fit, 1 = high doubt
    expected_minutes_next: float = 90.0  # 0-90 scale
    fixture_score: float = 5.0  # 0-10 easier = higher
    ceiling: float = 5.0  # upside for aggressive mode
    news: str = ""
    status: str = ""  # a = available, d = doubt, etc.


class Squad(BaseModel):
    """User squad (15 players) plus manager context."""

    players: list[Player] = Field(default_factory=list)
    free_transfers: int = 1
    bank: float = 0.0
    risk_profile: RiskProfile = "balanced"
    gameweek: int | None = None
    team_id: int | None = None  # FPL entry id if imported


class TransferOption(BaseModel):
    """Single transfer suggestion: out -> in."""

    player_out_id: int
    player_out_name: str
    player_in_id: int
    player_in_name: str
    player_in_team: str = ""
    cost_delta: float = 0.0  # bank impact after sale/buy
    projected_gain: float = 0.0
    reason: str = ""


class Recommendation(BaseModel):
    summary: str = ""
    starting_xi: list[int] = Field(default_factory=list)  # player ids in slot order
    bench_order: list[int] = Field(default_factory=list)
    captain: int | None = None
    vice_captain: int | None = None
    transfer_action: TransferAction = "roll"
    transfer_options: list[TransferOption] = Field(default_factory=list)
    explanation: str = ""
    confidence: Confidence = "medium"
    formation: str = ""  # e.g. "4-3-3"


# --- Import ---


class TeamImportRequest(BaseModel):
    team_id: int = Field(..., ge=1)
    free_transfers: int = Field(default=1, ge=0, le=5)
    bank: float = Field(default=0.0, ge=0.0)
    risk_profile: RiskProfile = "balanced"


class TeamImportResponse(BaseModel):
    manager_name: str = ""
    team_name: str = ""
    squad: Squad
    import_notes: list[str] = Field(default_factory=list)


# --- Analyze ---


class AnalyzeTeamRequest(BaseModel):
    user_id: str = Field(..., min_length=1)
    squad: Squad
    use_memory: bool = True


class AnalyzeTeamResponse(BaseModel):
    recommendation: Recommendation
    memory_used: bool = False
    previous_summary: str | None = None
    # HydraDB: whether latest prior session was loaded from Hydra (vs SQLite-only)
    previous_from_hydradb: bool = False
    # Dify workflow (orchestration); does not replace deterministic + Kimi body text
    dify_key_configured: bool = False
    dify_used: bool = False
    dify_error: str | None = None
    dify_workflow_run_id: str | None = None
    dify_status: str | None = None
    dify_output_preview: str | None = None


# --- Memory ---


class MemoryRecordOut(BaseModel):
    id: int
    user_id: str
    created_at: str
    squad_snapshot: dict[str, Any]
    recommendation: dict[str, Any]
    captain_id: int | None = None
    transfer_action: str | None = None
    transfer_options_json: list[dict[str, Any]] = Field(default_factory=list)
    notes: str = ""


# --- Image ---


class ParseImageResponse(BaseModel):
    ok: bool = True
    message: str = ""
    parsed_squad: Squad | None = None
    raw_model_output: str | None = None


# --- Compare / sessions (nice-to-have) ---


class CompareSummary(BaseModel):
    last_captain_id: int | None = None
    current_captain_id: int | None = None
    last_transfer_action: str | None = None
    current_transfer_action: str | None = None
    narrative: str = ""


class CompareTeamRequest(BaseModel):
    user_id: str = Field(..., min_length=1)
    squad: Squad
