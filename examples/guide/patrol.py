"""The guide's capstone: patrol a route, coexist with everything else.

    uv run python examples/guide/patrol.py

Everything from the guide in one node: navigation tasks in sequence, every
outcome handled, motion permission checked, and preemption by a human driver
respected — because on this robot you are never the only party involved.
"""

from __future__ import annotations

import asyncio

from zenode import Node, NodeConfig, run

from robodog_sdk import RobotClient, TaskState


class PatrolConfig(NodeConfig):
    #: Corners of the patrol route, map-frame meters, visited in order.
    waypoints: list[tuple[float, float]] = [(1.0, 0.0), (1.0, 1.0), (0.0, 1.0), (0.0, 0.0)]
    #: How many rounds to patrol; 0 means until stopped.
    loops: int = 0
    #: Seconds to allow per leg.
    leg_timeout: float = 120.0


class Patrol(Node):
    name = "patrol"
    config: PatrolConfig

    robot: RobotClient
    #: Waypoints reached so far (read by the guide's tests).
    completed: int = 0

    async def on_start(self) -> None:
        self.robot = RobotClient(self)
        self.spawn(self._patrol(), name="patrol")

    async def _patrol(self) -> None:
        try:
            await self.robot.wait_for_nav(timeout=5.0)
        except TimeoutError:
            self.log.error("no navigation coordinator — is the stack up?")
            self.stop()
            return

        rounds = 0
        while self.config.loops == 0 or rounds < self.config.loops:
            for x, y in self.config.waypoints:
                if not await self._drive_leg(x, y):
                    self.stop()
                    return
            rounds += 1
            self.log.info("round %d complete", rounds)
        self.stop()

    async def _drive_leg(self, x: float, y: float) -> bool:
        """Drive one leg; return False when the patrol should end."""
        # A tripped e-stop or a human on the gamepad outranks a patrol.
        # Wait rather than fight: priority is decided per command anyway.
        while not self.robot.motion_permitted():
            self.log.info("motion not permitted — waiting")
            await asyncio.sleep(1.0)
        if self.robot.preempted_by is not None:
            self.log.info("preempted by %s — waiting", self.robot.preempted_by.value)
            await asyncio.sleep(1.0)

        result = await self.robot.navigate_to(x, y, timeout=self.config.leg_timeout)
        if result.state is TaskState.SUCCEEDED:
            self.completed += 1
            self.log.info("reached (%.1f, %.1f)", x, y)
            return True
        self.log.warning("leg to (%.1f, %.1f) ended %s: %s",
                         x, y, result.state.value, result.message)
        return False


def cli() -> None:
    run(Patrol)


if __name__ == "__main__":
    cli()
