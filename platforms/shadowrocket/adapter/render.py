#!/usr/bin/env python3
"""
Shadowrocket Renderer
Outputs conf-style text similar to Loon/Surge group rules.
"""

from typing import Any, Dict, List

def _resolve(opt: str, id_to_display: Dict[str, str]) -> str:
    if opt in ("direct", "DIRECT"):
        return "DIRECT"
    if opt in ("reject", "REJECT"):
        return "REJECT"
    return id_to_display.get(opt, opt)

def render(ir: Any) -> str:
    id_to_display = dict(getattr(ir, "id_to_display", {}) or {})
    for g in getattr(ir, "base_groups", []) or []:
        name = g.get("name", {})
        display = name.get("zh") if isinstance(name, dict) else str(name)
        id_to_display[g["id"]] = display or g["id"]

    lines: List[str] = []
    lines.append("# AUTO-GENERATED from Core — DO NOT EDIT MANUALLY")
    lines.append("[General]")
    lines.append("ipv6 = true")
    lines.append("")
    lines.append("[Proxy Group]")

    for g in getattr(ir, "base_groups", []) or []:
        name = id_to_display.get(g["id"], g["id"])
        policies = []
        for o in g.get("options") or []:
            if isinstance(o, dict):
                if "ref" in o:
                    policies.append(id_to_display.get(o["ref"], o["ref"]))
                elif "action" in o:
                    act = o["action"]
                    policies.append("DIRECT" if act == "direct" else "REJECT" if act == "reject" else act)
            else:
                policies.append(_resolve(str(o), id_to_display))
        if g.get("include-all-nodes"):
            policies = policies or ["DIRECT"]
        lines.append(f"{name} = select, {', '.join(policies or ['DIRECT'])}")

    for s in getattr(ir, "services", []) or []:
        if hasattr(s, "id"):
            name, options, default = s.name_zh, s.proxy_options, s.proxy_default
            sid = s.id
        else:
            sid = s["id"]
            name = (s.get("name") or {}).get("zh", sid)
            options = (s.get("proxy") or {}).get("options") or []
            default = (s.get("proxy") or {}).get("default")
        id_to_display[sid] = name
        policies = [_resolve(str(o), id_to_display) for o in options]
        if default:
            d = _resolve(default, id_to_display)
            if d in policies:
                policies = [d] + [p for p in policies if p != d]
        lines.append(f"{name} = select, {', '.join(policies or ['DIRECT'])}")

    lines.append("")
    lines.append("[Rule]")
    for r in getattr(ir, "rules", []) or []:
        target = id_to_display.get(r.get("_group"), r.get("_group", "其它连接"))
        rtype = r.get("type", "")
        values = r.get("values") or []
        if rtype == "domain-suffix":
            for v in values:
                lines.append(f"DOMAIN-SUFFIX,{v},{target}")
        elif rtype == "domain-keyword":
            for v in values:
                lines.append(f"DOMAIN-KEYWORD,{v},{target}")
        elif rtype == "geoip":
            for v in values:
                lines.append(f"GEOIP,{v},{target}")
        elif rtype == "geosite":
            for v in values:
                lines.append(f"DOMAIN-SUFFIX,{v},{target}")
        elif rtype == "match":
            lines.append(f"FINAL,{target}")
    if not any(x.startswith("FINAL,") for x in lines):
        lines.append(f"FINAL,{id_to_display.get('final', '其它连接')}")

    return "\n".join(lines) + "\n"
