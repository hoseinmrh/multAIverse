import Link from "next/link";
import type { ReactNode } from "react";

import { DISCLAIMER } from "@/lib/constants";

export function AppShell({
  children,
  wide = false,
}: {
  children: ReactNode;
  wide?: boolean;
}) {
  return (
    <div className="app-frame">
      <a className="skip-link" href="#main-content">
        Skip to main content
      </a>
      <header className="topbar">
        <Link className="brand" href="/" aria-label="Multiverse home">
          <span className="brand-mark" aria-hidden="true">
            M
          </span>
          <span>Multiverse</span>
        </Link>
        <nav aria-label="Primary navigation">
          <Link href="/stories">Stories</Link>
          <Link href="/onboarding">New story</Link>
          <Link href="/settings">Settings</Link>
        </nav>
      </header>
      <main
        id="main-content"
        className={wide ? "content-shell content-wide" : "content-shell"}
      >
        {children}
      </main>
      <footer className="app-footer">{DISCLAIMER}</footer>
    </div>
  );
}
