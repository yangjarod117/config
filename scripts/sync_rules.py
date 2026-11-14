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
# 放行名单。三类规则在合并完所有来源之后统一生效：拒绝规则里只要有条目会拦到它们，就自动删掉，
# 不报错；删掉了什么打印在 Actions 日志里。Surge 的拒绝规则集开了 pre-matching，直连规则压不过它，
# 所以误拦只能在这里修。
#
# PROTECT：必须能访问的具体主机。会拦到这个主机的条目（同名、父域名后缀、关键词、通配）都删掉；
# 只针对它下面其他子域名的条目不动，例如 dns.weixin.qq.com 这类 HTTPDNS 照常拦。
PROTECT = {
    # 微信、QQ：消息、公众号、小程序、图片、视频号、登录
    "weixin.qq.com", "wx.qq.com", "long.weixin.qq.com", "short.weixin.qq.com",
    "szlong.weixin.qq.com", "szshort.weixin.qq.com", "szextshort.weixin.qq.com",
    "extshort.weixin.qq.com", "mp.weixin.qq.com", "open.weixin.qq.com", "api.weixin.qq.com",
    "res.wx.qq.com", "servicewechat.com", "mmbiz.qpic.cn", "mmbiz.qlogo.cn", "wx.qlogo.cn",
    "thirdwx.qlogo.cn", "wxapp.tc.qq.com", "wxs.qq.com", "wxa.wxs.qq.com", "gvideo.qpic.cn",
    "ssl.ptlogin2.qq.com", "xui.ptlogin2.qq.com", "graph.qq.com",
    # 支付
    "pay.weixin.qq.com", "wx.tenpay.com", "mobilegw.alipay.com", "openapi.alipay.com",
    "render.alipay.com", "gw.alipayobjects.com", "cashier.95516.com", "base.95516.com",
    "wallet.95516.com",
    # 验证码
    "captcha.qq.com", "ssl.captcha.qq.com", "t.captcha.qq.com", "turing.captcha.qcloud.com",
    "static.geetest.com", "api.geetest.com", "gcaptcha4.geetest.com", "c.dun.163.com",
    "cf.aliyun.com", "sec.taobao.com",
    # 短信验证码、本机号码一键登录（MobTech、极光、移动、电信、联通）
    "init.sms.mob.com", "sdkapi.sms.mob.com", "code.sms.mob.com",
    "smartop-sdkapi.jiguang.cn", "sdk.verification.jiguang.cn",
    "verify5.cmpassport.com", "onekey.cmpassport.com", "www.cmpassport.com",
    "id6.me", "e.189.cn", "opencloud.wostore.cn", "enrichgw.10010.com",
    "auth.wosms.cn", "msv6.wosms.cn",
    # Apple：证书校验、账号、App Store、推送、iCloud
    "ocsp.apple.com", "ocsp2.apple.com", "valid.apple.com", "crl.apple.com", "gs.apple.com",
    "gsa.apple.com", "appleid.apple.com", "idmsa.apple.com", "init.itunes.apple.com",
    "buy.itunes.apple.com", "api.push.apple.com", "setup.icloud.com", "www.icloud.com",
    # 云盘
    "pan.baidu.com", "pcs.baidu.com", "d.pcs.baidu.com", "c.pcs.baidu.com",
    "drive.quark.cn", "drive-pc.quark.cn", "pan.quark.cn", "api.aliyundrive.com",
    "api.alipan.com", "user.alipan.com", "www.123pan.com", "cloud.189.cn", "api.cloud.189.cn",
    # 地图、定位
    "apilocate.amap.com", "restapi.amap.com", "m5.amap.com", "lbs.qq.com", "apis.map.qq.com",
    "api.map.baidu.com", "loc.map.baidu.com",
    # 电商主接口和图片
    "acs.m.taobao.com", "guide-acs.m.taobao.com", "img.alicdn.com", "gw.alicdn.com",
    "g.alicdn.com", "heic.alicdn.com", "api.m.jd.com", "m.360buyimg.com", "img11.360buyimg.com",
    "wmapi.meituan.com", "p0.meituan.net", "mpay.meituan.com", "mobile.yangkeduo.com",
    "api.pinduoduo.com",
    # 字节、Telegram、12306
    "aweme.snssdk.com", "api.amemv.com", "api.telegram.org",
    "kyfw.12306.cn", "mobile.12306.cn",
    # 墨鱼模块单独放行它，拦了 12306 会出问题
    "ad.12306.cn",
    # 广告平台拦截器里夹带的非广告域名：夸克/UC 搜索、淘宝登录令牌
    "api.sm.cn", "c.sm.cn", "atoken.m.taobao.com",
}
# ALLOW_DOMAINS：整个域名都放行，包括子域名。设备风控（网易易盾、数美、阿里设备指纹、同盾、顶象、
# 极验），拦了会频繁弹滑块或提示环境异常。
ALLOW_DOMAINS = {
    "dun.163.com", "dun.163yun.com", "fengkongcloud.com", "fengkongcloud.cn", "ishumei.com",
    "ynuf.aliapp.org", "umid.alipay.com", "tongdun.net", "dingxiang-inc.com", "geetest.com",
}
# PUSH_DOMAINS：推送服务（极光、个推），拦了用它们的 App 收不到通知。整域放行，
# 但子域名里带统计、日志、广告字样的照常拦。
PUSH_DOMAINS = {"jpush.cn", "jpush.io", "getui.com", "getui.net", "igexin.com", "gepush.com"}
PUSH_KEEP_BLOCKED = re.compile(
    r"(^|[.-])(stats?|logs?|ads?|adv|track\w*|analytics?|report|apm|collect\w*|lbs|loc|phone)(?=$|[.\-\d])", re.I
)
# 字节系 App 启动先请求的 TTNet 网络配置，主机名以 tnc 开头。
TNC_SUFFIXES = (
    "capcutapi.com",
    "zijieapi.com",
    "isnssdk.com",
    "toutiaoapi.com",
    "bytedance.com",
    "snssdk.com",
    "sgsnssdk.com",
)
# 用户规定：fmz200 广告合集自己拦截的地址，一律不放行，以它为准。下面三个集合在解析它的规则时填充。
FMZ_ADS = "https://raw.githubusercontent.com/fmz200/wool_scripts/main/Surge/module/blockAds.module"
FMZ_EXACT = set()
FMZ_SUFFIX = set()
FMZ_KEYWORD = []
# 只收集直连规则、不合并拒绝规则的模块（拒绝规则由模块自己在设备上生效）。
DIRECT_ONLY_MODULES = [
    "https://raw.githubusercontent.com/ifflagged/Romeo/main/Modules/Surge/ddgksf2013/StartUpAds.sgmodule",
]
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
    # 可莉「广告平台拦截器」，只取拒绝规则：倍孜、AdScope、TopOn、广点通等第三方广告 SDK 平台。
    "https://raw.githubusercontent.com/ifflagged/Romeo/main/Modules/Surge/Kelee/BlockAdvertisers.sgmodule",
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


def push_ok_to_block(host):
    """推送域名下的统计、日志、广告子域名，照常拦。"""
    for d in PUSH_DOMAINS:
        if under(host, [d]) and host != d:
            return bool(PUSH_KEEP_BLOCKED.search(host[: -len(d) - 1]))
    return False


def fmz_blocks(host):
    """fmz200 广告合集自己会不会拦这个主机。"""
    parts = host.split(".")
    if host in FMZ_EXACT:
        return True
    if any(".".join(parts[i:]) in FMZ_SUFFIX for i in range(len(parts))):
        return True
    return any(k in host for k in FMZ_KEYWORD)


def protected(host):
    """这个主机必须能访问。fmz200 广告合集也拦的，不算。"""
    host = host.lower()
    if fmz_blocks(host):
        return False
    if host in PROTECT:
        return True
    if host.split(".")[0].startswith("tnc") and under(host, TNC_SUFFIXES):
        return True
    if under(host, ALLOW_DOMAINS):
        return True
    return under(host, PUSH_DOMAINS) and not push_ok_to_block(host)


def wildcard_hits(pattern, hosts):
    rx = re.compile(fnmatch.translate(pattern.lower()))
    return any(rx.match(h) for h in hosts)


def blocks_allowed(sec, item):
    """这条拒绝规则会不会拦到放行名单。"""
    item = item.lower()
    whole = ALLOW_DOMAINS | PUSH_DOMAINS
    if sec == "domain_set":
        return protected(item)
    guarded = [h for h in PROTECT | whole if protected(h)]
    if sec == "domain_suffix_set":
        # 条目本身受保护，或者它是某个受保护主机/域名的父域名
        return protected(item) or any(under(h, [item]) for h in guarded)
    if sec == "domain_keyword_set":
        if any(item in h for h in guarded):
            return True
        # 关键词本身像一个推送/风控域名下的主机名，例如 c-hzgt2.getui.com
        return any(d in item for d in whole) and protected(item.strip("."))
    if sec == "domain_wildcard_set":
        samples = PROTECT | whole | {"x." + d for d in whole}
        return wildcard_hits(item, [h for h in samples if protected(h)])
    return False


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


def collect_module_direct(line):
    """模块里的直连规则并入放行名单，让 Surge 的 pre-matching 也遵守模块作者的放行。"""
    parts = [p.strip() for p in line.split(",")]
    while len(parts) > 2 and parts[-1] in ("no-resolve", "extended-matching"):
        parts.pop()
    if len(parts) != 3 or parts[2] != "DIRECT":
        return
    host = parts[1].strip('"').lower()
    if parts[0] == "DOMAIN":
        PROTECT.add(host)
    elif parts[0] == "DOMAIN-SUFFIX":
        ALLOW_DOMAINS.add(host)


def module_direct_only():
    for url in DIRECT_ONLY_MODULES:
        section = None
        for line in get(url).decode("utf-8").splitlines():
            line = line.strip()
            if line.startswith("["):
                section = line
                continue
            if section == "[Rule]" and line and not line.startswith("#"):
                collect_module_direct(line)


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
            collect_module_direct(line)
            parts = [p.strip() for p in line.split(",")]
            kind = MODULE_TYPES.get(parts[0])
            while len(parts) > 2 and parts[-1] in ("no-resolve", "extended-matching"):
                parts.pop()
            if not kind or len(parts) < 3 or not parts[-1].startswith("REJECT"):
                continue
            item = ",".join(parts[1:-1])
            if len(item) > 1 and item[0] == item[-1] == '"':
                item = item[1:-1]
            if url == FMZ_ADS:
                {"domain_set": FMZ_EXACT, "domain_suffix_set": FMZ_SUFFIX}.get(kind, set()).add(
                    item.lower()
                )
                if kind == "domain_keyword_set":
                    FMZ_KEYWORD.append(item.lower())
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
            lambda s, v: s == "domain_suffix_set" and value(v) in DROP_SUFFIX,
        )
        bodies[name] = rewrite(
            bodies[name],
            lambda s, v: s == "domain_keyword_set" and value(v) in DROP_KEYWORD,
        )
        dropped = []

        def drop_allowed(s, v, dropped=dropped):
            if blocks_allowed(s, plain(v)):
                dropped.append(plain(v))
                return True
            return False

        bodies[name] = rewrite(bodies[name], drop_allowed)
        if dropped:
            print(name, "allow-list dropped", dropped)
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
        module_direct_only()
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
