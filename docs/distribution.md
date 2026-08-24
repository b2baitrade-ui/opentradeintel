# Distribution and trusted publishing

## Package name status

On 2026-08-24, `https://pypi.org/pypi/opentradeintel/json` returned HTTP 404, so no published PyPI project currently occupies `opentradeintel`. This is a point-in-time observation, not a reservation guarantee. OpenTradeIntel will not publish under a different name automatically.

## Release workflow

`.github/workflows/publish.yml` runs only when a GitHub release is published:

1. a restricted build job installs the lockfile, reruns quality gates and the benchmark;
2. the release tag must equal both installed distribution metadata and the module version, and its commit must be an ancestor of `origin/main`;
3. the job builds and validates wheel/sdist artifacts;
4. the built wheel metadata version is checked against the release tag before immutable artifacts move to a separate publish job;
5. the publish job receives only `id-token: write` and uses PyPI Trusted Publishing;
6. the PyPI action generates and uploads digital attestations by default and is configured explicitly to do so.

All GitHub Actions are pinned to immutable commit SHAs with readable version comments. Dependabot remains responsible for proposed action updates.

The build backend is intentionally constrained to Hatchling 1.27.x. That line emits core metadata 2.4, which the locked Twine 6.2 validation path accepts; newer Hatchling output observed during release preparation used metadata 2.5 and failed that validator. Widen the backend range only after building both artifacts and rerunning `uv run twine check dist/*` with the proposed toolchain.

Artifacts include the workflow run-attempt number, so a rerun does not collide with an earlier immutable GitHub artifact. Production PyPI duplicates intentionally fail loudly: PyPA recommends avoiding `skip-existing` for PyPI, where silently accepting an existing file could hide a race or an unexpected publisher.

The `0.2.0` version is a SemVer minor release: it adds a major alpha-stage feature, commands, and optional source-neutral fields while preserving every v0.1 required model field, command, score component, and 0–100 scoring semantic.

The repository's `pypi` GitHub environment restricts deployments to tags matching `v*`. The `main` branch requires a pull request plus successful `Python 3.12`, `Python 3.13`, `Python 3.14`, and `CodeQL (Python)` checks; force pushes and deletion are disabled. Repository administrators retain a bypass so the sole maintainer is not locked out during recovery.

An active repository tag ruleset targets `v*` and prevents deletion or non-fast-forward updates after a release tag is created. The publish workflow independently verifies that the tagged commit is contained in `origin/main`.

## Required one-time PyPI action

Before publishing the first release, a PyPI account owner must create a pending Trusted Publisher with exactly:

| Field | Value |
| --- | --- |
| PyPI project name | `opentradeintel` |
| GitHub owner | `b2baitrade-ui` |
| GitHub repository | `opentradeintel` |
| Workflow filename | `publish.yml` |
| Environment | `pypi` |

Use PyPI's **Your account -> Publishing -> Add a new pending publisher** page. No API token or repository secret is required. Publication must not be attempted until this one-time UI configuration is confirmed.

Official references:

- [Create a PyPI project through OIDC](https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/)
- [Publish with a Trusted Publisher](https://docs.pypi.org/trusted-publishers/using-a-publisher/)
- [PyPA publish action security guidance](https://github.com/pypa/gh-action-pypi-publish)
