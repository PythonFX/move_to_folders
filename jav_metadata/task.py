from dataclasses import dataclass, field


class TaskStatus:
    PENDING = 'PENDING'
    SUCCESS = 'SUCCESS'
    FAILED = 'FAILED'
    TIMEOUT = 'TIMEOUT'
    NO_COVER = 'NO COVER'
    NO_TITLE = 'NO TITLE'
    NO_NUMBER = 'NO NUMBER'
    USERSCRIPT_MISSING = 'USERSCRIPT MISSING'
    SKIPPED = 'SKIPPED'


@dataclass
class Task:
    number: str = ''
    video_path: str = ''
    status: str = TaskStatus.PENDING
    attempts: int = 0
    message: str = ''
    extra: dict = field(default_factory=dict)
