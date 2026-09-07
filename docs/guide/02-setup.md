# Set up the simulated robot

```{note}
**In this chapter:** install the prerequisites; start the simulated robot
with one command; verify it by sending it somewhere from your browser.
```

Prerequisites: chapter 1 read; a laptop with about 8 GB of RAM free.

## What you need

1. **Docker.** On Windows or macOS, install
   [Docker Desktop](https://www.docker.com/products/docker-desktop/) and
   start it. On Linux, install the
   [Docker Engine](https://docs.docker.com/engine/install/) for your
   distribution.
2. **[uv](https://docs.astral.sh/uv/).** This is the Python package and
   project manager you will use throughout the guide. Follow the
   [installation instructions](https://docs.astral.sh/uv/getting-started/installation/)
   for your platform.
3. **Python 3.11 or newer.** If your system does not have one, you do not
   need to install it separately — `uv python install 3.12` gets you a
   working interpreter that uv manages for you.

## Start the appliance

1. Download
   [`sim/compose.yaml`](https://github.com/hse-deb-algo-athlets/robodog-sdk/blob/main/sim/compose.yaml)
   into an empty directory on your laptop.
2. In that directory, run:

   ```bash
   docker compose up
   ```

   **What you should see:** Docker pulls the images the first time, then
   starts three services — `zenoh-router`, `sim-stack`, `mola` — and the
   terminal fills with interleaved log lines from the simulation as it
   comes up. Leave this terminal running; the stack stops when you stop
   it.
3. Open `http://localhost:8080` in your browser. You should see the
   simulated robot standing in an empty scene, in a web viewer you can
   orbit and zoom with the mouse.

## Send the robot somewhere — no code yet

1. Open the nav UI at `http://localhost:8081`.

   🚧 TODO(fabian): confirm nav-map port + a screenshot of the UI

2. Click a point on the map to send it as a navigation goal.
3. Switch back to the viewer at `http://localhost:8080` and watch the
   robot walk to the point you clicked.

```{tip}
Keep this browser page in mind for the rest of the guide: it is your
control experiment forever after. If clicking a goal in the nav UI moves
the robot but your own code doesn't, the problem is in your code, not in
the stack.
```

## macOS

Docker Desktop on macOS runs containers in a Linux virtual machine, and
that VM does not give MuJoCo's renderer access to your GPU. The simulation
itself is too slow to be useful there. Run it as a hybrid instead: the
router and SLAM stay in Docker, and the simulation runs natively on your
Mac.

1. Start only the containerized services:

   ```bash
   docker compose up zenoh-router mola
   ```

2. Run the simulation natively, pointed at the router from step 1.

   🚧 TODO(fabian): exact native-sim install/run commands for macOS once
   verified on the prof's machine (MUJOCO_GL=glfw, uv run sim against
   localhost router)

## Running the stack from source (optional)

If you are developing the control stack itself, or your platform can't run
the published images, you can run the stack from source instead of Docker
images. This requires access to the private
[`hse-deb-algo-athlets/robodog-digipro`](https://github.com/hse-deb-algo-athlets/robodog-digipro)
repository — ask your instructor for access. Once you have it, its
README/setup guide has the full instructions; the quick start is:
`uv sync --all-extras` to install dependencies, copy
`config/config.toml.example` to a working config file, start the Zenoh
router with that repository's own `docker compose` file, then `uv run sim`
to run the simulation itself.

```{warning}
**Troubleshooting**

- *Port 7447 already in use* — something else on your machine is already
  listening on that port (perhaps a previous `docker compose up` you
  forgot was running). Stop it, or stop the other process, then try again.
- *Docker Desktop not running* — `docker compose up` fails immediately
  with a connection error. Start Docker Desktop and wait for it to report
  it is running, then retry.
- *Viewer is black or empty* — give the simulation about 10 seconds to
  finish starting up after the log lines appear, then reload
  `http://localhost:8080`.
```

## Where to go next

Continue to chapter 3, where you create your own project and write your
first node. For the full map of processes and topics, see Architecture
<!-- link when concepts/architecture.md exists -->.
