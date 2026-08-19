import json
import os
import time
from datetime import datetime

from jav_metadata.browser_controller import BrowserController
from jav_metadata.task import TaskStatus

STATE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'state.json')

# 失败后值得重试的状态
RETRYABLE_STATUSES = {TaskStatus.FAILED, TaskStatus.TIMEOUT, TaskStatus.NO_COVER, TaskStatus.NO_TITLE}


def load_state():
    if not os.path.exists(STATE_PATH):
        return {}
    with open(STATE_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_state(state):
    with open(STATE_PATH, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def _record(state, task):
    state[task.number] = {
        'status': task.status,
        'title': task.extra.get('title', ''),
        'message': task.message,
        'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    }


def run(tasks, config, logger, retry_failed=False):
    """
    主调度循环：逐任务执行，单任务失败不影响整体，支持失败重跑。
    """
    state = load_state()

    pending = []
    for task in tasks:
        if task.status == TaskStatus.NO_NUMBER:
            continue  # scan 时已记录
        previous = state.get(task.number, {})
        if retry_failed:
            if previous.get('status') == TaskStatus.SUCCESS:
                task.status = TaskStatus.SKIPPED
                task.message = 'already succeeded, --retry-failed only reruns failures'
                logger.log(task)
                continue
        elif config['skip_processed'] and previous.get('status') == TaskStatus.SUCCESS:
            task.status = TaskStatus.SKIPPED
            task.message = 'already succeeded'
            logger.log(task)
            continue
        pending.append(task)

    if not pending:
        logger.info('no pending tasks')
        return tasks

    retry_count = config['retry_count']
    with BrowserController(config) as browser:
        for index, task in enumerate(pending):
            for attempt in range(1, retry_count + 1):
                task.attempts = attempt
                try:
                    browser.process_task(task)
                except Exception as e:
                    task.status = TaskStatus.FAILED
                    task.message = str(e)

                # 油猴未就绪属于环境问题，重试无意义
                if task.status in (TaskStatus.SUCCESS, TaskStatus.SKIPPED, TaskStatus.USERSCRIPT_MISSING):
                    break
                if task.status not in RETRYABLE_STATUSES:
                    break
                if attempt < retry_count:
                    logger.info(f'{task.number} | RETRY {attempt}/{retry_count} | {task.status} | {task.message}')

            logger.log(task)
            _record(state, task)
            save_state(state)

            if index < len(pending) - 1:
                time.sleep(config['download_delay'])

    return tasks


def summarize(tasks, logger):
    counts = {}
    for task in tasks:
        counts[task.status] = counts.get(task.status, 0) + 1

    logger.info('===== SUMMARY =====')
    for status, count in sorted(counts.items()):
        logger.info(f'{status}: {count}')

    failed = [t for t in tasks if t.status in RETRYABLE_STATUSES]
    if failed:
        logger.info('failed numbers (rerun with --retry-failed):')
        for task in failed:
            logger.info(f'  {task.number} | {task.status} | {task.message}')
