# Quantumult X

iOS、Mac 通用。

## 使用

1. 在 Quantumult X 里从 URL 下载配置：

```
https://raw.githubusercontent.com/yangjarod117/config/main/qx/qx.conf
```

2. 在 `[server_remote]` 里添加 Sub-Store 的 QX 格式订阅，标签写 `我的订阅`。
3. 生成并信任 MITM 证书。

规则集、去广告重写和节点每天自动更新。「屏蔽iOS更新」在 Mac 上要关掉，升级系统前也要关掉。

## 分流顺序

同 Egern，最后是系统 LAN、GEOIP CN 和 Global 兜底。
