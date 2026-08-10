# Changelog

## [2.1.0] - 2026-08-11

Complete compiler pipeline with Optimizer strategies and Release tag immutability gate.

- Security Policy abstraction, Platform IR, Compiler Pipeline, Rule Normalization
- Optimizer: drop_empty, dedup, merge_domain_suffix, shadow_prune, priority_sort
- Release tag gate: VERSION match, no retag, workflow contract, pins
- Artifact immutability pins + full integration tests

## [2.0.0] - 2026-08-10

Core V2 DNS leak-resistant baseline.
