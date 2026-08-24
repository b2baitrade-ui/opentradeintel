# Open-source readiness

This document records technical readiness signals; it is not a funding application and does not claim adoption or community activity that has not occurred.

## Project signals

- Public repository publication is part of the v0.1 release process.
- Apache License 2.0 grants clear source and patent permissions.
- Installation and runnable CLI/API examples are documented.
- CI checks supported Python versions, lint, formatting, types, dead code, branch coverage, and container health.
- Automated behavior tests cover domain, ingestion, normalization, scoring, CLI, and API.
- `SECURITY.md` defines supported versions and private reporting guidance.
- `CONTRIBUTING.md`, a Code of Conduct, issue forms, and a PR template support contributions.
- Releases are gated on local checks and green remote CI.
- Connector, parser, provider, and MCP adapter boundaries support incremental work.
- Dependabot, CodeQL, runtime dependency auditing, and full-history secret scanning provide maintainable baseline automation.

## Good tasks for coding agents

- Implement a new connector against a documented public source.
- Repair a parser regression from a minimal synthetic fixture.
- Generate focused edge-case tests with hand-checked expected values.
- Review a pull request for contract, privacy, and compatibility risks.
- Triage reproducible issues and identify the smallest failing test.
- Maintain documentation when commands or interfaces change.
- Prepare release notes from verified commits and changelog entries.
- Review dependencies, workflow permissions, and input-validation paths.

Agent-produced changes should remain subject to maintainer review, deterministic tests, secret scanning, and repository policy. Automated activity must not fabricate users, adoption, issues, stars, testimonials, benchmarks, or contributor identities.
