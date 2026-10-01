# Errors

`robodog_sdk` defines no exception classes of its own. What you meet are
Python's own built-ins, pydantic's, and, for one specific call, an
exception imported from `zenode`.

## `pydantic.ValidationError`

**Raised by:** constructing any message with invalid data: a field outside
its declared constraints, a wrong type, a missing required field. This
includes a movement or pose value outside the robot's capability envelope
(`robodog_sdk.limits`): `MovementCommand`, `TiltBody` and friends apply those
limits as pydantic field constraints, so an out-of-range value fails at
construction rather than being silently clamped. `NavigateThroughPosesGoal`'s
own `dwell_sec` validator (below) surfaces through this same exception, since
a `model_validator` raising `ValueError` is wrapped into a `ValidationError`
by pydantic.

**What to do:** Fix the value at the call site. Do not catch this to retry
with a clamped value: `robodog_sdk.limits.clamp_velocity` exists for the one
case that should saturate instead of raise (a joystick mapping or a
controller that overshoots slightly); for a decision (a planner request, a
value you compute), let the model validate and treat the exception as a bug
in your code.

## `PermissionError`

**Raised by:** `RobotClient.navigate_to()` (and `run_goal()`) when a
navigation goal is not accepted, most commonly because a task is already
running and the submit did not pass `preempt=True`.

**What to do:** Pass `preempt=True` to displace the running task, or call
`RobotClient.submit()` directly and read `handle.accepted` / `handle.reason`
if you would rather branch on the refusal than catch an exception.

## `TimeoutError`

**Raised by:**

- `RobotClient.wait_for_nav()`: nothing answered the navigation status probe
  within `timeout`; usually means the navigation coordinator is not running.
- `RobotClient.wait_for_task()` / `navigate_to()` / `run_goal()` past their
  `timeout=`: no terminal state arrived in time.
- `RobotClient.wait_until_ready()`: a named node was still absent when
  `timeout` elapsed.

**What to do:** For `wait_for_task` and `navigate_to`, remember the *wait*
timed out, not the task: it keeps running on the coordinator unless
you cancel it explicitly. For `wait_for_nav` and `wait_until_ready`, check
that the stack (or the relevant node) is actually up before retrying.

## `ValueError`

**Raised by:**

- `RobotClient.wait_until_ready()` when called with no node names.
- `NavigateThroughPosesGoal`'s validator: a `dwell_sec` list whose length
  does not match `poses`, or that contains a negative entry. This one
  surfaces wrapped in `pydantic.ValidationError` (see above), not as a bare
  `ValueError`, because pydantic re-raises `model_validator` failures that
  way.

**What to do:** Fix the call: supply at least one node name, or make
`dwell_sec` exactly as long as `poses` with no negative entries.

## `LookupError`

**Raised by:** `robodog_sdk.testing.FakeNav.task_status()` for a task id it
never ran. This is the test double's stand-in for the real coordinator's
behavior below. See [Testing](testing.md).

**What to do:** In a test, treat this the same way you would treat
`zenode.ServiceError` against the real stack: the task is unknown, not
merely still running.

## `zenode.ServiceError`

**Raised by:** `RobotClient.task_status()` against the real navigation
coordinator, for a task it has no record of (never submitted, or evicted
from its bounded history). "Unknown" is not a `TaskState` value, so the
coordinator refuses to dress it as one: the call answers on Zenoh's error
channel instead of returning a placeholder result, and that surfaces here as
an exception. `zenode.ServiceError` is imported from the `zenode` package
rather than defined by `robodog_sdk` itself. See
[Navigation](../concepts/navigation.md#asking-about-tasks) for the full
lifecycle this sits inside.

```{note}
`zenode.ServiceTimeout` (raised when nothing answers the status call at all,
usually because the coordinator is not running) *subclasses*
`zenode.ServiceError`. Catching `ServiceError` alone cannot tell "the
coordinator answered and has never heard of this task" apart from "nothing
answered." Catch `ServiceTimeout` first when that distinction matters.
```

**What to do:** Treat it as "this task id is not known," not as a transient
failure worth retrying with the same id. If you need to tell a genuinely
unknown task apart from a coordinator that is not responding at all, catch
`zenode.ServiceTimeout` before the broader `zenode.ServiceError`.
