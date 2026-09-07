# Tracing

Every node you write is traced without you asking for it, and that is the
point: when a command spans four processes and nothing moves, the question is
not which process is broken but which one dropped the chain, and answering it
needs one id that follows the message across all of them.

## Where traces start

A trace begins at the topics that begin a causal chain in the first place —
`system_state/odometry` and `localization/pose` — sampled at 1%
(`robodog_sdk.topics.TRACE_RATIO`) so a 20 Hz stream does not record a span on
every single frame. From there, everything a handler causes stays in the
trace automatically: `put()`, `await self.call()`, `self.spawn()`, and
`await self.blocking()` all propagate it. There is nothing to configure and
no API to learn — the propagation is a property of calling those from inside
a handler that is itself part of a trace.

## Service calls join, they do not start

A service call cannot be a trace root; it either continues the caller's trace
or carries none. A navigation task submitted from a plain script therefore
has no trace of its own to speak of, while one submitted from inside a
handler belongs to the trace of whatever triggered that handler.

## Following one message

```bash
uv run zenode logs --trace <id>    # every log record from that chain
uv run zenode trace <id>           # the path it took, hop by hop
```

Both work with nothing installed and no collector running — a trace id is
Zenoh-level metadata, not something an OpenTelemetry backend has to be up to
read. Span recording is optional (`zenode[otel]`) and adds detail beyond the
id and the log records; without it a traced `put()` costs roughly 3.6 μs
against 1.9 μs untraced, and topics that never carry a trace are unaffected
either way.

## Timers break the chain

A timer body is caused by the clock, not by a message, so it runs outside any
trace. The shape that loses the link is the common one: sense in a handler,
act later on a timer.

```python
@subscribe(StateTopics.odometry, mode="latest")
async def on_pose(self, msg):
    self.latest = msg


@every(0.1)
async def tick(self):
    self.cmd.put(...)  # orphaned — no link to the pose that caused it
```

The fix is to capture the trace context while it is still current, in the
handler, and restore it explicitly when the timer fires:

```python
from zenode import trace


@subscribe(StateTopics.odometry, mode="latest")
async def on_pose(self, msg):
    self.latest = (msg, trace.current())


@every(0.1)
async def tick(self):
    msg, traceparent = self.latest
    with trace.using(traceparent):
        self.cmd.put(...)
```

`examples/contract_drive.py` does exactly this: `on_odometry` stashes
`trace.current()` into `self._pose_trace` on every pose, and `tick` wraps its
`put()` in `with trace.using(self._pose_trace):` so the command it publishes
stays linked to the measurement that produced it, even though `tick` itself
runs on `@every`, off the clock.

The same problem applies to `RobotClient.driving()`: its republish pump is
clock-driven too, so commands it sends are not linked to whatever measurement
prompted the call. Call `robot.move()` directly from inside a handler instead
of through `driving()` when preserving the causal chain to that handler's
trigger matters.

## Your own topics

`trace=True` is yours to set on a `Topic` you declare, and it belongs on the
one that *starts* a chain — add `trace_ratio=` alongside it to sample a
continuous stream rather than record every frame. Marking a downstream topic
`trace=True` as well is harmless: a topic starts a new trace only when none
is already active, so a pipeline that is already inside a trace stays one
trace regardless of how many of its topics are marked. The practical
consequence is that `trace_ratio` only ever takes effect on whichever topic
actually started the trace — a `trace_ratio` set on a downstream topic that
never gets to start one has nothing to act on.
