"use client";

import { motion } from "framer-motion";
import Link from "next/link";

import { BackendStatus } from "@/components/backend-status";
import { DISCLAIMER } from "@/lib/constants";

const branches = [
  { label: "Applied AI", className: "landing-branch branch-blue" },
  { label: "Robotics", className: "landing-branch branch-violet" },
  { label: "Startup", className: "landing-branch branch-amber" },
];

export default function Home() {
  return (
    <main className="landing-shell">
      <a className="skip-link" href="#landing-content">
        Skip to main content
      </a>
      <div className="star-field" aria-hidden="true" />
      <nav className="landing-nav" aria-label="Landing navigation">
        <div className="brand">
          <span className="brand-mark" aria-hidden="true">
            M
          </span>
          Multiverse
        </div>
        <Link href="/settings">System status</Link>
      </nav>

      <section
        id="landing-content"
        className="landing-hero"
        aria-labelledby="page-title"
      >
        <motion.div
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.55 }}
          className="landing-copy"
        >
          <p className="eyebrow">
            A strategy game about the lives you might live
          </p>
          <h1 id="page-title">
            One choice.
            <span>Three possible futures.</span>
          </h1>
          <p className="lede">
            Build fictional alternate lives, make consequential decisions, and
            meet the future selves shaped by each path.
          </p>
          <div className="hero-actions">
            <Link className="button button-primary" href="/onboarding">
              Enter the Multiverse
              <span aria-hidden="true">→</span>
            </Link>
            <Link className="button button-secondary" href="/stories">
              View saved stories
            </Link>
          </div>
          <BackendStatus />
        </motion.div>

        <div
          className="landing-visual"
          aria-label="Three fictional futures branching from now"
        >
          <div className="reality-core">
            <span>NOW</span>
            <strong>2026</strong>
          </div>
          <div className="orbit orbit-one" aria-hidden="true" />
          <div className="orbit orbit-two" aria-hidden="true" />
          {branches.map((branch, index) => (
            <motion.div
              key={branch.label}
              className={branch.className}
              initial={{ opacity: 0, scale: 0.88 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.2 + index * 0.12 }}
            >
              <span>Universe {String.fromCharCode(65 + index)}</span>
              <strong>{branch.label}</strong>
            </motion.div>
          ))}
        </div>
      </section>

      <footer className="landing-footer">
        <span className="disclaimer-dot" aria-hidden="true" />
        {DISCLAIMER}
      </footer>
    </main>
  );
}
