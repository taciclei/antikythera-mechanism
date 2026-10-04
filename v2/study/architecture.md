# Anticythère 2.0 — Architecture de la machine

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

- **Une caisse de 470 × 360 × 391 mm** (largeur × hauteur × profondeur), plus l'orrery d'environ
  70 mm sur le couvercle. Masse estimée : **24,2 kg** en laiton, **20,7 kg**
  avec des platines intérieures en aluminium.
- **Trois faces** : devant le ciel vu de la Terre, derrière le calendrier et les éclipses, dessus le système solaire.
- **Cinq étages**, sept **tours planétaires** et un **bloc de la Lune**.
- **Environ 511 roues dentées**, détaillées au § 7.
- **Vérifié** :
  - 379 pièces modélisées en 3D (cylindres et tringles, avec leur cote z) ;
  - **0 collision** ;
  - 13 trains placés roue par roue ;
  - les 70 arbres de `trains.json` ont tous une place (13
    d'entre eux roue par roue, les autres dans des blocs) ;
  - faces et couvercle conformes.

## 1. Ce qui a changé après les revues

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

## 2. Le principe : une base de temps, deux bus, des tours

1. **La manivelle mène l'arbre-jour J** (1 tour par jour solaire moyen). Le calendrier grégorien impose ce choix.
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

## 3. Les trois faces

### 3.1 Face avant : le ciel vu de la Terre

| Cadran | Centre (mm) | Rayon | Ce qu'il montre |
|---|---|---|---|
| Le ciel vu de la Terre | (0 ; 0) | 150 | Soleil vrai (arbre central) ; Lune vraie et boule de phase ; Mercure ; Vénus ; Mars ; Jupiter ; Saturne ; Uranus ; Neptune ; Dragon (nœuds de la Lune) |
| Horloge 24 h | (−188 ; 118) | 34 | temps solaire moyen (arbre-jour J) ; temps sidéral (gmst) |
| Jupiter et ses lunes | (−188 ; −118) | 34 | Io ; Europe ; Ganymède ; Callisto ; ligne des conjonctions ν ; lunette (barre à λ_J,géo + 90°) |
| Équation du temps (±16,5 min, ×10) | (188 ; −118) | 34 | équation du temps |
| Plaque d'époque (fixe) | (188 ; 118) | 34 | gravé : orbites figées en 2050, valable 2000–2100, date de mise à l'heure |

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

### 3.2 Face arrière : le temps et les éclipses

| Cadran | Centre (mm, repère machine) | Rayon | Ce qu'il montre |
|---|---|---|---|
| Calendrier grégorien | (−112 ; 15) | 105 | anneau des 366 dates (lu à l'index du haut) ; guichet du jour de la semaine ; cadran des années 00-99 et guichet des 400 ans ; voyant « bissextile » |
| Éclipses | (112 ; 15) | 105 | Soleil vrai ; Lune vraie ; disque des nœuds gravé en γ et en magnitudes ; index de la coulisse (γ, amplifié) ; secteur total / annulaire |
| Saros (223 lunaisons) et Exeligmos | (170 ; −128) | 40 | aiguille du Saros sur 223 cases ; petit cadran de l'Exeligmos (+0 h, +8 h, +16 h) |
| Plaque « mode d'emploi » (fixe) | (−120 ; −135) | 30 | gravé : comment lire chaque cadran, comme les inscriptions de la v1 |

**Le sens des graduations.** La face arrière se lit de dos. Un arbre qui tourne dans le sens horaire vu de face tourne
donc dans le sens anti-horaire vu de dos. Les graduations sont gravées pour le lecteur de dos :
- l'anneau des dates avance dans le sens anti-horaire vu de dos ;
- le Saros et les éclipses suivent la même règle.

### 3.3 Couvercle : le système solaire vu d'en haut

| Corps | Rayon affiché (mm) | Source de l'angle |
|---|---|---|
| Mercure | 24 | tour de Mercure (suiveur F) |
| Vénus | 38 | tour de Vénus (suiveur F) |
| Terre | 52 | UAK maîtresse |
| Mars | 66 | tour de Mars (suiveur F) |
| Jupiter | 80 | tour de Jupiter (suiveur F) |
| Saturne | 92 | tour de Saturne (suiveur F) |
| Uranus | 102 | tour d'Uranus (suiveur F) |
| Neptune | 111 | tour de Neptune (suiveur F) |

**Ce que montre le couvercle :**
- **Les angles sont exacts.** Ils viennent des mêmes arbres que les aiguilles de devant.
- **Les orbites se voient.** Chaque planète glisse dans une rainure fixe, cercle décentré ou ellipse.
- **Les bras sont à des hauteurs différentes.** Le bras de la Lune (12 mm autour de la Terre) passe au-dessus de la rainure de Mars ; Saturne, Uranus et Neptune ne sont qu'à 3,6–3,8 mm l'une de l'autre.
- **La Terre est un tellurion :** un globe de 14 mm, incliné de 23,44°, qui tourne en un jour sidéral.
- **Le bras de la Lune** est mené par la 11ᵉ tringle.
- **L'aiguille d'ombre** est décalée de γ par la coulisse d'éclipse.

**Les tringles qui montent :** onze, espacées d'au moins 14,0 mm, alors qu'il en faut
12,2 pour leurs pignons.


## 4. L'intérieur : cinq étages

| Étage | Rôle | z (mm) | Sous-étages (z) | Contenu |
|---|---|---|---|---|
| **E5** | étage du temps, du calendrier et de la Lune | 3–123 | anneau 3–9, m1 9–48, m2 48–87, ponts 87–90, T1 90–105, T2 105–123 | cal_anneau, cal_meca, semaine, annees, lune, croix, jour, temps, precession_ring, saros, moon_node, moon_L |
| **E4** | étage des trains moyens (bus de l'année) | 125–185 | A 125–134, B 134–143, C 143–152, ponts 152–155, T1 155–170, T2 170–185 | Y, venus_L, neptune_L, mercury_L, mars_L, uranus_L, saturn_L, jupiter_L, moon_perigee |
| **E3** | étage de Kepler (unités d'anomalie) | 187–219 | uak 187–204, T1 204–219 | 7 tours, terre_maitre |
| **E2** | étage des modules géocentriques | 221–249 | mod 221–249 | 7 tours |
| **E1** | étage des renvois avant | 251–335 | T1 251–266, T2 266–281, pile 281–335 | pile, laplace, horloge, edt, prec_pignon |

**Règles de construction :**
- **Platines.** Des platines de 2 mm séparent les étages.
- **Arbres.** Un arbre de train va de la platine (en E5, d'un pont bas) jusqu'à un **pont** de 3 mm. Il traverse donc
  tous les plans de son étage.
- **Plans.** Chaque couple occupe un plan de 3 mm.
- **Tringles.** Leurs couches font 15 mm. Deux tringles d'une même couche ne se croisent jamais.

**Budget en hauteur des blocs** (plans de 3 mm, revue N5) :

| Bloc | Plans | Besoin (mm) | Hauteur (mm) | Contenu estimé |
|---|---|---|---|---|
| lune | 26 | 78 | 78 | 4 entrées sur l'axe M (L, ϖ, Ω, Y), copie de l'UAK Terre (4), cascade (13 : réduction 2, équation annuelle = différentiel plat 3 + couple 30:155, évection = différentiel plat 3, anomalie 2, variation 2), prises (3), coulisse d'éclipse et porte-nœuds (2) |
| temps | 20 | 60 | 78 | 5 différentiels plats (2 par plan de 3), joint de Hooke (5 plans), 120:12, 15:179 et son fou, copie de l'UAK Terre (4 plans), entrées et sorties |
| laplace | 18 | 54 | 54 | 3 trains de 3 couples (9), 2 doubleurs, 2 différentiels plats côte à côte (3), 4 couples vers le cadran jovien (4) |
| cal_meca | 8 | 24 | 78 | 2 croix de Malte, différentiel, 20:61, roues-programmes 4/100/400 et cames |

**Blocs-mécanismes** (enveloppes estimées ; leur intérieur sera dessiné en 3D) :

| Bloc | Étage | Centre | Rayon (mm) | Rôle |
|---|---|---|---|---|
| cal_anneau | E5 | (−112 ; 15) | 96,0 | anneau des dates : 200 dents intérieures (m 0,9), 366 crans à sautoir |
| cal_meca | E5 | (−112 ; 15) | 46,0 | croix de Malte (principale et de saut), différentiel, roues-programmes 4/100/400, cames |
| semaine | E5 | (−64 ; −10) | 20,0 | disque des 7 jours, vu par un guichet du cadran du calendrier |
| annees | E5 | (−125 ; −40) | 24,0 | disque du siècle (00-99) et guichet des 400 ans |
| lune | E5 | (112 ; 15) | 50,0 | cascade lunaire à 5 étages sur l'axe M, coulisse d'éclipse sur le porte-nœuds coaxial, copie de l'UAK Terre ; 3 couples d'entrée ramènent L, ϖ, Ω sur l'axe, 4 couples de prise en sortent |
| croix | E5 | (−66 ; −11) | 12,0 | croix de Malte du calendrier, menée par la goupille de J (interface J → calendrier) |
| jour | E5 | (−50 ; −20) | 17,0 | arbre-jour J ; sa goupille mène la croix de Malte du calendrier (6 fentes) et une croix de semaine à 7 positions (même rapport 1:7 que 10:70) |
| temps | E5 | (0 ; −78) | 46,0 | différentiels du temps sidéral, joint de Hooke (ε = 23,44°), équation du temps ×10, couple 15:179 (m 0,4) qui ramène l'arbre de précession au rapport de l'anneau, copie de l'UAK Terre menée par Y (Soleil vrai λ) |
| terre_maitre | E3 | (0 ; 0) | 28,0 | UAK maîtresse de la Terre : Soleil vrai (aiguille, orrery, temps) |
| pile | E1 | (0 ; 0) | 9,2 | pile centrale : arbre du Soleil et 9 tubes coaxiaux (Ø 18,4 mm) |
| laplace | E1 | (−143 ; −88) | 79,1 | boîte de Laplace : trains G, ν, C empilés (10 mm chacun), deux doubleurs, deux différentiels |
| horloge | E1 | (−188 ; 118) | 20,0 | renvoi des aiguilles 24 h : temps moyen (J) et temps sidéral |
| edt | E1 | (188 ; −118) | 14,0 | renvoi de l'aiguille de l'équation du temps |
| prec_pignon | E1 | (0 ; −66) | 8,0 | pignon de 15 dents (m 0,8) qui mène l'anneau tropique (179 dents intérieures) |

## 5. Les tours et les trains, roue par roue

| Planète | Axe (mm) | Module R | Unité de Kepler | Couples (ordre retenu) | Sous-étage | Reprise de Y | Moyeu |
|---|---|---|---|---|---|---|---|
| Mercure | (157 ; 102) | 60 | résolveur de Kepler + ellipse à deux bras | 73:79 · 64:31 · 37:17 | AB | 24 → fou 24 (tenon) → 24 | Y4a |
| Vénus | (−147 ; 92) | 70 | équant bissecté | 124:67 · 166:189 | A | 24 → fou 96 (tenon) → 24 | Y4a |
| Mars | (5 ; 92) | 70 | équant + épicyclet | 97:88 · 41:85 | A | 24 → fou 64 (tenon) → 24 | Y4b |
| Jupiter | (−168 ; −112) | 50 | équant bissecté | 10:26 · 16:73 | A | 24 → fou 32 (tenon) → 24 | Y4a |
| Saturne | (−56 ; −112) | 50 | équant bissecté | 10:41 · 11:79 | A | 24 → fou 32 (tenon) → 24 | Y4b |
| Uranus | (168 ; −112) | 50 | équant bissecté | 10:84 · 10:100 | A | 24 → fou 64 (tenon) → 24 | Y4b |
| Neptune | (56 ; −112) | 50 | équant bissecté | 12:148 · 11:147 | B | 24 → fou 96 (tenon) → 24 | Y4a |

**La recherche.** Pour chaque train, le script essaie toutes les combinaisons suivantes :
- les ordres des couples (le produit ne change pas) ;
- les places du pignon fou ;
- les reprises de Y par pignon fou sur tenon, de 16 à 112 dents (le sens est gardé) ;
- les sous-étages ;
- les angles, de 10° en 10°, avec un élagage dès qu'un arbre viole une règle.

**Les règles :**
- une roue ne touche aucun arbre, sauf le sien et celui de la roue qu'elle mène ;
- deux roues d'un même plan ne se touchent que si elles engrènent ;
- un petit pignon est taillé dans son arbre : sa partenaire peut donc en approcher l'arbre jusqu'au fond de dent.

| Train | Étage / sous-étage | Moyeu | Arbres (entrée → sortie) |
|---|---|---|---|
| `Y` | E4 / A | — | (−50 ; −20) → (−50 ; 3) → (−34 ; 41) → (0 ; 0) |
| `venus_L` | E4 / A | Y4a | (−96 ; 77) → (−60 ; 107) → (−147 ; 92) → (−126 ; 71) |
| `precession_ring` | E5 / T2 (coq + plan + tringle) | — | (56 ; −112) → (91 ; −106) |
| `neptune_L` | E4 / B | Y4a | (106 ; −144) → (99 ; −104) → (56 ; −112) → (78 ; −132) |
| `mercury_L` | E4 / AB | Y4a | (145 ; 82) → (184 ; 97) → (166 ; 112) → (157 ; 102) → (168 ; 78) → (148 ; 94) |
| `mars_L` | E4 / A | Y4b | (37 ; 117) → (29 ; 72) → (5 ; 92) → (26 ; 98) |
| `uranus_L` | E4 / A | Y4b | (134 ; −125) → (142 ; −103) → (168 ; −112) → (155 ; −130) |
| `saturn_L` | E4 / A | Y4b | (−69 ; −134) → (−75 ; −123) → (−56 ; −112) → (−58 ; −126) |
| `jupiter_L` | E4 / A | Y4a | (−194 ; −112) → (−187 ; −101) → (−168 ; −112) → (−181 ; −118) |
| `moon_perigee` | E4 / A | Y4b | (48 ; 10) → (48 ; −22) → (81 ; −3) |
| `saros` | E5 / m1 | Y5 | (154 ; −84) → (159 ; −98) → (170 ; −128) |
| `moon_node` | E5 / m1 | Y5 | (11 ; 46) → (33 ; 38) → (65 ; 32) → (18 ; 40) |
| `moon_L` | E5 / m1 | J5 | (14 ; −21) → (22 ; −18) → (42 ; −10) → (65 ; −2) |

## 6. Renvois et interfaces

| Renvoi | Rôle | Parcours |
|---|---|---|
| `geo_mercury` | longitude géocentrique de Mercure vers la pile avant | arbre à (157 ; 102), E2 mod → E1 T1 ; tringle (157 ; 102) → carrousel (E1 T1) |
| `orr_mercury` | longitude héliocentrique de Mercure vers l'orrery (suiveur F) | tringle prise → haut (E3 T1) |
| `geo_venus` | longitude géocentrique de Vénus vers la pile avant | arbre à (−147 ; 92), E2 mod → E1 T1 ; tringle (−147 ; 92) → carrousel (E1 T1) |
| `orr_venus` | longitude héliocentrique de Vénus vers l'orrery (suiveur F) | tringle prise → haut (E3 T1) |
| `geo_mars` | longitude géocentrique de Mars vers la pile avant | arbre à (5 ; 92), E2 mod → E1 T1 ; tringle (5 ; 92) → carrousel (E1 T1) |
| `orr_mars` | longitude héliocentrique de Mars vers l'orrery (suiveur F) | tringle prise → haut (E3 T1) |
| `geo_jupiter` | longitude géocentrique de Jupiter vers la pile avant | arbre à (−168 ; −112), E2 mod → E1 T1 ; tringle (−168 ; −112) → carrousel (E1 T1) |
| `orr_jupiter` | longitude héliocentrique de Jupiter vers l'orrery (suiveur F) | tringle prise → haut (E3 T1) |
| `geo_saturn` | longitude géocentrique de Saturne vers la pile avant | arbre à (−56 ; −112), E2 mod → E1 T1 ; tringle (−56 ; −112) → carrousel (E1 T1) |
| `orr_saturn` | longitude héliocentrique de Saturne vers l'orrery (suiveur F) | tringle prise → haut (E3 T1) |
| `geo_uranus` | longitude géocentrique d'Uranus vers la pile avant | arbre à (168 ; −112), E2 mod → E1 T1 ; tringle (168 ; −112) → carrousel (E1 T1) |
| `orr_uranus` | longitude héliocentrique d'Uranus vers l'orrery (suiveur F) | tringle prise → haut (E3 T1) |
| `geo_neptune` | longitude géocentrique de Neptune vers la pile avant | arbre à (56 ; −112), E2 mod → E1 T1 ; tringle (56 ; −112) → carrousel (E1 T1) |
| `orr_neptune` | longitude héliocentrique de Neptune vers l'orrery (suiveur F) | tringle prise → haut (E3 T1) |
| `orr_earth` | Soleil vrai (Terre) vers l'orrery | tringle prise → haut (E3 T1) |
| `moon_true` | Lune vraie vers la pile avant | arbre à (132 ; 15), E5 meca → E1 T1 ; tringle (132 ; 15) → carrousel (E1 T1) |
| `node` | nœud ascendant (aiguille du Dragon) vers la pile avant | arbre à (150 ; −5), E5 meca → E1 T1 ; tringle (150 ; −5) → carrousel (E1 T1) |
| `gamma` | course de la coulisse d'éclipse (γ) vers l'aiguille d'ombre du globe | arbre à (118 ; 40), E5 meca → E3 T1 ; tringle (118 ; 40) → (118 ; 168) (E3 T1) |
| `orr_moon` | Lune vraie vers le bras de la Lune du tellurion | arbre à (100 ; 30), E5 meca → E3 T1 ; tringle (100 ; 30) → (100 ; 168) (E3 T1) |
| `lune_Y` | année Y vers le bloc de la Lune (évection, équation annuelle) | tringle hub → (100 ; 62) (E5 T1) ; arbre à (100 ; 62), E5 T1 → E5 meca |
| `j_avant` | arbre-jour vers la boîte de Laplace | tringle hub → (−95 ; −45) (E5 T2) ; arbre à (−95 ; −45), E5 T2 → E1 pile |
| `vers_horloge` | temps moyen (J) et temps sidéral, coaxiaux, vers l'horloge 24 h | arbre à (−21 ; −58), E5 meca → E1 T2 ; tringle (−21 ; −58) → (−188 ; 118) (E1 T2) |
| `vers_edt` | équation du temps (×10) vers son cadran | arbre à (15 ; −58), E5 meca → E1 T2 ; tringle (15 ; −58) → (188 ; −118) (E1 T2) |
| `prec_avant` | arbre de la roue de 131 (précession × 179/15) : il monte droit jusqu'au pignon de l'anneau tropique | arbre à (0 ; −66), E5 meca → E1 pile |
| `tellurion` | temps sidéral vers la rotation du globe de l'orrery | arbre à (−30 ; −92), E5 meca → E3 T1 ; tringle (−30 ; −92) → (−30 ; 168) (E3 T1) |
| `lunette` | longitude géocentrique de Jupiter vers la lunette | arbre à (−168 ; −112), E1 T1 → E1 T2 ; tringle (−168 ; −112) → (−188 ; −118) (E1 T2) |
| `manivelle` | manivelle (paroi gauche) vers l'arbre-jour | tringle (−225 ; 25) → hub (E5 T2) |
| `temps_J` | arbre-jour vers le bloc du temps (temps sidéral, horloge) | tringle hub → (−42 ; −70) (E5 T2) ; arbre à (−42 ; −70), E5 T2 → E5 meca |
| `temps_Y` | année Y vers le bloc du temps (Soleil moyen, précession) | tringle hub → (30 ; −88) (E5 T1) ; arbre à (30 ; −88), E5 T1 → E5 meca |

**Carrousel** (angle de chaque arbre intermédiaire) : Lune 36°, Mercure 76°, Mars 116°, Vénus 156°, Jupiter −164°, Saturne −124°, Neptune −84°, Uranus −44°, Dragon −4°.

**Interfaces déclarées** (une pièce qui entre volontairement dans l'enveloppe d'un bloc) :

| Pièce | Bloc | Entre de (mm) |
|---|---|---|
| `croix` | jour | 11,0 |
| `croix` | cal_meca | 4,9 |
| `lune_Y#z1` | lune | 3,5 |
| `moon_perigee#a2` | lune | 4,0 |
| `moon_node#a2` | lune | 2,0 |
| `moon_node#w4` | lune | 27,7 |
| `moon_L#a3` | lune | 2,0 |
| `moon_L#w5` | lune | 19,2 |
| `lune_entree_moon_L#w1` | lune | 10,5 |
| `lune_entree_moon_L#fou` | lune | 33,0 |
| `lune_entree_moon_L#w2` | lune | 21,0 |
| `lune_entree_moon_node#w1` | lune | 10,5 |
| `lune_entree_moon_node#fou` | lune | 40,5 |
| `lune_entree_moon_node#w2` | lune | 21,0 |
| `lune_entree_moon_perigee#w1` | lune | 21,0 |
| `lune_entree_moon_perigee#fou` | lune | 21,0 |
| `lune_entree_moon_perigee#w2` | lune | 21,0 |

Ce sont :
- la croix de Malte, entre l'arbre-jour et le calendrier ;
- les arbres d'arrivée des trains de la Lune et leurs couples d'entrée (40 → pignon fou → 40), qui ramènent L, ϖ et Ω
  sur l'axe M du bloc ;
- l'arrivée de Y au bloc Lune.

L'intérieur des blocs devra les accueillir.

**Contrôle strict (revue N9).** Le recontrôle compte comme liées les seules pièces citées par leur identifiant exact.
Il trouve 37 recouvrements de plus, tous voulus : une pièce montée sur son propre axe de tour (UAK, tube Y, roue de
prise, couronne du bus, roue finale) ou le pignon de 10 taillé dans l'arbre de Neptune. Aucun recouvrement réel caché.


## 7. Les roues

| Poste | Roues |
|---|---|
| trains, différentiels et pas à pas de trains.json | 196 |
| couronnes des 4 moyeux (96 dents) | 4 |
| tringles de bus vers 11 trains (pignon 24, pignon 24, couronne 96) | 33 |
| reprises 1:1 du tube Y dans les 7 tours (couple, ou couple et pignon fou) | 21 |
| renvoi geo_mercury | 6 |
| renvoi orr_mercury | 6 |
| renvoi geo_venus | 6 |
| renvoi orr_venus | 6 |
| renvoi geo_mars | 6 |
| renvoi orr_mars | 6 |
| renvoi geo_jupiter | 6 |
| renvoi orr_jupiter | 6 |
| renvoi geo_saturn | 6 |
| renvoi orr_saturn | 6 |
| renvoi geo_uranus | 6 |
| renvoi orr_uranus | 6 |
| renvoi geo_neptune | 6 |
| renvoi orr_neptune | 6 |
| renvoi orr_earth | 6 |
| renvoi moon_true | 8 |
| renvoi node | 8 |
| renvoi gamma | 8 |
| renvoi orr_moon | 8 |
| renvoi lune_Y | 5 |
| renvoi j_avant | 3 |
| renvoi vers_horloge | 8 |
| renvoi vers_edt | 4 |
| renvoi prec_avant | 0 |
| renvoi tellurion | 6 |
| renvoi lunette | 4 |
| renvoi manivelle | 1 |
| renvoi temps_J | 3 |
| renvoi temps_Y | 3 |
| renvoi prec_bas (2 couples coniques) | 4 |
| entrées du bloc Lune : 3 couples 40 → fou → 40 (L, Ω, ϖ) | 9 |
| modules vectoriels : 7 × (bras planète 2 + bras Terre 2 + chaîne 1:1 3) | 49 |
| cascade lunaire : 6 couples relatifs | 12 |
| couronne de phase de la Lune (48:48) | 2 |
| cadran jovien : 4 couples | 8 |
| demi-roues anti-jeu (ciseaux) des 9 couples 64:64 du carrousel | 9 |
| bloc du temps : couple 15:179 de la précession + pignon fou | 3 |
| bloc du temps : copie de l'UAK Terre (couple d'entrée) | 2 |
| **Total** | **511** |

**Règles de compte :**
- une tringle 1:1 a deux couples coniques, soit 4 roues ;
- une tringle de moyeu a 3 roues : un pignon au départ, un pignon et une couronne à l'arrivée ;
- chaque tube de la pile ajoute un couple 64:64 ;
- une tringle vers le couvercle compte sa prise, son renvoi d'angle en haut et son couple vers le tube de l'orrery,
  moins le couple conique déjà compté dans `trains.json`.

## 8. Le sens de rotation

**Les règles d'inversion :**
- un couple extérieur inverse le sens, un couple intérieur le garde ;
- un pignon fou inverse ;
- un renvoi conique (ou une couronne) peut faire l'un ou l'autre : cela dépend de la face où engrène le pignon.

Chaque chaîne de renvoi contient au moins un renvoi conique ou un pignon fou. Le sens de chaque arbre peut donc
toujours être réglé pour retrouver le sens `phys` de `trains.json`. Le contrôle sur pièces réelles se fera en 3D.

| Renvoi | Chaîne | Sens sans réglage | Réglage |
|---|---|---|---|
| `geo_mercury` | con → con → ext | − | côté d'engrènement d'une conique |
| `orr_mercury` | ext → con → con → ext | + | côté d'engrènement d'une conique |
| `geo_venus` | con → con → ext | − | côté d'engrènement d'une conique |
| `orr_venus` | ext → con → con → ext | + | côté d'engrènement d'une conique |
| `geo_mars` | con → con → ext | − | côté d'engrènement d'une conique |
| `orr_mars` | ext → con → con → ext | + | côté d'engrènement d'une conique |
| `geo_jupiter` | con → con → ext | − | côté d'engrènement d'une conique |
| `orr_jupiter` | ext → con → con → ext | + | côté d'engrènement d'une conique |
| `geo_saturn` | con → con → ext | − | côté d'engrènement d'une conique |
| `orr_saturn` | ext → con → con → ext | + | côté d'engrènement d'une conique |
| `geo_uranus` | con → con → ext | − | côté d'engrènement d'une conique |
| `orr_uranus` | ext → con → con → ext | + | côté d'engrènement d'une conique |
| `geo_neptune` | con → con → ext | − | côté d'engrènement d'une conique |
| `orr_neptune` | ext → con → con → ext | + | côté d'engrènement d'une conique |
| `orr_earth` | ext → con → con → ext | + | côté d'engrènement d'une conique |
| `moon_true` | ext → con → con → ext | + | côté d'engrènement d'une conique |
| `node` | ext → con → con → ext | + | côté d'engrènement d'une conique |
| `gamma` | crémaillère → con → con | + | côté d'engrènement d'une conique |
| `orr_moon` | ext → con → con → ext | + | côté d'engrènement d'une conique |
| `lune_Y` | con → con → ext | − | côté d'engrènement d'une conique |
| `j_avant` | con → con | + | côté d'engrènement d'une conique |
| `vers_horloge` | con → con | + | côté d'engrènement d'une conique |
| `vers_edt` | con → con | + | côté d'engrènement d'une conique |
| `prec_avant` | int | + | aucun (même sens) |
| `tellurion` | ext → con → con | − | côté d'engrènement d'une conique |
| `lunette` | con → con | + | côté d'engrènement d'une conique |
| `manivelle` | con | + | côté d'engrènement d'une conique |
| `temps_J` | con → con | + | côté d'engrènement d'une conique |
| `temps_Y` | con → con | + | côté d'engrènement d'une conique |
| `prec_bas` | con → con | + | côté d'engrènement d'une conique |
| `reprises de Y dans les tours` | 24 → fou → 24 (2 engrènements) | + | aucun : la reprise par pignon fou garde le sens, la planète et la copie de la Terre tournent comme dans trains.json |
| `entrées du bloc Lune (L, Ω, ϖ)` | 40 → fou → 40 (2 engrènements) | + | aucun : le sens est gardé |

## 9. Le jeu des engrenages

**Le problème.** Avec un jeu de 0,03 mm par paire de dents, les renvois en aval d'un
suiveur laissent **0,82°** de flottement à l'aiguille. Ces renvois sont deux couples coniques
m 0,4 et le couple 64:64.

**Quand ce jeu apparaît.** Il apparaît **chaque fois que la sortie change de sens**, même si la manivelle tourne
toujours dans le même sens. C'est le cas :

- 7 aiguilles planétaires (stations de rétrogradation) ;
- équation du temps ;
- lunette de Jupiter ;
- coulisse d'éclipse γ ;
- aiguille d'ombre ;

C'est plus que l'erreur géométrique, au moment le plus intéressant : la boucle de rétrogradation.

**Le remède retenu** : coniques précontraintes par un ressort axial (le pignon est poussé dans la denture) et couples 64:64 à ciseaux (une demi-roue de plus par tube) ; jeu résiduel ≈ 0.

Un frein à friction ne convient pas : il retiendrait l'aiguille pendant que le jeu se rattrape. Les embrayages à
friction ne servent qu'à la mise à l'heure initiale.

## 10. Bilans

### 10.1 Masse

| Poste | Masse (g) |
|---|---|
| roues des trains (trains.json, sans les options) | 1659 |
| roues des différentiels | 458 |
| roues de renvoi et roues internes (architecture) | 1498 |
| platines intérieures (laiton, ajourées 50 %) | 5184 |
| platines-cadrans avant et arrière (laiton 3 mm) | 6609 |
| caisse en chêne 6 mm et porte arrière | 3437 |
| verre avant 2 mm | 846 |
| arbres, tubes, ponts, goupilles, ressorts | 1800 |
| UAK, modules, cascade, coulisses | 1500 |
| orrery et tellurion | 1200 |
| **Total** | **24,2 kg** |

Avec des platines intérieures en aluminium, la masse descend à **20,7 kg**. Les options
(`gmst_direct`, `synodic`, `saros_223`, `mars_apsides`) ne sont pas comptées.

### 10.2 Manivelle

**Mode normal.** Un pignon de 24 dents engrène la couronne de 96 de l'arbre-jour : **1 tour de manivelle = 6 heures**.

**Mode rapide.** Une boîte 1:30 sur la paroi donne **1 tour = 7,5 jours**. La manivelle « de la semaine » de
`trains.md` n'est plus possible : une croix de Malte ne se mène pas à l'envers.

**Effort.** L'effort de manivelle se mesurera sur prototype.

### 10.3 Fabrication

- **Modules.**
  - Trains : m 0,5, avec deux couples en m 0,55 et m 0,7.
  - Couronnes intérieures : m 0,8 et m 0,9.
  - Renvois coniques : m 0,4. Les coniques 40:40 de `trains.json` vers l'orrery deviennent un couple de prise et une
    conique m 0,4, au même rapport.
- **Tolérance de position :** 0,02 mm.
- **Le suiveur F des planètes extérieures** pivote à 0,4–3,7 mm de l'axe de la tour, à l'intérieur de son rayon. Il
  tourne donc sur une **bague excentrique de Ø 18 mm** fixée à la platine P2, autour de l'axe.
  - Sa roue de prise (46 dents, r 12) est enfilée sur la bague.
  - Elle engrène, à 23 mm, l'arbre décalé qui porte la conique.
  - Mercure, Jupiter et Saturne prennent du côté −x, les autres du côté +x.
  - Le modèle centre cette roue sur l'axe ; en réalité, elle tourne autour de F, jusqu'à 3,7 mm plus loin. Les jeux
    restent d'au moins 3,8 mm.
- **Différentiels** : à engrenages droits (satellites par paires), même relation que les différentiels coniques de
  `trains.json`, mais 3 plans de haut.
- **Les excentriques les plus fins :**
  - l'épicyclet de Mars (0,087 mm) ;
  - le bras Soleil de Neptune (1,6 mm).

  Ils se font par bague excentrique réglable ou par électroérosion.

## 11. Budget d'erreur attendu (2000–2100)

| Aiguille | Géométrie | Physique hors Kepler | Tolérance 0,02 mm | Rapport (°/siècle) |
|---|---|---|---|---|
| Mercure | 0,26° | 15″ | 0,05° | −0,0082° |
| Vénus | 0,21° | 20″ | 0,11° | −0,0009° |
| Mars | 0,24° | 40″ | 0,12° | 0,0060° |
| Jupiter | 0,07° | 0,11° | 0,04° | −0,0022° |
| Saturne | 0,08° | 0,17° | 0,03° | 0,0040° |
| Uranus | 0,05° | 50″ | 0,03° | 0,0052° |
| Neptune | 0,02° | 10″ | 0,03° | −0,0089° |

- **Copies de l'UAK Terre** (tours, bloc Lune, bloc du temps) : une tolérance de 0,02 mm donne environ
  0,05° d'écart entre le Soleil de l'aiguille et celui de chaque copie. Cet écart s'ajoute
  aux colonnes ci-dessus. Pour l'équation du temps, il fait au plus 12 s d'écart avec
  l'aiguille du Soleil.
- **Lune** : 0,26° au maximum, 0,10° rms.
- **Calendrier** : exact de 1582 à 6000 (0 erreur).
- **Temps sidéral** : −0,063 s par siècle.
- **Équation du temps** : 3,1 s au plus pour le modèle. Le bloc du temps
  calcule λ avec sa propre copie de l'UAK Terre : sa tolérance ajoute jusqu'à 12 s, soit
  environ 15 s au pire.
- **Éclipses** : 449 sur 452, erreur sur γ d'au plus 0,035.
- **Jeu** : environ 0 avec les roues à ciseaux ; sinon 0,82° à chaque changement de sens.

## 12. Ce que cette architecture ne prouve pas encore

- **Les blocs restent des enveloppes estimées**, pas des pièces : cascade lunaire, calendrier, temps, Laplace, UAK,
  modules. Leur intérieur, y compris les interfaces du § 6, sera dessiné et vérifié en 3D.
- **Le socle de l'orrery** n'est vérifié que pour l'espacement des tringles qui y arrivent.
- **La dynamique n'est pas calculée :** efforts, frottements, flexion.
- **Le modèle est fait de disques.** Une roue est un disque plein (tête de dent) ; une conique couchée est un disque
  dans sa couche. Les profils de dents et l'interférence fine viendront avec la 3D (BVH, comme la v1).

## 13. Suite

1. Construction 3D dans Blender à partir de `spec/architecture.json`, avec contrôle d'interférence pièce par pièce.
2. Preuves Lean 4 des rapports de `trains.json` et des identités exactes : Laplace, Hooke, calendrier.
