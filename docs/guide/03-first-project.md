# Your first project

```{note}
**In this chapter:** create a Python project with uv; connect a node to the
running simulation; receive live data from the robot.
```

Prerequisites: chapter 2 — the appliance is running.

## Create the project

1. Create a new project and move into it:

   ```bash
   uv init my-robot-project && cd my-robot-project
   ```

2. Add `robodog-sdk` as a dependency:

   ```bash
   uv add "robodog-sdk @ git+https://github.com/hse-deb-algo-athlets/robodog-sdk@v%%SDK_VERSION%%"
   ```

   **What you should see:** uv resolves the package and reports it installed,
   pulling in two runtime dependencies — `zenode`, which is the node
   framework the SDK is built on, and `pydantic`, which the SDK's message
   types are defined with.

## Tell your project where the robot is

Create `zenode.toml` next to `pyproject.toml`:

```toml
[transport]
mode = "client"
connect = ["tcp/localhost:7447"]
namespace = "robodog"
```

This file is read by zenode when your node starts. `connect` points at the
Zenoh router you brought up in chapter 2 — the same file with the dog's own
address in place of `localhost` talks to the real robot instead, and nothing
else about your code changes.

`namespace` matters more than it looks: every topic key the SDK uses is
prefixed with it on the wire, and the appliance you brought up in chapter 2
is deployed under `robodog`. Get this value wrong and there is no error —
your node starts, connects, and simply never receives anything.

```{warning}
**If your node never sees any data:** check `namespace = "robodog"` in
`zenode.toml` first — a mismatch here produces silence, not an error. Then
confirm your node is actually connected by running `uv run zenode nodes` in
the project directory; your node's name should appear in the list.
```

## A node that listens

Create `first_node.py` next to `zenode.toml` with the following content:

```{literalinclude} ../../examples/guide/first_node.py
:language: python
```

Walking through it:

A `Node` is one program in the conversation — one process that can publish
messages, subscribe to messages, or both. `FirstNode` is a node with a
single job: remember the robot's most recent position.

`name = "first-node"` is how this node identifies itself. It is the string
that shows up when you list running nodes with `uv run zenode nodes`, and it
is what you would use in the future to send this node its own configuration.

`@subscribe(StateTopics.odometry, mode="latest")` registers `on_odometry` to
be called whenever a new message arrives on the odometry topic. This is
publish/subscribe — see [pub/sub concepts](../concepts/pubsub.md) for the
full picture, but the short version is: nobody calls anybody else's
functions directly, programs just publish messages on named topics and
subscribe to the ones they care about. `mode="latest"` matters here — it means that if several odometry
messages arrive faster than your handler processes them, only the newest one
is delivered; the backlog is dropped. That is what you want for a live
position: you care where the robot is *now*, not the history of everywhere
it has been.

`on_odometry` is `async def`. Every handler in zenode is a coroutine, because
a node does many things concurrently — reading multiple topics, running
timers, talking to the network — all on a single thread, using an event
loop. The loop only makes progress on the next thing once the current
handler yields control back to it, so a handler that blocks (a long
computation, a synchronous network call, `time.sleep`) freezes the entire
node, not just itself. See [asyncio essentials](../concepts/async-python.md)
for what that means in practice; for now, the rule is simple: keep handlers
quick, and use `await` for anything that takes time.

Here is the whole flow you just built, from `uv run` to the first log line:

![Sequence of the first node starting: uv run starts the node, it subscribes at the router, and every odometry sample the simulation publishes is delivered to the handler, which logs the position](../_static/first-node-sequence.svg)

## Run it

Run the node:

```bash
uv run python first_node.py
```

**What you should see:** a log line each time the robot's position updates,
with the coordinates changing over time, for example:

```
robot at x=0.02 m, y=-0.01 m
robot at x=0.04 m, y=-0.01 m
```

Open the nav UI from chapter 2 (`http://localhost:8081`) and click a point
on the map to drive the robot. Watch the numbers in your terminal move as
the robot walks there.

## Troubleshooting

- **No log lines appear at all.** Check `zenode.toml` — the most common cause
  is `namespace` not set to `"robodog"`, which connects successfully but
  receives nothing. Confirm the router from chapter 2 is still running, and
  run `uv run zenode nodes` to check that your node is actually connected.

## Where to go next

Continue to chapter 4, where you send commands back to the robot instead of
only reading its state. For the concepts touched on here, see
[pub/sub](../concepts/pubsub.md) and
[asyncio essentials](../concepts/async-python.md).
