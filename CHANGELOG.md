# Changelog

All notable changes to this project are documented in this file. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

No unreleased changes yet.

## [0.2.0] - 2026-08-24

### Added

- Official no-auth TED v3 Search API connector with bounded pagination and iteration support.
- Deterministic TED-to-Tender mapping for public notice metadata, CPV, NUTS, values, dates, and URLs.
- `opentradeintel ted search` and `opentradeintel ted match` workflows.
- Score-neutral exact CPV tie-break signal without changing the documented 0–100 formula.
- Reproducible 20-opportunity/30-product synthetic matcher benchmark.
- Optional live TED smoke test excluded from default CI.

### Changed

- TED pagination deduplicates notices by publication number and rejects stalled page sequences.
- TED HTTP responses are streamed under a documented 16 MiB decoded-body ceiling.
- `ted match` returns at most ten matches per notice by default.
- Human-readable CLI output neutralizes terminal and bidirectional control characters from remote text.

## [0.1.0] - 2026-08-24

### Added

- Typed tender and product models.
- JSON and CSV ingestion with connector/parser interfaces.
- Local normalization and deterministic explainable matching.
- Shared application service, Typer CLI, and FastAPI endpoints.
- Dependency-free MCP adapter and optional provider protocol.
- Synthetic examples, automated tests, Docker support, and OSS project files.

[Unreleased]: https://github.com/b2baitrade-ui/opentradeintel/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/b2baitrade-ui/opentradeintel/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/b2baitrade-ui/opentradeintel/releases/tag/v0.1.0
