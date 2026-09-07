# The big picture

```{note}
**In this chapter:** understand what the Robodog system is; know which
processes exist and where your code fits; know what the SDK gives you.
```

Prerequisites: none.

## A robot, a control stack, and your code

The robot is a Unitree Go2 quadruped. On its back sits a Jetson computer that
runs the *control stack*: a set of independent programs that together drive
the robot. Among them are a robot bridge (talks to the Go2's own firmware), a
motion gateway (arbitrates who is allowed to move the robot right now), a
safety process (owns the emergency stop), a navigation coordinator, and a
SLAM process — SLAM stands for simultaneous localization and mapping, and it
is what builds the map and tracks the robot's position on it.

You do not write code inside the control stack. You write your own program,
in your own project, and it *talks to* the stack over the network — the stack
itself stays untouched.

The processes talk to each other, and to you, over
[Eclipse Zenoh](https://zenoh.io): each program publishes messages on named
topics, and subscribes to the topics it cares about. Nobody calls anybody
else's functions directly. See [pub/sub concepts](../concepts/pubsub.md)
for how that works.

`robodog-sdk` — this package — is how your Python program joins that
conversation. It knows every topic the stack exposes and every message type
that travels on it, and it provides `RobotClient`, an object with methods for
the operations you will use most: driving, reading state, sending navigation
goals.

<!-- diagram: architecture.svg inserted in the diagram task -->

## The simulation is the same robot

The whole stack also runs as a simulation on your own laptop, physics and
all, powered by MuJoCo. It publishes the same topics, carrying the same
message types, as the stack running on the real dog. A node you write and
test against the simulation runs against the real robot unchanged — you
switch which stack you point at, not how you talk to it.

You bring the simulation up with a single `docker compose up`. Chapter 2 does
exactly that, and by the end of it you have a robot to talk to without ever
touching hardware.

## What you will build in this guide

Working through this guide in order, you will:

- Chapter 2: bring up the simulated robot on your own laptop.
- Chapter 3: create your own project and write your first node.
- Chapter 4: drive the robot from your own code.
- Chapter 5: read the robot's state back and react to it.
- Chapter 6: send the robot to a goal and handle how navigation ends.
- Chapter 7: test your node without a robot or a simulation running.
- Chapter 8: define your own topics and message types.
- Chapter 9: share the robot with other command sources, use postures and
  tracing, and build a capstone patrol node.

Each chapter builds on the last. If something assumes a piece you have not
read yet, it is in an earlier chapter, not something you are expected to
already know.

## Where to go next

Continue to chapter 2, where you bring up the simulated robot. For the full
map of processes and topics, see
[Architecture](../concepts/architecture.md).
