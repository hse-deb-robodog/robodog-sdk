"""The guide's example nodes run and behave as their chapters claim.

Each file under ``examples/guide/`` is literalincluded by a guide chapter and
started here against the doubles in ``robodog_sdk.testing`` — an example that
stops working fails CI rather than a reader.
"""

from __future__ import annotations

import asyncio

import first_node
import pytest
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
