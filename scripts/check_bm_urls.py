#!/usr/bin/env python3
"""Sample blackmatrix7 URL health check (observability, not full crawl)."""

import sys
import urllib.request
from pathlib import Path
from typing import List, Tuple

try:
    import yaml
except ImportError:
    print("PyYAML required")
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent
SOURCES = ROOT / "core" / "rules" / "sources.yaml"
BASE = "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule"
TIMEOUT = 8

# Critical samples: Clash yaml (Meta) + Surge list (Egern) + Loon list
SAMPLES: List[Tuple[str, str]] = [
    ("Clash/AdvertisingLite/AdvertisingLite.yaml", "clash-ad"),
    ("Clash/China/China.yaml", "clash-china"),
    ("Clash/Apple/Apple.yaml", "clash-apple"),
    ("Clash/GitHub/GitHub.yaml", "clash-github"),
    ("Clash/OpenAI/OpenAI.yaml", "clash-ai"),
    ("Surge/AdvertisingLite/AdvertisingLite.list", "surge-ad"),
    ("Surge/China/China.list", "surge-china"),
    ("Surge/ChinaIPs/ChinaIPs.list", "surge-china-ip"),
    ("Surge/Apple/Apple.list", "surge-apple"),
    ("Loon/YouTube/YouTube.list", "loon-youtube"),
]


def head_ok(url: str) -> Tuple[bool, str]:
    try:
        req = urllib.request.Request(url, method="HEAD")
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            code = getattr(resp, "status", 200)
            if code and int(code) >= 400:
                return False, f"HTTP {code}"
            return True, str(code or 200)
    except Exception as e:
        # some CDNs reject HEAD — try GET range
        try:
            req = urllib.request.Request(url, headers={"Range": "bytes=0-0"})
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                return True, f"GET {getattr(resp, 'status', 200)}"
        except Exception as e2:
            return False, f"{type(e2).__name__}: {e2}"


def urls_from_sources() -> List[str]:
    data = {}
    if SOURCES.exists():
        data = yaml.safe_load(SOURCES.read_text(encoding="utf-8")) or {}
    base = data.get("blackmatrix7_base") or f"{BASE}/Clash"
    out = []
    for sid, meta in (data.get("sources") or {}).items():
        bm = meta.get("blackmatrix7") if isinstance(meta, dict) else None
        if isinstance(bm, dict) and bm.get("path"):
            out.append(f"{base.rstrip('/')}/{bm['path']}")
    return out[:5]  # cap extra samples from sources


def main() -> int:
    print("=== BM URL health (sample) ===")
    failed = 0
    checked = []

    for rel, tag in SAMPLES:
        url = f"{BASE}/{rel}"
        ok, msg = head_ok(url)
        checked.append(url)
        if ok:
            print(f"✅ [{tag}] {msg} {url}")
        else:
            failed += 1
            print(f"❌ [{tag}] {msg} {url}")

    for url in urls_from_sources():
        if url in checked:
            continue
        ok, msg = head_ok(url)
        if ok:
            print(f"✅ [sources] {msg} {url}")
        else:
            failed += 1
            print(f"❌ [sources] {msg} {url}")

    if failed:
        print(f"\n⚠️  {failed} URL(s) failed (non-blocking in CI continue-on-error)")
        return 1
    print("\n✅ all sampled BM URLs OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
