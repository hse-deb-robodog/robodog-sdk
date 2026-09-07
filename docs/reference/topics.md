# Topic reference

Every key declared in {mod}`robodog_sdk.topics`, one entry per `Topic` or
`Service`. Direction is relative to your process: `robot → you` and
`you → robot` describe data crossing the boundary between your code and the
stack, `stack-internal` marks a key you can read but that exists for one node
to talk to another, and `service` marks a request/reply key called with
`node.call` rather than published or subscribed.

*Latched*, *Expiry* and the *Published by* column come from the `Topic(...)`
declaration itself and from the verified producer mapping below — not from
guessing. Where the mapping does not name a producer for a key, the entry
carries a `🚧 TODO(fabian)` slot instead of an invented answer.

```{note}
`latched=True` marks the topics whose value a late joiner needs. Delivering
it requires zenoh-ext advanced pub/sub, which the *producer* has to opt into;
the stack's nodes currently publish with plain Zenoh publishers, so on most
`latched=True` keys latching costs nothing and delivers nothing to a late
subscriber yet. The exceptions are `safety/state`, `system_state/vda` and
`system_state/system`, which are backed by queryables and do answer a late
joiner immediately — every other entry below documents the contract's
declared intent, not current delivery.
```

## Module constants

| Constant | Value | What it does |
|---|---|---|
| `COMMAND_MAX_AGE` | `0.3` s | Maximum age of a movement command before it is dropped rather than executed. Also the deadman: when a producer stops publishing, the gateway's watchdog falls through to zero velocity within this window. Age is measured across hosts and needs synchronized clocks (NTP/chrony). |
| `TRACE_RATIO` | `0.01` | Fraction of trace-root messages on a continuous stream that get a recorded span. Unsampled traces still carry a trace id, so `zenode logs --trace` and `zenode trace` work at full rate; only span recording is skipped. At `0.01`, a 20 Hz odometry stream records roughly one trace every five seconds. |
| `CONTRACT_VERSION` | the installed package version | Reported on each node's health heartbeat, so a version skew between your project and the deployed stack shows up in `zenode health` instead of as a parse error somewhere else. |
| `SAFETY_SOURCE_PREFIX` | `"safety/source"` | Key template for the per-source safety latches (`safety/source/{source_id}`). See `safety_source_key` / `safety_source_topic`. |
| `TASK_KEY_PREFIX` | `"nav/task"` | Key template for the per-task feedback, result and status keys (`nav/task/{task_id}/...`). See `task_feedback_key`, `task_result_key`, `task_status_service`. |

Keys are relative; the deployment namespace (`[transport] namespace`, e.g.
`robodog`) is prefixed at runtime — except for keys declared with
`Topic.absolute`, which ignore it (see the `InputTopics` section below).
Today that namespace must be exactly `"robodog"`: the stack hard-codes the
prefix into its own key strings rather than deriving it from a namespace.

## Motion — `MotionTopics`

Two keys and one direction of travel. Every movement source — teleoperation,
a navigation skill, your node — publishes a `MovementCommand` to `request`;
the gateway arbitrates by `MovementSource` rank, passes the winner through
the collision zones, and publishes the survivor to `move`. There is no
handshake: priority is re-decided on every frame, so a source that stops
publishing stops being the driver without having to say so. The emergency
stop lives in `SafetyTopics`, not here.

### `motion/gateway/in` — {class}`~robodog_sdk.msgs.motion.MovementCommand`

| Direction | Latched | Expiry | Published by |
|---|---|---|---|
| you → robot | no | 0.3 s | 🚧 TODO(fabian): several sources publish here at once (teleoperation, navigation skills, your code, per the module docstring) — not a single category in the verified producer mapping |

**What it's for:** The inlet every movement source publishes a velocity command to, for the gateway to arbitrate.

**Details:** Not a trace root — a command is always caused by something upstream, and starting a trace here would sever it from that cause. A command older than `COMMAND_MAX_AGE` is dropped rather than executed.

### `command/motion/move` — {class}`~robodog_sdk.msgs.motion.MovementCommand`

| Direction | Latched | Expiry | Published by |
|---|---|---|---|
| stack-internal | no | 0.3 s | motion gateway |

**What it's for:** The gateway's arbitrated output — the only movement input the robot bridge subscribes to.

**Details:** An *output*: reading it tells you what the robot was actually told, not what any one source asked for. Publishing here bypasses arbitration and the collision monitor both, and is reserved for the gateway.

## Pose — `PoseTopics`

Discrete actions and body orientation — two keys, both inlets your code publishes to directly.

### `command/pose/action` — {class}`~robodog_sdk.msgs.motion.ActionCommand`

| Direction | Latched | Expiry | Published by |
|---|---|---|---|
| you → robot | no | — | your code |

**What it's for:** A discrete action trigger — emote, stance change (stand up, lie down, sit, dance, ...), stop — sent once per `ActionType`.

### `command/pose/tilt_body` — {class}`~robodog_sdk.msgs.motion.TiltBody`

| Direction | Latched | Expiry | Published by |
|---|---|---|---|
| you → robot | no | — | your code |

**What it's for:** The commanded body orientation (pitch/roll/yaw in degrees) while standing.

**Details:** Field values are pydantic-constrained to `robodog_sdk.limits.MAX_TILT_DEG` / `MAX_BODY_YAW_DEG` (±20°); a value outside that envelope raises `pydantic.ValidationError` at construction rather than being silently clamped — see [Errors](errors.md).

## Control — `ControlTopics`

Who is driving, and why the robot is not moving. One key, re-asserted on a
~1 Hz heartbeat as well as on every change, so a late subscriber is at most
one beat behind. This is the first thing to read when a command is sent and
nothing happens; for whether the robot may move *at all*, read `safety/state`
instead.

### `motion/gateway/status` — {class}`~robodog_sdk.msgs.motion.MotionGatewayStatus`

| Direction | Latched | Expiry | Published by |
|---|---|---|---|
| robot → you | yes | — | motion gateway |

**What it's for:** Who is driving right now, and what the gateway did to their command — the arbitration winner, the collision-zone action, whether the watchdog tripped.

**Details:** An edge stream: published on every state change, unchanged between edges, plus the heartbeat noted above. Silence for several seconds means the gateway itself is gone, not that nothing has changed.

## Safety — `SafetyTopics`

The safety path, in one prefix so it can be audited at a glance —
`zenode echo 'safety/**'` shows all of it. See ADR-002, ADR-004 and ADR-005 in
the robodog-digipro repository.

### `safety/state` — {class}`~robodog_sdk.msgs.safety.SafetyState`

| Direction | Latched | Expiry | Published by |
|---|---|---|---|
| robot → you | yes — backed by a queryable, answers a late joiner immediately | — | safety node |

**What it's for:** The authority: whether the robot may move at all, as a continuous level re-published on every change and on a heartbeat.

**Details:** Fail safe on silence — no fresh frame within the deadline, a lost liveliness token, or `source_alive=False` all mean stopped. Read `motion_permitted`, not `estop`: they differ for the whole `RELEASING` recovery phase, and the difference is a robot lying on the floor. The only key here to make a decision on.

### `safety/source/{source_id}` — {class}`~robodog_sdk.msgs.safety.SafetyState`

| Direction | Latched | Expiry | Published by |
|---|---|---|---|
| stack-internal | yes | — | 🚧 TODO(fabian): which node(s) publish the per-source latch under `safety/source/*`? (each safety panel itself, per the module docstring — not a category named in the verified producer mapping) |

**What it's for:** One safety source/panel's own latch; the aggregator OR-combines every source's copy of this into `safety/state`.

**Details:** Subscribe-only — the declared key is a wildcard. Narrow it to one source with `safety_source_topic(source_id)` (built from `SAFETY_SOURCE_PREFIX` via `safety_source_key`), for a panel reporting on itself.

### `safety/release` — {class}`~robodog_sdk.msgs.safety.ButtonEvent`

| Direction | Latched | Expiry | Published by |
|---|---|---|---|
| 🚧 TODO(fabian): robot → you, or stack-internal? | no | — | 🚧 TODO(fabian): not named in the verified producer mapping — presumably the physical safety panel |

**What it's for:** Momentary event: acknowledges a stop once the e-stop switch is pulled back out.

**Details:** An event, not a level — emitted once per press, and possibly re-sent a few times for reliability over a lossy link. Deduplicate on `(source_id, seq)`.

### `safety/cancel` — {class}`~robodog_sdk.msgs.safety.ButtonEvent`

| Direction | Latched | Expiry | Published by |
|---|---|---|---|
| you → robot | no | — | your code — `RobotClient.halt()` publishes here |

**What it's for:** Momentary event: stop now, without engaging the latching e-stop.

**Details:** `RobotClient.halt()` stamps the calling node's own name as `source_id` and an incrementing `seq`. A physical safety panel can publish the same event; either way it is a stop, not the latch itself.

### `command/motion/estop` — {class}`~robodog_sdk.msgs.motion.EmergencyStopCommand`

| Direction | Latched | Expiry | Published by |
|---|---|---|---|
| 🚧 TODO(fabian): robot → you, or stack-internal? | yes | — | 🚧 TODO(fabian): not named in the verified producer mapping (topics.py calls this a "legacy edge mirror" of `safety/state`) |

**What it's for:** Legacy edge mirror of the `safety/state` latch, kept for consumers that predate the aggregator.

**Details:** Carries the latch and nothing else — not the recovery phase — so it drops one phase *before* the robot can actually move again. Anything deciding whether to drive wants `SafetyState.motion_permitted`, not this. `RobotClient` exposes only the `stop` command value; an e-stop is cleared at the physical button, not through this SDK.

### `motion/collision/event` — {class}`~robodog_sdk.msgs.navigation.CollisionZoneEvent`

| Direction | Latched | Expiry | Published by |
|---|---|---|---|
| robot → you | yes | — | motion gateway |

**What it's for:** An obstacle entered or left one of the gateway's collision zones.

**Details:** Edge-triggered — one message on breach, one when the zone clears, not on every detection cycle. Zones are named by the deployment (`"stop"`, `"slowdown"`, ...); react to the name your deployment configured rather than assuming the set. 🚧 TODO(fabian): the declaration in `topics.py` carries its own `# TODO: Define correct blocked topic, LATCHED?` comment directly above it — worth confirming whether an edge-triggered event should be `latched=True` at all.

## Input — `InputTopics`

Human input devices. Both keys are declared `Topic.absolute`: the
teleoperation node publishes them at the root of the keyspace rather than
under the deployment namespace, because that is where they are.

### `nodes/joy` — {class}`~robodog_sdk.msgs.input.GamepadState`

| Direction | Latched | Expiry | Published by |
|---|---|---|---|
| robot → you | no | — | joy |

**What it's for:** Raw gamepad snapshot — analog axes and button state.

**Details:** Raw input, not a command: the teleoperation node maps this onto the gateway inlet as the `controller` movement source. Reading it directly observes what the operator is doing, not the robot moving.

### `nodes/controller_status` — {class}`~robodog_sdk.msgs.input.GamepadStatus`

| Direction | Latched | Expiry | Published by |
|---|---|---|---|
| robot → you | yes | — | joy |

**What it's for:** Whether a gamepad is connected and actively sending input.

## State — `StateTopics`

Robot state, published by the Go2 bridge or the simulation. The first four
are the raw streams off the robot; `system` is the composite the
system-state node fuses from all of them plus safety and the fleet runtime —
the one to read when the question is "what is going on" rather than "what is
this one sensor saying."

### `system_state/highstate` — {class}`~robodog_sdk.msgs.robot.RobotHighState`

| Direction | Latched | Expiry | Published by |
|---|---|---|---|
| robot → you | yes | — | bridge only (not published by the simulation) |

**What it's for:** High-level robot state straight from the Go2's sport mode — IMU, mode, velocity, body height, foot force.

### `system_state/odometry` — {class}`~robodog_sdk.msgs.robot.OdometryState`

| Direction | Latched | Expiry | Published by |
|---|---|---|---|
| robot → you | yes | — | bridge / simulation |

**What it's for:** The robot's raw pose from its odometry source — where it thinks it has driven to. Drifts, unlike `LocalizationTopics.pose`.

**Details:** A trace root (`trace=True`, `trace_ratio=TRACE_RATIO`): sense-decide-act chains begin at a pose.

### `system_state/battery` — {class}`~robodog_sdk.msgs.robot.BatteryState`

| Direction | Latched | Expiry | Published by |
|---|---|---|---|
| robot → you | yes | — | bridge only (not published by the simulation) |

**What it's for:** State of charge, level (`good` / `low` / `critical`), voltage, current and hottest-cell temperature.

**Details:** The simulation does not model a battery, so this key is silent under `zenode.toml` pointed at it. `robodog_sdk.testing.FakeStack` fakes it for local development.

### `system_state/motor` — {class}`~robodog_sdk.msgs.robot.MotorState`

| Direction | Latched | Expiry | Published by |
|---|---|---|---|
| robot → you | yes | — | bridge only (not published by the simulation) |

**What it's for:** Per-motor temperatures.

### `system_state/releasebutton` — {class}`~robodog_sdk.msgs.safety.ButtonEvent`

| Direction | Latched | Expiry | Published by |
|---|---|---|---|
| robot → you | no | — | safety node |

**What it's for:** The release-button press, forwarded here for the fleet bridge's wait actions.

### `system_state/vda` — {class}`~robodog_sdk.msgs.system_state.VdaFacet`

| Direction | Latched | Expiry | Published by |
|---|---|---|---|
| robot → you | yes — backed by a queryable, answers a late joiner immediately | — | 🚧 TODO(fabian): the module docstring names the producer as "the VDA5050 bridge" — is that the same process as bridge/sim in the verified mapping, or a separate fleet-integration process? |

**What it's for:** The control/order/location slice the VDA5050 (fleet) bridge owns, fused by the system-state node into `system_state/system`.

**Details:** The e-stop is deliberately absent from this facet — the safety node is its sole authority — so it only ever distinguishes `ControlMode.AUTO` from `ControlMode.MANUAL`.

### `system_state/system` — {class}`~robodog_sdk.msgs.system_state.SystemState`

| Direction | Latched | Expiry | Published by |
|---|---|---|---|
| robot → you | yes — backed by a queryable, answers a late joiner immediately | — | system-state |

**What it's for:** The composite: control mode, posture, order, nav activity, fleet location and safety phase, plus `headline` and `ready_to_move`, both recomputed on parse from the facets rather than trusted from the wire.

## Localization — `LocalizationTopics`

The robot's fused pose. Exactly one producer at a time — MOLA SLAM or the
odometry fallback node, never both (ADR-003); consumers do not need to know
which is running. MOLA's own ROS 2 output (`lidar_odometry/pose` etc.,
bridged by `zenoh-bridge-ros2dds`) is not part of this contract.

### `localization/pose` — {class}`~robodog_sdk.msgs.robot.OdometryState`

| Direction | Latched | Expiry | Published by |
|---|---|---|---|
| robot → you | yes | — | MOLA (or the odometry fallback node) |

**What it's for:** The robot's fused pose — the one navigation goals are expressed in.

**Details:** A trace root (`trace=True`, `trace_ratio=TRACE_RATIO`) — neither producer is a zenode node, so no trace context arrives from upstream to continue.

### `localization/map_identity` — {class}`~robodog_sdk.msgs.localization.MapIdentity`

| Direction | Latched | Expiry | Published by |
|---|---|---|---|
| robot → you | yes | — | MOLA (or the odometry fallback node) |

**What it's for:** Which map `localization/pose` is anchored to; see `RobotClient.map_id()`.

**Details:** Latched *and* re-stated on a slow (~0.2 Hz) heartbeat, unlike `map/grid`, which is change-only — the heartbeat is what makes its age meaningful: a consumer treats an identity older than its threshold as "no usable map." The odometry fallback publishes `pose` but no identity at all; that silence is the correct answer, since odometry has no map.

## Map — `MapTopics`

### `map/grid` — {class}`~robodog_sdk.msgs.occupancy.GridMap`

| Direction | Latched | Expiry | Published by |
|---|---|---|---|
| robot → you | yes | — | MOLA |

**What it's for:** The SLAM session's occupancy grid, exactly as MOLA built it — uninflated, the input every other consumer should start from.

**Details:** Published when a grid is rebuilt and when the active session changes, never on a timer. `stamp` is the age of the last *change*, not of a heartbeat — an old stamp here is normal and says nothing about whether SLAM is alive; read `localization/pose` for that. Agrees with `nav/costmap/global` on `map_id`; when they disagree, one of them has not caught up with a remap yet.

## Navigation topics — `NavTopics`

Task feedback, results, the planned route and the cost grids. The two task
keys are wildcards over the task id — both payloads carry `task_id`, so
demultiplexing needs no key parsing. Neither is latched, and a result is
published exactly once; a subscription declared after a task finished sees
nothing — ask `nav/task/{task_id}/status` (below) instead.

### `nav/task/{task_id}/feedback` — {class}`~robodog_sdk.msgs.navigation.TaskFeedback`

| Direction | Latched | Expiry | Published by |
|---|---|---|---|
| robot → you | no | — | nav coordinator |

**What it's for:** A running task's progress — pose, distance to goal, active skill, `activity` (`cruising`, `aligning`, `stalled`, `retreating`, ...), route segment index.

**Details:** ~10 Hz, driven by the skill's own control loop, so the rate is the skill's and not a guarantee. `state` is narrowed to `TaskState.RUNNING` — a terminal value can never appear here even by accident; see [Navigation](../concepts/navigation.md). Subscribe before submitting, or accept that the first samples are missed. Narrow to one task with `task_feedback_topic(task_id)` (built from `TASK_KEY_PREFIX`).

### `nav/task/{task_id}/result` — {class}`~robodog_sdk.msgs.navigation.TaskResult`

| Direction | Latched | Expiry | Published by |
|---|---|---|---|
| robot → you | no | — | nav coordinator |

**What it's for:** The one terminal payload for a task — `state` is always one of the four terminal outcomes described in [Navigation](../concepts/navigation.md).

**Details:** Published exactly once, never latched — subscribe **before** submitting, or use `nav/task/{task_id}/status` after the fact. Narrow to one task with `task_result_topic(task_id)`.

### `nav/path` — {class}`~robodog_sdk.msgs.navigation.PlannedPath`

| Direction | Latched | Expiry | Published by |
|---|---|---|---|
| robot → you | yes | — | nav coordinator |

**What it's for:** The dense, ordered waypoint list a skill committed to, for visualization.

**Details:** Republished once per plan, and again on a replan or a retreat. Nothing in the control loop subscribes to it — a consumer that misses one has missed a picture, not a command.

### `nav/costmap/global` — {class}`~robodog_sdk.msgs.occupancy.CostMap`

| Direction | Latched | Expiry | Published by |
|---|---|---|---|
| robot → you | yes | — | nav coordinator |

**What it's for:** The active MOLA session's map, already inflated by the robot radius — a planner treating the robot as a point is correct against this grid.

### `nav/costmap/local` — {class}`~robodog_sdk.msgs.occupancy.CostMap`

| Direction | Latched | Expiry | Published by |
|---|---|---|---|
| robot → you | no | — | nav coordinator |

**What it's for:** A rolling body-frame window rasterized from the LiDAR.

## Navigation services — `NavServices`

Submitting and cancelling navigation tasks. Services, not topics: request/reply
over Zenoh's queryable mechanism, called with `node.call` rather than
published or subscribed. There is no queue — a submit while another task runs
is refused unless it asks to preempt. See
[Navigation](../concepts/navigation.md) for the task lifecycle these three
calls drive.

### `nav/task/submit` — {class}`~robodog_sdk.msgs.navigation.TaskGoalEnvelope` → {class}`~robodog_sdk.msgs.navigation.TaskHandle`

| Direction | Latched | Expiry | Published by |
|---|---|---|---|
| service | n/a | n/a | nav coordinator |

**What it's for:** Start a navigation task; replies with its id, or `accepted=False` and a `reason` when another task is running without `?preempt=true`, the named skill does not exist, or the goal did not parse.

**Details:** Two knobs travel as query parameters rather than in the payload, so the goal on the wire stays exactly the goal: `?preempt=true` displaces a running task, `?on_estop=hold` keeps this task across an emergency stop (`EstopPolicy.HOLD`) instead of discarding it. `?client=` is also read and recorded against the task, for logs. Skills are named by string rather than declared in this contract — the stack ships `global_nav` (the default), `corridor_assist`, `waypoint_follow`, `door_traverse` and `dummy`.

### `nav/task/cancel` — {class}`~robodog_sdk.msgs.navigation.CancelRequest` → {class}`~robodog_sdk.msgs.navigation.CancelAck`

| Direction | Latched | Expiry | Published by |
|---|---|---|---|
| service | n/a | n/a | nav coordinator |

**What it's for:** Abandon a task and stop.

**Details:** `canceled=False` covers both "already finished" and "never heard of it" — `reason` distinguishes them in prose, not in a field.

### `nav/task/{task_id}/status` — {class}`~robodog_sdk.msgs.navigation.TaskStatusRequest` → {class}`~robodog_sdk.msgs.navigation.TaskResult`

| Direction | Latched | Expiry | Published by |
|---|---|---|---|
| service | n/a | n/a | nav coordinator |

**What it's for:** A late poll for one task's status — answers with the recorded `TaskResult` for a task the coordinator remembers, or one carrying `TaskState.RUNNING` if it is still going.

**Details:** For a task the coordinator has no record of — never submitted, or evicted from its bounded history — it answers on the Zenoh **error channel**, which surfaces as an exception rather than a placeholder result: `zenode.ServiceError` (see [Errors](errors.md) and [Navigation](../concepts/navigation.md#asking-about-tasks)). Declared per task; call it via `task_status_service(task_id)` rather than constructing the key directly.
