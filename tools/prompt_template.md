# PROMPT MAÎTRE : mécanisme d'Anticythère fonctionnel dans Blender 5.2 (exécution en une seule fois)

> Donne ce prompt tel quel à une session Claude Code neuve (Opus 5.5), lancée dans un **dossier vide**.
> Il contient tout : mission, règles, décisions, formules, pièges connus et la spécification complète déjà
> vérifiée (§12). Aucune autre source n'est nécessaire, et internet n'est pas utilisé.

---

## 0. Mission

Dans le dossier courant, construis un projet qui :

1. charge la spécification JSON du §12, source de vérité unique ;
2. **démontre mathématiquement** en fractions exactes que chaque train d'engrenages reproduit son cycle
   astronomique et que le mécanisme a exactement **un degré de liberté** (la manivelle) ;
3. génère la géométrie 3D de toutes les pièces : 69 engrenages à développante conjugués, arbres, tubes,
   plaques, piliers, tenons-rainures, leviers suiveurs, cadrans avant et arrière, boîtier ;
4. assemble le tout dans **Blender 5.2** avec une manivelle unique qui anime chaque pièce par des drivers ;
5. **vérifie physiquement** qu'aucune pièce ne pénètre une autre sur toute la plage de mouvement ;
6. exporte les pièces pour l'impression 3D, rend des images et une animation, et produit un rapport de vérification.

Le travail est terminé lorsque **tous les livrables du §10 existent** et que chaque critère du §9 est **vert**, ou
marqué ROUGE avec son diagnostic selon la règle « Fin de session et priorités » du §1.

## 1. Règles de travail (non négociables)

- Travaille uniquement dans le dossier courant. Pas d'internet. N'installe rien (pas de pip, brew ni
  extension Blender). Ne modifie pas `/Applications/Blender.app`.
- **Ne pose aucune question** et n'attends aucune validation : tout est décidé ici. Si un détail n'est pas
  spécifié, choisis l'option la plus simple compatible avec la spec et note-la dans `DECISIONS.md`
  (une ligne : décision, raison).
- **La spec est intangible** : ne change aucune valeur. Si un contrôle échoue à cause d'une donnée de la
  spec, n'affaiblis pas le contrôle : applique le repli prévu au §8, sinon signale le problème en tête du rapport.
- N'affaiblis jamais un test ni une tolérance pour le faire passer. Seules les tolérances du §9 s'appliquent.
- Avance étape par étape (§7). À chaque point de contrôle, lance les commandes indiquées et corrige jusqu'au
  vert avant de continuer. Tiens `PROGRESS.md` à jour (étape, état, durée, problèmes et correctifs).
- Toute commande Blender tourne en arrière-plan avec un code de sortie :
  `"$BL" -b --factory-startup --python-exit-code 1 -P script.py -- args`. Journaux dans `out/logs/`.
- Une commande shell ne doit pas dépasser environ 9 minutes : découpe les rendus et les longues
  vérifications (plages de frames, lots d'échantillons), ou lance-les en arrière-plan et surveille leur fin.
- Le paquet `am/` n'importe **jamais** `bpy` ni `mathutils` : il doit être testable hors de Blender. Seuls
  les scripts de `blender_scripts/` touchent à Blender. Pas de dépendance hors bibliothèque standard et numpy.
- **Fin de session et priorités.** Si, après les replis du §8, un critère reste rouge à cause de la spec,
  marque-le ROUGE avec son diagnostic en tête du rapport et passe à l'étape suivante. La session se termine
  quand tous les livrables existent. Ordre de priorité si le temps manque : (1) étapes 0 à 3, (2) étapes 4
  et 5 avec `out/am.blend` animé, (3) rapport, (4) étape 6, (5) impression, (6) rendus Cycles, (7) animation.

## 2. Environnement (vérifié sur cette machine)

```sh
PY=/Applications/Blender.app/Contents/Resources/5.2/python/bin/python3.13   # 3.13.13, numpy 2.3.4, tomllib, fastjsonschema, unittest
BL=/Applications/Blender.app/Contents/MacOS/Blender                         # Blender 5.2.2 LTS
```

- N'utilise **jamais** `/usr/bin/python3` (3.9, sans numpy). Pas de scipy, pytest ni shapely.
- Mac Apple M4, 16 Go ; GPU Metal listé « Apple M4 (GPU - 8 cores) ».

## 3. Le mécanisme en bref (ce que modélise la spec)

- Une **manivelle** latérale tourne l'arbre `a` (axe horizontal +x). Sa couronne **a1** (48 dents) entraîne la
  grande roue **b1** (223 dents) : **1 tour de b1 = 1 année**. Toutes les vitesses sont en tours par an.
- **Trains arrière**, derrière la plaque principale :
  - **Lune** : b2→c→d→e2/e5→k1, puis un **tenon-rainure** k1⇢k2 porté par le plateau tournant **e3**, puis
    k2→e6/e1→b3. Le résultat est la Lune moyenne 254/19 plus l'anomalie d'Hipparque.
  - **Métonique / Olympiade / Callippique** : b2→l→m→n→(o, p→cal).
  - **Saros / Exeligmos** : m3→e3/e4→f→g→h→i.
  - Les deux chemins partis de b2 se rejoignent sur e3 : c'est un vrai différentiel.
- **Trains avant** (modèle Freeth 2021, en grande partie **hypothétiques**) :
  - sur b1 : nœuds (main du dragon), Mercure et Vénus. Ce sont des épicycles portés par b1 qui engrènent
    des roues fixes. Un tenon sur chaque épicycle entraîne un **levier suiveur** monté sur l'axe central ;
  - sur la plaque **CP**, qui tourne avec b1 : Soleil vrai (excentrique + levier) et planètes supérieures
    (Mars, Jupiter, Saturne), chacune avec un tenon-rainure et une roue de sortie sur l'axe central.
- **Sorties** :
  - à l'avant, des tubes concentriques portent des anneaux planétaires, l'aiguille lunaire avec sa sphère
    de phase (différentiel b0/q1), l'aiguille de date et la main du dragon ;
  - à l'arrière, deux spirales (Métonique 5 tours / 235 cases, Saros 4 tours / 223 cases) suivies par des
    aiguilles à coulisseau, plus trois cadrans secondaires.
- Chaque pièce a un **statut** : `SURVIVING`, `RECONSTRUCTED` ou `HYPOTHETICAL`. Il est conservé partout :
  propriétés, collections, couleurs de débogage, rapport.

## 4. Décisions déjà tranchées (ne pas les rediscuter)

1. **Unités** : 1 unité Blender = 1 mm (`unit_settings.system='METRIC'`, `length_unit='MILLIMETERS'`,
   `scale_length=0.001`). `scale_length` est stocké en float32 : compare avec `math.isclose(x, 0.001, rel_tol=1e-6)`,
   jamais `==`. Caméras : `clip_start = 1.0`, `clip_end = 10000.0`. Repère et signes : voir `conventions` dans la
   spec. Taux positif = sens horaire vu de face.
2. **Profil de dent** : développante à **30°**, saillie 1·m, creux 1,25·m, congé de pied 0,2·m, sans
   déport. Jeu **uniquement par amincissement des dents** (0,03 mm pour le modèle savant), **jamais** en
   déplaçant les axes. Modules, positions d'axes et plages Z : ceux de la spec, sans modification.
3. **Couronnes** a1/b1 et b0/q1 : dents **déjà calculées par enveloppe** et vérifiées (spec `crowns`), à
   construire telles quelles (§5.6).
4. **Mouvement** : un Empty `AM_Controller` porte `ctl['crank'] = 0.0` (années) et `ctl['patina'] = 0.0`,
   écrits en **littéraux flottants** : avec `= 0`, la propriété serait entière et l'animation sauterait par
   années entières. Vérifie `type(ctl['crank']) is float` avant `keyframe_insert`, et applique
   `ctl.id_properties_ui('patina').update(min=0.0, max=1.0)`. Chaque corps est un Empty `B_<id>` dont la
   rotation est pilotée par un driver en **expression simple** : pas de fonction Python, pour que le fichier
   s'anime sans autorisation de scripts. **Pas de physique rigide** (Bullet) : elle ne peut pas reproduire
   des rapports exacts.
5. **Hiérarchie** : chaque pièce est un objet enfant de l'Empty de son corps, modélisé en coordonnées
   locales du corps. Les corps dont le parent est `b` ou `e_table` sont enfants de `B_b` ou de
   `B_e_table`. `matrix_parent_inverse` est l'identité partout. La position de l'Empty vaut
   `axis_xy_in_parent` dans le repère du parent. Tous les Empties sont à z = 0, sauf `B_a` (z = axe de a1)
   et `B_q` (z = 52,70 dans `B_moon`).
6. **Collections** : `AM_SURVIVING`, `AM_RECONSTRUCTED`, `AM_HYPOTHETICAL` pour les engrenages et pièces
   à statut ; `AM_STRUCTURE`, `AM_DIALS`, `AM_CASE`, `AM_HELPERS` (Empties). Propriétés personnalisées sur
   chaque objet : `status`, `role`, `teeth`, `module`, `body`, `sources`.
7. **Matériaux** : bronze PBR avec un mélange de patine piloté par `AM_Controller["patina"]` (0 = neuf,
   1 = musée), bois pour le boîtier. `obj.color` = couleur de statut, pour un affichage de débogage en
   Solid/Object.
8. **Incertitudes** : on applique les valeurs par défaut de la spec (`unresolved_defaults`). Le rapport les liste.

## 5. Formules (exactes, à implémenter telles quelles)

### 5.1 Angles et taux
- Angle d'un corps (convention mathématique, sens trigonométrique autour de son axe, relatif à son parent) :
  **θ(t) = −2π · rate_rel_parent · t** pour un corps linéaire, t en années.
- **Willis**, pour un engrènement extérieur de g1 (corps B1) et g2 (corps B2) sur le porteur C :
  z1·(w1 − wC) = −z2·(w2 − wC).
- Le solveur `am/kinematics.py` reconstruit **tous** les taux moyens par élimination de Gauss exacte
  (`fractions.Fraction`) :
  - inconnues : les **45 corps mobiles** hors `frame`, `a` et `q` ;
  - **44 équations** : 37 engrènements extérieurs (Willis), 4 tenons-rainures (taux moyen de la roue à rainure
    = taux moyen de la roue à tenon), 3 suiveurs (taux moyen du suiveur = taux de `b`, car d < i) ;
  - entrée : taux de `b` = 1.
  Il doit trouver : rang 44 (**DDL = 1**), aucune contrainte incohérente, des taux égaux à
  `bodies[].rate_abs_mean`, et **toutes** les `targets`. Deux cibles sont hors solveur et comparées en valeur
  absolue : `a` = 223/48 (définition) et `q@moon` = |w_b − w_moon| = 235/19.

### 5.2 Angles de chaque corps (à utiliser pour les drivers et le solveur)
{{BODY_TABLE}}

Détails :
- **Tenon-rainure** : θ_rainure = θ_tenon + atan2(e·sin(θ_tenon − β), r − e·cos(θ_tenon − β)). Les angles
  sont relatifs au porteur ; e = excentricité, r = rayon du tenon, β = `offset_dir_local_deg` en radians. La
  fonction est continue car e < r, et son taux moyen égale celui du tenon.
- **Suiveur** : θ_F = θ_b + γ0 + atan2(d·sin λ, i + d·cos λ), avec γ0 = atan2 de `epicycle_axis_xy_in_b`
  (λ : voir ci-dessous). Le levier (local +x) pointe alors toujours vers le tenon.
- **Phase lunaire** : `B_q` tourne autour de son X local (radial, le long de l'aiguille lunaire), par rapport
  à `B_moon`, de **θ_q = θ_b − θ_moon**, avec les angles monde en z. Loi **non linéaire**, car la Lune porte
  l'anomalie ; taux moyen +235/19 ; θ_q(0) = −0,0773916 rad. Driver : `-2*pi*fmod(c,1) - m`, où `m` est une
  variable `SINGLE_PROP` sur `B_moon.rotation_euler[2]`. N'utilise **jamais** la forme linéaire : les dents de
  q1 dériveraient jusqu'à 11° contre celles de b0.
- **Manivelle** : `B_a` tourne autour de X : **−2π·(223/48)·t**.
- Les valeurs du tableau sont arrondies pour la lecture. **Toutes les constantes** (axes, i, d, γ0, e, r, β,
  phases des tenons) se lisent dans le JSON en float64.
- **Suiveur (précision)** : λ = θ_épicycle_local + φ_t − γ0, avec φ_t = `followers[].pin_phase_deg` en
  radians (0 pour Mercure et Vénus, 84,5° pour le Soleil vrai). Le tenon est à l'angle local φ_t de son épicycle.
- Dans les drivers, garde les angles petits : `fmod(c*N/D, 1)` avant de multiplier par 2π, avec des fractions
  entières exactes. Pour composer un corps non linéaire, lis la rotation locale d'un autre Empty par une
  variable `SINGLE_PROP` sur `rotation_euler[2]` (ou `[0]` pour les axes X). Ne réinjecte **jamais** un angle
  modulé dans un rapport : les rapports utilisent toujours `c`.

### 5.3 Phasage des dents au montage
Pour chaque engrènement extérieur, calculé à t = 0 avec les angles réels des corps (non nuls pour les corps
non linéaires) : soit β12 l'angle de la ligne des centres de l'axe 1 vers l'axe 2 dans le repère du porteur,
φ1 l'angle monde de la dent 0 de g1 (angle du corps + décalage de phase de g1). Alors la dent 0 de g2 doit être
à φ2 = β12 + π + π/z2 − (z1/z2)·(φ1 − β12). Intègre ce décalage de phase dans le maillage de g2. Le graphe
des engrènements extérieurs a 28 composantes (b1 n'engrène que la couronne a1). Dans chacune, donne la phase 0
à une roue racine (la première roue de la composante rencontrée dans `meshes`), puis propage le long de
l'arbre. Deux roues d'un même corps ont des décalages indépendants. Vérifie ensuite chaque paire par le contrôle 2D du §5.8. Les couronnes a1 et q1 sont **déjà
phasées** dans leurs grilles d'enveloppe : la dent 0 est centrée en φ = π/48 (a1) ou π/20 (q1), face à la dent
0 de b1 ou b0, quand l'angle relatif est nul (a1 : θ_a = 0 ; q1 : θ_q = θ_b − θ_moon = 0). Construis les dents aux
φ de la grille **sans aucun décalage**. À t = 0, θ_q(0) = −0,0774 rad est porté par la rotation de `B_q`, et la
dent 0 de b0 est au même angle dans le repère Lune. b1 et b0 gardent leur dent 0 à l'angle local 0.

### 5.4 Profil à développante (numpy, float64)
r = m·z/2 ; rb = r·cos α ; ra = r + m ; rf = r − 1,25·m ; inv(x) = tan x − x.
Demi-angle de dent au rayon ρ ≥ rb : ψ(ρ) = π/(2z) + inv(α) − inv(arccos(rb/ρ)) − j/(4r), où j est le jeu
circonférentiel. Flancs de la dent k (centre θk = 2πk/z + phase) : ρ·(cos(θk ± ψ(ρ)), sin(θk ± ψ(ρ))), avec
ρ de max(rb, rf) à ra, **au moins 24 points par flanc**. Si rf < rb (z < 19 à 30°), prolonge radialement
de rb à rf. Arc de tête à ra, arc de pied à rf, congé ≈ 0,2·m. Retire les points consécutifs confondus
(tolérance 1e-9) : `me.validate()` ne les fusionne pas.
- **Largeur en tête** (`tooth.tip_land_rule`) : ≥ 0,2·m sur le profil **nominal** (j = 0) ; sur les profils
  amincis, > 0, valeur seulement rapportée.
- **Évidements** : suis exactement `tooth.lightening`. Pas de fenêtres pour les roues à tenon ou à rainure ;
  e3 a un bras vers K ; pour **b1**, les 4 rayons A/B/C/D de `b1_structure` ; **e4** est un anneau.
- **Alésage** de chaque roue : `gears[].bore_radius`. Une roue `fused` fait partie du corps de son arbre ; une
  roue `rides_on` tourne sur un support d'un autre corps avec 0,05 mm de jeu. Arbres, goujons, bossages, moyeux
  et tenons : exactement la table `shafts` (rayons et plages Z).
- **Cercles avec jeu** (alésages, trous, goujons, bossages, tubes) : polygones de
  n ≥ max(64, ⌈π/acos(R/(R+g))⌉ + 8) côtés, avec le même n pour l'alésage et l'arbre.

### 5.5 Maillages dans Blender
Extrude les contours 2D (extérieur + trous) entre z0 et z1. Triangule chaque face plane avec
`mathutils.geometry.delaunay_2d_cdt(pts2d, [], [boucle_ext, trou1, …], 3, 1e-9)` (output_type 3 : triangles
intérieurs, trous retirés). **N'utilise pas `tessellate_polygon`**, faux sur ces contours (§11). Contrôle : aucun
sommet ajouté (sinon le contour se recoupe : corrige-le), n + 2·(nombre de trous) − 2 triangles, aucune arête
partagée par plus de 2 triangles. Remplis ensuite `vertices`, `loops` et `polygons` avec `foreach_set` (pas de
`from_pydata` ni de bmesh dent par dent). Ensuite `me.validate()`,
`me.shade_smooth()`, `me.set_sharp_from_angle(angle=radians(30))`. **Orientation** : le contour extérieur en
sens trigonométrique, chaque trou en sens horaire (aire signée), parois générées dans ce sens. Chaque maillage
doit être **fermé, variété, orienté de façon cohérente** : aucune arête bmesh avec
`is_manifold and not is_contiguous`. Son volume, calculé en float64 sur les sommets relus, doit valoir
aire du contour × (float32(z1) − float32(z0)) à 1e-6 près (relatif), avec float32(z) = `float(numpy.float32(z))`
(les sommets sont stockés en float32). Pas de modificateur booléen sur la géométrie vérifiée.

### 5.6 Couronnes (contrates) : dents précalculées par enveloppe
Les dents de a1 et q1 sont **fournies** dans `crowns.a1.envelope` et `crowns.q1.envelope`. Ce sont des grilles
(s, ρ, φ_lo, φ_hi) calculées comme la région que les dents de b1 ou b0 (jeu 0,03 et marge 0,04 par flanc) ne
balaient jamais. Elles ont été vérifiées dans Blender 5.2.2 : **0 recouvrement BVH** sur 60 positions par pas, et
un jeu minimal de 0,013 à 0,041 mm à chaque position, donc un engrènement continu. **Ne les recalcule pas.**
Construis chaque dent selon `crowns.mesh_rule`, répète-la z fois (φ += k·2π/z), et ajoute le disque, l'arbre, la
manivelle (a1), l'arbre radial, les supports et la sphère de phase (q1) aux cotes du bloc `crowns`. Les dents
pénètrent le disque de 0,05 mm : ce sont des coques fermées séparées dans le même objet (même corps), et le
contrôle de variété se fait par coque. Repères : a1, s = x monde et φ autour de +x depuis −z vers +y ; q1, s = u
du repère Lune et φ autour de +u depuis −z vers +v.

### 5.7 Spirales arrière et coulisseaux
Repère arrière (u, v) = (−x, y). ψ = angle du corps n (Métonique) ou g (Saros), positif = sens horaire vu de
l'arrière = +θ en convention monde. On a k = floor(ψ/2π), φ = ψ − 2πk, R_k = r_start + k·pitch,
δ = pitch/2. Si φ < π, ρ = R_k. Sinon ρ = δ·cos φ + sqrt((R_k + δ)² − δ²·sin²φ). Le deuxième centre est au
centre du cadran + (0, +δ) en (u, v). La rainure (largeur 1,2) est taillée dans la plaque arrière le long de
cette spirale, pour ψ de 0 à tours·2π, avec des **extrémités rondes** (r 0,6) centrées sur les points
ψ = 0 et ψ = tours·2π. Les cases sont des traits radiaux entre les tours : 47 par tour pour le Métonique, 223
sur 4 tours pour le Saros. Le coulisseau (tenon r 0,5, appartenant au corps n ou g de son aiguille) glisse le
long du +y local de l'aiguille. Sa position `location.y` est pilotée par un driver qui calcule ψ_mod
**directement depuis c**, jamais depuis la rotation modulée de l'aiguille :
- Métonique : `10*pi*fmod(fmod(c/19,1)+1,1)` ;
- Saros : `8*pi*fmod(fmod(c*235/4237,1)+1,1)`.
La F-curve de ce driver est une **table de correspondance** ψ→ρ : ≥ 1800 clés, interpolation LINEAR. Vide
d'abord les 2 clés par défaut avec `fc.keyframe_points.clear()`.

### 5.8 Contrôles géométriques 2D (dans `am/`)
- Rapport de conduite ε = (√(ra1² − rb1²) + √(ra2² − rb2²) − a·sin α) / (π·m·cos α) ≥ 1,2.
- Interférence 2D d'une paire : 50 positions relatives sur un pas de dent. Distance signée minimale entre
  contours ≥ 0 (aucune pénétration), et jeu mesuré dans [0,4·j ; 3·j] près de la ligne des centres.
- **Pré-filtre de collisions.** Objets : roues (anneau alésage→tête), tubes, arbres, goujons, bossages et
  moyeux (`shafts.items`), tenons (anneau balayé autour de l'axe de leur corps), piliers, disques, leviers,
  anneaux, marqueurs, aiguilles et plaques. Pour chaque paire d'objets de **corps différents** dont les plages Z
  se recouvrent, compare les régions balayées :
  - porteur `b` (tout ce qui en dépend) : anneau autour de (0,0) ;
  - porteur `e_table` : anneau autour de E ;
  - repère fixe : cercle statique ;
  - deux objets rigides du même porteur : positions réelles ;
  - objets coaxiaux : intervalles radiaux, avec un jeu ≥ 0,04 (palier) ; sinon jeu ≥ 0,15 ;
  - leviers suiveurs : seuls comptent les objets de `b` dans leur secteur (`layers.swing_sectors`).
  **Contacts voulus**, exclus du comptage du pré-filtre mais testés au BVH : paires de `meshes` ; tenon ↔ sa
  rainure (`shafts.pins[].slot_in`) ; arbres, tubes et tenons ↔ plaques traversées (trous de jeu r + 0,05). Les
  objets d'un **même corps** ne sont ni comptés ni testés. **Paires retenues** (pour le BVH §5.9 c) : objets de
  corps différents dont les plages Z se recouvrent ou sont à moins de 0,1 mm, et dont les régions balayées sont
  à moins de 0,5 mm, contacts voulus compris.
- **Cosmos** (contrôle de sens) : élongation de Mercure, Vénus et du Soleil vrai par rapport au Soleil moyen
  dans ±asin(d/i) ; rétrogradation de Mars, Jupiter et Saturne à l'opposition (180 ± 1°) ; apogée solaire à la
  longitude 65,5 ± 0,5° ; amplitude de l'anomalie lunaire de 6,58° ; chaque tenon toujours dans sa rainure.
  Longitude affichée = −(θ_corps + marker_local_deg), le zodiaque croissant dans le sens horaire vu de face.

### 5.9 Contrôles 3D dans Blender (`check.py`)
- Pour chaque échantillon v, stocke une valeur **exactement représentable en float32** :
  `c = float(numpy.float32(v)); ctl['crank'] = c`, puis `ctl.update_tag()` et `view_layer.update()`. La
  propriété est un double mais le driver la lit en float32 ; compare au solveur évalué en c.
  Construis les BVH en **coordonnées monde** : sommets × `matrix_world` dans numpy, puis
  `BVHTree.FromPolygons(verts, tris, all_triangles=True)`. `overlap()` doit renvoyer une **liste vide**.
- Échantillonnage : (a) chaque engrènement, 50 positions sur un pas de dent ; (b) chaque tenon-rainure et
  chaque suiveur, 72 positions sur un cycle relatif complet ; (c) toutes les paires retenues par le
  pré-filtre, 240 valeurs de manivelle (120 uniformes sur [0, 1] an et 120 tirées au hasard sur [0, 76],
  graine 20260924). « Paires retenues » est défini au §5.8.
- Paires exclues : uniquement les objets d'un **même corps**, et les textes (objets FONT, voir étape 6). Tout
  le reste doit avoir un jeu physique : alésages +0,05, trous de plaques +0,05, rainure 1,1 pour un tenon de
  1,0. **Aucun contact de faces** entre corps différents : chaque extrémité d'arbre, de goujon ou de tenon
  s'arrête à ≥ 0,1 mm, ou dans un trou de jeu (§12 `shafts.rules`).

## 6. Arborescence à produire

```
spec/antikythera.json         # copie exacte du §12 (empreinte vérifiée)
am/__init__.py
am/spec.py                    # chargement, validation de structure, accès typé
am/kinematics.py              # Fraction, Willis, résolution globale, DDL, cibles, angles θ(t) en float64
am/expr.py                    # génère les expressions de drivers (≤ 255 car.) et les évalue en Python
am/involute.py                # profils à développante, jeu, phasage
am/outline.py                 # contours de roues : alésages, fenêtres, rayons de b1, anneau e4
am/crown.py                   # maillage des dents a1/q1 à partir des grilles d'enveloppe de la spec
am/layout.py                  # entraxes, recouvrements par couche, anneaux balayés, secteurs, zone a1
am/interference2d.py          # contrôle 2D par pas de dent
am/spiral.py                  # spirales à deux centres, table ψ→ρ
am/threemf.py                 # écriture 3MF minimale (zipfile + XML, unité millimeter)
am/report.py                  # rapport Markdown + HTML autonome
am/verify.py                  # CLI : python -m am.verify --stage {spec,kinematics,geometry,all} ; code ≠ 0 si échec
blender_scripts/bootstrap.py  # sys.path, lecture des arguments après "--"
blender_scripts/build.py      # scène, unités, collections, corps, pièces, matériaux → out/am.blend
blender_scripts/animate.py    # contrôleur, drivers, tables de correspondance, action de la manivelle
blender_scripts/dials.py      # cadrans avant/arrière, anneaux, aiguilles, graduations, textes
blender_scripts/materials.py
blender_scripts/check.py      # relecture des drivers, cycles, BVH, variétés → out/check.json
blender_scripts/export_print.py
blender_scripts/render.py
tests/test_*.py               # unittest (Python de Blender)
out/                          # am.blend, check.json, report.md, report.html, print/, renders/, logs/
README.md  DECISIONS.md  PROGRESS.md
```

## 7. Étapes et points de contrôle

**Étape 0 : spec.** Crée l'arborescence. Écris le bloc JSON du §12 dans `spec/antikythera.json`
(en plusieurs morceaux concaténés si nécessaire). Vérifie l'empreinte canonique :
```sh
"$PY" -c "import json,hashlib;d=json.load(open('spec/antikythera.json'));print(hashlib.sha256(json.dumps(d,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest())"
```
Elle doit valoir `{{SHA}}`. Sinon, compare les empreintes par section (§12) avec la même méthode appliquée à
`d[clé]`, puis réécris les sections fautives jusqu'à l'égalité.
✔ **Point 0** : empreinte identique.

**Étape 1 : cinématique exacte.** `am/spec.py`, `am/kinematics.py`, tests.
✔ **Point 1** : `"$PY" -m unittest discover -s tests -v` et `"$PY" -m am.verify --stage kinematics` sont
verts. DDL = 1, 0 incohérence, taux = spec, cibles = spec.

**Étape 2 : géométrie 2D.** `involute.py`, `outline.py`, `crown.py`, `layout.py`, `interference2d.py`,
`spiral.py`, tests.
✔ **Point 2** : `am.verify --stage geometry` est vert. Entraxes exacts, ε ≥ 1,2, aucune pénétration 2D,
pré-filtre sans conflit, zone de passage de a1 respectée, secteurs des suiveurs libres, contrôles cosmos du
§5.8 verts.

**Étape 3 : expressions.** `am/expr.py` génère une expression par corps (variable `c` = manivelle, plus
d'éventuelles variables `SINGLE_PROP`), sous-ensemble *simple expression*, ≤ 255 caractères. Un évaluateur
Python (restreint aux mêmes fonctions) reproduit θ(t).
✔ **Point 3** : écart < 1e-9 rad avec le solveur sur 200 valeurs de t dans [−50, 50] (angles comparés modulo 2π).

**Étape 4 : construction Blender.** `build.py`, `animate.py`, `materials.py` → `out/am.blend`.
✔ **Point 4** : la construction tourne sans erreur en `-b`. Chaque driver vérifie `is_valid`,
`is_simple_expression`, et `expression ==` la chaîne générée (pas de troncature). Chaque maillage est
fermé, variété, de volume > 0. Le nombre d'objets est cohérent avec la spec.

**Étape 5 : vérification 3D.** `check.py` → `out/check.json`.
✔ **Point 5** :
- relecture sur 50 valeurs de manivelle dans [−50, 50], arrondies en float32 comme au §5.9 : écart < 1e-5
  rad avec le solveur ;
- fermeture des cycles à 1e-5 rad près : après 19 ans, l'aiguille Métonique revient à son angle modulo 2π ;
  idem pour l'Olympiade après 4 ans, le Callippique après 76 ans, le Saros après float32(4237/235) ans ;
- la F-curve de `crank` vaut 0,0 à l'image 1, 0,5 à l'image 61 et 4,0 à l'image 481 ;
- **0 paire BVH en recouvrement** sur tous les échantillons du §5.9.

**Étape 6 : cadrans et boîtier.** `dials.py` (spec `dials`, `structure`), boîtier. Les **textes grecs**
restent des objets FONT (police intégrée, extrusion ≤ 0,05, dans AM_DIALS, corps frame, à ≥ 0,1 mm en z de
toute pièce mobile). Ils sont exclus du contrôle de variété, du BVH et de l'impression, et listés dans le
rapport. La police intégrée n'a pas le stigma Ϛ : la spec écrit déjà ΙΣΤ. Pour détecter un autre glyphe
manquant, compare son maillage à celui de '\U00010300' (boîte « notdef »). Marqueurs planétaires : sphères
**posées** sur la face avant de leur anneau, à `marker_local_deg`. **Affichage planétaire** : couleur de chaque astre,
étiquette qui suit sa planète en restant droite et lisible, et légende, exactement selon `dials.front.planet_display`
(contrainte Copy Location, pas de driver Python ; collection AM_LABELS, exclue du BVH, des contrôles de variété et de
l'impression). **Mise en scène** : sol, lumières, monde, couleurs et réglages EEVEE/Cycles exactement selon `staging`
(collection AM_STAGE, visibilité par vue). **Vue éclatée pilotable** : curseur `AM_Controller['explode']` selon
`explode`. Relance `check.py` complet, cadrans compris (avec `explode = 0`).
✔ **Point 6** : toujours 0 recouvrement ; les spirales suivent ρ(ψ) (écart < 0,01 mm sur 500 valeurs).

**Étape 7 : impression.** `export_print.py` pour chaque profil, selon `print_profiles.rules` : dents amincies
du jeu du profil (couronnes : φ_lo/φ_hi resserrés de jeu/2/ρ), alésages, trous, rainures de tenon et rainures
spirales régénérés avec `bore_clearance_mm`, puis contrôle 2D. Export d'un STL par pièce depuis une **copie
temporaire non parentée** dans le repère local de son corps, seule sélectionnée, supprimée ensuite
(`bpy.ops.wm.stl_export`, `use_scene_unit=False`, `global_scale` = échelle). Plus un 3MF complet via
`am/threemf.py`. Taille par rapport au plateau mesurée sur la copie locale.
✔ **Point 7** : ré-import d'un STL, les dimensions égalent l'échelle attendue à 1e-3 près ; le 3MF se relit
(zip et XML valides, maillages fermés) ; les pièces plus grandes que le plateau sont listées.

**Étape 8 : rendus.** `render.py` :
- Cycles Metal : un rendu de chauffe, puis 4 images finales (vue 3/4 avant, cadran avant de face, cadrans
  arrière de face, vue éclatée) dans `out/renders/` ;
- EEVEE : animation de 480 images, manivelle de 0 à 4 ans. Rends des **PNG** par plages
  (`out/renders/frames/f_####.png`), puis encode **une seule fois** en mp4 par le séquenceur, car il n'y a pas
  de ffmpeg sur la machine et chaque plage rendue en vidéo écraserait le fichier : scène `encode` (mêmes
  résolution et fps ; `enc.frame_start, enc.frame_end = 1, 480`, car une nouvelle scène s'arrête à 250 par
  défaut), `se = enc.sequence_editor_create()`,
  `st = se.strips.new_image(name='f', filepath=<abs>/f_0001.png, channel=1, frame_start=1)`, puis
  `st.elements.append('f_0002.png')`… ; `enc.render.use_sequencer = True`, réglages vidéo du §11,
  `with bpy.context.temp_override(scene=enc): bpy.ops.render.render(animation=True, scene=enc.name)`.
- **Vidéo éclatée** `antikythera_eclate.mp4` (360 images) selon `exploded_video`, mise en scène comprise.
✔ **Point 8** : fichiers présents et non vides ; `bpy.data.movieclips.load(<abs>/out/renders/antikythera.mp4).frame_duration == 480`.

**Étape 9 : rapport.** `am/report.py` → `out/report.md` et `out/report.html` (autonome). Contenu :
- tableau des 20 trains et plus (sortie, chaîne, rapport exact, cycle visé, période en jours, écart avec les
  `reference_values_days`) ;
- contrôles cosmos du §5.8 (élongations, rétrogradations, apogée, anomalie), avec une courte explication :
  les reculs des planètes dans la vidéo sont les rétrogradations attendues (`planet_display.retrograde_note`) ;
- DDL et rang ;
- résultats de tous les contrôles avec leurs chiffres ;
- modules et entraxes ;
- liste des pièces par statut ;
- `unresolved_defaults`, décisions, replis appliqués, pièces trop grandes pour l'impression.

`README.md` : comment tout relancer (une commande par étape). Termine par un résumé sur la sortie standard.

## 8. Replis autorisés (et seulement ceux-là)

- **Interférence d'une couronne** : les grilles d'enveloppe sont vérifiées. Contrôle d'abord ta
  construction : repère (s, φ), sens de φ, phase de b1/b0 à 0, jeu de b1/b0 = 0,03 et loi de q (θ_b − θ_moon).
  Seulement ensuite, resserre φ_lo/φ_hi de 0,01 mm/ρ par pas (au plus 0,03 mm).
- **Interférence 3D entre dents alors que le 2D passe** : augmente la densité des flancs (≥ 32 points par
  flanc) et vérifie le phasage.
- **Collision d'une pièce non dentée** (plaque, bride, capot, ornement, ferrure) : remodèle cette pièce
  (échancrure, dégagement, forme) dans l'enveloppe de la spec. Ne déplace **jamais** un axe d'engrenage et
  ne change **jamais** la plage Z d'une roue. Les positions et plages Z de la spec sont déjà validées
  (voir §12 `meta`) : soupçonne d'abord ta propre modélisation (orientation des piliers, avec la petite
  dimension radiale ; longueurs d'arbres ; rayons de b1).
- **Échec de Cycles Metal** : rends les images finales avec EEVEE et note-le.
- **Expression trop longue** : utilise des Empties intermédiaires pilotés (chaque expression ≤ 255), jamais
  de driver en fonction Python.

## 9. Critères d'acceptation (tous obligatoires)

1. Empreinte de la spec identique au §12.
2. Solveur exact : DDL = 1 ; 0 contrainte incohérente ; taux moyens = `rate_abs_mean` pour les 45 corps
   mobiles ; les 22 `targets` égales en `Fraction`.
3. Pour les 37 engrènements extérieurs : entraxes = m·(z1 + z2)/2 à 1e-6 mm près ; modules égaux ;
   recouvrement de face ≥ 0,5 mm ; ε ≥ 1,2 ; aucun z < 8 ; largeur en tête **nominale** (j = 0) ≥ 0,2·m. Les
   couronnes a1~b1 et b0~q1 sont validées par le BVH du §5.9 (a).
4. Contrôle 2D : 0 pénétration sur 50 positions pour chaque engrènement extérieur (jeu 0,03 mm).
5. Pré-filtre : 0 conflit hors contacts voulus ; zone de a1 respectée (r ≤ 63,6 entre z 4,6 et 33,73 pour tout
   ce que porte b, **sauf b1** lui-même) ; secteurs des suiveurs libres ; contrôles cosmos du §5.8 verts.
6. Drivers : tous valides, en expression simple, non tronqués ; relecture < 1e-5 rad ; cycles refermés.
7. BVH : **0** paire en recouvrement sur tous les échantillons (§5.9), cadrans et boîtier compris (hors
   textes FONT).
8. Maillages (hors textes FONT) : 100 % fermés, variétés, orientés de façon cohérente (arêtes contiguës),
   volume > 0 et égal à aire × épaisseur pour les pièces extrudées ; les couronnes sont contrôlées par coque.
9. Livrables du §10 présents ; `out/am.blend` s'ouvre et s'anime sans autorisation de scripts ; les 7 étiquettes
   suivent leur astre (écart XY étiquette − centre du marqueur constant à 1e-4 mm près sur 20 valeurs de manivelle)
   et sont visibles dans la vidéo, avec la légende ; à `explode = 1`, chaque pièce pilotée est à 3 × son z assemblé
   (1e-3 mm) ; la vidéo éclatée fait 360 images ; le sol ne coupe jamais le mécanisme, assemblé ou éclaté.
10. `PROGRESS.md` et `DECISIONS.md` sont à jour ; le rapport liste tout écart.

## 10. Livrables

- `out/am.blend` : collections par statut, manivelle `AM_Controller["crank"]` avec une action linéaire de 0 à
  4 ans sur 480 images (extrapolation linéaire), `AM_Controller["patina"]` réglable.
- `out/check.json` : tous les résultats chiffrés du §9.
- `out/report.md` et `out/report.html`.
- `out/print/<profil>/*.stl` et `out/print/<profil>/antikythera.3mf` pour `resin_x1`, `resin_x1_5` et `fdm_x2`.
- `out/renders/` : 4 images Cycles (ou EEVEE en repli), `antikythera.mp4` (480 images) et `antikythera_eclate.mp4` (360 images),
  avec la mise en scène `staging`.
- `README.md`, `DECISIONS.md`, `PROGRESS.md`, tests verts.

## 11. Pièges Blender 5.2 (vérifiés sur cette machine)

- Expressions de driver limitées à **255 caractères**, **tronquées sans erreur** : vérifie l'égalité après affectation.
- Fonctions autorisées en *simple expression* : `pi`, `sin`, `cos`, `tan`, `asin`, `acos`, `atan`, `atan2`,
  `sqrt`, `pow`, `exp`, `log`, `fmod`, `floor`, `ceil`, `trunc`, `round`, `int`, `abs`, `fabs`, `min`, `max`,
  `radians`, `degrees`, `lerp`, `clamp`, `smoothstep`, opérateurs arithmétiques, de comparaison, `and`/`or`/`not`
  et ternaire. Vérifie `driver.is_simple_expression`.
- Les entrées et sorties des drivers sont en **float32** : garde |crank| ≤ 100 et module les angles
  (`fmod`) à l'intérieur de l'expression.
- Depuis 5.0, une F-curve de driver créée en Python contient **2 clés par défaut** (0,0) et (1,1). Elles
  forment une identité inoffensive pour un driver normal. Pour une table, vide-les avec
  `fc.keyframe_points.clear()` : itérer sur `list(fc.keyframe_points)` avec `remove` lève « Keyframe not in
  F-Curve ».
- `ctl['crank'] = 0` crée une propriété **entière** et l'action interpole par années entières : utilise des
  flottants (`0.0`).
- Après avoir modifié une propriété dans un script, appelle `update_tag()` puis `view_layer.update()` (ou
  `scene.frame_set`), sinon les drivers renvoient des valeurs périmées.
- Une variable `TRANSFORMS` en `LOCAL_SPACE` ne renvoie pas la rotation multi-tours : utilise `SINGLE_PROP`
  sur `rotation_euler[i]`.
- Actions à slots (4.4+, l'ancienne API a été retirée en 5.0) : `ctl.keyframe_insert('["crank"]', frame=f)`,
  puis `bpy_extras.anim_utils.action_get_channelbag_for_slot(ctl.animation_data.action, ctl.animation_data.action_slot)`
  pour régler l'extrapolation et l'interpolation LINEAR des F-curves.
- Pas de `bpy.ops.mesh.primitive_gear` : Extra Objects n'est plus intégré et ses dents sont trapézoïdales.
- Le lissage automatique n'existe plus : utilise `mesh.set_sharp_from_angle()`. `Material.use_nodes` est
  obsolète, car un nouveau matériau contient déjà Principled BSDF et Material Output. Entrées Principled :
  'Base Color', 'Metallic', 'Roughness', 'Specular Tint', 'Coat Weight', etc.
- Le tampon de `mathutils` est en float32 : fais les calculs en numpy float64.
- `BVHTree.FromObject` renvoie des coordonnées locales ; `overlap()` ne détecte pas l'inclusion totale et
  est instable sur les faces coplanaires ; `epsilon` n'est pas une distance de sécurité. D'où les jeux
  axiaux ≥ 0,1 mm de la spec.
- Export : `bpy.ops.wm.stl_export(filepath=..., export_selected_objects=True, use_batch=False, global_scale=s,
  use_scene_unit=False, apply_modifiers=True, ascii_format=False, forward_axis='Y', up_axis='Z')`. L'ancien
  `export_mesh.stl` n'existe plus. Le 3MF n'est pas natif : écris-le toi-même.
- Rendu : moteur EEVEE = `'BLENDER_EEVEE'`. Pour Cycles Metal :
  `prefs.addons['cycles'].preferences.compute_device_type='METAL'`, `get_devices()`, activer les appareils
  METAL, `scene.cycles.device='GPU'`, `denoiser='OPENIMAGEDENOISE'`, `denoising_use_gpu=True`. Le premier
  rendu compile les noyaux (environ 2 minutes). Depuis 5.0, règle
  `image_settings.media_type` ('IMAGE' ou 'VIDEO') **avant** `file_format`. `media_type='VIDEO'` choisit FFMPEG
  et H264, mais avec un conteneur **MKV** par défaut : règle ensuite `r.ffmpeg.format='MPEG4'`,
  `r.ffmpeg.codec='H264'`, `r.ffmpeg.constant_rate_factor='HIGH'` et un chemin absolu terminé par `.mp4`. Il n'y
  a **pas de binaire ffmpeg** sur la machine.
- `stl_export` écrit chaque pièce avec sa transformation monde (rotation du parent, position assemblée) :
  exporte des copies non parentées dans le repère local. `use_batch=True` nomme les fichiers
  `<nom><objet>.stl`.
- `mathutils.geometry.tessellate_polygon` n'est **pas fiable** sur les contours d'engrenages. Mesuré sur cette
  machine : b1 à 24 points par flanc donne des triangles en trop et des arêtes utilisées 3 fois, et p2 (12 dents)
  donne 721 triangles au lieu de 756. `delaunay_2d_cdt(..., 3, 1e-9)` est exact sur les mêmes contours ;
  remappe les sommets par `orig_verts` s'il en renvoie de nouveaux.
- Les textes FONT convertis en maillage ne sont jamais des variétés, même après fusion des doublons. Le stigma
  Ϛ est absent de la police intégrée, qui affiche alors une boîte « notdef » avec des sommets.
- `--factory-startup` pour des exécutions reproductibles. En mode `-b`, `gpu.init()` n'est nécessaire que pour
  dessiner avec le module gpu.

## 12. Spécification complète (JSON) et empreintes

Empreinte canonique (SHA-256 de `json.dumps(d, ensure_ascii=False, sort_keys=True, separators=(',',':'))`) :
`{{SHA}}`

Empreintes par section (16 premiers caractères hexadécimaux, même méthode appliquée à `d[clé]`) :
{{SECTION_HASHES}}

Validation déjà faite sur cette spec :
- solveur exact indépendant : 45 corps, rang 44, DDL 1 ; 22 cibles exactes ; 37 entraxes exacts à 1e-6 mm ;
  ε ≥ 1,2 ;
- pré-filtre de collisions sur 165 objets (13 530 paires : roues, arbres, goujons, bossages, moyeux, tenons,
  piliers, leviers, anneaux, marqueurs, plaques) sans conflit ;
- cinématique non linéaire : Willis sur les angles à 1e-12 rad près, tenons toujours dans leurs rainures,
  élongations exactes, rétrogradations à 180 ± 0,03°, apogée solaire à 65,49°, anomalie lunaire de 6,58° ;
- couronnes par enveloppe vérifiées au BVH dans Blender 5.2.2 ;
- tests de mutation (dents, axes, modules et plages Z faussés) : tous détectés ;
- revue adversariale par 4 relecteurs indépendants (données, API Blender testée en direct, exécutabilité,
  géométrie) : toutes les corrections sont intégrées.

```json
{{SPEC_JSON}}
```
