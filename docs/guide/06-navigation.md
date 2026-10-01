# Navigation tasks

```{note}
**In this chapter:** send the robot to a position from code; handle every
outcome; watch a task's progress.
```

Prerequisites: chapters 2-5, with the appliance up.

## You already did this in the browser

Chapter 2 had you open the nav UI and click a point on the map. That click
submitted a *task* to the navigation coordinator, which drove the robot there
and reported back. This chapter does the identical thing from code:
`robot.navigate_to(x, y)` is the same submit, the same coordinator, the same
task lifecycle, just called from your process instead of a browser.

Keep that browser page open as you work through this chapter. It remains
your control experiment: if a goal you click there arrives but the same goal
from code doesn't, the problem is in your code, not the stack.

## A task ends in one of four states

```{literalinclude} ../../examples/guide/goto.py
:language: python
```

`robot.navigate_to(x, y, timeout=...)` submits the goal and waits: it
returns only once the task is over. When it returns, exactly one of four
things happened, carried in `result.state`:

- `TaskState.SUCCEEDED`: the only one of the four that means the robot
  arrived.
- `TaskState.BLOCKED`: the robot met the world and gave up trying, whether
  an obstacle that never cleared or no plan through the map. This is not an
  exception and not a bug. It is an outcome your code needs to handle, the
  same way you'd handle `SUCCEEDED`.
- `TaskState.FAILED`: something was wrong with the task itself, such as no
  pose source, no map, or an unhandled error in the skill.
- `TaskState.CANCELED`: a client (possibly this one, possibly another)
  canceled it, or a second submit preempted it.

Never assume arrival just because `navigate_to` returned without raising.
Check `result.state`, or the `result.succeeded` shortcut, before acting as
though the robot is where you asked it to be.

## While it runs

A running task streams `TaskFeedback` on `robot.state.nav.value`. Its
`state` field is always `TaskState.RUNNING` for the task's entire life:
that never changes until the terminal result arrives on a separate channel.
The field that actually moves is `activity`: `cruising` while driving
normally, `aligning` while rotating onto a heading, `stalled` when it's
stopped in front of something, `retreating` while backing off to the last
waypoint it passed.

A `stalled` activity is transient, not a verdict: the skill is still
trying, and it may resume cruising on its own. `robot.navigating` tells you
whether a task is under way at all (it's a freshness check on that feedback
stream, not a lookup by task id), which is handy for a periodic watcher.
`examples/navigate.py` in the repo has a `_watch()` background task that logs
this feed while a task runs.

## One task at a time

There is no queue. The coordinator runs one task at a time, and a second
`navigate_to` while one is already running is refused: it raises
`PermissionError` rather than starting anything.

- Pass `preempt=True` to cancel the running task first and take its place.
- To branch on the outcome instead of catching an exception, use
  `await robot.submit(goal)` directly. It returns a `TaskHandle` with
  `handle.accepted` and, when refused, `handle.reason`, with no exception either
  way.

For the full two-stage pattern (`submit` then `wait_for_task` separately,
handling a timeout with `cancel_task`, and a feedback watcher running
alongside), see `examples/navigate.py` in the repo.

## Stored positions belong to a map

A map-frame coordinate (the `x, y` you pass to `navigate_to`) is only
meaningful for the map it was recorded against. If the robot relocalizes
against a different map, or SLAM drops out, the same numbers can point
somewhere else entirely, or nowhere sensible at all.

Whenever you save a pose for later use, store `robot.map_id()` alongside it,
and refuse to drive to a saved coordinate when the current id disagrees with
the one it was stored under. `map_id()` returns `None` for "no usable map"
(covering "nothing published yet", "the last identity went stale", and "the
producer has no map right now" alike), and `None` never means "unchanged
from before"; treat it as "don't trust this".

See [navigation concepts](../concepts/navigation.md) for how the coordinator,
the skills, and the map identity fit together.

## Troubleshooting

- **`wait_for_nav` times out.** The navigation coordinator isn't up. Check
  the compose logs for the nav service.
- **The task ends `FAILED` immediately.** Usually means the localization
  stack (MOLA) isn't running, or there's no map loaded for it to localize
  against.

  🚧 TODO(fabian): what does nav report when MOLA is absent — exact failure
  mode for the troubleshooting box

## Where to go next

Continue to chapter 7. For the mechanism behind tasks and skills, see
[navigation concepts](../concepts/navigation.md).
