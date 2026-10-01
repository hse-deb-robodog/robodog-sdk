"""Define your own topic and message type — the contract pattern, for you.

    uv run python detections.py   # runs the detector

Everything the SDK does for the stack's topics you can do for your own:
a pydantic model as the payload schema, a Topic binding it to a key, and
publishers/subscribers on both ends that agree by construction.
"""

from __future__ import annotations

from pydantic import BaseModel
from zenode import Node, Topic, TopicSet, every, publish, run, subscribe


class Detection(BaseModel):
    """One detected object, in the robot's body frame."""

    label: str
    confidence: float
    x: float
    y: float


class PerceptionTopics(TopicSet):
    detections = Topic("perception/detections", Detection)


class Detector(Node):
    """Publishes a (pretend) detection twice a second."""

    name = "detector"

    #: Class-level declaration, materialized once the node has started —
    #: the same pattern `contract_drive.py` uses for `cmd`.
    out = publish(PerceptionTopics.detections)

    @every(0.5)
    async def tick(self) -> None:
        self.out.put(Detection(label="ball", confidence=0.9, x=1.2, y=0.1))


class Alerter(Node):
    """Reacts to detections — a stand-in for whatever your project does."""

    name = "alerter"

    seen: list[Detection]

    async def on_start(self) -> None:
        self.seen = []

    @subscribe(PerceptionTopics.detections)
    async def on_detection(self, msg: Detection) -> None:
        self.seen.append(msg)
        self.log.info(f"{msg.label} at ({msg.x:.1f}, {msg.y:.1f})")


def cli() -> None:
    run(Detector)


if __name__ == "__main__":
    cli()
