# Your own topics and message types

```{note}
**In this chapter:** define a message schema; declare a topic; publish and
subscribe between your own nodes.
```

Prerequisites: chapters 3, 7, with a project, and knowledge of how to run
nodes against the test harness.

## The pattern you have been using all along

`StateTopics.odometry`, `MotionTopics.request`, `SafetyTopics.state`: every
topic you have subscribed to or published on so far came from
`robodog_sdk.topics`. There is nothing special about that module. It is a
`TopicSet`, a plain class whose attributes are `Topic` declarations, each
binding a key string to a pydantic model. Your own data can use the same
mechanism.

If your project needs to move detections, scores, plans, or anything else
between two of *your* nodes, even across two separate projects, you declare
a schema and a topic the same way, and you get the same delivery guarantees,
the same validation, and the same `zenode topics` introspection for free.

## Schema, topic, nodes

```{literalinclude} ../../examples/guide/detections.py
:language: python
```

Three pieces, each doing one job:

- `Detection(BaseModel)` is the schema. Every field is typed, and pydantic
  validates on both ends. Construct a `Detection` with a field of the wrong
  type (a string where `confidence` wants a float that can't be coerced,
  say) and pydantic raises `pydantic.ValidationError` in the *publisher's*
  process, before anything reaches the wire. A malformed message never
  makes it to a subscriber to be misinterpreted; the mistake surfaces where
  it was made.
- `Topic("perception/detections", Detection)` binds that schema to a key.
  Both `publish()` and `@subscribe()` read it to know how to encode and
  decode: declare it once, in one module, and every node that imports it
  agrees on the wire format. A subscriber's idea of the schema cannot drift
  from a publisher's when both import the same `Topic`.
- `Detector` and `Alerter` are ordinary nodes, using `publish()` and
  `@subscribe()` as in earlier chapters. The only difference from
  `StateTopics.odometry` is that `PerceptionTopics.detections` is a topic
  *you* declared. Put `Alerter` in one project and `Detector` in a second,
  separate one; as long as both import the same `PerceptionTopics`, they
  agree on the key and the schema without ever coordinating directly.

`Topic` takes the same options regardless of who declares it. You have seen
several of them already, on the stack's own topics:

- `latched=True` declares that a late subscriber should get the last
  published value instead of waiting for the next change. For a topic *your*
  node publishes, zenode delivers on that: publishing and subscribing through
  the SDK (as every example in this guide does) backs the topic with zenoh's
  advanced pub/sub, which caches the last value and replays it to a late
  joiner automatically, with no extra code on either end. Use it for state
  that should always have a current answer. The stack's *own* producers don't
  all take that path yet, so not every stack topic that declares
  `latched=True` delivers on it today; see
  [pub/sub](../concepts/pubsub.md#latched-topics) for which ones do.
- `max_age=` makes subscribers drop samples older than this many seconds.
  Use it for commands that must be fresh, where an old value is worse than
  no value (compare `MotionTopics.request`).
- `trace=True` marks this topic as the start of a causal chain, so
  everything your handler does in response (further `put()` calls,
  service calls) is linked back to it. Chapter 9 covers tracing.

## Naming keys

```{tip}
There is no mandated prefix: you run your own router, and nothing enforces
one. But keys share one flat namespace on the wire (`robodog/...` at
runtime), so a short, project-specific prefix (`perception/…`,
`team_orange/…`) keeps `zenode topics` output readable and avoids a
collision if two projects ever end up sharing a router.
```

## See it on the wire

The contract is introspectable without reading any source, yours or the
SDK's. From your project:

```bash
uv run zenode topics --contract detections
```

sketches as:

```
KEY                                          SCHEMA                   FLAGS                                      OWNER
perception/detections                        Detection                -                                          detections.PerceptionTopics.detections
```

The same command, pointed at this package's contract, lists everything the
stack itself declares:

```bash
uv run zenode topics --contract robodog_sdk.topics
```

Run `uv run zenode topics` with no `--contract` at all and it reports
`no registered topics — pass --contract <module> that defines TopicSets`.
The listing comes from importing the module you name rather than from
asking a router what is live, so it works even with nothing running.

## Troubleshooting

- **The subscriber never sees anything, though the publisher is clearly
  running.** Both sides must reference the *same* `Topic`, or at least the
  identical key string and schema. Two `Topic("perception/detections", ...)`
  declarations in two different modules are two different, unrelated
  bindings as far as you're concerned; import `PerceptionTopics` from one
  shared module instead of redeclaring it.
- **A serialization or validation error appears on one side only.** The
  model changed in one project but the other still imports an older
  version of it: add a field, rename one, or tighten a type, and every
  process holding the old shape starts disagreeing with the new one. Pin or
  update the shared module in both places together.

## Where to go next

Continue to chapter 9, where tracing follows a message like this one across
every node that reacts to it. For the mechanism behind publish/subscribe
itself, see [pub/sub](../concepts/pubsub.md) and
[tracing](../concepts/tracing.md).
