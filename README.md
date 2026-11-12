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

1. AdRules 去广告 → REJECT
2. 局域网、iCloud → DIRECT
3. YouTube、YouTube Music → YouTube
4. Telegram → Telegram
5. Apple → Apple（默认 DIRECT，可切代理）
6. 中国域名、中国 IP → DIRECT
7. 其余 → Global

## 去广告模块

- [fmz200/wool_scripts](https://github.com/fmz200/wool_scripts) 广告拦截&净化合集
- [fmz200/wool_scripts](https://github.com/fmz200/wool_scripts) HTTPDNS 拦截器

需要开启 MITM 并信任证书。
