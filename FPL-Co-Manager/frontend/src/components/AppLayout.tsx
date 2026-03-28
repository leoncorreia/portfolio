import type { ReactNode } from "react";

type Props = { children: ReactNode };

export function AppLayout({ children }: Props) {
  return (
    <div className="app-root">
      <header className="hero">
        <div className="hero-inner">
          <p className="hero-eyebrow">Fantasy Premier League</p>
          <h1>FPL AI Co-Manager</h1>
          <p className="tagline">
            Import your squad, optimize lineup and transfers, and read AI-backed explanations — with session
            memory and optional Dify + HydraDB.
          </p>
        </div>
      </header>
      <div className="layout">
        <main className="main">{children}</main>
        <footer className="footer">
          <span>Deterministic core · SQLite · optional HydraDB · GMI + Kimi · Dify workflow</span>
        </footer>
      </div>
    </div>
  );
}
