# Loon
iOS、Mac 通用。
## 使用
1. 在 Loon 里从 URL 下载配置：
```
https://raw.githubusercontent.com/yangjarod117/config/main/loon/loon.conf
```
2. 在「节点订阅」里添加 Sub-Store 的 Loon 格式订阅，名称随意。「美国」「日本」按节点名筛选，「我的订阅」是全部节点。
3. 生成并信任 MITM 证书。

规则集、插件和节点按 Loon 的资源自动更新间隔更新。广告拦截&净化合集（fmz200）只支持 iOS，Mac 上不生效。「屏蔽iOS更新」插件只用于 iOS/iPadOS，升级系统前先关掉。
## 分流顺序
同 Egern，第一条是拒绝 QUIC，最后是 `.cn`、GEOIP CN 和 Global 兜底。

插件里的规则优先于这些规则集。可莉的广告平台拦截器已经并入去广告规则集（去掉了放行名单里的域名），不要再装它的插件，否则放行名单失效。
