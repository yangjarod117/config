# Surge

iOS 5.22+、Mac 6.9+ 通用。

## 使用

1. 从 URL 下载托管配置，文件名保持 `surge.conf`，不要启用它：

```
https://raw.githubusercontent.com/yangjarod117/config/main/surge/surge.conf
```

2. 新建一个本地配置，先在里面生成并信任 MITM 证书。生成证书时 Surge 会重写整个文件，所以要先做这一步。
3. 用文本模式打开这个本地配置，保留 `[MITM]` 里 Surge 写入的 `ca-passphrase` 和 `ca-p12` 两行，其余内容换成下面的，把 `Sub-Store 订阅地址` 换成 Sub-Store 的 Surge 格式链接，然后启用：

```
[General]
#!include surge.conf

[Proxy Group]
我的订阅 = select, policy-path=Sub-Store 订阅地址, update-interval=86400, icon-url=https://raw.githubusercontent.com/Koolson/Qure/master/IconSet/Color/Airport.png
#!include surge.conf

[Rule]
#!include surge.conf

[MITM]
h2 = true
hostname = -*.googlevideo.com
ca-passphrase = 保留原值
ca-p12 = 保留原值
```

4. 安装模块：

```
https://raw.githubusercontent.com/fmz200/wool_scripts/main/Surge/module/blockHTTPDNS.module
https://raw.githubusercontent.com/ifflagged/Romeo/main/Modules/Surge/ddgksf2013/StartUpAds.sgmodule
https://raw.githubusercontent.com/fmz200/wool_scripts/main/Surge/module/blockAds.module
```

托管配置每天自动更新，本地配置和证书不用再动。本地配置以后只用文本模式改，不要在界面里改设置，界面保存同样会重写文件。

## 分流顺序

同 Egern，最后多一条系统 LAN 规则，再到 GEOIP CN 和 FINAL。
