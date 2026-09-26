import numpy as np, soundfile as sf, soxr, sys
from mlx_audio.stt.utils import load
m = load("mlx-community/whisper-large-v3-turbo-asr-fp16")
for id in sys.argv[1:]:
    a, sr = sf.read(f'takes/{id}_t1.wav', dtype='float32'); a = soxr.resample(a, sr, 16000)
    for pad in [0.0, 0.5, 1.5]:
        z = np.zeros(int(pad*16000), np.float32)
        for wt in [False, True]:
            r = m.generate(np.concatenate([z, a, z]), language='fr', word_timestamps=wt, temperature=0.0, condition_on_previous_text=False)
            print(id, pad, wt, '|', r.text.strip())
