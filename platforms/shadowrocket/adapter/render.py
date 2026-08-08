#!/usr/bin/env python3
"""Shadowrocket — no rule_provider → domain_suffix fallback."""

import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))

from engines.rules_emit import emit_shadowrocket_style
from engines.capability import platform_from_adapter_file

PLATFORM = platform_from_adapter_file(__file__)


def _resolve(opt: str, m: Dict[str, str]) -> str:
    if opt in ("direct", "DIRECT"):
        return "DIRECT"
    if opt in ("reject", "REJECT"):
        return "REJECT"
    return m.get(opt, opt)


def render(ir: Any) -> str:
    m = dict(getattr(ir, "id_to_display", {}) or {})
    lines: List[str] = [
        "# AUTO-GENERATED | domain_suffix fallback (no rule_provider)",
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
        lines.append(f"{d} = select, {', '.join(pols or ['DIRECT'])}")
    for s in getattr(ir, "services", []) or []:
        m[s.id] = s.name_zh
        pols = [_resolve(str(o), m) for o in s.proxy_options]
        dd = _resolve(s.proxy_default, m)
        if dd in pols:
            pols = [dd] + [p for p in pols if p != dd]
        lines.append(f"{s.name_zh} = select, {', '.join(pols or ['DIRECT'])}")

    lines += ["", "[Rule]"]
    lines.extend(emit_shadowrocket_style(ir, m))
    return "\n".join(lines) + "\n"
