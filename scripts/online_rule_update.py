#!/usr/bin/env python3
"""Conservative twice-daily online rule updater.

Only authoritative/static published IP ranges are eligible. Dynamic DNS results are ignored.
Additions are syntax-validated; removals require three consecutive successful misses and only
apply to entries previously owned by this updater.
"""
from __future__ import annotations
import argparse, json, re, urllib.request, ipaddress
from pathlib import Path
from datetime import datetime, timezone
import yaml

ROOT = Path(__file__).resolve().parents[1]
SERVICES = ROOT / "core/rules/services"
SOURCES = ROOT / "core/rules/sources.yaml"
STATE = ROOT / ".update/online_state.json"
RULE_RE = re.compile(r"^(?:DOMAIN|DOMAIN-SUFFIX|DOMAIN-KEYWORD|IP-CIDR|IP-CIDR6),([^,\s#]+)", re.I)
HOST_RE = re.compile(r"(?<![A-Za-z0-9_-])(?:[A-Za-z0-9](?:[A-Za-z0-9_-]{0,61}[A-Za-z0-9])?\.)+[A-Za-z]{2,63}(?![A-Za-z0-9_-])")

CLASSIFIERS = {
    "apple": {
        "apple-account": ("account.apple.com", "appleid.cdn-apple.com", "idmsa.apple.com", "gsa.apple.com", "identity.apple.com"),
        "icloud": ("icloud.com", "icloud-content.com", "setup.icloud.com", "gateway.icloud.com", "probe.icloud.com", "pong.icloud.com", "metrics.icloud.com"),
        "app-store": ("itunes.apple.com", "apps.apple.com", "mzstatic.com", "ppq.apple.com", "vpp.itunes.apple.com"),
        "apple-music": ("music.apple.com",), "apple-tv": ("tv.apple.com",),
        "apple-maps": ("maps.apple.com", "apple-mapkit.com"), "apple-push": ("push.apple.com",),
        "apple-updates": ("appldnld.apple.com", "gdmf.apple.com", "gg.apple.com", "gs.apple.com", "mesu.apple.com", "static.ips.apple.com"),
        "apple-intelligence": ("guzzoni.apple.com", "smoot.apple.com", "apple-relay.apple.com"),
        "apple-developer": ("developer.apple.com",),
        "apple": ("apple.com", "apple-cloudkit.com", "apple-dns.net", "cdn-apple.com", "aaplimg.com", "apple.news"),
    },
    "google": {
        "youtube": ("youtube.com", "youtu.be", "googlevideo.com", "ytimg.com", "youtube-nocookie.com", "youtubekids.com"),
        "google-play": ("play.google.com", "play.googleapis.com", "android.clients.google.com", "gvt1.com", "gvt2.com"),
        "fcm": ("fcm.googleapis.com", "fcmregistrations.googleapis.com", "firebaseinstallations.googleapis.com"),
        "gmail": ("gmail.com", "googlemail.com", "gmailusercontent.com"),
        "drive": ("drive.google.com", "docs.google.com", "sheets.google.com", "slides.google.com", "googledrive.com"),
        "google-maps": ("maps.google.com", "maps.googleapis.com", "maps.gstatic.com"),
        "google-photos": ("photos.google.com", "photos.googleusercontent.com", "ggpht.com"),
        "android": ("android.com", "androidify.com"),
        "google": ("google.com", "googleapis.com", "gstatic.com", "googleusercontent.com", "recaptcha.net", "g.co", "appspot.com", "withgoogle.com"),
    },
}

def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "Proxy-Config-Center/4.1 rule-updater"})
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.read().decode("utf-8", "replace")

def valid_candidate(value: str) -> bool:
    value = value.strip().lower().rstrip(".")
    try:
        ipaddress.ip_network(value, strict=False)
        return True
    except ValueError:
        pass
    return bool(re.fullmatch(r"(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}", value))

def extract(text: str) -> tuple[set[str], set[str]]:
    domains, cidrs = set(), set()
    for line in text.splitlines():
        line = line.strip()
        m = RULE_RE.match(line)
        if m:
            value = m.group(1).strip().lower()
            try:
                net = ipaddress.ip_network(value, strict=False)
                cidrs.add(str(net)); continue
            except ValueError: pass
            if valid_candidate(value): domains.add(value.rstrip("."))
            continue
        for host in HOST_RE.findall(line):
            host = host.lower().rstrip(".")
            if valid_candidate(host): domains.add(host)
    return domains, cidrs

def extract_microsoft_json(text: str) -> tuple[set[str], set[str]]:
    try: data = json.loads(text)
    except json.JSONDecodeError: return set(), set()
    domains, cidrs = set(), set()
    for item in data if isinstance(data, list) else []:
        for value in item.get("urls", []) or []:
            value = value.strip().lower().lstrip("*.")
            if valid_candidate(value): domains.add(value)
        for value in item.get("ips", []) or []:
            if valid_candidate(value):
                try: cidrs.add(str(ipaddress.ip_network(value, strict=False)))
                except ValueError: pass
    return domains, cidrs

def load_state():
    return json.loads(STATE.read_text()) if STATE.exists() else {"owned": {}, "misses": {}, "updated_at": None}

def save_state(state):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    state["updated_at"] = datetime.now(timezone.utc).isoformat()
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True) + "\n")

def service_for(source: str, value: str) -> str:
    low = value.lower()
    for service, needles in CLASSIFIERS.get(source, {}).items():
        if any(low == n or low.endswith("." + n) for n in needles): return service
    return source

def load_service(path): return yaml.safe_load(path.read_text())

def add_values(doc, domains, cidrs):
    changed = False
    for rule in doc.get("rules", []):
        typ = rule.get("type")
        if typ == "domain-suffix" and domains:
            old = set(map(str.lower, rule.get("values", []))); new = sorted(old | domains)
            if new != rule.get("values", []): rule["values"] = new; changed = True
        elif typ in ("ip-cidr", "ip-cidr6") and cidrs:
            old = set(rule.get("values", [])); wanted = {x for x in cidrs if (":" in x) == (typ == "ip-cidr6")}
            new = sorted(old | wanted)
            if new != rule.get("values", []): rule["values"] = new; changed = True
    if domains and not any(r.get("type") == "domain-suffix" for r in doc.get("rules", [])):
        doc.setdefault("rules", []).append({"type":"domain-suffix","values":sorted(domains),"action":"group","target":doc.get("group")}); changed=True
    return changed

def run(dry=False):
    cfg = yaml.safe_load(SOURCES.read_text()); state = load_state(); observed={}; failures=[]
    for feed in cfg.get("feeds", []):
        source, url = feed["source"], feed["url"]
        try:
            text = fetch(url)
            domains, cidrs = extract_microsoft_json(text) if source == "microsoft" else extract(text)
            if not domains and not cidrs: raise RuntimeError("no valid candidates")
        except Exception as exc:
            failures.append(f"{source}: {exc}"); continue
        for value in domains | cidrs:
            service = service_for(source, value)
            observed.setdefault(service, {"domains":set(),"cidrs":set()})
            (observed[service]["cidrs"] if "/" in value else observed[service]["domains"]).add(value)
    if not observed: raise SystemExit("all online sources failed; refusing changes")

    changed=set()
    for service, vals in observed.items():
        path=SERVICES/f"{service}.yaml"
        if not path.exists(): continue
        doc=load_service(path)
        if add_values(doc, vals["domains"], vals["cidrs"]): changed.add(path)
        owned=state.setdefault("owned",{}).setdefault(service,[])
        state["owned"][service]=sorted(set(owned)|vals["domains"]|vals["cidrs"])
        for value in vals["domains"]|vals["cidrs"]: state.setdefault("misses",{}).pop(f"{service}:{value}",None)
        if not dry and path in changed: path.write_text(yaml.safe_dump(doc,sort_keys=False,allow_unicode=True))

    threshold=int(cfg.get("policy",{}).get("removals_require_consecutive_misses",3))
    for service, owned in list(state.get("owned",{}).items()):
        current=observed.get(service,{"domains":set(),"cidrs":set()}); current_set=current["domains"]|current["cidrs"]
        path=SERVICES/f"{service}.yaml"
        if not path.exists(): continue
        doc=load_service(path)
        for value in list(owned):
            if value in current_set: continue
            key=f"{service}:{value}"; misses=int(state.setdefault("misses",{}).get(key,0))+1; state["misses"][key]=misses
            if misses < threshold: continue
            removed=False
            for rule in doc.get("rules",[]):
                vals=rule.get("values",[])
                if value in vals: rule["values"]=[v for v in vals if v!=value]; removed=True
            if removed: changed.add(path)
            state["owned"][service]=[v for v in state["owned"][service] if v!=value]
        if not dry and path in changed: path.write_text(yaml.safe_dump(doc,sort_keys=False,allow_unicode=True))
    if not dry: save_state(state)
    print(json.dumps({"changed":sorted(str(p.relative_to(ROOT)) for p in changed),"source_failures":failures,"observed_services":len(observed)},ensure_ascii=False,indent=2))

if __name__ == "__main__":
    p=argparse.ArgumentParser(); p.add_argument("--dry-run",action="store_true"); run(p.parse_args().dry_run)
