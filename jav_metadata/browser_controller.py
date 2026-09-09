import os
import re

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

from jav_metadata.task import TaskStatus

# 文件名非法字符统一替换
ILLEGAL_FILENAME_CHARS = re.compile(r'[\\/:*?"<>|\r\n\t]')

# 过滤掉 Playwright 默认参数里影响"正常 Chrome 体验"的项：
# 不禁用扩展、不显示自动化提示条、不加 sandbox/mock keychain 等隔离参数
IGNORE_DEFAULT_ARGS = [
    '--enable-automation',
    '--disable-extensions',
    '--disable-component-extensions-with-background-pages',
    '--disable-default-apps',
    '--no-sandbox',
    '--disable-dev-shm-usage',
    '--use-mock-keychain',
]


def sanitize_filename(name):
    """统一替换非法字符，去首尾空格和点"""
    name = ILLEGAL_FILENAME_CHARS.sub('_', name)
    return name.strip(' .')


class BrowserController:
    """
    Playwright 浏览器控制层。
    只负责：启动真实 Chrome（独立 Profile）、打开页面、page.evaluate 调用油猴、监听下载。
    不做任何 DOM 解析。
    """

    def __init__(self, config):
        self.config = config
        self._playwright = None
        self.context = None

    def __enter__(self):
        self.launch()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def launch(self):
        self._playwright = sync_playwright().start()
        profile_dir = os.path.abspath(os.path.expanduser(self.config['chrome_profile_dir']))
        os.makedirs(profile_dir, exist_ok=True)
        self.context = self._playwright.chromium.launch_persistent_context(
            user_data_dir=profile_dir,
            channel='chrome',
            headless=self.config['headless'],
            accept_downloads=True,
            ignore_default_args=IGNORE_DEFAULT_ARGS,
            args=['--disable-blink-features=AutomationControlled'],
        )
        self.context.set_default_timeout(self.config['timeout'])

    def close(self):
        if self.context:
            self.context.close()
            self.context = None
        if self._playwright:
            self._playwright.stop()
            self._playwright = None

    def process_task(self, task):
        """
        处理单个任务：打开详情页 → 调油猴 → 监听下载 → 落盘 标题.jpg。
        只修改 task.status / task.message，不抛异常（超时映射为 TIMEOUT）。
        """
        url = self.config['detail_url_template'].replace('{number}', task.number)
        page = self.context.new_page()
        try:
            self._process_on_page(page, task, url)
        except PlaywrightTimeoutError:
            task.status = TaskStatus.TIMEOUT
            task.message = f'timeout opening {url}'
        finally:
            if self.config['close_tab_after_download'] or task.status != TaskStatus.SUCCESS:
                try:
                    page.close()
                except Exception:
                    pass

    def _process_on_page(self, page, task, url):
        page.goto(url, wait_until='domcontentloaded')

        ready = page.evaluate("typeof window.isReady === 'function' && window.isReady()")
        if not ready:
            task.status = TaskStatus.USERSCRIPT_MISSING
            task.message = 'window.isReady() not available'
            return

        info = page.evaluate("window.getMovieInfo()")
        if not info or not info.get('title'):
            task.status = TaskStatus.NO_TITLE
            task.message = 'userscript returned no title'
            return
        if not info.get('coverUrl'):
            task.status = TaskStatus.NO_COVER
            task.message = 'userscript returned no coverUrl'
            return

        save_path = self._cover_save_path(task, info['title'])
        if os.path.exists(save_path):
            task.status = TaskStatus.SKIPPED
            task.message = f'cover already exists: {save_path}'
            return

        # 事件驱动等待下载完成，不 sleep
        with page.expect_download() as download_info:
            page.evaluate("window.downloadCurrentMovie()")
        download = download_info.value
        download.save_as(save_path)

        task.status = TaskStatus.SUCCESS
        task.message = save_path
        task.extra['title'] = info['title']

    def _cover_save_path(self, task, title):
        folder = os.path.dirname(task.video_path)
        return os.path.join(folder, sanitize_filename(title) + '.jpg')
