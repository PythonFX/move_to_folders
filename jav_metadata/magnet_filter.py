import json
import os
import re

DEFAULT_RULES_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'filter_rules.json')

# 磁力名中番号尾巴的可选文件扩展名（如 -C.mp4 也视为 -C）
_EXTENSION_RE = re.compile(r'\.\w{2,4}$')


def load_rules(path=None):
    """加载筛选规则 JSON；文件不存在时抛错提示（规则是用户的显式配置）"""
    path = path or DEFAULT_RULES_PATH
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def _split_id_tail(name, number):
    """磁力名以番号开头(大小写不敏感)时,拆出 (名字中的番号, 尾巴)；否则 None"""
    if not name.lower().startswith(number.lower()):
        return None
    return name[:len(number)], name[len(number):].strip()


def _id_case(id_text):
    letters = [c for c in id_text if c.isalpha()]
    if letters and all(c.isupper() for c in letters):
        return 'upper'
    if letters and all(c.islower() for c in letters):
        return 'lower'
    return 'mixed'


def _match_step(magnet, number, step):
    """单条规则步匹配一个磁力候选。contains_all 针对全名(大小写不敏感);
    tail 针对番号后的尾巴(忽略常见扩展名,大小写不敏感,精确相等,
    因此 -U 不会误中 -UC / -U-C)"""
    name = magnet.get('name', '')
    if 'contains_all' in step:
        lower = name.lower()
        return all(kw.lower() in lower for kw in step['contains_all'])

    split = _split_id_tail(name, number)
    if not split:
        return False
    id_text, tail = split
    tail_core = _EXTENSION_RE.sub('', tail)
    # 默认尾巴大小写不敏感；规则可声明 tail_case_sensitive（如区间3的 -4k 仅小写）
    if step.get('tail_case_sensitive'):
        if tail_core != step['tail']:
            return False
    elif tail_core.upper() != step['tail'].upper():
        return False
    want_case = step.get('id_case', 'any')
    if want_case == 'any':
        return True
    return _id_case(id_text) == want_case


def _eval_steps(magnets, number, steps):
    """按规则步顺序取第一个有候选的步,返回该步第一个候选"""
    for step in steps:
        candidates = [m for m in magnets if _match_step(m, number, step)]
        if candidates:
            return candidates[0]
    return None


def select_magnets(magnets, number, rules):
    """对一部片按规则选出三个区间的磁力。区间2仅在区间1空缺时评估。
    返回 {'section1': magnet|None, 'section2': ..., 'section3': ...}"""
    result = {}
    for key in ('section1', 'section2', 'section3'):
        section = rules.get(key)
        if not section:
            result[key] = None
            continue
        fallback_of = section.get('fallback_of')
        if fallback_of and result.get(fallback_of):
            result[key] = None
            continue
        result[key] = _eval_steps(magnets, number, section.get('steps', []))
    return result
