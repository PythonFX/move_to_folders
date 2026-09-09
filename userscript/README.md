# Tampermonkey Userscript — JavBus Cover Downloader

Python 调度端（`jav_metadata/`）的页面层。Python 不做任何 DOM 解析，只通过
`page.evaluate()` 调用本脚本暴露的接口。

## 安装

使用日常 Chrome Profile（见 `jav_metadata/config.yaml` 的 `chrome_profile_dir`），
Tampermonkey 装在你平时的 Chrome 里即可，导入方式任选：

1. **最简单**：把 `javbus_cover_downloader.user.js` 拖进 Chrome 窗口，
   Tampermonkey 会自动弹出安装页，点"安装"
2. 或：Tampermonkey 图标 → 管理面板 → 实用工具 → 导入 → 选择本文件
3. 确认脚本已启用（`@match https://www.javbus.com/*`）

注意：程序启动浏览器前需要**完全退出日常 Chrome**（Cmd+Q），
否则同一 Profile 被占用会启动失败。

## 暴露给 Python 的接口

| 接口 | 返回 | 说明 |
|---|---|---|
| `window.isReady()` | `bool` | 页面加载完成且能取到标题 |
| `window.getMovieInfo()` | `{title, coverUrl, debug}` | `debug` 含命中元素的选择器/tag/位置 |
| `window.downloadCurrentMovie()` | — | 触发 `GM_download`，Python 监听浏览器下载事件落盘为 `标题.jpg` |

## 调试

在详情页 DevTools Console 执行：

```js
window.debugPageInfo()
```

会返回页面所有大图的 src/tag/位置、各级标题文本、以及当前命中的选择器。
**如果选择器没匹配对（标题/封面取错），把这段输出发给我来调整 `SELECTORS` 配置。**

选择器在脚本顶部 `SELECTORS` 常量里，按优先级排列，改起来很方便。
