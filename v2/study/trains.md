# Anticythère 2.0 — Les trains d’engrenages

*Généré par `v2/tools/trains.py` (ne pas éditer à la main). Données : `v2/spec/trains.json`. Constantes : `v2/research/constants.json`. Tous les rapports sont des fractions exactes, recalculées avec `fractions.Fraction` à chaque exécution ; `trains.py --check` les revérifie à partir des seuls nombres de dents.*

## 0. L’essentiel

- **Une seule entrée** : l’arbre-jour J, 1 tour par jour solaire moyen. Le calendrier grégorien compte des jours ; il n’est exact que si la machine compte des jours, car 146 097 = 3³·7·773, et 773 est premier et dépasse 220 dents.
- **La roue de l’année Y** (longitude moyenne de la Terre, repère fixe J2000) est menée par J en 3 couples. De Y partent : Mercure, Vénus, Mars, Jupiter, Saturne, Uranus, Neptune, périgée ϖ, nœuds Ω, Saros, comme les trains de b1 dans la machine antique. De J partent directement : Lune L, Ganymède, ν, Callisto. L’anneau du zodiaque (précession) part de Neptune.
- **16 trains approchés**, choisis par recherche exhaustive : 38 couples. Il faut aussi 18 couples de rapport exact (semaine, calendrier, renvois, Exeligmos…), 2 pignons fous pour le sens et 10 différentiels. Toutes les dentures sont dans [10, 220] ; la machine de base n’a aucune exception. La variante « Saros à 223 dents » en serait une, en hommage à b1.
- **Tout le reste est exact par construction** :
  - les différentiels : évection 2λ☉ − ϖ, temps sidéral, équation du temps, Laplace ;
  - les roues de rapport entier : semaine, calendrier, Exeligmos, épicyclet de Mars ;
  - les unités non linéaires, qui font un tour par tour : Kepler, modules géocentriques, cascade lunaire, joint de Hooke.
- **Bilan** : les 65 vérifications passent. Les plus grosses erreurs d’engrenage sont : Neptune −8,9·10⁻³°/siècle, Mercure −8,2·10⁻³°/siècle, périgée ϖ +6,7·10⁻³°/siècle.
  - C’est 100 à 1 000 fois sous les objectifs de la tâche (1°/siècle pour les planètes, 2°/siècle pour la Lune).
  - C’est aussi sous l’incertitude des moyens mouvements eux-mêmes (0,005 à 0,05°/siècle).
  - **Les engrenages ne limitent nulle part la précision** ; la géométrie et la physique la limitent.

| Grandeur | Objectif de la tâche | Erreur d’engrenage (°/siècle) | Marge |
|---|---|---|---|
| Soleil / Terre | < 1°/siècle | −3,8·10⁻⁴ | ×2 664 |
| Mercure | < 1°/siècle | −8,2·10⁻³ | ×122 |
| Vénus | < 1°/siècle | −8,6·10⁻⁴ | ×1 158 |
| Mars | < 1°/siècle | +6,0·10⁻³ | ×166 |
| Jupiter | < 1°/siècle | −2,2·10⁻³ | ×452 |
| Saturne | < 1°/siècle | +4,0·10⁻³ | ×248 |
| Uranus | < 1°/siècle | +5,2·10⁻³ | ×190 |
| Neptune | < 1°/siècle | −8,9·10⁻³ | ×112 |
| Lune, longitude moyenne L | < 2°/siècle | +1,1·10⁻³ | ×1 786 |
| Lune, élongation D = L − Y | < 2°/siècle | +1,6·10⁻³ | ×1 275 |
| Lune, argument de latitude F = L − Ω | < 2°/siècle | +2,4·10⁻³ | ×821 |
| Lune, anomalie M′ = L − ϖ | < 2°/siècle | −5,5·10⁻³ | ×360 |
| Précession (période) | à 0,5 % près | écart de 5,7·10⁻⁵ % | ×8,8·10³ |

---

## 1. Conventions et méthode

- **Unités.** Les vitesses sont en tours par jour solaire moyen, en fractions exactes. Les « tours par année tropique » s’obtiennent en multipliant par l’année tropique moyenne (365,2421896698 j, Laskar). L’erreur en °/siècle de longitude moyenne vaut (machine − cible) × 360 × 36 525. La **période réalisée** est celle que produit la machine (1/vitesse) : c’est « la période de l’approximation ».
- **Repère.**
  - Tous les trains tournent dans le repère **fixe J2000**, celui des étoiles et de la caisse ; les pivots excentriques de Kepler sont fixés à la caisse.
  - Le **zodiaque tropique** est un anneau qui tourne lentement à rebours (précession).
  - Une aiguille se lit donc en longitude tropique sur cet anneau, et en longitude J2000 sur la couronne fixe des constellations.
- **Cibles.**
  - Planètes et Terre : moyens mouvements DE441 ajustés sur 2000–2100 (`constants.json`).
  - Lune : polynômes de Meeus, ch. 47 (ELP-2000/82), pente moyenne sur 2000–2100, moins p_A.
  - Précession : p_A IAU 2006, pente moyenne 2000–2100 (5 029,90″/siècle).
  - Lunes galiléennes : théorie E5 de Lieske. Temps sidéral : IERS 2010.
- **Signes et sens.**
  - Une vitesse positive est directe (longitudes croissantes). Vu de face, le sens direct est horaire, comme sur le cadran avant de la v1.
  - Chaque couple extérieur inverse le sens ; un anneau à denture intérieure ne l’inverse pas.
  - Le sens de J est choisi pour que Y tourne dans le sens direct sans pignon fou : J tourne à rebours (antihoraire vu de face).
  - Un pignon fou de 20 dents est ajouté à tout train qui sortirait à l’envers.
- **Choix d’un train.**
  - Pour chaque sortie, la recherche exhaustive parcourt toutes les fractions N/D où N et D sont des produits de k nombres de dents compris entre 10 et la taille maximale, avec k = 1, 2 ou 3.
  - On retient d’abord le plus petit k, puis la plus petite taille maximale de roue (échelle 60, 80, 100, 120, 150, 180, 220 dents), puis la plus petite erreur, à condition que l’erreur ne dépasse pas la moitié de l’allocation.
  - Les couples sont ensuite appariés pour équilibrer les rapports par étage.
  - Le rapport visé tient compte de l’erreur réelle de l’arbre source : les erreurs ne s’accumulent pas le long d’une chaîne.
- **Allocations** (erreur d’engrenage admise, en °/siècle) :
  - Terre : 0,001. Elle se reporte sur toutes les planètes vues de la Terre et sur D = L − Y.
  - Planètes : 0,02. Mars, amplifiée ×3,7 à l’opposition, reste ainsi sous 0,1° géocentrique.
  - Lune : 0,01 pour L, 0,02 pour ϖ, 0,01 pour Ω.
  - Ganymède et ν : 0,002 chacun, car Io = 4·Ganymède + 3ν. Callisto : 0,01.
  - Précession : 10⁻⁴ en relatif. Saros : 10⁻⁷ en relatif.
- **Modules.** 0,5 mm par défaut : une roue de 220 dents fait 110 mm. Les deux anneaux à denture intérieure ont le diamètre du cadran avant : zodiaque 0,8 mm, dates 0,9 mm. Tous les modules sont ≥ 0,4 mm.

**Arbre des trains de la machine de base** (généré depuis la conception) :

```
J  (manivelle, 1 tour par jour)
 ├─ 3 couples (approché) → roue de l’année Y, Lune L, Ganymède, ν, Callisto
 ├─ 1 couple (exact) → semaine
 └─ croix de Malte (1/6 par jour) + croix de saut → Σ → 20:61 · 20:200 → anneau des dates
Y  (roue de l’année, repère J2000)
 ├─ 2 couples (approché) → Vénus, Mars, Jupiter, Saturne, Uranus, Neptune, périgée ϖ, nœuds Ω, Saros
 └─ 3 couples (approché) → Mercure
Neptune
 └─ 2 couples (approché) → anneau du zodiaque
rapports entiers (exacts) :
  EdT → aiguille de l’EdT (120:12)
  anneau des dates → programme 4 ans (15:60)
  programme 4 ans → programme 100 ans (12:60 · 12:60)
  programme 100 ans → programme 400 ans (15:60)
  Mars → épicyclet de Mars (60:20)
  Saros → Exeligmos (20:60)
différentiels (exacts) : évection 2Y − ϖ · X = Y + p · S = J + Y · TSMG = J + X · λ + p · EdT = X − α
                         équation annuelle · anneau des dates · Europe = 2Ga + ν · Io = 2Eu + ν
```

---

## 2. Base de temps et manivelle

| Sortie | Source | Cible (tours par année tropique) | Rapport du train (fraction) | Dents (menante:menée) | Erreur (ppm) | Erreur (°/siècle) | Période réalisée |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Semaine (1 tour en 7 jours) | J | — | `1/7` | 10:70 | exact | exact | — |

- **Heure.** L’aiguille des heures solaires moyennes (cadran de 24 h) est l’arbre J lui-même : rapport 1, exact.
- **Manivelle.** Trois positions sont possibles, toutes sur des arbres existants et sans rapport nouveau :
  - sur **J** : 1 tour = 1 jour ;
  - sur la **roue de la semaine W** : 1 tour = 7 jours exactement ; J tourne alors 7 fois, le couple 10:70 étant mené à l’envers ;
  - sur la **roue de l’année Y** : 1 tour = 1 année sidérale ; J tourne alors 365,26 fois. C’est un multiplicateur de 365 à travers 3 couples : possible mais dur (§ 14).
- **Jours solaires et temps des éphémérides.** J compte des jours solaires moyens (UT1), alors que les vitesses cibles sont en jours de 86 400 s SI (TT). L’écart ΔT vaut environ 69 s en 2026 et dérive d’environ 1 min par siècle ; il décale la Lune d’environ 0,01°. Il est négligé ; un réglage manuel reste possible.

## 3. Calendrier grégorien (règle 4/100/400)

| Organe | Rapport exact | Réalisation | Vitesse moyenne |
|---|---|---|---|
| Croix de Malte principale (6 fentes) | 1/6 de tour par jour | une goupille sur J | 1/6 tr/j |
| Croix de saut (6 fentes) | 1/6 de tour la nuit du 28 février des années communes | goupille escamotable, commandée par les cames | 303/(6 · 146 097) tr/j |
| Anneau des dates (366 positions, mois gravés) | (principale + saut)/61 | différentiel conique (½), puis 20:61 et 20:200 (denture intérieure) | 400/146 097 tr/j, soit 1 tour par année civile |
| Roue-programme de 4 ans (came C4) | 1/4 de la précédente | 15:60 | 100/146097 tr/j |
| Roue-programme de 100 ans (came C100) | 1/25 de la précédente | 12:60 · 12:60 | 4/146097 tr/j |
| Roue-programme de 400 ans (came C400) | 1/4 de la précédente | 15:60 | 1/146097 tr/j |

**Comment la règle 4/100/400 est appliquée.**

1. L’anneau avance d’une position par jour. Une année commune doit pourtant parcourir ses 366 positions en 365 jours.
2. La nuit du 28 février d’une année commune, la croix de saut ajoute une position : l’anneau passe directement du 28 février au 1ᵉʳ mars.
3. L’anneau fait donc **exactement un tour par année civile**, quelle qu’elle soit. Les roues-programmes, menées par l’anneau, font exactement un tour en 4, 100 et 400 ans.
4. On saute le 29 février si **C4 ∨ (C100 ∧ C400)**. Les cames sont lues quand l’anneau est sur le 28 février (position 58 sur 366) :
   - **C4**, sur la roue de 4 ans, est levée pendant les trois années non multiples de 4 : un secteur de 270° dont les bords sont à mi-chemin des lectures. Marge minimale : 45,0°.
   - **C100**, sur la roue de 100 ans, n’est levée que l’année séculaire : un secteur de 3,6°. Marge 1,80°, soit ± ½ an.
   - **C400**, sur la roue de 400 ans, est levée pour les trois siècles non multiples de 400 : un secteur de 270°. Marge 45,0°.

**Vérifications exactes** (en fractions) :
- logique des cames, année par année : **0 année fausse** de 1582 à 6000 ;
- mécanisme simulé jour par jour de 1600 à 2400 (292 194 jours) : croix de Malte, saut décidé par les cames à l’angle réel de l’anneau, date lue sous l’index comparée à la vraie date. **0 date fausse**, et **0 jour de la semaine faux** ;
- les trois roues reviennent à leur position après 400 ans : vérifier 400 années consécutives suffit donc pour toutes les années.

- **Jour de la semaine** : 1/7, exact. 146 097 jours font 20 871 semaines : la semaine ne dépend pas de la règle grégorienne.
- **Dérive civile** : 365,2425 j − 365,24219 j = 0,031 j par siècle, soit un jour en ~3 200 ans. Elle vient de la règle grégorienne elle-même, pas de la machine.

## 4. Soleil et Terre : la roue de l’année

| Sortie | Source | Cible (tours par année tropique) | Rapport du train (fraction) | Dents (menante:menée) | Erreur (ppm) | Erreur (°/siècle) | Période réalisée |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Y : Terre (longitude moyenne, J2000) | J | 0,999961196 | `589/215136` | 31:180 · 19:144 · 10:83 | −1,04·10⁻² | −3,8·10⁻⁴ | 365,25637 j |

- Année sidérale réalisée : 365,256366723 j ; cible 365,256362915 j (écart +0,329 s).
- Le **Soleil moyen** est Y + 180°, sur le même arbre.
- Le **Soleil vrai** sort de l’unité de Kepler de la Terre (équant bissecté), qui fait un tour par tour.
- Le Soleil tropique, lu sur le zodiaque, vaut Y + p ; il est formé par différentiel (§ 8).

## 5. Planètes

### 5.1 Longitudes moyennes héliocentriques (repère J2000), depuis la roue de l’année

| Sortie | Source | Cible (tours par année tropique) | Rapport du train (fraction) | Dents (menante:menée) | Erreur (ppm) | Erreur (°/siècle) | Période réalisée |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Mercure | roue de l’année Y | 4,151929958 | `172864/41633` | 37:17 · 64:31 · 73:79 + pignon fou 20 | −5,48·10⁻² | −8,2·10⁻³ | 87,96926 j |
| Vénus | roue de l’année Y | 1,625460109 | `20584/12663` | 124:67 · 166:189 | −1,48·10⁻² | −8,6·10⁻⁴ | 224,70081 j |
| Mars | roue de l’année Y | 0,531663688 | `3977/7480` | 97:88 · 41:85 | 3,15·10⁻¹ | +6,0·10⁻³ | 686,97954 j |
| Jupiter | roue de l’année Y | 0,084296052 | `80/949` | 10:26 · 16:73 | −7,30·10⁻¹ | −2,2·10⁻³ | 4 332,85 j (11,863 a) |
| Saturne | roue de l’année Y | 0,033959669 | `110/3239` | 10:41 · 11:79 | 3,30 | +4,0·10⁻³ | 10 755,14 j (29,447 a) |
| Uranus | roue de l’année Y | 0,011904154 | `1/84` | 10:84 · 10:100 | 1,22·10¹ | +5,2·10⁻³ | 30 681,53 j (84,003 a) |
| Neptune | roue de l’année Y | 0,006067305 | `11/1813` | 12:148 · 11:147 | −4,09·10¹ | −8,9·10⁻³ | 60 200,89 j (164,825 a) |

| Planète | Unité de Kepler | Période sidérale réalisée | Cible (DE441) | Écart | Incertitude du taux cible |
|---|---|---|---|---|---|
| Mercure | résolveur de Kepler (RK) + ellipse à deux bras | 87,96926 j | 87,96926 j | +0,416 s | ±0,005°/siècle |
| Vénus | équant bissecté | 224,70081 j | 224,70080 j | +0,287 s | ±0,005°/siècle |
| Mars | équant + épicyclet (EQE) | 686,97954 j | 686,97975 j | −18,699 s | ±0,005°/siècle |
| Jupiter | équant bissecté | 4 332,85 j (11,863 a) | 4 332,85 j (11,863 a) | +273,179 s | ±0,003°/siècle |
| Saturne | équant bissecté | 10 755,14 j (29,447 a) | 10 755,18 j (29,447 a) | −51,1 min | ±0,044°/siècle |
| Uranus | équant bissecté | 30 681,53 j (84,003 a) | 30 681,91 j (84,004 a) | −541,2 min | ±0,035°/siècle |
| Neptune | équant bissecté | 60 200,89 j (164,825 a) | 60 198,43 j (164,818 a) | +2,465 j | ±0,047°/siècle |

Pour les planètes lentes, l’écart de période paraît grand en jours, mais il ne compte qu’en degrés par siècle : Neptune ne fait que 0,6 tour par siècle.

### 5.2 Ce qu’il faut de plus pour la face avant (géocentrique) et l’orrery : des rapports exacts

| Organe | Rapport | Réalisation | Rôle |
|---|---|---|---|
| Unité de Kepler (une par planète, Terre comprise) | 1 tour par tour | équant : goupille et rainure menée par la rainure ; Mercure : résolveur M = E − e sin E | angle autour du centre φ_C (modules) et anomalie vraie (orrery) |
| Bras planète d’un module vectoriel | 1:1 | renvoi depuis l’unité de Kepler | vecteur Soleil→planète à l’échelle s |
| Bras Terre des 7 modules | 1:1 (×7) | un arbre « φ_C Terre + 180° » et 7 roues égales | vecteur Terre→Soleil |
| Bras 2 d’un module (chaîne le long du bras 1) | 1:1 | roue sur tube, pignon fou, roue égale | conserve l’angle absolu |
| Épicyclet de Mars | 3 | 60:20 | angle 3L − 2ϖ (ϖ figé dans la caisse) |
| Bras (a − b)/2 de Mercure | −1 | inverseur conique coaxial 40:40 | ellipse exacte à deux bras |
| Tubes de l’orrery (8) | 1:1 | renvoi d’angle conique ou roue de champ vers le couvercle | longitudes héliocentriques vraies |
| Aiguilles géocentriques (7 + Soleil) | 1:1 | suiveur du module, renvoi coaxial vers la face avant | longitudes géocentriques |

La vitesse moyenne de chaque aiguille géocentrique est exacte, et vérifiée : c’est celle de la planète pour Mars à Neptune, celle du Soleil (Y) pour Mercure et Vénus. Les boucles de rétrogradation sont des oscillations autour de ce mouvement moyen.

### 5.3 Ce que les erreurs d’engrenage deviennent vues de la Terre

Une erreur δ sur la longitude héliocentrique déplace la planète de r·δ. Vue de la Terre, cela fait au plus r·δ/Δ_min. Borne par siècle, engrenages seuls (planète et Terre) :

| Planète | Δ_min (ua) | Amplification planète | Amplification Terre | Borne géocentrique (°/siècle) |
|---|---|---|---|---|
| Mercure | 0,517 | ×0,90 | ×1,90 | +8,1·10⁻³ |
| Vénus | 0,255 | ×2,86 | ×3,86 | +3,9·10⁻³ |
| Mars | 0,365 | ×3,79 | ×2,79 | +0,024 |
| Jupiter | 3,934 | ×1,26 | ×0,26 | +2,9·10⁻³ |
| Saturne | 8,006 | ×1,13 | ×0,13 | +4,6·10⁻³ |
| Uranus | 17,266 | ×1,06 | ×0,06 | +5,6·10⁻³ |
| Neptune | 28,795 | ×1,04 | ×0,04 | +9,3·10⁻³ |

Ces bornes sont 10 à 100 fois plus petites que les erreurs de géométrie de l’étude des mécanismes (0,02 à 0,26°, dues surtout à l’inclinaison et à la dérive séculaire des orbites).

## 6. La Lune

### 6.1 Les trois trains approchés

| Sortie | Source | Cible (tours par année tropique) | Rapport du train (fraction) | Dents (menante:menée) | Erreur (ppm) | Erreur (°/siècle) | Période réalisée |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Lune : longitude moyenne L | J | 13,368227536 | `4598/125625` | 11:25 · 22:75 · 19:67 | 2,33·10⁻³ | +1,1·10⁻³ | 27,32166 j |
| Périgée ϖ (porte-satellite de l’anomalie) | roue de l’année Y | 0,112986645 | `1222/10815` | 47:105 · 26:103 | 1,64 | +6,7·10⁻³ | 3 232,61 j (8,851 a) |
| Nœud Ω (porte-nœuds, sens rétrograde) | roue de l’année Y | −0,053763612 | `-252/4687` | 12:43 · 21:109 + pignon fou 20 | 6,80·10⁻¹ | −1,3·10⁻³ | 6 793,48 j (18,600 a) |

### 6.2 Les arguments, tous obtenus sans nouveau rapport

| Argument | Formé par | Vitesse réalisée (tours par année tropique) | Cible | Erreur (°/siècle) | Période réalisée |
|---|---|---|---|---|---|
| Élongation D (lunaison) | L − Y | 12,368266381 | 12,368266337 | +1,6·10⁻³ | 29,53059 j |
| Argument de latitude F | L − Ω | 13,421991215 | 13,421991147 | +2,4·10⁻³ | 27,21222 j |
| Anomalie M′ | L − ϖ | 13,255240737 | 13,255240891 | −5,5·10⁻³ | 27,55455 j |
| Porte-satellite de l’évection | 2Y − ϖ (différentiel) | 1,886935542 | 1,886935748 | −7,4·10⁻³ | 193,56368 j |

- Les engrenages décalent l’heure des syzygies, donc des éclipses, de 0,19 min par siècle.
- La comparaison de D avec Meeus contient aussi un petit désaccord des cibles entre elles : la Terre de DE441 et le Soleil de Meeus diffèrent d’environ 0,001°/siècle.

### 6.3 Les étages de la cascade (rapports exacts sur les porte-satellites)

| Étage (ordre de la cascade) | Porte-satellite | Rapports relatifs au porte-satellite | Terme produit |
|---|---|---|---|
| 1. Réduction à l’écliptique | Ω (porte-nœuds) | montée 2:1 (60:30), goupille et rainure, descente 1:2 (30:60) | −0,114° sin 2F |
| 2. Équation annuelle | — (différentiel) | gain 3/31 = ½ × 30:155 sur (λ☉ vrai − λ☉ moyen), retranché de la longitude de la Lune | −0,185° sin M |
| 3. Évection | 2λ☉ − ϖ (différentiel ; gains 80:20 et 40:20) | 1:1 | 1,274° sin(2D − M′) |
| 4. Anomalie (équant) | ϖ (périgée) | 1:1 | 6,289° sin M′ (+ 0,173° sin 2M′) |
| 5. Variation | Y (Soleil moyen) | montée 2:1 (60:30), goupille et rainure, descente 1:2 (30:60) | 0,658° sin 2D |
| Boule de phase | aiguille de la Lune | couronne 1:1 (48:48) menée par le tube du Soleil vrai | phase vraie |

Vitesses moyennes, exactes :
- la Lune vraie tourne en moyenne comme L ;
- la boule de phase tourne comme L − Y (la lunaison) ;
- le moteur de l’équation annuelle a une vitesse moyenne nulle.

Le gain de l’équation annuelle vise 0,185116/1,914602 = 0,096686 ; 3/31 = 0,096774, soit 0,09 % de 0,185°, environ 0,0002°.

## 7. Éclipses

| Sortie | Source | Cible (tours par année tropique) | Rapport du train (fraction) | Dents (menante:menée) | Erreur (ppm) | Erreur (°/siècle) | Période réalisée |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Saros (1 tour = 223 lunaisons) | roue de l’année Y | 0,055463078 | `273/4922` | 13:46 · 21:107 | 4,95·10⁻¹ | +9,9·10⁻⁴ | 6 585,32 j (18,030 a) |
| Exeligmos (1 tour = 3 Saros) | Saros | 0,018487693 | `1/3` | 20:60 | 4,95·10⁻¹ | +3,3·10⁻⁴ | 19 755,95 j (54,090 a) |

- La prédiction des éclipses n’utilise **aucun rapport de plus**. La coulisse écossaise est portée par le porte-nœuds Ω et menée par la goupille de l’unité d’anomalie : elle donne γ ∝ r·sin F (étude des mécanismes, § 5).
- Les aiguilles du Saros et de l’Exeligmos sont des compteurs de retour.
- Saros réalisé : 6 585,32 j (18,030 a), pour une cible de 6 585,32 j (18,030 a) (écart −281,614 s). Il part de la roue de l’année Y, en 2 couples. Depuis J, il faudrait trois couples (réduction de 1:6 585, proche de la limite 22³ = 10 648) ; depuis Y, le rapport n’est que 1:18.
- **Variante exacte** (option) :
  - un arbre synodique D = L − Y (différentiel), puis 20:223 et 10:200 ;
  - le rapport vaut alors exactement 1/223 de la lunaison de la machine ;
  - la roue de 223 dents sort de la règle des 220 dents. L’exception se justifie : 223 est premier, comme pour b1 dans la machine antique ;
  - écart à la cible : 3,52·10⁻³ ppm, celui de D.

## 8. Temps sidéral, équation du temps, précession

| Sortie | Source | Cible (tours par année tropique) | Rapport du train (fraction) | Dents (menante:menée) | Erreur (ppm) | Erreur (°/siècle) | Période réalisée |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Anneau du zodiaque tropique (précession) | Neptune | −0,000038810 | `-150/23449` | 10:131 · 15:179 (int.) | −5,68·10⁻¹ | +7,9·10⁻⁷ | 9 411 004,50 j (25 766,477 a) |
| Aiguille de l’EdT (×10) | EdT | — | `10` | 120:12 | exact | exact | — |
| Globe-tellurion (chaîne 1:1) | rotation stellaire | — | `1` | 40:40 | exact | exact | — |

- **Précession.** Période réalisée : 25 766,5 années tropiques, pour une cible de 25 766,5 ans. La cible est la pente moyenne de p_A sur 2000–2100 ; avec le seul terme linéaire, on aurait 25 771,6 ans. Écart relatif : −5,7·10⁻⁷.
  - Le train part de l’arbre de **Neptune**. Deux couples suffisent ainsi, au lieu de quatre depuis Y, car 25 766 > 22³ = 10 648.
  - Le dernier couple attaque la denture intérieure de l’anneau lui-même.

| Différentiel | Relation exacte (vitesses) | Gains des côtés | Rôle |
|---|---|---|---|
| Soleil moyen tropique X = Y + p (différentiel) | sun_trop = (1)·Y + (−1)·precession_ring | 40:20, −40:20 | Soleil moyen tropique (EdT, temps sidéral) |
| Rotation stellaire S = J + Y (différentiel ; mène le globe-tellurion) | stellar = (1)·J + (1)·Y | 40:20, 40:20 | globe-tellurion de l’orrery |
| Temps sidéral moyen (TSMG) = J + X (différentiel) | gmst = (1)·J + (1)·sun_trop | 40:20, 40:20 | aiguille du temps sidéral |
| Soleil vrai tropique λ + p (entrée du joint de Hooke) | lambda_trop = (1)·earth_true + (−1)·precession_ring | 40:20, −40:20 | entrée du joint de Hooke |
| Équation du temps EdT = X − α (différentiel ; vitesse moyenne nulle) | eot = (1)·sun_trop + (−1)·alpha_sun | 40:20, −40:20 | équation du temps |
| Lune : porte-satellite de l’évection 2λ☉ − ϖ (différentiel, sans nouveau rapport approché) | evection_carrier = (2)·Y + (−1)·moon_perigee | 80:20, −40:20 | porte-satellite de l’évection |
| Lune : moteur de l’équation annuelle (3/31)(λ☉ vrai − λ☉ moyen) (vitesse moyenne nulle) | annual_eq = (3/31)·earth_true + (−3/31)·Y | direct, −direct ; puis 30:155 | équation annuelle de la Lune |
| Anneau des dates (366 positions) = (croix principale + croix de saut)/61 | cal_sum = (1/61)·cal_cross_main + (1/61)·cal_cross_skip | direct, direct ; puis 20:61 · 20:200 | anneau des dates |
| Europe = 2·Ganymède + ν (différentiel) | europa = (2)·ganymede + (1)·nu | 80:20, 40:20 | Europe |
| Io = 2·Europe + ν (différentiel) | io = (2)·europa + (1)·nu | 80:20, 40:20 | Io |

Un différentiel conique donne ½(s₁ + s₂) sur son porte-satellite. Un gain 40:20 (×2) sur chaque côté donne donc s₁ + s₂, et un gain 80:20 (×4) donne 2s₁. Le signe « − » est obtenu par un pignon fou.

- **Temps sidéral.** TSMG = J + Y + p : c’est une identité exacte. Vitesse réalisée : 1,0027379093227 tr/j ; IERS : 1,0027379093450 tr/j. Écart : −0,070 s de temps sidéral par siècle, qui se décompose ainsi :
  - −0,090 s : erreur du train de Y ;
  - +0,074 s : la pente moyenne de p_A sur 2000–2100, au lieu de sa valeur J2000 ;
  - −0,054 s : écart entre l’année DE441 et l’année implicite de la formule IERS.
- *Variante* : un train direct depuis J, 197:164 · 151:148 · 18:22. Il donne +1,279 s par siècle sans différentiel. Mais il n’est plus lié au Soleil de la machine : l’écart avec l’aiguille du Soleil dériverait. On retient le différentiel, la solution de Schwilgué à Strasbourg.
- **Globe-tellurion.** S = J + Y. L’écart à l’ERA de l’IERS vaut −27,92 s par siècle, soit environ p_A(1 − cos ε) ≈ 417″ par siècle. Ce n’est pas une erreur d’engrenage : le globe a un axe fixe, alors que l’ERA est mesuré autour de l’axe réel, qui précesse. C’est invisible sur un globe.
- **Équation du temps.** EdT = X − α, où α sort du joint de Hooke. Le joint fait un tour par tour : la vitesse moyenne de l’EdT est donc **exactement nulle**, et l’aiguille ne dérive jamais. Un couple 120:12 l’agrandit ×10.
- *Option* : un plateau d’apsides de Mars, mené par l’anneau de précession par le couple 14:44. Période 80 980 ans, pour une cible de 81 101 ans. Il supprimerait la plus grande part de la dérive séculaire de Mars (0,33° à ±100 ans).

## 9. Les lunes galiléennes (jovicentriques, repère fixe)

| Sortie | Source | Cible (tours par année tropique) | Rapport du train (fraction) | Dents (menante:menée) | Erreur (ppm) | Erreur (°/siècle) | Période réalisée |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Ganymède | J | 51,050316016 | `9686/69299` | 167:131 · 10:23 · 29:115 | −1,25·10⁻⁴ | −2,3·10⁻⁴ | 7,15455 j |
| ν (ligne des conjonctions à −ν) | J | 0,750274744 | `2432/1183925` | 16:115 · 19:145 · 16:142 | −2,34·10⁻² | −6,3·10⁻⁴ | 486,81127 j |
| Callisto | J | 21,885181306 | `69615/1161806` | 51:122 · 35:89 · 39:107 | 3,20·10⁻³ | +2,5·10⁻³ | 16,68902 j |

| Lune | Formée par | Période sidérale réalisée | Cible (E5) | Erreur (°/siècle) | Période relative au bras de Jupiter de l’orrery |
|---|---|---|---|---|---|
| Io | 2·Europe + ν | 1,7691378 j | 1,7691378 j | −2,8·10⁻³ | 1,7698604 j |
| Europe | 2·Ganymède + ν | 3,5511810 j | 3,5511810 j | −1,1·10⁻³ | 3,5540940 j |
| Ganymède | train | 7,1545530 j | 7,1545530 j | −2,3·10⁻⁴ | 7,1663863 j |
| Callisto | train | 16,6890182 j | 16,6890182 j | +2,5·10⁻³ | 16,7535485 j |

- La relation de Laplace n_Io − 3n_Eu + 2n_Ga = 0 est **exacte par construction**, quels que soient les rapports des deux trains : (4Ga + 3ν) − 3(2Ga + ν) + 2Ga = 0.
- Les doubleurs des différentiels (80:20 et 40:20) sont exacts.
- La « ligne des conjonctions » se montre par une aiguille sur l’arbre ν renversé (1:1). Elle fait un tour rétrograde en 486,8 jours.
- Ces vitesses sont jovicentriques et sidérales, pour un cadran jovien fixe. Sur le bras de Jupiter de l’orrery, il faudrait retrancher la vitesse de Jupiter (dernière colonne). Ce serait exact avec une seconde boîte de Laplace au bout du bras ; cette option n’est pas retenue.

## 10. Bilan d’erreur complet

| Sortie | Erreur (ppm) | Erreur (°/siècle) | Années pour 1° | Allocation (°/siècle) | Commentaire |
|---|---|---|---|---|---|
| roue de l’année Y | −1,04·10⁻² | −3,8·10⁻⁴ | 2,7·10⁵ | 0,001 | se reporte sur toutes les planètes vues de la Terre |
| Mercure | −5,48·10⁻² | −8,2·10⁻³ | 1,2·10⁴ | 0,020 | pignon fou |
| Vénus | −1,48·10⁻² | −8,6·10⁻⁴ | 1,2·10⁵ | 0,020 |  |
| Mars | 3,15·10⁻¹ | +6,0·10⁻³ | 1,7·10⁴ | 0,020 |  |
| Jupiter | −7,30·10⁻¹ | −2,2·10⁻³ | 4,5·10⁴ | 0,020 |  |
| Saturne | 3,30 | +4,0·10⁻³ | 2,5·10⁴ | 0,020 |  |
| Uranus | 1,22·10¹ | +5,2·10⁻³ | 1,9·10⁴ | 0,020 |  |
| Neptune | −4,09·10¹ | −8,9·10⁻³ | 1,1·10⁴ | 0,020 |  |
| Lune L | 2,33·10⁻³ | +1,1·10⁻³ | 8,9·10⁴ | 0,010 |  |
| périgée ϖ | 1,64 | +6,7·10⁻³ | 1,5·10⁴ | 0,020 |  |
| nœuds Ω | 6,80·10⁻¹ | −1,3·10⁻³ | 7,6·10⁴ | 0,010 | pignon fou |
| Lune D | 3,52·10⁻³ | +1,6·10⁻³ | 6,4·10⁴ | — | L − Y |
| Lune F | 5,04·10⁻³ | +2,4·10⁻³ | 4,1·10⁴ | — | L − Ω |
| Lune M′ | −1,16·10⁻² | −5,5·10⁻³ | 1,8·10⁴ | — | L − ϖ |
| porte-satellite de l’évection | −1,09·10⁻¹ | −7,4·10⁻³ | 1,3·10⁴ | — | 2Y − ϖ |
| Ganymède | −1,25·10⁻⁴ | −2,3·10⁻⁴ | 4,4·10⁵ | 0,002 |  |
| ν | −2,34·10⁻² | −6,3·10⁻⁴ | 1,6·10⁵ | 0,002 |  |
| Europe | −3,00·10⁻⁴ | −1,1·10⁻³ | 9,0·10⁴ | — | 2·Ganymède + ν |
| Io | −3,81·10⁻⁴ | −2,8·10⁻³ | 3,5·10⁴ | — | 4·Ganymède + 3ν |
| Callisto | 3,20·10⁻³ | +2,5·10⁻³ | 4,0·10⁴ | 0,010 |  |
| Saros | 4,95·10⁻¹ | +9,9·10⁻⁴ | 1,0·10⁵ | — | compteur |
| anneau du zodiaque | −5,68·10⁻¹ | +7,9·10⁻⁷ | 1,3·10⁸ | — | erreur relative de la période |
| Temps sidéral (TSMG) | −2,22·10⁻⁵ | −0,070 s/siècle | — | 1 s/siècle | identité J + Y + p |

**Pour comparaison**, d’après l’étude des mécanismes et les constantes :
- la géométrie seule laisse 0,02 à 0,26° géocentriques sur 2000–2100 ;
- la Lune à 5 étages laisse 0,26° au maximum ;
- les perturbations hors Kepler valent 0,11° (Jupiter) et 0,17° (Saturne) ;
- les moyens mouvements cibles sont eux-mêmes incertains de 0,005 à 0,05°/siècle.

**Les engrenages ne sont nulle part le facteur limitant.**

### Vérifications (65/65 réussies)

| Vérification | Valeur | Limite | État |
|---|---|---|---|
| tâche : roue de l’année Y < 1°/siècle | −3,75·10⁻⁴ | ≤ 1 | ✅ |
| tâche : Mercure < 1°/siècle | −0,0082 | ≤ 1 | ✅ |
| tâche : Vénus < 1°/siècle | −8,64·10⁻⁴ | ≤ 1 | ✅ |
| tâche : Mars < 1°/siècle | 0,0060 | ≤ 1 | ✅ |
| tâche : Jupiter < 1°/siècle | −0,0022 | ≤ 1 | ✅ |
| tâche : Saturne < 1°/siècle | 0,0040 | ≤ 1 | ✅ |
| tâche : Uranus < 1°/siècle | 0,0052 | ≤ 1 | ✅ |
| tâche : Neptune < 1°/siècle | −0,0089 | ≤ 1 | ✅ |
| tâche : Lune L < 2°/siècle | 0,0011 | ≤ 2 | ✅ |
| tâche : Lune D < 2°/siècle | 0,0016 | ≤ 2 | ✅ |
| tâche : Lune F < 2°/siècle | 0,0024 | ≤ 2 | ✅ |
| tâche : Lune M′ < 2°/siècle | −0,0055 | ≤ 2 | ✅ |
| tâche : nœuds Ω < 2°/siècle | −0,0013 | ≤ 2 | ✅ |
| tâche : périgée ϖ < 2°/siècle | 0,0067 | ≤ 2 | ✅ |
| tâche : période de précession à 0,5 % près | −5,68·10⁻⁷ | ≤ 0,005 | ✅ |
| étude des mécanismes : roue de l’année Y ≤ 0,1°/siècle | −3,75·10⁻⁴ | ≤ 0,1 | ✅ |
| étude des mécanismes : Mars ≤ 0,1°/siècle | 0,0060 | ≤ 0,1 | ✅ |
| étude des mécanismes : Vénus ≤ 0,1°/siècle | −8,64·10⁻⁴ | ≤ 0,1 | ✅ |
| allocation : roue de l’année Y ≤ 0,001°/siècle | −3,75·10⁻⁴ | ≤ 0,001 | ✅ |
| allocation : Mercure ≤ 0,02°/siècle | −0,0082 | ≤ 0,02 | ✅ |
| allocation : Vénus ≤ 0,02°/siècle | −8,64·10⁻⁴ | ≤ 0,02 | ✅ |
| allocation : Mars ≤ 0,02°/siècle | 0,0060 | ≤ 0,02 | ✅ |
| allocation : Jupiter ≤ 0,02°/siècle | −0,0022 | ≤ 0,02 | ✅ |
| allocation : Saturne ≤ 0,02°/siècle | 0,0040 | ≤ 0,02 | ✅ |
| allocation : Uranus ≤ 0,02°/siècle | 0,0052 | ≤ 0,02 | ✅ |
| allocation : Neptune ≤ 0,02°/siècle | −0,0089 | ≤ 0,02 | ✅ |
| allocation : Lune L ≤ 0,01°/siècle | 0,0011 | ≤ 0,01 | ✅ |
| allocation : périgée ϖ ≤ 0,02°/siècle | 0,0067 | ≤ 0,02 | ✅ |
| allocation : nœuds Ω ≤ 0,01°/siècle | −0,0013 | ≤ 0,01 | ✅ |
| allocation : Ganymède ≤ 0,002°/siècle | −2,30·10⁻⁴ | ≤ 0,002 | ✅ |
| allocation : ν ≤ 0,002°/siècle | −6,32·10⁻⁴ | ≤ 0,002 | ✅ |
| allocation : Callisto ≤ 0,01°/siècle | 0,0025 | ≤ 0,01 | ✅ |
| géocentrique (engrenages seuls) : Mercure ≤ 0,1°/siècle | 0,0081 | ≤ 0,1 | ✅ |
| géocentrique (engrenages seuls) : Vénus ≤ 0,1°/siècle | 0,0039 | ≤ 0,1 | ✅ |
| géocentrique (engrenages seuls) : Mars ≤ 0,1°/siècle | 0,0239 | ≤ 0,1 | ✅ |
| géocentrique (engrenages seuls) : Jupiter ≤ 0,1°/siècle | 0,0029 | ≤ 0,1 | ✅ |
| géocentrique (engrenages seuls) : Saturne ≤ 0,1°/siècle | 0,0046 | ≤ 0,1 | ✅ |
| géocentrique (engrenages seuls) : Uranus ≤ 0,1°/siècle | 0,0056 | ≤ 0,1 | ✅ |
| géocentrique (engrenages seuls) : Neptune ≤ 0,1°/siècle | 0,0093 | ≤ 0,1 | ✅ |
| lunes galiléennes : Io ≤ 0,02°/siècle | −0,0028 | ≤ 0,02 | ✅ |
| lunes galiléennes : Europe ≤ 0,02°/siècle | −0,0011 | ≤ 0,02 | ✅ |
| temps sidéral ≤ 1 s/siècle | −0,0703 | ≤ 1 | ✅ |
| Saros ≤ 10⁻⁶ relatif | 4,95·10⁻⁷ | ≤ 1·10⁻⁶ | ✅ |
| Mercure ≤ 0,05°/siècle | −0,0082 | ≤ 0,05 | ✅ |
| identité : Io − 3·Europe + 2·Ganymède = 0 | 0 | = 0 | ✅ |
| identité : évection = 2Y − ϖ | 0 | = 0 | ✅ |
| identité : TSMG = J + Y + p | 0 | = 0 | ✅ |
| identité : vitesse moyenne de l’EdT = 0 | 0 | = 0 | ✅ |
| identité : vitesse moyenne de l’équation annuelle = 0 | 0 | = 0 | ✅ |
| exact : semaine = 1/7 tour par jour | 0 | = 0 | ✅ |
| exact : 146 097 jours = 20 871 semaines | 0 | = 0 | ✅ |
| exact : anneau des dates = 400/146 097 tour par jour (1 tour par année civile) | 0 | = 0 | ✅ |
| exact : roues-programmes 1/4, 1/100, 1/400 de l’anneau | 0 | = 0 | ✅ |
| exact : vitesse moyenne de l’aiguille géocentrique (Mercure) | 0 | = 0 | ✅ |
| exact : vitesse moyenne de l’aiguille géocentrique (Vénus) | 0 | = 0 | ✅ |
| exact : vitesse moyenne de l’aiguille géocentrique (Mars) | 0 | = 0 | ✅ |
| exact : vitesse moyenne de l’aiguille géocentrique (Jupiter) | 0 | = 0 | ✅ |
| exact : vitesse moyenne de l’aiguille géocentrique (Saturne) | 0 | = 0 | ✅ |
| exact : vitesse moyenne de l’aiguille géocentrique (Uranus) | 0 | = 0 | ✅ |
| exact : vitesse moyenne de l’aiguille géocentrique (Neptune) | 0 | = 0 | ✅ |
| exact : Exeligmos = Saros/3 | 0 | = 0 | ✅ |
| grégorien : années fausses 1582–6000 | 0 | = 0 | ✅ |
| grégorien jour par jour 1600–2400 (292 194 jours) : dates fausses | 0 | = 0 | ✅ |
| semaine jour par jour 1600–2400 : jours faux | 0 | = 0 | ✅ |
| dentures hors [10, 220] sans exception déclarée | 0 | = 0 | ✅ |

## 11. Inventaire et encombrement

| Poste | Nombre |
|---|---|
| Couples des trains approchés | 38 (76 roues) |
| Couples de rapport exact modélisés (semaine, calendrier, renvois, Exeligmos…) | 18 (36 roues) |
| Pignons fous de sens | 2 |
| Différentiels coniques, avec leurs couples de gain | 10 (78 roues) |
| Croix de Malte et leurs plateaux à goupille | 2 (4 pièces) |
| Renvois 1:1 non modélisés comme arbres : modules, aiguilles, cascade lunaire, cadran jovien (estimation) | ~87 roues |
| **Total estimé des roues dentées** | **~283** |

**Arbres partagés.** Chaque arbre source porte les premières roues menantes de plusieurs trains. Deux roues menantes de même denture et de même module peuvent n’en faire qu’une, qui engrène avec plusieurs roues disposées autour d’elle, comme b1 dans la machine antique :

| Arbre source | Premières roues menantes (dents → train) | Roues communes possibles |
|---|---|---|
| arbre-jour J | 10 → semaine, 31 → roue de l’année Y, 11 → Lune L, 167 → Ganymède, 16 → ν, 51 → Callisto | — |
| roue de l’année Y | 37 → Mercure, 124 → Vénus, 97 → Mars, 10 → Jupiter, 10 → Saturne, 10 → Uranus, 12 → Neptune, 47 → périgée ϖ, 12 → nœuds Ω, 13 → Saros | 10 dents : Jupiter, Saturne, Uranus ; 12 dents : Neptune, nœuds Ω |

Plus grandes roues :

| Arbre | Dents | Module (mm) | Diamètre primitif (mm) | Engrènement |
|---|---|---|---|---|
| anneau des dates | 200 | 0,90 | 180,0 | denture intérieure |
| anneau du zodiaque | 179 | 0,80 | 143,2 | denture intérieure |
| Vénus | 189 | 0,50 | 94,5 | extérieur |
| roue de l’année Y | 180 | 0,50 | 90,0 | extérieur |
| Ganymède | 167 | 0,50 | 83,5 | extérieur |
| Vénus | 166 | 0,50 | 83,0 | extérieur |
| équation annuelle (gain 3/31) | 155 | 0,50 | 77,5 | extérieur |
| Neptune | 148 | 0,50 | 74,0 | extérieur |

Ordre de grandeur :
- les roues ordinaires font au plus ~95 mm ;
- les deux anneaux du cadran avant font 143 et 180 mm.

C’est le format de la v1 (plaque de 176 × 300 mm), avec plus d’étages. L’implantation (plans, entraxes, empilement des tubes coaxiaux) reste à faire.

## 12. Fractions continues : la meilleure fraction n’est pas toujours taillable

Pour chaque train conçu, le tableau donne :
- le rapport visé r et ses premiers quotients partiels ;
- la première réduite (convergente) qui tient l’allocation, et si elle se taille en 1 à 3 couples de [10, 220] ;
- la fraction retenue p/q.

La dernière colonne divise l’erreur de la fraction retenue par celle de la meilleure fraction de dénominateur ≤ q (descente de Stern–Brocot). ×1 signifie que la fraction retenue est elle-même une meilleure approximation.

| Train | Rapport visé r | Fraction continue de r | 1ʳᵉ réduite dans l’allocation | Taillable ? | Fraction retenue | Erreur / meilleure erreur (dén. ≤ q) |
|---|---|---|---|---|---|---|
| roue de l’année Y | 0,0027378031 | [0; 365; 3; 1; 9; 13; 1; 3; …] | 511/186646 | non (facteur premier > 220 ou trop grand) | `589/215136` | ×5,28 |
| Mercure | 4,1520911168 | [4; 6; 1; 1; 2; 1; 4; 1; …] | 1092/263 | non (facteur premier > 220 ou trop grand) | `172864/41633` | ×6 369,33 |
| Vénus | 1,6255232018 | [1; 1; 1; 1; 2; 29; 2; 22; …] | 777/478 | non (facteur premier > 220 ou trop grand) | `20584/12663` | ×8,29 |
| Mars | 0,5316843245 | [0; 1; 1; 7; 2; 1; 1; 3; …] | 1913/3598 | non (facteur premier > 220 ou trop grand) | `3977/7480` | ×16,69 |
| Jupiter | 0,0842993239 | [0; 11; 1; 6; 3; 1; 2; 17; …] | 80/949 | oui (2 couples, ×2) | `80/949` | ×1,00 |
| Saturne | 0,0339609871 | [0; 29; 2; 4; 10; 1; 12; 1; …] | 92/2709 | oui (2 couples, ×3) | `110/3239` | ×13,73 |
| Uranus | 0,0119046161 | [0; 84; 971; 1; 5; 2; 2; 1; …] | 1/84 | oui (2 couples, ×100) | `1/84` | ×1,00 |
| Neptune | 0,0060675402 | [0; 164; 1; 4; 3; 3; 2; 1; …] | 16/2637 | non (facteur premier > 220 ou trop grand) | `11/1813` | ×1,00 |
| Lune L | 0,0366009949 | [0; 27; 3; 9; 5; 2; 1; 2; …] | 1685/46037 | non (facteur premier > 220 ou trop grand) | `4598/125625` | ×1,00 |
| périgée ϖ | 0,1129910307 | [0; 8; 1; 5; 1; 2; 9; 3; …] | 187/1655 | non (facteur premier > 220 ou trop grand) | `1222/10815` | ×35,45 |
| nœuds Ω | 0,0537656985 | [0; 18; 1; 1; 2; 50; 1; 4; …] | 252/4687 | oui (2 couples, ×1) | `252/4687` | ×1,00 |
| anneau du zodiaque | 0,0063968649 | [0; 156; 3; 16; 8; 1; 3; 8; …] | 3/469 | oui (2 couples, ×40) | `150/23449` | ×1,88 |
| Saros | 0,0554652306 | [0; 18; 34; 8; 1; 2; 1; 1; …] | 273/4922 | oui (2 couples, ×1) | `273/4922` | ×1,00 |
| Ganymède | 0,1397711367 | [0; 7; 6; 2; 7; 1; 10; 7; …] | 9686/69299 | oui (3 couples, ×5) | `9686/69299` | ×1,00 |
| ν | 0,0020541842 | [0; 486; 1; 4; 3; 2; 1; 4; …] | 249/121216 | non (facteur premier > 220 ou trop grand) | `2432/1183925` | ×163,04 |
| Callisto | 0,0599196422 | [0; 16; 1; 2; 4; 1; 1; 1; …] | 3952/65955 | non (facteur premier > 220 ou trop grand) | `69615/1161806` | ×413,17 |
| TSMG direct (variante) | 1,0027379093 | [1; 365; 4; 7; 1; 3; 99; 1; …] | 46879/46751 | non (facteur premier > 220 ou trop grand) | `267723/266992` | ×88,77 |
| apsides de Mars (option) | 0,3177093577 | [0; 3; 6; 1; 3; 1; 1; 25; …] | 7/22 | oui (1 couple, ×2) | `7/22` | ×1,00 |

**Combien de couples faut-il ?** Erreur du meilleur train à 1, 2 et 3 couples (roues jusqu’à 220 dents), en °/siècle. En gras : le train retenu, avec la taille maximale de ses roues.

| Train | 1 couple | 2 couples | 3 couples | Allocation |
|---|---|---|---|---|
| roue de l’année Y | impossible | 1,6 | **3,8·10⁻⁴** (roues ≤ 180) ; à 220 : 6,9·10⁻⁵ | 1·10⁻³ |
| Mercure | 3,0 | 2,8·10⁻² | **8,2·10⁻³** (roues ≤ 80) ; à 220 : 4,6·10⁻⁶ | 2·10⁻² |
| Vénus | 1,6·10¹ | **8,6·10⁻⁴** (roues ≤ 220) ; à 220 : 8,6·10⁻⁴ | 5,5·10⁻⁶ | 2·10⁻² |
| Mars | 8,3·10⁻¹ | **6,0·10⁻³** (roues ≤ 100) ; à 220 : 1,5·10⁻³ | 6,6·10⁻⁷ | 2·10⁻² |
| Jupiter | 1,1 | **2,2·10⁻³** (roues ≤ 80) ; à 220 : 1,6·10⁻⁴ | 1,6·10⁻⁸ | 2·10⁻² |
| Saturne | impossible | **4,0·10⁻³** (roues ≤ 80) ; à 220 : 5,4·10⁻⁴ | 8,0·10⁻⁸ | 2·10⁻² |
| Uranus | impossible | **5,2·10⁻³** (roues ≤ 100) ; à 220 : 4,4·10⁻³ | 1,7·10⁻⁷ | 2·10⁻² |
| Neptune | impossible | **8,9·10⁻³** (roues ≤ 150) ; à 220 : 4,3·10⁻⁴ | 1,3·10⁻⁷ | 2·10⁻² |
| Lune L | impossible | 8,8·10⁻² | **1,1·10⁻³** (roues ≤ 80) ; à 220 : 7,1·10⁻⁵ | 1·10⁻² |
| périgée ϖ | 1,2·10⁻¹ | **6,7·10⁻³** (roues ≤ 120) ; à 220 : 4,3·10⁻⁴ | 3,6·10⁻⁸ | 2·10⁻² |
| nœuds Ω | 8,1·10⁻² | **1,3·10⁻³** (roues ≤ 120) ; à 220 : 2,5·10⁻⁵ | 8,6·10⁻⁸ | 1·10⁻² |
| anneau du zodiaque | impossible | **7,9·10⁻⁷** (roues ≤ 180) ; à 220 : 7,9·10⁻⁷ | 4,6·10⁻⁹ | 1·10⁻⁴ |
| Saros | 3,3 | **9,9·10⁻⁴** (roues ≤ 120) ; à 220 : 3,1·10⁻⁵ | 1,1·10⁻⁶ | 2·10⁻³ |
| Ganymède | 1,8·10² | 1,8·10⁻¹ | **2,3·10⁻⁴** (roues ≤ 180) ; à 220 : 2,3·10⁻⁴ | 2·10⁻³ |
| ν | impossible | 1,6·10² | **6,3·10⁻⁴** (roues ≤ 150) ; à 220 : 2,9·10⁻⁴ | 2·10⁻³ |
| Callisto | 1,6·10² | 1,0·10⁻¹ | **2,5·10⁻³** (roues ≤ 150) ; à 220 : 4,5·10⁻⁴ | 1·10⁻² |
| apsides de Mars (option) | **6,6·10⁻⁴** (roues ≤ 60) ; à 220 : 1,4·10⁻⁶ | 5,6·10⁻⁸ | 7,8·10⁻¹¹ | 4·10⁻³ |

« impossible » : le rapport sort de l’intervalle qu’un seul couple de 10 à 220 dents peut donner (1:22 à 22:1). Le retenu n’est pas toujours le plus précis : c’est le plus petit nombre de couples qui tient la moitié de l’allocation, avec les plus petites roues.

Comment lire ce tableau :
- Les réduites successives sont les fractions de Huygens (1682). À dénominateur donné, elles sont les meilleures possibles.
- Mais leurs facteurs premiers dépassent souvent 220 : un nombre premier de 223 ou plus ne se taille pas.
- La recherche exhaustive trouve des rapports moins « optimaux » au sens de Stern–Brocot, mais taillables, et encore bien plus précis que nécessaire.

## 13. Candidats aux preuves Lean 4

**Tous les rapports sont candidats**, car ce sont des fractions exactes. La méthode de la v1 s’applique : `Kinematics.lean` et `Targets.lean` y sont générés depuis la spec. Il y a quatre familles d’énoncés :

1. **Rapports de trains**, un énoncé par arbre : ω_sortie = ± Π menantes / Π menées · ω_source. On en déduit la vitesse par rapport à J par `norm_num`. Exemple : `ω Y = (31·19·10 / 180·144·83) · ω J`, soit ω Y = 589/215136 · ω J.
2. **Bornes d’erreur** : |ω − cible| · 360 · 36 525 < borne. La cible est la décimale exacte de `constants.json` ; la preuve est un `norm_num` sur des rationnels.
3. **Identités exactes par construction** :
   - Laplace : Io − 3·Europe + 2·Ganymède = 0 ;
   - évection = 2Y − ϖ ; TSMG = J + Y + p ;
   - vitesse moyenne nulle de l’EdT et de l’équation annuelle ;
   - Exeligmos = Saros/3 ; anneau des dates = 400/146 097 tr/j ;
   - vitesse moyenne des aiguilles géocentriques = celle de la planète ou du Soleil.
4. **Logique grégorienne** : `decide` sur les 400 cas, plus la périodicité de 400 ans des trois cames ; et 146 097 = 7 · 20 871.

`trains.json` → `lean_candidates` en contient 98 : 36 rapports, 34 identités et vitesses moyennes, 26 bornes, 2 énoncés décidables.

Vitesses exactes des arbres approchés par rapport à J (tours par jour) :

| Arbre | Vitesse exacte (tr/j) | Cible (°/siècle ; fraction exacte dans `trains.json`) | Machine (°/siècle) |
|---|---|---|---|
| roue de l’année Y | `589/215136` | 35 999,372865 | 35 999,372490 |
| Mercure | `102638/9028989` | 149 472,674726 | 149 472,666541 |
| Vénus | `18259/4102812` | 58 517,815231 | 58 517,814367 |
| Mars | `2342453/1609217280` | 19 140,302044 | 19 140,308074 |
| Jupiter | `2945/12760254` | 3 034,722762 | 3 034,720547 |
| Saturne | `32395/348412752` | 1 222,574226 | 1 222,578257 |
| Uranus | `589/18071424` | 428,558709 | 428,563958 |
| Neptune | `6479/390041568` | 218,427640 | 218,418697 |
| Lune L | `4598/125625` | 481 266,482463 | 481 266,483582 |
| périgée ϖ | `359879/1163347920` | 4 067,606201 | 4 067,612869 |
| nœuds Ω | `-4123/28009512` | −1 935,531406 | −1 935,532722 |
| anneau du zodiaque | `-161975/1524347454672` | −1,397195 | −1,397194 |
| Saros | `53599/352966464` | 1 996,713496 | 1 996,714484 |
| Ganymède | `9686/69299` | 1 837 850,676286 | 1 837 850,676056 |
| ν | `2432/1183925` | 27 010,468356 | 27 010,467724 |
| Callisto | `69615/1161806` | 787 883,374740 | 787 883,377259 |

## 14. Questions ouvertes

- **Manivelle rapide.** Une manivelle sur Y (1 tour = 1 an) entraîne J à ×365 à travers trois couples, ainsi que les croix de Malte et la boîte de Laplace (Io : 206 tours par tour de manivelle). C’est cinématiquement exact, mais le couple et l’usure sont à étudier. Alternatives : la manivelle sur W seulement (1 tour = 1 semaine), ou un débrayage du calendrier et des lunes galiléennes en marche rapide, qu’il faudrait alors recaler.
- **Saros : 223 dents ou pas ?** La machine de base suit la règle des 220 dents : 2 couples depuis la roue de l’année Y, à 4,9·10⁻⁷ près. La variante exacte demande une roue de 223 dents et un différentiel de plus (arbre synodique) ; elle rend hommage à b1.
- **Fenêtre des cibles.** Toutes les cibles sont des pentes moyennes sur 2000–2100. L’écart entre jeux d’éléments va jusqu’à 0,46°/siècle (Saturne, selon la fenêtre), soit 50 à 1 000 fois les erreurs d’engrenage. Changer de fenêtre change donc les cibles, pas la conclusion ; il faudrait seulement relancer la recherche (quelques secondes).
- **Modules et place.** Les modules (0,5 mm ; anneaux 0,8–0,9 mm) et les entraxes sont indicatifs. Les roues de 10 dents demandent un déport de denture ou un angle de pression de 25 à 30°, comme dans la v1.
- **Sens des différentiels.** Les relations sont écrites en vitesses signées. Le sens physique de chaque entrée (et donc les pignons fous éventuels) se fixera à l’implantation.
- **Plateau d’apsides de Mars.** L’option est chiffrée (§ 8). La machine de base garde le réglage séculaire à la main.
- **Lunes galiléennes sur l’orrery.** La machine de base les montre sur un cadran jovien fixe. Les montrer autour de la Jupiter du couvercle demanderait une seconde boîte de Laplace au bout du bras.

## 15. Reproduire

```
BPY=/Applications/Blender.app/Contents/Resources/5.2/python/bin/python3.13
$BPY ~/antikythera/v2/tools/trains.py           # recherche, vérification et écriture (quelques secondes)
$BPY ~/antikythera/v2/tools/trains.py --check   # revérifie spec/trains.json à partir des seules dentures
```

