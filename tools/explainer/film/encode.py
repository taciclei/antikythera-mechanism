#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Encodage du film « Le ciel dans une boîte » : images composées (composite.py) + voix -> MP4.

Vidéo H.264 (libx264, yuv420p, BT.709, CRF 18, preset slow, GOP 2 s, +faststart), audio AAC 192 kb/s, 48 kHz,
stéréo. La piste voix est mixée dans la même commande avec le filtre de audio_placement.json (adelay par chapitre,
amix normalize=0, apad à la durée du film) : aucun fichier intermédiaire.

  ~/voxtral-tts/bin/python tools/explainer/film/encode.py                       # film/comp -> film/film.mp4
  ~/voxtral-tts/bin/python tools/explainer/film/encode.py --preview \\
        --frames-dir build/out/explainer/film/preview_comp --out build/out/explainer/film/animatic_placeholder.mp4
  ~/voxtral-tts/bin/python tools/explainer/film/encode.py --verify-only build/out/explainer/film/film.mp4

--preview : 960 x 540, CRF 23, preset veryfast (aperçus rapides). Les images manquantes arrêtent l'encodage, sauf
--allow-missing (l'image précédente est tenue ; le nombre d'images tenues est affiché). Les images peuvent être
numérotées %05d.png (composite.py) ou %04d.png. Après l'encodage, le fichier est contrôlé : durée 160,36 s à une
image près (conteneur, vidéo et audio), 4 009 images, flux H.264 yuv420p et AAC 48 kHz ; résultat dans
<sortie>.check.json, code de retour 1 si un contrôle échoue.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
FILM = ROOT / 'build' / 'out' / 'explainer' / 'film'
FFMPEG = os.environ.get('FFMPEG', str(Path.home() / '.local' / 'bin' / 'ffmpeg'))


def load():
    T = json.loads((FILM / 'timeline.json').read_text(encoding='utf-8'))
    A = json.loads((FILM / 'audio_placement.json').read_text(encoding='utf-8'))
    return T, A


def voice_filter(A):
    """Fichiers et filtre de mixage, repris tels quels de audio_placement.json (ffmpeg_hint)."""
    files = [str(ROOT / c['file']) for c in A['clips']]
    m = re.search(r'-filter_complex\s+"([^"]+)"', A['ffmpeg_hint'])
    if not m:
        raise SystemExit('audio_placement.json : filtre introuvable dans ffmpeg_hint')
    filt = m.group(1)
    hinted = re.findall(r'-i\s+(\S+\.wav)', A['ffmpeg_hint'])
    if [str(ROOT / h) for h in hinted] != files:
        raise SystemExit('audio_placement.json : les fichiers de ffmpeg_hint ne suivent pas clips[]')
    return files, filt


def frame_file(d, f):
    for name in ('%05d.png' % f, '%04d.png' % f):
        p = d / name
        if p.exists() and p.stat().st_size > 0:
            return p
    return None


def build_sequence(frames_dir, n, allow_missing, tmp):
    """Liens %05d.png contigus (1..n) dans tmp ; les trous sont bouchés par l'image précédente si permis."""
    missing, last = [], None
    first_ok = next((frame_file(frames_dir, f) for f in range(1, n + 1) if frame_file(frames_dir, f)), None)
    if first_ok is None:
        raise SystemExit('aucune image dans %s' % frames_dir)
    for f in range(1, n + 1):
        p = frame_file(frames_dir, f)
        if p is None:
            missing.append(f)
            p = last or first_ok
        last = p
        os.symlink(p.resolve(), tmp / ('%05d.png' % f))
    if missing and not allow_missing:
        raise SystemExit('%d images manquantes dans %s (première : %d) : relancer composite.py ou passer '
                         '--allow-missing' % (len(missing), frames_dir, missing[0]))
    return missing


def probe_size(path):
    from PIL import Image
    with Image.open(path) as im:
        return im.size


def encode(args):
    T, A = load()
    n, fps, dur = T['frame_end'], T['fps'], T['total_seconds']
    frames_dir = Path(args.frames_dir)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    w, h = (960, 540) if args.preview else tuple(T['resolution'])
    crf = args.crf if args.crf is not None else (23 if args.preview else 18)
    preset = args.preset or ('veryfast' if args.preview else 'slow')
    with tempfile.TemporaryDirectory(prefix='enc_', dir=args.tmp) as td:
        tmp = Path(td)
        missing = build_sequence(frames_dir, n, args.allow_missing, tmp)
        src_w, src_h = probe_size(tmp / '00001.png')
        vf = ('[0:v]scale=%d:%d:flags=lanczos:out_color_matrix=bt709:out_range=tv,format=yuv420p,'
              'setparams=range=tv:color_primaries=bt709:color_trc=bt709:colorspace=bt709[v]' % (w, h))
        cmd = [FFMPEG, '-hide_banner', '-y', '-loglevel', 'error', '-stats',
               '-framerate', str(fps), '-start_number', '1', '-i', str(tmp / '%05d.png')]
        filt = vf
        maps = ['-map', '[v]']
        if not args.no_audio:
            files, afilt = voice_filter(A)
            for fl in files:
                cmd += ['-i', fl]
            # les entrées audio sont décalées d'un rang (l'entrée 0 est la vidéo)
            afilt = re.sub(r'\[(\d+)\]adelay', lambda m: '[%d:a]adelay' % (int(m.group(1)) + 1), afilt)
            filt = vf + ';' + afilt
            maps += ['-map', '[out]']
        cmd += ['-filter_complex', filt] + maps
        cmd += ['-c:v', 'libx264', '-preset', preset, '-crf', str(crf), '-pix_fmt', 'yuv420p',
                '-profile:v', 'high', '-g', str(2 * fps), '-bf', '2',
                '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-color_range', 'tv',
                '-r', str(fps), '-frames:v', str(n)]
        if not args.preview:
            cmd += ['-tune', 'film']
        if not args.no_audio:
            cmd += ['-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-ac', '2']
        cmd += ['-movflags', '+faststart', '-metadata', 'title=' + T['title'], '-t', '%.3f' % dur, str(out)]
        print('[encode] %d images %dx%d (%s) -> %s %dx%d, CRF %s, preset %s%s'
              % (n, src_w, src_h, frames_dir, out, w, h, crf, preset,
                 '' if not missing else ', %d images tenues (manquantes)' % len(missing)), flush=True)
        print('[encode] ' + ' '.join(shlex.quote(c) for c in cmd), flush=True)
        t0 = time.time()
        r = subprocess.run(cmd, cwd=str(ROOT))
        if r.returncode:
            raise SystemExit('ffmpeg a échoué (code %d)' % r.returncode)
        print('[encode] %.1f s' % (time.time() - t0), flush=True)
    return verify(out, T, expect_size=(w, h), audio=not args.no_audio, missing=missing)


# ----------------------------------------------------------------------------- contrôle
def _ffmpeg_stderr(args):
    r = subprocess.run([FFMPEG, '-hide_banner'] + args, capture_output=True, text=True)
    return r.stderr


def _hms(s):
    h, m, sec = s.split(':')
    return int(h) * 3600 + int(m) * 60 + float(sec)


def verify(path, T=None, expect_size=None, audio=True, missing=None):
    if T is None:
        T, _ = load()
    n, fps, dur = T['frame_end'], T['fps'], T['total_seconds']
    tol = 1.0 / fps + 1e-6
    info = _ffmpeg_stderr(['-i', str(path)])
    res = {'fichier': str(path), 'taille_octets': Path(path).stat().st_size, 'controles': []}

    def check(name, ok, detail):
        res['controles'].append({'controle': name, 'ok': bool(ok), 'detail': detail})
        print('[verify] %-5s %s : %s' % ('OK' if ok else 'ÉCHEC', name, detail), flush=True)

    m = re.search(r'Duration: (\d+:\d+:[\d.]+)', info)
    cdur = _hms(m.group(1)) if m else None
    check('durée du conteneur', cdur is not None and abs(cdur - dur) <= tol,
          '%s s (attendu %.2f s ± %.2f)' % (cdur, dur, tol))
    vs = re.search(r'Stream #0:\d+.*?: Video: (.*)', info)
    vline = vs.group(1) if vs else ''
    wh = re.search(r'(\d{3,5})x(\d{3,5})', vline)
    size = (int(wh.group(1)), int(wh.group(2))) if wh else None
    check('flux vidéo', vline.startswith('h264') and 'yuv420p' in vline and '25 fps' in vline and
          (expect_size is None or size == tuple(expect_size)), vline[:150])
    # images et durée du flux vidéo (copie sans décodage)
    st = _ffmpeg_stderr(['-i', str(path), '-map', '0:v:0', '-c', 'copy', '-f', 'null', '-'])
    fr = re.findall(r'frame=\s*(\d+)', st)
    tv = re.findall(r'time=(\d+:\d+:[\d.]+)', st)
    nf = int(fr[-1]) if fr else None
    check('nombre d\'images', nf == n, '%s (attendu %d)' % (nf, n))
    vdur = nf / fps if nf else None
    check('durée vidéo', vdur is not None and abs(vdur - dur) <= tol, '%s s' % vdur)
    if audio:
        as_ = re.search(r'Stream #0:\d+.*?: Audio: (.*)', info)
        aline = as_.group(1) if as_ else ''
        check('flux audio', aline.startswith('aac') and '48000 Hz' in aline, aline[:150])
        br = re.search(r'(\d+) kb/s', aline)
        check('débit audio', br is not None and 176 <= int(br.group(1)) <= 208, (br.group(0) if br else '?'))
        sa = _ffmpeg_stderr(['-i', str(path), '-map', '0:a:0', '-f', 'null', '-'])
        ta = re.findall(r'time=(\d+:\d+:[\d.]+)', sa)
        adur = _hms(ta[-1]) if ta else None
        check('durée audio (décodée)', adur is not None and abs(adur - dur) <= tol, '%s s' % adur)
        # niveau : la voix est bien là
        vol = _ffmpeg_stderr(['-i', str(path), '-map', '0:a:0', '-af', 'volumedetect', '-f', 'null', '-'])
        mv = re.search(r'mean_volume: ([-\d.]+) dB', vol)
        mx = re.search(r'max_volume: ([-\d.]+) dB', vol)
        check('niveau audio', mv is not None and float(mv.group(1)) > -40 and float(mx.group(1)) <= 0.0,
              'moyen %s dB, crête %s dB' % (mv and mv.group(1), mx and mx.group(1)))
    if missing:
        res['images_tenues'] = len(missing)
    res['ok'] = all(c['ok'] for c in res['controles'])
    Path(str(path) + '.check.json').write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding='utf-8')
    print('[verify] %s -> %s.check.json' % ('tout est bon' if res['ok'] else 'des contrôles échouent', path),
          flush=True)
    return 0 if res['ok'] else 1


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--frames-dir', default=str(FILM / 'comp'))
    ap.add_argument('--out', default=str(FILM / 'film.mp4'))
    ap.add_argument('--preview', action='store_true', help='960 x 540, CRF 23, preset veryfast')
    ap.add_argument('--crf', type=int)
    ap.add_argument('--preset')
    ap.add_argument('--allow-missing', action='store_true', help='tenir l\'image précédente à la place des trous')
    ap.add_argument('--no-audio', action='store_true')
    ap.add_argument('--tmp', default=None, help='dossier des liens temporaires')
    ap.add_argument('--verify-only', metavar='MP4')
    args = ap.parse_args()
    if args.verify_only:
        return verify(Path(args.verify_only))
    return encode(args)


if __name__ == '__main__':
    sys.exit(main())
