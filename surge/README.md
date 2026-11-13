# Surge

iOS、Mac 通用。

## 使用

1. 在 Surge 里从 URL 下载配置：

```
https://raw.githubusercontent.com/yangjarod117/config/main/surge/surge.conf
```

2. 用文本模式把「我的订阅」里的 `订阅链接` 换成 Sub-Store 的 Surge 格式链接。
3. 生成并信任 MITM 证书。
4. 安装模块：

```
https://raw.githubusercontent.com/fmz200/wool_scripts/main/Surge/module/blockHTTPDNS.module
https://raw.githubusercontent.com/ifflagged/Romeo/main/Modules/Surge/ddgksf2013/StartUpAds.sgmodule
https://raw.githubusercontent.com/fmz200/wool_scripts/main/Surge/module/blockAds.module
```

规则集和节点每天自动更新。配置本身有改动时再重新下载，把旧配置里 `[MITM]` 的 `ca-passphrase`、`ca-p12` 两行和订阅链接贴回去，证书就不用重新生成。

## 分流顺序

同 Egern，最后多一条系统 LAN 规则，再到 GEOIP CN 和 FINAL。
