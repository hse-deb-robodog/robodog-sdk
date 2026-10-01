# Contributing to robodog-sdk

This document is for changing the SDK itself. If you only want to *use* the
SDK in your project, you never need it: start with the
[guide](https://hse-deb-robodog.github.io/robodog-sdk/guide/) instead.

## When a change belongs in the SDK

The SDK is the shared contract between every project and the control stack.
That gives a simple rule for where code lives:

- **A topic or message type belongs here** when it crosses the wire to the
  control stack, or when more than one project needs it. The contract is only
  useful if both sides import the same definition.
- **It belongs in your own project** when only your team uses it. Chapter 8
  of the guide shows the pattern: your own `TopicSet` and pydantic models,
  with the same machinery, in your own repository. Nothing about that
  requires touching the SDK.

A topic that starts team-specific and turns out to be useful to others is a
good SDK candidate. Open an issue describing the topic, its payload, and who
publishes it, and it can graduate into the contract with the next release.

Two more things live here and follow the same logic: `RobotClient`
conveniences that any project would want, and the test doubles in
`robodog_sdk.testing`. Robot capability limits live in
`robodog_sdk.limits`; if a limit is wrong, fix it there rather than working
around the model in your project.

Keep the dependency rule in mind: the package deliberately depends on
`zenode` and `pydantic` only. Anything that needs more (OpenCV, NumPy,
MuJoCo, serial drivers) is a node, and nodes belong in the stack repository
or in your project.

## Making a change

1. Branch from `main` and make the change, including tests. The examples
   under `examples/` are tested in CI, so if your change affects documented
   behavior, the guide examples and their tests in
   `tests/test_guide_examples.py` need to keep passing, and possibly need
   updating.

2. Run the same gates CI runs:

   ```bash
   uv run pytest
   uv run ruff check --fix && uv run ruff format
   uv run pyright
   uv run --group docs sphinx-build -W docs docs/_build/html
   ```

3. Add an entry under `## [Unreleased]` in `CHANGELOG.md`. The changelog is
   written for consumers who pin a tag: say what changes for them and what,
   if anything, they must do about it. Look at the existing entries for the
   expected level of detail.

4. If the change moves or adds topic keys, update the affected docs pages
   (the topic reference at `docs/reference/topics.md` at minimum) in the same
   pull request. The docs build is a CI gate, so a stale cross-reference
   fails the build anyway.

5. Open a pull request against `main` and get it reviewed.

## Releasing a version

A release is a git tag. The `release` workflow does the rest: it verifies
the tag against `pyproject.toml`, builds the sdist and wheel, runs the test
suite against the built wheel (so packaging mistakes fail the release, not a
student's install), and creates a GitHub release with generated notes.

The steps:

1. Decide the version. Semantic versioning; while the project is `0.x`, a
   minor bump (`0.2.x` to `0.3.0`) signals that topic keys or APIs may have
   moved, and a patch bump signals additions and fixes that break nobody.
   `CONTRACT_VERSION` is the package version, so it moves automatically with
   every release.

2. In one commit on `main`:
   - bump `version` in `pyproject.toml`,
   - rename `## [Unreleased]` in `CHANGELOG.md` to the new version with
     today's date, and add a fresh empty `## [Unreleased]` above it.

3. Tag and push:

   ```bash
   git tag v0.3.0
   git push origin main v0.3.0
   ```

   The tag must match the `pyproject.toml` version exactly (the workflow
   checks), and it must be `v`-prefixed.

4. Check that the release workflow went green and the release appeared on
   the [releases page](https://github.com/hse-deb-robodog/robodog-sdk/releases).
   Then tell the people who need to update; the guide's
   [updating section](https://hse-deb-robodog.github.io/robodog-sdk/guide/03-first-project.html#updating-the-sdk-later)
   covers their side.

🚧 TODO(fabian): who is allowed to tag releases: maintainers only, or any
contributor after review? Write the policy here.

🚧 TODO(fabian): when the SDK moves topic keys, the control stack must move
in the same coordinated release. Describe how that coordination works
(matching digipro release? deployment order on the dog and the appliance
images?).

Publishing to PyPI is planned but not active; it needs `zenode` on PyPI
first, since a wheel cannot depend on a git URL. Until then, consumers
install from the git tag.

## Documentation

The docs live in `docs/` (Sphinx, MyST Markdown) and deploy from `main`.
Guide code examples are real files under `examples/guide/`, pulled into the
pages with `literalinclude` and tested in CI; edit the file, and the docs
and tests follow. Install snippets use the literal token `%%SDK_VERSION%%`,
which the build replaces with the installed version, so never hard-code a
version into a docs page.
