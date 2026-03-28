import type { AnalyzeTeamResponse } from "../types";

type Props = { analysis: AnalyzeTeamResponse | null };

export function DifyStatusCard({ analysis }: Props) {
  if (!analysis) return null;
  const {
    dify_key_configured,
    dify_used,
    dify_error,
    dify_workflow_run_id,
    dify_status,
    dify_output_preview,
  } = analysis;

  if (!dify_key_configured) {
    return (
      <section className="card card-muted card-dify">
        <h2>Dify workflow</h2>
        <p className="small">
          <strong>DIFY_API_KEY</strong> not loaded as a real key (missing, <code>placeholder</code>, or wrong
          file). Put the key in <code>backend/.env</code> and restart the API. The backend loads{" "}
          <code>backend/.env</code> by file path so your terminal cwd does not matter.
        </p>
      </section>
    );
  }

  return (
    <section className="card card-muted card-dify">
      <h2>Dify workflow</h2>
      <ul className="notes">
        <li>
          Used: <strong>{dify_used ? "yes" : "no"}</strong>
        </li>
        {dify_workflow_run_id && <li>Run id: {dify_workflow_run_id}</li>}
        {dify_status && <li>Status: {dify_status}</li>}
        {dify_output_preview && (
          <li>
            Output preview: <pre className="small-pre">{dify_output_preview}</pre>
          </li>
        )}
        {dify_error && <li className="error-text">Error: {dify_error}</li>}
      </ul>
    </section>
  );
}
