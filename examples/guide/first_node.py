"""The guide's first node: subscribe to the robot's position and log it.

uv run python first_node.py
"""

from __future__ import annotations

from zenode import Node, run, subscribe

from robodog_sdk import OdometryState, StateTopics


class FirstNode(Node):
    name = "first-node"

    #: The most recent position, kept so other parts of the node can read it.
    last: OdometryState | None = None

    @subscribe(StateTopics.odometry, mode="latest")
    async def on_odometry(self, msg: OdometryState) -> None:
        self.last = msg
        self.log.info(f"robot at x={msg.x:.2f} m, y={msg.y:.2f} m")


def cli() -> None:
    run(FirstNode)


if __name__ == "__main__":
    cli()
