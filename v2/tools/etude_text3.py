"""Fin de study/etude.html : limites, revue, fichiers, pied de page."""


def tail(A, review, verdict, repo, fr, review2=None, review3=None):
    import os
    j = A["jeu"]
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    video = ('<figure><video src="img/annee.mp4" controls muted loop playsinline preload="metadata" '
             'poster="img/front34.jpg"></video><figcaption><b>Une année en 15 secondes</b> (2026, un jour toutes les '
             'deux images) : les aiguilles, l\'orrery et les cadrans tournent aux vitesses exactes.</figcaption></figure>'
             if os.path.exists(os.path.join(here, "study", "img", "annee.mp4")) else "")
    P = [f"""<h2><span class="n">08</span>Ce qui n'est pas encore prouvé</h2>
<ul class="tight">
<li><b>Les blocs-mécanismes sont des enveloppes estimées.</b> C'est le cas de la cascade lunaire, du calendrier, du
bloc du temps, de la boîte de Laplace et des unités de Kepler. Leur intérieur sera dessiné pièce par pièce en 3D.</li>
<li><b>Le jeu des engrenages.</b> Les renvois en aval d'un suiveur laissent environ {fr(j['aval_suiveur_deg'])}° de
flottement, chaque fois qu'une sortie change de sens : une planète qui rétrograde, l'équation du temps, la coulisse
d'éclipse. Des roues anti-jeu à ciseaux sont donc prévues sur toute cette chaîne.</li>
<li><b>La dynamique n'est pas calculée</b> : efforts, frottements, flexion des tringles. L'effort de manivelle se
mesurera sur prototype.</li>
<li><b>Les pièces les plus fines.</b> L'épicyclet de Mars mesure 0,087 mm : il faut une bague excentrique réglable ou
l'électroérosion.</li>
<li><b>Les phénomènes hors de portée</b> : la bande de centralité d'une éclipse, l'écart ΔT entre temps terrestre et
rotation de la Terre, les grandes inégalités de Jupiter et Saturne au-delà de quelques siècles.</li>
</ul>"""]
    vd = verdict(review)
    if vd:
        P.append(f"""<h3>Deux revues adversariales</h3>
<p>Une première revue indépendante a relu la version 1 de l'architecture. Son verdict :</p>{vd}
<p><b>La version 2 a répondu point par point :</b></p>
<ul class="tight">
<li>Le bus de l'année arrive sur l'axe de chaque tour.</li>
<li>Le bloc du temps et celui de la Lune reçoivent toutes leurs entrées.</li>
<li>Le bloc du temps ramène la précession au bon rapport.</li>
<li>Chaque roue est dans son plan et chaque arbre va de la platine au pont.</li>
<li>Les pignons des moyeux et les roues du carrousel sont modélisés.</li>
<li>Les sens de rotation et le jeu sont traités.</li>
</ul>
<p>Résultat : {A['verifications']['objets']} pièces, {len(A['verifications']['collisions'])} collision. Le détail
est au § 1 de <a href="{repo}/blob/main/v2/study/architecture.md">architecture.md</a>.</p>
<p><a href="{repo}/blob/main/v2/study/review.md">Lire la première revue</a>.</p>""")
        if review2:
            P.append(f"""<p>Une seconde revue a vérifié ces corrections. Son verdict :</p>{verdict(review2)}
<p><b>La version 3 a répondu à son tour :</b></p>
<ul class="tight">
<li>Les reprises de Y passent par un pignon fou sur tenon, qui garde le sens de chaque planète.</li>
<li>Le bloc Lune a ses couples d'entrée 1:1.</li>
<li>L'arbre de précession descend vraiment dans le bloc du temps, porté par un coq.</li>
<li>La roue du suiveur F tourne sur sa bague excentrique, avec une prise à 23 mm.</li>
<li>Chaque bloc a un budget de hauteur vérifié.</li>
<li>Les liens se font par identifiant exact.</li>
</ul>
<p>Un contrôle strict ne trouve plus aucun recouvrement caché. Ce sont le § 1.2 et le § 6 de
<a href="{repo}/blob/main/v2/study/architecture.md">architecture.md</a>.</p>
<p><a href="{repo}/blob/main/v2/study/review2.md">Lire la seconde revue</a>.</p>""")
        if review3:
            P.append(f"""<p>Une troisième revue a vérifié la version 3. Son verdict :</p>{verdict(review3)}
<p><b>La version 4 règle ces deux points.</b></p>
<ul class="tight">
<li>Les entrées du bloc Lune (40 → pignon fou → 40) sont modélisées et placées.</li>
<li>Les budgets de hauteur des blocs sont complets.</li>
<li>L'arbre de précession est relié.</li>
</ul>
<p><a href="{repo}/blob/main/v2/study/review3.md">Lire la troisième revue</a>.</p>""")
    P.append(f"""<h2><span class="n">09</span>La machine en 3D</h2>
<p>La maquette Blender suit l'architecture vérifiée, pièce par pièce :</p>
<ul class="tight">
<li>415 pièces de mécanique, dont 153 roues droites à dents vraies (développante de 30°, jeu de 0,03 mm),
72 coniques, 19 couronnes, 40 tringles et 6 platines percées ;</li>
<li>28 blocs translucides et étiquetés pour les mécanismes encore à dessiner ;</li>
<li>les trois faces, la caisse et la manivelle.</li></ul>
<p><b>Contrôle d'interférence</b> : 133 contacts d'engrenage, chacun vérifié à 24 instants d'un tour, sans aucun
recouvrement ; 183 paires de pièces voisines, sans collision. Chaque pièce tourne au taux exact de
<code>trains.json</code> ; les aiguilles suivent des éphémérides à moins de 0,4° de JPL Horizons sur 2000–2100.</p>
<div class="shots">
<figure><img src="img/front.jpg" alt="Face avant de la maquette : grand cadran du ciel, dix aiguilles, quatre petits cadrans" loading="lazy"><figcaption><b>Face avant</b>, le 4 octobre 2026.</figcaption></figure>
<figure><img src="img/back.jpg" alt="Face arrière : cadran des éclipses, calendrier grégorien, Saros" loading="lazy"><figcaption><b>Face arrière</b>, vue de dos.</figcaption></figure>
<figure><img src="img/front34.jpg" alt="Vue de trois quarts : la caisse et l'orrery sur le couvercle" loading="lazy"><figcaption><b>Trois quarts</b> : l'orrery sur le couvercle.</figcaption></figure>
<figure><img src="img/lid.jpg" alt="Le couvercle vu d'en haut : orbites et planètes" loading="lazy"><figcaption><b>Le couvercle</b>, vu d'en haut.</figcaption></figure>
</div>
<figure><img src="img/etages.jpg" alt="Les cinq étages vus de face, puis l'intérieur sans la caisse" loading="lazy"><figcaption><b>Les cinq
étages</b> (E5 à E1), vus de face, puis l'intérieur sans la caisse ni les cadrans avant. Les blocs translucides sont
les mécanismes encore à dessiner.</figcaption></figure>
{video}
<p><b>Preuves Lean 4</b> : 201 théorèmes générés depuis <code>trains.json</code> et <code>architecture.json</code>
(rapports, vitesses, identités, architecture), compilés sans avertissement et audités : ils ne reposent que sur les
trois axiomes standard. Voir <a href="{repo}/blob/main/v2/blender/README.md">la maquette et les preuves</a>.</p>""".replace("{video}", video))
    files = [("research/mechanisms.md", "la meilleure réalisation de chaque sous-système, chiffrée"),
             ("research/precedents.md", "les machines qui l'ont déjà fait : Strasbourg, Olsen, Hahn…"),
             ("research/constants.md", "les constantes modernes et leurs sources"),
             ("spec/trains.json", "les 70 arbres et leurs rapports exacts"),
             ("study/trains.md", "l'étude des trains d'engrenages"),
             ("spec/architecture.json", "l'architecture vérifiée (positions, étages, renvois)"),
             ("study/architecture.md", "l'architecture expliquée"),
             ("blender/README.md", "la maquette 3D, ses contrôles et les preuves Lean"),
             ("lean/", "les 201 théorèmes Lean 4 de la v2"),
             ("tools/", "les scripts qui produisent et vérifient tout")]
    lis = "".join(f'<li><a href="{repo}/blob/main/v2/{p}"><code>v2/{p}</code></a> : {d}</li>' for p, d in files)
    P.append(f"""<h2><span class="n">10</span>Les fichiers</h2><ul class="tight">{lis}</ul>
<h2><span class="n">11</span>La suite</h2>
<ol class="tight"><li><b>Dessiner l'intérieur des blocs</b> pièce par pièce : unités de Kepler, modules vectoriels,
cascade de la Lune, bloc du temps, calendrier, boîte de Laplace.</li>
<li><b>Prolonger les preuves Lean</b> aux mécanismes non linéaires (identité du module vectoriel, joint de Hooke).</li>
<li><b>Un prototype</b>, pour mesurer l'effort de manivelle et le jeu réel.</li></ol>
<footer>Page générée par <code>v2/tools/build_etude.py</code> à partir des fichiers vérifiés du dépôt.
Anticythère 2.0 est une évolution moderne, pas une reconstruction historique. ·
<a href="{repo}">github.com/taciclei/antikythera-mechanism</a></footer>""")
    return P
