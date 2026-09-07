"""The guide's example nodes run and behave as their chapters claim.

Each file under ``examples/guide/`` is literalincluded by a guide chapter and
started here against the doubles in ``robodog_sdk.testing`` — an example that
stops working fails CI rather than a reader.
"""

from __future__ import annotations

import asyncio

import first_node
import pytest
import timed_drive
from zenode.testing import harness

from robodog_sdk.testing import FakeStack

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
