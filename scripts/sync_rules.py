import json
import os
import re
import sys
import time
import urllib.request

INDEX = "https://magicrule.pages.dev/data/index/Egern.json"
NAMES = [
    "AdvertisingLite",
    "Privacy",
    "Hijacking",
    "Lan",
    "iCloud",
    "YouTube",
    "YouTubeMusic",
    "Telegram",
    "Apple",
    "China",
    "ChinaIPs",
    "Global",
]
DEDUPE = {"Privacy": "AdvertisingLite"}
REJECT = ["Hijacking", "AdvertisingLite", "Privacy"]
KEEP = {
    "wxs.qq.com",
    "wxa.wxs.qq.com",
    "gvideo.qpic.cn",
}
MODULES = [
    "https://raw.githubusercontent.com/fmz200/wool_scripts/main/Surge/module/blockAds.module",
    "https://raw.githubusercontent.com/fmz200/wool_scripts/main/Surge/module/blockHTTPDNS.module",
]
MODULE_TYPES = {
    "DOMAIN": "domain_set",
    "DOMAIN-SUFFIX": "domain_suffix_set",
    "DOMAIN-KEYWORD": "domain_keyword_set",
    "IP-CIDR": "ip_cidr_set",
    "IP-CIDR6": "ip_cidr6_set",
    "URL-REGEX": "url_regex_set",
    "USER-AGENT": "user_agent_set",
}
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "rules")
HEADERS = {"User-Agent": "Mozilla/5.0", "Referer": "https://magicrule.pages.dev/"}


def get(url):
    last = None
    for _ in range(3):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read()
        except Exception as e:
            last = e
            time.sleep(5)
    raise last


def entries(body):
    section = None
    for line in body.splitlines():
        m = re.match(r"^([a-z0-9_]+):", line)
        if m:
            section = m.group(1)
            continue
        m = re.match(r"^\s+- (.+)$", line)
        if m and section:
            yield section, m.group(1).strip()


def value(item):
    return item.strip('"').strip("'")


def rewrite(body, drop):
    out = []
    section = None
    for line in body.splitlines():
        m = re.match(r"^([a-z0-9_]+):", line)
        if m:
            section = m.group(1)
            out.append(line)
            continue
        m = re.match(r"^\s+- (.+)$", line)
        if m and section and drop(section, m.group(1).strip()):
            continue
        out.append(line)
    return "\n".join(out) + "\n"


def module_reject():
    sets = {v: [] for v in MODULE_TYPES.values()}
    for url in MODULES:
        section = None
        for line in get(url).decode("utf-8").splitlines():
            line = line.strip()
            if line.startswith("["):
                section = line
                continue
            if section != "[Rule]" or not line or line.startswith("#"):
                continue
            parts = [p.strip() for p in line.split(",")]
            kind = MODULE_TYPES.get(parts[0])
            while len(parts) > 2 and parts[-1] in ("no-resolve", "extended-matching"):
                parts.pop()
            if not kind or len(parts) < 3 or not parts[-1].startswith("REJECT"):
                continue
            item = ",".join(parts[1:-1])
            if len(item) > 1 and item[0] == item[-1] == '"':
                item = item[1:-1]
            if item not in sets[kind]:
                sets[kind].append(item)
    if not sets["domain_suffix_set"]:
        raise ValueError("module rules not found")
    lines = ["no_resolve: true"]
    for kind, items in sets.items():
        if items:
            lines.append(kind + ":")
            lines.extend("  - " + json.dumps(i, ensure_ascii=False) for i in items)
    return "\n".join(lines) + "\n"


def main():
    index = json.loads(get(INDEX))
    rules = {r["name"]: r for r in index["rules"]}
    os.makedirs(OUT, exist_ok=True)
    bodies = {}
    failed = []
    for name in NAMES:
        try:
            manifest = json.loads(get(rules[name]["manifest"]))
            artifact = next(a for a in manifest["artifacts"] if a["key"] == "rules")
            body = get(artifact["url"]).decode("utf-8")
            if "_set:" not in body:
                raise ValueError("empty rule file")
            bodies[name] = body
        except Exception as e:
            failed.append(name)
            print(name, "failed:", e, file=sys.stderr)
    try:
        bodies["ModuleReject"] = module_reject()
    except Exception as e:
        failed.append("ModuleReject")
        print("ModuleReject failed:", e, file=sys.stderr)
    if failed:
        sys.exit(1)
    for name, base in DEDUPE.items():
        seen = set(entries(bodies[base]))
        bodies[name] = rewrite(bodies[name], lambda s, v: (s, v) in seen)
    for name in REJECT:
        bodies[name] = rewrite(
            bodies[name],
            lambda s, v: s in ("domain_set", "domain_suffix_set") and value(v) in KEEP,
        )
    for name, body in bodies.items():
        with open(os.path.join(OUT, name + ".yaml"), "w", encoding="utf-8") as f:
            f.write(body)
        print(name, sum(1 for _ in entries(body)))


if __name__ == "__main__":
    main()
