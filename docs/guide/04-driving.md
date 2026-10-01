# Drive the robot

```{note}
**In this chapter:** move the robot from code; understand why commands
expire; stop reliably.
```

Prerequisites: chapters 2-3, with the simulation running and a
project with a working node.

## Meet RobotClient

`RobotClient` is the one object you use for everything you do to and with
the robot: movement, navigation, and the state and safety queries you'll
meet in later chapters. Create it once, in `on_start`, from the node it
belongs to:

```python
async def on_start(self) -> None:
    self.robot = RobotClient(self)
```

It holds no privileged connection to the stack. Underneath, it publishes and
subscribes on the same topics any node could use directly (see how commands
reach the robot in [motion](../concepts/motion.md) for the full picture). That
means anything `RobotClient` can do, another node (or a human at the
gamepad) can also do, and the stack's usual arbitration between sources still
applies to it.

## Commands expire after 0.3 seconds

Every movement command carries a maximum age, `COMMAND_MAX_AGE = 0.3`
seconds. The motion gateway checks the timestamp on each command it
receives, and if the newest one it has is older than that, it stops the
robot, regardless of what the command said.

This is a safety feature, not a quirk: if your program stops publishing
(it crashes, hits a breakpoint, or loses the network), the robot stops within
0.3 seconds of the last thing you told it. There is no code path that leaves
the robot coasting on a stale instruction.

The direct consequence is that a single call doesn't keep the robot moving:

```python
self.robot.move(x=0.3)  # drives forward for about 300 ms, then stops
```

There are two correct ways to sustain motion:

- `async with self.robot.driving(x=...)`: republishes the command for you
  at a safe rate for as long as the block runs, and always sends a stop on
  the way out, including when the block raises. This is what the example
  below uses.
- Call `self.robot.move(...)` yourself from a handler that fires regularly
  enough to beat the expiry: a periodic timer, or a subscription that
  delivers fast enough. Chapter 5 does this.

```{warning}
Command age is measured across machines: the timestamp is set on your
laptop and checked on the robot's Jetson (or, in simulation, by the
gateway process). If the two clocks disagree by more than a fraction of a
second, every command looks stale the moment it arrives and the robot
ignores you, with no error on your side. Keep clocks NTP-synchronized;
this is a classic first thing to check when nothing moves.
```

## A node that drives

```{literalinclude} ../../examples/guide/timed_drive.py
:language: python
```

A few new pieces beyond chapter 3:

`DriveConfig(NodeConfig)` is a typed configuration object. Its fields,
`speed` and `duration`, get the defaults declared here unless something
overrides them, which is what makes the same node reusable: run it as-is,
or drop a `[node.timed-drive]` section into `zenode.toml` to change `speed`
and `duration` without touching the code.

`self.spawn(self._run(), name="drive")` starts `_run` as a background task
owned by the node, rather than awaiting it inline in `on_start`. `on_start`
returns quickly and the node is fully up while `_run` does its work
concurrently. Use this pattern any time a node needs to run its own
long-lived logic alongside handling messages.

`async with self.robot.driving(x=self.config.speed):` is the guarantee from
the previous section made concrete: for as long as the block's body runs
(here, `await asyncio.sleep(self.config.duration)`), the command is
republished often enough to never expire, and the moment the block exits,
for any reason, the robot is sent a stop.

## Run it

Create `timed_drive.py` next to `first_node.py` with the code above, then:

```bash
uv run python timed_drive.py
```

**What you should see:** in the simulation viewer from chapter 2, the robot
walks forward for about 2 seconds and then stops. Your terminal logs `done`
once `_run` finishes.

## Speed limits are enforced in your process

`MovementCommand` validates every value you give it against the robot's
real capability envelope. Pass a speed outside that range and
`self.robot.move(...)` (or `driving(...)`) raises `pydantic.ValidationError`
immediately, at the call site, before anything is sent over the network,
let alone reaches the robot. There is no need to guess safe values or clamp
them yourself; an out-of-range command simply never leaves your process.

## Troubleshooting

- **The robot doesn't move.** Check that the simulation viewer shows it
  standing upright. A robot that has fallen over won't walk regardless of
  what you command. Also check whether anything else is currently driving
  it: if a navigation task from chapter 2's nav UI is still running, it
  outranks your node's commands. Cancel it in the nav UI, then retry.
- **On the real robot, nothing happens and there's no error.** See the
  clock warning above and verify NTP sync between your machine and the
  robot.

## Where to go next

Continue to chapter 5, where a node reacts to live state instead of running
on a fixed timer. For the underlying mechanism, see
[motion and the command gateway](../concepts/motion.md).
