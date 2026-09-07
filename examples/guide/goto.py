"""Send the robot somewhere and handle every way that can end.

    uv run python examples/guide/goto.py

A navigation goal is a *task*: you submit it, the stack works on it, and it
ends in exactly one of four states. Only SUCCEEDED means the robot arrived.
BLOCKED is not an error — the robot met the world and stopped trying.
"""

from __future__ import annotations

from zenode import Node, NodeConfig, run

from robodog_sdk import RobotClient, TaskResult, TaskState


class GotoConfig(NodeConfig):
    #: Goal position in the map frame, in meters.
    x: float = 1.0
    y: float = 0.5
    #: Seconds to wait for the task before giving up on it.
    timeout: float = 120.0


class Goto(Node):
    name = "goto"
    config: GotoConfig

    robot: RobotClient
    #: The task's outcome, kept for inspection (and for the guide's tests).
    result: TaskResult | None = None

    async def on_start(self) -> None:
        self.robot = RobotClient(self)
        self.spawn(self._run(), name="goto")

    async def _run(self) -> None:
        try:
            await self.robot.wait_for_nav(timeout=5.0)
        except TimeoutError:
            self.log.error("no navigation coordinator answered — is the stack up?")
            self.stop()
            return

        self.result = await self.robot.navigate_to(
            self.config.x, self.config.y, timeout=self.config.timeout
        )

        if self.result.state is TaskState.SUCCEEDED:
            self.log.info("arrived")
        elif self.result.state is TaskState.BLOCKED:
            self.log.warning("blocked on the way: %s", self.result.message)
        elif self.result.state is TaskState.CANCELED:
            self.log.warning("someone canceled the task: %s", self.result.message)
        else:  # TaskState.FAILED
            self.log.error("navigation failed: %s", self.result.message)
        self.stop()


def cli() -> None:
    run(Goto)


if __name__ == "__main__":
    cli()
