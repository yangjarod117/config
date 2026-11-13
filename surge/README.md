# Surge

iOS 5.22+、Mac 6.9+ 通用。

## 使用

1. 从 URL 下载托管配置，文件名保持 `surge.conf`，不要启用它：

```
https://raw.githubusercontent.com/yangjarod117/config/main/surge/surge.conf
```

2. 新建一个本地配置并启用，内容如下，把 `Sub-Store 订阅地址` 换成 Sub-Store 的 Surge 格式链接：

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
```

3. 在本地配置里生成并信任 MITM 证书。
4. 安装模块：

```
https://raw.githubusercontent.com/fmz200/wool_scripts/main/Surge/module/blockHTTPDNS.module
https://raw.githubusercontent.com/ifflagged/Romeo/main/Modules/Surge/ddgksf2013/StartUpAds.sgmodule
https://raw.githubusercontent.com/fmz200/wool_scripts/main/Surge/module/blockAds.module
```

托管配置每天自动更新，本地配置和证书不用再动。

## 分流顺序

同 Egern，最后多一条系统 LAN 规则，再到 GEOIP CN 和 FINAL。
