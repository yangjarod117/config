import os
import re
import sys
import time
import urllib.request

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
NAME = "去广告合集"
FMZ = "https://raw.githubusercontent.com/fmz200/wool_scripts/main/"
SURGE_ADS = FMZ + "Surge/module/blockAds.module"
SURGE_DNS = FMZ + "Surge/module/blockHTTPDNS.module"
LOON_ADS = FMZ + "Loon/plugin/blockAds.plugin"
LOON_DNS = FMZ + "Loon/plugin/Block_HTTPDNS.plugin"
QX_ADS = FMZ + "QuantumultX/rewrite/rewrite.snippet"
MOYU = "https://ddgksf2013.top/rewrite/StartUpAds.conf"
UA = {MOYU: "Quantumult%20X/1.5.5"}
DROP = re.compile(r"youtube|googlevideo|testflight|bilibili\\\.com\\/x\\/v2\\/account\\/(?:mine|myinfo)|due_date: ?9005270400000|vip_type = 2", re.I)
REJECT_LOCATION = {
    "reject": "http://reject/",
    "reject-200": "http://reject-200/",
    "reject-img": "http://reject-img/",
    "reject-dict": "http://reject-dict/",
    "reject-array": "http://reject-array/",
}
SURGE_REJECT = {
    "reject-200": 'data-type=text data=" " status-code=200',
    "reject-img": "data-type=tiny-gif status-code=200",
    "reject-dict": 'data-type=text data="{}" status-code=200 header="Content-Type:application/json"',
    "reject-array": 'data-type=text data="[]" status-code=200 header="Content-Type:application/json"',
}
LOON_REJECT = {
    "reject": "reject(404)",
    "reject-200": "reject(200)",
    "reject-img": "reject_img(200)",
    "reject-dict": "reject_dict(200)",
    "reject-array": "reject_array(200)",
}
QX_SCRIPT = {
    "script-response-body": ("response", True),
    "script-response-header": ("response", False),
    "script-request-body": ("request", True),
    "script-request-header": ("request", False),
    "script-echo-response": ("request", False),
    "script-analyze-echo-response": ("request", True),
}


def get(url):
    headers = {"User-Agent": UA.get(url, "Mozilla/5.0")}
    last = None
    for _ in range(3):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read().decode("utf-8")
        except Exception as e:
            last = e
            time.sleep(5)
    raise last


def sections(text):
    out = {}
    current = None
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith(("#", ";", "//")):
            continue
        m = re.fullmatch(r"\[([^\]]+)\]", s)
        if m:
            current = m.group(1).lower()
            out.setdefault(current, [])
            continue
        if current is not None:
            out[current].append(s)
    return out


def hosts_of(lines):
    out = []
    for s in lines:
        m = re.match(r"hostname\s*=\s*(.*)$", s, re.I)
        if m:
            out += [h.strip() for h in m.group(1).replace("%APPEND%", "").split(",") if h.strip()]
    return out


def unquote(v):
    v = v.strip()
    if len(v) > 1 and v[0] == v[-1] and v[0] in "\"'":
        return v[1:-1]
    return v


def tokens(text):
    return re.findall(r"'[^']*'|\"[^\"]*\"|\S+", text)


def split_params(text):
    out = []
    buf = ""
    quote = None
    for c in text:
        if quote:
            buf += c
            if c == quote:
                quote = None
        elif c in "\"'" and buf.rstrip().endswith("="):
            quote = c
            buf += c
        elif c == ",":
            out.append(buf.strip())
            buf = ""
        else:
            buf += c
    if buf.strip():
        out.append(buf.strip())
    return out


def map_local(rest):
    params = {}
    for part in re.split(r"\s(?=(?:data-type|data|status-code|header)=)", rest):
        k, _, v = part.partition("=")
        params[k.strip()] = unquote(v)
    kind = params.get("data-type", "file")
    data = params.get("data", "")
    status = int(params.get("status-code", "200"))
    header = params.get("header", "")
    if kind == "tiny-gif":
        return {"kind": "reject-img"}
    if kind == "text" and status == 200:
        if data == "{}" and "json" in header:
            return {"kind": "reject-dict"}
        if data == "[]" and "json" in header:
            return {"kind": "reject-array"}
        if data.strip() == "" and not header:
            return {"kind": "reject-200"}
    if kind == "text" and status == 404 and data == "" and not header:
        return {"kind": "reject"}
    headers = {}
    for pair in header.split("|"):
        k, sep, v = pair.partition(":")
        if sep:
            headers[k.strip()] = v.strip()
    return {"kind": "mock", "type": kind, "data": data, "status": status, "headers": headers}


def parse_surge(text):
    sec = sections(text)
    entries = []
    for s in sec.get("url rewrite", []):
        t = s.split()
        p = t[0]
        mode = t[2] if len(t) > 2 else "header"
        if mode == "reject":
            e = {"kind": "reject"}
        elif mode in ("302", "307"):
            e = {"kind": "redirect", "status": int(mode), "target": t[1]}
        elif mode == "header":
            e = {"kind": "header", "target": t[1]}
        else:
            raise ValueError("surge url rewrite: " + s)
        e.update(pattern=p, raw=("URL Rewrite", s))
        entries.append(e)
    for s in sec.get("header rewrite", []):
        t = [unquote(x) for x in tokens(s)]
        phase = "request"
        if t[0] in ("http-request", "http-response"):
            phase = t.pop(0)[5:]
        ops = {"header-add": "add", "header-del": "delete", "header-replace": "replace"}
        if t[1] not in ops:
            raise ValueError("surge header rewrite: " + s)
        e = {"kind": "header-rewrite", "phase": phase, "op": ops[t[1]], "name": t[2], "value": t[3] if len(t) > 3 else None}
        e.update(pattern=t[0], raw=("Header Rewrite", s))
        entries.append(e)
    for s in sec.get("body rewrite", []):
        head, p, rest = (s.split(None, 2) + ["", ""])[:3]
        if head in ("http-response-jq", "http-request-jq"):
            e = {"kind": "jq", "phase": head[5:-3], "filter": unquote(rest)}
        elif head in ("http-response", "http-request"):
            t = rest.split()
            if not t or len(t) % 2:
                raise ValueError("surge body rewrite: " + s)
            e = {"kind": "regex", "phase": head[5:], "pairs": list(zip(t[::2], t[1::2]))}
        else:
            raise ValueError("surge body rewrite: " + s)
        e.update(pattern=p, raw=("Body Rewrite", s))
        entries.append(e)
    for s in sec.get("map local", []):
        p, _, rest = s.partition(" ")
        e = map_local(rest)
        e.update(pattern=p, raw=("Map Local", s))
        entries.append(e)
    for s in sec.get("script", []):
        name, _, rest = s.partition("=")
        params = {}
        for part in split_params(rest):
            k, _, v = part.partition("=")
            params[k.strip()] = unquote(v)
        if params.get("type") not in ("http-request", "http-response"):
            raise ValueError("surge script: " + s)
        e = {
            "kind": "script",
            "phase": params["type"][5:],
            "name": name.strip(),
            "url": params["script-path"],
            "body": params.get("requires-body") == "true",
            "binary": params.get("binary-body-mode") == "true",
            "timeout": params.get("timeout"),
            "max_size": params.get("max-size"),
            "argument": params.get("argument"),
            "pattern": params["pattern"],
            "raw": ("Script", s),
        }
        entries.append(e)
    general = [s for s in sec.get("general", []) if not DROP.search(s)]
    return entries, hosts_of(sec.get("mitm", [])), general


def parse_qx(text):
    entries = []
    hosts = []
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith(("#", ";", "//")):
            continue
        if re.match(r"hostname\s*=", s, re.I):
            hosts += hosts_of([s])
            continue
        m = re.match(r"^(\S+)\s+(?:(\S+)\s+)?(url|url-and-header)\s+(\S+)(?:\s+(.*))?$", s)
        if not m:
            continue
        p, _, mode, kind, rest = m.groups()
        rest = rest or ""
        e = {"pattern": p, "raw": s, "qx": kind if mode == "url" else "url-and-header"}
        if mode != "url":
            e["kind"] = "native"
        elif kind in REJECT_LOCATION:
            e["kind"] = kind
        elif kind in ("302", "307"):
            e.update(kind="redirect", status=int(kind), target=rest)
        elif kind in ("response-body", "request-body"):
            find, sep, repl = rest.partition(" " + kind + " ")
            if not sep:
                raise ValueError("qx body: " + s)
            e.update(kind="regex", phase=kind.split("-")[0], pairs=[(find, repl)])
        elif kind in ("jsonjq-response-body", "jsonjq-request-body"):
            e.update(kind="jq", phase=kind.split("-")[1], filter=unquote(rest))
        elif kind in QX_SCRIPT:
            phase, body = QX_SCRIPT[kind]
            e.update(kind="script", phase=phase, url=rest.split()[0], body=body, binary=False,
                     timeout=None, max_size=None, argument=None, name=script_name(rest.split()[0]))
        else:
            e["kind"] = "native"
        e["terminal"] = mode == "url" and (kind in REJECT_LOCATION or kind in ("302", "307", "echo-response"))
        entries.append(e)
    return entries, hosts


def parse_loon(text):
    sec = sections(text)
    entries = []
    for name in ("rewrite", "script"):
        for s in sec.get(name, []):
            m = re.search(r"\$\{url\} ~= /((?:\\.|[^/\\])*)/[a-z]*", s)
            p = m.group(1) if m else s.split()[0]
            stop = bool(re.search(r"then (reject\w*\(|redirect\(|response\.body\.mock)", s)) or (
                not m and re.search(r"\s(reject[\w-]*|30[27])(\s|$)", s) is not None)
            entries.append({"pattern": p, "terminal": stop, "raw": (name, s)})
    args = [s for s in sec.get("argument", []) if not DROP.search(s)]
    return entries, hosts_of(sec.get("mitm", [])), args


def script_name(url):
    return os.path.splitext(url.rstrip("/").split("/")[-1])[0]


def terminal(e):
    if "terminal" in e:
        return e["terminal"]
    return e.get("kind") in REJECT_LOCATION or e.get("kind") in ("redirect", "mock")


def text_of(e):
    raw = e.get("raw")
    return raw if isinstance(raw, str) else raw[1]


def assemble(items):
    kept = []
    seen = set()
    for e, sec, out in items:
        flat = out if isinstance(out, str) else "\n".join(out)
        if DROP.search(text_of(e)) or DROP.search(e["pattern"]) or DROP.search(flat):
            continue
        if (sec, flat) in seen:
            continue
        seen.add((sec, flat))
        kept.append((e, sec, out))
    first = {}
    for i, (e, _, _) in enumerate(kept):
        if terminal(e):
            first.setdefault(e["pattern"], i)
    return [(sec, out) for i, (e, sec, out) in enumerate(kept) if first.get(e["pattern"], i) == i]


def merge_hosts(*lists):
    seen = set()
    out = []
    for h in [h for lst in lists for h in lst]:
        k = h.lower()
        if k in seen or DROP.search(h):
            continue
        seen.add(k)
        out.append(h)
    return out


def loon_regex(p):
    out = []
    i = 0
    while i < len(p):
        c = p[i]
        if c == "\\" and i + 1 < len(p):
            out.append(p[i:i + 2])
            i += 2
            continue
        out.append("\\/" if c == "/" else c)
        i += 1
    return "/" + "".join(out) + "/"


def loon_string(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"').replace("${", "\\${") + '"'


def to_surge(e):
    p = e["pattern"]
    k = e["kind"]
    if k == "reject":
        return "URL Rewrite", p + " - reject"
    if k in SURGE_REJECT:
        return "Map Local", p + " " + SURGE_REJECT[k]
    if k == "regex":
        parts = [x for pair in e["pairs"] for x in pair]
        if any(re.search(r"\s", x) or x == "" for x in parts):
            raise ValueError("surge body token: " + p)
        return "Body Rewrite", " ".join(["http-" + e["phase"], p] + parts)
    if k == "jq":
        if "'" in e["filter"]:
            raise ValueError("surge jq quote: " + p)
        return "Body Rewrite", "http-%s-jq %s '%s'" % (e["phase"], p, e["filter"])
    if k == "script":
        if '"' in p:
            raise ValueError("surge script pattern: " + p)
        pattern = '"%s"' % p if "," in p else p
        line = "%s = type=http-%s, pattern=%s, script-path=%s" % (e["name"], e["phase"], pattern, e["url"])
        if e["body"]:
            line += ", requires-body=true"
        return "Script", line
    raise ValueError("surge: " + text_of(e))


def to_loon(e):
    p = loon_regex(e["pattern"])
    k = e["kind"]
    if k in LOON_REJECT:
        return "rewrite", "request if ${url} ~= %s then %s" % (p, LOON_REJECT[k])
    if k == "regex":
        acts = ["%s.body.replace(%s, %s)" % (e["phase"], loon_regex(f), loon_string(r)) for f, r in e["pairs"]]
        return "rewrite", "%s if ${url} ~= %s then %s" % (e["phase"], p, " | ".join(acts))
    if k == "jq":
        return "rewrite", "%s if ${url} ~= %s then %s.json.jq(`%s`)" % (e["phase"], p, e["phase"], e["filter"].replace("`", "``"))
    if k == "script":
        line = '%s if ${url} ~= %s then script(%s)' % (e["phase"], p, loon_string(e["url"]))
        if e["body"]:
            line += " with requires_body=true"
        return "script", line
    raise ValueError("loon: " + text_of(e))


def to_qx(e):
    if e["kind"] in REJECT_LOCATION:
        return "%s url %s" % (e["pattern"], e["kind"])
    raise ValueError("qx: " + text_of(e))


def q(s):
    return "'" + str(s).replace("'", "''") + "'"


def to_egern(e):
    p = e["pattern"]
    k = e["kind"]
    if k in REJECT_LOCATION:
        return "url_rewrites", ["- match: " + q(p), "  location: " + q(REJECT_LOCATION[k])]
    if k == "redirect":
        return "url_rewrites", ["- match: " + q(p), "  location: " + q(e["target"]), "  status_code: %d" % e["status"]]
    if k == "header":
        return "url_rewrites", ["- match: " + q(p), "  location: " + q(e["target"])]
    if k == "mock":
        if e["type"] == "base64":
            return None
        body = get(e["data"]) if e["type"] == "file" else e["data"]
        lines = ["- match: " + q(p), "  status_code: %d" % e["status"]]
        if e["headers"]:
            lines.append("  headers:")
            lines += ["    %s: %s" % (hk, q(hv)) for hk, hv in e["headers"].items()]
        lines.append("  body: " + q(body.replace("\r", "").replace("\n", "")))
        return "map_locals", lines
    if k == "regex":
        out = []
        for f, r in e["pairs"]:
            out += ["- %s_regex:" % e["phase"], "    match: " + q(p), "    find: " + q(f), "    replace: " + q(r)]
        return "body_rewrites", out
    if k == "jq":
        return "body_rewrites", ["- %s_jq:" % e["phase"], "    match: " + q(p), "    filter: " + q(e["filter"])]
    if k == "header-rewrite":
        lines = ["- %s:" % e["op"], "    match: " + q(p), "    name: " + q(e["name"])]
        if e["value"] is not None:
            lines.append("    value: " + q(e["value"]))
        lines.append("    type: " + e["phase"])
        return "header_rewrites", lines
    if k == "script":
        lines = ["- http_%s:" % e["phase"], "    name: " + q(e["name"]), "    match: " + q(p), "    script_url: " + q(e["url"])]
        if e["body"]:
            lines.append("    body_required: true")
        if e["binary"]:
            lines.append("    binary_body: true")
        if e["timeout"]:
            lines.append("    timeout: %d" % int(e["timeout"]))
        if e["max_size"] and int(e["max_size"]) > 0:
            lines.append("    max_size: %d" % int(e["max_size"]))
        if e["argument"]:
            lines += ["    arguments:", "      _compat.$argument: " + q(e["argument"])]
        return "scriptings", lines
    raise ValueError("egern: " + text_of(e))


def write(path, text):
    with open(os.path.join(ROOT, path), "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def build_surge(groups, general, hosts):
    order = ["URL Rewrite", "Header Rewrite", "Body Rewrite", "Map Local", "Script"]
    out = {k: [] for k in order}
    items = []
    for e in groups:
        sec, line = e["raw"] if e["src"] == "surge" else to_surge(e)
        items.append((e, sec, line))
    for sec, line in assemble(items):
        out[sec].append(line)
    lines = ["#!name=" + NAME]
    if general:
        lines += ["[General]"] + general
    for k in order:
        if out[k]:
            lines += ["[%s]" % k] + out[k]
    lines += ["[MITM]", "hostname = %APPEND% " + ", ".join(hosts)]
    write("surge/adblock.sgmodule", "\n".join(lines) + "\n")


def build_egern(groups, hosts):
    order = ["url_rewrites", "header_rewrites", "body_rewrites", "map_locals", "scriptings"]
    out = {k: [] for k in order}
    items = []
    for e in groups:
        r = to_egern(e)
        if r:
            items.append((e, r[0], r[1]))
    for sec, block in assemble(items):
        out[sec] += ["  " + x for x in block]
    lines = ["name: " + q(NAME)]
    for k in order:
        if out[k]:
            lines += [k + ":"] + out[k]
    lines += ["mitm:", "  hostnames:", "    includes:"] + ["      - " + q(h) for h in hosts]
    write("egern/adblock.yaml", "\n".join(lines) + "\n")


def build_loon(groups, args, hosts):
    out = {"rewrite": [], "script": []}
    items = []
    for e in groups:
        sec, line = e["raw"] if e["src"] == "loon" else to_loon(e)
        items.append((e, sec, line))
    for sec, line in assemble(items):
        out[sec].append(line)
    lines = ["#!name=" + NAME]
    if args:
        lines += ["[Argument]"] + args
    lines += ["[Rewrite]"] + out["rewrite"] + ["[Script]"] + out["script"]
    lines += ["[MITM]", "hostname = " + ", ".join(hosts)]
    write("loon/adblock.lpx", "\n".join(lines) + "\n")


def build_qx(groups, hosts):
    items = []
    for e in groups:
        items.append((e, "", e["raw"] if e["src"] == "qx" else to_qx(e)))
    lines = [line for _, line in assemble(items)]
    lines.append("hostname = " + ", ".join(hosts))
    write("qx/adblock.snippet", "\n".join(lines) + "\n")


def tag(entries, src):
    entries[:] = [e for e in entries if not DROP.search(text_of(e)) and not DROP.search(e["pattern"])]
    for e in entries:
        e["src"] = src
    return entries


def main():
    text = {u: get(u) for u in (SURGE_ADS, SURGE_DNS, LOON_ADS, LOON_DNS, QX_ADS, MOYU)}
    if " url " not in text[MOYU] or "[Script]" not in text[SURGE_ADS] or "[Rewrite]" not in text[LOON_ADS]:
        raise ValueError("unexpected source")
    s_ads, s_ads_hosts, general = parse_surge(text[SURGE_ADS])
    s_dns, s_dns_hosts, _ = parse_surge(text[SURGE_DNS])
    l_ads, l_ads_hosts, args = parse_loon(text[LOON_ADS])
    l_dns, l_dns_hosts, _ = parse_loon(text[LOON_DNS])
    q_ads, q_ads_hosts = parse_qx(text[QX_ADS])
    moyu, moyu_hosts = parse_qx(text[MOYU])
    tag(s_ads, "surge")
    tag(s_dns, "surge")
    tag(l_ads, "loon")
    tag(l_dns, "loon")
    tag(q_ads, "qx")
    tag(moyu, "qx")
    surge_hosts = merge_hosts(s_dns_hosts, moyu_hosts, s_ads_hosts)
    build_surge(s_dns + moyu + s_ads, general, surge_hosts)
    build_egern(s_dns + moyu + s_ads, surge_hosts)
    build_loon(l_dns + moyu + l_ads, args, merge_hosts(l_dns_hosts, moyu_hosts, l_ads_hosts))
    q_dns = [dict(e, src="surge") for e in s_dns]
    build_qx(q_dns + moyu + q_ads, merge_hosts(s_dns_hosts, moyu_hosts, q_ads_hosts))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(e, file=sys.stderr)
        sys.exit(1)
