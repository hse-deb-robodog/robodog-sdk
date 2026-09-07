# robodog-sdk

```{toctree}
:hidden:

guide/index
concepts/index
reference/index
```

`robodog-sdk` is the Python package your program uses to control the
Robodog, a Unitree Go2 driven by a control stack you talk to over the
network. It is for students building their own software on top of that
stack, built on [zenode](https://hse-deb-algo-athlets.github.io/zenode/).

::::{grid} 1 1 3 3
:gutter: 3

:::{grid-item-card} Guide
:link: guide/index
:link-type: doc

New here? Start at chapter 1, from empty laptop to your code driving the
robot.
:::

:::{grid-item-card} Concepts
:link: concepts/index
:link-type: doc

How the system works under the hood.
:::

:::{grid-item-card} Reference
:link: reference/index
:link-type: doc

Every topic, class and exception.
:::

::::

## Install

```bash
uv add "robodog-sdk @ git+https://github.com/hse-deb-algo-athlets/robodog-sdk@v%%SDK_VERSION%%"
```

Two dependencies (`zenode`, `pydantic`), no hardware or simulation packages,
so it installs on any laptop in seconds. The optional `livox` extra adds CDR
point-cloud decoding for the externally-produced `livox/lidar` topic:

```bash
uv add "robodog-sdk[livox] @ git+https://github.com/hse-deb-algo-athlets/robodog-sdk@v%%SDK_VERSION%%"
```

Semantic versioning: `0.x` may move keys between minor versions, so pin the
tag shown here.

## License

Apache License 2.0. See
[LICENSE](https://github.com/hse-deb-algo-athlets/robodog-sdk/blob/main/LICENSE)
and [NOTICE](https://github.com/hse-deb-algo-athlets/robodog-sdk/blob/main/NOTICE).
Copyright 2026 Hochschule Esslingen.
