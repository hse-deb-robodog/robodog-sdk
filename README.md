# robodog-sdk

The Python SDK for the Robodog, a Unitree Go2 quadruped run by a control
stack you talk to over the network. Install this package in your own project
and your code becomes a peer of every process in that stack: it can read the
robot's sensors, drive it, and send it navigation goals, against the real dog
or a simulation on your laptop. You never work inside the control stack
itself.

![The Robodog control stack processes around the central Zenoh router, with your node joining from outside on the same topics](docs/_static/architecture.svg)

Built on [zenode](https://github.com/hse-deb-algo-athlets/zenode), with
[pydantic](https://docs.pydantic.dev) message types. Those are the only two
dependencies, so it installs on any laptop in seconds.

## Documentation

The docs at <https://hse-deb-algo-athlets.github.io/robodog-sdk/> are the
place to start:

| Section | Covers |
|---|---|
| [Guide](https://hse-deb-algo-athlets.github.io/robodog-sdk/guide/) | New here? Start at chapter 1: from an empty laptop to your code driving the robot |
| [Concepts](https://hse-deb-algo-athlets.github.io/robodog-sdk/concepts/) | How the system works under the hood |
| [Reference](https://hse-deb-algo-athlets.github.io/robodog-sdk/reference/) | Every topic, class and exception |

## Install

```bash
uv add "robodog-sdk @ git+https://github.com/hse-deb-algo-athlets/robodog-sdk@v0.2.1"
```

Pin a tag: the project uses semantic versioning and `0.x` minor versions may
still move topic keys. Check the
[releases](https://github.com/hse-deb-algo-athlets/robodog-sdk/releases) page
for the current one.

## A taste

A complete node that watches the robot's position and stops it past a line:

```python
from zenode import Node, run, subscribe
from robodog_sdk import OdometryState, RobotClient, StateTopics


class Wanderer(Node):
    name = "wanderer"

    async def on_start(self) -> None:
        self.robot = RobotClient(self)

    @subscribe(StateTopics.odometry, mode="latest")
    async def on_pose(self, msg: OdometryState) -> None:
        if msg.x > 2.0:
            self.robot.halt()
```

Chapter 3 of the guide builds a file like this line by line, and chapter 2
brings up the simulated robot to run it against (one `docker compose up` with
[`sim/compose.yaml`](sim/compose.yaml)).

## What is in this repo

| Path | Contents |
|---|---|
| `src/robodog_sdk/` | The package: topics, message types, `RobotClient`, test doubles |
| `examples/` | Runnable example nodes, including everything the guide builds |
| `sim/` | The compose file for the simulated robot |
| `docs/` | The documentation sources |

## Development

For working on the SDK itself:

```bash
uv sync
uv run pytest
uv run ruff check --fix && uv run ruff format
uv run pyright
uv run --group docs sphinx-build -W docs docs/_build/html
```

## License

Apache License 2.0, see [LICENSE](LICENSE) and [NOTICE](NOTICE).
Copyright 2026 Hochschule Esslingen.
