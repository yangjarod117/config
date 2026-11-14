# Egern

## 使用

1. 下载 `egern.yaml` 导入 Egern，作为本地配置使用。
2. 把「我的订阅」里的 `订阅链接` 换成自己的订阅地址。
3. 日常在 Egern 里「更新资源」即可；主配置有改动时再重新导入。

```
https://raw.githubusercontent.com/yangjarod117/config/main/egern/egern.yaml
```

## 分流顺序

1. 局域网 → DIRECT
2. 反劫持、去广告、隐私追踪 → REJECT
3. iCloud → DIRECT
4. YouTube → YouTube
5. Telegram → Telegram
6. 国外 AI → AI
7. Google → Google
8. Apple → Apple（默认 DIRECT）
9. 中国域名 → DIRECT
10. 境外域名 → Global
11. `.cn` 域名 → DIRECT（MagicRule 的中国规则集不含 `.cn`）
12. 中国 IP → DIRECT
13. 其余 → Global

## DNS

1. `DirectDNS.yaml`：国内 DNS
2. `ForeignDNS.yaml`：Cloudflare、Google DoH
3. 其余：系统 DNS、阿里 DoH、腾讯 DoH
