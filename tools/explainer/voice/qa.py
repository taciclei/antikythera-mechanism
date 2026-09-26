"""Compare chaque prise transcrite à son texte TTS. Usage: qa.py [take|all]"""
import sys, json, pathlib
import textnorm as T

W = pathlib.Path(__file__).parent
rows = []
for sj in sorted((W / 'takes').glob('*.stt.json')):
    meta = json.loads(sj.with_name(sj.name.replace('.stt.json', '.json')).read_text())
    st = json.loads(sj.read_text())
    r = T.wer(meta['text'], st['text'])
    rows.append(dict(id=meta['id'], take=meta['take'], dur=round(meta['dur'], 2), wer=round(r['wer'], 3),
                     n=r['n'], errs=r['errs'], hyp=st['text'], ref=meta['text'],
                     minp=min([w['p'] for w in st['words']] or [0])))
if __name__ == '__main__':
    for r in rows:
        flag = '' if r['wer'] == 0 else '  <<<'
        print(f"{r['id']} t{r['take']} {r['dur']:5.2f}s WER {r['wer']:.2f} minp {r['minp']:.2f}{flag}")
        if r['wer'] > 0:
            print('   REF:', r['ref']); print('   HYP:', r['hyp'])
            print('   ', [(o, a, b) for o, a, b in r['errs']])
    json.dump(rows, open(W / 'qa_units.json', 'w'), ensure_ascii=False, indent=1)
