import fnmatch
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
    "Google",
    "Apple",
    "China",
    "ChinaIPs",
    "Global",
]
DEDUPE = {"Privacy": "AdvertisingLite"}
FOREIGN_DNS = ["YouTube", "Telegram", "AI", "Google", "Global"]
DOMAIN_TYPES = (
    "domain_set",
    "domain_suffix_set",
    "domain_keyword_set",
    "domain_wildcard_set",
    "domain_regex_set",
)
ORDER = [
    "Lan",
    "Hijacking",
    "AdvertisingLite",
    "Privacy",
    "iCloud",
    "YouTube",
    "Telegram",
    "AI",
    "Google",
    "Apple",
    "China",
    "Global",
    "ChinaIPs",
]
REJECT = ["Hijacking", "AdvertisingLite", "Privacy"]
# 走代理的规则集。其余规则集是直连或拒绝，Apple 默认直连。
PROXY_SETS = {"YouTube", "Telegram", "AI", "Google", "Global"}
# 直连规则集里被 ForeignDNS 覆盖的域名，收进 DirectDNS，改用国内 DNS。
DIRECT_DNS = ["Lan", "iCloud", "Apple", "China"]
KEEP = {
    "wxs.qq.com",
    "wxa.wxs.qq.com",
    "gvideo.qpic.cn",
    # 墨鱼模块单独放行它，拦了 12306 会出问题。
    "ad.12306.cn",
}
# openx 关键词会拦掉 openxlab.org.cn、openxla.org。换成 OpenX 自己的域名。
DROP_KEYWORD = {"openx"}
EXTRA_REJECT_SUFFIX = ["openx.com"]
# MagicRule 把同一批广告域名灌进了 Lan、Telegram、Apple。Lan 排最前且是直连，
# 这些域名会绕过去广告。只从 Lan 删掉同时出现在下面规则集里的域名。
LAN_SHARED_WITH = ("AdvertisingLite", "Telegram", "Apple")
LAN_PROTECTED = {
    "miwifi.com",
    "asusrouter.com",
    "routerlogin.com",
    "tplogin.cn",
    "localhost.weixin.qq.com",
    "local",
    "lan",
    "home",
    "internal",
    "home.arpa",
}
# 整段顶级域。去广告规则里的 data 会拦掉所有 .data 网站。
DROP_SUFFIX = {"data"}
# Google 规则集用整段国家后缀来覆盖 google.com.au 这类域名，但 google.com.au 已经单独列出。
# 裸的 co、au 会把无关网站送进 Google。只保留 Google 自己的品牌后缀。
GOOGLE_BRAND_TLD = {
    "android",
    "chrome",
    "dclk",
    "gbiz",
    "gle",
    "gmail",
    "goog",
    "google",
    "guge",
    "hangout",
    "nexus",
    "xn--flw351e",
    "xn--qcka1pmc",
}
# 这些域名会落到 Google 策略，不能放进 AI。
GEMINI_SKIP = {"apis.google.com"}
AI_SOURCES = [
    "OpenAI",
    "Anthropic",
    "Gemini",
    "GoogleDeepMind",
    "Grok",
    "Groq",
    "Perplexity",
    "Poe",
    "HuggingFace",
    "Cursor",
    "JetBrainsAI",
    "Windsurf",
    "ByteDanceAI",
]
AI_SKIP_KEYWORD = {"datadog", "sentry", "sift", "codex"}
# 厂商规则集里夹带的公共依赖。留在 AI 里会把支付、统计整站带跑。
AI_INFRA = {
    "stripe.com",
    "sentry.io",
    "segment.io",
    "intercom.io",
    "intercomcdn.com",
    "auth0.com",
    "launchdarkly.com",
    "algolia.net",
    "statsigapi.net",
    "statsig.com",
    "featuregates.org",
    "identrust.com",
    "arkoselabs.com",
    "livekit.cloud",
    "datadoghq.com",
}
# 国内厂商，含海外域名。留给中国规则或直连，不进 AI。
DOMESTIC_AI = {
    "deepseek.com",
    "deepseeksvc.com",
    "doubao.com",
    "doudou.com",
    "kimi.com",
    "kimi.ai",
    "moonshot.cn",
    "qwen.ai",
    "qwenlm.ai",
    "qianwen.com",
    "tongyi.com",
    "bigmodel.cn",
    "chatglm.cn",
    "zhipucn.com",
    "z.ai",
    "hailuoai.com",
    "minimaxi.com",
    "minimax.io",
    "xingyeai.com",
    "hunyuan.tencent.com",
    "yuanbao.tencent.com",
    "yuanqi.tencent.com",
    "coze.cn",
    "cozebaas.cn",
    "cozefn.cn",
    "cozeide.cn",
    "trae.cn",
    "trae.com.cn",
    "marscode.cn",
    "marscode.com.cn",
    "xiaoaiassist.com",
    "xiaomimimo.com",
    "miaibox.com",
    "iflytek.com",
}
AI_EXTRA_SUFFIX = [
    "bfl.ai",
    "cerebras.ai",
    "character.ai",
    "cohere.ai",
    "cohere.com",
    "copilot.com",
    "copilot.cloud.microsoft",
    "copilot.microsoft.com",
    "githubcopilot.com",
    "elevenlabs.com",
    "elevenlabs.io",
    "fireworks.ai",
    "heygen.com",
    "ideogram.ai",
    "inflection.ai",
    "leonardo.ai",
    "llama.com",
    "llamameta.net",
    "lumalabs.ai",
    "midjourney.com",
    "mistral.ai",
    "ollama.com",
    "openrouter.ai",
    "pi.ai",
    "pika.art",
    "replicate.com",
    "replicate.delivery",
    "runway.com",
    "runwayml.com",
    "stability.ai",
    "suno.ai",
    "suno.com",
    "together.ai",
    "together.xyz",
]
AI_EXTRA_DOMAIN = [
    "ai.meta.com",
    "ai.developer.meta.com",
    "aidemos.meta.com",
    "llama.developer.meta.com",
    "copilot-proxy.githubusercontent.com",
    "copilot-telemetry-service.githubusercontent.com",
    "copilot-workspace.githubnext.com",
]
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
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "egern", "rules")
SURGE_OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "surge", "rules")
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


def merge_rules(base, extra):
    # 用 plain 还原转义后再比较、再 json.dumps，否则 URL-REGEX 里的反斜杠会被转义两次。
    have = {(sec, plain(v)) for sec, v in entries(base)}
    add = {}
    for sec, v in entries(extra):
        item = plain(v)
        if (sec, item) in have:
            continue
        have.add((sec, item))
        add.setdefault(sec, []).append(item)
    if not add:
        return base if base.endswith("\n") else base + "\n"
    lines = base.splitlines()

    def section_index(sec):
        for i, line in enumerate(lines):
            if re.match(r"^" + re.escape(sec) + r":", line):
                return i
        return None

    present = []
    missing = []
    for sec, items in add.items():
        idx = section_index(sec)
        (present if idx is not None else missing).append((idx, sec, items))
    for idx, sec, items in sorted(present, reverse=True):
        end = idx + 1
        while end < len(lines) and re.match(r"^\s+- ", lines[end]):
            end += 1
        block = ["  - " + json.dumps(i, ensure_ascii=False) for i in items]
        lines[end:end] = block
    for _, sec, items in missing:
        lines.append(sec + ":")
        lines.extend("  - " + json.dumps(i, ensure_ascii=False) for i in items)
    return "\n".join(lines) + "\n"


def under(item, suffixes):
    return any(item == d or item.endswith("." + d) for d in suffixes)


def china_domains(body):
    exact = set()
    suffixes = set()
    for sec, v in entries(body):
        item = value(v)
        if sec == "domain_set":
            exact.add(item)
        elif sec == "domain_suffix_set":
            suffixes.add(item)
    return exact, suffixes


def covered_by(item, exact, suffixes):
    if item in exact or item in suffixes:
        return True
    parts = item.split(".")
    return any(".".join(parts[i:]) in suffixes for i in range(len(parts)))


class Matcher:
    """按 Egern 的方式匹配域名，用来判断一个域名最终落到哪个规则集。"""

    def __init__(self, body):
        self.exact = set()
        self.suffixes = set()
        self.keywords = []
        self.patterns = []
        for sec, v in entries(body):
            item = value(v).lower()
            if sec == "domain_set":
                self.exact.add(item)
            elif sec == "domain_suffix_set":
                self.suffixes.add(item)
            elif sec == "domain_keyword_set":
                self.keywords.append(item)
            elif sec == "domain_wildcard_set":
                self.patterns.append(re.compile(fnmatch.translate(item)).match)
            elif sec == "domain_regex_set":
                try:
                    self.patterns.append(re.compile(value(v), re.I).search)
                except re.error:
                    pass

    def covers_all(self, host):
        """host 和它的所有子域名都会命中。"""
        parts = host.split(".")
        if any(".".join(parts[i:]) in self.suffixes for i in range(len(parts))):
            return True
        return any(k in host for k in self.keywords)

    def match(self, host):
        if host in self.exact or self.covers_all(host):
            return True
        return any(p(host) for p in self.patterns)


def first_set(host, sec, names, matchers):
    """host 在 names 里第一个命中的规则集。后缀条目只认能覆盖全部子域名的命中。"""
    host = host.lower()
    for name in names:
        m = matchers[name]
        hit = m.covers_all(host) if sec == "domain_suffix_set" else m.match(host)
        if hit:
            return name
    return None


def filter_google(body):
    def drop(sec, v):
        item = value(v)
        return sec == "domain_suffix_set" and "." not in item and item not in GOOGLE_BRAND_TLD

    return rewrite(body, drop)


def make_ai(bodies):
    body = "no_resolve: true\n"
    for name in AI_SOURCES:
        body = merge_rules(body, bodies[name])
    extra = ["no_resolve: true", "domain_suffix_set:"]
    extra.extend("  - " + json.dumps(i, ensure_ascii=False) for i in AI_EXTRA_SUFFIX)
    extra.append("domain_set:")
    extra.extend("  - " + json.dumps(i, ensure_ascii=False) for i in AI_EXTRA_DOMAIN)
    body = merge_rules(body, "\n".join(extra) + "\n")
    exact, suffixes = china_domains(bodies["China"])

    def drop(sec, v):
        item = value(v)
        if sec == "domain_keyword_set" and item in AI_SKIP_KEYWORD:
            return True
        if item.endswith(".cn") or item.endswith(".com.cn"):
            return True
        if under(item, DOMESTIC_AI) or under(item, AI_INFRA) or item in GEMINI_SKIP:
            return True
        if sec in ("domain_set", "domain_suffix_set") and covered_by(item, exact, suffixes):
            return True
        return False

    body = rewrite(body, drop)
    print("AI", sum(1 for _ in entries(body)))
    return body


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


def strip_lan(bodies):
    shared = set()
    for name in LAN_SHARED_WITH:
        for sec, v in entries(bodies[name]):
            if sec in ("domain_set", "domain_suffix_set"):
                shared.add(value(v))
    removed = set()

    def drop(sec, v):
        item = value(v)
        if sec not in ("domain_set", "domain_suffix_set") or item not in shared:
            return False
        if item in LAN_PROTECTED:
            raise RuntimeError("lan filter would drop " + item)
        removed.add(item)
        return True

    bodies["Lan"] = rewrite(bodies["Lan"], drop)
    print("Lan pollution removed", len(removed))


def prune(body):
    lines = body.splitlines()
    out = []
    for i, line in enumerate(lines):
        if re.match(r"^[a-z0-9_]+_set:\s*$", line):
            nxt = lines[i + 1] if i + 1 < len(lines) else ""
            if not re.match(r"^\s+- ", nxt):
                continue
        out.append(line)
    return "\n".join(out) + "\n"


def build(bodies, module_body):
    # YouTube Music 和 YouTube 走同一个策略组，并进 YouTube，少一个规则集文件。
    bodies["YouTube"] = merge_rules(bodies["YouTube"], bodies.pop("YouTubeMusic"))
    before = sum(1 for _ in entries(bodies["AdvertisingLite"]))
    bodies["AdvertisingLite"] = merge_rules(bodies["AdvertisingLite"], module_body)
    print(
        "AdvertisingLite added from modules",
        sum(1 for _ in entries(bodies["AdvertisingLite"])) - before,
    )
    strip_lan(bodies)
    for name, base in DEDUPE.items():
        seen = {(sec, value(v)) for sec, v in entries(bodies[base])}
        bodies[name] = rewrite(
            bodies[name], lambda s, v, seen=seen: (s, value(v)) in seen
        )
    for name in REJECT:
        bodies[name] = rewrite(
            bodies[name],
            lambda s, v: s in ("domain_set", "domain_suffix_set") and value(v) in KEEP,
        )
        bodies[name] = rewrite(
            bodies[name],
            lambda s, v: s == "domain_suffix_set" and value(v) in DROP_SUFFIX,
        )
        bodies[name] = rewrite(
            bodies[name],
            lambda s, v: s == "domain_keyword_set" and value(v) in DROP_KEYWORD,
        )
    extra = ["domain_suffix_set:"]
    extra.extend("  - " + json.dumps(i) for i in EXTRA_REJECT_SUFFIX)
    bodies["AdvertisingLite"] = merge_rules(bodies["AdvertisingLite"], "\n".join(extra) + "\n")
    bodies["Google"] = filter_google(bodies["Google"])
    bodies["AI"] = make_ai(bodies)
    for name in AI_SOURCES:
        bodies.pop(name, None)
    exact = set()
    suffixes = set()

    def covered(s, v):
        item = value(v)
        if (s, item) in exact:
            return True
        if s not in ("domain_set", "domain_suffix_set"):
            return False
        parts = item.split(".")
        return any(".".join(parts[i:]) in suffixes for i in range(len(parts)))

    for name in ORDER:
        bodies[name] = rewrite(bodies[name], covered)
        for s, v in entries(bodies[name]):
            exact.add((s, value(v)))
            if s == "domain_suffix_set":
                suffixes.add(value(v))
    matchers = {name: Matcher(bodies[name]) for name in ORDER}

    # ForeignDNS：只收最终走代理的域名。被前面直连、拒绝规则集抢走的不收，
    # 例如 China 的 microsoft 关键词让一批 Global 里的微软域名走直连。
    merged = {t: [] for t in DOMAIN_TYPES}
    seen = set()
    dropped = 0
    for name in FOREIGN_DNS:
        before = ORDER[: ORDER.index(name)]
        for s, v in entries(bodies[name]):
            if s not in merged or (s, v) in seen:
                continue
            if s in ("domain_set", "domain_suffix_set"):
                hit = first_set(value(v), s, before, matchers)
                if hit and hit not in PROXY_SETS:
                    dropped += 1
                    continue
            seen.add((s, v))
            merged[s].append(v)
    print("ForeignDNS dropped (not proxied)", dropped)
    lines = []
    for t, items in merged.items():
        if items:
            lines.append(t + ":")
            lines.extend("  - " + v for v in items)
    bodies["ForeignDNS"] = "\n".join(lines) + "\n"

    # DirectDNS：直连规则集里会被 ForeignDNS 的父域名、整段后缀或关键词兜住的域名，
    # 例如 cn.download.nvidia.com、apple.de。DNS 转发里排在 ForeignDNS 前面，走国内 DNS。
    foreign = Matcher(bodies["ForeignDNS"])
    direct = {"domain_set": [], "domain_suffix_set": []}
    seen = set()
    for name in DIRECT_DNS:
        before = ORDER[: ORDER.index(name)]
        for s, v in entries(bodies[name]):
            if s not in direct or (s, value(v)) in seen:
                continue
            item = value(v)
            if not foreign.match(item.lower()):
                continue
            hit = first_set(item, s, before, matchers)
            if hit in PROXY_SETS or hit in REJECT:
                continue
            seen.add((s, item))
            direct[s].append(item)
    print("DirectDNS", sum(len(i) for i in direct.values()))
    lines = []
    for t, items in direct.items():
        if items:
            lines.append(t + ":")
            lines.extend("  - " + json.dumps(i, ensure_ascii=False) for i in items)
    bodies["DirectDNS"] = "\n".join(lines) + "\n"
    return bodies


def main():
    index = json.loads(get(INDEX))
    rules = {r["name"]: r for r in index["rules"]}
    os.makedirs(OUT, exist_ok=True)
    bodies = {}
    failed = []
    for name in NAMES + [n for n in AI_SOURCES if n not in NAMES]:
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
        module_body = module_reject()
    except Exception as e:
        failed.append("modules")
        print("modules failed:", e, file=sys.stderr)
    if failed:
        sys.exit(1)
    bodies = build(bodies, module_body)
    for stale_name in ("ModuleReject.yaml", "Gemini.yaml", "YouTubeMusic.yaml"):
        stale = os.path.join(OUT, stale_name)
        if os.path.exists(stale):
            os.remove(stale)
    for name, body in bodies.items():
        with open(os.path.join(OUT, name + ".yaml"), "w", encoding="utf-8", newline="\n") as f:
            f.write(prune(body))
        print(name, sum(1 for _ in entries(body)))
    write_surge(bodies)


# Egern 字段 → Surge 规则类型。Surge 没有 DOMAIN-REGEX，domain_regex_set 不输出。
SURGE_TYPES = {
    "domain_set": "DOMAIN",
    "domain_suffix_set": "DOMAIN-SUFFIX",
    "domain_keyword_set": "DOMAIN-KEYWORD",
    "domain_wildcard_set": "DOMAIN-WILDCARD",
    "ip_cidr_set": "IP-CIDR",
    "ip_cidr6_set": "IP-CIDR6",
    "asn_set": "IP-ASN",
    "url_regex_set": "URL-REGEX",
    "user_agent_set": "USER-AGENT",
}
# Surge 走代理的请求由节点远端解析，不需要按规则集分流 DNS。
SURGE_SKIP = {"ForeignDNS", "DirectDNS"}


def plain(v):
    """YAML 里的值还原成原文。双引号值要反转义，例如 URL-REGEX 里的 \\\\d → \\d。"""
    v = v.strip()
    if len(v) > 1 and v[0] == v[-1] == '"':
        return json.loads(v)
    if len(v) > 1 and v[0] == v[-1] == "'":
        return v[1:-1].replace("''", "'")
    return v


def write_surge(bodies):
    """把处理好的规则集转成 Surge 的 .list，和 Egern 用同一份数据。"""
    os.makedirs(SURGE_OUT, exist_ok=True)
    wanted = set()
    for name, body in bodies.items():
        if name in SURGE_SKIP:
            continue
        lines = []
        skipped = 0
        for sec, v in entries(body):
            kind = SURGE_TYPES.get(sec)
            if not kind:
                skipped += 1
                continue
            lines.append(kind + "," + plain(v))
        wanted.add(name + ".list")
        with open(os.path.join(SURGE_OUT, name + ".list"), "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(lines) + "\n")
        print("surge", name, len(lines), "skipped" if skipped else "", skipped or "")
    for stale in os.listdir(SURGE_OUT):
        if stale.endswith(".list") and stale not in wanted:
            os.remove(os.path.join(SURGE_OUT, stale))


if __name__ == "__main__":
    main()
