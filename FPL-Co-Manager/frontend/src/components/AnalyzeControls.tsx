type Props = {
  onAnalyze: () => void;
  disabled: boolean;
  useMemory: boolean;
  setUseMemory: (v: boolean) => void;
};

export function AnalyzeControls({ onAnalyze, disabled, useMemory, setUseMemory }: Props) {
  return (
    <section className="card card-step">
      <div className="card-head">
        <span className="step-pill" aria-hidden>
          2
        </span>
        <h2>Analyze</h2>
      </div>
      <label className="checkbox">
        <input type="checkbox" checked={useMemory} onChange={(e) => setUseMemory(e.target.checked)} />
        <span>Use prior session memory (show previous summary)</span>
      </label>
      <div className="actions">
        <button type="button" className="primary" onClick={onAnalyze} disabled={disabled}>
          Analyze team
        </button>
      </div>
    </section>
  );
}
