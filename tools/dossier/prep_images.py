# Re-encode the film stills and one diagram used by the dossier (run with a Python that has PIL,
# e.g. ~/voxtral-tts/bin/python). Output: <name>.jpg next to this script, 1400 px wide, quality 80.
import os
from PIL import Image
EX = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'build/out/explainer')
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = {
    'film_ch1': 'film/comp/00470.png',    # ch. 1: the machine reassembles, corroded
    'film_ch5': 'film/comp/02240.png',    # ch. 5: Games dial, historical pairs, pointer enters ΙΣΘΜΙΑ ΟΛΥΜΠΙΑ
    'film_ch6': 'film/comp/02560.png',    # ch. 6: Saros pointer enters cell 112 « Σ Η »
    'film_ch7': 'film/comp/03363.png',    # ch. 7: parapegma, Ξ (illustration)
    'diag_eclipse': 'diagrams/eclipse/0200.png',  # animated diagram: full moon on a node
}
W = 1400
for name, rel in SRC.items():
    im = Image.open(os.path.join(EX, rel)).convert('RGB')
    h = round(im.height * W / im.width)
    im = im.resize((W, h), Image.LANCZOS)
    out = os.path.join(HERE, name + '.jpg')
    im.save(out, 'JPEG', quality=80, optimize=True, progressive=True)
    print(name, im.size, os.path.getsize(out))
