# config

自用 Egern 配置，不含节点。

## 导入

Egern → 配置 → 从 URL 导入：

```
https://raw.githubusercontent.com/yangjarod117/config/main/egern.yaml
```

## 节点

在 Egern 里添加的订阅和节点会进入「我的订阅」，「美国」「日本」按节点名自动筛选：

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

- 阿里、腾讯、字节的域名分别交给各自的 DNS
- 其他中国域名走国内 DoH 和运营商 DNS
- 已知境外域名走 Cloudflare、Google DoH
- 其余走国内 DNS

## 规则来源

`rules/` 里是 [MagicRule](https://magicrule.pages.dev) 生成的 Egern 原生规则，GitHub Actions 每天北京时间 4:30 同步一次。同步时去掉隐私规则里与去广告规则重复的条目，并从拒绝规则中放行微信头像、视频、小程序相关域名。

## 去广告模块

- [fmz200/wool_scripts](https://github.com/fmz200/wool_scripts) 广告拦截&净化合集
- [fmz200/wool_scripts](https://github.com/fmz200/wool_scripts) HTTPDNS 拦截器

需要开启 MITM 并信任证书。
