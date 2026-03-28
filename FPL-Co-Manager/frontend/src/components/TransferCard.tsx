import type { Recommendation } from "../types";

type Props = { rec: Recommendation | null };

export function TransferCard({ rec }: Props) {
  if (!rec) return null;
  return (
    <section className="card card-transfers">
      <h2>Transfers</h2>
      <p>
        Action: <strong>{rec.transfer_action === "roll" ? "Roll" : "Make a transfer"}</strong>
      </p>
      {rec.transfer_options.length === 0 ? (
        <p className="muted">No ranked swaps this window (or free transfers exhausted).</p>
      ) : (
        <ul className="transfer-list">
          {rec.transfer_options.map((t) => (
            <li key={`${t.player_out_id}-${t.player_in_id}`}>
              <strong>
                {t.player_out_name} → {t.player_in_name}
              </strong>{" "}
              ({t.player_in_team}) · gain ~{t.projected_gain.toFixed(2)} · {t.reason}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
