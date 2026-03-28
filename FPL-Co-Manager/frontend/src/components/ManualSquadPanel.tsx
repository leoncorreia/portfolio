import { useState } from "react";
import type { Squad } from "../types";

type Props = {
  onApply: (squad: Squad) => void;
};

export function ManualSquadPanel({ onApply }: Props) {
  const [json, setJson] = useState("");
  const [err, setErr] = useState<string | null>(null);

  function apply() {
    setErr(null);
    try {
      const parsed = JSON.parse(json) as Squad;
      if (!parsed.players || !Array.isArray(parsed.players)) {
        throw new Error("JSON must include a players array.");
      }
      onApply({
        ...parsed,
        free_transfers: parsed.free_transfers ?? 1,
        bank: parsed.bank ?? 0,
        risk_profile: parsed.risk_profile ?? "balanced",
      });
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Invalid JSON");
    }
  }

  return (
    <section className="card card-manual">
      <h2>Manual squad (fallback)</h2>
      <p className="small">
        Paste a <code>Squad</code> JSON object (see API schema). Use when import fails.
      </p>
      <textarea
        className="code"
        rows={8}
        value={json}
        onChange={(e) => setJson(e.target.value)}
        placeholder='{"players":[...], "free_transfers":1, "bank":0.5, "risk_profile":"balanced"}'
      />
      {err && <p className="error-text">{err}</p>}
      <button type="button" className="secondary" onClick={apply}>
        Load squad from JSON
      </button>
    </section>
  );
}
