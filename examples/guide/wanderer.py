"""Close the loop: drive forward until the robot has covered a distance.

    uv run python examples/guide/wanderer.py

Publishing one command per odometry message keeps the command stream fresher
than the 0.3 s expiry, so the deadman never trips while data flows — and if
data stops flowing, stopping is exactly what should happen.
"""

from __future__ import annotations

from zenode import Node, NodeConfig, run, subscribe

from robodog_sdk import OdometryState, RobotClient, StateTopics


class WanderConfig(NodeConfig):
    #: Forward speed in m/s.
    speed: float = 0.3
    #: Stop after covering this distance along x, in meters.
    distance: float = 1.0


class Wanderer(Node):
    name = "wanderer"
    config: WanderConfig

    robot: RobotClient

    async def on_start(self) -> None:
        self.robot = RobotClient(self)

    @subscribe(StateTopics.odometry, mode="latest")
    async def on_odometry(self, msg: OdometryState) -> None:
        if msg.x < self.config.distance:
            self.robot.move(x=self.config.speed)
        else:
            self.robot.halt()


def cli() -> None:
    run(Wanderer)


if __name__ == "__main__":
    cli()
