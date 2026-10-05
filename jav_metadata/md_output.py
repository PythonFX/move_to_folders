import os
from datetime import datetime

from jav_metadata.magnet_filter import load_rules

SECTION_KEYS = ('section1', 'section2', 'section3')


def _fmt_section_line(label, magnet):
    """单个区间的输出行：命中给名称+链接，未命中标注"""
    if magnet:
        return f'- {label}: {magnet["name"]}\n  {magnet["magnet"]}'
    return f'- {label}: (无匹配)'


def build_batch_block(input_text, entries, rules):
    """
    生成一次点击操作的 md 区块：
    批次头 → 每部片三个区间明细 → 批次总览表（行=片，列=区间1/2/3）。
    entries: [{'number': str, 'sections': {'section1': magnet|None, ...}}]
    """
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    lines = [
        f'## 批次 {now} · 输入: {input_text} ({len(entries)} 部)',
        '',
    ]
    for entry in entries:
        number = entry['number']
        sections = entry['sections']
        lines.append(f'### {number}')
        for key in SECTION_KEYS:
            section = rules.get(key, {})
            label = section.get('title', key)
            lines.append(_fmt_section_line(label, sections.get(key)))
        lines.append('')

    # 总览表
    short_titles = []
    for key in SECTION_KEYS:
        title = rules.get(key, {}).get('title', key)
        short_titles.append(title.split('·')[0].strip() if '·' in title else title)
    lines.append('| 番号 | ' + ' | '.join(short_titles) + ' |')
    lines.append('| --- | --- | --- | --- |')
    for entry in entries:
        cells = []
        for key in SECTION_KEYS:
            magnet = entry['sections'].get(key)
            cells.append(magnet['name'] if magnet else '—')
        lines.append(f'| {entry["number"]} | ' + ' | '.join(cells) + ' |')
    lines.append('')
    return '\n'.join(lines)


def append_batch(md_path, input_text, entries, rules=None):
    """把一批结果追加进当日 md 文件：批次之间用一个空行隔开，绝不覆盖"""
    rules = rules or load_rules()
    block = build_batch_block(input_text, entries, rules)

    exists = os.path.exists(md_path)
    with open(md_path, 'a', encoding='utf-8') as f:
        if not exists:
            date_str = os.path.splitext(os.path.basename(md_path))[0]
            f.write(f'# JAV 下载链接收集 · {date_str}\n')
        # 批次间空行分隔（新文件标题后同样空一行）
        f.write('\n' + block + '\n')
    return md_path


def dated_md_path(folder):
    """按日期命名的输出文件路径，如 20261005.md"""
    return os.path.join(folder, datetime.now().strftime('%Y%m%d') + '.md')
