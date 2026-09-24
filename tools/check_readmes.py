"""Structural check of the translated READMEs against README.md (headings, tables, code, links, key numbers, language bar)."""
import re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
LANGS = ['fr', 'es', 'de', 'it', 'pt', 'el', 'zh', 'ja']
def parse(t):
    code = re.findall(r"```.*?```", t, flags=re.S)
    lines = t.split('\n'); t = '\n'.join(lines[:2] + lines[3:])          # drop the language bar (line 3)
    body = re.sub(r"```.*?```", "", t, flags=re.S)
    return dict(
        headings=[len(m) for m in re.findall(r"^(#+) ", body, flags=re.M)],
        table_rows=len(re.findall(r"^\|.*\|\s*$", body, flags=re.M)),
        code=code,
        links=sorted(re.findall(r"\]\(([^)]+)\)", body)),
        inline_code=sorted(re.findall(r"`([^`]+)`", body)),
        numbers=sorted(set(re.findall(r"[−-]?\d+/\d+|10⁻\d|7·10⁻⁷|±6\.58°|180° ± 0\.03°|(?<![\d,. ])\d{2,}(?![\d,.]\d)", body)) - {'000', '5'}),
    )
ref = parse((ROOT / 'README.md').read_text())
bad = 0
for l in LANGS:
    p = ROOT / f'README.{l}.md'
    if not p.exists(): print(f'{l}: MISSING'); bad += 1; continue
    t = p.read_text(); d = parse(t); issues = []
    for k in ('headings', 'table_rows', 'code', 'links'):
        if d[k] != ref[k]: issues.append(k)
    miss_num = [n for n in ref['numbers'] if n not in d['numbers']]
    if miss_num: issues.append(f'numbers missing {miss_num[:8]}')
    miss_ic = [c for c in set(ref['inline_code']) if c not in set(d['inline_code'])]
    if miss_ic: issues.append(f'inline code missing {miss_ic[:6]}')
    bar = p.read_text().split('\n')[2]
    if '[English](README.md)' not in bar or bar.count('](README.') != 8: issues.append('language bar')
    print(f"{l}: {'OK' if not issues else 'ISSUES ' + '; '.join(issues)}")
    bad += bool(issues)
sys.exit(1 if bad else 0)
