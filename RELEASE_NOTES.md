# Release Notes — v2.2.0

## Theme

Architecturally cannot emit insecure DNS configuration.

## Kernel

- `SecureDNSEndpoint` / `BootstrapIP` typed constructors
- Dynamic policy profiles (`PROXY_POLICY_PROFILE`)
- Resolver intelligent scheduling
- Incremental compile fingerprints
- PlatformAdapter hard-fail before write
- `build.py` and `compiler.py` both use secure emit path

## Verify

```bash
make security && make compile_gate && make compile && make test && make golden
```

## Package

Source archive: `Proxy-Config-Center-2.2.0-src.tar.gz`

## Publish

GitHub Actions → Release → `release_tag=2.2.0`
