#!/usr/bin/env python3
"""Shadowrocket — domain_suffix only (no GEOIP/GEOSITE)."""
from typing import Any, Dict, List

def _resolve(opt: str, m: Dict[str, str]) -> str:
    if opt in ("direct", "DIRECT"): return "DIRECT"
    if opt in ("reject", "REJECT"): return "REJECT"
    return m.get(opt, opt)

def render(ir: Any) -> str:
    m = dict(getattr(ir, "id_to_display", {}) or {})
    lines = ["# AUTO-GENERATED | blackmatrix7 via Core", "[General]", "ipv6 = true", "", "[Proxy Group]"]
    for g in getattr(ir, "base_groups", []) or []:
        name = g.get("name", {})
        d = name.get("zh") if isinstance(name, dict) else str(name)
        m[g["id"]] = d or g["id"]
        pols = []
        for o in g.get("options") or []:
            if isinstance(o, dict):
                if "ref" in o: pols.append(m.get(o["ref"], o["ref"]))
                elif "action" in o: pols.append("DIRECT" if o["action"]=="direct" else "REJECT")
            else: pols.append(_resolve(str(o), m))
        if g.get("include-all-nodes") and not pols: pols = ["DIRECT"]
        lines.append(f"{d} = select, {', '.join(pols or ['DIRECT'])}")
    for s in getattr(ir, "services", []) or []:
        m[s.id] = s.name_zh
        pols = [_resolve(str(o), m) for o in s.proxy_options]
        dd = _resolve(s.proxy_default, m)
        if dd in pols: pols = [dd]+[p for p in pols if p!=dd]
        lines.append(f"{s.name_zh} = select, {', '.join(pols or ['DIRECT'])}")
    lines += ["", "[Rule]"]
    for rs in getattr(ir, "rule_sources", []) or []:
        if rs.is_match: continue
        t = m.get(rs.target_service, rs.target_service)
        for d in rs.domain_suffix:
            lines.append(f"DOMAIN-SUFFIX,{d},{t}")
    lines.append(f"FINAL,{m.get('final','其它连接')}")
    return "\n".join(lines)+"\n"
