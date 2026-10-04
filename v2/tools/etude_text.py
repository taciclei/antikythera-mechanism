"""Texte de study/etude.html (français). Les chiffres viennent des fichiers passés en argument."""
import html
import re


def _review_verdict(md):
    if not md:
        return None
    m = re.search(r"^## Verdict\s*\n(.*?)(?=^## )", md, re.S | re.M)
    if not m:
        return None
    paras = [p.strip() for p in m.group(1).strip().split("\n\n") if p.strip()]
    out = []
    for p in paras:
        t = html.escape(p.replace("\n", " "))
        t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
        t = re.sub(r"`(.+?)`", r"<code>\1</code>", t)
        out.append(f"<p>{t}</p>")
    return "".join(out)


def body(A, T, C, review, figure, table, fr, repo):
    v, m, w, b = A["verifications"], A["masse"], A["roues"], A["budget_erreur"]
    ev, inv = T["evaluation"], T["inventory"]
    cal, ecl, moon = C["calendar_time"], C["eclipses"], C["moon"]
    box = m["box_mm"]
    lu = b["lune_deg"]
    det = ecl["detection"]
    hits = det["new"]["hits"] + det["full"]["hits"]
    n_ecl = ecl["new"]["n"] + ecl["full"]["n"]
    years = cal["gregorian"]["years_checked"].replace("-", "–")
    hipp = moon["moon_errors"]["antikythera_pinslot_anomaly"]["max_deg"]
    P = []
    P.append(f"""<header class="title">
<p class="kicker">Étude de conception · v2 · octobre 2026</p>
<h1>Anticythère 2.0</h1>
<p class="lede">Et si l'on refaisait la machine d'Anticythère avec l'astronomie d'aujourd'hui ? Huit planètes sur des
orbites de Kepler, une Lune moderne, le calendrier grégorien, les éclipses et les lunes de Jupiter. Le tout tient dans
une boîte qu'on fait tourner à la manivelle.</p>
<p class="warn"><strong>Ce n'est pas une reconstruction historique.</strong> C'est une évolution moderne, dans l'esprit
de la machine antique. La reconstruction historique (la « v1 ») reste à la racine du
<a href="{repo}">dépôt</a>, figée au repère <a href="{repo}/releases/tag/v1-historique">v1-historique</a>.</p>
</header>
<div class="figs">
<div><b>8</b><span>planètes sur des orbites de Kepler</span></div>
<div><b>{fr(lu['max'])}°</b><span>erreur max. de la Lune (v1 : {fr(hipp, 1)}°)</span></div>
<div><b>{years}</b><span>calendrier grégorien juste chaque année</span></div>
<div><b>{hits}/{n_ecl}</b><span>éclipses NASA 2001–2100 retrouvées</span></div>
<div><b>≈ {w['total']}</b><span>roues dentées</span></div>
<div><b>{fr(m['total_kg'], 1)} kg</b><span>caisse de {box[0]} × {box[1]} × {box[2]} mm</span></div>
</div>""")
    P.append("""<h2><span class="n">01</span>Ce qui change</h2>""")
    P.append(table(["", "Machine antique (v1)", "Anticythère 2.0"], [
        ["Planètes", "5, sur des cercles", "<b>8</b>, sur des orbites <b>képlériennes</b>"],
        ["Lune", "anomalie d'Hipparque", "anomalie, <b>évection</b>, <b>variation</b>, équation annuelle"],
        ["Rapports", "relations babyloniennes", "<b>périodes modernes</b>, moins de 0,01° de dérive par siècle"],
        ["Calendrier", "égyptien de 365 jours, Méton", "<b>grégorien</b> (4/100/400), jour de la semaine"],
        ["Temps", "—", "<b>heure sidérale</b>, <b>équation du temps</b>, <b>précession</b>"],
        ["Éclipses", "spirale du Saros, glyphes", "géométrie : <b>γ</b>, magnitude, totale ou annulaire, <b>lieu</b> sur un globe"],
        ["Affichage", "le ciel vu de la Terre", "le ciel vu de la Terre <b>et</b> le système solaire vu d'en haut"],
        ["En plus", "—", "les <b>lunes de Jupiter</b> (résonance de Laplace)"]]))
    P.append("""<h2><span class="n">02</span>Comment le mouvement circule</h2>
<p>Tout part d'un seul arbre : <b>l'arbre-jour J</b>, qui fait un tour par jour solaire moyen. Le calendrier grégorien
l'impose. Ses cycles (146 097 jours en 400 ans) contiennent le nombre premier 773, impossible à tailler en
engrenage : on ne peut que <b>compter des jours</b>.</p>
<p>J mène l'<b>arbre de l'année Y</b>. Deux « bus » de tringles, comme les renvois qui mènent les quatre cadrans d'une
horloge de clocher, distribuent J et Y. Chaque planète a sa <b>tour</b>, qui empile trois étages :</p>
<ul class="tight"><li>son train d'engrenages moyen ;</li><li>son unité de Kepler ;</li><li>son module géocentrique.</li></ul>""")
    P.append(figure("fig_blocs.svg", "<b>Circulation du mouvement.</b> La manivelle mène J, qui mène Y. J et Y alimentent "
                    "les blocs de calcul. Trois collecteurs portent leurs sorties vers les trois faces : chaque point "
                    "noir est une liaison."))
    P.append("""<h2><span class="n">03</span>Les trois faces</h2>
<div class="two"><div><h3>Devant : le ciel vu de la Terre</h3><ul class="tight">
<li>dix aiguilles sur l'écliptique : le Soleil, la Lune avec sa boule de phase, les sept planètes et le Dragon, qui montre les nœuds de la Lune ;</li>
<li>un anneau fixe des constellations ;</li>
<li>un anneau tropique qui recule d'un tour en 25 772 ans : c'est la précession. Il porte aussi les mois grégoriens ;</li>
<li>quatre petits cadrans : l'horloge 24 h (temps moyen et sidéral), l'équation du temps, Jupiter et ses lunes, la plaque d'époque.</li></ul></div>
<div><h3>Derrière : le temps</h3><ul class="tight">
<li>le calendrier grégorien : un anneau de 366 dates, le jour de la semaine, les années ;</li>
<li>le cadran des éclipses : le Soleil, la Lune et le disque des nœuds gradué en γ ;</li>
<li>le Saros, qui annonce le retour d'une éclipse, et l'Exeligmos ;</li>
<li>une plaque « mode d'emploi ».</li></ul></div></div>""")
    P.append(figure("fig_faces.svg", "<b>Les deux faces à l'échelle</b> (450 × 340 mm). La face arrière est dessinée "
                    "vue de dos. Les aiguilles du grand cadran sont schématiques."))
    P.append("""<h3>Dessus : le système solaire vu d'en haut</h3>
<p>L'orrery du couvercle est mené par <b>les mêmes arbres</b> que les aiguilles de devant. Les deux affichages sont donc
toujours d'accord.</p>
<ul class="tight"><li>Les rayons sont comprimés, mais les angles sont exacts.</li>
<li>Chaque planète glisse dans une rainure fixe : l'ellipse de Mercure se voit.</li>
<li>La Terre est un globe incliné qui tourne en un jour sidéral.</li>
<li>Une <b>aiguille d'ombre</b> touche le globe à l'endroit où l'éclipse sera la plus forte.</li></ul>""")
    P.append(figure("fig_couvercle.svg", "<b>Le couvercle vu d'en haut, à l'échelle.</b> Le cercle pointillé centré sur le "
                    "Soleil fait voir le décalage de l'ellipse de Mercure (e = 0,21). Les petits ronds violets marquent "
                    "l'arrivée des dix tringles qui montent de l'intérieur."))
    return P + mechanisms(A, T, C, review, figure, table, fr, repo)


def mechanisms(A, T, C, review, figure, table, fr, repo):
    from etude_text2 import rest
    return rest(A, T, C, review, figure, table, fr, repo, _review_verdict)
