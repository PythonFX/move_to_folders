# JAV Metadata Automation Framework 技术方案（Codex）

> 本文档为 Codex 开发使用的技术设计文档。

## 项目目标

开发一个本地自动化工具，用于批量整理本地 JAV 视频文件。

初版流程：

1.  扫描目录
2.  提取番号
3.  Playwright 打开真实 Chrome（独立 Profile）
4.  访问详情页
5.  Tampermonkey 解析页面
6.  下载封面（标题命名）
7.  保存到视频同目录
8.  进入下一部

## 核心设计原则

-   不直接 requests / BeautifulSoup 抓站
-   全部通过真实浏览器完成
-   Python 不解析 DOM
-   Tampermonkey 负责所有页面逻辑
-   Playwright 仅负责浏览器控制
-   三层彻底解耦
-   低频稳定优先，不追求极限速度
-   单任务失败不影响整体

## 架构

Python Scheduler → Playwright → Tampermonkey Userscript

### Python

负责：

-   扫描目录
-   正则提取番号
-   创建任务对象
-   浏览器调度
-   日志
-   Retry
-   等待下载结束
-   配置读取

不负责：

-   DOM
-   XPath
-   CSS
-   HTML
-   图片解析

### Playwright

负责：

-   launch_persistent_context()
-   独立 Chrome Profile
-   打开页面
-   等待加载
-   page.evaluate(...)
-   下载监听
-   Tab 生命周期

建议：

-   不使用 Selenium
-   不使用默认 Chrome Profile
-   使用 expect_download / download API
-   Headed 模式

### Tampermonkey

唯一负责页面逻辑。

负责：

-   获取标题
-   获取封面
-   下载图片
-   文件命名
-   DOM 解析

建议暴露：

-   window.isReady()
-   window.downloadCurrentMovie()
-   window.getMovieInfo()

Python 通过 page.evaluate() 调用，而不是模拟鼠标点击。

## 通信

Python ↓

page.evaluate()

↓

Tampermonkey JS

↓

GM_download()

避免：

-   OCR
-   鼠标坐标
-   图像识别

## 下载

监听浏览器下载完成。

不要 sleep。

## 文件命名

默认：

标题.jpg

统一替换非法字符。

## Retry

默认：

3 次。

失败写日志。

继续下一部。

## 配置

config.yaml：

-   movie_root
-   retry_count
-   timeout
-   download_delay
-   headless
-   close_tab_after_download

## 日志

记录：

-   SUCCESS
-   FAILED
-   TIMEOUT
-   NO COVER
-   NO TITLE

支持失败重跑。

## 二期扩展

保持 Python 不变，仅扩展 Userscript：

-   下载样图
-   下载演员头像
-   下载 NFO
-   获取演员
-   获取标签
-   打开其他站点
-   收藏
-   更多 Metadata

最终演化为 Metadata Automation Framework，而非单纯封面下载工具。
