import json, html
from fractions import Fraction as F
from data import GEARS
import figs
Y = 365.2422
def fr(x, d=2): return f"{x:,.{d}f}".replace(",", " ").replace(".", ",")
def days(rate): return Y/abs(float(rate))
# verify the chain products while building rows
assert F(64,38)*F(48,24)*F(127,32) == F(254,19)
assert -F(64,38)*F(53,96)*F(27,223) * -1 * -1 == -F(477,4237)  # b2~l1 (-), l2~m1 (+), m3~e3 (-)
assert F(254,19) - F(477,4237) == F(56165,4237) - 0 or True
k1_rel = -(-F(254,19)) + (-F(477,4237))  # placeholder check below
assert (-F(477,4237)) - (-F(254,19)) == F(56165,4237)   # k1|e3 = -(e5 - e3), e5=-254/19
n1 = -F(53,57)*F(15,53); assert n1 == -F(5,19)
assert -F(57,60)*n1 == F(1,4)
p1 = -F(15,60)*n1; assert p1 == F(5,76); assert -F(12,60)*p1 == -F(1,76)
e3 = -F(477,4237); f1 = -F(188,53)*e3; g1 = -F(30,54)*f1; assert g1 == -F(940,4237)
h1 = -F(20,60)*g1; i1 = -F(15,60)*h1; assert i1 == -F(235,12711)
assert 1 - F(49*64, 62*48) == -F(5,93)
assert F(254,19) + F(5,93) == F(23717,1767)
assert F(51*89, 72*20) == F(1513,480) and F(51,44)*F(34,63) == F(289,462)
assert F(56,64)*F(38,71) == F(133,284) and F(56,64)*F(45,43) == F(315,344) and F(56,52)*F(61,68) == F(427,442)
T = [
 ("Manivelle a1","manivelle → a1 48 ⊥ b1 223","223/48","tours de manivelle par an",None,"par définition","S"),
 ("Soleil moyen (b1)","b1 223","+1","année tropique",Y,"base de temps","S"),
 ("Aiguille de date","b1 → piliers → plaque CP → tube de date","+1","année",Y,"exact","R"),
 ("Lune (aiguille b3)","b2 64→c1 38 · c2 48→d1 24 · d2 127→e2 32 · e5 50→k1 50 ⇢ k2 50→e6 50 · e1 32→b3 32","+254/19","mois sidéral",days(F(254,19)),"−11,5 ppm","S"),
 ("Ligne des apsides (e3)","b2 64→l1 38 · l2 53→m1 96 · m3 27→e3 223","−477/4237","révolution des apsides (8,88 ans)",days(F(477,4237)),"+0,36 %","R"),
 ("Anomalie (k1 sur e3)","e5 50→k1 50, porté par le plateau e3","+56165/4237","mois anomalistique",days(F(56165,4237)),"−45 ppm","S"),
 ("Phase de la Lune (q1)","b0 20 (Soleil moyen) ⊥ q1 20 sur l'aiguille lunaire","+235/19 rel. Lune","mois synodique",days(F(235,19)),"−12,5 ppm","H"),
 ("Métonique (n1)","m1 → m2 15→n1 53","−5/19","19 ans = 235 lunaisons, 5 tours",5*days(F(5,19)),"−12 ppm","R"),
 ("Olympiade (o1)","n3 57→o1 60","+1/4","cycle des Jeux, 4 ans",days(F(1,4)),"exact","R"),
 ("Callippique (cal1)","n2 15→p1 60 · p2 12→cal1 60","−1/76","76 ans",days(F(1,76)),"exact en années","R"),
 ("Saros (g1)","e4 188→f1 53 · f2 30→g1 54","−940/4237","223 lunaisons, 4 tours",4*days(F(940,4237)),"−12 ppm","R"),
 ("Exeligmos (i1)","g2 20→h1 60 · h2 15→i1 60","−235/12711","3 Saros",days(F(235,12711)),"−12 ppm","R"),
 ("Nœuds, main du dragon (nd48)","fx49 fixe→nd62 · nd64→nd48, sur b1","−5/93","18,6 ans, rétrograde",days(F(5,93)),"+4 ppm (sidéral)","H"),
 ("Mois draconitique (dérivé)","aiguille lunaire − nœuds","+23717/1767","mois draconitique",days(F(23717,1767)),"−14 ppm","H"),
 ("Mercure","fx51 fixe→me72 · me89→me40→me20, tenon + levier","1513/480 rel. b1","1513 synodiques en 480 ans",Y*480/1513,"−58 ppm","H"),
 ("Vénus","fx51 fixe→vn44 · vn34→vn26→r1 63, tenon + levier","289/462 rel. b1","289 synodiques en 462 ans",Y*462/289,"−65 ppm","H"),
 ("Soleil vrai","fx56 fixe→cp52→su56, excentrique + levier","su56 = 0 ; moyenne +1","anomalie solaire",Y,"exact en moyenne","H"),
 ("Mars","fx56→cp64 · ma38→ma40→ma71 ⇢ ma80s→ma80o","133/284 rel. CP ; sortie 151/284","133 synodiques en 284 ans",Y*284/133,"−31 ppm","H"),
 ("Jupiter","fx56→cp64 · ju45→ju40→ju43 ⇢ ju65s→ju65o","315/344 rel. CP ; sortie 29/344","315 synodiques en 344 ans",Y*344/315,"−31 ppm","H"),
 ("Saturne","fx56→cp52 · sa61→sa40→sa68 ⇢ sa86s→sa86o","427/442 rel. CP ; sortie 15/442","427 synodiques en 442 ans",Y*442/427,"−46 ppm","H"),
]
assert len(T) == 20
STC = {"S":("st-s","Survivant"),"R":("st-r","Reconstruit"),"H":("st-h","Hypothétique")}
rows = []
for name, chain, rate, target, per, err, st in T:
    pd = "—" if per is None else fr(per, 2 if per < 1000 else 1) + " j"
    c, l = STC[st]
    rows.append(f'<tr><td><b>{html.escape(name)}</b></td><td class="chain">{html.escape(chain)}</td><td class="mono">{html.escape(rate)}</td><td>{html.escape(target)}</td><td class="num mono">{pd}</td><td class="mono">{html.escape(err)}</td><td><span class="chip {c}">{l}</span></td></tr>')
M = [("a1 ⊥ b1 (couronne)","0,5776","axe de a1 à z = 18,9"),("b2 · c1 · l1","0,480","24,48 · 24,48"),("c2 · d1","0,4472","16,10"),
     ("d2 · e2","0,4855","38,60"),("e1 · b3","0,5594","17,90"),("l2 · m1","0,4966","37,00"),("m3 · e3","0,466","58,25"),
     ("e4 · f1","0,5203","62,70"),("e5 · k1","0,512","25,60"),("k2 · e6","0,534","26,70 (K′ décalé de 1,1 radialement)"),
     ("f2 · g1","0,5167","21,70"),("g2 · h1","0,4475","17,90"),("h2 · i1","0,4347","16,30"),("m2 · n1","0,514","17,48"),
     ("n3 · o1","0,4171","24,40"),("n2 · p1 · p2 · cal1","0,5","18,75 · 18,00"),("b0 · q1 (couronne)","0,5","face ≤ 1 mm"),
     ("fx49 · nd62","0,4865","27,00"),("nd64 · nd48","0,4821","27,00"),("fx51 · vn44 · me72","0,5389","25,60 · 33,15"),
     ("vn34 · vn26 · r1","0,521","15,63 · 23,18"),("me89 · me40 · me20","0,5","32,25 · 15,00"),
     ("plaque CP (19 roues)","0,48","25,92 · 28,80 · 24,24 · 41,28 · 20,40 · 19,92 · 31,20 · 18,72 · 26,64 · 38,40")]
mrows = "".join(f'<tr><td class="mono">{a}</td><td class="num mono">{b}</td><td class="mono">{c}</td></tr>' for a,b,c in M)
SRC = [("Freeth et al. 2021, « A Model of the Cosmos in the ancient Greek Antikythera Mechanism », Sci. Rep. 11:5821","https://pmc.ncbi.nlm.nih.gov/articles/PMC7955085/"),
 ("Freeth et al. 2021, informations supplémentaires (tables S8, S9)","https://static-content.springer.com/esm/art%3A10.1038%2Fs41598-021-84310-w/MediaObjects/41598_2021_84310_MOESM4_ESM.pdf"),
 ("Freeth et al. 2006, Nature 444:587","https://www.nature.com/articles/nature05357"),
 ("Freeth et al. 2006, notes supplémentaires","https://static-content.springer.com/esm/art%3A10.1038%2Fnature05357/MediaObjects/41586_2006_BFnature05357_MOESM1_ESM.pdf"),
 ("Freeth, Jones, Steele, Bitsakis 2008, notes supplémentaires (Olympiade, Callippique)","https://archive.nyu.edu/bitstream/2451/60882/2/Freeth_Jones_Steele_Bitsakis_2008_supplementary.pdf"),
 ("Freeth & Jones 2012, « The Cosmos in the Antikythera Mechanism », ISAW Papers 4","http://dlib.nyu.edu/awdl/isaw/isaw-papers/4/"),
 ("Price 1974, « Gears from the Greeks »","https://gwern.net/doc/history/1974-desollaprice.pdf"),
 ("Budiselic et al. 2020, preuve d'un calendrier lunaire","https://bhi.co.uk/wp-content/uploads/2020/12/BHI-Antikythera-Mechanism-Evidence-of-a-Lunar-Calendar.pdf"),
 ("Woan & Bayley 2024, nombre de trous de l'anneau calendrier","https://arxiv.org/abs/2403.00040"),
 ("Anastasiou et al. 2014, spirales à deux centres","https://journals.sagepub.com/doi/abs/10.1177/0021828614537185"),
 ("Szigety & Arenas 2025, dents triangulaires","https://arxiv.org/abs/2504.00327"),
 ("Voulgaris et al. 2021, 2022, 2024","https://arxiv.org/abs/2104.06181"),
 ("Efstathiou et al. 2021, réplique fonctionnelle","https://digitalheritagelab.eu/wp-content/uploads/2025/03/heritage-04-00211-v4_compressed.pdf"),
 ("Carman & Di Cocco 2016, phase lunaire","http://dlib.nyu.edu/awdl/isaw/isaw-papers/11/"),
 ("Freeth 2014, « Eclipse Prediction on the Ancient Greek Astronomical Calculating Machine Known as the Antikythera Mechanism », PLoS ONE 9(7):e103275 (51 cases à glyphe, 38 Σ, 28 Η)","https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0103275"),
 ("Carman & Evans 2014, « On the epoch of the Antikythera mechanism and its eclipse predictor », Archive for History of Exact Sciences 68:693-774","https://philpapers.org/rec/EVAOTE-2"),
 ("Bitsakis & Jones 2016, « The Front Dial and Parapegma Inscriptions », Almagest 7.1 (parapegme, anneau égyptien)","https://archive.nyu.edu/jspui/bitstream/2451/71597/6/IAM%203%20bitsakis-jones-2016-the-front-dial-and-parapegma-inscriptions.pdf"),
 ("Iversen 2017, « The Calendar on the Antikythera Mechanism and the Corinthian Family of Calendars », Hesperia 86.1:129-203 (cadran des Jeux)","https://www.jstor.org/stable/10.2972/hesperia.86.1.0129"),
 ("Jones 2017, A Portable Cosmos, Oxford University Press (compte rendu BMCR 2018.05.16)","https://bmcr.brynmawr.edu/2018/2018.05.16/"),
 ("Hésiode, Les Travaux et les Jours, v. 618-622 (citation française : trad. Leconte de Lisle, 1869 ; texte anglais en ligne : trad. Evelyn-White 1914)","https://www.theoi.com/Text/HesiodWorksDays.html"),
 ("Végèce, Epitoma rei militaris IV, 39 (saison de navigation)","https://www.thelatinlibrary.com/vegetius4.html"),
 ("Meeus, Astronomical Algorithms, 2e éd. (éléments moyens du calage J2000)", None),
 ("NASA/GSFC, F. Espenak, catalogues d'éclipses 2021-2030", [("Soleil","https://eclipse.gsfc.nasa.gov/SEdecade/SEdecade2021.html"),("Lune","https://eclipse.gsfc.nasa.gov/LEdecade/LEdecade2021.html")])]
def src_li(t, u):
    if u is None: return f'<li>{html.escape(t)}</li>'
    if isinstance(u, str): u = [("lien", u)]
    return f'<li>{html.escape(t)} · ' + " · ".join(f'<a href="{v}">{html.escape(k)}</a>' for k, v in u) + '</li>'
srcs = "".join(src_li(t, u) for t, u in SRC)
# ---------- Lean 4: theorem count per module, checked against the .lean files ----------
import os, re
HERE = os.path.dirname(os.path.abspath(__file__))
AK = os.path.dirname(os.path.dirname(HERE))          # repository root
os.chdir(HERE)                                      # template and images sit next to this script
LEAN = [("Kinematics.lean","généré","Une équation par contact d'engrenage, tirée des nombres de dents : 37 équations de Willis, 2 paires de couronnes, 4 tenons-rainures, 3 suiveurs. Théorèmes <span class=\"mono\">determined</span>, <span class=\"mono\">determined_by_crank</span>, <span class=\"mono\">consistent</span>, <span class=\"mono\">moves</span> et <span class=\"mono\">one_dof</span> : les vecteurs de vitesses moyennes admissibles forment exactement une droite, donc un seul degré de liberté.",5),
        ("Targets.lean","généré","Les 22 cibles astronomiques de la spec, déduites des seuls nombres de dents (b1 = 1 tour par an).",22),
        ("Geometry.lean","généré","Les 37 engrènements extérieurs : modules égaux et entraxe égal à m(z₁ + z₂)/2 à 10⁻⁶ mm près.",37),
        ("PinSlot.lean","à la main","Lois non linéaires (atan2) des 4 tenons-rainures et des 3 suiveurs ; écart maximal exactement arcsin(e/r) ; vitesses moyennes inchangées par un retard borné, ce qui justifie le modèle linéaire ; anomalie lunaire 6,579° &lt; arcsin(1,1/9,6) &lt; 6,581° ; amplitudes de Saturne, Jupiter, Mars, Mercure, Vénus et du Soleil vrai.",71),
        ("Astronomy.lean","à la main","Cycles de Méton, du Saros, de l'Exeligmos, de Callippe et des Olympiades ; anomalie et apsides lunaires, nœuds ; relations de périodes planétaires (sidérale = solaire − synodique) ; précision en jours face aux valeurs modernes, par exemple le mois sidéral à 0,0005 jour de 27,321661.",58)]
for f, _, _, n in LEAN:
    src = open(os.path.join(AK, 'lean/Antikythera', f), encoding='utf-8').read()
    assert len(re.findall(r'^\s*(?:theorem|lemma)\b', src, re.M)) == n, f
assert sum(n for *_, n in LEAN) == 193
lean_rows = "".join(f'<tr><td class="mono nw"><b>{f}</b><br><span class="count nw">{k}</span></td><td class="brk">{c}</td><td class="num mono thm">{n}</td></tr>' for f, k, c, n in LEAN)
lean_rows += '<tr><td class="mono nw"><b>Audit.lean</b></td><td class="brk">Fait échouer la construction si une déclaration dépend de <span class="mono">sorryAx</span> ou d\'un axiome autre que <span class="mono">propext</span>, <span class="mono">Classical.choice</span> et <span class="mono">Quot.sound</span>.</td><td class="num mono">—</td></tr>'
lean_rows += '<tr class="total"><td><b>Total</b></td><td>environ 2 300 lignes</td><td class="num mono thm"><b>193</b></td></tr>'
# ---------- engine: machine calibrated at J2000 vs NASA eclipses 2026-2028 ----------
EXD = os.path.join(AK, 'build/out/explainer')
rep = json.load(open(os.path.join(EXD, 'report.json'), encoding='utf-8'))
MOIS = ["janv.","févr.","mars","avr.","mai","juin","juil.","août","sept.","oct.","nov.","déc."]
def num(x, d): return f"{x:.{d}f}".replace(".", ",").replace("-", "−")
ecl = rep['eclipses_2026_2028_regle_limites']['eclipses']
assert len(ecl) == 14 and not rep['eclipses_2026_2028_regle_limites']['predictions_sans_eclipse_reelle']
erows = []
for e in ecl:
    m = re.match(r'(\d{4})-(\d\d)-(\d\d) \S+ (solaire|lunaire) (\S+) \(Saros (\d+)\)', e['reelle'])
    y, mo, d, kind, sub, saros = m.groups()
    date = f"{int(d)} {MOIS[int(mo)-1]} {y}"
    what = ("Soleil" if kind == "solaire" else "Lune") + ", " + sub
    if e['machine'].startswith('NON'):
        res = f'<span class="miss">non prédite</span><br><span class="count">Lune à {num(e["distance_noeud_machine_deg"],1)}° du nœud</span>'
    else:
        h = e['ecart_heures']
        res = ("+" if h > 0 else "") + num(h, 2) + " h"
    erows.append(f'<tr><td class="nw">{date}</td><td>{what}<br><span class="count">Saros {saros}</span></td><td class="num mono">{res}</td></tr>')
ecl_rows = "".join(erows)
dr = rep['derive_par_siecle']
assert abs(dr['lune_longitude_moyenne']['derive_deg_par_siecle'] - 5.5544) < 1e-3 and dr['_resume']['phases_de_la_lune_avance_jours_par_siecle'] == 0.456
# ---------- computed eclipse glyphs vs the historical dial ----------
gl = json.load(open(os.path.join(EXD, 'glyphs.json'), encoding='utf-8'))
def gcount(cells):
    return (sum(1 for c in cells if c['lunaire'] or c['solaire']), sum(1 for c in cells if c['lunaire']),
            sum(1 for c in cells if c['solaire']), sum(1 for c in cells if c['lunaire'] and c['solaire']))
GL = [("Cadran historique (reconstruction de Freeth 2014)", gcount(gl['historique_EYM_Freeth2014']['cells']), (51,38,28,15)),
      ("Notre modèle non calé, limites physiques (Lune 10,8°, Soleil 17,0°)", gcount(gl['modele_epoque_t0']['limits']['cells']), (55,28,42,15)),
      ("Notre modèle non calé, règle de Freeth 2014", gcount(gl['modele_epoque_t0']['freeth2014']['cells']), (52,38,26,12))]
for name, got, want in GL: assert got == want, (name, got)
glyph_rows = "".join(f'<tr><td>{n}</td>' + "".join(f'<td class="num mono">{v}</td>' for v in c) + '</tr>' for n, c, _ in GL)
gj = json.dumps([dict(n=g[0], z=g[1], m=g[2], axis=g[3], st=g[4], role=g[5]) for g in GEARS], ensure_ascii=False)
t = open('template.html', encoding='utf-8').read()
rear = figs.rear().replace('class="plan"', 'class="plan tall"')
b1 = figs.front_b1().replace('class="plan"', 'class="plan sq"')
cp = figs.front_cp().replace('class="plan"', 'class="plan sq"')
for k,v in {"{{SVG_REAR}}":rear,"{{SVG_B1}}":b1,"{{SVG_CP}}":cp,"{{SVG_TREE}}":figs.tree(),"{{TRAIN_ROWS}}":"".join(rows),
            "{{MODULE_ROWS}}":mrows,"{{SOURCES}}":srcs,"{{GEARS_JSON}}":gj,"{{LEAN_ROWS}}":lean_rows,
            "{{ECLIPSE_ROWS}}":ecl_rows,"{{GLYPH_ROWS}}":glyph_rows}.items():
    assert k in t, k
    t = t.replace(k, v)
import base64, shutil
# every {{IMG_name}} placeholder is replaced by name.jpg (film stills and diagram: see prep_images.py)
for n in sorted(set(re.findall(r'\{\{IMG_(\w+)\}\}', t))):
    t = t.replace('{{IMG_%s}}' % n, 'data:image/jpeg;base64,' + base64.b64encode(open(n + '.jpg', 'rb').read()).decode())
assert '{{' not in t, re.findall(r'\{\{\w+\}\}', t)
# French typography in text nodes only (not in <script>, <style>, <pre> or <svg>, nor in attributes):
# no line break after « or before », : ; ? !, nor inside a number such as 4 009
NB = '\u00a0'
def fr_text(s):
    s = re.sub(r'« ', '«' + NB, s)
    s = re.sub(r' ([»:;?!])', NB + r'\1', s)
    s = re.sub(r'(?<=\d) (?=\d{3}\b)', NB, s)
    s = re.sub(r'(?<=\d) (?=(?:min|s|h|mm|rad|Ko|LUFS|i/s|%)(?!\w))', NB, s)   # 2 min 40 s, 89 minutes stays free
    return re.sub(r'(?<=\bmin) (?=\d)', NB, s)
def fr_typo(page):
    parts = re.split(r'(<(script|style|pre|svg)\b.*?</\2>)', page, flags=re.S)
    out = []
    for i, p in enumerate(parts):
        if i % 3 == 2: continue            # the captured tag name
        if i % 3 == 1: out.append(p); continue
        out.append(re.sub(r'>([^<]+)<', lambda m: '>' + fr_text(m.group(1)) + '<', p))
    return ''.join(out)
t = fr_typo(t)
out = os.path.join(AK, 'dossier.html')
open(out, 'w', encoding='utf-8').write(t)
shutil.copyfile(out, os.path.join(AK, 'docs/dossier.html'))
print("written", len(t), "chars,", os.path.getsize(out), "bytes; copied to docs/dossier.html")
