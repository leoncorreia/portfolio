import type { Player, Recommendation } from "../types";

type Props = {
  rec: Recommendation | null;
  playersById: Map<number, Player>;
};

export function LineupCard({ rec, playersById }: Props) {
  if (!rec) return null;
  const label = (id: number) => playersById.get(id)?.web_name ?? `#${id}`;
  return (
    <section className="card card-lineup">
      <h2>Lineup</h2>
      <h3>Starting XI</h3>
      <ol className="lineup">
        {rec.starting_xi.map((id) => (
          <li key={id}>
            {label(id)}
            {id === rec.captain ? " (C)" : ""}
            {id === rec.vice_captain ? " (VC)" : ""}
          </li>
        ))}
      </ol>
      <h3>Bench order</h3>
      <ol className="lineup">
        {rec.bench_order.map((id) => (
          <li key={id}>{label(id)}</li>
        ))}
      </ol>
      <p className="small">
        Captain: <strong>{rec.captain != null ? label(rec.captain) : "—"}</strong> · Vice:{" "}
        <strong>{rec.vice_captain != null ? label(rec.vice_captain) : "—"}</strong>
      </p>
    </section>
  );
}
