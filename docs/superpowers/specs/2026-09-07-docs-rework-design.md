# Documentation rework — design

**Date:** 2026-09-07
**Status:** approved by Fabian (brainstorming session)

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
- Docs are self-contained about bringing up the stack (simulation path uses
  real commands from the local `robodog-digipro` repo; lab/hardware-specific
  values get marked TODO slots).

## Non-goals

- No tooling change: Sphinx + Furo + MyST + autodoc + existing docs CI stay.
- No general asyncio or Python course — only asyncio as met through zenode.
- No changes to SDK code (except possibly docstring fixes surfaced while
  documenting).

## Decisions (from brainstorming)

| Question | Decision |
|---|---|
| Scope | Self-contained for students, including stack/sim bring-up |
| Foundations | Taught here in context, not delegated to zenode docs |
| Existing content | Keep all facts, rewrite fully; cut pure opinion |
| Language | English |
| Tooling | Keep Sphinx + Furo + MyST |
| Diagrams | diagram-design skill → SVG in `docs/_static/`; mermaid only for trivial inline flows |
| Structure | Guide (sequential) + Concepts (any order) + Reference |

## Structure

```
docs/
├── index.md                   # Landing: what/for whom, system picture, 3 entry cards,
│                              #   install command, license. Nothing else.
├── guide/
│   ├── 01-big-picture.md      # What the Robodog system is; architecture diagram
│   ├── 02-setup.md            # uv, Zenoh router (docker), simulation stack, verification
│   ├── 03-first-project.md    # New project: pyproject, zenode.toml, first node;
│   │                          #   teaches async handlers / Node / run / @subscribe in passing
│   ├── 04-driving.md          # RobotClient: move/driving/halt; the deadman in practice
│   ├── 05-sensing.md          # Subscribing to state (odometry, battery); closing the loop
│   ├── 06-navigation.md       # Tasks: submit, feedback, the four outcomes, preemption
│   ├── 07-testing.md          # FakeStack / FakeNav; in-process harness
│   ├── 08-custom-topics.md    # Advanced: own topics + Pydantic message types
│   └── 09-advanced-control.md # Advanced: multi-node projects, tilt/postures, tracing;
│                              #   ends in one worked multi-file example (e.g. patrol node)
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
│   └── errors.md              # NEW: exceptions and what each means
└── _static/                   # exported diagram SVGs (+ sources for re-rendering)
```

The current six `.md` pages and `api/*.rst` are replaced by this tree; git
history preserves them. `README.md`'s docs table is updated. `examples/`
stays and is referenced from the guide.

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
`topics.py`. Prose comes from existing docs/docstrings where available;
otherwise a marked TODO slot.

## Diagrams

Produced with the diagram-design skill, exported as SVG (light/dark-safe)
into `docs/_static/`:

1. System architecture — processes + SDK's place, router in the middle
   (guide/01, concepts/architecture)
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
- Guide snippets that can run against `robodog_sdk.testing` doubles are
  exercised the way `tests/test_examples.py` does, where practical.
- Fact-preservation check: every technical claim in the old pages is either
  present in the new tree or deliberately dropped as pure opinion.
