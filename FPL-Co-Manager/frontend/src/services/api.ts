import type { AnalyzeTeamResponse, MemoryRecordOut, Squad, TeamImportResponse } from "../types";

const JSON_HEADERS = { "Content-Type": "application/json" };

async function handle<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const j = await res.json();
      detail = typeof j.detail === "string" ? j.detail : JSON.stringify(j.detail ?? j);
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  return res.json() as Promise<T>;
}

export async function importTeam(body: {
  team_id: number;
  free_transfers: number;
  bank: number;
  risk_profile: string;
}): Promise<TeamImportResponse> {
  const res = await fetch("/api/import-team", {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify(body),
  });
  return handle<TeamImportResponse>(res);
}

export async function analyzeTeam(body: {
  user_id: string;
  squad: Squad;
  use_memory: boolean;
}): Promise<AnalyzeTeamResponse> {
  const res = await fetch("/api/analyze", {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify(body),
  });
  return handle<AnalyzeTeamResponse>(res);
}

export async function getMemory(userId: string): Promise<MemoryRecordOut | null> {
  const res = await fetch(`/api/memory/${encodeURIComponent(userId)}`);
  if (res.status === 404) return null;
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const j: unknown = await res.json();
      if (typeof j === "object" && j && "detail" in j) {
        detail = String((j as { detail: unknown }).detail);
      }
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  const data: unknown = await res.json();
  if (data === null) return null;
  return data as MemoryRecordOut;
}

export async function getDemoHints(): Promise<{ sample_team_id: number; note: string }> {
  const res = await fetch("/api/demo-hints");
  return handle(res);
}

export async function parseImage(file: File): Promise<unknown> {
  const fd = new FormData();
  fd.append("file", file);
  const res = await fetch("/api/parse-image", { method: "POST", body: fd });
  return handle(res);
}
