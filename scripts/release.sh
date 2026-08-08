#!/usr/bin/env bash
# Release helper — run from repo root
set -euo pipefail

VERSION="${1:-1.0.0}"
TAG="v${VERSION}"

echo "=== Proxy-Config-Center Release $TAG ==="

pip install -q pyyaml
python scripts/validate.py
python tests/test_semantic.py
python tests/test_golden.py
python scripts/build.py
python scripts/check_config.py

echo "$VERSION" > VERSION

git add -A
git status
git commit -m "release: $TAG" || echo "(no new commit)"
git tag -f "$TAG"
git push origin HEAD
git push origin "$TAG" --force

echo "Done. GitHub Actions will create the Release with configs zip."
echo "https://github.com/cn-wanmei/Proxy-Config-Center/releases"
