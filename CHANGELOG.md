# Changelog

## [Unreleased]

### Added
- Strict capability schema and complete rule capability matrix
- Cross-file reference graph validation and rule priority constraints
- Full generated-config golden snapshot fingerprints
- Cached rule-source health checks with optional SHA-256 integrity pins
- Large Core/platform diff safety gate
- Version validation and release artifact attestation

### Changed
- Capability resolution is fail-fast; missing profiles and dependency failures no longer silently degrade builds
- `rule_set`, `rule_provider`, and `domain_fallback` are modeled independently
- Generated `build/` and `final/` configuration files are no longer auto-committed by CI
- Releases build fresh artifacts from source and generate GitHub release notes automatically

## [1.0.0] - 2026-08-08

### Added
- Core V1: DNS three-layer model, unified strategy groups, rule priority
- Rule Engine / DNS Engine / Proxy Policy V1
- Full rules: ads, China, Apple, AI, Google, YouTube, Spotify, Telegram, Twitter, Netflix, TikTok, Game, E-Hentai
- Icons via ClashTools CDN
- Renderers: Clash Meta, Clash, Stash, Egern, Loon, Shadowrocket
- CI: validate, semantic/golden tests, build, artifact
- Release workflow on tag `v*`

### Notes
- Nodes managed by Sub-Store only
- Configs are generated from Core; CI artifacts and releases are the distribution mechanism
