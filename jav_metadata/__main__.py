import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from jav_metadata.config import load_config
from jav_metadata.logger import ResultLogger
from jav_metadata.scanner import scan_movie_root
from jav_metadata.scheduler import run, summarize
from jav_metadata.task import TaskStatus

USERSCRIPT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'userscript', 'javbus_cover_downloader.user.js')


def setup_browser():
    """启动独立 Profile 的 Chrome 并停住，给用户安装 Tampermonkey、导入脚本的时机"""
    from jav_metadata.browser_controller import BrowserController

    config = load_config()
    with BrowserController(config) as browser:
        page = browser.context.new_page()
        page.goto('https://www.tampermonkey.net/', wait_until='domcontentloaded')
        print()
        print('=' * 60)
        print('浏览器已启动（独立 Profile），请在该窗口中完成：')
        print()
        print('1. 在当前打开的 tampermonkey.net 页面安装 Tampermonkey 扩展')
        print('2. 打开 Tampermonkey 管理面板 → 实用工具 → 导入 → 选择文件：')
        print(f'   {USERSCRIPT_PATH}')
        print('   （或在管理面板新建脚本，把该文件内容粘贴进去）')
        print('3. 确认脚本已启用（match: https://www.javbus.com/*）')
        print()
        print('可选验证：打开任意 javbus 详情页，F12 Console 执行')
        print('   window.debugPageInfo()  应能看到 title / coverUrl')
        print('=' * 60)
        input('完成后回到这里按回车关闭浏览器...')
    print('setup 完成，接下来运行: python -m jav_metadata --test')


def main():
    parser = argparse.ArgumentParser(
        prog='python -m jav_metadata',
        description='JAV Metadata Automation — Python 调度端（油猴负责页面逻辑）',
    )
    parser.add_argument('--config', help='config.yaml 路径，默认包内配置')
    parser.add_argument('--root', help='覆盖 config 中的 movie_root')
    parser.add_argument('--retry-failed', action='store_true', help='只重跑上次失败的任务')
    parser.add_argument('--test', action='store_true', help='测试模式：只处理前两个任务后停止')
    parser.add_argument('--setup', action='store_true',
                        help='只启动独立 Profile 的 Chrome 并等待，用于安装 Tampermonkey 和导入脚本')
    parser.add_argument('--search', metavar='KEYWORD',
                        help='搜索模式：逐页收集搜索结果的番号并输出（不下载封面）')
    parser.add_argument('--max-pages', type=int, default=None, help='--search 最多翻页数')
    parser.add_argument('--magnets', metavar='NUMBER', help='提取指定番号的磁力下载列表并输出')
    args = parser.parse_args()

    config = load_config(args.config)

    if args.setup:
        setup_browser()
        return

    logger = ResultLogger()
    logger.info(f'log file: {logger.log_path}')

    if args.search:
        from jav_metadata.search import collect_search_numbers
        numbers = collect_search_numbers(config, args.search, max_pages=args.max_pages, logger=logger)
        for number in numbers:
            print(number)
        logger.info(f'search "{args.search}": total {len(numbers)} movie(s)')
        return

    if args.magnets:
        from jav_metadata.search import get_movie_magnets
        magnets = get_movie_magnets(config, args.magnets, logger=logger)
        for m in magnets:
            print(f'{m["date"]}\t{m["size"]}\t{m["name"]}\n\t{m["magnet"]}')
        logger.info(f'{args.magnets}: total {len(magnets)} magnet(s)')
        return

    if args.root:
        config['movie_root'] = args.root
    if not config['movie_root'] or not os.path.isdir(config['movie_root']):
        print('error: 请通过 --root 或 config.yaml 的 movie_root 指定有效的视频目录')
        sys.exit(1)

    logger.info(f'scanning: {config["movie_root"]}')

    tasks = scan_movie_root(config['movie_root'], logger)
    logger.info(f'{len(tasks)} task(s) found')

    if args.test:
        # 只截取有番号的任务，NO NUMBER 不占用测试名额
        tasks = [t for t in tasks if t.status != TaskStatus.NO_NUMBER][:2]
        logger.info(f'--test mode: only processing first {len(tasks)} task(s)')

    tasks = run(tasks, config, logger, retry_failed=args.retry_failed)
    summarize(tasks, logger)


if __name__ == '__main__':
    main()
