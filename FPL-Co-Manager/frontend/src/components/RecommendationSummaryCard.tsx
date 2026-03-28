import type { Recommendation } from "../types";

type Props = { rec: Recommendation | null };

export function RecommendationSummaryCard({ rec }: Props) {
  if (!rec) return null;
  return (
    <section className="card card-highlight card-summary">
      <h2>Summary</h2>
      <p>{rec.summary}</p>
      <p className="small">
        Confidence: <strong>{rec.confidence}</strong> · Formation: <strong>{rec.formation}</strong>
      </p>
    </section>
  );
}
