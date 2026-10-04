"""Fin de study/etude.html : limites, revue, fichiers, pied de page."""


def tail(A, review, verdict, repo, fr, review2=None, review3=None):
    j = A["jeu"]
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
    files = [("research/mechanisms.md", "la meilleure réalisation de chaque sous-système, chiffrée"),
             ("research/precedents.md", "les machines qui l'ont déjà fait : Strasbourg, Olsen, Hahn…"),
             ("research/constants.md", "les constantes modernes et leurs sources"),
             ("spec/trains.json", "les 70 arbres et leurs rapports exacts"),
             ("study/trains.md", "l'étude des trains d'engrenages"),
             ("spec/architecture.json", "l'architecture vérifiée (positions, étages, renvois)"),
             ("study/architecture.md", "l'architecture expliquée"),
             ("tools/", "les scripts qui produisent et vérifient tout")]
    lis = "".join(f'<li><a href="{repo}/blob/main/v2/{p}"><code>v2/{p}</code></a> : {d}</li>' for p, d in files)
    P.append(f"""<h2><span class="n">09</span>Les fichiers</h2><ul class="tight">{lis}</ul>
<h2><span class="n">10</span>La suite</h2>
<ol class="tight"><li><b>La machine en 3D</b> dans Blender, à partir de <code>spec/architecture.json</code>, avec un contrôle
d'interférence pièce par pièce, comme pour la v1.</li>
<li><b>Les preuves Lean 4</b> des rapports exacts et des identités : Laplace, Hooke, calendrier.</li></ol>
<footer>Page générée par <code>v2/tools/build_etude.py</code> à partir des fichiers vérifiés du dépôt.
Anticythère 2.0 est une évolution moderne, pas une reconstruction historique. ·
<a href="{repo}">github.com/taciclei/antikythera-mechanism</a></footer>""")
    return P
