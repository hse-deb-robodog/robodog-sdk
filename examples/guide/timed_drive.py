"""Drive forward for a fixed time, then stop — the guide's first movement.

    uv run python examples/guide/timed_drive.py
"""

from __future__ import annotations

import asyncio

from zenode import Node, NodeConfig, run

from robodog_sdk import RobotClient


class DriveConfig(NodeConfig):
    #: Forward speed in m/s.
    speed: float = 0.3
    #: How long to drive, in seconds.
    duration: float = 2.0


class TimedDrive(Node):
    name = "timed-drive"
    config: DriveConfig

    robot: RobotClient

    async def on_start(self) -> None:
        self.robot = RobotClient(self)
        self.spawn(self._run(), name="drive")

    async def _run(self) -> None:
        # driving() republishes the command for as long as the block runs and
        # always stops the robot on the way out — even on an exception.
        async with self.robot.driving(x=self.config.speed):
            await asyncio.sleep(self.config.duration)
        self.log.info("done")
        self.stop()


def cli() -> None:
    run(TimedDrive)


if __name__ == "__main__":
    cli()
