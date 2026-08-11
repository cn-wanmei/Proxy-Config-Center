#!/usr/bin/env python3
"""Fetch trusted public service feeds, merge verified domains/IPs, and retire stale auto-owned entries.

The updater is deliberately conservative:
- network failures never delete rules;
- malformed candidates are ignored;
- removals require consecutive successful misses;
- dynamic DNS-resolved IPs are never learned automatically;
- only domains/IPs learned by this updater may be retired.
"""
from __future__ import annotations
import argparse, json, re, urllib.request
from pathlib import Path
from datetime import datetime, timezone
import ipaddress
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
        "apple-music": ("music.apple.com",),
        "apple-tv": ("tv.apple.com",),
        "apple-maps": ("maps.apple.com", "apple-mapkit.com"),
        "apple-push": ("push.apple.com",),
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
    if "://" in value or "/" in value and not re.match(r"^[0-9a-fA-F:.]+/\d+$", value):
        return False
    try:
        ipaddress.ip_network(value, strict=False)
        return True
    except ValueError:
        pass
    return bool(re.fullmatch(r"(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+[A-Za-z]{2,63}", value))

def extract(text: str) -> set[str]:
    out = set()
    for line in text.splitlines():
        line = line.strip()
        m = RULE_RE.match(line)
        if m:
            value = m.group(1).strip()
            if valid_candidate(value): out.add(value.lower())
            continue
        for host in HOST_RE.findall(line):
            host = host.lower().rstrip(".")
            if valid_candidate(host): out.add(host)
    return out

def load_state():
    if STATE.exists():
        return json.loads(STATE.read_text())
    return {"owned": {}, "misses": {}, "updated_at": None}

def save_state(state):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    state["updated_at"] = datetime.now(timezone.utc).isoformat()
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True) + "\n")

def service_for(source: str, value: str) -> str:
    if source in CLASSIFIERS:
        low = value.lower()
        for service, needles in CLASSIFIERS[source].items():
            if any(low == n or low.endswith("." + n) for n in needles):
                return service
    return source

def load_service(path: Path):
    return yaml.safe_load(path.read_text())

def add_values(doc, values):
    changed = False
    for rule in doc.get("rules", []):
        if rule.get("type") == "domain-suffix":
            existing = {str(v).lower() for v in rule.get("values", [])}
            new = sorted(existing | values)
            if new != rule.get("values", []):
                rule["values"] = new; changed = True
            return changed
    if values:
        doc.setdefault("rules", []).append({"type": "domain-suffix", "values": sorted(values), "action": "group", "target": doc.get("group")})
        return True
    return False

def run(dry=False):
    cfg = yaml.safe_load(SOURCES.read_text())
    state = load_state()
    observed = {}
    changed_files = set()
    source_failures = []
    for feed in cfg.get("feeds", []):
        source, url = feed["source"], feed["url"]
        try:
            text = fetch(url)
            values = extract(text)
            if not values:
                raise RuntimeError("no valid candidates")
        except Exception as exc:
            source_failures.append(f"{source}: {exc}")
            continue
        for value in values:
            service = service_for(source, value)
            observed.setdefault(service, set()).add(value)
    if source_failures and not observed:
        raise SystemExit("all online sources failed; refusing changes")

    for service, values in observed.items():
        path = SERVICES / f"{service}.yaml"
        if not path.exists():
            continue
        doc = load_service(path)
        domain_values = {v for v in values if not "/" in v}
        if add_values(doc, domain_values):
            changed_files.add(path)
        owned = state.setdefault("owned", {}).setdefault(service, [])
        state["owned"][service] = sorted(set(owned) | domain_values)
        for v in domain_values:
            state.setdefault("misses", {}).pop(f"{service}:{v}", None)
        if not dry and path in changed_files:
            path.write_text(yaml.safe_dump(doc, sort_keys=False, allow_unicode=True))

    # Retire only entries previously introduced by the updater, after 3 successful misses.
    threshold = int(cfg.get("policy", {}).get("removals_require_consecutive_misses", 3))
    for service, owned in list(state.get("owned", {}).items()):
        current = observed.get(service, set())
        path = SERVICES / f"{service}.yaml"
        if not path.exists(): continue
        doc = load_service(path)
        for value in list(owned):
            if value in current: continue
            key = f"{service}:{value}"
            misses = int(state.setdefault("misses", {}).get(key, 0)) + 1
            state["misses"][key] = misses
            if misses < threshold: continue
            removed = False
            for rule in doc.get("rules", []):
                vals = rule.get("values", [])
                if value in vals:
                    rule["values"] = [v for v in vals if v != value]
                    removed = True
            if removed:
                changed_files.add(path)
            state["owned"][service] = [v for v in state["owned"][service] if v != value]
        if not dry and path in changed_files:
            path.write_text(yaml.safe_dump(doc, sort_keys=False, allow_unicode=True))

    if not dry: save_state(state)
    print(json.dumps({"changed": sorted(str(p.relative_to(ROOT)) for p in changed_files), "source_failures": source_failures, "observed_services": len(observed)}, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    run(args.dry_run)
