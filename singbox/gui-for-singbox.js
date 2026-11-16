/**
 * GUI.for.SingBox「混入与脚本」里的脚本，Windows 用。
 *
 * 每次生成内核配置时，从 Sub-Store 拉取用 windows.json 生成好的完整配置（含节点和策略组），
 * 替换掉 GUI 自己生成的配置。只保留 GUI 的两部分，让 GUI 界面里的功能照常可用：
 *   inbounds      TUN 和系统代理端口，GUI 首页的「系统代理」「TUN」开关改的就是它们
 *   experimental  面板接口（clash_api）和缓存，GUI 靠它显示策略组、切换节点
 *
 * 用法：
 * 1. 先按 substore.js 开头的说明，在 Sub-Store 里用 windows.json 建好文件，复制它的链接。
 * 2. 在 GUI 里新建一个配置，入站按需打开 TUN 或系统代理，其余不用设置，GUI 里也不用添加订阅。
 * 3. 右键这个配置，打开「混入与脚本」，把本文件整段粘贴到「脚本」里，再把下面的 SUBSTORE_URL 换成第 1 步的链接。
 * 4. 启动内核。每次启动都会从 Sub-Store 拉取一次配置。
 *
 * 启动时拉取失败：先关掉系统代理再启动。系统代理指向的内核还没启动时，GUI 的请求可能发不出去。
 */
const SUBSTORE_URL = '这里换成 Sub-Store 文件链接'

const onGenerate = async (config) => {
  const res = await Plugins.HttpGet(SUBSTORE_URL, {}, { Timeout: 30 })
  if (res.status && (res.status < 200 || res.status >= 300)) {
    throw new Error(`从 Sub-Store 拉取配置失败：HTTP ${res.status}`)
  }
  const remote = typeof res.body === 'string' ? JSON.parse(res.body) : res.body
  if (!remote || !Array.isArray(remote.outbounds)) {
    throw new Error('Sub-Store 返回的不是 sing-box 配置')
  }
  remote.inbounds = config.inbounds
  remote.experimental = config.experimental
  return remote
}
