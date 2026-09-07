# Pub/sub

Every process in the stack, and every node you write, talks the same way:
it publishes messages on named topics and subscribes to the topics it cares
about. Nobody calls anybody else's functions. A publisher does not know who,
if anyone, is listening, and a subscriber does not know who published — how
many programs are running, where they run, and whether they are written in
Python or something else is completely invisible to your code. This page is
the mechanism behind that: what a key actually is, what "latched" and
"expires" mean, and how the SDK's request/response calls fit in.

## Keys and the namespace

A topic's key, as declared in `robodog_sdk.topics`, is relative:
`StateTopics.odometry` is `system_state/odometry`. Nothing on the wire is
addressed by that string alone, though — the `namespace` set in your
`zenode.toml` is prefixed to every key your node uses, so that relative key
travels as `robodog/system_state/odometry`.

The deployment you are talking to — appliance or dog, it makes no
difference — is fixed at `robodog`. That is not a placeholder you are meant
to change; it is the one value that currently addresses the stack at all.

```{warning}
Get the namespace wrong and there is no error. Your node starts, connects to
the router successfully, and simply never sees a message — it is
subscribing to a prefix nothing publishes under. Silence, not an exception,
is the failure mode, which is why it is the first thing to check when
nothing arrives. Run `uv run zenode nodes` to confirm your node is even
connected in the first place.
```

<!-- diagram: pubsub.svg inserted in the diagram task -->

## Latched topics

A latched topic re-delivers its most recent value to a subscriber that joins
after it was published, rather than making that subscriber wait for the next
change. That is the mechanism behind something you have probably already
noticed: subscribe to `StateTopics.odometry`, `StateTopics.battery`, or
`SafetyTopics.state` and you get a value immediately, even if the robot's
been sitting idle since before your node started. Those are state — they
describe a condition that holds until something changes it, so a late
subscriber genuinely needs to know the current value, not just future ones.

Command topics are not latched, and that follows the same logic in reverse:
`MotionTopics.request` describes an instruction for right now, and there is
no "current instruction" to replay to a node that starts up later — a
subscriber that joins late on a command topic waits for the next command,
same as anyone else.

## Commands expire

A topic can declare a `max_age`; a subscriber discards anything older than
that rather than acting on it. The clearest example is the movement inlet,
where `COMMAND_MAX_AGE = 0.3` seconds doubles as the deadman: stop
publishing — your process crashes, the network drops — and within 0.3
seconds the gateway is looking at nothing fresh enough to act on and falls
through to zero velocity, or to the next-ranking source still publishing.
See [driving](../guide/04-driving.md) for what that deadman looks like from
the driver's seat.

Age is judged by comparing a timestamp set on the publisher's machine
against the clock on whichever machine is checking it — often a different
host entirely. That comparison is only meaningful if the two clocks agree,
which is why the stack requires synchronized clocks (NTP or chrony) across
every machine involved. Let them drift and every command looks stale the
moment it arrives, with nothing in the failure to say why.

## Services

Not everything is a broadcast. Submitting a navigation task, or asking for
one task's status, is a request that expects exactly one reply — you want an
answer to *your* question, not everyone's opinion. Zenode calls this
pattern a service, and the stack uses it wherever the interaction is
genuinely request/response rather than an ongoing stream.

You will not usually declare or call a service directly. `RobotClient`
wraps the ones a typical node needs — `navigate_to`, `task_status` — behind
plain `async` methods, so from your code a service call reads like any other
`await`, not like a second API to learn on top of pub/sub.

## Seeing the wire

Three commands turn the contract from something you read in source into
something you can watch live:

```bash
uv run zenode topics --contract robodog_sdk.topics
uv run zenode nodes
uv run zenode health
```

`zenode topics` lists every declared key against the contract module, so you
can check a key or a message shape without opening `topics.py`. `zenode
nodes` lists who is actually connected right now — the check for "is my node
even here." `zenode health` reports each node's heartbeat, and that
heartbeat carries `CONTRACT_VERSION`: if your project and the deployed stack
were built against different versions of the contract, that skew shows up
there, as a mismatched version in a health report, rather than surfacing
later as a confusing parse error somewhere else entirely.
