# Test your node without a robot

```{note}
**In this chapter:** run your node's logic in a test, in-process, with no
router, no simulation, and no appliance; fake situations that are hard — or
impossible — to produce for real.
```

Prerequisites: chapters 3–5 — you have a project and the `Wanderer` node
from chapter 5.

## The test harness

`zenode.testing.harness()` runs your nodes in a single process over an
in-memory transport. There is no router, no network, and no appliance —
starting a node under the harness is just as fast as calling a function,
which is what makes it reasonable to do on every test run, not just
occasionally by hand.

A harness on its own is empty: nothing publishes odometry, nothing accepts a
navigation goal. `robodog_sdk.testing` supplies doubles that play the
stack's side of the conversation:

- **`FakeStack`** latches state on the same topics the real stack
  publishes — odometry, battery, safety, the gateway status — and records
  every command your node sends, so a test can assert on what was
  published rather than guess at side effects.
- **`FakeNav`** stands in for the navigation coordinator: it accepts a
  goal, streams feedback while the "task" is running, and ends it wherever
  you tell it to — including states a real robot might take minutes, or an
  obstacle, to reach.

## A complete test

```{literalinclude} ../../tests/test_guide_examples.py
:pyobject: test_wanderer_drives_until_the_distance_is_covered
:language: python
```

This is not a paraphrase — it is the actual test that runs against
`Wanderer` in this project's CI. Walking its anatomy:

1. **Start the fake, then your node.** `FakeStack` must be running before
   `Wanderer` starts, so the state your node subscribes to already has a
   value the moment it looks — nodes read latched topics, not a channel
   that might still be empty.
2. **Poke state.** `stack.set_pose(x=0.0, y=0.0)` publishes an odometry
   frame, exactly as the real stack would after the robot moved.
3. **Sleep a settle interval.** Publishing is asynchronous — the handler
   that reacts to the new pose runs on the event loop, not synchronously
   inside `set_pose`. `SETTLE = 0.2` gives it room to run before the test
   inspects anything. This is generous on purpose: assert on behavior, not
   on how fast the machinery happens to be today.
4. **Assert on what the fake recorded.** `stack.last_command` is the most
   recent `MovementCommand` `Wanderer` published; `stack.stopped` is
   `True` once that command is zero velocity. Nothing here inspects
   `Wanderer`'s internals — the test only sees what a real subscriber to
   the gateway topic would see.

## Situations you cannot arrange on a desk

Some conditions a node has to handle are hard to trigger with a desk, a
laptop, and a simulation: a battery running low, a human grabbing the
gamepad mid-task, an e-stop being pressed, the safety source itself going
silent, a navigation task stalling in place. `FakeStack` and `FakeNav`
let you fake all of them directly:

```{literalinclude} ../../tests/test_guide_examples.py
:pyobject: test_wanderer_survives_a_battery_scare
:language: python
```

- **`stack.set_battery(soc=..., level=...)`** publishes a battery state —
  including `BatteryLevel.critical` at 5% charge, without spending an
  afternoon running a real pack flat.
- **`stack.set_driver(source, ...)`** publishes a gateway status, which is
  how a test says "a human just took the gamepad" — a preemption your node
  can't provoke from its own commands, because it's a fact about who else
  is driving, not about what it sent.
- **`stack.set_safety(estop=True, ...)`** fakes the e-stop being pressed.
  `stack.set_safety(source_alive=False, phase=EstopPhase.SOURCE_LOST)`
  fakes the safety source going silent instead — a different cause that
  stops the robot just as hard, and a branch worth testing separately from
  a pressed button.
- **`nav.result_state = TaskState.BLOCKED`** makes the next task the fake
  coordinator finishes end BLOCKED, exercising your node's BLOCKED branch
  without an obstacle anywhere near the robot.
- **`nav.activity = NavActivity.STALLED`** fakes a mid-task stall — the
  same sub-state a real skill reports when it's stopped in front of
  something but still trying — without needing anything to actually stop
  it.

```{note}
These are stand-ins, not physics — nothing moves, and no motor ever spins.
"Does the robot actually get there" is a question for the simulation
(chapter 2), not for the fakes. Use the fakes to test how your node
*decides*; use the simulation to test whether the robot *arrives*.
```

## Set it up in your own project

1. Add the test dependencies:

   ```bash
   uv add --dev pytest pytest-asyncio
   ```

2. Add these two lines to `pyproject.toml`:

   ```toml
   [tool.pytest.ini_options]
   asyncio_mode = "auto"
   testpaths = ["tests"]
   ```

   `asyncio_mode = "auto"` lets you write `async def test_...` directly,
   with no `@pytest.mark.asyncio` decorator on every function.

3. Put your tests under `tests/`, alongside your nodes:

   ```
   my-project/
   ├── my_node.py
   ├── tests/
   │   └── test_my_node.py
   └── pyproject.toml
   ```

   In your own project, `my_node.py` is the `wanderer.py` you wrote in
   chapter 5, and `test_my_node.py` imports it by its module name (`import
   wanderer`) — the same way `tests/test_guide_examples.py` imports
   `wanderer` in this repository.

4. Run them:

   ```bash
   uv run pytest
   ```

## Troubleshooting

- **The test hangs.** Almost always a missing `await`, or a fake you
  never started under the harness — a subscription on a topic nobody is
  publishing to just waits, and `asyncio.sleep(SETTLE)` won't rescue a
  handler that never runs.
- **The test is flaky.** Usually the settle interval is too tight for the
  machine running it. Raise it before you do anything else, and prefer
  asserting on behavior (`stack.stopped`, `node.result is not None`) over
  timing — a test that waits in a loop for a condition, as
  `test_goto_submits_the_goal_and_finishes` does, is more robust than one
  that sleeps a fixed amount and hopes.

## Where to go next

Continue to chapter 8.
