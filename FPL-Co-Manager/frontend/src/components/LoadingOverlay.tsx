type Props = { show: boolean; label?: string };

export function LoadingOverlay({ show, label = "Working…" }: Props) {
  if (!show) return null;
  return (
    <div className="overlay" aria-busy="true" aria-live="polite">
      <div className="overlay-panel">
        <div className="spinner" />
        <p className="overlay-label">{label}</p>
      </div>
    </div>
  );
}
