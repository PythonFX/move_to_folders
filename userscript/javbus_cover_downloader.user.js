// ==UserScript==
// @name         JavBus Cover Downloader (Python Scheduler Bridge)
// @namespace    jav-metadata-automation
// @version      0.2.0
// @description  JAV Metadata Automation 页面层：向 Python Playwright 调度端暴露 window.isReady / getMovieInfo / downloadCurrentMovie / getSearchResults / getMagnetList
// @match        https://www.javbus.com/*
// @grant        none
// @run-at       document-idle
// ==/UserScript==

(function () {
    'use strict';

    /**
     * 选择器配置 —— 按候选优先级排列，第一个命中的生效。
     * 页面结构如有变动，只需改这里（或告诉我实际情况）。
     */
    const SELECTORS = {
        // 标题：JavBus 详情页的主标题
        title: [
            'h3',
            'title',
        ],
        // 封面大图：a.bigImage 的 href 指向原图，内部 img 是缩略
        cover: [
            'a.bigImage',
            'a.bigImage img',
            '.movie .bigImage img',
            'img[src*="pics.dmm.co.jp"][src*="pl.jpg"]',
        ],
    };

    function firstMatch(selectorList) {
        for (const selector of selectorList) {
            const el = document.querySelector(selector);
            if (el) return { el, selector };
        }
        return { el: null, selector: null };
    }

    function getTitleElement() {
        return firstMatch(SELECTORS.title);
    }

    function getCoverElement() {
        return firstMatch(SELECTORS.cover);
    }

    function extractTitle() {
        const { el } = getTitleElement();
        if (!el) return '';
        // <title> 标签带站点后缀，去掉 " - JavBus" 之类
        return el.textContent.replace(/\s*-\s*JavBus.*$/i, '').trim();
    }

    function extractCoverUrl() {
        const { el } = getCoverElement();
        if (!el) return '';
        // <a> 标签取 href（原图），<img> 取 src
        const url = (el.tagName === 'A' ? el.href : el.src) || '';
        // JavBus 部分资源是相对协议 //xxx，补全 https:
        if (url.startsWith('//')) return 'https:' + url;
        return url;
    }

    function describeElement(el, selector) {
        if (!el) return { selector, found: false };
        const rect = el.getBoundingClientRect();
        return {
            selector,
            found: true,
            tag: el.tagName.toLowerCase(),
            text: (el.textContent || '').trim().slice(0, 120),
            src: el.src || el.href || '',
            position: { x: Math.round(rect.x), y: Math.round(rect.y), width: Math.round(rect.width), height: Math.round(rect.height) },
        };
    }

    function sanitizeFilename(name) {
        return name.replace(/[\\/:*?"<>|\r\n\t]/g, '_').replace(/^[\s.]+|[\s.]+$/g, '');
    }

    // ===== 暴露给 Python (page.evaluate) 的契约接口 =====

    window.isReady = function () {
        return document.readyState !== 'loading' && !!extractTitle();
    };

    window.getMovieInfo = function () {
        const title = extractTitle();
        const coverUrl = extractCoverUrl();
        return {
            title,
            coverUrl,
            // 调试信息：命中元素的选择器 / tag / 位置，页面结构不符时把这些发给我
            debug: {
                url: location.href,
                titleElement: describeElement(getTitleElement().el, getTitleElement().selector),
                coverElement: describeElement(getCoverElement().el, getCoverElement().selector),
            },
        };
    };

    window.downloadCurrentMovie = function () {
        const title = extractTitle();
        const coverUrl = extractCoverUrl();
        if (!coverUrl) throw new Error('no cover url found');
        // @grant none（页面主世界运行），用 <a download> 触发浏览器原生下载，
        // Python 侧 page.expect_download() 捕获后 save_as 落盘为最终文件名
        const a = document.createElement('a');
        a.href = coverUrl;
        a.download = sanitizeFilename(title || 'cover') + '.jpg';
        document.body.appendChild(a);
        a.click();
        a.remove();
    };

    // 搜索结果页：提取当前页全部条目 [{number, url}]
    window.getSearchResults = function () {
        return Array.from(document.querySelectorAll('a.movie-box'))
            .map(a => {
                const m = (a.href || '').match(/javbus\.com\/([A-Za-z0-9-]+)\/?(\?.*)?$/);
                return m ? { number: m[1].toUpperCase(), url: a.href } : null;
            })
            .filter(Boolean);
    };

    // 详情页：提取"磁力連結投稿"表格 [{name, magnet, size, date}]
    window.getMagnetList = function () {
        const table = document.querySelector('table#magnet-table')
            || Array.from(document.querySelectorAll('table')).find(t => t.querySelector('a[href^="magnet:"]'));
        if (!table) return [];
        const rows = [];
        for (const tr of table.querySelectorAll('tr')) {
            const link = tr.querySelector('a[href^="magnet:"]');
            if (!link) continue;
            const tds = tr.querySelectorAll('td');
            rows.push({
                name: (tds[0] ? tds[0].textContent : link.textContent).replace(/\s+/g, ' ').trim(),
                magnet: link.href,
                size: tds[1] ? tds[1].textContent.trim() : '',
                date: tds[2] ? tds[2].textContent.trim() : '',
            });
        }
        return rows;
    };

    // 手动调试用：在 DevTools Console 执行 window.debugPageInfo() 查看页面结构
    window.debugPageInfo = function () {
        const images = Array.from(document.querySelectorAll('img'))
            .filter(img => img.naturalWidth >= 300 || img.width >= 300)
            .slice(0, 10)
            .map(img => describeElement(img, 'img (auto-scan)'));
        const headings = Array.from(document.querySelectorAll('h1, h2, h3, h4, title'))
            .slice(0, 10)
            .map(h => describeElement(h, h.tagName.toLowerCase() + ' (auto-scan)'));
        const info = { url: location.href, headings, images, movieInfo: window.getMovieInfo() };
        console.log('[jav-metadata] debugPageInfo:', info);
        return info;
    };
})();
