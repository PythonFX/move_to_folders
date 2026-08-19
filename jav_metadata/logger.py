import logging
import os
from datetime import datetime

LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')


class ResultLogger:
    """终端 + 文件双写日志：时间 | 番号 | 状态 | 消息"""

    def __init__(self):
        os.makedirs(LOG_DIR, exist_ok=True)
        log_path = os.path.join(LOG_DIR, datetime.now().strftime('result_%Y%m%d_%H%M%S.log'))

        self._logger = logging.getLogger('jav_metadata')
        self._logger.setLevel(logging.INFO)
        self._logger.propagate = False

        formatter = logging.Formatter('%(asctime)s | %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

        file_handler = logging.FileHandler(log_path, encoding='utf-8')
        file_handler.setFormatter(formatter)
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)

        self._logger.addHandler(file_handler)
        self._logger.addHandler(stream_handler)
        self.log_path = log_path

    def log(self, task):
        number = task.number or '-'
        self._logger.info(f'{number} | {task.status} | {task.message}')

    def info(self, message):
        self._logger.info(message)
