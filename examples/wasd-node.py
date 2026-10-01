from typing import Any

import pygame
from zenode import Node, every, publish, run, subscribe

from robodog_sdk import (
    MotionTopics,
    MovementCommand,
    MovementSource,
    OdometryState,
    RobotClient,
    StateTopics,
)

#: Teleop speeds, m/s and deg/s — well inside the envelope in robodog_sdk.limits.
TELEOP_LINEAR_MS = 0.5
TELEOP_YAW_DEG = 60.0


class WasdNode(Node):
    name = "wasd-node"

    # get topic to publish to
    # mtopic = publish(MotionTopics.move) # raw movement
    mtopic = publish(MotionTopics.request)  # seve movement

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        pygame.init()
        pygame.display.set_mode((320, 120))
        pygame.display.set_caption("Teleop — WASD, Q to quit")

    async def on_start(self) -> None:
        self.robot = RobotClient(self)

    @every(interval=30, unit="hz")
    async def wasd_mover(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.stop()
                return
            if event.type == pygame.KEYDOWN and event.key == pygame.K_q:
                self.stop()
                return

        keys = pygame.key.get_pressed()
        x = TELEOP_LINEAR_MS * (keys[pygame.K_w] - keys[pygame.K_s])
        z_deg = TELEOP_YAW_DEG * (keys[pygame.K_a] - keys[pygame.K_d])

        self.mtopic.put(MovementCommand(x=x, z_deg=z_deg, source=MovementSource.assisted_teleop))

    @subscribe(StateTopics.odometry, mode="latest")
    async def on_pose(self, msg: OdometryState) -> None:
        if msg.x > 2.0:
            self.robot.halt()

    async def on_stop(self) -> None:
        self.log.info("stop")
        self.mtopic.put(MovementCommand())


def cli() -> None:
    run(WasdNode)


if __name__ == "__main__":
    cli()
