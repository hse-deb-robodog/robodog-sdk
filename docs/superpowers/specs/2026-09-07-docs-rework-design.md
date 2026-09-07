# Documentation rework — design

**Date:** 2026-09-07 (amended same day after grilling session)
**Status:** approved by Fabian (brainstorming + grilling sessions)

## Problem

The current documentation (six MyST pages + autodoc API reference) is written
for expert peers: dense, essayistic, opinion-led headings, and it assumes the
reader already knows Zenoh, zenode, asyncio, and the robot. The actual
audience are students familiar with none of these. There is no path from
"nothing installed" to "my node drives the robot", no explanation of the
foundations, and no per-topic reference.

## Goals

- A student with no Zenoh/zenode/asyncio/robot experience can follow one
  sequential guide from zero to a custom node controlling the (simulated)
  robot, entirely within these docs.
- Foundations (pub/sub, zenode's model, asyncio essentials) are taught here,
  in robot context; the zenode docs become optional further reading.
- All technical facts from the existing pages are preserved but fully
  rewritten in plain, professional prose. Opinion/rationale that does not
  change what the reader should do is cut. Nothing is copied verbatim.
- A per-topic reference exists: every topic's key, payload, direction,
  latched/expiry, publisher, and purpose.
- Explanatory diagrams for the load-bearing mechanisms.
- Docs are self-contained: bringing up the simulated robot requires no
  access to the private stack repo (see distribution model below).

## Non-goals

- No tooling change: Sphinx + Furo + MyST + autodoc + existing docs CI stay.
- No general asyncio or Python course — only asyncio as met through zenode.
- No changes to SDK code (except possibly docstring fixes surfaced while
  documenting).

## Distribution model: the simulation appliance

Deployment reality: the control stack runs on the Jetson on the dog; student
code lives in the students' own repos and talks to the stack over Zenoh via
this SDK. Students never work inside the stack — the only reason to touch it
is running the simulation locally. `robodog-digipro` is **private**;
`robodog-sdk` and `zenode` are public.

Decision: the SDK stays its own public repo and dependency. The simulated
stack ships as a **container appliance**:

- **One fat sim-stack image**, built and published (public GHCR) from
  `robodog-digipro` CI. Default process set: `sim`, `motion-gateway`,
  `safety`, `nav`, `system-state`, `joy`, `nav-map`.
  - `joy` starts but idles without a gamepad; gamepad passthrough
    (`/dev/input`) works on native Linux only — documented as such.
  - `nav-map` (browser UI for submitting nav goals) is exposed: it is the
    no-code verification tool ("if clicking works but your node doesn't,
    the problem is your code").
  - `localization` (odometry-passthrough fallback) is **excluded** — MOLA
    is mandatory and two publishers on `localization/pose` must not race.
  - `nav-viz`, `sensor-viz`, `rerun`, `vda5050`, `nav-remote` stay
    from-source extras.
- **Stock Zenoh router image.**
- **Existing MOLA image** (`mola_docker/`), unchanged: it consumes the
  sim's `sensors/livox/*` topics over Zenoh (no livox driver involved) and
  publishes `localization/pose`, `localization/map_identity`, `map/grid`.
  MOLA is part of the default bring-up — much of the system consumes the
  lidar pointcloud, not just odometry. No degraded mode in the guide.

Three services, one command. The compose file lives in **this repo** at
`sim/compose.yaml` (a separate template repo may take over later), pinning
image tags to the digipro release so compose ↔ SDK ↔ `CONTRACT_VERSION`
stay in lockstep. Exposed ports: mjviser web viewer (`:8080`) and the
`nav-map` UI.

External dependency (digipro-side, outside this repo, no time pressure but
precedes finalizing the setup chapter): Dockerfile + CI publish job for the
fat image; verify the MOLA image builds on amd64 (expected fine; sim EGL
config may need tweaks in containers without GPU).

## Decisions

| Question | Decision |
|---|---|
| Scope | Self-contained for students, incl. sim bring-up via the appliance |
| Foundations | Taught here in context, not delegated to zenode docs |
| Existing content | Keep all facts, rewrite fully; cut pure opinion |
| Language | English |
| Tooling | Keep Sphinx + Furo + MyST |
| Structure | Guide (sequential) + Concepts (any order) + Reference |
| Supported OSes | Linux + Windows (compose appliance); macOS (hybrid: native sim + containerized router/MOLA — verified by the prof); from-source as documented alternative (requires instructor-granted access to private digipro) |
| Primary scenario | Own laptop, own router, everything local; "connect to the lab dog" is its own section |
| Install snippets | Version substituted from `conf.py` `release`; never hand-pinned, never `main` |
| Rollout | Single PR from `docs/rework`, structured commits per part |
| Namespace / custom topics | `robodog` stays hard-coded (verified: no config/roadmap in digipro). Every student runs their own router, so no collision problem: **no prefix mandate**; ch. 08 keeps a light good-practice note on descriptive key names |
| Capstone example | Course-neutral: patrol/inspection node or turtle-style driving demo — picked at writing time |
| Diagrams | diagram-design skill with **HSE branding** onboarded from hs-esslingen.de; must stay legible in Furo light *and* dark themes; SVG in `docs/_static/`; mermaid only for trivial inline flows |
| Snippet verification | Substantial examples are CI-tested files included via MyST `literalinclude`; trivial fragments inline, untested |
| Old URLs | `sphinx-reredirects` stubs from the six old pages to their new homes |

## Structure

```
docs/
├── index.md                   # Landing: what/for whom, system picture, 3 entry cards,
│                              #   install command, license. Nothing else.
├── guide/
│   ├── 01-big-picture.md      # What the Robodog system is; architecture diagram
│   ├── 02-setup.md            # The appliance: docker compose up (Linux/Windows),
│   │                          #   macOS hybrid path, from-source alternative;
│   │                          #   verification incl. clicking a nav goal in nav-map
│   ├── 03-first-project.md    # New project: pyproject, zenode.toml, first node;
│   │                          #   teaches async handlers / Node / run / @subscribe in passing
│   ├── 04-driving.md          # RobotClient: move/driving/halt; the deadman in practice
│   ├── 05-sensing.md          # Subscribing to state; built on ODOMETRY (sim publishes
│   │                          #   no battery — battery appears in ch. 07 via FakeStack
│   │                          #   and on the real robot); closing the loop
│   ├── 06-navigation.md       # Tasks: browser first (nav-map), then the same from code;
│   │                          #   submit, feedback, the four outcomes, preemption
│   ├── 07-testing.md          # FakeStack / FakeNav; in-process harness
│   ├── 08-custom-topics.md    # Advanced: own topics + Pydantic message types
│   └── 09-advanced-control.md # Advanced: multi-node projects, tilt/postures, tracing;
│                              #   ends in the worked capstone example
├── concepts/
│   ├── architecture.md        # Stack processes, who talks to whom, topic groups per process
│   ├── pubsub.md              # Zenoh/zenode messaging model: keys, namespaces, latched,
│   │                          #   max_age, pub/sub vs services
│   ├── async-python.md        # Asyncio as met in zenode; blocking-the-loop treated at length
│   ├── motion.md              # Gateway, source arbitration (controller > assisted_teleop >
│   │                          #   planner > autonomous), deadman, collision zones, gateway state
│   ├── safety.md              # Hardware vs software stop, latching, motion_permitted,
│   │                          #   fail-safe on silence
│   ├── navigation.md          # Task lifecycle, state vs activity, e-stop policy,
│   │                          #   maps/frames/map identity
│   └── tracing.md             # How tracing works, timers break the chain, custom topics
├── reference/
│   ├── index.md               # How the reference is organized
│   ├── topics.md              # NEW per-topic reference (format below)
│   ├── client.md              # RobotClient autodoc
│   ├── messages.md            # msgs.* autodoc
│   ├── testing.md             # testing doubles autodoc
│   └── errors.md              # NEW: exceptions and what each means (see below)
└── _static/                   # exported diagram SVGs (+ sources for re-rendering)
sim/
└── compose.yaml               # NEW: the simulation appliance (router + sim-stack + MOLA)
```

The current six `.md` pages and `api/*.rst` are replaced by this tree; git
history preserves them, and `sphinx-reredirects` maps the old URLs.
`README.md`'s docs table is updated. `examples/` stays and is referenced
from the guide.

## Guide page template

Every guide page has:

1. **"In this chapter"** box — 3–4 bullets of what the student can do after
2. **Prerequisites** — which chapters it builds on, what must be running
3. Numbered steps; every code block complete and runnable (placeable in a
   file), each followed by *what you should see* (expected terminal output)
4. **Troubleshooting** callout at classic failure points (wrong namespace →
   silence; unsynced clocks → commands ignored)
5. **"Where to go next"** footer — next chapter + related concept page

Content placement rule: guide chapters carry only what is needed to act;
full mechanisms live in the concept pages, linked at first mention.

## Topic reference format

One section per topic group (Motion, Pose, Control, Safety, Input, State,
Localization, Map, Nav). Per topic, a fixed entry:

- Header: key + payload type
- Fact table: direction, latched, expiry (`max_age`), published by
- *What it's for:* one sentence
- *Details:* rate, frame conventions, caveats

Mechanical facts (key, type, latched, max_age, trace) are derived from
`topics.py`. "Published by" comes from the verified process → topic mapping
gathered from digipro source. Remaining prose comes from existing
docs/docstrings where available; otherwise a marked TODO slot.

## Errors reference

The SDK defines **no custom exception classes** (verified). `errors.md`
documents the real surface: `PermissionError` (refused nav goal / guarded
client op), `TimeoutError` (coordinator not answering), `ValueError`
(validator failures, `wait_until_ready` misuse), `LookupError` (FakeNav),
and `pydantic.ValidationError` (message construction, incl. limit
violations). The old docs mention a `ServiceError` that does not exist in
this package — the rewrite names the real exception after verifying against
zenode.

## Diagrams

Produced with the diagram-design skill (HSE brand tokens onboarded from
hs-esslingen.de, theme-safe), exported as SVG into `docs/_static/`:

1. System architecture — processes + SDK's place, router in the middle;
   shows the appliance == the real dog in shape (guide/01,
   concepts/architecture)
2. Pub/sub model — key/namespace anatomy, decoupling, latched vs streaming
   (concepts/pubsub)
3. Motion command flow — sources → inlet → gateway arbitration → robot;
   collision shaping and deadman (concepts/motion)
4. Navigation task lifecycle — state machine incl. the four outcomes
   (concepts/navigation)
5. Safety chain — hardware vs software stop, latch and release path
   (concepts/safety)
6. First-node sequence — startup + first message (guide/03)

Mermaid remains acceptable for trivial inline flows.

## Writing style

- Plain declarative headings stating the fact ("Commands expire after
  0.3 seconds"), never rhetorical ones.
- Second person, present tense. No essayistic asides. Rationale only where
  it changes what the student should do.
- Behavior claims name the concrete observable ("the robot stops", "you get
  a `ValidationError`").
- Admonitions: `note` context, `warning` damage/surprise (safety,
  arbitration ranks), `tip` conveniences.

## TODO convention

Facts only Fabian knows are marked `🚧 TODO(fabian): <specific question>` —
greppable; each states a concrete question, never bare "fill this in".

## Build note

`docs/superpowers/` must be added to `exclude_patterns` in `conf.py` —
otherwise the `-W` build fails on documents not in any toctree.

## Verification

- `uv run sphinx-build -W docs docs/_build/html` must pass (warnings as
  errors) at every step.
- Substantial guide examples live as files exercised in CI against the
  `robodog_sdk.testing` doubles (the way `tests/test_examples.py` does) and
  are pulled into the docs via `literalinclude` — single source of truth.
- Fact-preservation check: every technical claim in the old pages is either
  present in the new tree or deliberately dropped as pure opinion.
- The macOS hybrid path is verified on real hardware (the prof's machine)
  before the setup chapter claims it.
