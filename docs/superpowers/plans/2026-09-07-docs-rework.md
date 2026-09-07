# Documentation Rework Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the expert-oriented docs with a student-facing docs site: a sequential Guide (zero → custom node driving the simulated robot), standalone Concepts pages, and a Reference including a per-topic reference — plus the `sim/compose.yaml` appliance file and CI-tested guide examples.

**Architecture:** Sphinx + Furo + MyST stays. New tree `docs/guide/`, `docs/concepts/`, `docs/reference/` is built page-by-page on branch `docs/rework` (old pages coexist until the cutover task). Substantial guide examples live as runnable files in `examples/guide/`, tested in `tests/test_guide_examples.py`, and are pulled into pages via `literalinclude`. Diagrams are produced with the diagram-design skill (HSE branding) and inserted after the cutover.

**Tech Stack:** Python ≥3.11, uv, Sphinx 8 (myst-parser, autodoc, napoleon, intersphinx, copybutton, mermaid, + new: sphinx-design, sphinx-reredirects), Furo, pytest + pytest-asyncio (`asyncio_mode = "auto"`), zenode test harness, docker compose.

**Spec:** `docs/superpowers/specs/2026-09-07-docs-rework-design.md`

## Global Constraints

- Work on branch `docs/rework`. Never commit to `main`.
- `uv run --group docs sphinx-build -W docs docs/_build/html` must pass at the end of EVERY task (warnings are errors).
- `uv run pytest` must pass at the end of every task that touches Python files.
- Writing style (spec section "Writing style"): plain declarative headings stating the fact; second person, present tense; no essayistic asides; rationale only where it changes what the student does; behavior claims name the concrete observable; admonitions: `{note}` context, `{warning}` damage/surprise, `{tip}` conveniences.
- Nothing is copied verbatim from the old pages (`docs/driving.md`, `docs/navigation.md`, `docs/safety.md`, `docs/tracing.md`, `docs/testing.md`, old `docs/index.md`) — same facts, new prose.
- Facts only Fabian knows are marked exactly `🚧 TODO(fabian): <specific question>` — each states a concrete question.
- Version in install snippets: write the literal token `%%SDK_VERSION%%`; the conf.py hook (Task 1) replaces it at build time. Never hand-write a version tag in a page.
- Namespace is `robodog` everywhere, presented as a fixed fact of the deployment.
- Every guide page follows the template: "In this chapter" bullets → Prerequisites → numbered steps with complete runnable code and "what you should see" → Troubleshooting callout where classically needed → "Where to go next" footer linking the next chapter + related concept page.
- Guide chapters carry only what is needed to act; mechanisms live in concept pages, linked at first mention.
- Commit after every task with a `docs:`-prefixed conventional message (examples/tests may use `test:`/`feat:` where more accurate).

---

### Task 1: Docs infrastructure (version substitution, new extensions, build hygiene)

**Files:**
- Modify: `docs/conf.py`
- Modify: `pyproject.toml` (docs dependency group)
- Modify: `docs/index.md` (only the two install snippets — swap hardcoded tag for the token)

**Interfaces:**
- Produces: build-time replacement of the literal token `%%SDK_VERSION%%` with the installed package version (e.g. `0.2.1`) in every MyST source; extensions `sphinx_design` (for `{grid}` cards, used in Task 16) and `sphinx_reredirects` (config stays empty until Task 16) available to all later tasks.

- [ ] **Step 1: Add docs dependencies**

In `pyproject.toml`, extend the `docs` dependency group:

```toml
docs = [
    # Built in CI and on demand (uv run --group docs …); never shipped, so the
    # runtime-dependency constraint is untouched. Mirrors the zenode setup.
    "sphinx>=8.2",
    "furo>=2024.8.6",
    "myst-parser>=4.0",
    "sphinx-copybutton>=0.5.2",
    "sphinxcontrib-mermaid>=1.0",
    "sphinx-design>=0.6",
    "sphinx-reredirects>=0.1.5",
]
```

Run: `uv sync --group docs` — expect it to resolve and install both new packages.

- [ ] **Step 2: Update conf.py**

In `docs/conf.py`:

a) Extend the extensions list:

```python
extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",  # docstrings use Google-style Args:/Returns: sections
    "sphinx.ext.intersphinx",
    "sphinx_copybutton",
    "sphinxcontrib.mermaid",
    "sphinx_design",
    "sphinx_reredirects",
]
```

b) Change `exclude_patterns` to also skip the spec/plan documents (they are not part of the site and fail `-W` as un-toctree'd):

```python
exclude_patterns = ["_build", "superpowers"]
```

c) Add (empty for now) redirects config after `exclude_patterns`:

```python
# Old page URLs → new homes. Filled in at cutover (see the rework plan).
redirects: dict[str, str] = {}
```

d) At the bottom of the file, add the version-substitution hook. `source-read` fires on the raw source of every page, so the token works anywhere — including inside fenced code blocks, which MyST substitutions cannot reach:

```python
def _substitute_version(app, docname, source):
    source[0] = source[0].replace("%%SDK_VERSION%%", release)


def setup(app):
    app.connect("source-read", _substitute_version)
```

- [ ] **Step 3: Use the token in the existing index.md**

In `docs/index.md`, replace both install snippets' `@v0.2.1` with `@v%%SDK_VERSION%%` (the surrounding lines stay as they are for now; this page is fully rewritten in Task 16).

- [ ] **Step 4: Verify the build and the substitution**

Run: `uv run --group docs sphinx-build -W docs docs/_build/html`
Expected: success, no warnings.

Run: `grep -o "robodog-sdk@v[0-9.]*" docs/_build/html/index.html | head -2`
Expected: `robodog-sdk@v0.2.1` (the real version, not the token). Also run `grep -c "%%SDK_VERSION%%" docs/_build/html/index.html` — expected `0`.

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml uv.lock docs/conf.py docs/index.md
git commit -m "docs: add version substitution, sphinx-design and reredirects infrastructure"
```

---

### Task 2: Section skeleton (guide/concepts/reference indexes)

**Files:**
- Create: `docs/guide/index.md`
- Create: `docs/concepts/index.md`
- Create: `docs/reference/index.md`
- Modify: `docs/index.md` (toctree only)

**Interfaces:**
- Produces: three section index pages, each with its own `{toctree}` that later tasks append entries to. Root toctree includes them (old pages stay listed until Task 16).

- [ ] **Step 1: Create the three index pages**

`docs/guide/index.md`:

````markdown
# Guide

A sequential path from an empty laptop to your own software controlling the
robot. The chapters build on each other — work through them in order. If you
are new to the system, start at chapter 1.

```{toctree}
:maxdepth: 1
```
````

`docs/concepts/index.md`:

````markdown
# Concepts

How the system actually works, one mechanism per page. These pages do not
build on each other — read them when the guide links here, or whenever you
want the full picture behind something you are using.

```{toctree}
:maxdepth: 1
```
````

`docs/reference/index.md`:

````markdown
# Reference

Lookup material: every topic on the wire, every class and method in the
package, and every exception you can encounter.

```{toctree}
:maxdepth: 1
```
````

- [ ] **Step 2: Wire them into the root toctree**

In `docs/index.md`, change the hidden toctree to:

```markdown
```{toctree}
:hidden:

guide/index
concepts/index
reference/index
driving
navigation
safety
tracing
testing
api/index
```
```

- [ ] **Step 3: Build**

Run: `uv run --group docs sphinx-build -W docs docs/_build/html`
Expected: success. (An empty `{toctree}` is legal.)

- [ ] **Step 4: Commit**

```bash
git add docs/guide/index.md docs/concepts/index.md docs/reference/index.md docs/index.md
git commit -m "docs: add guide/concepts/reference section skeleton"
```

---

### Task 3: Guide chapter 1 — The big picture

**Files:**
- Create: `docs/guide/01-big-picture.md`
- Modify: `docs/guide/index.md` (toctree entry)

**Interfaces:**
- Produces: the guide's opening page. References `_static/architecture.svg` — but do NOT add the image yet (Task 17 inserts it); leave the marked slot described below.

- [ ] **Step 1: Write the page**

Structure and mandatory content for `docs/guide/01-big-picture.md`:

- H1: `The big picture`
- "In this chapter" `{note}` box: understand what the Robodog system is; know which processes exist and where your code fits; know what the SDK gives you.
- Prerequisites: none.
- Section `A robot, a control stack, and your code` — facts to state:
  - The robot is a Unitree Go2 quadruped. On its back sits a Jetson computer running the *control stack*: a set of independent programs (robot bridge, motion gateway, safety, navigation, SLAM) that together drive the robot.
  - You do not write code inside the control stack. You write your own program, in your own project, and it *talks to* the stack over the network.
  - The messaging layer is [Eclipse Zenoh](https://zenoh.io): programs publish messages on named topics and subscribe to the topics they care about. Link `[pub/sub concepts](../concepts/pubsub.md)`.
  - `robodog-sdk` (this package) is how your Python program joins that conversation: it knows every topic, every message type, and provides `RobotClient` for the common operations.
  - A comment slot exactly here: `<!-- diagram: architecture.svg inserted in the diagram task -->`
- Section `The simulation is the same robot` — facts:
  - The whole stack also runs as a simulation on your laptop (MuJoCo physics). It publishes the same topics with the same types, so the code you write against the simulation runs unchanged against the real dog.
  - You bring it up with a single `docker compose up` — chapter 2 does exactly that.
- Section `What you will build in this guide` — one line per chapter 2–9, phrased as abilities ("bring up the simulated robot", "drive it from your own code", …).
- "Where to go next" footer: chapter 2, and `[Architecture](../concepts/architecture.md)` for the full process/topic map. (The concepts pages do not exist yet — write the links anyway; the build only checks them once both sides exist, and Tasks 12–14 create them. If `-W` flags a broken cross-reference at this point, keep the link text but make it a plain-text mention with a `<!-- link when concepts/architecture.md exists -->` comment and restore it in Task 12.)

- [ ] **Step 2: Add to the guide toctree**

In `docs/guide/index.md`, the toctree becomes:

```markdown
```{toctree}
:maxdepth: 1

01-big-picture
```
```

- [ ] **Step 3: Build**

Run: `uv run --group docs sphinx-build -W docs docs/_build/html`
Expected: success.

- [ ] **Step 4: Commit**

```bash
git add docs/guide/01-big-picture.md docs/guide/index.md
git commit -m "docs: add guide chapter 1 (big picture)"
```

---

### Task 4: Guide chapter 2 — Setup, plus the sim appliance compose file

**Files:**
- Create: `sim/compose.yaml`
- Create: `docs/guide/02-setup.md`
- Modify: `docs/guide/index.md` (append `02-setup`)

**Interfaces:**
- Produces: `sim/compose.yaml` (three services: `zenoh-router`, `sim-stack`, `mola`). Later chapters assume "the appliance is up" means `docker compose -f sim/compose.yaml up` succeeded and the router listens on `tcp/localhost:7447`.

- [ ] **Step 1: Write sim/compose.yaml**

```yaml
# The simulated Robodog control stack. One command brings up the same set of
# programs that runs on the real dog's Jetson:
#
#     docker compose up
#
# Web viewer:  http://localhost:8080   (watch the simulated robot)
# Nav UI:      http://localhost:8081   (click to send navigation goals)
services:
  zenoh-router:
    # 🚧 TODO(fabian): pin the router image+tag the stack deploys with
    image: eclipse/zenoh:1.5.1
    ports:
      - "7447:7447"

  sim-stack:
    # Simulation, motion gateway, safety, navigation, system-state, joy and
    # the nav web UI in one image, published from the robodog-digipro CI.
    # 🚧 TODO(fabian): replace with the first published tag once the image exists
    image: ghcr.io/hse-deb-algo-athlets/robodog-sim-stack:latest
    depends_on:
      - zenoh-router
    environment:
      ZENOH_ROUTER_ENDPOINT: tcp/zenoh-router:7447
    ports:
      - "8080:8080"   # mjviser web viewer
      # 🚧 TODO(fabian): confirm the nav-map UI port and map it here
      - "8081:8081"
    # Gamepad teleoperation (Linux only): uncomment to pass your gamepad
    # through to the joy node. Has no effect on Windows/macOS.
    # devices:
    #   - /dev/input:/dev/input

  mola:
    # LiDAR-inertial SLAM. Consumes the simulated Livox point cloud over
    # Zenoh and publishes pose, map identity and the occupancy grid.
    # 🚧 TODO(fabian): image name+tag of the published MOLA image
    image: ghcr.io/hse-deb-algo-athlets/robodog-mola:latest
    depends_on:
      - zenoh-router
    environment:
      ZENOH_ROUTER_ENDPOINT: tcp/zenoh-router:7447
```

Run: `docker compose -f sim/compose.yaml config`
Expected: prints the resolved config without errors (images need not exist for `config`).

- [ ] **Step 2: Write the setup chapter**

Structure and mandatory content for `docs/guide/02-setup.md`:

- H1: `Set up the simulated robot`
- "In this chapter" box: install the prerequisites; start the simulated robot with one command; verify it by sending it somewhere from your browser.
- Prerequisites: chapter 1 read; a laptop with ~8 GB RAM free.
- Section `What you need` — numbered install steps with links: Docker (Desktop on Windows/macOS, engine on Linux), [uv](https://docs.astral.sh/uv/), Python ≥ 3.11 (note: `uv python install 3.12` works if the system lacks one).
- Section `Start the appliance` — steps:
  1. Download `sim/compose.yaml` (link to the file on GitHub `main`).
  2. `docker compose up` in that directory. "What you should see": three services starting; log lines from the simulation.
  3. Open `http://localhost:8080` — the simulated robot in the web viewer.
- Section `Send the robot somewhere — no code yet` — steps: open the nav UI (`http://localhost:8081` — carry the `🚧 TODO(fabian): confirm nav-map port + a screenshot of the UI` marker), click a goal on the map, watch the robot drive there in the viewer. State the lesson explicitly in a `{tip}`: this browser page is your control experiment forever after — *if clicking works but your code doesn't, the problem is in your code, not the stack.*
- Section `macOS` — the hybrid path, presented as its own subsection, not an afterthought: run `zenoh-router` and `mola` from the compose file (`docker compose up zenoh-router mola`), and the simulation natively. Carry marker: `🚧 TODO(fabian): exact native-sim install/run commands for macOS once verified on the prof's machine (MUJOCO_GL=glfw, uv run sim against localhost router)`.
- Section `Running the stack from source (optional)` — one paragraph: for stack development or platforms where the images don't work; requires access to the private `hse-deb-algo-athlets/robodog-digipro` repository ("ask your instructor"); link to that repo's README/setup guide; summary of its quick start (`uv sync --all-extras`, copy `config/config.toml.example`, router via its docker compose, `uv run sim`).
- Troubleshooting `{warning}` box: port 7447 already in use; Docker Desktop not running; viewer black/empty (give the sim ~10 s).
- "Where to go next": chapter 3; `[Architecture](../concepts/architecture.md)` (same broken-link fallback rule as Task 3).

- [ ] **Step 3: Append `02-setup` to the toctree in `docs/guide/index.md`, build**

Run: `uv run --group docs sphinx-build -W docs docs/_build/html`
Expected: success.

- [ ] **Step 4: Commit**

```bash
git add sim/compose.yaml docs/guide/02-setup.md docs/guide/index.md
git commit -m "docs: add setup chapter and simulation appliance compose file"
```

---

### Task 5: Guide chapter 3 — Your first project (+ example + test)

**Files:**
- Create: `examples/guide/first_node.py`
- Create: `tests/test_guide_examples.py`
- Modify: `tests/conftest.py` (add `examples/guide` to the path)
- Create: `docs/guide/03-first-project.md`
- Modify: `docs/guide/index.md` (append `03-first-project`)

**Interfaces:**
- Consumes: `zenode.Node`, `zenode.run`, `zenode.subscribe`, `robodog_sdk.StateTopics`, `robodog_sdk.OdometryState`, `robodog_sdk.testing.FakeStack`, `zenode.testing.harness`.
- Produces: `examples/guide/first_node.py` defining `class FirstNode(Node)` with attribute `last: OdometryState | None` and handler `on_odometry`; `tests/test_guide_examples.py` with shared constant `SETTLE = 0.2`, which every later guide-example task appends tests to.

- [ ] **Step 1: Extend conftest**

In `tests/conftest.py`, below the existing insert:

```python
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "examples" / "guide"))
```

- [ ] **Step 2: Write the failing test**

Create `tests/test_guide_examples.py`:

```python
"""The guide's example nodes run and behave as their chapters claim.

Each file under ``examples/guide/`` is literalincluded by a guide chapter and
started here against the doubles in ``robodog_sdk.testing`` — an example that
stops working fails CI rather than a reader.
"""

from __future__ import annotations

import asyncio

import first_node
import pytest
from zenode.testing import harness

from robodog_sdk.testing import FakeStack

pytestmark = pytest.mark.integration

SETTLE = 0.2  # generous: these assert on behaviour, not on latency


async def test_first_node_receives_odometry() -> None:
    async with harness() as h:
        stack = await h.start_node(FakeStack)
        node = await h.start_node(first_node.FirstNode)

        stack.set_pose(x=1.5, y=-0.5)
        await asyncio.sleep(SETTLE)

        assert node.last is not None, "the handler should have run"
        assert node.last.x == pytest.approx(1.5)
```

- [ ] **Step 3: Run it to verify it fails**

Run: `uv run pytest tests/test_guide_examples.py -v`
Expected: FAIL/ERROR with `ModuleNotFoundError: No module named 'first_node'`.

- [ ] **Step 4: Write the example**

Create `examples/guide/first_node.py`:

```python
"""The guide's first node: subscribe to the robot's position and log it.

uv run python examples/guide/first_node.py
"""

from __future__ import annotations

from zenode import Node, run, subscribe

from robodog_sdk import OdometryState, StateTopics


class FirstNode(Node):
    name = "first-node"

    #: The most recent position, kept so other parts of the node can read it.
    last: OdometryState | None = None

    @subscribe(StateTopics.odometry, mode="latest")
    async def on_odometry(self, msg: OdometryState) -> None:
        self.last = msg
        self.log.info("robot at x=%.2f m, y=%.2f m", msg.x, msg.y)


def cli() -> None:
    run(FirstNode)


if __name__ == "__main__":
    cli()
```

- [ ] **Step 5: Run the test to verify it passes**

Run: `uv run pytest tests/test_guide_examples.py -v`
Expected: PASS. Then run the full suite: `uv run pytest` — expected: all pass.

- [ ] **Step 6: Write the chapter**

Structure and mandatory content for `docs/guide/03-first-project.md`:

- H1: `Your first project`
- "In this chapter" box: create a Python project with uv; connect a node to the running simulation; receive live data from the robot.
- Prerequisites: chapter 2 — the appliance is running.
- Section `Create the project` — exact commands: `uv init my-robot-project && cd my-robot-project`, then `uv add "robodog-sdk @ git+https://github.com/hse-deb-algo-athlets/robodog-sdk@v%%SDK_VERSION%%"`. "What you should see": the resolved install, two runtime dependencies.
- Section `Tell your project where the robot is` — the `zenode.toml`, verbatim:

  ```toml
  [transport]
  mode = "client"
  connect = ["tcp/localhost:7447"]
  namespace = "robodog"
  ```

  Facts to state: this file is read by zenode at start; `connect` points at the router from chapter 2 (the same file with the dog's address instead talks to the real robot); every topic key is prefixed with `namespace` on the wire, and the deployment uses `robodog` — with any other value you see no data and no error. `{warning}` box for exactly that failure mode, plus the check: `uv run zenode nodes`.
- Section `A node that listens` — introduce the code via `` ```{literalinclude} ../../examples/guide/first_node.py `` with `:language: python`. Then explain, in prose keyed to the code, each concept **on first contact**: what a `Node` is (one program in the conversation); `name` (how it appears in `zenode nodes`); `@subscribe(StateTopics.odometry, mode="latest")` (call this method on new data; `latest` drops backlog — you want current position, not history); why the handler is `async def` — with a short plain-language explanation of the event loop: the node does many things concurrently on one thread, so handlers must never block; link `[asyncio essentials](../concepts/async-python.md)` and `[pub/sub](../concepts/pubsub.md)` at first mention.
- Section `Run it` — `uv run python first_node.py` (their copy), expected output: log lines with the pose changing as the sim publishes. Tell them to drive the robot from the nav UI (chapter 2) and watch the numbers move.
- Troubleshooting: no log lines → namespace/router checklist from above.
- "Where to go next": chapter 4; concepts: pub/sub, asyncio.

- [ ] **Step 7: Append `03-first-project` to the guide toctree, build**

Run: `uv run --group docs sphinx-build -W docs docs/_build/html`
Expected: success.

- [ ] **Step 8: Commit**

```bash
git add examples/guide/first_node.py tests/test_guide_examples.py tests/conftest.py docs/guide/03-first-project.md docs/guide/index.md
git commit -m "docs: add guide chapter 3 (first project) with tested example"
```

---

### Task 6: Guide chapter 4 — Driving (+ example + test)

**Files:**
- Create: `examples/guide/timed_drive.py`
- Modify: `tests/test_guide_examples.py` (append tests)
- Create: `docs/guide/04-driving.md`
- Modify: `docs/guide/index.md` (append `04-driving`)

**Interfaces:**
- Consumes: `RobotClient(node)` with `.move(x=, y=, z_deg=)`, `.halt()`, `async with .driving(x=...)`; `FakeStack.set_pose/.last_command/.stopped`; `zenode.NodeConfig`.
- Produces: `examples/guide/timed_drive.py` defining `DriveConfig(NodeConfig)` (fields `speed: float = 0.3`, `duration: float = 2.0`) and `class TimedDrive(Node)`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_guide_examples.py` (add `import timed_drive` to the imports):

```python
async def test_timed_drive_drives_then_stops() -> None:
    async with harness() as h:
        stack = await h.start_node(FakeStack)
        await h.start_node(
            timed_drive.TimedDrive,
            config=timed_drive.DriveConfig(speed=0.3, duration=0.3),
        )

        await asyncio.sleep(SETTLE)
        assert stack.last_command is not None
        assert stack.last_command.x == pytest.approx(0.3), "should be driving forward"

        await asyncio.sleep(0.4)  # past the configured duration
        assert stack.stopped, "leaving driving() must leave the robot stopped"
```

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/test_guide_examples.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'timed_drive'`.

- [ ] **Step 3: Write the example**

Create `examples/guide/timed_drive.py`:

```python
"""Drive forward for a fixed time, then stop — the guide's first movement.

uv run python examples/guide/timed_drive.py
"""

from __future__ import annotations

import asyncio

from zenode import Node, NodeConfig, run

from robodog_sdk import RobotClient


class DriveConfig(NodeConfig):
    #: Forward speed in m/s.
    speed: float = 0.3
    #: How long to drive, in seconds.
    duration: float = 2.0


class TimedDrive(Node):
    name = "timed-drive"
    config: DriveConfig

    robot: RobotClient

    async def on_start(self) -> None:
        self.robot = RobotClient(self)
        self.spawn(self._run(), name="drive")

    async def _run(self) -> None:
        # driving() republishes the command for as long as the block runs and
        # always stops the robot on the way out — even on an exception.
        async with self.robot.driving(x=self.config.speed):
            await asyncio.sleep(self.config.duration)
        self.log.info("done")
        self.stop()


def cli() -> None:
    run(TimedDrive)


if __name__ == "__main__":
    cli()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_guide_examples.py -v` then `uv run pytest`
Expected: PASS / all pass. If a `FakeStack` or client signature differs from the code above, fix the example (not the assertion's meaning) against the real API in `src/robodog_sdk/`.

- [ ] **Step 5: Write the chapter**

Structure and mandatory content for `docs/guide/04-driving.md`:

- H1: `Drive the robot`
- "In this chapter" box: move the robot from code; understand why commands expire; stop reliably.
- Prerequisites: chapters 2–3.
- Section `Meet RobotClient` — facts: one object, created with your node (`RobotClient(self)` in `on_start`), covering movement, navigation and safety queries; it publishes the same messages any stack node does — no privileged access; link `[how commands reach the robot](../concepts/motion.md)`.
- Section `Commands expire after 0.3 seconds` — facts, stated as the safety feature it is: every movement command carries a maximum age of 0.3 s (`COMMAND_MAX_AGE`); if your program stops publishing — crash, breakpoint, network drop — the robot stops. Consequence: a single `robot.move(x=0.3)` drives for 300 ms only. The two correct patterns: `async with robot.driving(...)` (republishes for you, always stops on exit), or calling `robot.move(...)` from a handler that fires regularly (chapter 5 does this). `{warning}`: age is measured across machines — clocks must be NTP-synchronized or the robot ignores you (guide troubleshooting classic).
- Section `A node that drives` — `{literalinclude}` of `timed_drive.py`, prose walking the new pieces: `NodeConfig` (typed config, overridable from `zenode.toml`), `self.spawn` (start a background job owned by the node), the `driving()` context manager guarantee.
- Section `Run it` — command + "what you should see": the robot moves forward in the viewer for 2 s and stops.
- Section `Speed limits are enforced in your process` — fact: `MovementCommand` validates against the robot's real capability envelope; out-of-range values raise `pydantic.ValidationError` at call time, before anything reaches the robot.
- Troubleshooting: robot doesn't move → is the sim viewer showing it upright; is anyone else commanding it (nav task still running from ch. 2 — cancel in the nav UI); clocks (real robot only).
- "Where to go next": chapter 5; concepts: motion.

- [ ] **Step 6: Append `04-driving` to the guide toctree, build**

Run: `uv run --group docs sphinx-build -W docs docs/_build/html`
Expected: success.

- [ ] **Step 7: Commit**

```bash
git add examples/guide/timed_drive.py tests/test_guide_examples.py docs/guide/04-driving.md docs/guide/index.md
git commit -m "docs: add guide chapter 4 (driving) with tested example"
```

---

### Task 7: Guide chapter 5 — Sensing and closing the loop (+ example + test)

**Files:**
- Create: `examples/guide/wanderer.py`
- Modify: `tests/test_guide_examples.py` (append tests)
- Create: `docs/guide/05-sensing.md`
- Modify: `docs/guide/index.md` (append `05-sensing`)

**Interfaces:**
- Consumes: everything from Tasks 5–6.
- Produces: `examples/guide/wanderer.py` defining `WanderConfig(NodeConfig)` (fields `speed: float = 0.3`, `distance: float = 1.0`) and `class Wanderer(Node)` that drives forward until odometry `x` exceeds `distance`, then halts. (Odometry only — the sim publishes no battery data; battery appears in chapter 7 via `FakeStack` per the spec.)

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_guide_examples.py` (add `import wanderer` to the imports):

```python
async def test_wanderer_drives_until_the_distance_is_covered() -> None:
    async with harness() as h:
        stack = await h.start_node(FakeStack)
        await h.start_node(
            wanderer.Wanderer,
            config=wanderer.WanderConfig(speed=0.3, distance=1.0),
        )

        stack.set_pose(x=0.0, y=0.0)
        await asyncio.sleep(SETTLE)
        assert stack.last_command is not None
        assert stack.last_command.x == pytest.approx(0.3), "should be driving"

        stack.set_pose(x=2.0, y=0.0)  # past the target distance
        await asyncio.sleep(SETTLE)
        assert stack.stopped, "should stop once the distance is covered"
```

- [ ] **Step 2: Run to verify failure** — `uv run pytest tests/test_guide_examples.py -v`, expect `ModuleNotFoundError: No module named 'wanderer'`.

- [ ] **Step 3: Write the example**

Create `examples/guide/wanderer.py`:

```python
"""Close the loop: drive forward until the robot has covered a distance.

    uv run python examples/guide/wanderer.py

Publishing one command per odometry message keeps the command stream fresher
than the 0.3 s expiry, so the deadman never trips while data flows — and if
data stops flowing, stopping is exactly what should happen.
"""

from __future__ import annotations

from zenode import Node, NodeConfig, run, subscribe

from robodog_sdk import OdometryState, RobotClient, StateTopics


class WanderConfig(NodeConfig):
    #: Forward speed in m/s.
    speed: float = 0.3
    #: Stop after covering this distance along x, in meters.
    distance: float = 1.0


class Wanderer(Node):
    name = "wanderer"
    config: WanderConfig

    robot: RobotClient

    async def on_start(self) -> None:
        self.robot = RobotClient(self)

    @subscribe(StateTopics.odometry, mode="latest")
    async def on_odometry(self, msg: OdometryState) -> None:
        if msg.x < self.config.distance:
            self.robot.move(x=self.config.speed)
        else:
            self.robot.halt()


def cli() -> None:
    run(Wanderer)


if __name__ == "__main__":
    cli()
```

- [ ] **Step 4: Run tests** — `uv run pytest`, expected: all pass (same fix rule as Task 6 Step 4).

- [ ] **Step 5: Write the chapter**

Structure and mandatory content for `docs/guide/05-sensing.md`:

- H1: `React to what the robot senses`
- "In this chapter" box: read live robot state; make movement depend on it; know which state topics exist.
- Prerequisites: chapters 3–4.
- Section `Sense, decide, act — in the handler` — `{literalinclude}` of `wanderer.py`; prose: the whole control loop is the handler; one `move()` per odometry message keeps commands fresh (ties back to ch. 4's expiry — and note the elegant property: if sensing dies, driving stops, which is the safe direction).
- Section `What else you can subscribe to` — a short table: `StateTopics.odometry` (position), `StateTopics.battery` (charge — `{note}`: not published by the simulation; you'll fake it in chapter 7 and see it live on the real robot), `LocalizationTopics.pose` (map-frame position from SLAM), `SafetyTopics.state` (e-stop latch). One line each on when to use which; full list link → `[Topic reference](../reference/topics.md)` (broken-link fallback rule as in Task 3 until Task 15 lands).
- Section `Client state without subscribing` — fact: `RobotClient` already watches the important topics; `robot.state.odometry.value`, `.fresh(within=...)` for staleness; when you just need the latest value in a background job, read it from `robot.state` instead of wiring your own subscription.
- Section `Run it` — expected behavior in the viewer.
- Troubleshooting: handler never fires → same namespace checklist; robot creeps past the line → that's real robot dynamics (braking distance), not a bug.
- "Where to go next": chapter 6; concepts: pub/sub.

- [ ] **Step 6: Append `05-sensing` to the toctree, build** — `uv run --group docs sphinx-build -W docs docs/_build/html`, expected: success.

- [ ] **Step 7: Commit**

```bash
git add examples/guide/wanderer.py tests/test_guide_examples.py docs/guide/05-sensing.md docs/guide/index.md
git commit -m "docs: add guide chapter 5 (sensing) with tested example"
```

---

### Task 8: Guide chapter 6 — Navigation tasks (+ example + test)

**Files:**
- Create: `examples/guide/goto.py`
- Modify: `tests/test_guide_examples.py` (append tests)
- Create: `docs/guide/06-navigation.md`
- Modify: `docs/guide/index.md` (append `06-navigation`)

**Interfaces:**
- Consumes: `RobotClient.wait_for_nav(timeout=)`, `.navigate_to(x, y, timeout=) -> TaskResult`, `TaskResult.state`, `TaskState.{SUCCEEDED,BLOCKED,FAILED,CANCELED}`, `robodog_sdk.testing.FakeNav` (`.goals`, `.result_state`).
- Produces: `examples/guide/goto.py` defining `GotoConfig(NodeConfig)` (fields `x: float = 1.0`, `y: float = 0.5`, `timeout: float = 120.0`) and `class Goto(Node)` handling all four outcomes.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_guide_examples.py` (add `import goto` and extend the robodog imports with `TaskState`; add `from robodog_sdk.testing import FakeNav` alongside `FakeStack`):

```python
async def test_goto_submits_the_goal_and_finishes() -> None:
    async with harness() as h:
        await h.start_node(FakeStack)
        nav = await h.start_node(FakeNav)
        await h.start_node(goto.Goto, config=goto.GotoConfig(x=2.0, y=0.5, timeout=5.0))

        for _ in range(50):
            if nav.goals:
                break
            await asyncio.sleep(0.05)

        assert len(nav.goals) == 1, "exactly one goal should have been submitted"


async def test_goto_reports_blocked_without_crashing() -> None:
    async with harness() as h:
        await h.start_node(FakeStack)
        nav = await h.start_node(FakeNav)
        nav.result_state = TaskState.BLOCKED
        node = await h.start_node(goto.Goto, config=goto.GotoConfig(timeout=5.0))

        for _ in range(50):
            if node.result is not None:
                break
            await asyncio.sleep(0.05)

        assert node.result is not None
        assert node.result.state is TaskState.BLOCKED
```

- [ ] **Step 2: Run to verify failure** — expect `ModuleNotFoundError: No module named 'goto'`.

- [ ] **Step 3: Write the example**

Create `examples/guide/goto.py`:

```python
"""Send the robot somewhere and handle every way that can end.

    uv run python examples/guide/goto.py

A navigation goal is a *task*: you submit it, the stack works on it, and it
ends in exactly one of four states. Only SUCCEEDED means the robot arrived.
BLOCKED is not an error — the robot met the world and stopped trying.
"""

from __future__ import annotations

from zenode import Node, NodeConfig, run

from robodog_sdk import RobotClient, TaskResult, TaskState


class GotoConfig(NodeConfig):
    #: Goal position in the map frame, in meters.
    x: float = 1.0
    y: float = 0.5
    #: Seconds to wait for the task before giving up on it.
    timeout: float = 120.0


class Goto(Node):
    name = "goto"
    config: GotoConfig

    robot: RobotClient
    #: The task's outcome, kept for inspection (and for the guide's tests).
    result: TaskResult | None = None

    async def on_start(self) -> None:
        self.robot = RobotClient(self)
        self.spawn(self._run(), name="goto")

    async def _run(self) -> None:
        try:
            await self.robot.wait_for_nav(timeout=5.0)
        except TimeoutError:
            self.log.error("no navigation coordinator answered — is the stack up?")
            self.stop()
            return

        self.result = await self.robot.navigate_to(
            self.config.x, self.config.y, timeout=self.config.timeout
        )

        if self.result.state is TaskState.SUCCEEDED:
            self.log.info("arrived")
        elif self.result.state is TaskState.BLOCKED:
            self.log.warning("blocked on the way: %s", self.result.message)
        elif self.result.state is TaskState.CANCELED:
            self.log.warning("someone canceled the task: %s", self.result.message)
        else:  # TaskState.FAILED
            self.log.error("navigation failed: %s", self.result.message)
        self.stop()


def cli() -> None:
    run(Goto)


if __name__ == "__main__":
    cli()
```

- [ ] **Step 4: Run tests** — `uv run pytest`, expected: all pass (fix-against-real-API rule applies).

- [ ] **Step 5: Write the chapter**

Structure and mandatory content for `docs/guide/06-navigation.md`:

- H1: `Navigation tasks`
- "In this chapter" box: send the robot to a position from code; handle every outcome; watch a task's progress.
- Prerequisites: chapters 2–5; the appliance up.
- Section `You already did this in the browser` — open by connecting to chapter 2's nav UI: clicking the map submitted a *task*; this chapter does the identical thing from code, and the browser remains the control experiment when code misbehaves.
- Section `A task ends in one of four states` — `{literalinclude}` of `goto.py`; facts: `navigate_to` submits and waits; `SUCCEEDED` is the only arrival; `BLOCKED` means the robot met the world and gave up trying (an outcome to handle, not an exception); `FAILED`/`CANCELED` round it out. Check the result — never assume arrival.
- Section `While it runs` — facts: feedback on `robot.state.nav.value` (`TaskFeedback`); `state` is `RUNNING` for the whole task — the field that moves is `activity` (`cruising`, `aligning`, `stalled`, `retreating`); a stall is transient, the skill is still trying; `robot.navigating` tells you a task is under way.
- Section `One task at a time` — facts: no queue; a second goal is refused while one runs, `navigate_to` raises `PermissionError`; `preempt=True` cancels the running task first; to branch instead of catch, `await robot.submit(goal)` and read `handle.accepted` / `handle.reason`. Point at `examples/navigate.py` (repo link) for the full two-stage pattern including `wait_for_task`, `cancel_task` and a feedback watcher.
- Section `Stored positions belong to a map` — facts: a map-frame coordinate is only meaningful for the map it came from; store `robot.map_id()` beside any saved pose and refuse to drive when the ids differ; `map_id()` returns `None` for "no usable map", which never means "unchanged". Link `[navigation concepts](../concepts/navigation.md)`.
- Troubleshooting: `wait_for_nav` times out → nav service not up (compose logs); task immediately `FAILED` → is MOLA up / does the map exist (`🚧 TODO(fabian): what does nav report when MOLA is absent — exact failure mode for the troubleshooting box`).
- "Where to go next": chapter 7; concepts: navigation.

- [ ] **Step 6: Append `06-navigation` to the toctree, build** — expected: success.

- [ ] **Step 7: Commit**

```bash
git add examples/guide/goto.py tests/test_guide_examples.py docs/guide/06-navigation.md docs/guide/index.md
git commit -m "docs: add guide chapter 6 (navigation) with tested example"
```

---

### Task 9: Guide chapter 7 — Testing your node

**Files:**
- Modify: `tests/test_guide_examples.py` (append one battery-driven test, written to be literalincluded)
- Create: `docs/guide/07-testing.md`
- Modify: `docs/guide/index.md` (append `07-testing`)

**Interfaces:**
- Consumes: `FakeStack.set_battery(soc=, level=)`, `FakeStack.set_driver(...)`, `FakeStack.set_safety(...)`, `FakeStack.stopped`, `FakeNav` (`.result_state`, `.activity`), `robodog_sdk.BatteryLevel`, `wanderer.Wanderer` from Task 7.
- Produces: test function `test_wanderer_survives_a_battery_scare` in `tests/test_guide_examples.py`, literalincluded by the chapter via `:pyobject:`.

- [ ] **Step 1: Write the showcase test (it should pass immediately — it tests Task 7's node)**

Append to `tests/test_guide_examples.py` (add `BatteryLevel` to the robodog imports):

```python
async def test_wanderer_survives_a_battery_scare() -> None:
    """The chapter-7 showcase: fake state no desk can produce for real."""
    async with harness() as h:
        stack = await h.start_node(FakeStack)
        await h.start_node(
            wanderer.Wanderer,
            config=wanderer.WanderConfig(speed=0.3, distance=5.0),
        )

        stack.set_pose(x=0.0, y=0.0)
        stack.set_battery(soc=5, level=BatteryLevel.critical)
        await asyncio.sleep(SETTLE)

        # Wanderer ignores battery by design — the point is that YOUR node
        # can now see a critical battery without draining one.
        assert stack.last_command is not None, "still driving; battery was observable"
```

Run: `uv run pytest tests/test_guide_examples.py -v` — expected: PASS. If `set_battery`'s signature differs (check `src/robodog_sdk/testing.py`), fix the call here and keep the docstring.

- [ ] **Step 2: Write the chapter**

Structure and mandatory content for `docs/guide/07-testing.md`:

- H1: `Test your node without a robot`
- "In this chapter" box: run your node's logic in a test, in-process, no router, no simulation; fake situations that are hard to produce for real.
- Prerequisites: chapters 3–5 (uses `Wanderer`).
- Section `The test harness` — facts: `zenode.testing.harness()` runs nodes in one process with an in-memory transport — no router, no network, no appliance; `robodog_sdk.testing` plays the stack's side: `FakeStack` latches state and records every command your node publishes; `FakeNav` accepts goals, streams feedback and ends tasks wherever you tell it to.
- Section `A complete test` — literalinclude the Task 7 test from the test suite itself, so the docs show *real CI-run code*:

  ```markdown
  ```{literalinclude} ../../tests/test_guide_examples.py
  :pyobject: test_wanderer_drives_until_the_distance_is_covered
  :language: python
  ```
  ```

  Prose: walk the anatomy — start the fake, start your node, poke state (`set_pose`), sleep a settle interval, assert on what the fake recorded (`last_command`, `stopped`).
- Section `Situations you cannot arrange on a desk` — literalinclude `test_wanderer_survives_a_battery_scare` via `:pyobject:`; facts: `set_battery` fakes charge states, `set_driver(...)` fakes a human on the gamepad preempting you, `set_safety(...)` fakes the e-stop — including the safety source going silent, which stops the robot just as hard for a different reason; `nav.result_state = TaskState.BLOCKED` exercises your BLOCKED branch without an obstacle, `nav.activity = NavActivity.STALLED` fakes a mid-task stall.
- Section `Set it up in your own project` — steps: `uv add --dev pytest pytest-asyncio`, the two `pyproject.toml` lines (`asyncio_mode = "auto"`, `testpaths`), file layout, `uv run pytest`.
- `{note}`: these are stand-ins, not physics — nothing moves. "Does the robot actually get there" is a question for the simulation (chapter 2), not for the fakes.
- Troubleshooting: test hangs → a missing `await` or an unstarted fake; flaky timing → raise the settle interval, assert on behavior not latency.
- "Where to go next": chapter 8.

- [ ] **Step 3: Append `07-testing` to the toctree, build** — expected: success. Run `uv run pytest` — all pass.

- [ ] **Step 4: Commit**

```bash
git add tests/test_guide_examples.py docs/guide/07-testing.md docs/guide/index.md
git commit -m "docs: add guide chapter 7 (testing) backed by real CI tests"
```

---

### Task 10: Guide chapter 8 — Custom topics and message types (+ example + test)

**Files:**
- Create: `examples/guide/detections.py`
- Modify: `tests/test_guide_examples.py` (append test)
- Create: `docs/guide/08-custom-topics.md`
- Modify: `docs/guide/index.md` (append `08-custom-topics`)

**Interfaces:**
- Consumes: `zenode` `TopicSet`, `Topic`, `publish`, `every` (timer decorator — verify the exact import against zenode; the old tracing doc shows `@every(0.1)`), `pydantic.BaseModel`, harness `h.collect(topic)`.
- Produces: `examples/guide/detections.py` defining `class Detection(BaseModel)` (fields `label: str`, `confidence: float`, `x: float`, `y: float`), `class PerceptionTopics(TopicSet)` with `detections = Topic("perception/detections", Detection)`, publisher node `Detector`, consumer node `Alerter` (attribute `seen: list[Detection]`).

- [ ] **Step 1: Write the failing test**

Append to `tests/test_guide_examples.py` (add `import detections`):

```python
async def test_detections_flow_from_detector_to_alerter() -> None:
    async with harness() as h:
        alerter = await h.start_node(detections.Alerter)
        await h.start_node(detections.Detector)

        for _ in range(50):
            if alerter.seen:
                break
            await asyncio.sleep(0.05)

        assert alerter.seen, "the alerter should receive the detector's messages"
        assert alerter.seen[0].label == "ball"
```

- [ ] **Step 2: Run to verify failure** — expect `ModuleNotFoundError: No module named 'detections'`.

- [ ] **Step 3: Write the example**

Create `examples/guide/detections.py`:

```python
"""Define your own topic and message type — the contract pattern, for you.

    uv run python examples/guide/detections.py   # runs the detector

Everything the SDK does for the stack's topics you can do for your own:
a pydantic model as the payload schema, a Topic binding it to a key, and
publishers/subscribers on both ends that agree by construction.
"""

from __future__ import annotations

from pydantic import BaseModel
from zenode import Node, Topic, TopicSet, every, publish, run, subscribe


class Detection(BaseModel):
    """One detected object, in the robot's body frame."""

    label: str
    confidence: float
    x: float
    y: float


class PerceptionTopics(TopicSet):
    detections = Topic("perception/detections", Detection)


class Detector(Node):
    """Publishes a (pretend) detection twice a second."""

    name = "detector"

    async def on_start(self) -> None:
        self._out = publish(PerceptionTopics.detections)

    @every(0.5)
    async def tick(self) -> None:
        self._out.put(Detection(label="ball", confidence=0.9, x=1.2, y=0.1))


class Alerter(Node):
    """Reacts to detections — a stand-in for whatever your project does."""

    name = "alerter"

    seen: list[Detection]

    async def on_start(self) -> None:
        self.seen = []

    @subscribe(PerceptionTopics.detections)
    async def on_detection(self, msg: Detection) -> None:
        self.seen.append(msg)
        self.log.info("%s at (%.1f, %.1f)", msg.label, msg.x, msg.y)


def cli() -> None:
    run(Detector)


if __name__ == "__main__":
    cli()
```

- [ ] **Step 4: Run tests** — `uv run pytest`, all pass. If zenode's decorator/`publish` import paths differ, fix imports against zenode's actual API (check how `src/robodog_sdk/topics.py` and `examples/contract_drive.py` import them).

- [ ] **Step 5: Write the chapter**

Structure and mandatory content for `docs/guide/08-custom-topics.md`:

- H1: `Your own topics and message types`
- "In this chapter" box: define a message schema; declare a topic; publish and subscribe between your own nodes.
- Prerequisites: chapters 3, 7.
- Section `The pattern you have been using all along` — fact: `StateTopics`, `MotionTopics` etc. are nothing magical — a `TopicSet` binding keys to pydantic models; you get the identical machinery for your own data.
- Section `Schema, topic, nodes` — literalinclude `detections.py`; prose per piece: the pydantic model is the schema (validation on both ends — a malformed publish raises in the publisher's process, link `pydantic.ValidationError`); the `Topic` binds key+type; a second node in another project imports the same module and the two agree by construction. Mention topic options with one line each: `latched=True` (late subscribers get the last value — right for state), `max_age=` (commands that must be fresh), `trace=True` (chapter 9 covers tracing).
- Section `Naming keys` — `{tip}`, good-practice only (no mandate, per spec): keys live in the shared `robodog` namespace on the wire; start yours with a short project-specific prefix (`perception/…`, `team_orange/…`) so `zenode topics` output stays readable and nothing collides if two projects ever share a router.
- Section `See it on the wire` — `uv run zenode topics` and `uv run zenode topics --contract robodog_sdk.topics` to introspect; expected output sketch.
- Troubleshooting: subscriber silent though publisher runs → both sides must import the *same* Topic (same key string); serialization error → the model changed on one side only.
- "Where to go next": chapter 9; concepts: pub/sub, tracing.

- [ ] **Step 6: Append `08-custom-topics` to the toctree, build** — expected: success.

- [ ] **Step 7: Commit**

```bash
git add examples/guide/detections.py tests/test_guide_examples.py docs/guide/08-custom-topics.md docs/guide/index.md
git commit -m "docs: add guide chapter 8 (custom topics) with tested example"
```

---

### Task 11: Guide chapter 9 — Advanced control and the capstone (+ example + test)

**Files:**
- Create: `examples/guide/patrol.py`
- Modify: `tests/test_guide_examples.py` (append test)
- Create: `docs/guide/09-advanced-control.md`
- Modify: `docs/guide/index.md` (append `09-advanced-control`)

**Interfaces:**
- Consumes: everything prior, plus `RobotClient.motion_permitted()`, `.preempted_by`, `.hold_tilt(pitch_deg=)/.clear_tilt()`, `zenode.trace`.
- Produces: `examples/guide/patrol.py` — the capstone: `PatrolConfig(NodeConfig)` (field `waypoints: list[tuple[float, float]] = [(1.0, 0.0), (1.0, 1.0), (0.0, 1.0), (0.0, 0.0)]`, field `loops: int = 0` where 0 = forever) and `class Patrol(Node)` (attribute `completed: int` — waypoints reached).

- [ ] **Step 1: Write the failing test**

Append to `tests/test_guide_examples.py` (add `import patrol`):

```python
async def test_patrol_visits_the_waypoints_in_order() -> None:
    async with harness() as h:
        await h.start_node(FakeStack)
        nav = await h.start_node(FakeNav)
        node = await h.start_node(
            patrol.Patrol,
            config=patrol.PatrolConfig(waypoints=[(1.0, 0.0), (1.0, 1.0)], loops=1),
        )

        for _ in range(100):
            if node.completed >= 2:
                break
            await asyncio.sleep(0.05)

        assert node.completed == 2, "one loop over two waypoints"
        assert len(nav.goals) == 2, "one task per waypoint"


async def test_patrol_stops_the_route_when_a_leg_blocks() -> None:
    async with harness() as h:
        await h.start_node(FakeStack)
        nav = await h.start_node(FakeNav)
        nav.result_state = TaskState.BLOCKED
        node = await h.start_node(
            patrol.Patrol,
            config=patrol.PatrolConfig(waypoints=[(1.0, 0.0), (1.0, 1.0)], loops=1),
        )

        for _ in range(50):
            if nav.goals:
                break
            await asyncio.sleep(0.05)
        await asyncio.sleep(SETTLE)

        assert len(nav.goals) == 1, "a blocked leg must end the patrol, not skip ahead"
        assert node.completed == 0
```

- [ ] **Step 2: Run to verify failure** — expect `ModuleNotFoundError: No module named 'patrol'`.

- [ ] **Step 3: Write the example**

Create `examples/guide/patrol.py`:

```python
"""The guide's capstone: patrol a route, coexist with everything else.

    uv run python examples/guide/patrol.py

Everything from the guide in one node: navigation tasks in sequence, every
outcome handled, motion permission checked, and preemption by a human driver
respected — because on this robot you are never the only party involved.
"""

from __future__ import annotations

import asyncio

from zenode import Node, NodeConfig, run

from robodog_sdk import RobotClient, TaskState


class PatrolConfig(NodeConfig):
    #: Corners of the patrol route, map-frame meters, visited in order.
    waypoints: list[tuple[float, float]] = [(1.0, 0.0), (1.0, 1.0), (0.0, 1.0), (0.0, 0.0)]
    #: How many rounds to patrol; 0 means until stopped.
    loops: int = 0
    #: Seconds to allow per leg.
    leg_timeout: float = 120.0


class Patrol(Node):
    name = "patrol"
    config: PatrolConfig

    robot: RobotClient
    #: Waypoints reached so far (read by the guide's tests).
    completed: int = 0

    async def on_start(self) -> None:
        self.robot = RobotClient(self)
        self.spawn(self._patrol(), name="patrol")

    async def _patrol(self) -> None:
        try:
            await self.robot.wait_for_nav(timeout=5.0)
        except TimeoutError:
            self.log.error("no navigation coordinator — is the stack up?")
            self.stop()
            return

        rounds = 0
        while self.config.loops == 0 or rounds < self.config.loops:
            for x, y in self.config.waypoints:
                if not await self._drive_leg(x, y):
                    self.stop()
                    return
            rounds += 1
            self.log.info("round %d complete", rounds)
        self.stop()

    async def _drive_leg(self, x: float, y: float) -> bool:
        """Drive one leg; return False when the patrol should end."""
        # A tripped e-stop or a human on the gamepad outranks a patrol.
        # Wait rather than fight: priority is decided per command anyway.
        while not self.robot.motion_permitted():
            self.log.info("motion not permitted — waiting")
            await asyncio.sleep(1.0)
        if self.robot.preempted_by is not None:
            self.log.info("preempted by %s — waiting", self.robot.preempted_by.value)
            await asyncio.sleep(1.0)

        result = await self.robot.navigate_to(x, y, timeout=self.config.leg_timeout)
        if result.state is TaskState.SUCCEEDED:
            self.completed += 1
            self.log.info("reached (%.1f, %.1f)", x, y)
            return True
        self.log.warning(
            "leg to (%.1f, %.1f) ended %s: %s", x, y, result.state.value, result.message
        )
        return False


def cli() -> None:
    run(Patrol)


if __name__ == "__main__":
    cli()
```

- [ ] **Step 4: Run tests** — `uv run pytest`, all pass (fix-against-real-API rule; note `FakeStack` defaults must permit motion — if `motion_permitted()` is False by default in the harness, check `testing.py` for how `FakeStack` seeds safety state and adjust the example's wait or the test setup accordingly, keeping the wait loop in the example).

- [ ] **Step 5: Write the chapter**

Structure and mandatory content for `docs/guide/09-advanced-control.md`:

- H1: `Advanced control`
- "In this chapter" box: share the robot with other command sources; use postures; keep causality traceable; put it all together.
- Prerequisites: chapters 4–8.
- Section `You are not the only one commanding the robot` — facts: every command carries a `source`; the motion gateway forwards whichever *fresh* command has the highest rank — `controller` > `assisted_teleop` > `planner` > `autonomous`; your code defaults to `autonomous`, the bottom rank, so a human on the gamepad preempts you instantly and you resume automatically when they let go; there is no lock to take or release; `robot.preempted_by` tells you who currently outranks you (ignoring it is also valid); setting a higher source is *claiming to be* that source — only do it if you are that thing. `{warning}` on that last fact. Link `[motion concepts](../concepts/motion.md)`.
- Section `When commands go out and nothing moves` — facts: read `robot.state.gateway` — `active_source` (who won), `action`/`active_zones` (what the gateway did to their command), `watchdog_tripped` (the winner went silent); a breached stop zone strips only the velocity component heading into the obstacle — the robot can still turn or reverse out; `robot.blocked_by_zone` lists the zones currently shaping your commands.
- Section `Postures: tilt and holds` — facts with a short inline (untested) fragment: `robot.tilt(pitch_deg=10)` applies for one control frame and relaxes (the robot neutralizes it — not the deadman; the tilt key has no expiry); `robot.hold_tilt(pitch_deg=10.0)` keeps re-asserting at 10 Hz until `clear_tilt()`; `async with robot.tilting(...)` restores the previous hold on exit. `{warning}`: the tilt key bypasses the gateway — no arbitration, no collision cover; two nodes holding different tilts fight silently, last write wins each frame.
- Section `Keeping the causal chain` — facts: messages your handlers cause are traced automatically (`put`, `call`, `spawn`, `blocking`); a timer body is caused by the clock, so it starts *outside* any trace — the sense-then-act-via-timer shape loses the link; the fix, with the exact short fragment: store `(msg, trace.current())` in the handler, wrap the timer's publish in `with trace.using(traceparent):`; `robot.driving()`'s pump is clock-driven too — prefer `robot.move()` inside a handler when the chain matters; follow a chain with `uv run zenode trace <id>` and `uv run zenode logs --trace <id>`. Link `[tracing concepts](../concepts/tracing.md)`.
- Section `The capstone: a patrol node` — literalinclude `patrol.py`; prose: point out where each earlier chapter appears (tasks & outcomes ← ch. 6, motion permission & preemption ← this chapter, config ← ch. 4, and its tests live in the suite ← ch. 7). Invite modification: add a `hold_tilt` "look around" at each corner; publish a `Detection` (ch. 8) when something is seen.
- Section `Splitting into several nodes` — facts: one node per concern is the stack's own pattern; nodes find each other only through topics, so splitting is free — same `zenode.toml`, run each with its own `uv run` process; the harness starts several nodes in one test exactly as chapter 7 showed.
- "Where to go next": the Concepts section and the Reference; you are done with the guide.
- `{note}` at the chapter top: an alternative capstone (turtle-style shape-driving demo) was considered; if preferred later, it replaces this section — the spec allows either.

- [ ] **Step 6: Append `09-advanced-control` to the toctree, build** — expected: success.

- [ ] **Step 7: Commit**

```bash
git add examples/guide/patrol.py tests/test_guide_examples.py docs/guide/09-advanced-control.md docs/guide/index.md
git commit -m "docs: add guide chapter 9 (advanced control) with tested capstone"
```

---

### Task 12: Concepts — architecture, pub/sub, asyncio

**Files:**
- Create: `docs/concepts/architecture.md`
- Create: `docs/concepts/pubsub.md`
- Create: `docs/concepts/async-python.md`
- Modify: `docs/concepts/index.md` (toctree: the three pages)
- Modify: `docs/guide/01-big-picture.md`, `docs/guide/02-setup.md` (restore any deferred links per the Task 3 fallback rule)

**Interfaces:**
- Produces: the three concept pages every guide chapter links to.

- [ ] **Step 1: Write `architecture.md`**

Mandatory content (facts verified against robodog-digipro source during brainstorming):

- One-paragraph plain-language summary first.
- The process roster, one short subsection per process, each stating what it does and its key topics: **robot bridge / simulation** (`system_state/highstate|odometry|battery|motor`, camera and LiDAR sensor topics; the sim covers the motion/sensor surface but not battery), **motion gateway** (consumes the command inlet, publishes the arbitrated `command/motion/move`, `motion/gateway/status`, collision events), **safety** (`safety/state`, e-stop shim), **navigation coordinator** (task submit/feedback/result, costmaps, path; sends motion requests into the gateway inlet), **MOLA SLAM** (consumes the Livox point cloud over Zenoh; publishes `localization/pose`, `localization/map_identity`, `map/grid`), **system-state** (aggregate `system_state/system`), **joy** (gamepad → commands at `controller` rank), **nav web UI** (submits nav tasks from the browser).
- The identity statement: the appliance from chapter 2 and the Jetson on the dog run the same processes speaking the same topics — your code cannot tell them apart, by design.
- Comment slot: `<!-- diagram: architecture.svg inserted in the diagram task -->` (shared image with guide/01).
- Where each process's messages are specified: link `[Topic reference](../reference/topics.md)` (fallback rule until Task 15).

- [ ] **Step 2: Write `pubsub.md`**

Mandatory content:

- Summary paragraph: programs that never call each other, only publish and subscribe; who is running, where they run, and how many there are is invisible to your code.
- `Keys and the namespace` — keys in the contract are relative (`system_state/odometry`); the `namespace` from `zenode.toml` is prefixed on the wire (`robodog/system_state/odometry`); the deployment's namespace is `robodog`, a fixed fact; the failure mode of any other value (silence, no error) and the `zenode nodes` check. Comment slot: `<!-- diagram: pubsub.svg inserted in the diagram task -->`
- `Latched topics` — a latched topic re-delivers its last value to late subscribers; that is why state topics (odometry, battery, safety) answer immediately while command topics do not.
- `Commands expire` — `max_age` on a topic means consumers ignore anything older; the movement inlet's 0.3 s is the deadman (link to guide ch. 4); age is judged across machines → synchronized clocks.
- `Services` — some interactions are request/response (submitting a nav task, asking task status); zenode calls these services; the SDK wraps the ones you need (`navigate_to`, `task_status`), so you meet them as awaits, not as a new API to learn.
- `Seeing the wire` — `uv run zenode topics --contract robodog_sdk.topics`, `zenode nodes`, `zenode health`; `CONTRACT_VERSION` rides on each node's health heartbeat, so a version skew between your project and the deployed stack shows up in `zenode health` rather than as a parse error somewhere else.

- [ ] **Step 3: Write `async-python.md`**

Mandatory content (new authorship — scoped to "asyncio as met through zenode", per the spec's non-goals):

- Summary: why everything here is `async def` — a node does many things at once (handlers, timers, background jobs) on one thread; the event loop switches between them at every `await`.
- `The one rule: never block` — the mistake treated at length: `time.sleep`, heavy loops, blocking I/O freeze *every* handler in the node — subscriptions stall, the deadman trips, the robot stops (tie the abstract mistake to its very concrete robot symptom). Correct forms: `await asyncio.sleep(...)`; for genuinely blocking work `await self.blocking(fn, ...)` (zenode runs it off-thread — verify exact signature against zenode docs when writing).
- `Handlers, timers, and spawned jobs` — the three ways code runs in a node: `@subscribe` (a message arrived), `@every` (the clock), `self.spawn(coro, name=...)` (a background job owned by the node, canceled on stop); which the guide used where.
- `Waiting for several things` — `asyncio.gather` for parallel awaits; `asyncio.wait_for`/`timeout=` parameters for bounding waits (the SDK's own `timeout=` parameters are this).
- `What you do not need` — explicit loop management, `asyncio.run`, threads: `zenode.run(Node)` owns the loop; say so to stop students from cargo-culting event-loop code from the internet.
- Comment slot: `<!-- diagram: first-node-sequence.svg inserted in the diagram task -->`

- [ ] **Step 4: Toctree, restore deferred links, build**

`docs/concepts/index.md` toctree gains `architecture`, `pubsub`, `async-python` (this order). Restore any links deferred by the Task 3/4 fallback rule. Run the build — expected: success.

- [ ] **Step 5: Commit**

```bash
git add docs/concepts/architecture.md docs/concepts/pubsub.md docs/concepts/async-python.md docs/concepts/index.md docs/guide/01-big-picture.md docs/guide/02-setup.md
git commit -m "docs: add architecture, pubsub and asyncio concept pages"
```

---

### Task 13: Concepts — motion and safety

**Files:**
- Create: `docs/concepts/motion.md`
- Create: `docs/concepts/safety.md`
- Modify: `docs/concepts/index.md` (append `motion`, `safety`)

**Interfaces:**
- Produces: the two mechanism pages the driving/advanced chapters link to.

- [ ] **Step 1: Write `motion.md`**

Mandatory facts (all from the old `driving.md`, re-explained per style rules):

- Summary paragraph, then comment slot `<!-- diagram: motion-flow.svg inserted in the diagram task -->`.
- `Two supported ways to command` — the contract (`MotionTopics` + `MovementCommand` via `publish`) and `RobotClient` are the same wire messages, same priority; the client is a convenience facade, not a privileged channel; dropping to the contract is fully supported (point at `examples/client_drive.py` vs `examples/contract_drive.py` — diffing them shows exactly what the client adds).
- `The deadman` — `COMMAND_MAX_AGE = 0.3 s` on the movement inlet; stop publishing → robot stops; `driving()` republishes at 10 Hz; cross-host age ⇒ NTP/chrony requirement.
- `Arbitration` — one inlet for all sources; the gateway forwards the freshest command with the highest-ranking `MovementSource`: `controller` > `assisted_teleop` > `planner` > `autonomous`; no lock exists — priority rides on every frame; preemption and automatic resumption follow; `source` defaults to `autonomous`; a higher `source` is a claim to *be* that source (`{warning}`).
- `The gateway's own report` — `motion/gateway/status`: `active_source`, `action`, `active_zones`, `watchdog_tripped`; published on change, re-asserted about once a second — a stale value means the gateway itself is gone.
- `Collision zones shape commands` — `GatewayAction.stop` is directional: only the velocity component toward the obstacle is stripped; full zeroing happens only for a surrounding obstacle, a stale LiDAR scan, or a tripped watchdog.
- `Velocity limits` — `MovementCommand` validates against `robodog_sdk.limits`; out-of-range raises `pydantic.ValidationError` in *your* process; a wrong limit is fixed in `limits.py`, not worked around.
- `Postures are different` — tilt bypasses the gateway entirely: no arbitration, no collision cover, no deadman; single `tilt()` lasts one control frame (robot neutralizes); `hold_tilt` re-asserts at 10 Hz, publishes nothing while the setpoint is zero, `clear_tilt()` sends one leveling frame then goes quiet; `tilting()` restores the previous hold on exit; concurrent holders fight silently at 10 Hz (`{warning}`).

- [ ] **Step 2: Write `safety.md`**

Mandatory facts (from old `safety.md`):

- Summary paragraph, then comment slot `<!-- diagram: safety-chain.svg inserted in the diagram task -->`.
- `Hardware latches, software does not` — `robot.emergency_stop()` publishes a cancel event that safety node, nav coordinator and fleet bridge each act on (robot zeroed, task canceled, order runtime wiped); it does not latch and has no software counterpart — only the physical switch latches, and only the release press on the panel clears it.
- `Ask motion_permitted()` — the latch drops one phase before the robot can move (deliberately, so the bridge can stand it back up); `motion_permitted(within=...)` closes that gap and fails safe on silence: a safety latch that stopped arriving reads exactly like one saying "stopped" — which is why it takes a freshness window instead of being a property. Contrast with reading `state.safety.value.estop` directly (don't).
- `Zones shape, they do not own` — cross-link the directional-stop fact in `motion.md`; `robot.blocked_by_zone` for the current shaping zones.
- `What this means for your node` — the pattern the capstone used: check `motion_permitted()` before starting motion; treat denial as "wait", not "error".

- [ ] **Step 3: Toctree, build** — append `motion`, `safety`; expected: success.

- [ ] **Step 4: Commit**

```bash
git add docs/concepts/motion.md docs/concepts/safety.md docs/concepts/index.md
git commit -m "docs: add motion and safety concept pages"
```

---

### Task 14: Concepts — navigation and tracing

**Files:**
- Create: `docs/concepts/navigation.md`
- Create: `docs/concepts/tracing.md`
- Modify: `docs/concepts/index.md` (append `navigation`, `tracing`)

**Interfaces:**
- Produces: the remaining two concept pages.

- [ ] **Step 1: Write `navigation.md`**

Mandatory facts (from old `navigation.md`):

- Summary paragraph, then comment slot `<!-- diagram: nav-lifecycle.svg inserted in the diagram task -->`.
- `Task lifecycle` — submit → accepted/refused; while running, `TaskFeedback.state` is `RUNNING` and never anything else — the terminal verdict lives only on the result key, so the two can never disagree; `activity` is the moving field (`cruising`, `aligning`, `stalled`, `retreating`); a stall is transient; only a result carrying `BLOCKED` means the skill gave up.
- `The four outcomes` — `SUCCEEDED` (arrival — the only one), `BLOCKED` (met the world; an outcome, not an error), `FAILED`, `CANCELED`.
- `One task at a time` — no queue; refusal semantics; `preempt=True` cancels-then-submits; `navigate_to` raises `PermissionError` on refusal, `submit()`+`handle.accepted` to branch instead.
- `E-stop policy` — a task nobody is awaiting is discarded on e-stop by default (nobody wants a route resuming minutes after a human hit the button); `on_estop=EstopPolicy.HOLD` only when this process owns the mission and will handle recovery.
- `Asking about tasks` — `task_status()` answers with a real state for a task the coordinator remembers (including `RUNNING` — check `state.is_terminal`) and raises for one it never heard of or has evicted: "unknown" is not a lifecycle state. **Verify and name the actual exception type raised** (check `RobotClient.task_status` in `client.py:750` and what zenode's service layer raises — the old docs said `ServiceError`, which does not exist in this package; the errors reference (Task 15) must agree with what this page says.)
- `Map identity` — a map-frame coordinate is valid only for the map it came from; store `robot.map_id()` beside saved poses, refuse on mismatch; `None` means "no usable map" (SLAM down, odometry fallback, nothing published) and never "unchanged".

- [ ] **Step 2: Write `tracing.md`**

Mandatory facts (from old `tracing.md`):

- Summary: your node is traced without asking; when a command spans four processes, one id follows it.
- `Where traces start` — the causal-chain roots: `system_state/odometry` and `localization/pose`, sampled at 1 % (`TRACE_RATIO`); everything a handler causes stays in the trace automatically (`put()`, `await self.call()`, `self.spawn()`, `await self.blocking()`); nothing to configure.
- `Service calls join, they do not start` — a task submitted from a plain script has no trace; one submitted inside a handler belongs to the trace of what triggered the handler.
- `Following one message` — `uv run zenode logs --trace <id>`, `uv run zenode trace <id>`; both work with no collector; spans optional via `zenode[otel]`; cost ≈ 3.6 µs traced vs 1.9 µs untraced per `put()`, untraced topics unaffected.
- `Timers break the chain` — the clock causes the timer body, so it runs outside any trace; the sense-then-act shape and its fix (capture `trace.current()` in the handler, `with trace.using(...)` in the timer) with both code fragments from the guide restated in full; `examples/contract_drive.py` does exactly this; `RobotClient.driving()`'s pump is clock-driven too — `robot.move()` in a handler preserves the chain.
- `Your own topics` — `trace=True` on the topic that *starts* a chain, `trace_ratio=` to sample streams; marking downstream topics is harmless (a topic only starts a trace when none is active), and `trace_ratio` takes effect only on the topic that actually started the trace.

- [ ] **Step 3: Toctree, build** — append `navigation`, `tracing`; expected: success. Also restore any remaining deferred concept links in guide chapters.

- [ ] **Step 4: Commit**

```bash
git add docs/concepts/navigation.md docs/concepts/tracing.md docs/concepts/index.md
git commit -m "docs: add navigation and tracing concept pages"
```

---

### Task 15: Reference — topics, errors, API pages (replaces docs/api/)

**Files:**
- Create: `docs/reference/topics.md`
- Create: `docs/reference/errors.md`
- Create: `docs/reference/client.md`
- Create: `docs/reference/messages.md`
- Create: `docs/reference/testing.md`
- Modify: `docs/reference/index.md` (toctree)
- Delete: `docs/api/index.rst`, `docs/api/client.rst`, `docs/api/contract.rst`, `docs/api/msgs.rst`, `docs/api/testing.rst`
- Modify: `docs/index.md` (remove `api/index` from the root toctree)

**Interfaces:**
- Consumes: the existing `docs/api/*.rst` autodoc directives (port their module/member lists — read them before deleting).
- Produces: the complete reference section. The old `api/` pages are deleted *in this task* (autodoc'ing the same module from two pages breaks `-W` with duplicate-description warnings).

- [ ] **Step 1: Write `topics.md` (the per-topic reference)**

Read `src/robodog_sdk/topics.py` in full. For every `Topic` in every `TopicSet` (`MotionTopics`, `PoseTopics`, `ControlTopics`, `SafetyTopics`, `InputTopics`, `StateTopics`, `LocalizationTopics`, `MapTopics`, `NavTopics`, `NavServices`), emit one entry under an H2 per topic group, using exactly this shape:

```markdown
### `system_state/odometry` — {class}`~robodog_sdk.msgs.system_state.OdometryState`

| Direction | Latched | Expiry | Published by |
|---|---|---|---|
| robot → you | yes | — | bridge / simulation |

**What it's for:** The robot's position and velocity in the odometry frame.

**Details:** 🚧 TODO(fabian): update rate on the real robot vs the simulation?
```

Rules: *Direction* is one of `robot → you`, `you → robot`, `stack-internal`, `service`; *Latched*/*Expiry*/trace facts come from the `Topic(...)` declaration (do not guess — read each declaration); *Published by* comes from this verified mapping: bridge/sim → `system_state/*` (battery/motor/highstate: bridge only, not sim), sensor topics; motion gateway → `command/motion/move`, `motion/gateway/status`, `motion/collision/event`; safety node → `safety/state`, `system_state/releasebutton`; nav coordinator → `nav/*` (costmaps, path, per-task feedback/result); MOLA → `localization/pose`, `localization/map_identity`, `map/grid`; joy → gamepad topics; system-state → `system_state/system`; your code → `command/*` inlet topics. For anything not covered by that mapping, write a `🚧 TODO(fabian):` slot naming the topic. *What it's for* is one sentence you write from the topic's docstring/comment in `topics.py` and the old docs' facts. Also document the module constants at the top of the page: `COMMAND_MAX_AGE` (0.3 s, the deadman), `TRACE_RATIO` (0.01), `CONTRACT_VERSION`.

- [ ] **Step 2: Write `errors.md`**

Content (verified against source during planning — re-verify line numbers before writing):

- Intro fact: the SDK defines no exception classes of its own; you meet Python built-ins and pydantic's.
- One H2 per exception, each with *raised by* and *what it means / what to do*:
  - `pydantic.ValidationError` — constructing any message with invalid data, including movement values outside the robot's capability envelope (`robodog_sdk.limits`); fix the value, don't work around the model.
  - `PermissionError` — `navigate_to` when a task is already running and `preempt` is false (use `preempt=True` or `submit()` + `handle.accepted`).
  - `TimeoutError` — `wait_for_nav` (no coordinator answered), `wait_for_task`/`navigate_to` past `timeout=` (the *wait* timed out, not the task — cancel explicitly if you want the task gone).
  - `ValueError` — `wait_until_ready()` with no node names; `NavigateThroughPosesGoal` validator violations (dwell list length, negative dwell) — these surface wrapped in `ValidationError`.
  - `LookupError` — `FakeNav.task_status` for an unknown task id (test double).
  - The exception `task_status()` raises for unknown/evicted tasks against the real coordinator — whatever Task 14's verification found; name it and cross-link the navigation concept page.

- [ ] **Step 3: Write the autodoc pages**

Each is a thin MyST page wrapping the same autodoc directives the old `.rst` files used (open each old file and port its module list and options exactly — e.g. `docs/api/msgs.rst` lists the msgs submodules with `:members:`). Shape:

````markdown
# RobotClient

```{eval-rst}
.. automodule:: robodog_sdk.client
   :members:
   :show-inheritance:
```
````

`client.md` ← old `client.rst`; `messages.md` ← old `msgs.rst` (all `robodog_sdk.msgs.*` submodules) **plus** old `contract.rst`'s `robodog_sdk.topics` / `robodog_sdk.frames` / `robodog_sdk.limits` sections if they are autodoc (read it — if `contract.rst` autodocs `topics.py`, keep that in `messages.md` under an H2 or give it its own brief section; the human-written per-topic page from Step 1 stays the primary topics page); `testing.md` ← old `testing.rst`.

- [ ] **Step 4: Delete `docs/api/`, update toctrees, build**

`docs/reference/index.md` toctree: `topics`, `client`, `messages`, `testing`, `errors`. Remove `api/index` from `docs/index.md`'s root toctree. Delete the five `.rst` files. Restore deferred `[Topic reference]` links in guide chapters 5 and concepts/architecture.

Run: `uv run --group docs sphinx-build -W docs docs/_build/html`
Expected: success — in particular no duplicate-object warnings and no orphan warnings.

- [ ] **Step 5: Commit**

```bash
git add -A docs/reference docs/api docs/index.md docs/guide docs/concepts
git commit -m "docs: add topic, error and API reference; retire docs/api"
```

---

### Task 16: Cutover — new landing page, remove old pages, redirects, README

**Files:**
- Modify: `docs/index.md` (full rewrite)
- Delete: `docs/driving.md`, `docs/navigation.md`, `docs/safety.md`, `docs/tracing.md`, `docs/testing.md`
- Modify: `docs/conf.py` (fill `redirects`)
- Modify: `README.md` (docs table)

**Interfaces:**
- Consumes: every page from Tasks 2–15 (all links must resolve).
- Produces: the finished site structure.

- [ ] **Step 1: Rewrite the landing page**

`docs/index.md` — full content plan:

- H1 `robodog-sdk`; hidden toctree with exactly `guide/index`, `concepts/index`, `reference/index`.
- One short paragraph: what the SDK is (the Python package your program uses to control the Robodog — a Unitree Go2 driven by a control stack you talk to over the network), who it's for (students building on the robot), built on zenode (link).
- A `{grid}` (sphinx-design) of three link cards: **Guide** ("New here? Start at chapter 1 — from empty laptop to your code driving the robot"), **Concepts** ("How the system works under the hood"), **Reference** ("Every topic, class and exception").
- Install section — the two commands with `@v%%SDK_VERSION%%` (base and `[livox]` extra), one sentence each; the versioning fact in one line: semantic versioning, `0.x` may move keys between minor versions — pin the tag shown here.
- License section — Apache-2.0, LICENSE/NOTICE links, copyright Hochschule Esslingen (same links as the old page).
- Nothing else: no namespace essay (lives in guide ch. 3 + concepts/pubsub), no first-node code (guide ch. 3), no contract introspection (guide ch. 8 / concepts/pubsub).

- [ ] **Step 2: Delete the five old pages and fill the redirects**

In `docs/conf.py`:

```python
# Old page URLs → new homes, so links from course material and the stack
# repo's docs keep working.
redirects = {
    "driving": "concepts/motion.html",
    "navigation": "concepts/navigation.html",
    "safety": "concepts/safety.html",
    "tracing": "concepts/tracing.html",
    "testing": "guide/07-testing.html",
    "api/index": "reference/index.html",
    "api/client": "reference/client.html",
    "api/msgs": "reference/messages.html",
    "api/contract": "reference/topics.html",
    "api/testing": "reference/testing.html",
}
```

Delete the five old `.md` pages.

- [ ] **Step 3: Update README**

In `README.md`, find the documentation table/links section and update targets: Guide → `https://hse-deb-algo-athlets.github.io/robodog-sdk/guide/`, Concepts, Reference accordingly; remove rows pointing at deleted pages; add one line about `sim/compose.yaml` ("run the simulated robot: see the Guide, chapter 2"). Keep the README's own tone; only the pointers change.

- [ ] **Step 4: Verify**

Run: `uv run --group docs sphinx-build -W docs docs/_build/html`
Expected: success.

Run: `ls docs/_build/html/driving.html && grep -o 'url=[^"]*' docs/_build/html/driving.html`
Expected: the file exists and contains `url=concepts/motion.html` (a redirect stub).

Run: `uv run pytest` — all pass.

- [ ] **Step 5: Commit**

```bash
git add -A docs README.md
git commit -m "docs: cut over to the new structure with redirects from old URLs"
```

---

### Task 17: Diagrams A — HSE brand profile, architecture, pub/sub, first-node sequence

> **Execution note:** run this task and Task 18 INLINE in the main session, not in a subagent — they invoke the `diagram-design` plugin skills and need web access for brand onboarding.

**Files:**
- Create: `docs/_static/architecture.svg` (+ the diagram-design HTML source next to it or under `docs/_static/diagrams/`)
- Create: `docs/_static/pubsub.svg`
- Create: `docs/_static/first-node-sequence.svg`
- Modify: `docs/guide/01-big-picture.md`, `docs/concepts/architecture.md`, `docs/concepts/pubsub.md`, `docs/concepts/async-python.md`, `docs/guide/03-first-project.md` (replace the `<!-- diagram: … -->` slots with images)

**Interfaces:**
- Produces: a saved diagram-design brand profile (HSE) reused by Task 18; three SVGs referenced via `![…](/_static/….svg)` with meaningful alt text.

- [ ] **Step 1: Onboard the brand** — invoke the `diagram-design:diagram-design` skill and onboard brand tokens from `https://www.hs-esslingen.de/`; save as a client profile (via `diagram-design:profile`) named `hse`. Constraint to carry into every diagram: backgrounds transparent or theme-neutral, all strokes/text legible on both Furo light (`#fff`-ish) and dark (`#131416`-ish) backgrounds — if HSE's palette fails contrast on dark, keep HSE hues for fills and use theme-safe neutral strokes/text.
- [ ] **Step 2: Architecture diagram** — content per spec: the appliance/stack processes from `concepts/architecture.md` (bridge/sim, gateway, safety, nav, MOLA, system-state, joy, nav UI) around a central Zenoh router, with "your node" visually distinct and outside the stack boundary; a caption-level cue that the same picture holds for the real dog (Jetson) and the laptop (compose). Export via `diagram-design:export-diagram` to `docs/_static/architecture.svg`.
- [ ] **Step 3: Pub/sub diagram** — key anatomy (`robodog` + `/` + `system_state/odometry`), one publisher → topic → N subscribers decoupling, latched vs streaming distinction. Export to `docs/_static/pubsub.svg`.
- [ ] **Step 4: First-node sequence diagram** — sequence: `uv run` → node starts → subscribes → sim publishes odometry → handler runs → log line; matches guide ch. 3's code exactly (same names). Export to `docs/_static/first-node-sequence.svg`.
- [ ] **Step 5: Insert the images** — replace each `<!-- diagram: … -->` slot with `![<one-sentence alt text describing the diagram's content>](/_static/<name>.svg)`; guide/01 and concepts/architecture share `architecture.svg`.
- [ ] **Step 6: Build** — `uv run --group docs sphinx-build -W docs docs/_build/html`; expected: success, images present in `_build/html/_static/`. Open one page and eyeball both themes.
- [ ] **Step 7: Commit**

```bash
git add docs/_static docs/guide docs/concepts
git commit -m "docs: add HSE-branded architecture, pubsub and sequence diagrams"
```

---

### Task 18: Diagrams B — motion flow, navigation lifecycle, safety chain

> **Execution note:** inline in the main session (see Task 17).

**Files:**
- Create: `docs/_static/motion-flow.svg`, `docs/_static/nav-lifecycle.svg`, `docs/_static/safety-chain.svg` (+ sources)
- Modify: `docs/concepts/motion.md`, `docs/concepts/navigation.md`, `docs/concepts/safety.md` (replace slots)

**Interfaces:**
- Consumes: the `hse` diagram-design profile from Task 17.

- [ ] **Step 1: Motion flow** — sources (controller / assisted_teleop / planner / autonomous, ranked visually) → one inlet → gateway (arbitration: freshest + highest rank; collision-zone shaping; watchdog) → robot; the deadman annotated on the inlet (0.3 s). Export to `docs/_static/motion-flow.svg`.
- [ ] **Step 2: Navigation lifecycle** — state machine: submitted → (refused | accepted) → RUNNING (activity badges: cruising/aligning/stalled/retreating) → the four terminal outcomes, SUCCEEDED visually distinct. Export to `docs/_static/nav-lifecycle.svg`.
- [ ] **Step 3: Safety chain** — hardware button (latches; release on panel) vs `emergency_stop()` (event: safety node + nav coordinator + fleet bridge each act; no latch); the `motion_permitted()` gap annotated. Export to `docs/_static/safety-chain.svg`.
- [ ] **Step 4: Insert images, build, commit**

```bash
git add docs/_static docs/concepts
git commit -m "docs: add motion, navigation and safety diagrams"
```

---

### Task 19: Fact-preservation audit and final verification

**Files:**
- Modify: any page found lacking (fixes only)

**Interfaces:**
- Consumes: the old pages via git history: `git show dfc20aa:docs/driving.md` (same for `navigation.md`, `safety.md`, `tracing.md`, `testing.md`, `index.md`).

- [ ] **Step 1: Audit** — for each old page, list every technical claim (each heading's facts) and check it appears somewhere in the new tree. The plan's Tasks 12–14 enumerate the intended homes; anything missing is a bug — add it to the right page. Explicitly confirm these easy-to-lose facts landed: cross-host age ⇒ NTP; gateway status re-asserted ~1 s / stale ⇒ gateway gone; directional stop semantics; hold_tilt publishes nothing at zero setpoint; `tilting()` restores the previous hold; service calls join traces rather than start them; trace cost numbers; `EstopPolicy.HOLD` condition; `map_id()` `None` semantics; `CONTRACT_VERSION` on the health heartbeat; the namespace failure mode (silence, no error).
- [ ] **Step 2: TODO inventory** — run `grep -rn "TODO(fabian)" docs sim` and verify every hit states a concrete question. Print the list in the task report for Fabian.
- [ ] **Step 3: Final verification** — run all three, expect success:

```bash
uv run --group docs sphinx-build -W docs docs/_build/html
uv run pytest
uv run pyright
```

(`pyright` covers the new example files; fix any typing complaints in `examples/guide/`.)

- [ ] **Step 4: Commit fixes**

```bash
git add -A docs examples tests
git commit -m "docs: fact-preservation audit fixes"
```

---

## Out of scope (tracked, not in this plan)

- **digipro-side:** Dockerfile + CI publish job for `robodog-sim-stack`, amd64 build of the MOLA image, pinning real image tags into `sim/compose.yaml` (three `🚧 TODO(fabian)` markers there), nav-map port confirmation, macOS native-sim verification on the prof's machine.
- Screenshot of the nav UI for guide ch. 2 (needs the running appliance).
