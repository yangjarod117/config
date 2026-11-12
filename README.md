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
2. 去广告模块的拒绝规则、反劫持、去广告、隐私追踪 → REJECT
3. iCloud → DIRECT
4. YouTube、YouTube Music → YouTube
5. Telegram → Telegram
6. Apple → Apple（默认 DIRECT，可切代理）
7. 中国域名 → DIRECT
8. 已知境外域名 → Global
9. 中国 IP → DIRECT
10. 其余 → Global

## DNS

- 已知境外域名：Cloudflare、Google DoH 同时查询，取最快的结果
- 其余域名：系统 DNS、阿里 DoH、腾讯 DoH 同时查询，取最快的结果

## 规则处理

同步时去掉隐私规则里与去广告规则重复的条目，从拒绝规则中放行微信小程序、视频相关域名，并把 fmz200 两个模块里的拒绝规则提取成 `ModuleReject.yaml` 放在最前面。

## 去广告模块

- [fmz200/wool_scripts](https://github.com/fmz200/wool_scripts) 广告拦截&净化合集
- [fmz200/wool_scripts](https://github.com/fmz200/wool_scripts) HTTPDNS 拦截器

需要开启 MITM 并信任证书。
