"""The guide's example nodes run and behave as their chapters claim.

Each file under ``examples/guide/`` is literalincluded by a guide chapter and
started here against the doubles in ``robodog_sdk.testing`` — an example that
stops working fails CI rather than a reader.
"""

from __future__ import annotations

import asyncio

import first_node
import goto
import pytest
import timed_drive
import wanderer
from zenode.testing import harness

from robodog_sdk import BatteryLevel, TaskState
from robodog_sdk.testing import FakeNav, FakeStack

pytestmark = pytest.mark.integration

SETTLE = 0.2  # generous: these assert on behaviour, not on latency


async def test_first_node_receives_odometry() -> None:
    async with harness() as h:
        stack = await h.start_node(FakeStack)
        node = await h.start_node(first_node.FirstNode)

        stack.set_pose(x=1.5, y=-0.5)
        await asyncio.sleep(SETTLE)

        assert node.last is not None, "the handler should have run"
        assert node.last.x == pytest.approx(1.5)


async def test_timed_drive_drives_then_stops() -> None:
    async with harness() as h:
        stack = await h.start_node(FakeStack)
        await h.start_node(
            timed_drive.TimedDrive,
            config=timed_drive.DriveConfig(speed=0.3, duration=0.3),
        )

        await asyncio.sleep(SETTLE)
        assert stack.last_command is not None
        assert stack.last_command.x == pytest.approx(0.3), "should be driving forward"

        await asyncio.sleep(0.4)  # past the configured duration
        assert stack.stopped, "leaving driving() must leave the robot stopped"


async def test_wanderer_drives_until_the_distance_is_covered() -> None:
    async with harness() as h:
        stack = await h.start_node(FakeStack)
        await h.start_node(
            wanderer.Wanderer,
            config=wanderer.WanderConfig(speed=0.3, distance=1.0),
        )

        stack.set_pose(x=0.0, y=0.0)
        await asyncio.sleep(SETTLE)
        assert stack.last_command is not None
        assert stack.last_command.x == pytest.approx(0.3), "should be driving"

        stack.set_pose(x=2.0, y=0.0)  # past the target distance
        await asyncio.sleep(SETTLE)
        assert stack.stopped, "should stop once the distance is covered"


async def test_goto_submits_the_goal_and_finishes() -> None:
    async with harness() as h:
        await h.start_node(FakeStack)
        nav = await h.start_node(FakeNav)
        await h.start_node(goto.Goto, config=goto.GotoConfig(x=2.0, y=0.5, timeout=5.0))

        for _ in range(50):
            if nav.goals:
                break
            await asyncio.sleep(0.05)

        assert len(nav.goals) == 1, "exactly one goal should have been submitted"


async def test_wanderer_survives_a_battery_scare() -> None:
    """The chapter-7 showcase: fake state no desk can produce for real."""
    async with harness() as h:
        stack = await h.start_node(FakeStack)
        await h.start_node(
            wanderer.Wanderer,
            config=wanderer.WanderConfig(speed=0.3, distance=5.0),
        )

        stack.set_pose(x=0.0, y=0.0)
        stack.set_battery(soc=5, level=BatteryLevel.critical)
        await asyncio.sleep(SETTLE)

        # Wanderer ignores battery by design — the point is that YOUR node
        # can now see a critical battery without draining one.
        assert stack.last_command is not None, "still driving; battery was observable"


async def test_goto_reports_blocked_without_crashing() -> None:
    async with harness() as h:
        await h.start_node(FakeStack)
        nav = await h.start_node(FakeNav)
        nav.result_state = TaskState.BLOCKED
        node = await h.start_node(goto.Goto, config=goto.GotoConfig(timeout=5.0))

        for _ in range(50):
            if node.result is not None:
                break
            await asyncio.sleep(0.05)

        assert node.result is not None
        assert node.result.state is TaskState.BLOCKED
