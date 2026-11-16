# sing-box

适用于 sing-box 1.14 及以上。三份配置模板的分流、DNS 和策略组相同，只有入站和面板不一样：

| 文件 | 客户端 | 区别 |
|---|---|---|
| `phone.json` | 官方 iOS、安卓客户端 | 只用 VPN 接管，不设系统代理 |
| `mac.json` | 官方 Mac 客户端 | 多一个本机代理端口 `127.0.0.1:7890`，和本机网页面板 `http://127.0.0.1:9090/ui` |
| `windows.json` | GUI.for.SingBox | 端口和 GUI 的默认值一致：代理 `20122`，面板 `20123` |

模板里的策略组是空的，要用 Sub-Store 把节点填进去，生成客户端能直接导入的在线配置。

## 用 Sub-Store 生成在线配置

每个平台在 Sub-Store 里建一个「文件」：

1. 来源选「远程」，链接填对应的模板：

```
https://raw.githubusercontent.com/yangjarod117/config/main/singbox/phone.json
https://raw.githubusercontent.com/yangjarod117/config/main/singbox/mac.json
https://raw.githubusercontent.com/yangjarod117/config/main/singbox/windows.json
```

2. 添加「脚本操作」，选链接，填下面的地址，把 `订阅名称` 换成 Sub-Store 里你的订阅名：

```
https://raw.githubusercontent.com/yangjarod117/config/main/singbox/substore.js#name=订阅名称
```

用的是组合订阅的话，在后面再加 `&type=collection`。

3. 保存后复制这个文件的链接。手机和 Mac 在官方客户端里新建配置，类型选「远程」，填这个链接。

脚本把全部节点放进「我的订阅」，再按节点名筛出「美国」「日本」，筛选规则和其他软件一样。哪个地区一个节点都没有，就删掉这个组。脚本是 `substore.js`。

## Windows：GUI.for.SingBox

GUI.for.SingBox 会自己生成配置，要用脚本把它换成 Sub-Store 里的这份：

1. 在 GUI 里新建一个配置，入站按需打开 TUN 或系统代理，其余不用设置。
2. 右键这个配置，打开「混入与脚本」，把 `gui-for-singbox.js` 的内容粘贴到「脚本」里，再把开头的 `SUBSTORE_URL` 换成 Windows 那个文件的链接。
3. 启动内核。

每次启动内核时，GUI 都会从 Sub-Store 拉取一次配置。入站和面板仍然用 GUI 自己的，首页的系统代理、TUN 开关和策略组面板照常可用。如果启动时拉取失败，先关掉系统代理再启动。

## 和其他软件的区别

sing-box 没有 MITM 和模块，去广告只靠规则集拒绝域名和 IP。墨鱼、fmz200 这类改写类去广告用不了，App 里的广告会比 Egern、Surge 多。规则集里的 URL 正则、User-Agent 和 IP-ASN 规则，sing-box 也不支持，生成时会跳过。

## 分流顺序

同 Egern。最前面多一条拒绝 853 端口，防止系统用加密 DNS 绕过分流。最后是 `.cn`、GEOIP CN 和 Global 兜底。

## DNS

1. 一键登录、银行、Apple 推送：阿里 DNS，返回真实 IP
2. 去广告规则集：直接拒绝
3. `DirectDNS.yaml` 和直连规则集：阿里 DNS
4. `ForeignDNS.yaml`：Fake IP，由节点远端解析
5. 其余：先通过代理问 Google DNS，结果是中国 IP 就用阿里 DNS 的真实 IP，否则用 Fake IP
