# Voix off du film explicatif (Voxtral TTS, en local)

Scripts qui ont produit `build/out/explainer/voice/` (voix `fr_female` de Mistral Voxtral TTS, exécutée en local
avec MLX sur Apple Silicon ; poids sous licence CC BY-NC 4.0, donc usage non commercial).

- `units.py` : les 44 phrases, texte d'origine et texte envoyé à la synthèse (réécritures phonétiques : années en
  toutes lettres, « Xi » pour ksi…), pauses.
- `gen.py` : génération des prises (`~/voxtral-tts/bin/python`, modèle `mlx-community/Voxtral-4B-TTS-2603-mlx-bf16`).
- `stt.py`, `stt2.py` : transcription de contrôle (Whisper large-v3-turbo et Parakeet TDT 0.6B v3, en MLX).
- `select.py` / `pick.py` : découpe des prises en phrases et choix des meilleures d'après les deux transcriptions.
- `process.py` : assemblage, fondus de 5 ms, passe-haut 60 Hz, loudness −16 LUFS, limiteur −1 dBTP.
- `srt.py` : sous-titres calés sur les mots (Parakeet), texte d'origine.
- `textnorm.py`, `qa.py`, `final_qa.py`, `final_units.py` : normalisation et contrôles finaux.

Environnement : `uv venv ~/voxtral-tts --python 3.12 && VIRTUAL_ENV=~/voxtral-tts uv pip install mlx-audio
"mistral-common[audio]" pyloudnorm num2words`. Les scripts écrivent leurs prises intermédiaires à côté d’eux-mêmes
(`takes/`, journaux) : copiez ce dossier ailleurs avant de les relancer.
