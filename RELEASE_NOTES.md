# Release Notes — v2.1.0

## Summary

Formal 2.1.0 compiler release: Policy → Security → IR → Optimizer → Platform IR → Emit → Reverse Validate → Release Tag Gate.

## Highlights

- Security Policy abstraction (`core/security/policy.yaml`)
- Platform IR + unified `scripts/compiler.py` pipeline
- Rule normalization + Optimizer (dedup / merge / shadow_prune / priority_sort)
- Release tag immutability gate (no retag; VERSION must match)
- DNS leak-resistant defaults retained from 2.0
- Golden snapshots refreshed for 2.1 emit

## Verify before tag

```bash
make security && make compile_gate && make compile && make test && make golden
make release_tag_gate
```

## Publish

GitHub Actions → **Release** workflow → `workflow_dispatch` with `release_tag=2.1.0` (or `v2.1.0`).

Immutable: existing `v2.1.0` cannot be overwritten.
