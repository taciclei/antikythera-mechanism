"""Écrit study/architecture.md (version 2) à partir de la sortie vérifiée d'architecture.py."""
import json
import os

import arch_faces as F
import arch_layout as L

HERE = os.path.dirname(os.path.abspath(__file__))
V2 = os.path.dirname(HERE)
UAK_FR = {"kes": "résolveur de Kepler + ellipse à deux bras", "eq": "équant bissecté", "eqe": "équant + épicyclet"}


def f1(x):
    return f"{x:.1f}".replace(".", ",").replace("-", "−")


def f0(x):
    return f"{x:.0f}".replace("-", "−")


def xy(c):
    return f"({f0(c[0])} ; {f0(c[1])})"


def table(head, rows):
    out = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


def stages_txt(st):
    return " · ".join(f"{a}:{b}" for a, b in st)


def write(out):
    import arch_doc2
    with open(os.path.join(V2, "spec", "trains.json")) as f:
        S = {s["id"]: s for s in json.load(f)["shafts"]}
    P = part1(out) + arch_doc2.part2(out, S)
    path = os.path.join(V2, "study", "architecture.md")
    with open(path, "w") as f:
        f.write("\n".join(P).rstrip() + "\n")
    print("écrit", os.path.relpath(path, V2))


def part1(out):
    c, m, w = out["verifications"], out["masse"], out["roues"]
    box = m["box_mm"]
    P = [f"""# Anticythère 2.0 — Architecture de la machine

> ⚠️ **Ce n'est pas une reconstruction historique.** C'est l'architecture d'une machine moderne, dans l'esprit
> d'Anticythère : une boîte, une manivelle, des cadrans. La v1 historique reste à la racine du dépôt.

Ce document dit **où va chaque pièce** et **comment les mouvements circulent** dans la machine. Il est produit par
`v2/tools/architecture.py`. Le script lit `spec/trains.json` et `research/calc/`, place les trains d'engrenages roue
par roue, puis vérifie qu'aucune pièce n'en heurte une autre. Les choix de conception sont dans `tools/arch_layout.py`,
`arch_routes.py` et `arch_faces.py` ; le résultat complet est dans `spec/architecture.json`.

**Version 4.** L'architecture a été relue trois fois par des revues adversariales indépendantes :
- `study/review.md` sur la version 1 ;
- `study/review2.md` sur la version 2 ;
- `study/review3.md` sur la version 3.

Chaque défaut trouvé a été corrigé ; le § 1 dit lesquels et comment.

## 0. L'essentiel

- **Une caisse de {box[0]} × {box[1]} × {box[2]} mm** (largeur × hauteur × profondeur), plus l'orrery d'environ
  70 mm sur le couvercle. Masse estimée : **{f1(m['total_kg'])} kg** en laiton, **{f1(m['total_kg_alu_inner'])} kg**
  avec des platines intérieures en aluminium.
- **Trois faces** : devant le ciel vu de la Terre, derrière le calendrier et les éclipses, dessus le système solaire.
- **Cinq étages**, sept **tours planétaires** et un **bloc de la Lune**.
- **Environ {w['total']} roues dentées**, détaillées au § 7.
- **Vérifié** :
  - {c['objets']} pièces modélisées en 3D (cylindres et tringles, avec leur cote z) ;
  - **{len(c['collisions'])} collision** ;
  - {c['trains_places']} trains placés roue par roue ;
  - les {c['couverture']['n_shafts']} arbres de `trains.json` ont tous une place ({c['couverture']['placed_wheel_level']}
    d'entre eux roue par roue, les autres dans des blocs) ;
  - faces et couvercle conformes.
""",
         """## 1. Ce qui a changé après les revues

### 1.1 Première revue (version 1 → version 2)

| Défaut relevé (`review.md`) | Réponse de la version 2 |
|---|---|
| B1 · les copies de l'UAK Terre n'avaient pas d'entrée Y | Le bus arrive **sur l'axe** de la tour, sur un tube Y. Un couple 1:1 (ou un couple à pignon fou) reprend Y vers l'entrée du train. Le tube Y monte jusqu'à la copie de l'UAK Terre. |
| B2 · train J → Y : la roue de 144 traversait l'arbre Y | Ordre des couples inversé (10:83, 19:144, 31:180) ; la roue de 180 est sur Y. |
| B3 · pignons du moyeu Y4 superposés | Pignons modélisés ; deux couronnes Y4 sur deux couches (T1, T2). |
| B4 · roues du carrousel percées | Roues de 64 modélisées ; pas régulier de 40° ; tringles d'arrivée vérifiées avec le carrousel. |
| B5 · boîte de Laplace trop petite | Rayon calculé depuis les trains (r ≥ 75,1 mm, plus 4 mm) ; trois trains empilés de 10 mm. |
| I1 · mauvais arbre de précession au bloc du temps | Le bloc reçoit l'arbre de la roue de 131 et le ramène au rapport de l'anneau par son propre couple 15:179. |
| I2 · sens de rotation absent | Tableau des sens (§ 8) : chaque chaîne a un renvoi conique réglable ou un pignon fou. |
| I3 · « jeu nul en marche avant » faux | Faux en effet : onze sorties s'inversent seules. Roues anti-jeu à ciseaux exigées en aval des suiveurs (§ 9). |
| I4 · entrées manquantes (temps, Lune, bras de Lune) | Tringles J et Y vers le bloc du temps, Y vers le bloc Lune, 11ᵉ tringle (Lune) vers le couvercle. |
| I5 · arbres non prolongés | Tout arbre de train va de la platine à un pont et traverse tous les plans de son étage. |
| I6 · couches de tringles trop minces | Coniques m 0,4 (Ø 10,4 mm) et couches de 15 mm. |
| I7 · liens trop larges, interfaces cachées | Liens pièce à pièce seulement ; interfaces listées avec leur profondeur (§ 6). |
| I8 · prise héliocentrique | Couple de prise vers un arbre décalé, puis conique ; palier excentrique du suiveur F décrit (§ 10). |
| I9 · roues oubliées | Les 71 roues internes sont comptées, plus tous les nouveaux renvois. |
| I10 · pignons fous non placés | Placés (Mercure, nœud), dans le couple que choisit la recherche. |
| M1–M10 | Corrigés dans le texte : pile Ø 18,4 mm, jeu recalculé, anneau tropique, couvercle, sens des cadrans arrière, masse sans options. |

Trois choix nouveaux sont apparus pendant la reprise :
- **Neptune et Uranus échangent leurs tours.** Neptune est passée au centre de la rangée du bas.
- **Le couple 10:131 de la précession** est sous la platine P4. L'arbre L de Neptune y descend.
- **Le train du périgée** est à l'étage 4. Son arbre de sortie descend dans le bloc de la Lune.

**Deux couples changent de module ; leurs rapports restent exacts :**
- Neptune, 11:147 en m 0,55 ;
- Jupiter, 10:26 en m 0,7.

Comme dans la v1, c'est la géométrie qui commande ici, pas le rapport.

### 1.2 Seconde revue (version 2 → version 3)

| Défaut relevé (`review2.md`) | Réponse de la version 3 |
|---|---|
| N1 · dans 4 tours, la reprise directe inversait le sens de la planète | Toutes les reprises passent par un **pignon fou** (24 → fou → 24), qui garde le sens. Le fou tourne sur un **tenon porté par le pont** : son arbre ne descend pas jusqu'à la roue finale, ce qui place aussi Vénus et Neptune. |
| N2 · les couples d'entrée du bloc Lune changeaient les rapports | Couples 1:1 dédiés : 100:100 (entraxe 50) pour L et Ω, 72:72 (entraxe 36) pour ϖ. |
| N3 · l'arbre de précession n'atteignait pas le bloc du temps | Coq de 2 mm sous le couple 10:131, puis le plan du couple, puis la tringle au-dessus. Un arbre descend dans le bloc, en un point libre choisi par la recherche. |
| N4 · la bague du suiveur F ne tenait pas avec la prise à 12 mm | La roue de F (46 dents, r 12) tourne sur la bague excentrique ; sa partenaire est à 23 mm. Jupiter, Saturne et Mercure prennent du côté −x. |
| N5 · la hauteur des blocs n'était pas vérifiée | Budget de plans par bloc, vérifié (§ 4). Étage 5 : deux demi-niveaux de 30 mm. Pile avant et boîte de Laplace : 51 mm. |
| N6 · `prec_avant` : tringle de 8 mm | Remplacée par un arbre droit jusqu'au pignon de l'anneau. |
| N7 · arbres de précession sans palier bas | Coq en bas de la couche T2 (N3). |
| N8 · ciseaux sur des coniques de Ø 10 | Coniques précontraintes par ressort axial. Les 9 couples 64:64 ont des ciseaux, et leurs 9 demi-roues sont comptées. |
| N9 · liens par préfixe de nom | Liens par identifiant exact. Seules les parties d'un même axe de tour répondent à son nom. Contrôle strict au § 6. |
| N10 · comptes et interfaces | Roues recomptées ; interfaces complétées (arrivée de Y au bloc Lune). |

### 1.3 Troisième revue (version 3 → version 4)

| Point relevé (`review3.md`) | Réponse de la version 4 |
|---|---|
| A · les couples d'entrée 100:100 et 72:72 du bloc Lune ne trouvaient aucun plan | Entrées L, Ω, ϖ par 40 → pignon fou → 40 (même sens, rapport 1:1), **modélisées et placées** sans collision. |
| B · le budget du bloc Lune oubliait 2 différentiels et le 30:155 | Budget complet : 26 plans (78 mm). Étage 5 : deux demi-niveaux de 39 mm. Laplace : 18 plans (54 mm), pile avant de 54 mm. |
| B · différentiels « plats » contre coniques dans `trains.json` | Choix assumé : différentiels à engrenages droits, même relation, 3 plans de haut. |
| C · rien ne liait l'arbre de précession du bloc du temps à `prec_avant` | La tringle de précession finit sur l'arbre `prec_avant`, qui monte à l'anneau et descend dans le bloc. |
| Textes, compte de la copie de l'UAK Terre du bloc du temps (2 roues), équation du temps | Corrigés ; l'équation du temps est donnée avec l'écart de la copie (§ 11). |
| Roue de prise centrée sur l'axe au lieu de F | Écart de 3,7 mm au plus ; les jeux restent ≥ 3,8 mm (§ 10.3). |

**Un autre choix nouveau : λ du bloc du temps.**
- **Le problème.** La chaîne qui prenait λ sur l'UAK maîtresse (roue, pignon fou de r 30, roue) coupait trois arbres
  du bloc du temps.
- **La solution.** Le bloc a maintenant sa propre copie de l'UAK Terre, menée par Y, comme les tours et le bloc Lune.
"""]
    P.append("## 2. Le principe : une base de temps, deux bus, des tours\n")
    P.append("""1. **La manivelle mène l'arbre-jour J** (1 tour par jour solaire moyen). Le calendrier grégorien impose ce choix.
2. **J mène l'arbre de l'année Y** par 3 couples.
3. **Des bus de tringles distribuent J et Y**, comme les renvois qui mènent les cadrans d'une horloge de clocher :
   - au départ, une couronne de 96 dents mène des pignons de 24, et la tringle tourne 4 fois plus vite ;
   - à l'arrivée, un pignon de 24 mène une couronne de 96 ;
   - le rapport net vaut **1:1 exactement**.
4. **Chaque tour planétaire** reçoit Y sur un tube, dans son axe. Elle empile trois étages :
   - le train moyen, à l'étage 4. Un pignon fou sur tenon reprend Y du tube vers l'entrée du train (24 → fou → 24, même sens), et la roue finale revient sur l'axe, comme dans la minuterie d'une horloge ;
   - l'unité de Kepler de la planète et une copie de celle de la Terre, à l'étage 3 ;
   - le module vectoriel, à l'étage 2.
5. **Vers l'avant**, chaque sortie rejoint la pile de tubes du grand cadran par une tringle et un **carrousel** de neuf arbres, à 40° d'intervalle sur un cercle de 32 mm.
""")
    P.append("## 3. Les trois faces\n\n### 3.1 Face avant : le ciel vu de la Terre\n")
    P.append(table(["Cadran", "Centre (mm)", "Rayon", "Ce qu'il montre"],
                   [[d["titre"], xy(d["c"]), f0(d["R"]), " ; ".join(d["aiguilles"]) or "—"] for d in F.FRONT.values()]))
    P.append("""
**Les deux anneaux du grand cadran :**
- **Constellations J2000 (fixe).** C'est le repère des étoiles.
- **Zodiaque tropique et mois grégoriens (tournant).** Il recule d'un tour en 25 772 ans : c'est la précession.

**La commande de l'anneau tropique.** L'anneau est une seule pièce qui tourne dans une feuillure de la platine-cadran.
- Ses 179 dents intérieures (m 0,8) sont à r 71,6 mm, sous les aiguilles.
- Le pignon de 15 dents qui le mène passe par un trou de la platine.
- Il n'y a donc pas de fente annulaire.

**La pile centrale.** Elle compte dix aiguilles : l'arbre du Soleil, au centre, et neuf tubes. Son diamètre est de
18,4 mm, avec un arbre de 4 mm et 1,6 mm de plus par tube.

Les tubes s'empilent de l'arrière vers l'avant. Le Dragon est le plus extérieur, la Lune la plus intérieure.
""")
    P.append("### 3.2 Face arrière : le temps et les éclipses\n")
    P.append(table(["Cadran", "Centre (mm, repère machine)", "Rayon", "Ce qu'il montre"],
                   [[d["titre"], xy(d["c"]), f0(d["R"]), " ; ".join(d["aiguilles"]) or "—"] for d in F.BACK.values()]))
    P.append("""
**Le sens des graduations.** La face arrière se lit de dos. Un arbre qui tourne dans le sens horaire vu de face tourne
donc dans le sens anti-horaire vu de dos. Les graduations sont gravées pour le lecteur de dos :
- l'anneau des dates avance dans le sens anti-horaire vu de dos ;
- le Saros et les éclipses suivent la même règle.
""")
    o = F.ORRERY
    P.append("### 3.3 Couvercle : le système solaire vu d'en haut\n")
    P.append(table(["Corps", "Rayon affiché (mm)", "Source de l'angle"],
                   [[L.NAME_FR[k], f0(v), "UAK maîtresse" if k == "earth" else f"tour {L.de(L.NAME_FR[k])} (suiveur F)"]
                    for k, v in o["rayons"].items()]))
    P.append(f"""
**Ce que montre le couvercle :**
- **Les angles sont exacts.** Ils viennent des mêmes arbres que les aiguilles de devant.
- **Les orbites se voient.** Chaque planète glisse dans une rainure fixe, cercle décentré ou ellipse.
- **Les bras sont à des hauteurs différentes.** Le bras de la Lune (12 mm autour de la Terre) passe au-dessus de la rainure de Mars ; Saturne, Uranus et Neptune ne sont qu'à 3,6–3,8 mm l'une de l'autre.
- **La Terre est un tellurion :** un globe de {f0(2 * o['tellurion']['globe_r'])} mm, incliné de 23,44°, qui tourne en un jour sidéral.
- **Le bras de la Lune** est mené par la 11ᵉ tringle.
- **L'aiguille d'ombre** est décalée de γ par la coulisse d'éclipse.

**Les tringles qui montent :** onze, espacées d'au moins {f1(c['couvercle']['min_gap_mm'])} mm, alors qu'il en faut
{f1(c['couvercle']['need_mm'])} pour leurs pignons.
""")
    return P


if __name__ == "__main__":
    import architecture
    architecture.main()
