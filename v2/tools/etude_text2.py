"""Seconde moitié du texte de study/etude.html."""

BODIES = [("Y", "Soleil (roue de l'année)"), ("mercury_L", "Mercure"), ("venus_L", "Vénus"), ("mars_L", "Mars"),
          ("jupiter_L", "Jupiter"), ("saturn_L", "Saturne"), ("uranus_L", "Uranus"), ("neptune_L", "Neptune"),
          ("moon_L", "Lune, longitude moyenne"), ("moon_D", "Lune, élongation D"), ("moon_F", "Lune, latitude F"),
          ("moon_Mp", "Lune, anomalie M′")]


def rest(A, T, C, review, figure, table, fr, repo, verdict):
    v, m, w, b = A["verifications"], A["masse"], A["roues"], A["budget_erreur"]
    ev, inv = T["evaluation"], T["inventory"]
    cal, ecl, moon = C["calendar_time"], C["eclipses"], C["moon"]
    eot = cal["equation_of_time"]
    det = ecl["detection"]
    hits = det["new"]["hits"] + det["full"]["hits"]
    n_ecl = ecl["new"]["n"] + ecl["full"]["n"]
    geo = {r["sortie"].split(" (")[0]: r for r in b["planetes"]}
    P = ["""<h2><span class="n">04</span>Huit mécanismes qui font la différence</h2><div class="mech">"""]
    mech = [
        ("Kepler pour chaque planète",
         "Une planète va plus vite près du Soleil. Six corps utilisent un <b>équant bissecté</b> : une goupille dans une "
         "rainure, décalée de quelques dixièmes de millimètre. Mars ajoute un minuscule <b>épicyclet</b>. Mercure, très "
         "excentrique, a un <b>résolveur</b> qui résout mécaniquement M = E − e sin E.",
         f"géométrie seule : {fr(geo['Neptune']['geometrie_deg'])}° (Neptune) à {fr(geo['Mercure']['geometrie_deg'])}° (Mercure)"),
        ("Le module vectoriel",
         "Pour passer du Soleil à la Terre, chaque tour contient un petit orrery à deux bras, à l'échelle exacte. Un "
         "suiveur rainuré vise de la Terre vers la planète : sa direction est la longitude géocentrique. La goupille "
         "dessine même la boucle de rétrogradation.",
         "pivot du suiveur en O = P₁ + s·(C_T − C_p)"),
        ("Une Lune moderne",
         "Cinq étages en cascade ajoutent, l'un après l'autre : la réduction à l'écliptique, l'équation annuelle, "
         "l'évection, l'anomalie et la variation. Schwilgué avait mécanisé ces termes à Strasbourg en 1842 ; ici, chacun "
         "a son amplitude chiffrée.",
         f"{fr(b['lune_deg']['max'])}° max, {fr(b['lune_deg']['rms'])}° rms"),
        ("Le calendrier grégorien",
         "Un anneau de 366 dates avance d'un cran par jour par une croix de Malte. Les années communes, une seconde croix "
         "saute le 29 février. Trois cames (4, 100 et 400 ans) décident. Tout dépend de la position : la machine peut "
         "tourner à l'envers sans perdre le calendrier.",
         f"juste chaque année de {cal['gregorian']['years_checked'].replace('-', ' à ')}"),
        ("Le temps sidéral et l'équation du temps",
         "Un différentiel ajoute le jour et le Soleil moyen : c'est le temps sidéral. Un <b>joint de Hooke</b> incliné de "
         "23,44° fait exactement tan α = cos ε · tan λ. C'est la réduction à l'équateur, que Hooke avait lui-même "
         "remarquée.",
         f"sidéral {fr(b['sideral_s_par_siecle'], 3)} s/siècle ; EdT {fr(eot['hooke_with_precession_input_max_err_s'], 1)} s "
         f"(came : {fr(eot['fixed_cam_2050_max_err_s'], 1)} s)"),
        ("Les éclipses par la géométrie",
         "Une coulisse sur le porte-nœuds est menée par la goupille même de l'unité d'anomalie de la Lune. Sa course vaut "
         "r·sin F, proportionnelle à γ, la distance de l'ombre au centre de la Terre. Sur le couvercle, une aiguille "
         "d'ombre montre le lieu de l'éclipse.",
         f"{hits}/{n_ecl} éclipses ; lieu à {fr(ecl['new']['where_lat_err_deg_rms'], 1)}° rms en latitude"),
        ("Le zodiaque qui recule",
         "La machine calcule dans le repère fixe des étoiles : les pivots de Kepler restent ainsi fixes dans la caisse. "
         "Un train très lent, pris sur le train moyen de Neptune, fait reculer l'anneau du zodiaque tropique. C'est la "
         "précession des équinoxes : Olsen et Schwilgué l'avaient aussi.",
         f"un tour en {cal['precession']['period_tropical_years']:,.0f} années tropiques".replace(",", "\u202f")),
        ("Les lunes de Jupiter",
         "Une <b>boîte de Laplace</b> construit Europe = 2·Ganymède + ν et Io = 2·Europe + ν avec deux doubleurs et deux "
         "différentiels. La résonance 1:2:4 est exacte par construction. Une « lunette » montre les lunes à l'est ou à "
         "l'ouest de Jupiter, comme aux jumelles.",
         "relation de Laplace exacte"),
    ]
    for t, txt, acc in mech:
        P.append(f'<section><h3>{t}</h3><p>{txt}</p><p class="acc">{acc}</p></section>')
    P.append("</div>")
    P.append(f"""<h2><span class="n">05</span>Les engrenages</h2>
<p>Les rapports viennent des périodes modernes (JPL, IAU). Ils ont été cherchés exhaustivement et vérifiés en
<b>fractions exactes</b> :</p>
<ul class="tight"><li>{inv['designed_pairs']} couples approchés et {inv['exact_pairs']} couples exacts ;</li>
<li>{inv['differentials']} différentiels et {inv['steppers']} mécanismes pas à pas ;</li>
<li>toutes les dentures entre 10 et 220 ;</li>
<li><b>les 65 vérifications</b> de <code>trains.py</code> passent.</li></ul>
<p>Résultat : <b>les engrenages ne limitent nulle part la précision</b>. Leur dérive reste 100 à 1 000 fois sous les
objectifs ; ce sont la géométrie et la physique qui fixent la limite.</p>""")
    rows = [[name, fr(ev[k]["deg_per_century"], 4) + "°"] for k, name in BODIES if k in ev]
    P.append(table(["Sortie", "Dérive due aux engrenages (par siècle)"], rows, num=(1,)))
    P.append(f"""<h2><span class="n">06</span>L'architecture</h2>
<p>La machine tient dans une caisse de <b>{m['box_mm'][0]} × {m['box_mm'][1]} × {m['box_mm'][2]} mm</b>, avec l'orrery
sur le couvercle. Elle pèse environ <b>{fr(m['total_kg'], 1)} kg</b> en laiton, {fr(m['total_kg_alu_inner'], 1)} kg avec
des platines intérieures en aluminium : c'est la classe de l'éclipsarium de Rømer (27 kg).</p>
<p>Cinq étages se suivent de l'arrière vers l'avant :</p>
<ul class="tight"><li>le temps, le calendrier et la Lune ;</li><li>les trains moyens ;</li><li>les unités de Kepler ;</li>
<li>les modules géocentriques ;</li><li>les renvois vers la pile de tubes du grand cadran.</li></ul>""")
    P.append(figure("fig_coupe.svg", "<b>Coupe schématique</b> (plan x ≈ 0, l'arrière à gauche). Cinq étages entre les deux cadrans. L'axe central porte "
                    "l'année Y, la Terre maîtresse puis l'aiguille du Soleil. Une tour planétaire, ici celle de Mars, "
                    "empile son train, son unité de Kepler et son module.", "narrow"))
    P.append(figure("fig_etages.svg", f"<b>Les cinq étages, tels que le vérificateur les a placés.</b> "
                    f"{v['trains_places']} trains posés roue par roue par recherche exhaustive, avec leurs pignons fous, "
                    f"leurs reprises 1:1 et leurs tringles. {v['objets']} pièces, {len(v['collisions'])} collision."))
    P.append(table(["Contrôle", "Résultat"], [
        ["Pièces modélisées (roues, arbres, couronnes, tringles, avec leur cote z)", v["objets"]],
        ["Trains placés roue par roue", f"{v['trains_places']} (échecs : {len(v['echecs_placement'])})"],
        ["Collisions", f"<b>{len(v['collisions'])}</b>"],
        ["Arbres de <code>trains.json</code> qui ont une place", f"<b>{v['couverture']['assigned']} / {v['couverture']['n_shafts']}</b>"],
        ["Interfaces déclarées (pièces qui entrent dans un bloc)", len(v["interfaces"])],
        ["Cadrans dans leur face, sans chevauchement", "oui" if v["faces"]["ok"] else "non"],
        ["Roues dentées (trains + renvois)", f"≈ {w['total']}"]], num=(1,)))
    P.append("""<h2><span class="n">07</span>Budget d'erreur (2000–2100)</h2>
<p>La précision d'une aiguille dépend de trois choses :</p>
<ul class="tight"><li>la <b>géométrie</b> du modèle : forme de l'orbite, inclinaison, lente dérive des orbites ;</li>
<li>la <b>physique</b> que Kepler ignore : les planètes s'attirent entre elles ;</li>
<li>la <b>fabrication</b> : une tolérance de 0,02 mm.</li></ul>""")
    P.append(table(["Aiguille", "Géométrie", "Physique hors Kepler", "Tolérance 0,02 mm"],
                   [[k, fr(r["geometrie_deg"]) + "°", r["physique_hors_kepler"].replace(".", ","),
                     fr(r["tolerance_0_02mm_deg"]) + "°"] for k, r in geo.items()], num=(1, 2, 3)))
    P.append(f"""<ul class="tight"><li><b>Lune</b> : {fr(b['lune_deg']['max'])}° au maximum.</li>
<li><b>Calendrier</b> : {b['calendrier']}.</li>
<li><b>Temps sidéral</b> : {fr(b['sideral_s_par_siecle'], 3)} s par siècle.</li>
<li><b>Équation du temps</b> : {fr(b['equation_du_temps_s'], 1)} s au plus.</li>
<li><b>Éclipses</b> : {hits} sur {n_ecl}, erreur sur γ d'au plus {fr(b['eclipses']['gamma_err_max'], 3)}.</li></ul>""")
    import os
    from etude_text3 import tail
    r2 = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "study", "review2.md")
    review2 = open(r2).read() if os.path.exists(r2) else None
    r3 = r2.replace("review2", "review3")
    review3 = open(r3).read() if os.path.exists(r3) else None
    return P + tail(A, review, verdict, repo, fr, review2, review3)
