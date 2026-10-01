# Advanced control

```{note}
**In this chapter:** share the robot with other command sources; use
postures; keep causality traceable; put it all together.
```

Prerequisites: chapters 4-8.

## You are not the only one commanding the robot

Every command you send carries a `source`, and the motion gateway is not a
queue: it forwards whichever *fresh* command has the highest rank, dropping
the rest. The ranking, lowest to highest:

```
autonomous < planner < assisted_teleop < controller
```

Your code defaults to `MovementSource.autonomous`, the bottom rank. That is
why a human on the gamepad preempts you the moment they touch it, and why
you resume automatically the moment they let go: there is no lock to take
or release, and nothing to hand back. The gateway re-decides on every frame,
from whatever is freshest.

`robot.preempted_by` tells you who currently outranks you: `None` when
nothing does, which covers both "we are driving" and "nobody is driving".
Reading it is optional: a node that never checks it still behaves correctly,
because the gateway does the arbitration regardless of whether your code
notices. Checking it only lets you log or wait more gracefully instead of
quietly losing every command to a higher source.

```{warning}
Setting a higher `source` on your own commands is not a way to "win" the
arbitration: it is a claim to *be* that thing. `controller` means "a human
holding the gamepad right now"; `assisted_teleop` means "human intent shaped
by a skill". Only pass a higher source if your node genuinely is that party.
Claiming `controller` from an autonomous routine defeats the entire point of
the ranking, because the human's real gamepad input no longer reliably outranks
you.
```

See [motion concepts](../concepts/motion.md) for how the gateway decides
this, frame by frame.

## When commands go out and nothing moves

You sent a command, the call didn't raise, and the robot isn't moving. Start
with `robot.state.gateway`:

- `active_source` is who won arbitration this frame. If it isn't your
  source, someone else's command is the one being forwarded; see the
  section above.
- `action` and `active_zones` are what the collision monitor did to the
  winning command, and which zones it did it because of. A stop zone does
  not necessarily mean zero: it strips only the velocity component heading
  *into* the obstacle, leaving the robot free to turn or reverse out of it.
  Read `active_zones` as well as `action` to see what the robot may still
  do.
- `watchdog_tripped` means the winning source went silent (a crashed
  process, a dropped connection) and the gateway is holding the robot at
  zero until it speaks again. This can be true even while `active_source`
  still names your own node, if your commands stopped arriving.

`robot.blocked_by_zone` is the shortcut for the zones currently shaping your
commands. Empty means nothing is breached, which does not by itself mean the
robot will move: check the watchdog and arbitration too.

## Postures: tilt and holds

Two different mechanisms handle body orientation, and they behave nothing
alike:

```python
robot.tilt(pitch_deg=10)  # one control frame, then relaxes
robot.hold_tilt(pitch_deg=10.0)  # re-asserted at 10 Hz until cleared
robot.clear_tilt()  # back to level

async with robot.tilting(pitch_deg=10.0):  # held for the block
    ...  # restores the previous hold on exit
```

`robot.tilt(...)` applies for a single control frame and the robot itself
neutralizes it shortly after. The tilt key has no expiry, so this is not
the deadman at work; the robot relaxes back to level on its own. Use it for
a nudge.

`robot.hold_tilt(pitch_deg=10.0)` keeps re-asserting the setpoint at 10 Hz
until `clear_tilt()` (or another `hold_tilt` call) changes it. This is what
holds an orientation. `async with robot.tilting(...)` holds one for
the duration of a block and restores whatever hold was active before it on
exit, so nesting a temporary tilt inside a longer-running one returns to
that hold rather than dropping to level.

```{warning}
The tilt key **bypasses the motion gateway** entirely: it is not arbitrated
against another source, and it is not covered by the collision monitor or
the deadman. Two nodes holding different tilts fight silently: there is no
error, no rejection, just whichever one published most recently winning that
frame. Coordinate tilt ownership yourself; the gateway will not do it for
you.
```

## Keeping the causal chain

Messages your handlers cause are traced automatically. A `put()`, a `call()`,
a `spawn()`, or a `blocking()` invoked from inside a handler is linked back
to whatever message caused that handler to run, with no extra code required.

A timer breaks this. The body of a periodic callback is caused by the clock,
not by any incoming message, so anything it publishes starts a *new* trace
with no link to whatever earlier message prompted the timer to be set up in
the first place. The common shape that loses the link is sense, then act
later via a timer: by the time the timer fires, the trace that started at
the sensor reading is gone.

The fix is to capture the trace id when you still have it, and restore it
explicitly when the timer fires:

```python
# in the handler, while the trace is still current:
self._pending = (msg, trace.current())

# in the timer body, later, on the clock:
msg, traceparent = self._pending
with trace.using(traceparent):
    self.outbound.put(derive_from(msg))
```

`robot.driving()`'s republish pump is clock-driven the same way, so prefer
`robot.move()` called directly from inside a handler when the causal chain
to that handler's trigger matters.

Follow a chain from the command line once you have an id:

```bash
uv run zenode trace <id>
uv run zenode logs --trace <id>
```

`trace` shows every hop across the fleet; `logs --trace` follows only the
log records carrying that id.

See [tracing concepts](../concepts/tracing.md) for how the trace id
propagates under the hood.

## Checking whether you may move at all

Arbitration, above, decides *who* wins when several sources want to drive.
It says nothing about whether driving is permitted at all. That is a
separate authority, and the call that asks it is
`robot.motion_permitted(within=...)`: whether the safety system currently
allows motion. A `False` result means wait, not error: a tripped e-stop, a
robot still mid-recovery, or a safety source that has gone silent all read as
"not permitted." The call fails safe: if the safety latch stops arriving
within the freshness window you gave it, that counts the same as it saying
stopped, so a crashed safety node can never be mistaken for permission. See [safety](../concepts/safety.md) for the full
mechanism, including how it differs from the collision zones covered above.

## The capstone: a patrol node

```{literalinclude} ../../examples/guide/patrol.py
:language: python
```

Every earlier chapter shows up here:

- Navigation tasks and handling every outcome: chapter 6, in `_drive_leg`'s
  use of `navigate_to` and its check of `result.state`.
- Motion permission and preemption: introduced above in this chapter, and
  applied together in the `motion_permitted` wait loop and the
  `preempted_by` check, both in `_drive_leg`.
- Configuration: chapter 4, in `PatrolConfig(NodeConfig)` and its typed,
  documented fields.
- Tests against the harness, with no robot required: chapter 7; `Patrol`'s
  own tests live alongside the rest of the guide's, in
  `tests/test_guide_examples.py`.

Modify it. Two directions worth trying:

- Add a `hold_tilt` "look around" at each corner: hold a yaw sweep for a
  second or two after each leg completes, then `clear_tilt()` before moving
  on.
- Publish a `Detection` (chapter 8) when something is seen at a waypoint,
  so a separate node can react to what the patrol finds without `Patrol`
  itself knowing anything about alerts.

## Splitting into several nodes

One node per concern is how the stack itself is built: the navigation
coordinator, the safety node, and the gateway are all separate processes,
coupled only through the topics they share. Your own project can follow the
same shape. Split `Patrol` from a detector, or a detector from an alerter,
and nothing about either node needs to change, because they were never
coupled to each other's code, only to a topic both sides import.

Both halves keep reading the same `zenode.toml`; each runs as its own
`uv run` process, found by the other through the topics it publishes and
subscribes to, just as `FakeStack` and your node are two separate objects
under the test harness. The harness already starts several nodes together in
one test: every test in this guide that calls `h.start_node` more than once
has been doing that since chapter 7.

## Where to go next

That's the guide. From here:

- [Concepts](../concepts/index.md): how the mechanisms you've been using
  work underneath, covering the gateway, tracing, navigation, and pub/sub.
- [Reference](../reference/index.md): every topic on the wire, every class
  and method, every exception, for lookup.
