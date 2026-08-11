#!/usr/bin/env python3
"""Conservative twice-daily online rule updater."""
from __future__ import annotations
import argparse, json, re, urllib.request, ipaddress
from pathlib import Path
from datetime import datetime, timezone
import yaml
ROOT=Path(__file__).resolve().parents[1]; SERVICES=ROOT/"core/rules/services"; SOURCES=ROOT/"core/rules/sources.yaml"; STATE=ROOT/".update/online_state.json"
RULE_RE=re.compile(r"^(?:DOMAIN|DOMAIN-SUFFIX|DOMAIN-KEYWORD|IP-CIDR|IP-CIDR6),([^,\s#]+)",re.I); HOST_RE=re.compile(r"(?<![A-Za-z0-9_-])(?:[A-Za-z0-9](?:[A-Za-z0-9_-]{0,61}[A-Za-z0-9])?\.)+[A-Za-z]{2,63}(?![A-Za-z0-9_-])")
CLASSIFIERS={"apple":{"apple-account":("account.apple.com","appleid.cdn-apple.com","idmsa.apple.com","gsa.apple.com","identity.apple.com"),"icloud":("icloud.com","icloud-content.com","setup.icloud.com","gateway.icloud.com","probe.icloud.com","pong.icloud.com","metrics.icloud.com"),"app-store":("itunes.apple.com","apps.apple.com","mzstatic.com","ppq.apple.com","vpp.itunes.apple.com"),"apple-music":("music.apple.com",),"apple-tv":("tv.apple.com",),"apple-maps":("maps.apple.com","apple-mapkit.com"),"apple-push":("push.apple.com",),"apple-updates":("appldnld.apple.com","gdmf.apple.com","gg.apple.com","gs.apple.com","mesu.apple.com","static.ips.apple.com"),"apple-intelligence":("guzzoni.apple.com","smoot.apple.com","apple-relay.apple.com"),"apple-developer":("developer.apple.com",),"apple":("apple.com","apple-cloudkit.com","apple-dns.net","cdn-apple.com","aaplimg.com","apple.news")},"google":{"youtube":("youtube.com","youtu.be","googlevideo.com","ytimg.com","youtube-nocookie.com","youtubekids.com"),"google-play":("play.google.com","play.googleapis.com","android.clients.google.com","gvt1.com","gvt2.com"),"fcm":("fcm.googleapis.com","fcmregistrations.googleapis.com","firebaseinstallations.googleapis.com"),"gmail":("gmail.com","googlemail.com","gmailusercontent.com"),"drive":("drive.google.com","docs.google.com","sheets.google.com","slides.google.com","googledrive.com"),"google-maps":("maps.google.com","maps.googleapis.com","maps.gstatic.com"),"google-photos":("photos.google.com","photos.googleusercontent.com","ggpht.com"),"android":("android.com","androidify.com"),"google":("google.com","googleapis.com","gstatic.com","googleusercontent.com","recaptcha.net","g.co","appspot.com","withgoogle.com")}}
def fetch(url):
 req=urllib.request.Request(url,headers={"User-Agent":"Proxy-Config-Center/4.1 rule-updater"});
 with urllib.request.urlopen(req,timeout=25) as r:return r.read().decode("utf-8","replace")
def valid_candidate(v):
 v=v.strip().lower().rstrip(".")
 try: ipaddress.ip_network(v,strict=False); return True
 except ValueError: pass
 return bool(re.fullmatch(r"(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}",v))
def extract(text):
 d,c=set(),set()
 for line in text.splitlines():
  line=line.strip(); m=RULE_RE.match(line)
  if m:
   v=m.group(1).strip().lower()
   try:c.add(str(ipaddress.ip_network(v,strict=False)));continue
   except ValueError:pass
   if valid_candidate(v):d.add(v.rstrip("."));continue
  for h in HOST_RE.findall(line):
   h=h.lower().rstrip(".")
   if valid_candidate(h):d.add(h)
 return d,c
def extract_microsoft_json(text):
 try:data=json.loads(text)
 except json.JSONDecodeError:return set(),set()
 d,c=set(),set()
 for item in data if isinstance(data,list) else []:
  for v in item.get("urls",[]) or []:
   v=v.strip().lower().lstrip("*.")
   if valid_candidate(v):d.add(v)
  for v in item.get("ips",[]) or []:
   try:c.add(str(ipaddress.ip_network(v,strict=False)))
   except ValueError:pass
 return d,c
def extract_github_json(text):
 try:data=json.loads(text)
 except json.JSONDecodeError:return set(),set()
 d,c=set(),set(); domains=data.get("domains",{}) if isinstance(data,dict) else {}
 for vals in domains.values() if isinstance(domains,dict) else []:
  for v in vals or []:
   v=str(v).lower().lstrip("*.")
   if valid_candidate(v):d.add(v)
 for key,vals in data.items() if isinstance(data,dict) else []:
  if key=="domains" or not isinstance(vals,list):continue
  for v in vals:
   if isinstance(v,str):
    try:c.add(str(ipaddress.ip_network(v,strict=False)))
    except ValueError:pass
 return d,c
def load_state():return json.loads(STATE.read_text()) if STATE.exists() else {"owned":{},"misses":{},"updated_at":None}
def save_state(s):
 STATE.parent.mkdir(parents=True,exist_ok=True);s["updated_at"]=datetime.now(timezone.utc).isoformat();STATE.write_text(json.dumps(s,ensure_ascii=False,indent=2,sort_keys=True)+"\n")
def service_for(source,v):
 low=v.lower()
 for service,needles in CLASSIFIERS.get(source,{}).items():
  if any(low==n or low.endswith("."+n) for n in needles):return service
 return source
def add_values(doc,domains,cidrs):
 changed=False
 for r in doc.get("rules",[]):
  t=r.get("type")
  if t=="domain-suffix" and domains:
   old=set(map(str.lower,r.get("values",[])));new=sorted(old|domains)
   if new!=r.get("values",[]):r["values"]=new;changed=True
  elif t in ("ip-cidr","ip-cidr6") and cidrs:
   old=set(r.get("values",[]));wanted={x for x in cidrs if (":" in x)==(t=="ip-cidr6")};new=sorted(old|wanted)
   if new!=r.get("values",[]):r["values"]=new;changed=True
 if domains and not any(r.get("type")=="domain-suffix" for r in doc.get("rules",[])):
  doc.setdefault("rules",[]).append({"type":"domain-suffix","values":sorted(domains),"action":"group","target":doc.get("group")});changed=True
 return changed
def run(dry=False):
 cfg=yaml.safe_load(SOURCES.read_text());state=load_state();observed={};failures=[]
 for feed in cfg.get("feeds",[]):
  source,url=feed["source"],feed["url"]
  try:
   text=fetch(url)
   if source=="microsoft":d,c=extract_microsoft_json(text)
   elif source=="github":d,c=extract_github_json(text)
   else:d,c=extract(text)
   if not d and not c:raise RuntimeError("no valid candidates")
  except Exception as exc:failures.append(f"{source}: {exc}");continue
  for v in d|c:
   service=service_for(source,v);bucket=observed.setdefault(service,{"domains":set(),"cidrs":set()});(bucket["cidrs"] if "/" in v else bucket["domains"]).add(v)
 if not observed:raise SystemExit("all online sources failed; refusing changes")
 changed=set()
 for service,vals in observed.items():
  path=SERVICES/f"{service}.yaml"
  if not path.exists():continue
  doc=yaml.safe_load(path.read_text())
  if add_values(doc,vals["domains"],vals["cidrs"]):changed.add(path)
  owned=state.setdefault("owned",{}).setdefault(service,[]);state["owned"][service]=sorted(set(owned)|vals["domains"]|vals["cidrs"])
  for v in vals["domains"]|vals["cidrs"]:state.setdefault("misses",{}).pop(f"{service}:{v}",None)
  if not dry and path in changed:path.write_text(yaml.safe_dump(doc,sort_keys=False,allow_unicode=True))
 threshold=int(cfg.get("policy",{}).get("removals_require_consecutive_misses",3))
 for service,owned in list(state.get("owned",{}).items()):
  current=observed.get(service,{"domains":set(),"cidrs":set()});current_set=current["domains"]|current["cidrs"];path=SERVICES/f"{service}.yaml"
  if not path.exists():continue
  doc=yaml.safe_load(path.read_text())
  for v in list(owned):
   if v in current_set:continue
   key=f"{service}:{v}";misses=int(state.setdefault("misses",{}).get(key,0))+1;state["misses"][key]=misses
   if misses<threshold:continue
   removed=False
   for r in doc.get("rules",[]):
    vals=r.get("values",[])
    if v in vals:r["values"]=[x for x in vals if x!=v];removed=True
   if removed:changed.add(path)
   state["owned"][service]=[x for x in state["owned"][service] if x!=v]
  if not dry and path in changed:path.write_text(yaml.safe_dump(doc,sort_keys=False,allow_unicode=True))
 if not dry:save_state(state)
 print(json.dumps({"changed":sorted(str(p.relative_to(ROOT)) for p in changed),"source_failures":failures,"observed_services":len(observed)},ensure_ascii=False,indent=2))
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--dry-run",action="store_true");run(p.parse_args().dry_run)
