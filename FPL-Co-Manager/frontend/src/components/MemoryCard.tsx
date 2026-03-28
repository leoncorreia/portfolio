type Props = {
  memoryUsed: boolean;
  previousSummary: string | null;
  lastCaptain?: string | null;
  lastTransfer?: string | null;
  previousFromHydradb?: boolean;
};

export function MemoryCard({
  memoryUsed,
  previousSummary,
  lastCaptain,
  lastTransfer,
  previousFromHydradb,
}: Props) {
  return (
    <section className="card card-memory">
      <h2>Memory</h2>
      {!memoryUsed && <p className="muted">No prior recommendation for this browser profile.</p>}
      {memoryUsed && previousSummary && (
        <p>
          <strong>Previous summary:</strong> {previousSummary}
          <span className="small">{previousFromHydradb ? " (HydraDB)" : " (local DB)"}</span>
        </p>
      )}
      {lastCaptain && (
        <p className="small">
          Last captain (stored): <strong>{lastCaptain}</strong>
        </p>
      )}
      {lastTransfer && (
        <p className="small">
          Last transfer stance: <strong>{lastTransfer}</strong>
        </p>
      )}
    </section>
  );
}
