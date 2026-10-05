import time

from jav_metadata.browser_controller import BrowserController

SEARCH_URL_TEMPLATE = 'https://www.javbus.com/search/{keyword}/{page}'
DETAIL_URL_TEMPLATE = 'https://www.javbus.com/{number}'


def collect_search_numbers(config, keyword, query='type=&parent=ce', max_pages=None, logger=None):
    """
    逐页打开搜索结果页，经油猴 window.getSearchResults() 提取番号。
    去重；某页没有新番号（越界后 javbus 会重复最后一页）或达到 max_pages 即停。
    返回有序去重后的番号列表。
    """
    numbers = []
    seen = set()
    delay = config.get('download_delay', 3)

    with BrowserController(config) as browser:
        page = browser.context.new_page()
        page_num = 1
        while True:
            url = SEARCH_URL_TEMPLATE.format(keyword=keyword, page=page_num)
            if query:
                url += '?' + query
            page.goto(url, wait_until='domcontentloaded')
            page.wait_for_timeout(2000)  # 给油猴注入留时间

            results = page.evaluate(
                "typeof window.getSearchResults === 'function' ? window.getSearchResults() : []")
            new_items = [r for r in results if r['number'] not in seen]
            if logger:
                logger.info(f'search page {page_num}: {len(results)} item(s), {len(new_items)} new')

            if not new_items:
                break
            for r in new_items:
                seen.add(r['number'])
                numbers.append(r['number'])

            page_num += 1
            if max_pages and page_num > max_pages:
                break
            time.sleep(delay)  # 翻页间隔，模拟真人

    return numbers


def get_movie_magnets(config, number, logger=None):
    """打开详情页，经油猴 window.getMagnetList() 提取磁力列表 [{name, magnet, size, date}]"""
    url = DETAIL_URL_TEMPLATE.format(number=number)
    with BrowserController(config) as browser:
        page = browser.context.new_page()
        page.goto(url, wait_until='domcontentloaded')
        page.wait_for_timeout(2000)
        magnets = page.evaluate(
            "typeof window.getMagnetList === 'function' ? window.getMagnetList() : []")
        if logger:
            logger.info(f'{number}: {len(magnets)} magnet(s)')
        return magnets
