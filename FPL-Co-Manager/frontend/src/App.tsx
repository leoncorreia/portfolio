import { useCallback, useEffect, useMemo, useState } from "react";
import { AnalyzeControls } from "./components/AnalyzeControls";
import { AppLayout } from "./components/AppLayout";
import { ErrorBanner } from "./components/ErrorBanner";
import { DifyStatusCard } from "./components/DifyStatusCard";
import { ImageUploadPlaceholder } from "./components/ImageUploadPlaceholder";
import { ImportTeamCard } from "./components/ImportTeamCard";
import { ImportedTeamView } from "./components/ImportedTeamView";
import { LineupCard } from "./components/LineupCard";
import { LoadingOverlay } from "./components/LoadingOverlay";
import { ManualSquadPanel } from "./components/ManualSquadPanel";
import { MemoryCard } from "./components/MemoryCard";
import { RecommendationSummaryCard } from "./components/RecommendationSummaryCard";
import { TransferCard } from "./components/TransferCard";
import { useStableUserId } from "./hooks/useStableUserId";
import {
  analyzeTeam,
  getDemoHints,
  getMemory,
  importTeam,
  isProductionApiUrlMissing,
} from "./services/api";
import type {
  AnalyzeTeamResponse,
  MemoryRecordOut,
  Player,
  Recommendation,
  RiskProfile,
  Squad,
} from "./types";

export default function App() {
  const userId = useStableUserId();
  const [teamId, setTeamId] = useState("");
  const [freeTransfers, setFreeTransfers] = useState(1);
  const [bank, setBank] = useState("0.0");
  const [risk, setRisk] = useState<RiskProfile>("balanced");

  const [squad, setSquad] = useState<Squad | null>(null);
  const [managerName, setManagerName] = useState<string | undefined>();
  const [teamName, setTeamName] = useState<string | undefined>();
  const [importNotes, setImportNotes] = useState<string[]>([]);

  const [analysis, setAnalysis] = useState<AnalyzeTeamResponse | null>(null);
  const [memoryRecord, setMemoryRecord] = useState<MemoryRecordOut | null>(null);

  const [loading, setLoading] = useState(false);
  const [loadingLabel, setLoadingLabel] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [useMemory, setUseMemory] = useState(true);

  const playersById = useMemo(() => {
    const m = new Map<number, Player>();
    squad?.players.forEach((p) => m.set(p.id, p));
    return m;
  }, [squad]);

  const rec: Recommendation | null = analysis?.recommendation ?? null;

  const refreshMemory = useCallback(async () => {
    try {
      const m = await getMemory(userId);
      setMemoryRecord(m as MemoryRecordOut | null);
    } catch {
      setMemoryRecord(null);
    }
  }, [userId]);

  useEffect(() => {
    void refreshMemory();
  }, [refreshMemory]);

  async function handleImport() {
    setError(null);
    const id = parseInt(teamId, 10);
    if (Number.isNaN(id)) {
      setError("Enter a numeric team ID.");
      return;
    }
    const bankVal = parseFloat(bank);
    if (Number.isNaN(bankVal) || bankVal < 0) {
      setError("Bank must be a non-negative number.");
      return;
    }
    setLoading(true);
    setLoadingLabel("Importing from FPL…");
    try {
      const res = await importTeam({
        team_id: id,
        free_transfers: freeTransfers,
        bank: bankVal,
        risk_profile: risk,
      });
      setSquad(res.squad);
      setManagerName(res.manager_name);
      setTeamName(res.team_name);
      setImportNotes(res.import_notes);
      setAnalysis(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Import failed");
    } finally {
      setLoading(false);
    }
  }

  async function handleDemo() {
    setError(null);
    setLoading(true);
    setLoadingLabel("Loading demo hint…");
    try {
      const hints = await getDemoHints();
      setTeamId(String(hints.sample_team_id));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Demo hint failed");
    } finally {
      setLoading(false);
    }
  }

  async function handleAnalyze() {
    if (!squad) {
      setError("Import or load a squad first.");
      return;
    }
    setError(null);
    setLoading(true);
    setLoadingLabel("Analyzing squad…");
    try {
      const res = await analyzeTeam({ user_id: userId, squad, use_memory: useMemory });
      setAnalysis(res);
      await refreshMemory();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Analysis failed");
    } finally {
      setLoading(false);
    }
  }

  function applyManualSquad(s: Squad) {
    setSquad(s);
    setManagerName(undefined);
    setTeamName(undefined);
    setImportNotes(["Loaded from manual JSON."]);
    setAnalysis(null);
    setError(null);
  }

  const lastCaptainName =
    memoryRecord?.captain_id != null
      ? playersById.get(memoryRecord.captain_id)?.web_name ?? `Player #${memoryRecord.captain_id}`
      : undefined;

  return (
    <AppLayout>
      <ErrorBanner
        message={
          isProductionApiUrlMissing()
            ? "This deployment has no VITE_API_URL. In Vercel → Project → Settings → Environment Variables, set VITE_API_URL to your Render API origin (https://….onrender.com, no trailing slash), save, then Redeploy."
            : null
        }
      />
      <ErrorBanner message={error} onDismiss={() => setError(null)} />
      <LoadingOverlay show={loading} label={loadingLabel} />

      <ImportTeamCard
        teamId={teamId}
        setTeamId={setTeamId}
        freeTransfers={freeTransfers}
        setFreeTransfers={setFreeTransfers}
        bank={bank}
        setBank={setBank}
        risk={risk}
        setRisk={setRisk}
        onImport={handleImport}
        onDemo={handleDemo}
        disabled={loading}
      />

      <ImportedTeamView squad={squad} managerName={managerName} teamName={teamName} notes={importNotes} />

      <AnalyzeControls
        onAnalyze={handleAnalyze}
        disabled={loading || !squad}
        useMemory={useMemory}
        setUseMemory={setUseMemory}
      />

      <MemoryCard
        memoryUsed={analysis?.memory_used ?? false}
        previousSummary={analysis?.previous_summary ?? null}
        lastCaptain={lastCaptainName ?? null}
        lastTransfer={memoryRecord?.transfer_action ?? null}
        previousFromHydradb={analysis?.previous_from_hydradb}
      />

      <DifyStatusCard analysis={analysis} />

      <RecommendationSummaryCard rec={rec} />
      <LineupCard rec={rec} playersById={playersById} />
      <TransferCard rec={rec} />

      {rec?.explanation && (
        <section className="card card-explain">
          <h2>Explanation</h2>
          <pre className="explain">{rec.explanation}</pre>
        </section>
      )}

      <ManualSquadPanel onApply={applyManualSquad} />
      <ImageUploadPlaceholder />
    </AppLayout>
  );
}
