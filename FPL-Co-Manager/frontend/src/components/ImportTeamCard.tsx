import type { RiskProfile } from "../types";

type Props = {
  teamId: string;
  setTeamId: (v: string) => void;
  freeTransfers: number;
  setFreeTransfers: (v: number) => void;
  bank: string;
  setBank: (v: string) => void;
  risk: RiskProfile;
  setRisk: (v: RiskProfile) => void;
  onImport: () => void;
  onDemo: () => void;
  disabled: boolean;
};

export function ImportTeamCard({
  teamId,
  setTeamId,
  freeTransfers,
  setFreeTransfers,
  bank,
  setBank,
  risk,
  setRisk,
  onImport,
  onDemo,
  disabled,
}: Props) {
  return (
    <section className="card card-step">
      <div className="card-head">
        <span className="step-pill" aria-hidden>
          1
        </span>
        <h2>Import team</h2>
      </div>
      <label className="field">
        <span>FPL team ID</span>
        <input
          type="text"
          inputMode="numeric"
          value={teamId}
          onChange={(e) => setTeamId(e.target.value)}
          placeholder="e.g. 123456"
        />
      </label>
      <div className="row">
        <label className="field">
          <span>Free transfers</span>
          <input
            type="number"
            min={0}
            max={5}
            value={freeTransfers}
            onChange={(e) => setFreeTransfers(Number(e.target.value))}
          />
        </label>
        <label className="field">
          <span>Bank (£m)</span>
          <input type="text" value={bank} onChange={(e) => setBank(e.target.value)} placeholder="0.0" />
        </label>
      </div>
      <label className="field">
        <span>Risk profile</span>
        <select value={risk} onChange={(e) => setRisk(e.target.value as RiskProfile)}>
          <option value="safe">Safe</option>
          <option value="balanced">Balanced</option>
          <option value="aggressive">Aggressive</option>
        </select>
      </label>
      <div className="actions">
        <button type="button" className="primary" onClick={onImport} disabled={disabled}>
          Import team
        </button>
        <button type="button" className="secondary" onClick={onDemo} disabled={disabled}>
          Demo team ID
        </button>
      </div>
    </section>
  );
}
