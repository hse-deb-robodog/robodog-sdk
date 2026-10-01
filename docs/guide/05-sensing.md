# React to what the robot senses

```{note}
**In this chapter:** read live robot state; make movement depend on it;
know which state topics exist.
```

Prerequisites: chapters 3-4, with a project that subscribes to
odometry and a node that drives the robot.

## Sense, decide, act — in the handler

```{literalinclude} ../../examples/guide/wanderer.py
:language: python
```

There is no separate loop here: the whole control loop *is* the handler.
Every time an odometry message arrives, `on_odometry` looks at where the
robot is and decides what to do about it: keep driving, or stop. Sensing,
deciding and acting happen in the same few lines, on every message.

Calling `self.robot.move(...)` once per odometry message is what keeps the
robot moving at all: chapter 4 established that a command expires after
`COMMAND_MAX_AGE = 0.3` seconds, and the simulation publishes odometry much
faster than that, so as long as data keeps flowing, the deadman never trips.
Writing it this way has a useful side effect: if sensing dies (the topic
goes silent, the node crashes), driving stops on its own, within 0.3
seconds, with no extra code to make that happen, because the safe direction
is also the default one.

## What else you can subscribe to

`wanderer.py` only reads `StateTopics.odometry`, but it is one of several
state streams a node can subscribe to directly:

| Topic | Carries | Use it when |
| --- | --- | --- |
| `StateTopics.odometry` | Position and orientation, from the robot's own odometry | You need the robot's live pose, as in this chapter |
| `StateTopics.battery` | Charge level | You need to react to charge; see the note below |
| `LocalizationTopics.pose` | Map-frame position, from SLAM | You need position that is correct on the map, not just relative to where the robot started |
| `SafetyTopics.state` | The e-stop latch | You need to know whether the robot is currently permitted to move at all |

```{note}
The simulation you have been running since chapter 2 does not publish
battery data, since there is no battery to model. `StateTopics.battery` is real
on the physical robot, and chapter 7 gives you a way to fake it locally with
`FakeStack` before you ever see it live on the dog.
```

The full list of topics, with the message type and description for each,
lives in the [topic reference](../reference/topics.md).

## Client state without subscribing

Subscribing directly, as `wanderer.py` does, is one way to get state. It is
not the only way: `RobotClient` already subscribes to the topics that
matter most, and keeps the latest value of each on `robot.state`.

```python
robot.state.odometry.value  # the latest OdometryState, or None
robot.state.odometry.fresh(within=1.0)  # False if nothing arrived recently
```

Every attribute on `robot.state` works the same way: `.value` for the
latest message, `.fresh(within=...)` to check it hasn't gone stale. When you
just need the latest reading for a one-off decision (a background job, a
periodic check, a log line), read it from `robot.state` instead of wiring up
a subscription of your own. Reach for a subscription, as `wanderer.py` does,
when you need to react to *every* update as it arrives.

## Run it

Create `wanderer.py` next to `first_node.py` with the code above, then:

```bash
uv run python wanderer.py
```

**What you should see:** in the simulation viewer, the robot walks forward
in a straight line and stops after covering about a meter.

## Troubleshooting

- **The handler never fires.** Same checklist as earlier chapters: confirm
  `namespace = "robodog"` in `zenode.toml`, and that the simulation from
  chapter 2 is still running.
- **The robot creeps a little past the line before stopping.** That's real
  robot dynamics (braking distance), not a bug in the node. The command to
  halt is sent the instant `msg.x` crosses `distance`; covering the last bit
  of ground before it actually comes to rest is physics, not lag in your
  code.

## Where to go next

Continue to chapter 6. For the mechanism behind subscriptions, see
[pub/sub](../concepts/pubsub.md).
