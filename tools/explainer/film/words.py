"""Word-level timings of the French voice-over (input of timeline.py).

Runs the local STT model parakeet-tdt-0.6b-v3 (mlx-audio, already in the HF cache: no download) on each chapter
file build/out/explainer/voice/chN.wav and writes build/out/explainer/film/words.json:
    {"model": ..., "chapters": {"1": [{"w": "Il", "start": 0.0, "end": 0.24}, ...], ...}}
Times are in seconds from the start of chN.wav (NOT narration_full.wav).  Words are the STT spelling (numbers in
digits, a few homophones): timeline.py only uses them as time stamps, matched by the first letters.

    ~/voxtral-tts/bin/python tools/explainer/film/words.py
"""
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[3]
VOICE = ROOT / 'build' / 'out' / 'explainer' / 'voice'
OUT = ROOT / 'build' / 'out' / 'explainer' / 'film' / 'words.json'
MODEL = 'mlx-community/parakeet-tdt-0.6b-v3'


def main():
    from mlx_audio.stt.utils import load_model
    model = load_model(MODEL)
    chapters = {}
    for n in range(1, 8):
        res = model.generate(str(VOICE / f'ch{n}.wav'))
        words = []
        for s in res.sentences:
            cur = None
            for tok in s.tokens:            # sub-word tokens: a leading space starts a new word
                if cur is None or tok.text.startswith(' '):
                    if cur:
                        words.append(cur)
                    cur = {'w': tok.text.strip(), 'start': round(float(tok.start), 3), 'end': round(float(tok.end), 3)}
                else:
                    cur['w'] += tok.text
                    cur['end'] = round(float(tok.end), 3)
            if cur:
                words.append(cur)
        chapters[str(n)] = words
        print(n, len(words), 'words', flush=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({'model': MODEL, 'unit': 's from the start of chN.wav', 'chapters': chapters},
                              ensure_ascii=False, indent=1))
    print('wrote', OUT)


if __name__ == '__main__':
    main()
