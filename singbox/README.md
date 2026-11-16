# sing-box

适用于 sing-box 1.14 及以上。三份配置模板的分流、DNS 和策略组相同，只有入站和面板不一样：

| 文件 | 客户端 | 区别 |
|---|---|---|
| `phone.json` | 官方 iOS、安卓客户端 | 只用 VPN 接管，不设系统代理 |
| `mac.json` | 官方 Mac 客户端 | 多一个本机代理端口 `127.0.0.1:7890`，和本机网页面板 `http://127.0.0.1:9090/ui` |
| `windows.json` | GUI.for.SingBox | 端口和 GUI 的默认值一致：代理 `20122`，面板 `20123` |

模板里的策略组是空的，要用 Sub-Store 把节点填进去，生成客户端能直接导入的在线配置。

## 链接

Sub-Store 文件来源，按平台选一个：

```
https://raw.githubusercontent.com/yangjarod117/config/main/singbox/phone.json
```

```
https://raw.githubusercontent.com/yangjarod117/config/main/singbox/mac.json
```

```
https://raw.githubusercontent.com/yangjarod117/config/main/singbox/windows.json
```

Sub-Store 脚本操作，把 `订阅名称` 换成自己的订阅名，组合订阅在后面加 `&type=collection`：

```
https://raw.githubusercontent.com/yangjarod117/config/main/singbox/substore.js#name=订阅名称
```

GUI.for.SingBox 脚本，打开后整段复制：

```
https://raw.githubusercontent.com/yangjarod117/config/main/singbox/gui-for-singbox.js
```
