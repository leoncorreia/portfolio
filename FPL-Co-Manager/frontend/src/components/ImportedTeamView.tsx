import type { Squad } from "../types";

type Props = {
  squad: Squad | null;
  managerName?: string;
  teamName?: string;
  notes?: string[];
};

export function ImportedTeamView({ squad, managerName, teamName, notes }: Props) {
  if (!squad) {
    return (
      <section className="card card-muted">
        <h2>Imported squad</h2>
        <p>No squad loaded yet.</p>
      </section>
    );
  }
  return (
    <section className="card card-squad">
      <h2>Imported squad</h2>
      {(managerName || teamName) && (
        <p className="meta">
          {managerName && <strong>{managerName}</strong>}
          {managerName && teamName ? " — " : null}
          {teamName && <span>{teamName}</span>}
        </p>
      )}
      {notes && notes.length > 0 && (
        <ul className="notes">
          {notes.map((n) => (
            <li key={n}>{n}</li>
          ))}
        </ul>
      )}
      <div className="table-wrap">
        <table className="table">
          <thead>
            <tr>
              <th>Player</th>
              <th>Pos</th>
              <th>Club</th>
              <th>£m</th>
              <th>Form</th>
            </tr>
          </thead>
          <tbody>
            {squad.players.map((p) => (
              <tr key={p.id}>
                <td>{p.web_name}</td>
                <td>{p.position}</td>
                <td>{p.team_short}</td>
                <td>{p.price.toFixed(1)}</td>
                <td>{p.form}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
