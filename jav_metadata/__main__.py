import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from jav_metadata.config import load_config
from jav_metadata.logger import ResultLogger
from jav_metadata.scanner import scan_movie_root
from jav_metadata.scheduler import run, summarize


def main():
    parser = argparse.ArgumentParser(
        prog='python -m jav_metadata',
        description='JAV Metadata Automation — Python 调度端（油猴负责页面逻辑）',
    )
    parser.add_argument('--config', help='config.yaml 路径，默认包内配置')
    parser.add_argument('--root', help='覆盖 config 中的 movie_root')
    parser.add_argument('--retry-failed', action='store_true', help='只重跑上次失败的任务')
    args = parser.parse_args()

    config = load_config(args.config)
    if args.root:
        config['movie_root'] = args.root
    if not config['movie_root'] or not os.path.isdir(config['movie_root']):
        print('error: 请通过 --root 或 config.yaml 的 movie_root 指定有效的视频目录')
        sys.exit(1)

    logger = ResultLogger()
    logger.info(f'log file: {logger.log_path}')
    logger.info(f'scanning: {config["movie_root"]}')

    tasks = scan_movie_root(config['movie_root'], logger)
    logger.info(f'{len(tasks)} task(s) found')

    tasks = run(tasks, config, logger, retry_failed=args.retry_failed)
    summarize(tasks, logger)


if __name__ == '__main__':
    main()
