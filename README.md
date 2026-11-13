# config

自用 Egern 配置，不含节点。

## 使用

1. 下载 `egern.yaml` 导入 Egern，作为本地配置使用，不开自动更新。
2. 在 Egern 里添加订阅，订阅会进入「我的订阅」。
3. 日常在 Egern 里「更新资源」，一键更新模块、订阅和规则集。
4. 主配置有改动时，再按需重新下载导入。

下载地址：

```
https://raw.githubusercontent.com/yangjarod117/config/main/egern.yaml
```

`rules/` 里的规则集由 GitHub Actions 每天北京时间 4:30 从 [MagicRule](https://magicrule.pages.dev) 同步。

## 节点筛选

- 美国：`(?i)(美国|🇺🇸|(^|[^a-z])us)`
- 日本：`(?i)(日本|🇯🇵|(^|[^a-z])jp)`

## 分流顺序

1. 局域网 → DIRECT
2. 反劫持、去广告、隐私追踪 → REJECT
3. iCloud → DIRECT
4. YouTube、YouTube Music → YouTube
5. Telegram → Telegram
6. 国外 AI → AI
7. Google → Google
8. Apple → Apple（默认 DIRECT，可切代理）
9. 中国域名 → DIRECT
10. 已知境外域名 → Global
11. 中国 IP → DIRECT
12. 其余 → Global

去广告模块里的规则由 Egern 排在主配置规则前面，所以模块仍会先于上面的规则集生效。

## DNS

- `ForeignDNS.yaml` 里的域名：Cloudflare、Google DoH 同时查询，取最快的结果。该规则集由 YouTube、YouTube Music、Telegram、AI、Google、Global 每天自动合并生成，只保留域名类条目
- 其余域名：系统 DNS、阿里 DoH、腾讯 DoH 同时查询，取最快的结果

## 规则处理

同步时把 fmz200 两个模块里的拒绝规则并入 `AdvertisingLite.yaml`，去掉隐私规则里与去广告规则重复的条目，从拒绝规则中放行微信小程序、视频相关域名。MagicRule 的局域网规则集里混有一批广告域名，同步时从局域网里删掉。最后按分流顺序删掉被前面规则集覆盖、永远匹配不到的条目。

不使用 MagicRule 的整份 Google 规则集里的国家后缀：`co`、`au` 这种整段后缀会把正常网站送去代理。Google 策略只去掉这类裸后缀，`google.com.au` 这类完整域名仍走 Google。AI 策略放在 Google 前面，避免 Gemini 被 `google` 关键字抢走。AI 合并 OpenAI、Anthropic、Gemini、Grok、Mistral、Copilot、Meta、Midjourney 等国外厂商，去掉支付和统计用的公共域名。DeepSeek、豆包、Kimi、通义、智谱、混元这些国内服务不进 AI，继续直连。字节的海外产品 Cici、Coze 国际站和 trae.ai 算国外，走 AI。

## 去广告模块

配置里按这个顺序合并，写在上面的先生效：

1. [fmz200/wool_scripts](https://github.com/fmz200/wool_scripts) HTTPDNS 拦截器
2. [ddgksf2013](https://ddgksf2013.top/rewrite/StartUpAds.conf) 墨鱼去开屏 2.0。官方文件是 Quantumult X 格式，配置里用的是 [Romeo](https://github.com/ifflagged/Romeo) 转好的 Surge 模块
3. [fmz200/wool_scripts](https://github.com/fmz200/wool_scripts) 广告拦截&净化合集

需要开启 MITM 并信任证书。墨鱼模块和广告合集有一部分相同的解密域名，觉得 App 变慢可以单独关掉墨鱼模块。
