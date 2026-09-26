"""Normalisation de texte français pour comparer texte envoyé et transcription."""
import re, unicodedata
from num2words import num2words

# Graphies équivalentes (même prononciation) que Whisper peut choisir.
EQUIV = {
    'xi': 'ksi', 'ksy': 'ksi', 'eta': 'eta', 'heta': 'eta', 'etat': 'eta',
    'pleiade': 'pleiade', 'pleyade': 'pleiade', 'pleiades': 'pleiades',
    'vegeces': 'vegece', 'vegesse': 'vegece', 'vegess': 'vegece',
    'antikythere': 'anticythere', 'antikythera': 'anticythere',
    'sarosse': 'saros', 'sarros': 'saros', 'hesiod': 'hesiode',
    'veges': 'vegece', 'vegesse': 'vegece', 'anticitaire': 'anticythere', 'anticitere': 'anticythere',
    'olympiades': None,  # différent : ne pas rapprocher
    'cents': 'cent', 'vingts': 'vingt', 'jeu': 'jeux', 'mil': 'mille',
    'o': 'o', 'oh': 'o',
}


def strip_accents(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')


def _num(m):
    n = int(m.group(0))
    return ' ' + num2words(n, lang='fr') + ' '


def words(s, equiv=True):
    s = s.lower()
    s = s.replace('’', "'").replace('‘', "'")
    s = re.sub(r'(\d)[\s  ](\d{3})\b', r'\1\2', s)   # 1 900 -> 1900
    s = re.sub(r'\d+', _num, s)
    s = re.sub(r'\bdenticit(?:aire|ère|ere)\b', "d'anticythère", s)   # « d'Anticythère » collé par Whisper
    s = re.sub(r'\bau\s+tour\s+du\b', 'autour du', s)                      # homophone
    s = re.sub(r'\bzodiac\b', 'zodiaque', s)
    s = s.replace('-', ' ').replace("'", ' ')
    s = re.sub(r'[«»"“”.,:;!?…()\[\]—–/]', ' ', s)
    s = strip_accents(s)
    out = []
    for w in s.split():
        if equiv and w in EQUIV and EQUIV[w]:
            w = EQUIV[w]
        out.append(w)
    return out


def align(ref, hyp):
    """Levenshtein ; renvoie (S, D, I, ops) avec ops = liste de (op, r, h)."""
    n, m = len(ref), len(hyp)
    d = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1): d[i][0] = i
    for j in range(m + 1): d[0][j] = j
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            c = 0 if ref[i-1] == hyp[j-1] else 1
            d[i][j] = min(d[i-1][j-1] + c, d[i-1][j] + 1, d[i][j-1] + 1)
    i, j, ops = n, m, []
    while i > 0 or j > 0:
        if i > 0 and j > 0 and d[i][j] == d[i-1][j-1] + (0 if ref[i-1] == hyp[j-1] else 1):
            ops.append(('=' if ref[i-1] == hyp[j-1] else 'S', ref[i-1], hyp[j-1])); i -= 1; j -= 1
        elif i > 0 and d[i][j] == d[i-1][j] + 1:
            ops.append(('D', ref[i-1], None)); i -= 1
        else:
            ops.append(('I', None, hyp[j-1])); j -= 1
    ops.reverse()
    S = sum(o[0] == 'S' for o in ops); D = sum(o[0] == 'D' for o in ops); I = sum(o[0] == 'I' for o in ops)
    return S, D, I, ops


def wer(ref_text, hyp_text):
    r, h = words(ref_text), words(hyp_text)
    S, D, I, ops = align(r, h)
    errs = [o for o in ops if o[0] != '=']
    return dict(n=len(r), S=S, D=D, I=I, wer=(S + D + I) / max(1, len(r)), errs=errs)


if __name__ == '__main__':
    print(words("En 1900, des pêcheurs d'éponges ; Êta : 0, 8 ou 16 heures. Tournez-la ! « Olympia »"))
    print(wer("En mille neuf cent, des pêcheurs", "En 1900, des pécheurs"))


def phon(w):
    """Clé phonétique grossière : neutralise les finales muettes (pluriels, e muet, -ent verbal)."""
    w = re.sub(r'c(?=[eiy])', 's', w)
    if len(w) > 2 and w[-1] in 'sx': w = w[:-1]
    if len(w) > 5 and w.endswith('ent'): w = w[:-2]
    while len(w) > 2 and w.endswith('e'): w = w[:-1]
    return w


def pwords(s):
    return [phon(w) for w in words(s)]
