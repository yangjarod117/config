import json
import os
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
    "Alibaba",
    "Tencent",
    "ByteDance",
    "China",
    "ChinaIPs",
    "Global",
]
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


def main():
    index = json.loads(get(INDEX))
    rules = {r["name"]: r for r in index["rules"]}
    os.makedirs(OUT, exist_ok=True)
    failed = []
    for name in NAMES:
        try:
            manifest = json.loads(get(rules[name]["manifest"]))
            artifact = next(a for a in manifest["artifacts"] if a["key"] == "rules")
            body = get(artifact["url"]).decode("utf-8")
            if "_set:" not in body:
                raise ValueError("empty rule file")
            with open(os.path.join(OUT, name + ".yaml"), "w", encoding="utf-8") as f:
                f.write(body)
            print(name, len(body.splitlines()))
        except Exception as e:
            failed.append(name)
            print(name, "failed:", e, file=sys.stderr)
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
