import os
import yaml

DEFAULT_CONFIG = {
    'movie_root': '/Volumes/XSK/==new==/==new==',
    'retry_count': 3,
    'timeout': 30000,
    'download_delay': 3,
    'headless': True,
    'close_tab_after_download': True,
    'chrome_profile_dir': os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.chrome-profile'),
    'detail_url_template': 'https://www.javbus.com/{number}',
    'skip_processed': True,
    'inject_userscript': True,  # Python 自注入页面层脚本(不依赖 Tampermonkey)
}

DEFAULT_CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.yaml')


def load_config(path=None):
    """读取 config.yaml；文件不存在时写入默认配置；缺失键用默认值补齐"""
    path = path or DEFAULT_CONFIG_PATH
    if not os.path.exists(path):
        with open(path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(DEFAULT_CONFIG, f, allow_unicode=True, sort_keys=False)
        return dict(DEFAULT_CONFIG)

    with open(path, 'r', encoding='utf-8') as f:
        loaded = yaml.safe_load(f) or {}

    config = dict(DEFAULT_CONFIG)
    config.update(loaded)
    return config
