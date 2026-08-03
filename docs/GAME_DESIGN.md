# Game Design

## Product promise

Multiverse is a strategy and storytelling game for exploring fictional paths,
not a predictor or professional-advice product. The disclaimer remains visible
where users enter the experience.

## Core loop

The complete loop will let a player choose a profile and scenario, explore
three universes, advance a year, resolve an important choice, inspect its
immediate and delayed consequences, and compare paths after several years.

## Simulation principles

- The deterministic engine owns time, statistics, money, flags, requirements,
  random selection, delayed effects, and snapshots.
- Statistics normally remain between 0 and 100.
- Income is not treated as a direct proxy for happiness.
- High stress can compound into burnout and health penalties.
- Success and failure remain possible across different starting conditions.
- Realistic, Cinematic, Utopian, Dark, and Chaos modes influence event
  selection and tone without bypassing the engine.

## Implemented Phase 3 balance model

All balance values live in `backend/app/services/simulation/balance.py`.
Effects are capped per application, aggregate yearly statistic movement is
capped, positive gains diminish near 100, and every normalized result is
clamped to 0–100. Negative modifiers become stronger during sustained high
stress. A second consecutive extreme-stress year applies a health penalty.

Happiness is a nonlinear weighted calculation. Health, relationships, freedom,
purpose, stability, and a saturating income-security contribution add value;
quadratic stress and burnout subtract it. The small, saturating finance weight
prevents income from dominating happiness.

Annual finances combine momentum-sensitive income growth, a bounded savings
rate influenced by discipline and stress, a startup runway penalty, positive
asset returns, and debt interest. Net worth may be negative; income cannot be.

Career momentum combines relevant skills, reputation/relationship-derived
opportunity, discipline, current level, and recent success. Research momentum
uses impact, stress-adjusted focus, network, research skills, and institutional
support. Startup momentum uses execution, network, capital, market timing,
reputation, team quality, and creativity. Each momentum score becomes a bounded
success probability with nonzero failure and success tails, then receives the
configured simulation-mode modifier.

Delayed consequences carry a trigger offset, probability, description, and a
validated effect payload. The probability is drawn once when due from a stable
seed namespace, and the stored record is marked consumed whether or not it
occurs. Important decisions block time until one valid choice is resolved.

## Phase 4 narrative design

The mock narrative layer turns deterministic state into fictional texture; it
does not decide what the state becomes. It proposes typed effects on choices,
and the simulation engine remains responsible for validation, caps, seeded
probability, and application.

Each seeded path has a distinct narrative vocabulary:

- Applied AI Leader emphasizes technical leadership, model reviews, applied
  research windows, compensation trade-offs, relocation, and sponsorship.
- Robotics Researcher emphasizes field trials, joint laboratory roles, grant
  gaps, authorship, conferences, and prototype failures.
- Startup Founder emphasizes fundraising, runway, co-founder alignment,
  enterprise pilots, production incidents, and the changing founder role.

Shared state-sensitive events cover health and relationships. Very low health
or extreme stress prioritizes health/crisis material; negative net worth
prioritizes finance/crisis; severely strained relationships prioritize
relationship events. Used event keys are removed from the candidate pool, so a
five-year path does not repeat a significant event.

Modes affect selection and tone without changing engine authority:

- Realistic uses grounded language and ordinary constraints.
- Cinematic foregrounds public turning points and reversals.
- Utopian favors coherent opportunities while retaining trade-offs.
- Dark favors crisis, financial pressure, and health costs.
- Chaos selects absurd but internally consistent events, such as a
  sensor-equipped coffee machine attracting fictional venture interest.

Yearly summaries state the defining event, visible financial/statistical
position, and central trade-off without calling the outcome a prediction.
Artifacts are typed rather than free-form blobs: news articles, academic
abstracts, company announcements, diary entries, emails, and professional
posts each have their own validated fields and fictional metadata.

Future-self profiles derive identity, occupation, location, happiness, stress,
achievement, and regret from the supplied timeline context. Personality is
seed-stable. Replies refer only to event keys present in that context and frame
advice as reflection from a fictional character, never as a guarantee.
