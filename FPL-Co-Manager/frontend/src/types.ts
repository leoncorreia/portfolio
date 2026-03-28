export type PositionCode = "GKP" | "DEF" | "MID" | "FWD";
export type RiskProfile = "safe" | "balanced" | "aggressive";
export type Confidence = "low" | "medium" | "high";
export type TransferAction = "roll" | "transfer";

export interface Player {
  id: number;
  web_name: string;
  full_name?: string | null;
  team_id: number;
  team_short: string;
  position: PositionCode;
  price: number;
  total_points: number;
  form: number;
  minutes: number;
  points_per_game: number;
  ict_index: number;
  selected_by_percent: number;
  injury_risk: number;
  expected_minutes_next: number;
  fixture_score: number;
  ceiling: number;
  news: string;
  status: string;
}

export interface Squad {
  players: Player[];
  free_transfers: number;
  bank: number;
  risk_profile: RiskProfile;
  gameweek?: number | null;
  team_id?: number | null;
}

export interface TransferOption {
  player_out_id: number;
  player_out_name: string;
  player_in_id: number;
  player_in_name: string;
  player_in_team: string;
  cost_delta: number;
  projected_gain: number;
  reason: string;
}

export interface Recommendation {
  summary: string;
  starting_xi: number[];
  bench_order: number[];
  captain: number | null;
  vice_captain: number | null;
  transfer_action: TransferAction;
  transfer_options: TransferOption[];
  explanation: string;
  confidence: Confidence;
  formation: string;
}

export interface TeamImportResponse {
  manager_name: string;
  team_name: string;
  squad: Squad;
  import_notes: string[];
}

export interface AnalyzeTeamResponse {
  recommendation: Recommendation;
  memory_used: boolean;
  previous_summary: string | null;
  previous_from_hydradb: boolean;
  dify_key_configured: boolean;
  dify_used: boolean;
  dify_error: string | null;
  dify_workflow_run_id: string | null;
  dify_status: string | null;
  dify_output_preview: string | null;
}

export interface MemoryRecordOut {
  id: number;
  user_id: string;
  created_at: string;
  squad_snapshot: Record<string, unknown>;
  recommendation: Record<string, unknown>;
  captain_id: number | null;
  transfer_action: string | null;
  transfer_options_json: Record<string, unknown>[];
  notes: string;
}
