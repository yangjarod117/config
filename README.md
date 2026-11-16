# config

纯自用代理配置，不含节点。

| 目录 | 软件 |
|---|---|
| [egern](egern) | Egern |
| [surge](surge) | Surge |
| [loon](loon) | Loon |
| [qx](qx) | Quantumult X |
| [singbox](singbox) | sing-box |

各目录下的 `rules/` 由 GitHub Actions 每天北京时间凌晨 1:00 同步生成；去广告合集（`adblock.*`）每周一凌晨 2:00 生成。

## 来源与许可

- 规则集来自 [MagicRule](https://magicrule.pages.dev)
- 去广告规则另并入 [fmz200/wool_scripts](https://github.com/fmz200/wool_scripts) 的广告拦截&净化合集、HTTPDNS 拦截器（GPL-3.0），以及[可莉](https://github.com/luestr/ProxyResource)的广告平台拦截器
- sing-box 的 GEOIP 用 [SagerNet/sing-geoip](https://github.com/SagerNet/sing-geoip)，Mac 面板用 [zashboard](https://github.com/Zephyruso/zashboard)，配置写法参考[七尺宇](https://github.com/qichiyuhub/rule)
- 去广告合集由 fmz200 的广告拦截&净化合集、HTTPDNS 拦截器（GPL-3.0）和 [ddgksf2013](https://github.com/ddgksf2013)（墨鱼）的去开屏 2.0 合并生成，脚本仍引用原作者地址
- 屏蔽 iOS 更新来自 [TributePaulWalker](https://github.com/TributePaulWalker/Profiles)，版权归原作者
