#!/usr/bin/env python3
"""Loon — capabilities-aware rules, policy groups and icons."""

import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))

from engines.capability import supports, supports_rule_set, platform_from_adapter_file
from engines.rules_emit import emit_loon_style

try:
    from engines.icons import icon_url
except Exception:
    def icon_url(name):
        return name if name and str(name).startswith("http") else None

PLATFORM = platform_from_adapter_file(__file__)


def _resolve(opt: str, m: Dict[str, str]) -> str:
    if opt in ("direct", "DIRECT"):
        return "DIRECT"
    if opt in ("reject", "REJECT"):
        return "REJECT"
    return m.get(opt, opt)


def _icon_suffix(icon_name: str) -> str:
    if not supports(PLATFORM, "icons"):
        return ""
    url = icon_url(icon_name)
    return f", img-url = {url}" if url else ""


def render(ir: Any) -> str:
    m = dict(getattr(ir, "id_to_display", {}) or {})
    lines: List[str] = [
        "# AUTO-GENERATED | capabilities-aware",
        "[General]",
        "ipv6 = true",
        "",
        "[Proxy Group]",
    ]
    for g in getattr(ir, "base_groups", []) or []:
        name = g.get("name", {})
        d = name.get("zh") if isinstance(name, dict) else str(name)
        m[g["id"]] = d or g["id"]
        pols = []
        for o in g.get("options") or []:
            if isinstance(o, dict):
                if "ref" in o:
                    pols.append(m.get(o["ref"], o["ref"]))
                elif "action" in o:
                    pols.append("DIRECT" if o["action"] == "direct" else "REJECT")
            else:
                pols.append(_resolve(str(o), m))
        if g.get("include-all-nodes") and not pols:
            pols = ["DIRECT"]
        gt = "url-test" if g.get("type") == "url-test" else "select"
        lines.append(f"{d} = {gt}, {', '.join(pols or ['DIRECT'])}{_icon_suffix(g.get('icon'))}")
    for s in getattr(ir, "services", []) or []:
        m[s.id] = s.name_zh
        pols = [_resolve(str(o), m) for o in s.proxy_options]
        dd = _resolve(s.proxy_default, m)
        if dd in pols:
            pols = [dd] + [p for p in pols if p != dd]
        lines.append(f"{s.name_zh} = select, {', '.join(pols or ['DIRECT'])}{_icon_suffix(s.icon)}")

    lines += ["", "[Rule]"]
    use_rs = supports_rule_set(PLATFORM)
    lines.extend(emit_loon_style(ir, m, use_rs))
    return "\n".join(lines) + "\n"
