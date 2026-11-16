/**
 * GUI.for.SingBox「混入与脚本」里的脚本，Windows 用。
 *
 * 每次生成内核配置时，从 Sub-Store 拉取用 windows.json 生成好的完整配置（含节点和策略组），
 * 替换掉 GUI 自己生成的配置。只保留 GUI 的两部分，让 GUI 界面里的功能照常可用：
 *   inbounds      TUN 和系统代理端口，GUI 首页的「系统代理」「TUN」开关改的就是它们
 *   experimental  面板接口（clash_api）和缓存，GUI 靠它显示策略组、切换节点
 *
 * 用法：把下面的 SUBSTORE_URL 换成 Sub-Store 里 Windows 那个文件的链接，整段粘贴到配置的「脚本」里。
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
