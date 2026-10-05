import json
import os
from datetime import datetime

STATE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'collect_state.json')


def load_collect_state():
    """读取链接收集断点记录 {number: {'time': ..., 'matched': bool}}"""
    if not os.path.exists(STATE_PATH):
        return {}
    with open(STATE_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_collect_state(state):
    with open(STATE_PATH, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def filter_uncollected(numbers, state):
    """拆分 (待提取, 已提取跳过)，保持原有顺序"""
    pending = [n for n in numbers if n not in state]
    skipped = [n for n in numbers if n in state]
    return pending, skipped


def mark_collected(numbers, matched_map, state=None):
    """把成功提取的番号写入记录。matched_map: {number: 是否有规则匹配}"""
    if state is None:
        state = load_collect_state()
    for number in numbers:
        state[number] = {
            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'matched': bool(matched_map.get(number)),
        }
    save_collect_state(state)
    return state
