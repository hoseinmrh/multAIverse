import { BackendStatus } from "@/components/backend-status";

export default function Home() {
  return (
    <main className="page-shell">
      <div className="ambient ambient-one" aria-hidden="true" />
      <div className="ambient ambient-two" aria-hidden="true" />

      <section className="hero" aria-labelledby="page-title">
        <p className="eyebrow">Local-first alternate-life simulator</p>
        <h1 id="page-title">Multiverse</h1>
        <p className="lede">
          Explore the choices, trade-offs, and unexpected turns that could shape
          a fictional version of your future.
        </p>

        <BackendStatus />

        <p className="phase-note">
          Foundation online. Profiles and universe simulation arrive in the next
          development phases.
        </p>
      </section>

      <footer>
        Multiverse creates fictional scenarios for entertainment and reflection.
        Its simulations are not predictions or professional advice.
      </footer>
    </main>
  );
}
