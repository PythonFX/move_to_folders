import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import string_utils
from exceptions import MultipleVideoNumberMatch, NoVideoNumberMatch
from jav_metadata.task import Task, TaskStatus

VIDEO_EXTENSIONS = {'mp4', 'mkv', 'avi', 'm4v', 'wmv', 'mov', 'flv', 'webm'}


def scan_movie_root(movie_root, logger=None):
    """
    递归扫描目录，为每个视频提取番号并创建任务。
    同一番号去重（封面只下载一次，存到第一个视频所在目录）。
    番号提取失败的文件生成 NO NUMBER 任务，不影响整体。
    """
    tasks = []
    seen_numbers = set()

    for dir_path, _, file_names in os.walk(movie_root):
        for file_name in sorted(file_names):
            ext = os.path.splitext(file_name)[1].lower().lstrip('.')
            if ext not in VIDEO_EXTENSIONS:
                continue
            video_path = os.path.join(dir_path, file_name)
            try:
                number = string_utils.get_video_number(file_name)
            except (NoVideoNumberMatch, MultipleVideoNumberMatch) as e:
                task = Task(number='', video_path=video_path,
                            status=TaskStatus.NO_NUMBER, message=f'{file_name} | {e}')
                tasks.append(task)
                if logger:
                    logger.log(task)
                continue

            if number in seen_numbers:
                continue
            seen_numbers.add(number)
            tasks.append(Task(number=number, video_path=video_path))

    return tasks
