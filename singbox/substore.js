/**
 * Sub-Store「文件」脚本：把订阅节点填进 singbox/ 下的配置模板，输出 sing-box 官方客户端可以直接用的完整配置。
 *
 * 用法（详见 singbox/README.md）：
 *   文件来源填模板地址，例如 https://raw.githubusercontent.com/yangjarod117/config/main/singbox/phone.json
 *   脚本操作填本文件地址，后面带参数：
 *   https://raw.githubusercontent.com/yangjarod117/config/main/singbox/substore.js#name=订阅名称&type=subscription
 *
 * 参数：
 *   name  必填，Sub-Store 里单条订阅或组合订阅的名称
 *   type  可选，subscription（单条订阅，默认）或 collection（组合订阅）
 *
 * 填充规则和其他软件的配置一致：
 *   我的订阅  全部节点
 *   美国、日本  按节点名筛选
 * 某个地区一个节点都没有时，删掉这个组，并从其他策略组里去掉它，避免出现空策略组导致配置无法启动。
 */

const GROUPS = [
  { tag: '我的订阅', filter: null },
  { tag: '美国', filter: /(美国|🇺🇸|(^|[^a-z])us)/i },
  { tag: '日本', filter: /(日本|🇯🇵|(^|[^a-z])jp)/i },
]

const args = typeof $arguments === 'object' && $arguments ? $arguments : {}
const name = args.name
if (!name) {
  throw new Error('缺少参数 name：在脚本地址后面加上 #name=订阅名称')
}
const type = /^(collection|组合订阅)$/i.test(args.type || '') ? 'collection' : 'subscription'

const config = JSON.parse($content ?? $files[0])
if (!Array.isArray(config.outbounds)) {
  throw new Error('模板不是 sing-box 配置：没有 outbounds')
}

const nodes = await produceArtifact({ name, type, platform: 'sing-box', produceType: 'internal' })
if (!Array.isArray(nodes) || nodes.length === 0) {
  throw new Error(`「${name}」里没有可用节点`)
}

// 节点名和策略组同名时，在节点名后面加序号
const used = new Set(config.outbounds.map((o) => o.tag))
for (const node of nodes) {
  let tag = node.tag
  for (let i = 2; used.has(tag); i++) {
    tag = `${node.tag} ${i}`
  }
  node.tag = tag
  used.add(tag)
}

const empty = new Set()
for (const { tag, filter } of GROUPS) {
  const group = config.outbounds.find((o) => o.tag === tag)
  if (!group) {
    throw new Error(`模板里没有策略组「${tag}」`)
  }
  group.outbounds = nodes.filter((n) => !filter || filter.test(n.tag)).map((n) => n.tag)
  if (group.outbounds.length === 0) {
    empty.add(tag)
  }
}

if (empty.size > 0) {
  config.outbounds = config.outbounds.filter((o) => !empty.has(o.tag))
  for (const o of config.outbounds) {
    if (Array.isArray(o.outbounds)) {
      o.outbounds = o.outbounds.filter((t) => !empty.has(t))
    }
  }
}

config.outbounds.push(...nodes)
$content = JSON.stringify(config, null, 2)
