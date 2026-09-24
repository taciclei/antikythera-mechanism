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
| corps | parent | axe (repère du parent, mm) | roues | taux moyen absolu | angle θ(t) |
|---|---|---|---|---|---|
| `frame` | — | — | fx51, fx49, fx56 | 0 | fixe |
| `a` | frame | (0.0000, 0.0000) | a1 | — | autour de +x : −2π·(223/48)·t |
| `b` | frame | (0.0000, 0.0000) | b1, b2, b0 | 1 | −2π·(1)·t |
| `moon` | frame | (0.0000, 0.0000) | b3 | 254/19 | monde : θ = −θ_e_inner |
| `c` | frame | (-7.8891, -23.1740) | c2, c1 | -32/19 | −2π·(-32/19)·t |
| `d` | frame | (-13.0733, -38.4156) | d1, d2 | 64/19 | −2π·(64/19)·t |
| `e_pipe` | frame | (14.1105, -11.0151) | e2, e5 | -254/19 | −2π·(-254/19)·t |
| `e_table` | frame | (14.1105, -11.0151) | e3, e4 | -477/4237 | −2π·(-477/4237)·t |
| `e_inner` | frame | (14.1105, -11.0151) | e1, e6 | -254/19 | monde : θ = θ_e_table − θ_kp (θ_kp local à e_table) |
| `k` | e_table | (20.1731, -15.7609) | k1 | 55688/4237 | −2π·(56165/4237)·t (local) |
| `kp` | e_table | (21.0399, -16.4382) | k2 | 55688/4237 | tenon-rainure : θ = θ_k + atan2(1.1·sin(θ_k − β), 9.6 − 1.1·cos(θ_k − β)), β = −38° |
| `l` | frame | (19.8733, 14.2941) | l2, l1 | -32/19 | −2π·(-32/19)·t |
| `m` | frame | (0.0000, 45.5000) | m1, m3, m2 | 53/57 | −2π·(53/57)·t |
| `f` | frame | (19.7179, -73.4600) | f1, f2 | 1692/4237 | −2π·(1692/4237)·t |
| `g` | frame | (0.0000, -82.5240) | g1, g2 | -940/4237 | −2π·(-940/4237)·t |
| `h` | frame | (11.5059, -96.2362) | h1, h2 | 940/12711 | −2π·(940/12711)·t |
| `i` | frame | (-0.2562, -107.5227) | i1 | -235/12711 | −2π·(-235/12711)·t |
| `n` | frame | (0.0000, 62.9760) | n1, n3, n2 | -5/19 | −2π·(-5/19)·t |
| `o` | frame | (-24.4003, 62.9760) | o1 | 1/4 | −2π·(1/4)·t |
| `p` | frame | (12.7650, 76.7098) | p1, p2 | 5/76 | −2π·(5/76)·t |
| `cal` | frame | (24.4003, 62.9760) | cal1 | -1/76 | −2π·(-1/76)·t |
| `q` | moon | (0.0000, 0.0000) | q1 | — | autour de son X local (radial), relatif à `moon` : θ_q = θ_b − θ_moon (NON LINÉAIRE ; moyenne +235/19) |
| `spA` | b | (16.5726, 28.7046) | me72, me89 | 41/24 | −2π·(17/24)·t (local) |
| `spB` | b | (23.3827, -13.5000) | nd62, nd64 | 111/62 | −2π·(49/62)·t (local) |
| `spC` | b | (-12.8000, -22.1703) | vn44, vn34 | 95/44 | −2π·(51/44)·t (local) |
| `x_me40` | b | (28.2742, -1.3476) | me40 | -553/960 | −2π·(-1513/960)·t (local) |
| `x_me20` | b | (32.3566, -15.7814) | me20 | 1993/480 | −2π·(1513/480)·t (local) |
| `x_vn26` | b | (-11.0705, -6.6362) | vn26 | -295/572 | −2π·(-867/572)·t (local) |
| `x_r1` | b | (-25.1954, 11.7488) | r1 | 751/462 | −2π·(289/462)·t (local) |
| `t_nodes` | frame | (0.0000, 0.0000) | nd48 | -5/93 | −2π·(-5/93)·t |
| `x_cp52` | b | (-8.8652, 24.3568) | cp52, sa61 | 27/13 | −2π·(14/13)·t (local) |
| `x_cp64` | b | (2.5101, -28.6904) | cp64, ma38, ju45 | 15/8 | −2π·(7/8)·t (local) |
| `x_su56` | b | (-34.3914, 19.8559) | su56 | 0 | −2π·(-1)·t (local) |
| `x_sa40` | b | (-1.0611, 47.3062) | sa40 | -167/260 | −2π·(-427/260)·t (local) |
| `x_sa68` | b | (22.1400, 35.7495) | sa68 | 869/442 | −2π·(427/442)·t (local) |
| `x_sa86s` | b | (20.6400, 35.7495) | sa86s | 869/442 | tenon-rainure : θ = θ_x_sa68 + atan2(1.5·sin(θ_x_sa68 − β), 14.37 − 1.5·cos(θ_x_sa68 − β)), β = 180° (local à b) |
| `x_ju40` | b | (22.0874, -34.4253) | ju40 | 1/64 | −2π·(-63/64)·t (local) |
| `x_ju43` | b | (28.6000, -15.6000) | ju43 | 659/344 | −2π·(315/344)·t (local) |
| `x_ju65s` | b | (27.0200, -15.6000) | ju65s | 659/344 | tenon-rainure : θ = θ_x_ju43 + atan2(1.58·sin(θ_x_ju43 − β), 8.22 − 1.58·cos(θ_x_ju43 − β)), β = 180° (local à b) |
| `x_ma40` | b | (-3.8512, -46.2964) | ma40 | 27/160 | −2π·(-133/160)·t (local) |
| `x_ma71` | b | (-24.8984, -29.9654) | ma71 | 417/284 | −2π·(133/284)·t (local) |
| `x_ma80s` | b | (-19.2000, -33.2554) | ma80s | 417/284 | tenon-rainure : θ = θ_x_ma71 + atan2(6.58·sin(θ_x_ma71 − β), 10.0 − 6.58·cos(θ_x_ma71 − β)), β = 330° (local à b) |
| `t_saturn` | frame | (0.0000, 0.0000) | sa86o | 15/442 | monde : θ = θ_b − θ_x_sa86s (θ_x_sa86s local à b) |
| `t_jupiter` | frame | (0.0000, 0.0000) | ju65o | 29/344 | monde : θ = θ_b − θ_x_ju65s (θ_x_ju65s local à b) |
| `t_mars` | frame | (0.0000, 0.0000) | ma80o | 151/284 | monde : θ = θ_b − θ_x_ma80s (θ_x_ma80s local à b) |
| `t_mercury` | frame | (0.0000, 0.0000) | — | 1 | suiveur : θ = θ_b + γ0 + atan2(d·sin λ, i + d·cos λ), λ = θ_x_me20 − γ0 ; i = 36.0000, d = 14.0400, γ0 = -26.0000° |
| `t_venus` | frame | (0.0000, 0.0000) | — | 1 | suiveur : θ = θ_b + γ0 + atan2(d·sin λ, i + d·cos λ), λ = θ_x_r1 − γ0 ; i = 27.8000, d = 20.0100, γ0 = 155.0000° |
| `t_trueSun` | frame | (0.0000, 0.0000) | — | 1 | suiveur : θ = θ_b + γ0 + atan2(d·sin λ, i + d·cos λ), λ = θ_x_su56 + 84.5° − γ0 ; i = 39.7117, d = 1.6547, γ0 = 150.0000° |

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
Elle doit valoir `18934c80264941ed315ced4273d0b16d733132a296d64e25300bea5576ab86b3`. Sinon, compare les empreintes par section (§12) avec la même méthode appliquée à
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
**posées** sur la face avant de leur anneau, à `marker_local_deg`. Relance `check.py` complet, cadrans compris.
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
✔ **Point 8** : fichiers présents et non vides ; `bpy.data.movieclips.load(<abs>/out/renders/antikythera.mp4).frame_duration == 480`.

**Étape 9 : rapport.** `am/report.py` → `out/report.md` et `out/report.html` (autonome). Contenu :
- tableau des 20 trains et plus (sortie, chaîne, rapport exact, cycle visé, période en jours, écart avec les
  `reference_values_days`) ;
- contrôles cosmos du §5.8 (élongations, rétrogradations, apogée, anomalie) ;
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
9. Livrables du §10 présents ; `out/am.blend` s'ouvre et s'anime sans autorisation de scripts.
10. `PROGRESS.md` et `DECISIONS.md` sont à jour ; le rapport liste tout écart.

## 10. Livrables

- `out/am.blend` : collections par statut, manivelle `AM_Controller["crank"]` avec une action linéaire de 0 à
  4 ans sur 480 images (extrapolation linéaire), `AM_Controller["patina"]` réglable.
- `out/check.json` : tous les résultats chiffrés du §9.
- `out/report.md` et `out/report.html`.
- `out/print/<profil>/*.stl` et `out/print/<profil>/antikythera.3mf` pour `resin_x1`, `resin_x1_5` et `fdm_x2`.
- `out/renders/` : 4 images Cycles (ou EEVEE en repli) et `antikythera.mp4`.
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
`18934c80264941ed315ced4273d0b16d733132a296d64e25300bea5576ab86b3`

Empreintes par section (16 premiers caractères hexadécimaux, même méthode appliquée à `d[clé]`) :
- `meta` : `77963810ccaa7144`
- `conventions` : `af4c802d9ae056bf`
- `tooth` : `93fb0961a01aa09a`
- `crowns` : `8a954c9370248f11`
- `tubes` : `944b9da8a04324e3`
- `shafts` : `9148da89bf733376`
- `layers` : `83c07f497ff003e1`
- `structure` : `f006f499597321c3`
- `dials` : `ba888f45f7eee551`
- `materials` : `d65e7385e381163e`
- `collections` : `cbb11ec44a0b52fa`
- `print_profiles` : `9da46f0dab38ee62`
- `render` : `5b70c502b4cf2144`
- `sources` : `25ab64b512ef9546`
- `reference_values_days` : `95a6e4108910d168`
- `unresolved_defaults` : `bf1cae6e62624373`
- `gears` : `37752b74f1ce9551`
- `bodies` : `c26ea54b7bf3bcc5`
- `meshes` : `a9fec5db88e1f6a8`
- `pin_slots` : `c725ddbf931ff550`
- `followers` : `212f41ca5b8917ed`
- `targets` : `c2c1ccd0cf1098a0`
- `axes_world_xy` : `6b172d0f645b5386`
- `axes_e3_local_xy` : `3b4aed434f19bbb3`

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
{
 "meta":{"name":"Antikythera Mechanism — functional reconstruction spec","version":"1.0.0","date":"2026-09-24","basis":"Freeth et al. 2021 (Sci. Rep. 11:5821) cosmos model + Freeth 2006/2008 back-dial trains, with geometric corrections for a conjugate, interference-free build","units":"millimetres, years (1 year = 1 turn of b1), degrees where stated","status_levels":{"SURVIVING":"physically attested in the fragments (CT)","RECONSTRUCTED":"strong evidence (inscriptions, dial scales, forced ratios)","HYPOTHETICAL":"proposed by a model (mostly Freeth 2021 front trains)"}},
 "conventions":{
  "frame":"World frame = front view: +x to the right, +y up (Metonic dial on top, Saros below), +z toward the FRONT viewer. z = 0 is the front face of the Main Plate (Main Plate occupies z -2.0..0.0).",
  "rate_sign":"Rates are in revolutions of the body per year (b1 = +1). POSITIVE = CLOCKWISE SEEN FROM THE FRONT. A negative rate on a back-dial pointer means clockwise seen from the back.",
  "blender_angle":"For a z-axis body: local rotation about +z (right-handed, relative to its parent) = -2*pi*rate_rel_parent*years + phase. Parent/child: bodies with parent 'e_table' or 'b' are parented to that carrier in Blender; their axis_xy_in_parent is in the carrier's local frame at crank = 0 (for 'b' this equals world XY; for 'e_table' it is relative to axis E).",
  "crank":"Body 'a' turns about the +x axis (line y = 0, z = 19.1624). Angle about +x = -2*pi*(223/48)*years. Check: at the contact point (x = 64.4024, y = 0, z = 5.30) b1's clockwise motion is toward -y, and a1 rotating negatively about +x moves its lowest point toward -y.",
  "moon_phase":"Body 'q' turns about its radial axis +u (u = the Moon body's local +x, along the Moon pointer), relative to the Moon body, by theta_q = theta_b - theta_moon (world z-angles; 20:20 crown b0~q1; right-handed about +u). NONLINEAR because theta_moon carries the lunar anomaly; mean rate +235/19; theta_q(0) = -0.0773916 rad. Never use a linear law.",
  "time_control":"One Empty 'AM_Controller' with custom property 'crank' = years (float). Keep |crank| <= 100 in drivers (float32).",
  "phases":"Uncalibrated epoch: every LINEAR body angle is 0 at crank = 0; nonlinear bodies (kp, e_inner, moon, q, slot gears, planet outputs, followers) take the value of their formula at crank = 0. Spur tooth phasing is computed so meshing teeth interleave at crank = 0 using the actual body angles; crown teeth come pre-phased in crowns.*.envelope.",
  "reference_directions":"Each body is modelled in its local frame and its Blender object rotation is exactly the body angle theta_B(t). Front pointers (Moon, Date, Dragon Hand), follower levers, pins and slots lie along local +x. Planet markers sit at their ring's marker_local_deg (dials.front.cosmos_rings). Back-dial pointers lie along local +y (spiral start at 12 o'clock). Pins sit at local angle 0 (local +x) of their pin gear / epicycle, EXCEPT the true-Sun pin at local angle followers[trueSun].pin_phase_deg of su56; slots lie along local +x of the slot gear / follower, so every slot contains its pin at all times by construction.",
  "pin_slot_formula":"Pin gear angle th1 (math convention, relative to the carrier), pin radius r, slot-gear axis offset e in direction beta (from pin-gear axis to slot-gear axis, carrier frame): slot gear angle th2 = th1 + atan2(e*sin(th1 - beta), r - e*cos(th1 - beta)). Continuous because e < r. Mean rate of th2 = mean rate of th1.",
  "follower_formula":"theta_F = theta_b + g0 + atan2(d*sin(lam), i + d*cos(lam)), lam = theta_epi_local + pin_phase - g0, where g0 = atan2 of epicycle_axis_xy_in_b, theta_epi_local = the epicycle body's angle relative to b, pin_phase = followers[].pin_phase_deg in radians. Continuous (d < i). Mean rate of every follower = rate of b (= 1).",
  "willis":"For gears g1 (on body B1) and g2 (on body B2) meshing on carrier C: z1*(w1 - wC) = -z2*(w2 - wC) (external mesh)."
 },
 "tooth":{
  "profile":"involute",
  "pressure_angle_deg":30.0,
  "addendum_coeff":1.0,
  "dedendum_coeff":1.25,
  "root_fillet_coeff":0.2,
  "profile_shift":0.0,
  "min_teeth_without_undercut":8,
  "backlash_circumferential_mm":{"scholarly":0.03,"print":"see print_profiles"},
  "backlash_rule":"Thin every tooth by backlash/2 at the pitch circle (flank half-angle psi -= backlash/(4*r)). NEVER move axes.",
  "tip_land_rule":"Tip land >= 0.2*m on the NOMINAL profile (j = 0) for every z of the spec (minimum: p2, 0.228*m). On thinned profiles (scholarly and print) the tip land must be > 0 and is only reported.",
  "lightening":"Wheels with pitch radius > 12 get 4-6 windows between the hub (bore + 2) and the rim (root - max(1.5, 2m)), arms max(1.5, 0.12*r) wide, EXCEPT pin/slot gears (solid) and b1 (spec b1_structure). e3: windows only between 4 and 40 mm from E, with one arm >= 8 wide centred on the K direction (-38 deg in the e_table frame) carrying boss_k; the solid ring 40..rim carries e4 through e4_spacers. e4 is an annulus (inner radius 41.8).",
  "why_30deg":"The 30 deg basic rack is exactly the equilateral-triangle rack of the ancient teeth; conjugate, no undercut down to 8 teeth, contact ratio 1.3-1.4.",
  "optional_render_mode":"triangular straight-flank teeth (historical look, not conjugate) for renders only, never for checks or print"
 },
 "crowns":{
  "method":"Envelope-generated teeth (pre-computed and BVH-verified on Blender 5.2.2: 0 overlaps on 60 positions per pitch, engagement gap 0.013-0.041 mm at every position). Do NOT regenerate them: build them from the grids below.",
  "mesh_rule":"For tooth k (k = 0..z-1), node (i, j): s = s_grid[i][j], rho = rho_levels[j], phi = phi_lo_rad[i][j] + k*2*pi/z (lo flank) and phi_hi_rad[i][j] + k*2*pi/z (hi flank). Crown-frame point = (s, rho*sin(phi), -rho*cos(phi)) relative to the crown axis point; i.e. a1 local (x, y, z - axis_z) and q1 local (u, v, z - axis_z). Faces (quads, each split in 2 triangles), L = lo node, H = hi node, I = last row (root), J = last column: lo flank L(i,j)-L(i,j+1)-L(i+1,j+1)-L(i+1,j); hi flank H(i,j)-H(i+1,j)-H(i+1,j+1)-H(i,j+1); side j = 0: L(i,0)-L(i+1,0)-H(i+1,0)-H(i,0); side j = J: L(i,J)-H(i,J)-H(i+1,J)-L(i+1,J); tip row (i = 0): L(0,j)-H(0,j)-H(0,j+1)-L(0,j+1); root row (i = I): L(I,j)-L(I,j+1)-H(I,j+1)-H(I,j). This winding is outward for both crowns (verified: tooth volume a1 1.3913 mm3, q1 0.8116 mm3, 0 non-contiguous edges). A positive volume alone does not prove the winding: also check is_contiguous on every edge. Row i = last lies 0.05 mm inside the disc, so teeth and disc overlap (same body): keep them as separate closed shells in one object (check manifoldness per connected shell).",
  "a1":{"meshes_with":"b1","body":"a","axis":"+x","axis_y":0.0,"axis_z":19.1624,"teeth":48,"module":0.5776,"pitch_ring_radius":13.8624,"s_is":"world x","phi_is":"angle about +x measured from -z toward +y; B_a rotation alpha adds to phi","disc":{"x":[65.1244,66.6244],"r_out":14.9,"bore":0.0,"note":"solid disc fused to the shaft; spans z 4.26..34.06, below the CP (34.15)"},"shaft":{"radius":1.5,"x":[66.6244,108.0],"through":"crank_bracket hole r 1.55 and case right wall hole r 1.55"},"crank":{"arm":"bar 25 x 4 x 2 at x 99..101, from the shaft axis toward +z","knob":"cylinder r 3 along +x, x 101..111, at the arm end"},"envelope":{"tooth0_centre_rad":0.065449847,"rho_levels":[13.2624,13.3624,13.4624,13.5624,13.6624,13.7624,13.8624,13.9624,14.0624,14.1624,14.2624,14.3624,14.4624,14.5624],"s_grid":[[64.1498,64.1498,64.0998,64.0498,63.9998,63.9498,63.8748,63.8248,63.8498,63.8748,63.8998,63.9498,63.9748,63.9748],[64.242945,64.242945,64.197491,64.152036,64.106582,64.061127,63.992945,63.947491,63.970218,63.992945,64.015673,64.061127,64.083855,64.083855],[64.336091,64.336091,64.295182,64.254273,64.213364,64.172455,64.111091,64.070182,64.090636,64.111091,64.131545,64.172455,64.192909,64.192909],[64.429236,64.429236,64.392873,64.356509,64.320145,64.283782,64.229236,64.192873,64.211055,64.229236,64.247418,64.283782,64.301964,64.301964],[64.522382,64.522382,64.490564,64.458745,64.426927,64.395109,64.347382,64.315564,64.331473,64.347382,64.363291,64.395109,64.411018,64.411018],[64.615527,64.615527,64.588255,64.560982,64.533709,64.506436,64.465527,64.438255,64.451891,64.465527,64.479164,64.506436,64.520073,64.520073],[64.708673,64.708673,64.685945,64.663218,64.640491,64.617764,64.583673,64.560945,64.572309,64.583673,64.595036,64.617764,64.629127,64.629127],[64.801818,64.801818,64.783636,64.765455,64.747273,64.729091,64.701818,64.683636,64.692727,64.701818,64.710909,64.729091,64.738182,64.738182],[64.894964,64.894964,64.881327,64.867691,64.854055,64.840418,64.819964,64.806327,64.813145,64.819964,64.826782,64.840418,64.847236,64.847236],[64.988109,64.988109,64.979018,64.969927,64.960836,64.951745,64.938109,64.929018,64.933564,64.938109,64.942655,64.951745,64.956291,64.956291],[65.081255,65.081255,65.076709,65.072164,65.067618,65.063073,65.056255,65.051709,65.053982,65.056255,65.058527,65.063073,65.065345,65.065345],[65.1744,65.1744,65.1744,65.1744,65.1744,65.1744,65.1744,65.1744,65.1744,65.1744,65.1744,65.1744,65.1744,65.1744]],"phi_lo_rad":[[0.0604606,0.0591296,0.0592713,0.0592659,0.0589659,0.0585188,0.0586609,0.0604228,0.0601232,0.0599709,0.0601132,0.0590775,0.0593672,0.0608351],[0.0570736,0.0557426,0.055737,0.0555843,0.0552844,0.0545428,0.0545375,0.0552687,0.054969,0.054964,0.0549591,0.0542179,0.0545076,0.0559755],[0.0535393,0.0523556,0.0522028,0.0519028,0.0514556,0.0507139,0.0504142,0.0501145,0.0498149,0.0498098,0.0499522,0.0493582,0.0496479,0.0511158],[0.0501523,0.0489685,0.0486685,0.0482212,0.0476268,0.0467379,0.0462908,0.0451076,0.0446607,0.0446557,0.0449452,0.0443513,0.0447883,0.0462562],[0.046618,0.0454343,0.0451342,0.0446869,0.0437979,0.0427618,0.0421675,0.040837,0.0395065,0.0396488,0.0397911,0.0394917,0.0399286,0.0412492],[0.043231,0.0420472,0.0415999,0.0408581,0.0399691,0.0387857,0.0380442,0.0364191,0.0343523,0.0344946,0.0346369,0.0344847,0.035069,0.0363896],[0.0396967,0.0385129,0.0380656,0.0371765,0.0361403,0.0348096,0.0337735,0.0321485,0.0291982,0.0293404,0.02963,0.0296251,0.0302093,0.0313827],[0.0367656,0.0357246,0.034384,0.0333477,0.032017,0.0303918,0.0295029,0.0275834,0.024044,0.0241862,0.0244758,0.0246182,0.0253497,0.026523],[0.0312546,0.0305003,0.025706,0.0236284,0.0225922,0.0214088,0.0203727,0.0188949,0.0187425,0.0190321,0.0193216,0.0196113,0.0203428,0.0215161],[0.0109183,0.0120829,0.0136305,0.0140564,0.0143455,0.0141929,0.0137459,0.0135935,0.0135884,0.0137306,0.0141675,0.0146044,0.0153359,0.0160674],[0.007299,0.0072934,0.0072878,0.0072823,0.0072769,0.0072716,0.0072664,0.0072612,0.0072561,0.0072511,0.0072461,0.0072412,0.0072364,0.0072317],[0.007299,0.0072934,0.0072878,0.0072823,0.0072769,0.0072716,0.0072664,0.0072612,0.0072561,0.0072511,0.0072461,0.0072412,0.0072364,0.0072317]],"phi_hi_rad":[[0.0704391,0.0717701,0.0716284,0.0716338,0.0719338,0.0723809,0.0722388,0.0704769,0.0707765,0.0709288,0.0707865,0.0718222,0.0715325,0.0700646],[0.0738261,0.0751571,0.0751627,0.0753154,0.0756153,0.0763569,0.0763622,0.075631,0.0759307,0.0759357,0.0759406,0.0766818,0.0763921,0.0749242],[0.0773604,0.0785441,0.0786969,0.0789969,0.0794441,0.0801858,0.0804855,0.0807852,0.0810848,0.0810899,0.0809475,0.0815415,0.0812518,0.0797839],[0.0807474,0.0819312,0.0822312,0.0826785,0.0832729,0.0841618,0.0846089,0.0857921,0.086239,0.086244,0.0859545,0.0865484,0.0861114,0.0846435],[0.0842817,0.0854654,0.0857655,0.0862128,0.0871018,0.0881379,0.0887322,0.0900627,0.0913932,0.0912509,0.0911086,0.091408,0.0909711,0.0896505],[0.0876687,0.0888525,0.0892998,0.0900416,0.0909306,0.092114,0.0928555,0.0944806,0.0965474,0.0964051,0.0962628,0.0964149,0.0958307,0.0945101],[0.091203,0.0923868,0.0928341,0.0937232,0.0947594,0.0960901,0.0971261,0.0990457,0.1017015,0.1015593,0.1012697,0.1012746,0.1006904,0.099517],[0.0941341,0.0951751,0.0965157,0.097552,0.0988827,0.1005079,0.1013967,0.1036108,0.1068557,0.1067135,0.1064239,0.1062815,0.10555,0.1043767],[0.0996451,0.1003994,0.1051937,0.1072713,0.1083075,0.1094909,0.110527,0.1120048,0.1121571,0.1118676,0.1115781,0.1112884,0.1105569,0.1093836],[0.1199814,0.1188168,0.1172692,0.1168433,0.1165542,0.1167068,0.1171538,0.1173062,0.1173113,0.1171691,0.1167322,0.1162953,0.1155638,0.1148323],[0.1236007,0.1236063,0.1236119,0.1236174,0.1236228,0.1236281,0.1236333,0.1236385,0.1236436,0.1236486,0.1236536,0.1236584,0.1236633,0.123668],[0.1236007,0.1236063,0.1236119,0.1236174,0.1236228,0.1236281,0.1236333,0.1236385,0.1236436,0.1236486,0.1236536,0.1236584,0.1236633,0.123668]],"tip_s_min":63.8248,"tip_s_max":64.1498},"status":"SURVIVING"},
  "q1":{"meshes_with":"b0","body":"q","carrier":"moon","axis":"radial +u (Moon local +x)","axis_z":52.7,"teeth":20,"module":0.5,"pitch_ring_radius":5.0,"s_is":"Moon-frame u","phi_is":"angle about +u measured from -z toward +v; B_q rotation adds to phi","disc":{"u":[5.625,6.625],"r_out":5.55,"bore":0.0,"note":"spans z 47.15..58.25: 0.15 above the Dragon Hand, 0.35 below the Moon arm"},"arbor":{"radius":0.6,"u":[2.0,17.6]},"hangers":"two brackets owned by body moon, 0.6 thick in u at u 2.3..2.9 and 16.8..17.4, hanging from the cap top plate (z 58.6) down to z 51.4, each with a hole r 0.65 at z 52.70","phase_sphere":{"radius":3.0,"centre_u":13.0,"centre_z":52.7,"halves":"one hemisphere dark, one silver; the dark half faces +z when theta_q = 0"},"envelope":{"tooth0_centre_rad":0.157079633,"rho_levels":[4.55,4.619231,4.688462,4.757692,4.826923,4.896154,4.965385,5.034615,5.103846,5.173077,5.242308,5.311538,5.380769,5.45],"s_grid":[[4.5,4.5,4.5,4.5,4.5,4.5,4.5,4.525,4.55,4.55,4.575,4.6,4.6,4.6],[4.606818,4.606818,4.606818,4.606818,4.606818,4.606818,4.606818,4.629545,4.652273,4.652273,4.675,4.697727,4.697727,4.697727],[4.713636,4.713636,4.713636,4.713636,4.713636,4.713636,4.713636,4.734091,4.754545,4.754545,4.775,4.795455,4.795455,4.795455],[4.820455,4.820455,4.820455,4.820455,4.820455,4.820455,4.820455,4.838636,4.856818,4.856818,4.875,4.893182,4.893182,4.893182],[4.927273,4.927273,4.927273,4.927273,4.927273,4.927273,4.927273,4.943182,4.959091,4.959091,4.975,4.990909,4.990909,4.990909],[5.034091,5.034091,5.034091,5.034091,5.034091,5.034091,5.034091,5.047727,5.061364,5.061364,5.075,5.088636,5.088636,5.088636],[5.140909,5.140909,5.140909,5.140909,5.140909,5.140909,5.140909,5.152273,5.163636,5.163636,5.175,5.186364,5.186364,5.186364],[5.247727,5.247727,5.247727,5.247727,5.247727,5.247727,5.247727,5.256818,5.265909,5.265909,5.275,5.284091,5.284091,5.284091],[5.354545,5.354545,5.354545,5.354545,5.354545,5.354545,5.354545,5.361364,5.368182,5.368182,5.375,5.381818,5.381818,5.381818],[5.461364,5.461364,5.461364,5.461364,5.461364,5.461364,5.461364,5.465909,5.470455,5.470455,5.475,5.479545,5.479545,5.479545],[5.568182,5.568182,5.568182,5.568182,5.568182,5.568182,5.568182,5.570455,5.572727,5.572727,5.575,5.577273,5.577273,5.577273],[5.675,5.675,5.675,5.675,5.675,5.675,5.675,5.675,5.675,5.675,5.675,5.675,5.675,5.675]],"phi_lo_rad":[[0.1348908,0.1359182,0.1369465,0.1383292,0.1400662,0.141804,0.1438961,0.1431616,0.1424278,0.1445221,0.1437897,0.1427046,0.1451544,0.1476048],[0.1271154,0.1270824,0.1274039,0.1280797,0.1291099,0.1304943,0.1318795,0.131145,0.1300577,0.1317987,0.1310663,0.1299811,0.1320775,0.1341745],[0.1196934,0.1182467,0.1178613,0.1178303,0.1181536,0.1188311,0.1198629,0.118775,0.1176877,0.1190752,0.1179894,0.1169043,0.1186472,0.1203907],[0.1126248,0.1097644,0.1079653,0.1072274,0.1071973,0.107168,0.1078463,0.1064049,0.1053177,0.1063518,0.105266,0.1038274,0.1052169,0.1069604],[0.1041425,0.1023424,0.0987761,0.096978,0.0958875,0.0955048,0.0954763,0.0940349,0.0925943,0.0932749,0.0921891,0.0907505,0.09214,0.0931767],[0.0949533,0.0942135,0.0913541,0.0870819,0.0849312,0.0838416,0.0834597,0.0816649,0.0798708,0.080198,0.0787588,0.0776736,0.0787097,0.0793929],[0.0847039,0.0850244,0.0828718,0.0793065,0.0743283,0.0725319,0.0710897,0.0689414,0.0671474,0.0671211,0.0656819,0.0645967,0.0649259,0.0656092],[0.0737476,0.0751284,0.0736827,0.0704708,0.0654926,0.0612222,0.0590731,0.0565714,0.0547773,0.0540443,0.052605,0.0515199,0.0514956,0.0518255],[0.0638427,0.0662574,0.0623729,0.0584542,0.0545363,0.0506193,0.0470565,0.0442014,0.0420539,0.0409674,0.0395281,0.0380895,0.0380653,0.0380417],[0.0482918,0.0461119,0.0422275,0.0400759,0.0382786,0.0361287,0.0343331,0.0318314,0.0293304,0.0278905,0.0264512,0.0250127,0.024635,0.024258],[0.0179058,0.0178728,0.0178409,0.0178098,0.0177797,0.0177504,0.0177219,0.0176942,0.0176673,0.017641,0.0176155,0.0175907,0.0175664,0.0175428],[0.0179058,0.0178728,0.0178409,0.0178098,0.0177797,0.0177504,0.0177219,0.0176942,0.0176673,0.017641,0.0176155,0.0175907,0.0175664,0.0175428]],"phi_hi_rad":[[0.1792684,0.1782411,0.1772128,0.1758301,0.1740931,0.1723552,0.1702631,0.1709977,0.1717315,0.1696371,0.1703695,0.1714547,0.1690049,0.1665545],[0.1870439,0.1870768,0.1867554,0.1860795,0.1850494,0.183665,0.1822797,0.1830143,0.1841015,0.1823606,0.183093,0.1841781,0.1820818,0.1799848],[0.1944659,0.1959126,0.196298,0.196329,0.1960057,0.1953281,0.1942963,0.1953843,0.1964715,0.195084,0.1961699,0.197255,0.1955121,0.1937686],[0.2015345,0.2043949,0.206194,0.2069319,0.206962,0.2069913,0.2063129,0.2077543,0.2088416,0.2078075,0.2088933,0.2103319,0.2089424,0.2071989],[0.2100168,0.2118169,0.2153831,0.2171813,0.2182717,0.2186545,0.2186829,0.2201244,0.221565,0.2208844,0.2219702,0.2234088,0.2220193,0.2209826],[0.2192059,0.2199457,0.2228051,0.2270773,0.229228,0.2303176,0.2306995,0.2324944,0.2342885,0.2339613,0.2354005,0.2364856,0.2354496,0.2347663],[0.2294554,0.2291349,0.2312874,0.2348528,0.2398309,0.2416274,0.2430696,0.2452178,0.2470119,0.2470381,0.2484774,0.2495625,0.2492333,0.2485501],[0.2404117,0.2390309,0.2404766,0.2436885,0.2486667,0.2529371,0.2550861,0.2575878,0.2593819,0.260115,0.2615543,0.2626394,0.2626636,0.2623338],[0.2503166,0.2479019,0.2517863,0.2557051,0.259623,0.26354,0.2671027,0.2699579,0.2721054,0.2731919,0.2746311,0.2760697,0.2760939,0.2761175],[0.2658675,0.2680474,0.2719318,0.2740834,0.2758807,0.2780306,0.2798262,0.2823279,0.2848288,0.2862688,0.287708,0.2891466,0.2895242,0.2899013],[0.2962535,0.2962864,0.2963184,0.2963494,0.2963796,0.2964089,0.2964374,0.2964651,0.296492,0.2965182,0.2965437,0.2965686,0.2965928,0.2966164],[0.2962535,0.2962864,0.2963184,0.2963494,0.2963796,0.2964089,0.2964374,0.2964651,0.296492,0.2965182,0.2965437,0.2965686,0.2965928,0.2966164]],"tip_s_min":4.5,"tip_s_max":4.6},"status":"SURVIVING"}
 },
 "tubes":[
  {"id":"moon_arbor","body":"moon","r_in":0.0,"r_out":1.2,"z":[-3.45,59.4]},
  {"id":"fixed_tube","body":"frame","r_in":1.4,"r_out":2.3,"z":[-1.0,10.15],"note":"pressed into the Main Plate; carries fx51 (L1) and fx49 (L2)"},
  {"id":"b_hub","body":"b","r_in":2.5,"r_out":3.2,"z":[1.8,7.85],"note":"b2 and b1 are fixed on it; it turns on the fixed tube"},
  {"id":"t_meanSun","body":"b","r_in":1.4,"r_out":1.9,"z":[10.3,48.2],"note":"driven by the mean-Sun bar (L3); b0 at its front end"},
  {"id":"t_nodes","body":"t_nodes","r_in":2.1,"r_out":2.6,"z":[11.45,47.0]},
  {"id":"t_mercury","body":"t_mercury","r_in":2.8,"r_out":3.3,"z":[12.6,46.45]},
  {"id":"t_venus","body":"t_venus","r_in":3.5,"r_out":4.0,"z":[13.75,45.9]},
  {"id":"t_trueSun","body":"t_trueSun","r_in":4.2,"r_out":4.7,"z":[24.6,45.35]},
  {"id":"t_mars","body":"t_mars","r_in":4.9,"r_out":5.4,"z":[25.55,44.8]},
  {"id":"t_jupiter","body":"t_jupiter","r_in":5.6,"r_out":6.1,"z":[26.7,44.25]},
  {"id":"t_saturn","body":"t_saturn","r_in":6.3,"r_out":6.8,"z":[29.0,43.7]},
  {"id":"t_date","body":"b","r_in":7.0,"r_out":7.5,"z":[34.15,43.15],"note":"fused to the CP"}
 ],
 "shafts":{
  "rules":["Studs extend exactly 0.05 mm beyond the free end of the hub they carry (never into a neighbouring layer). No face contact between different bodies: every shaft, stud, boss, hub, pin end stops >= 0.1 mm from parts of other bodies, or ends inside a clearance hole (hole radius = shaft radius + 0.05). Blind bearings are not modelled.","Plates (main, back, front, Sub-Plate, CP, Strap, D-plate) get a clearance hole (r + 0.05) wherever a shaft of another body passes or ends inside them; holes for shafts of their own body are fused.","Every gear's bore is gears[].bore_radius: 'fused' gears are part of the shaft's body; 'rides_on' gears turn on a support owned by another body with 0.05 mm radial clearance.","Circles facing a radial clearance g (bores, holes, studs, bosses, tubes) are polygons with n >= max(64, ceil(pi/acos(R/(R+g))) + 8) sides, and a bore and its shaft use the same n."],
  "items":[{"id":"stud_c","owner":"frame","axis_body":"c","r":1.2,"z":[0.0,3.4]},{"id":"stud_l","owner":"frame","axis_body":"l","r":1.2,"z":[0.0,3.6]},{"id":"shaft_d","owner":"d","axis_body":"d","r":1.0,"z":[-4.9,2.55]},{"id":"shaft_m","owner":"m","axis_body":"m","r":1.0,"z":[-16.4,2.15]},{"id":"shaft_e_inner","owner":"e_inner","axis_body":"e_inner","r":1.0,"z":[-16.4,-0.1]},{"id":"pipe_e","owner":"e_pipe","axis_body":"e_pipe","r_in":1.2,"r":1.8,"z":[-7.1,-3.6]},{"id":"shaft_f","owner":"f","axis_body":"f","r":1.0,"z":[-16.4,-0.1]},{"id":"shaft_g","owner":"g","axis_body":"g","r":1.0,"z":[-18.2,-0.1]},{"id":"shaft_h","owner":"h","axis_body":"h","r":1.0,"z":[-16.4,-0.1]},{"id":"shaft_i","owner":"i","axis_body":"i","r":1.0,"z":[-17.0,-0.1]},{"id":"shaft_n","owner":"n","axis_body":"n","r":1.0,"z":[-18.2,-0.1]},{"id":"shaft_o","owner":"o","axis_body":"o","r":1.0,"z":[-17.0,-0.1]},{"id":"shaft_p","owner":"p","axis_body":"p","r":1.0,"z":[-16.4,-0.1]},{"id":"shaft_cal","owner":"cal","axis_body":"cal","r":1.0,"z":[-17.0,-0.1]},{"id":"boss_k","owner":"e_table","axis_body":"k","r":2.3,"z":[-7.25,-6.45]},{"id":"stud_kp","owner":"e_table","axis_body":"kp","r":1.0,"z":[-7.85,-7.25]},{"id":"e4_spacers","owner":"e_table","axis_body":"e_table","note":"6 spacers r 1.0 at radius 46.0 from E (every 60 deg), z -6.60..-6.45, join e4 to e3"},{"id":"stud_spA","owner":"b","axis_body":"spA","r":0.8,"z":[6.65,17.1]},{"id":"hub_spA","owner":"spA","axis_body":"spA","r_in":0.85,"r":1.4,"z":[6.75,17.05]},{"id":"stud_spB","owner":"b","axis_body":"spB","r":0.8,"z":[6.65,12.5]},{"id":"hub_spB","owner":"spB","axis_body":"spB","r_in":0.85,"r":1.4,"z":[6.75,12.45]},{"id":"stud_spC","owner":"b","axis_body":"spC","r":0.8,"z":[6.65,17.1]},{"id":"hub_spC","owner":"spC","axis_body":"spC","r_in":0.85,"r":1.4,"z":[6.75,17.05]},{"id":"stud_me40","owner":"b","axis_body":"x_me40","r":0.8,"z":[16.0,22.85],"note":"hangs from the Strap"},{"id":"hub_me40","owner":"x_me40","axis_body":"x_me40","r_in":0.85,"r":1.4,"z":[16.05,22.75]},{"id":"stud_me20","owner":"b","axis_body":"x_me20","r":0.8,"z":[14.85,22.85],"note":"hangs from the Strap"},{"id":"hub_me20","owner":"x_me20","axis_body":"x_me20","r_in":0.85,"r":1.4,"z":[14.9,22.75]},{"id":"stud_vn26","owner":"b","axis_body":"x_vn26","r":0.8,"z":[16.0,17.8],"note":"hangs from the D-plate"},{"id":"hub_vn26","owner":"x_vn26","axis_body":"x_vn26","r_in":0.85,"r":1.4,"z":[16.05,17.7]},{"id":"stud_r1","owner":"b","axis_body":"x_r1","r":0.8,"z":[14.85,17.8],"note":"hangs from the D-plate"},{"id":"hub_r1","owner":"x_r1","axis_body":"x_r1","r_in":0.85,"r":1.4,"z":[14.9,17.7]},{"id":"shaft_cp52","owner":"x_cp52","axis_body":"x_cp52","r":1.0,"z":[30.15,37.3],"note":"through a CP hole r 1.05"},{"id":"shaft_cp64","owner":"x_cp64","axis_body":"x_cp64","r":1.0,"z":[26.7,37.3],"note":"through a CP hole r 1.05"},{"id":"shaft_su56","owner":"x_su56","axis_body":"x_su56","r":1.0,"z":[33.25,37.3],"note":"through a CP hole r 1.05"},{"id":"crank_disc_su56","owner":"x_su56","axis_body":"x_su56","r":2.6,"z":[33.25,34.0]},{"id":"stud_sa40","owner":"b","axis_body":"x_sa40","r":0.8,"z":[30.1,34.15]},{"id":"hub_sa40","owner":"x_sa40","axis_body":"x_sa40","r_in":0.85,"r":1.4,"z":[30.15,34.05]},{"id":"stud_ju40","owner":"b","axis_body":"x_ju40","r":0.8,"z":[27.8,34.15]},{"id":"hub_ju40","owner":"x_ju40","axis_body":"x_ju40","r_in":0.85,"r":1.4,"z":[27.85,34.05]},{"id":"stud_ma40","owner":"b","axis_body":"x_ma40","r":0.8,"z":[26.65,34.15]},{"id":"hub_ma40","owner":"x_ma40","axis_body":"x_ma40","r_in":0.85,"r":1.4,"z":[26.7,34.05]},{"id":"boss_sa68","owner":"b","axis_body":"x_sa68","r":2.7,"z":[30.1,34.15]},{"id":"stud_sa86s","owner":"b","axis_body":"x_sa86s","r":1.2,"z":[29.0,30.1]},{"id":"boss_ju43","owner":"b","axis_body":"x_ju43","r":2.8,"z":[27.8,34.15]},{"id":"stud_ju65s","owner":"b","axis_body":"x_ju65s","r":1.2,"z":[26.7,27.8]},{"id":"boss_ma71","owner":"b","axis_body":"x_ma71","r":7.8,"z":[26.65,34.15]},{"id":"stud_ma80s","owner":"b","axis_body":"x_ma80s","r":1.2,"z":[25.55,26.65]}],
  "pins":[{"id":"pin_lunar","owner":"k","local_xy":[9.6,0.0],"r":0.5,"z":[-7.8,-7.2],"slot_in":"k2"},{"id":"pin_saturn","owner":"x_sa68","local_xy":[14.37,0.0],"r":0.5,"z":[29.05,30.15],"slot_in":"sa86s"},{"id":"pin_jupiter","owner":"x_ju43","local_xy":[8.22,0.0],"r":0.5,"z":[26.75,27.85],"slot_in":"ju65s"},{"id":"pin_mars","owner":"x_ma71","local_xy":[10.0,0.0],"r":0.5,"z":[25.6,26.7],"slot_in":"ma80s"},{"id":"pin_mercury","owner":"x_me20","local_xy":[14.04,0.0],"r":0.5,"z":[12.65,14.9],"slot_in":"mercury_follower"},{"id":"pin_venus","owner":"x_r1","local_xy":[20.01,0.0],"r":0.5,"z":[13.8,14.9],"slot_in":"venus_follower"},{"id":"pin_trueSun","owner":"x_su56","local_polar":["d = followers[trueSun].pin_d","angle = followers[trueSun].pin_phase_deg"],"r":0.5,"z":[24.65,33.25],"slot_in":"true_sun_follower"}],
  "slots":"Every slot is a radial slot of width 1.1 with round ends, along local +x of its slot gear or follower, spanning (pin radius - offset - 0.6) .. (pin radius + offset + 0.6) from that body's axis (followers: i - d - 0.6 .. i + d + 0.6). Pin/slot gears (k1, k2, sa68, sa86s, ju43, ju65s, ma71, ma80s) have NO lightening windows."
 },
 "layers":{
  "front_under_b1":"F1 z 0.15..2.55: c2, d1, l2, m1. F2 z 1.60..3.80: c1, l1, b2. b1 z 3.95..6.65 (hub and rivets to 7.85).",
  "b1_to_strap":"L1 8.00-9.00 fx51 me72 vn44 | L2 9.15-10.15 fx49 nd62 | L3 10.30-11.30 mean-Sun bar | L4 11.45-12.45 nd64 nd48 | L5 12.60-13.60 Mercury follower | L6 13.75-14.75 Venus follower | L7 14.90-15.90 me20 disk + r1 disk (pins point back) | L8 16.05-17.65 me89 me40 me20 vn34 vn26 r1 | L9 17.80-18.80 D-plate | Strap 22.85-24.45",
  "strap_to_cp":"T1 24.60-25.40 true-Sun follower | T2 25.55-26.55 ma80s ma80o | T3 26.70-27.70 ma38 ma40 ma71 ju65s ju65o | T4 27.85-28.85 ju45 ju40 ju43 | T5 29.00-30.00 sa86s sa86o | T6 30.15-31.15 sa61 sa40 sa68 | CP 34.15-36.15 | C0 36.30-37.30 fx56 cp52 cp64 su56 | Sub-Plate 37.45-38.65",
  "rear":"Main Plate -2.0..0 | R1 -3.45..-2.15 b3 e1 | R2 -4.90..-3.60 d2 e2 | R3 -6.45..-5.05 e3 m3 | R4 -8.10..-6.60 e4 f1 e5 k1 m2 n1 | R5 -7.95..-7.35 k2 e6 (inside the e4 annulus) | -9.75..-8.25 f2 g1 n3 o1 | -11.50..-9.90 g2 h1 n2 p1 | -13.05..-11.55 h2 i1 p2 cal1 | back plate -16.5..-15.0",
  "swing_sectors":"Relative to b: the Mercury follower (L5) swings within -49..-3 deg and the Venus follower (L6) within 109..201 deg (r < 52). No b-carried arbor may cross L5 or L6 inside those sectors except the intended pins."
 },
 "structure":[
  {"id":"main_plate","body":"frame","status":"SURVIVING","z":[-2.0,0.0],"outline":"rounded rectangle x -88..88, y -160..140, corner r 4","holes":"clearance holes r + 0.05 cut through the plate: fixed tube (r 2.3, pressed in, fused), d and m (r 1.05, shafts pass through), and e_inner, f, g, h, i, n, o, p, cal (r 1.05, shafts end at z -0.10 inside the hole); c and l studs fused on the front face; no blind bearings"},
  {"id":"back_plate","body":"frame","status":"RECONSTRUCTED","z":[-16.5,-15.0],"outline":"same as main_plate","holes":"clearance holes r 1.05 cut through the plate: n, g (shafts pass through to their pointers at z -18.2), o, cal, i (pass through to z -17.0), and m, e_inner, f, h, p (shafts end at z -16.40 inside the hole); spiral grooves cut through (width 1.2)"},
  {"id":"front_plate","body":"frame","status":"RECONSTRUCTED","z":[40.0,41.5],"outline":"same as main_plate","holes":"central r 7.8; calendar hole circle (see dials.front)"},
  {"id":"frame_pillars","body":"frame","status":"RECONSTRUCTED","count":4,"xy":[[-82,95],[82,95],[-82,-95],[82,-95]],"radius":2.5,"z":[-15.0,40.0],"note":"pass through the Main Plate; keep clear of a1 and the crank bracket"},
  {"id":"crank_bracket","body":"frame","status":"HYPOTHETICAL","shape":"L-bracket on the Main Plate at x 80..84, y -4..4, rising to z 21.5 with a bearing hole r 1.55 at z = a1 axis_z","z":[0.0,21.5]},
  {"id":"b1_structure","body":"b","status":"SURVIVING","rim_inner_radius":53.0,"hub_radius":9.0,"hub_top_z":7.85,"spokes":[{"name":"A","angle_deg":60,"feature":"flat 10.5x10.3 carrying the spA stud"},{"name":"B","angle_deg":-30,"feature":"bearing OD 9.7 at r 27.0 (spB)"},{"name":"C","angle_deg":240,"feature":"hole at r 25.6 (spC)"},{"name":"D","angle_deg":150,"feature":"pierced block at r 31.8 carrying the mean-Sun bar post"}],"spoke_width":15.5},
  {"id":"short_pillars","body":"b","status":"SURVIVING","count":2,"polar":[[56.0,-19.0],[56.0,161.0]],"section":[5.0,4.4],"z":[6.65,22.85],"tenon_to":24.45},
  {"id":"long_pillars","body":"b","status":"SURVIVING","count":4,"polar":[[58.5,15.0],[58.5,105.0],[58.5,195.0],[58.5,285.0]],"section":[9.1,7.0],"z":[6.65,34.15],"tenon_to":36.15,"note":"outer face <= 63.3 (a1 keep-out)"},
  {"id":"mean_sun_bar","body":"b","status":"HYPOTHETICAL","z":[10.3,11.3],"shape":"bar width 3 from a collar on t_meanSun (r 1.9..3.4) to the Spoke D block at 31.8@150 deg, with a post down to b1 (z 6.65)"},
  {"id":"strap","body":"b","status":"HYPOTHETICAL","z":[22.85,24.45],"shape":"bar 123 x 24.8 along the -19/161 deg line through the centre, central hole r 7.8, holes for the short-pillar tenons and the me40/me20 studs"},
  {"id":"d_plate","body":"b","status":"SURVIVING","z":[17.8,18.8],"shape":"plate 25.3 wide centred on the 161 deg line, from 5.0 to 34.0 along that line (inner edge >= 4.15 from the centre), fixed to the Strap by 2 posts r 1.0 (z 18.80..22.85) placed away from the Venus sector r < 50; carries the vn26 and r1 studs"},
  {"id":"mercury_disk","body":"x_me20","status":"HYPOTHETICAL","z":[14.9,15.9],"radius":15.5,"pin":{"radius":0.5,"d":14.04,"z":[12.6,14.9]}},
  {"id":"venus_disk","body":"x_r1","status":"SURVIVING","z":[14.9,15.9],"radius":21.5,"pin":{"radius":0.5,"d":20.01,"z":[13.75,14.9]}},
  {"id":"mercury_follower","body":"t_mercury","status":"HYPOTHETICAL","z":[12.6,13.6],"shape":"lever from the tube to r 52 with a radial slot 21.96-0.6 .. 50.04+0.6, width 1.1"},
  {"id":"venus_follower","body":"t_venus","status":"HYPOTHETICAL","z":[13.75,14.75],"shape":"lever to r 49.5 with a slot 7.79-0.6 .. 47.81+0.6, width 1.1"},
  {"id":"true_sun_follower","body":"t_trueSun","status":"HYPOTHETICAL","z":[24.6,25.4],"shape":"lever to r 43.5 with a slot (i-d-0.6)..(i+d+0.6), width 1.1"},
  {"id":"true_sun_pin","body":"x_su56","status":"HYPOTHETICAL","shape":"su56 arbor passes through the CP; behind the CP a crank disc (r 2.6, z 33.25..34.00) carries an eccentric pin r 0.5 at d = i/24 from the su56 axis, spanning z 24.60..33.25"},
  {"id":"cp","body":"b","status":"HYPOTHETICAL","z":[34.15,36.15],"shape":"disc r 65.0, central hole r 7.0 (the Date tube is fused to it), bearing holes for cp52/cp64/su56 arbors, boss mounts for the pin/slot pairs and idler studs"},
  {"id":"sub_plate","body":"frame","status":"HYPOTHETICAL","z":[37.45,38.65],"shape":"disc r 60 with central hole r 7.8; fx56 (bore 7.8) is joined to it by a spacer ring r 7.8..12.0, z 37.30..37.45 (frame); 3 standoffs r 2 at r 57 (90, 210, 330 deg) up to the front plate (z 38.65..40.0)"},
  {"id":"case","body":"frame","status":"RECONSTRUCTED","shape":"wooden box, inner x -92..92, y -164..144, z -24..62, walls 5; front and back covers optional (hidden by default); crank shaft through the right wall (x = 92) at y 0, z = a1 axis_z, crank arm 25 long with a knob"}
 ],
 "dials":{
  "front":{"zodiac_ring":{"body":"frame","status":"SURVIVING","radii":[62.5,70.0],"z_face":41.5,"divisions":360,"signs":12,"labels":["ΚΡΙΟΣ","ΤΑΥΡΟΣ","ΔΙΔΥΜΟΙ","ΚΑΡΚΙΝΟΣ","ΛΕΩΝ","ΠΑΡΘΕΝΟΣ","ΧΗΛΑΙ","ΣΚΟΡΠΙΟΣ","ΤΟΞΟΤΗΣ","ΑΙΓΟΚΕΡΩΣ","ΥΔΡΟΧΟΟΣ","ΙΧΘΥΕΣ"],"orientation":"longitude 0 (start of Krios) on the +x axis (3 o'clock) so the mean Sun (b, local +x) is at longitude 0 at crank 0; longitudes increase CLOCKWISE seen from the front"},"calendar_ring":{"body":"frame","note":"movable by hand in the original; modelled fixed","status":"SURVIVING","radii":[70.0,79.0],"z":[41.65,42.45],"day_divisions":365,"months":12,"epagomenal_days":5,"month_labels":["ΘΩΥΘ","ΦΑΩΦΙ","ΑΘΥΡ","ΧΟΙΑΚ","ΤΥΒΙ","ΜΕΧΙΡ","ΦΑΜΕΝΩΘ","ΦΑΡΜΟΥΘΙ","ΠΑΧΩΝ","ΠΑΥΝΙ","ΕΠΙΦΙ","ΜΕΣΟΡΗ","ΕΠΑΓΟΜΕΝΑΙ"],"hole_circle":{"radius":77.34,"count":354,"count_alternatives":[355,365],"hole_diameter":0.8,"sources":["B20","WB24","F21SI 6.4.2 (365)"]}},"cosmos_rings":[{"body":"t_saturn","radii":[58.0,62.0],"z":[43.3,43.7],"marker_r":60.0,"marker_local_deg":0.0,"label":"Saturn"},{"body":"t_jupiter","radii":[53.0,57.0],"z":[43.85,44.25],"marker_r":55.0,"marker_local_deg":0.0,"label":"Jupiter"},{"body":"t_mars","radii":[48.0,52.0],"z":[44.4,44.8],"marker_r":50.0,"marker_local_deg":150.0,"label":"Mars"},{"body":"t_trueSun","radii":[43.0,47.0],"z":[44.95,45.35],"marker_r":45.0,"marker_local_deg":-150.0,"label":"true Sun (golden sphere r 1.6)"},{"body":"t_venus","radii":[38.0,42.0],"z":[45.5,45.9],"marker_r":40.0,"marker_local_deg":-155.0,"label":"Venus"},{"body":"t_mercury","radii":[33.0,37.0],"z":[46.05,46.45],"marker_r":35.0,"marker_local_deg":26.0,"label":"Mercury"}],"cosmos_rings_note":"Each ring = annulus + a thin disc from its tube to the annulus at the same z. Radii are visual estimates from F21 Fig. 7 (LOW confidence). Marker = stone sphere r 1.2 (true Sun: golden sphere r 1.6) RESTING on the ring front face (centre z = ring z1 + sphere radius) at marker_r, at local angle marker_local_deg (math convention) of the ring body. Followers: marker_local_deg = -g0 so the display = mean Sun + elongation; superior planets: 180 + beta so retrograde happens at opposition.","date_pointer":{"body":"b","z":[42.65,43.15],"length":78.5,"width":2.0},"dragon_hand":{"body":"t_nodes","z":[46.6,47.0],"half_length":30.0,"status":"HYPOTHETICAL"},"moon_pointer":{"body":"moon","arm_z":[58.6,59.4],"length":62.0,"width":3.0,"window":{"centre_u":13.0,"diameter":8.2,"ring_boss_r_out":5.1},"cap":"a top plate at the arm (z 58.6..59.4) plus the two hanger brackets of crowns.q1.hangers (u 2.3..2.9 and 16.8..17.4) carrying the q1 arbor at z 52.70; the q1 disc (r_out 5.55 about its axis, z 47.15..58.25) clears the arm by 0.35 and the Dragon Hand (z <= 47.0) by 0.15"},"parapegma":{"body":"frame","status":"SURVIVING","plates":[{"y":[82,138]},{"y":[-158,-82]}],"z":[41.5,42.0],"x":[-80,80],"note":"2 columns of engraved lines each (placeholder text)"}},
  "back":{"view_frame":"Back-view 2D coords (u, v) = (-x, y). Pointer angle psi measured CLOCKWISE seen from the back, from +v (12 o'clock): direction (u, v) = (sin psi, cos psi), i.e. world (x, y) = (-sin psi, cos psi).","spiral_model":"Two-centre half-circle spiral (Anastasiou et al. 2014). k = floor(psi / 2pi), phi = psi - 2pi*k, R_k = r_start + k*pitch, delta = pitch/2. If phi < pi: rho = R_k. Else: rho = delta*cos(phi) + sqrt((R_k + delta)^2 - delta^2*sin(phi)^2). Second centre = dial centre + (0, +delta) in (u, v). Alternative (not default): Archimedean rho = r_start + pitch*psi/(2pi).","metonic":{"centre":"N","turns":5,"cells":235,"cells_per_turn":47,"r_start":44.0,"pitch":5.2,"groove_width":1.2,"rim_outer":72.0,"pointer_body":"n","pointer_rate_back_clockwise":"5/19","pointer":{"z":[-18.2,-17.4],"length":72.0},"status":"SURVIVING"},"saros":{"centre":"G","turns":4,"cells":223,"cells_per_turn":55.75,"r_start":44.0,"pitch":6.5,"groove_width":1.2,"rim_outer":72.0,"pointer_body":"g","pointer_rate_back_clockwise":"940/4237","pointer":{"z":[-18.2,-17.4],"length":72.0},"glyphs":"eclipse glyph placeholders optional","status":"SURVIVING"},"follower":"Each spiral pointer carries a radial slider (owned by the pointer body n or g) with a pin r 0.5 riding in the groove at rho(psi). psi_mod is computed from the crank c directly, never from the wrapped pointer rotation: Metonic psi_mod = 10*pi*fmod(fmod(c/19, 1) + 1, 1); Saros psi_mod = 8*pi*fmod(fmod(c*235/4237, 1) + 1, 1). rho(psi_mod) through a driver F-curve lookup table (>= 1800 keys, LINEAR; clear the 2 default keys first). The groove is the spiral offset by +-0.6 with round ends (r 0.6) centred on the spiral points at psi = 0 and psi = turns*2pi.","subsidiary":[{"id":"olympiad","centre":"O","radius":18.0,"sectors":4,"labels":["ΙΣΘΜΙΑ","ΟΛΥΜΠΙΑ","ΝΕΜΕΑ","ΠΥΘΙΑ"],"sector_tilt_deg":8,"pointer_body":"o","pointer":{"z":[-17.0,-16.6],"length":16.0},"note":"turns anticlockwise seen from the back (+1/4)","status":"SURVIVING"},{"id":"callippic","centre":"cal","radius":18.0,"sectors":4,"pointer_body":"cal","pointer":{"z":[-17.0,-16.6],"length":16.0},"status":"RECONSTRUCTED"},{"id":"exeligmos","centre":"I","radius":17.0,"sectors":3,"labels":["","Η","ΙΣΤ"],"label_note":"the stigma Ϛ (U+03DA) is missing from Blender's built-in font, so 16 is written ΙΣΤ","pointer_body":"i","pointer":{"z":[-17.0,-16.6],"length":15.0},"status":"SURVIVING"}],"centre_distance_N_G":145.5}
 },
 "materials":{"bronze":{"base_color_linear":[0.92,0.7,0.47],"metallic":1.0,"roughness":0.35,"note":"interpolated between copper and brass (physicallybased.info); approximation"},"patina":{"base_colors":["verdigris ~ (0.18, 0.42, 0.34)","cuprite brown ~ (0.22, 0.10, 0.06)"],"metallic":0.0,"roughness":0.8,"mix":"AO + noise through a colour ramp; mix factor driven by AM_Controller['patina'] (0 = new, 1 = museum)"},"wood":{"base_color_linear":[0.3,0.18,0.1],"roughness":0.6},"status_debug_colors":{"SURVIVING":[0.72,0.45,0.16,1],"RECONSTRUCTED":[0.16,0.55,0.48,1],"HYPOTHETICAL":[0.5,0.42,0.78,1]}},
 "collections":["AM_SURVIVING","AM_RECONSTRUCTED","AM_HYPOTHETICAL","AM_STRUCTURE","AM_DIALS","AM_CASE","AM_HELPERS"],
 "print_profiles":{
  "resin_x1":{"scale":1.0,"backlash_mm":0.05,"axial_gap_mm":0.15,"bore_clearance_mm":0.05,"min_wall_mm":0.4,"bed_mm":[218,123]},
  "resin_x1_5":{"scale":1.5,"backlash_mm":0.08,"axial_gap_mm":0.2,"bore_clearance_mm":0.08,"min_wall_mm":0.5,"bed_mm":[218,123]},
  "fdm_x2":{"scale":2.0,"backlash_mm":0.2,"axial_gap_mm":0.3,"bore_clearance_mm":0.2,"min_wall_mm":0.8,"bed_mm":[256,256]},
  "rules":"Values are at print scale. Regenerate tooth outlines with the profile backlash (thinner teeth; crown teeth: shrink phi_lo/phi_hi by backlash/2/rho each), regenerate every bore, plate hole, pin slot (width 2*r_pin + 2*bore_clearance) and spiral groove with bore_clearance_mm, keep the scaled axis positions exactly, re-run the 2D interference check. min_wall_mm applies to rims, arms, hubs and slot/bore walls, not to tip lands (tip lands only reported; list teeth with tip land < 0.2*m_print as fragile). Export one STL per part from an UNPARENTED temporary copy in the part's body-local frame, plus one 3MF with all parts (unit millimeter). List every part larger than the bed (measured on the local copy); b1 at fdm_x2 is ~260 mm."
 },
 "render":{"preview":{"engine":"BLENDER_EEVEE","resolution":[1280,720]},"final":{"engine":"CYCLES","device":"METAL","resolution":[1920,1080],"samples":256,"denoiser":"OPENIMAGEDENOISE","denoising_use_gpu":true},"animation":{"engine":"BLENDER_EEVEE","frames":480,"fps":24,"crank_years":[0.0,4.0],"format":"FFMPEG H264 mp4"},"cameras":["front three-quarter","front dial straight on","back dials straight on","exploded view (z offsets x3 by layer)"]},
 "sources":{
  "F21":"https://pmc.ncbi.nlm.nih.gov/articles/PMC7955085/",
  "F21SI":"https://static-content.springer.com/esm/art%3A10.1038%2Fs41598-021-84310-w/MediaObjects/41598_2021_84310_MOESM4_ESM.pdf",
  "F06":"https://www.nature.com/articles/nature05357",
  "F06SI":"https://static-content.springer.com/esm/art%3A10.1038%2Fnature05357/MediaObjects/41586_2006_BFnature05357_MOESM1_ESM.pdf",
  "F08SI":"https://archive.nyu.edu/bitstream/2451/60882/2/Freeth_Jones_Steele_Bitsakis_2008_supplementary.pdf",
  "FJ12":"http://dlib.nyu.edu/awdl/isaw/isaw-papers/4/",
  "P74":"https://gwern.net/doc/history/1974-desollaprice.pdf",
  "B20":"https://bhi.co.uk/wp-content/uploads/2020/12/BHI-Antikythera-Mechanism-Evidence-of-a-Lunar-Calendar.pdf",
  "WB24":"https://arxiv.org/abs/2403.00040",
  "A14":"https://journals.sagepub.com/doi/abs/10.1177/0021828614537185",
  "SA25":"https://arxiv.org/abs/2504.00327",
  "V21":"https://arxiv.org/pdf/2204.11136",
  "V22":"https://arxiv.org/abs/2104.06181",
  "V24":"https://arxiv.org/abs/2412.07023",
  "E21":"https://digitalheritagelab.eu/wp-content/uploads/2025/03/heritage-04-00211-v4_compressed.pdf",
  "CDC16":"http://dlib.nyu.edu/awdl/isaw/isaw-papers/11/",
  "SEI":"https://pos.sissa.it/170/007/pdf"
 },
 "reference_values_days":{"tropical_year":365.2422,"sidereal_month":27.321661,"tropical_month":27.321582,"synodic_month":29.530589,"anomalistic_month":27.55455,"draconic_month":27.212221,"lunar_apsides_period":3232.6054,"lunar_nodes_period_tropical":6798.38,"lunar_nodes_period_sidereal":6793.48,"metonic_235_synodic":6939.6884,"saros_223_synodic":6585.3213,"exeligmos":19755.9639,"callippic_940_synodic":27758.7536,"synodic_mercury":115.88,"synodic_venus":583.92,"synodic_mars":779.94,"synodic_jupiter":398.88,"synodic_saturn":378.09,"sidereal_mars":686.98,"sidereal_jupiter":4332.589,"sidereal_saturn":10759.22,"note":"Use for the report's error column only. Every train reproduces its ANCIENT period relation exactly; deviations from these modern values come from the relations themselves."},
 "unresolved_defaults":["Axis XY coordinates are derived (not published); residuals against CT distances are within ~0.8 mm.","Angles of H, I, O, P and the K direction on e3 are unpublished design choices.","Cosmos ring radii are visual estimates from F21 Fig. 7.","True-Sun eccentricity d = i/24 (Hipparchus); F21SI Table S9 does not give it. Solar apogee set at longitude 65.5 deg (Hipparchus) through followers[trueSun].pin_phase_deg = 84.5.","Crown teeth (a1, q1) are envelope-generated against the involute spur (clearance 0.04 per flank) instead of the ancient hand-filed form.","Lunar pin radius 9.6 mm (alternative 9.9).","Calendar hole count 354 (alternatives 355, 365).","Epoch phases are uncalibrated (all 0 at crank 0).","Rear-layout handedness follows Price 1974 (mirror not excluded).","Main Plate modelled 2.0 thick (Price: double sheet 2 x 2.0-2.3); turntable raised 3.05 mm instead of 2.7 to keep 0.15 mm axial gaps."],
 "gears":[
  {"id":"a1","teeth":48,"module":0.5776,"pitch_radius":13.8624,"tip_radius":14.44,"root_radius":13.1404,"body":"a","z":[4.6,33.73],"kind":"crown","status":"SURVIVING","role":"Contrate input pinion on the crank shaft; drives b1 (crank turns 223/48 per year)","axis_xy_world_at_crank0":null,"bore_radius":0.0,"mount":"crown (solid disc fused to its shaft)","alternatives":[{"value":"44-52","source":"Wright limits"}]},
  {"id":"b1","teeth":223,"module":0.5776,"pitch_radius":64.4024,"tip_radius":64.98,"root_radius":63.6804,"body":"b","z":[3.95,6.65],"kind":"spur","status":"SURVIVING","role":"Main drive wheel, 1 turn = 1 tropical year; carries every front epicyclic train, the Strap and the CP","axis_xy_world_at_crank0":[0.0,0.0],"bore_radius":3.2,"mount":"fused to tube b_hub","alternatives":[{"value":224,"source":"F06SI limits 223/224"},{"value":225,"source":"Price 1974; V22"},{"value":"228/229","source":"V24 (3% shrinkage)"}]},
  {"id":"b2","teeth":64,"module":0.48,"pitch_radius":15.36,"tip_radius":15.84,"root_radius":14.76,"body":"b","z":[1.8,3.8],"kind":"spur","status":"SURVIVING","role":"Year input for the rear trains (Moon via c1, calendars and eclipses via l1)","axis_xy_world_at_crank0":[0.0,0.0],"bore_radius":3.2,"mount":"fused to tube b_hub","alternatives":[]},
  {"id":"b3","teeth":32,"module":0.5594,"pitch_radius":8.9504,"tip_radius":9.5098,"root_radius":8.25115,"body":"moon","z":[-3.45,-2.15],"kind":"spur","status":"SURVIVING","role":"Takes the Moon (with anomaly) from e1 to the central Moon arbor","axis_xy_world_at_crank0":[0.0,0.0],"bore_radius":1.2,"mount":"fused to tube moon_arbor","alternatives":[]},
  {"id":"c1","teeth":38,"module":0.48,"pitch_radius":9.12,"tip_radius":9.6,"root_radius":8.52,"body":"c","z":[1.6,3.1],"kind":"spur","status":"SURVIVING","role":"Moon train","axis_xy_world_at_crank0":[-7.8890642192,-23.1739738876],"bore_radius":1.25,"mount":"rides_on stud_c (owner frame)","alternatives":[]},
  {"id":"c2","teeth":48,"module":0.4472,"pitch_radius":10.7328,"tip_radius":11.18,"root_radius":10.1738,"body":"c","z":[0.15,1.45],"kind":"spur","status":"SURVIVING","role":"Moon train","axis_xy_world_at_crank0":[-7.8890642192,-23.1739738876],"bore_radius":1.25,"mount":"rides_on stud_c (owner frame)","alternatives":[{"value":"47-49","source":"F06SI"}]},
  {"id":"d1","teeth":24,"module":0.4472,"pitch_radius":5.3664,"tip_radius":5.8136,"root_radius":4.8074,"body":"d","z":[0.15,2.55],"kind":"spur","status":"SURVIVING","role":"Moon train (arbor passes through the Main Plate)","axis_xy_world_at_crank0":[-13.0732908379,-38.4156284896],"bore_radius":1.0,"mount":"fused to shaft_d","alternatives":[]},
  {"id":"d2","teeth":127,"module":0.4855,"pitch_radius":30.82925,"tip_radius":31.31475,"root_radius":30.222375,"body":"d","z":[-4.9,-3.6],"kind":"spur","status":"SURVIVING","role":"Moon train, prime 127 = 254/2","axis_xy_world_at_crank0":[-13.0732908379,-38.4156284896],"bore_radius":1.0,"mount":"fused to shaft_d","alternatives":[]},
  {"id":"e1","teeth":32,"module":0.5594,"pitch_radius":8.9504,"tip_radius":9.5098,"root_radius":8.25115,"body":"e_inner","z":[-3.45,-2.15],"kind":"spur","status":"SURVIVING","role":"Moon output with anomaly, drives b3","axis_xy_world_at_crank0":[14.1105021486,-11.0150973556],"bore_radius":1.0,"mount":"fused to shaft_e_inner","alternatives":[]},
  {"id":"e2","teeth":32,"module":0.4855,"pitch_radius":7.768,"tip_radius":8.2535,"root_radius":7.161125,"body":"e_pipe","z":[-4.6,-3.6],"kind":"spur","status":"SURVIVING","role":"Mean sidereal Moon","axis_xy_world_at_crank0":[14.1105021486,-11.0150973556],"bore_radius":1.8,"mount":"fused to pipe_e","alternatives":[]},
  {"id":"e3","teeth":223,"module":0.466,"pitch_radius":51.959,"tip_radius":52.425,"root_radius":51.3765,"body":"e_table","z":[-6.45,-5.05],"kind":"spur","status":"SURVIVING","role":"Turntable: lunar apsidal line, 8.88 yr; carries k1 and k2","axis_xy_world_at_crank0":[14.1105021486,-11.0150973556],"bore_radius":1.85,"mount":"rides_on pipe_e (owner e_pipe)","alternatives":[{"value":"217-235","source":"F06SI CT limits"}]},
  {"id":"e4","teeth":188,"module":0.5203,"pitch_radius":48.9082,"tip_radius":49.4285,"root_radius":48.257825,"body":"e_table","z":[-8.1,-6.6],"kind":"annulus_external","status":"SURVIVING","role":"Annulus with external teeth, drives the Saros/Exeligmos trains","axis_xy_world_at_crank0":[14.1105021486,-11.0150973556],"bore_radius":41.8,"mount":"annulus fixed to e3 by e4_spacers (same body)","alternatives":[{"value":"180-192","source":"F06SI"}],"annulus_inner_radius":41.8},
  {"id":"e5","teeth":50,"module":0.512,"pitch_radius":12.8,"tip_radius":13.312,"root_radius":12.16,"body":"e_pipe","z":[-7.1,-6.6],"kind":"spur","status":"SURVIVING","role":"Drives k1","axis_xy_world_at_crank0":[14.1105021486,-11.0150973556],"bore_radius":1.8,"mount":"fused to pipe_e","alternatives":[{"value":"50-52","source":"F06SI; Wright 51"}]},
  {"id":"e6","teeth":50,"module":0.534,"pitch_radius":13.35,"tip_radius":13.884,"root_radius":12.6825,"body":"e_inner","z":[-7.95,-7.35],"kind":"spur","status":"SURVIVING","role":"Receives the variable Moon motion from k2","axis_xy_world_at_crank0":[14.1105021486,-11.0150973556],"bore_radius":1.0,"mount":"fused to shaft_e_inner","alternatives":[{"value":"49-50","source":"F06SI; Wright 53"}]},
  {"id":"k1","teeth":50,"module":0.512,"pitch_radius":12.8,"tip_radius":13.312,"root_radius":12.16,"body":"k","z":[-7.2,-6.6],"kind":"spur","status":"SURVIVING","role":"Pin gear on the e3 turntable","axis_xy_world_at_crank0":[34.283577441,-26.7760311239],"bore_radius":2.35,"mount":"rides_on boss_k (owner e_table)","alternatives":[{"value":"48-51","source":"F06SI"}]},
  {"id":"k2","teeth":50,"module":0.534,"pitch_radius":13.35,"tip_radius":13.884,"root_radius":12.6825,"body":"kp","z":[-7.85,-7.35],"kind":"spur","status":"SURVIVING","role":"Slot gear on the e3 turntable (Hipparchan lunar anomaly)","axis_xy_world_at_crank0":[35.1503892699,-27.4532587468],"bore_radius":1.05,"mount":"rides_on stud_kp (owner e_table)","alternatives":[{"value":"48-52","source":"F06SI"}]},
  {"id":"f1","teeth":53,"module":0.5203,"pitch_radius":13.78795,"tip_radius":14.30825,"root_radius":13.137575,"body":"f","z":[-7.9,-6.6],"kind":"spur","status":"SURVIVING","role":"Saros train","axis_xy_world_at_crank0":[19.7178722445,-73.4599900645],"bore_radius":1.0,"mount":"fused to shaft_f","alternatives":[{"value":54,"source":"alternative count"}]},
  {"id":"f2","teeth":30,"module":0.5167,"pitch_radius":7.7505,"tip_radius":8.2672,"root_radius":7.104625,"body":"f","z":[-9.45,-8.25],"kind":"spur","status":"SURVIVING","role":"Saros train","axis_xy_world_at_crank0":[19.7178722445,-73.4599900645],"bore_radius":1.0,"mount":"fused to shaft_f","alternatives":[]},
  {"id":"g1","teeth":54,"module":0.5167,"pitch_radius":13.9509,"tip_radius":14.4676,"root_radius":13.305025,"body":"g","z":[-9.75,-8.25],"kind":"spur","status":"SURVIVING","role":"Saros pointer: 4 turns = 223 synodic months","axis_xy_world_at_crank0":[0.0,-82.524],"bore_radius":1.0,"mount":"fused to shaft_g","alternatives":[{"value":"54-56","source":"F06SI"}]},
  {"id":"g2","teeth":20,"module":0.4475,"pitch_radius":4.475,"tip_radius":4.9225,"root_radius":3.915625,"body":"g","z":[-11.5,-9.9],"kind":"spur","status":"SURVIVING","role":"Exeligmos train","axis_xy_world_at_crank0":[0.0,-82.524],"bore_radius":1.0,"mount":"fused to shaft_g","alternatives":[]},
  {"id":"h1","teeth":60,"module":0.4475,"pitch_radius":13.425,"tip_radius":13.8725,"root_radius":12.865625,"body":"h","z":[-10.9,-9.9],"kind":"spur","status":"SURVIVING","role":"Exeligmos train","axis_xy_world_at_crank0":[11.5058982134,-96.2361955318],"bore_radius":1.0,"mount":"fused to shaft_h","alternatives":[{"value":"60-64","source":"F06SI"}]},
  {"id":"h2","teeth":15,"module":0.4347,"pitch_radius":3.26025,"tip_radius":3.69495,"root_radius":2.716875,"body":"h","z":[-13.05,-11.65],"kind":"spur","status":"SURVIVING","role":"Exeligmos train","axis_xy_world_at_crank0":[11.5058982134,-96.2361955318],"bore_radius":1.0,"mount":"fused to shaft_h","alternatives":[]},
  {"id":"i1","teeth":60,"module":0.4347,"pitch_radius":13.041,"tip_radius":13.4757,"root_radius":12.497625,"body":"i","z":[-12.85,-11.65],"kind":"spur","status":"SURVIVING","role":"Exeligmos pointer: 1 turn = 3 Saros","axis_xy_world_at_crank0":[-0.2561529074,-107.5226876793],"bore_radius":1.0,"mount":"fused to shaft_i","alternatives":[]},
  {"id":"l1","teeth":38,"module":0.48,"pitch_radius":9.12,"tip_radius":9.6,"root_radius":8.52,"body":"l","z":[1.8,3.3],"kind":"spur","status":"SURVIVING","role":"Metonic/apsides trains (prime 19)","axis_xy_world_at_crank0":[19.8733147053,14.2941163638],"bore_radius":1.25,"mount":"rides_on stud_l (owner frame)","alternatives":[]},
  {"id":"l2","teeth":53,"module":0.4966,"pitch_radius":13.1599,"tip_radius":13.6565,"root_radius":12.53915,"body":"l","z":[0.15,1.65],"kind":"spur","status":"SURVIVING","role":"Metonic/apsides trains","axis_xy_world_at_crank0":[19.8733147053,14.2941163638],"bore_radius":1.25,"mount":"rides_on stud_l (owner frame)","alternatives":[]},
  {"id":"m1","teeth":96,"module":0.4966,"pitch_radius":23.8368,"tip_radius":24.3334,"root_radius":23.21605,"body":"m","z":[0.15,2.15],"kind":"spur","status":"SURVIVING","role":"Split point of the Metonic and Saros trains","axis_xy_world_at_crank0":[0.0,45.5],"bore_radius":1.0,"mount":"fused to shaft_m","alternatives":[{"value":"96-99","source":"F06SI"}]},
  {"id":"m2","teeth":15,"module":0.514,"pitch_radius":3.855,"tip_radius":4.369,"root_radius":3.2125,"body":"m","z":[-8.4,-6.6],"kind":"spur","status":"SURVIVING","role":"Drives n1 (Metonic)","axis_xy_world_at_crank0":[0.0,45.5],"bore_radius":1.0,"mount":"fused to shaft_m","alternatives":[]},
  {"id":"m3","teeth":27,"module":0.466,"pitch_radius":6.291,"tip_radius":6.757,"root_radius":5.7085,"body":"m","z":[-6.45,-5.05],"kind":"spur","status":"RECONSTRUCTED","role":"Drives the e3 turntable (count forced by the ratio)","axis_xy_world_at_crank0":[0.0,45.5],"bore_radius":1.0,"mount":"fused to shaft_m","alternatives":[]},
  {"id":"n1","teeth":53,"module":0.514,"pitch_radius":13.621,"tip_radius":14.135,"root_radius":12.9785,"body":"n","z":[-8.1,-6.6],"kind":"spur","status":"RECONSTRUCTED","role":"Metonic pointer: 5 turns = 19 years","axis_xy_world_at_crank0":[0.0,62.976],"bore_radius":1.0,"mount":"fused to shaft_n","alternatives":[]},
  {"id":"n2","teeth":15,"module":0.5,"pitch_radius":3.75,"tip_radius":4.25,"root_radius":3.125,"body":"n","z":[-11.4,-9.9],"kind":"spur","status":"RECONSTRUCTED","role":"Drives the Callippic train","axis_xy_world_at_crank0":[0.0,62.976],"bore_radius":1.0,"mount":"fused to shaft_n","alternatives":[]},
  {"id":"n3","teeth":57,"module":0.4171,"pitch_radius":11.88735,"tip_radius":12.30445,"root_radius":11.365975,"body":"n","z":[-9.45,-8.25],"kind":"spur","status":"RECONSTRUCTED","role":"Drives the Olympiad (Games) dial","axis_xy_world_at_crank0":[0.0,62.976],"bore_radius":1.0,"mount":"fused to shaft_n","alternatives":[]},
  {"id":"o1","teeth":60,"module":0.4171,"pitch_radius":12.513,"tip_radius":12.9301,"root_radius":11.991625,"body":"o","z":[-9.35,-8.25],"kind":"spur","status":"SURVIVING","role":"Games/Olympiad pointer, 4 years (the only anticlockwise back pointer)","axis_xy_world_at_crank0":[-24.40035,62.976],"bore_radius":1.0,"mount":"fused to shaft_o","alternatives":[{"value":"57-61","source":"F06SI/F08SI"}]},
  {"id":"p1","teeth":60,"module":0.5,"pitch_radius":15.0,"tip_radius":15.5,"root_radius":14.375,"body":"p","z":[-11.2,-9.9],"kind":"spur","status":"RECONSTRUCTED","role":"Callippic train","axis_xy_world_at_crank0":[12.7649722263,76.7098262717],"bore_radius":1.0,"mount":"fused to shaft_p","alternatives":[]},
  {"id":"p2","teeth":12,"module":0.5,"pitch_radius":3.0,"tip_radius":3.5,"root_radius":2.375,"body":"p","z":[-13.05,-11.55],"kind":"spur","status":"RECONSTRUCTED","role":"Callippic train","axis_xy_world_at_crank0":[12.7649722263,76.7098262717],"bore_radius":1.0,"mount":"fused to shaft_p","alternatives":[]},
  {"id":"cal1","teeth":60,"module":0.5,"pitch_radius":15.0,"tip_radius":15.5,"root_radius":14.375,"body":"cal","z":[-12.85,-11.55],"kind":"spur","status":"RECONSTRUCTED","role":"Callippic pointer, 76 years","axis_xy_world_at_crank0":[24.40035,62.976],"bore_radius":1.0,"mount":"fused to shaft_cal","alternatives":[]},
  {"id":"q1","teeth":20,"module":0.5,"pitch_radius":5.0,"tip_radius":5.5,"root_radius":4.375,"body":"q","z":[47.2,58.2],"kind":"crown","status":"SURVIVING","role":"Moon-phase contrate on a radial arbor in the Moon-pointer cap","axis_xy_world_at_crank0":null,"bore_radius":0.0,"mount":"crown (solid disc fused to its shaft)","alternatives":[]},
  {"id":"r1","teeth":63,"module":0.521,"pitch_radius":16.4115,"tip_radius":16.9325,"root_radius":15.76025,"body":"x_r1","z":[16.05,17.65],"kind":"spur","status":"SURVIVING","role":"Venus epicycle (surviving 63-tooth gear)","axis_xy_world_at_crank0":[-25.1953564796,11.7487876764],"bore_radius":1.4,"mount":"fused to hub_r1","alternatives":[{"value":64,"source":"rejected by FJ12 and F21SI"}]},
  {"id":"b0","teeth":20,"module":0.5,"pitch_radius":5.0,"tip_radius":5.5,"root_radius":4.375,"body":"b","z":[47.2,48.2],"kind":"spur","status":"HYPOTHETICAL","role":"Mean Sun input to the Moon-phase differential","axis_xy_world_at_crank0":[0.0,0.0],"bore_radius":1.9,"mount":"fused to tube t_meanSun","alternatives":[]},
  {"id":"fx51","teeth":51,"module":0.538947368421,"pitch_radius":13.7431578947,"tip_radius":14.2821052632,"root_radius":13.0694736842,"body":"frame","z":[8.0,9.0],"kind":"spur","status":"HYPOTHETICAL","role":"Fixed gear shared by Mercury and Venus","axis_xy_world_at_crank0":[0,0],"bore_radius":2.3,"mount":"fused to tube fixed_tube","alternatives":[]},
  {"id":"fx49","teeth":49,"module":0.486486486486,"pitch_radius":11.9189189189,"tip_radius":12.4054054054,"root_radius":11.3108108108,"body":"frame","z":[9.15,10.15],"kind":"spur","status":"HYPOTHETICAL","role":"Fixed gear of the Nodes train","axis_xy_world_at_crank0":[0,0],"bore_radius":2.3,"mount":"fused to tube fixed_tube","alternatives":[]},
  {"id":"nd62","teeth":62,"module":0.486486486486,"pitch_radius":15.0810810811,"tip_radius":15.5675675676,"root_radius":14.472972973,"body":"spB","z":[9.15,10.15],"kind":"spur","status":"HYPOTHETICAL","role":"Nodes train","axis_xy_world_at_crank0":[23.3826859022,-13.5],"bore_radius":1.4,"mount":"fused to hub_spB","alternatives":[]},
  {"id":"nd64","teeth":64,"module":0.482142857143,"pitch_radius":15.4285714286,"tip_radius":15.9107142857,"root_radius":14.8258928571,"body":"spB","z":[11.45,12.45],"kind":"spur","status":"HYPOTHETICAL","role":"Nodes train","axis_xy_world_at_crank0":[23.3826859022,-13.5],"bore_radius":1.4,"mount":"fused to hub_spB","alternatives":[]},
  {"id":"nd48","teeth":48,"module":0.482142857143,"pitch_radius":11.5714285714,"tip_radius":12.0535714286,"root_radius":10.96875,"body":"t_nodes","z":[11.45,12.45],"kind":"spur","status":"HYPOTHETICAL","role":"Dragon Hand (lunar nodes, 18.6 yr, retrograde)","axis_xy_world_at_crank0":[0.0,0.0],"bore_radius":2.6,"mount":"fused to tube t_nodes","alternatives":[]},
  {"id":"vn44","teeth":44,"module":0.538947368421,"pitch_radius":11.8568421053,"tip_radius":12.3957894737,"root_radius":11.1831578947,"body":"spC","z":[8.0,9.0],"kind":"spur","status":"HYPOTHETICAL","role":"Venus train","axis_xy_world_at_crank0":[-12.8,-22.1702503369],"bore_radius":1.4,"mount":"fused to hub_spC","alternatives":[]},
  {"id":"vn34","teeth":34,"module":0.521,"pitch_radius":8.857,"tip_radius":9.378,"root_radius":8.20575,"body":"spC","z":[16.05,17.05],"kind":"spur","status":"HYPOTHETICAL","role":"Venus train","axis_xy_world_at_crank0":[-12.8,-22.1702503369],"bore_radius":1.4,"mount":"fused to hub_spC","alternatives":[]},
  {"id":"vn26","teeth":26,"module":0.521,"pitch_radius":6.773,"tip_radius":7.294,"root_radius":6.12175,"body":"x_vn26","z":[16.05,17.05],"kind":"spur","status":"HYPOTHETICAL","role":"Venus idler","axis_xy_world_at_crank0":[-11.0704837376,-6.6362336799],"bore_radius":1.4,"mount":"fused to hub_vn26","alternatives":[]},
  {"id":"me72","teeth":72,"module":0.538947368421,"pitch_radius":19.4021052632,"tip_radius":19.9410526316,"root_radius":18.7284210526,"body":"spA","z":[8.0,9.0],"kind":"spur","status":"HYPOTHETICAL","role":"Mercury train","axis_xy_world_at_crank0":[16.5726315789,28.7046399099],"bore_radius":1.4,"mount":"fused to hub_spA","alternatives":[]},
  {"id":"me89","teeth":89,"module":0.5,"pitch_radius":22.25,"tip_radius":22.75,"root_radius":21.625,"body":"spA","z":[16.05,17.05],"kind":"spur","status":"HYPOTHETICAL","role":"Mercury train (prime 89)","axis_xy_world_at_crank0":[16.5726315789,28.7046399099],"bore_radius":1.4,"mount":"fused to hub_spA","alternatives":[]},
  {"id":"me40","teeth":40,"module":0.5,"pitch_radius":10.0,"tip_radius":10.5,"root_radius":9.375,"body":"x_me40","z":[16.05,17.05],"kind":"spur","status":"HYPOTHETICAL","role":"Mercury idler","axis_xy_world_at_crank0":[28.2742081463,-1.3475747479],"bore_radius":1.4,"mount":"fused to hub_me40","alternatives":[]},
  {"id":"me20","teeth":20,"module":0.5,"pitch_radius":5.0,"tip_radius":5.5,"root_radius":4.375,"body":"x_me20","z":[16.05,17.05],"kind":"spur","status":"HYPOTHETICAL","role":"Mercury epicycle","axis_xy_world_at_crank0":[32.3565856668,-15.7813612844],"bore_radius":1.4,"mount":"fused to hub_me20","alternatives":[]},
  {"id":"fx56","teeth":56,"module":0.48,"pitch_radius":13.44,"tip_radius":13.92,"root_radius":12.84,"body":"frame","z":[36.3,37.3],"kind":"spur","status":"HYPOTHETICAL","role":"Fixed gear for the true Sun and the superior planets","axis_xy_world_at_crank0":[0,0],"bore_radius":7.8,"mount":"fused to the Sub-Plate through the spacer ring (frame); the Date tube passes inside","alternatives":[]},
  {"id":"cp52","teeth":52,"module":0.48,"pitch_radius":12.48,"tip_radius":12.96,"root_radius":11.88,"body":"x_cp52","z":[36.3,37.3],"kind":"spur","status":"HYPOTHETICAL","role":"True-Sun idler and Saturn g2","axis_xy_world_at_crank0":[-8.865162115,24.3568327308],"bore_radius":1.0,"mount":"fused to shaft_cp52","alternatives":[]},
  {"id":"cp64","teeth":64,"module":0.48,"pitch_radius":15.36,"tip_radius":15.84,"root_radius":14.76,"body":"x_cp64","z":[36.3,37.3],"kind":"spur","status":"HYPOTHETICAL","role":"Mars/Jupiter g2","axis_xy_world_at_crank0":[2.5100853911,-28.690407305],"bore_radius":1.0,"mount":"fused to shaft_cp64","alternatives":[]},
  {"id":"su56","teeth":56,"module":0.48,"pitch_radius":13.44,"tip_radius":13.92,"root_radius":12.84,"body":"x_su56","z":[36.3,37.3],"kind":"spur","status":"HYPOTHETICAL","role":"True-Sun epicycle (pure translation)","axis_xy_world_at_crank0":[-34.3913790731,19.8558719656],"bore_radius":1.0,"mount":"fused to shaft_su56","alternatives":[]},
  {"id":"sa61","teeth":61,"module":0.48,"pitch_radius":14.64,"tip_radius":15.12,"root_radius":14.04,"body":"x_cp52","z":[30.15,31.15],"kind":"spur","status":"HYPOTHETICAL","role":"Saturn g3","axis_xy_world_at_crank0":[-8.865162115,24.3568327308],"bore_radius":1.0,"mount":"fused to shaft_cp52","alternatives":[]},
  {"id":"sa40","teeth":40,"module":0.48,"pitch_radius":9.6,"tip_radius":10.08,"root_radius":9.0,"body":"x_sa40","z":[30.15,31.15],"kind":"spur","status":"HYPOTHETICAL","role":"Saturn idler","axis_xy_world_at_crank0":[-1.0610691422,47.3062059874],"bore_radius":1.4,"mount":"fused to hub_sa40","alternatives":[]},
  {"id":"sa68","teeth":68,"module":0.48,"pitch_radius":16.32,"tip_radius":16.8,"root_radius":15.72,"body":"x_sa68","z":[30.15,31.15],"kind":"spur","status":"HYPOTHETICAL","role":"Saturn pin gear","axis_xy_world_at_crank0":[22.14,35.7495286682],"bore_radius":2.75,"mount":"rides_on boss_sa68 (owner b)","alternatives":[]},
  {"id":"sa86s","teeth":86,"module":0.48,"pitch_radius":20.64,"tip_radius":21.12,"root_radius":20.04,"body":"x_sa86s","z":[29.0,30.0],"kind":"spur","status":"HYPOTHETICAL","role":"Saturn slot gear","axis_xy_world_at_crank0":[20.64,35.7495286682],"bore_radius":1.25,"mount":"rides_on stud_sa86s (owner b)","alternatives":[]},
  {"id":"sa86o","teeth":86,"module":0.48,"pitch_radius":20.64,"tip_radius":21.12,"root_radius":20.04,"body":"t_saturn","z":[29.0,30.0],"kind":"spur","status":"HYPOTHETICAL","role":"Saturn output (29.47 yr)","axis_xy_world_at_crank0":[0.0,0.0],"bore_radius":6.8,"mount":"fused to tube t_saturn","alternatives":[]},
  {"id":"ju45","teeth":45,"module":0.48,"pitch_radius":10.8,"tip_radius":11.28,"root_radius":10.2,"body":"x_cp64","z":[27.85,28.85],"kind":"spur","status":"HYPOTHETICAL","role":"Jupiter g3","axis_xy_world_at_crank0":[2.5100853911,-28.690407305],"bore_radius":1.0,"mount":"fused to shaft_cp64","alternatives":[]},
  {"id":"ju40","teeth":40,"module":0.48,"pitch_radius":9.6,"tip_radius":10.08,"root_radius":9.0,"body":"x_ju40","z":[27.85,28.85],"kind":"spur","status":"HYPOTHETICAL","role":"Jupiter idler","axis_xy_world_at_crank0":[22.0873900365,-34.4253129556],"bore_radius":1.4,"mount":"fused to hub_ju40","alternatives":[]},
  {"id":"ju43","teeth":43,"module":0.48,"pitch_radius":10.32,"tip_radius":10.8,"root_radius":9.72,"body":"x_ju43","z":[27.85,28.85],"kind":"spur","status":"HYPOTHETICAL","role":"Jupiter pin gear","axis_xy_world_at_crank0":[28.5999925981,-15.6],"bore_radius":2.85,"mount":"rides_on boss_ju43 (owner b)","alternatives":[]},
  {"id":"ju65s","teeth":65,"module":0.48,"pitch_radius":15.6,"tip_radius":16.08,"root_radius":15.0,"body":"x_ju65s","z":[26.7,27.7],"kind":"spur","status":"HYPOTHETICAL","role":"Jupiter slot gear","axis_xy_world_at_crank0":[27.0199925981,-15.6],"bore_radius":1.25,"mount":"rides_on stud_ju65s (owner b)","alternatives":[]},
  {"id":"ju65o","teeth":65,"module":0.48,"pitch_radius":15.6,"tip_radius":16.08,"root_radius":15.0,"body":"t_jupiter","z":[26.7,27.7],"kind":"spur","status":"HYPOTHETICAL","role":"Jupiter output (11.86 yr)","axis_xy_world_at_crank0":[0.0,0.0],"bore_radius":6.1,"mount":"fused to tube t_jupiter","alternatives":[]},
  {"id":"ma38","teeth":38,"module":0.48,"pitch_radius":9.12,"tip_radius":9.6,"root_radius":8.52,"body":"x_cp64","z":[26.7,27.7],"kind":"spur","status":"HYPOTHETICAL","role":"Mars g3","axis_xy_world_at_crank0":[2.5100853911,-28.690407305],"bore_radius":1.0,"mount":"fused to shaft_cp64","alternatives":[]},
  {"id":"ma40","teeth":40,"module":0.48,"pitch_radius":9.6,"tip_radius":10.08,"root_radius":9.0,"body":"x_ma40","z":[26.7,27.7],"kind":"spur","status":"HYPOTHETICAL","role":"Mars idler","axis_xy_world_at_crank0":[-3.851213673,-46.2964367897],"bore_radius":1.4,"mount":"fused to hub_ma40","alternatives":[]},
  {"id":"ma71","teeth":71,"module":0.48,"pitch_radius":17.04,"tip_radius":17.52,"root_radius":16.44,"body":"x_ma71","z":[26.7,27.7],"kind":"spur","status":"HYPOTHETICAL","role":"Mars pin gear","axis_xy_world_at_crank0":[-24.8984471569,-29.9653755053],"bore_radius":7.85,"mount":"rides_on boss_ma71 (owner b)","alternatives":[]},
  {"id":"ma80s","teeth":80,"module":0.48,"pitch_radius":19.2,"tip_radius":19.68,"root_radius":18.6,"body":"x_ma80s","z":[25.55,26.55],"kind":"spur","status":"HYPOTHETICAL","role":"Mars slot gear","axis_xy_world_at_crank0":[-19.2,-33.2553755053],"bore_radius":1.25,"mount":"rides_on stud_ma80s (owner b)","alternatives":[]},
  {"id":"ma80o","teeth":80,"module":0.48,"pitch_radius":19.2,"tip_radius":19.68,"root_radius":18.6,"body":"t_mars","z":[25.55,26.55],"kind":"spur","status":"HYPOTHETICAL","role":"Mars output (1.88 yr)","axis_xy_world_at_crank0":[0.0,0.0],"bore_radius":5.4,"mount":"fused to tube t_mars","alternatives":[]}
 ],
 "bodies":[
  {"id":"frame","parent":null,"axis":"z","kind":"fixed","gears":["fx51","fx49","fx56"],"axis_xy_in_parent":null,"rate_abs_mean":"0","rate_rel_parent_mean":null,"note":"Main Plate, back plate, front plate, Sub-Plate, fixed central tube (fx51, fx49) and Sub-Plate gear fx56"},
  {"id":"a","parent":"frame","axis":"x","kind":"crank","gears":["a1"],"axis_xy_in_parent":[0.0,0.0],"rate_abs_mean":null,"rate_rel_parent_mean":null,"note":"Axis along +x at y = 0, z = 19.1624. Angle about +x = -2*pi*(223/48)*years (see conventions)."},
  {"id":"b","parent":"frame","axis":"z","kind":"revolute","gears":["b1","b2","b0"],"axis_xy_in_parent":[0.0,0.0],"rate_abs_mean":"1","rate_rel_parent_mean":"1","note":"b1, b2, spokes, pillars, Strap, D-plate, CP, mean-Sun bar and tube (with b0), Date tube"},
  {"id":"moon","parent":"frame","axis":"z","kind":"revolute","gears":["b3"],"axis_xy_in_parent":[0.0,0.0],"rate_abs_mean":"254/19","rate_rel_parent_mean":"254/19"},
  {"id":"c","parent":"frame","axis":"z","kind":"revolute","gears":["c2","c1"],"axis_xy_in_parent":[-7.8890642192,-23.1739738876],"rate_abs_mean":"-32/19","rate_rel_parent_mean":"-32/19"},
  {"id":"d","parent":"frame","axis":"z","kind":"revolute","gears":["d1","d2"],"axis_xy_in_parent":[-13.0732908379,-38.4156284896],"rate_abs_mean":"64/19","rate_rel_parent_mean":"64/19"},
  {"id":"e_pipe","parent":"frame","axis":"z","kind":"revolute","gears":["e2","e5"],"axis_xy_in_parent":[14.1105021486,-11.0150973556],"rate_abs_mean":"-254/19","rate_rel_parent_mean":"-254/19"},
  {"id":"e_table","parent":"frame","axis":"z","kind":"revolute","gears":["e3","e4"],"axis_xy_in_parent":[14.1105021486,-11.0150973556],"rate_abs_mean":"-477/4237","rate_rel_parent_mean":"-477/4237"},
  {"id":"e_inner","parent":"frame","axis":"z","kind":"pin_slot_driven","gears":["e1","e6"],"axis_xy_in_parent":[14.1105021486,-11.0150973556],"rate_abs_mean":"-254/19","rate_rel_parent_mean":"-254/19"},
  {"id":"k","parent":"e_table","axis":"z","kind":"revolute","gears":["k1"],"axis_xy_in_parent":[20.1730752923,-15.7609337683],"rate_abs_mean":"55688/4237","rate_rel_parent_mean":"56165/4237"},
  {"id":"kp","parent":"e_table","axis":"z","kind":"pin_slot_output","gears":["k2"],"axis_xy_in_parent":[21.0398871213,-16.4381613912],"rate_abs_mean":"55688/4237","rate_rel_parent_mean":"56165/4237"},
  {"id":"l","parent":"frame","axis":"z","kind":"revolute","gears":["l2","l1"],"axis_xy_in_parent":[19.8733147053,14.2941163638],"rate_abs_mean":"-32/19","rate_rel_parent_mean":"-32/19"},
  {"id":"m","parent":"frame","axis":"z","kind":"revolute","gears":["m1","m3","m2"],"axis_xy_in_parent":[0.0,45.5],"rate_abs_mean":"53/57","rate_rel_parent_mean":"53/57"},
  {"id":"f","parent":"frame","axis":"z","kind":"revolute","gears":["f1","f2"],"axis_xy_in_parent":[19.7178722445,-73.4599900645],"rate_abs_mean":"1692/4237","rate_rel_parent_mean":"1692/4237"},
  {"id":"g","parent":"frame","axis":"z","kind":"revolute","gears":["g1","g2"],"axis_xy_in_parent":[0.0,-82.524],"rate_abs_mean":"-940/4237","rate_rel_parent_mean":"-940/4237"},
  {"id":"h","parent":"frame","axis":"z","kind":"revolute","gears":["h1","h2"],"axis_xy_in_parent":[11.5058982134,-96.2361955318],"rate_abs_mean":"940/12711","rate_rel_parent_mean":"940/12711"},
  {"id":"i","parent":"frame","axis":"z","kind":"revolute","gears":["i1"],"axis_xy_in_parent":[-0.2561529074,-107.5226876793],"rate_abs_mean":"-235/12711","rate_rel_parent_mean":"-235/12711"},
  {"id":"n","parent":"frame","axis":"z","kind":"revolute","gears":["n1","n3","n2"],"axis_xy_in_parent":[0.0,62.976],"rate_abs_mean":"-5/19","rate_rel_parent_mean":"-5/19"},
  {"id":"o","parent":"frame","axis":"z","kind":"revolute","gears":["o1"],"axis_xy_in_parent":[-24.40035,62.976],"rate_abs_mean":"1/4","rate_rel_parent_mean":"1/4"},
  {"id":"p","parent":"frame","axis":"z","kind":"revolute","gears":["p1","p2"],"axis_xy_in_parent":[12.7649722263,76.7098262717],"rate_abs_mean":"5/76","rate_rel_parent_mean":"5/76"},
  {"id":"cal","parent":"frame","axis":"z","kind":"revolute","gears":["cal1"],"axis_xy_in_parent":[24.40035,62.976],"rate_abs_mean":"-1/76","rate_rel_parent_mean":"-1/76"},
  {"id":"q","parent":"moon","axis":"radial","kind":"nonlinear_crown","gears":["q1"],"axis_xy_in_parent":[0.0,0.0],"rate_abs_mean":null,"rate_rel_parent_mean":null,"note":"Radial arbor along the Moon pointer direction (+u = Moon local +x) at z = 52.70. Angle about +u relative to moon = theta_b - theta_moon (NONLINEAR; mean +235/19)."},
  {"id":"spA","parent":"b","axis":"z","kind":"revolute","gears":["me72","me89"],"axis_xy_in_parent":[16.5726315789,28.7046399099],"rate_abs_mean":"41/24","rate_rel_parent_mean":"17/24"},
  {"id":"spB","parent":"b","axis":"z","kind":"revolute","gears":["nd62","nd64"],"axis_xy_in_parent":[23.3826859022,-13.5],"rate_abs_mean":"111/62","rate_rel_parent_mean":"49/62"},
  {"id":"spC","parent":"b","axis":"z","kind":"revolute","gears":["vn44","vn34"],"axis_xy_in_parent":[-12.8,-22.1702503369],"rate_abs_mean":"95/44","rate_rel_parent_mean":"51/44"},
  {"id":"x_me40","parent":"b","axis":"z","kind":"revolute","gears":["me40"],"axis_xy_in_parent":[28.2742081463,-1.3475747479],"rate_abs_mean":"-553/960","rate_rel_parent_mean":"-1513/960"},
  {"id":"x_me20","parent":"b","axis":"z","kind":"revolute","gears":["me20"],"axis_xy_in_parent":[32.3565856668,-15.7813612844],"rate_abs_mean":"1993/480","rate_rel_parent_mean":"1513/480"},
  {"id":"x_vn26","parent":"b","axis":"z","kind":"revolute","gears":["vn26"],"axis_xy_in_parent":[-11.0704837376,-6.6362336799],"rate_abs_mean":"-295/572","rate_rel_parent_mean":"-867/572"},
  {"id":"x_r1","parent":"b","axis":"z","kind":"revolute","gears":["r1"],"axis_xy_in_parent":[-25.1953564796,11.7487876764],"rate_abs_mean":"751/462","rate_rel_parent_mean":"289/462"},
  {"id":"t_nodes","parent":"frame","axis":"z","kind":"revolute","gears":["nd48"],"axis_xy_in_parent":[0.0,0.0],"rate_abs_mean":"-5/93","rate_rel_parent_mean":"-5/93"},
  {"id":"x_cp52","parent":"b","axis":"z","kind":"revolute","gears":["cp52","sa61"],"axis_xy_in_parent":[-8.865162115,24.3568327308],"rate_abs_mean":"27/13","rate_rel_parent_mean":"14/13"},
  {"id":"x_cp64","parent":"b","axis":"z","kind":"revolute","gears":["cp64","ma38","ju45"],"axis_xy_in_parent":[2.5100853911,-28.690407305],"rate_abs_mean":"15/8","rate_rel_parent_mean":"7/8"},
  {"id":"x_su56","parent":"b","axis":"z","kind":"revolute","gears":["su56"],"axis_xy_in_parent":[-34.3913790731,19.8558719656],"rate_abs_mean":"0","rate_rel_parent_mean":"-1"},
  {"id":"x_sa40","parent":"b","axis":"z","kind":"revolute","gears":["sa40"],"axis_xy_in_parent":[-1.0610691422,47.3062059874],"rate_abs_mean":"-167/260","rate_rel_parent_mean":"-427/260"},
  {"id":"x_sa68","parent":"b","axis":"z","kind":"revolute","gears":["sa68"],"axis_xy_in_parent":[22.14,35.7495286682],"rate_abs_mean":"869/442","rate_rel_parent_mean":"427/442"},
  {"id":"x_sa86s","parent":"b","axis":"z","kind":"pin_slot_output","gears":["sa86s"],"axis_xy_in_parent":[20.64,35.7495286682],"rate_abs_mean":"869/442","rate_rel_parent_mean":"427/442"},
  {"id":"x_ju40","parent":"b","axis":"z","kind":"revolute","gears":["ju40"],"axis_xy_in_parent":[22.0873900365,-34.4253129556],"rate_abs_mean":"1/64","rate_rel_parent_mean":"-63/64"},
  {"id":"x_ju43","parent":"b","axis":"z","kind":"revolute","gears":["ju43"],"axis_xy_in_parent":[28.5999925981,-15.6],"rate_abs_mean":"659/344","rate_rel_parent_mean":"315/344"},
  {"id":"x_ju65s","parent":"b","axis":"z","kind":"pin_slot_output","gears":["ju65s"],"axis_xy_in_parent":[27.0199925981,-15.6],"rate_abs_mean":"659/344","rate_rel_parent_mean":"315/344"},
  {"id":"x_ma40","parent":"b","axis":"z","kind":"revolute","gears":["ma40"],"axis_xy_in_parent":[-3.851213673,-46.2964367897],"rate_abs_mean":"27/160","rate_rel_parent_mean":"-133/160"},
  {"id":"x_ma71","parent":"b","axis":"z","kind":"revolute","gears":["ma71"],"axis_xy_in_parent":[-24.8984471569,-29.9653755053],"rate_abs_mean":"417/284","rate_rel_parent_mean":"133/284"},
  {"id":"x_ma80s","parent":"b","axis":"z","kind":"pin_slot_output","gears":["ma80s"],"axis_xy_in_parent":[-19.2,-33.2553755053],"rate_abs_mean":"417/284","rate_rel_parent_mean":"133/284"},
  {"id":"t_saturn","parent":"frame","axis":"z","kind":"pin_slot_driven","gears":["sa86o"],"axis_xy_in_parent":[0.0,0.0],"rate_abs_mean":"15/442","rate_rel_parent_mean":"15/442"},
  {"id":"t_jupiter","parent":"frame","axis":"z","kind":"pin_slot_driven","gears":["ju65o"],"axis_xy_in_parent":[0.0,0.0],"rate_abs_mean":"29/344","rate_rel_parent_mean":"29/344"},
  {"id":"t_mars","parent":"frame","axis":"z","kind":"pin_slot_driven","gears":["ma80o"],"axis_xy_in_parent":[0.0,0.0],"rate_abs_mean":"151/284","rate_rel_parent_mean":"151/284"},
  {"id":"t_mercury","parent":"frame","axis":"z","kind":"follower","gears":[],"axis_xy_in_parent":[0.0,0.0],"rate_abs_mean":"1","rate_rel_parent_mean":"1"},
  {"id":"t_venus","parent":"frame","axis":"z","kind":"follower","gears":[],"axis_xy_in_parent":[0.0,0.0],"rate_abs_mean":"1","rate_rel_parent_mean":"1"},
  {"id":"t_trueSun","parent":"frame","axis":"z","kind":"follower","gears":[],"axis_xy_in_parent":[0.0,0.0],"rate_abs_mean":"1","rate_rel_parent_mean":"1"}
 ],
 "meshes":[
  {"driver":"b2","driven":"c1","carrier":"frame","type":"external","module":0.48,"centre_distance":24.48,"contact_ratio":1.391,"face_overlap":1.3},
  {"driver":"c2","driven":"d1","carrier":"frame","type":"external","module":0.4472,"centre_distance":16.0992,"contact_ratio":1.361,"face_overlap":1.3},
  {"driver":"d2","driven":"e2","carrier":"frame","type":"external","module":0.4855,"centre_distance":38.59725,"contact_ratio":1.398,"face_overlap":1.0},
  {"driver":"b2","driven":"l1","carrier":"frame","type":"external","module":0.48,"centre_distance":24.48,"contact_ratio":1.391,"face_overlap":1.5},
  {"driver":"l2","driven":"m1","carrier":"frame","type":"external","module":0.4966,"centre_distance":36.9967,"contact_ratio":1.413,"face_overlap":1.5},
  {"driver":"m3","driven":"e3","carrier":"frame","type":"external","module":0.466,"centre_distance":58.25,"contact_ratio":1.397,"face_overlap":1.4},
  {"driver":"e5","driven":"k1","carrier":"e_table","type":"external","module":0.512,"centre_distance":25.6,"contact_ratio":1.394,"face_overlap":0.5},
  {"driver":"k2","driven":"e6","carrier":"e_table","type":"external","module":0.534,"centre_distance":26.7,"contact_ratio":1.394,"face_overlap":0.5},
  {"driver":"e1","driven":"b3","carrier":"frame","type":"external","module":0.5594,"centre_distance":17.9008,"contact_ratio":1.359,"face_overlap":1.3},
  {"driver":"e4","driven":"f1","carrier":"frame","type":"external","module":0.5203,"centre_distance":62.69615,"contact_ratio":1.423,"face_overlap":1.3},
  {"driver":"f2","driven":"g1","carrier":"frame","type":"external","module":0.5167,"centre_distance":21.7014,"contact_ratio":1.376,"face_overlap":1.2},
  {"driver":"g2","driven":"h1","carrier":"frame","type":"external","module":0.4475,"centre_distance":17.9,"contact_ratio":1.358,"face_overlap":1.0},
  {"driver":"h2","driven":"i1","carrier":"frame","type":"external","module":0.4347,"centre_distance":16.30125,"contact_ratio":1.34,"face_overlap":1.2},
  {"driver":"m2","driven":"n1","carrier":"frame","type":"external","module":0.514,"centre_distance":17.476,"contact_ratio":1.336,"face_overlap":1.5},
  {"driver":"n3","driven":"o1","carrier":"frame","type":"external","module":0.4171,"centre_distance":24.40035,"contact_ratio":1.404,"face_overlap":1.1},
  {"driver":"n2","driven":"p1","carrier":"frame","type":"external","module":0.5,"centre_distance":18.75,"contact_ratio":1.34,"face_overlap":1.3},
  {"driver":"p2","driven":"cal1","carrier":"frame","type":"external","module":0.5,"centre_distance":18.0,"contact_ratio":1.324,"face_overlap":1.3},
  {"driver":"fx49","driven":"nd62","carrier":"b","type":"external","module":0.486486486486,"centre_distance":27.0,"contact_ratio":1.4,"face_overlap":1.0},
  {"driver":"nd64","driven":"nd48","carrier":"b","type":"external","module":0.482142857143,"centre_distance":27.0,"contact_ratio":1.4,"face_overlap":1.0},
  {"driver":"fx51","driven":"vn44","carrier":"b","type":"external","module":0.538947368421,"centre_distance":25.6,"contact_ratio":1.39,"face_overlap":1.0},
  {"driver":"vn34","driven":"vn26","carrier":"b","type":"external","module":0.521,"centre_distance":15.63,"contact_ratio":1.352,"face_overlap":1.0},
  {"driver":"vn26","driven":"r1","carrier":"b","type":"external","module":0.521,"centre_distance":23.1845,"contact_ratio":1.374,"face_overlap":1.0},
  {"driver":"fx51","driven":"me72","carrier":"b","type":"external","module":0.538947368421,"centre_distance":33.1452631579,"contact_ratio":1.405,"face_overlap":1.0},
  {"driver":"me89","driven":"me40","carrier":"b","type":"external","module":0.5,"centre_distance":32.25,"contact_ratio":1.401,"face_overlap":1.0},
  {"driver":"me40","driven":"me20","carrier":"b","type":"external","module":0.5,"centre_distance":15.0,"contact_ratio":1.344,"face_overlap":1.0},
  {"driver":"fx56","driven":"cp52","carrier":"b","type":"external","module":0.48,"centre_distance":25.92,"contact_ratio":1.399,"face_overlap":1.0},
  {"driver":"cp52","driven":"su56","carrier":"b","type":"external","module":0.48,"centre_distance":25.92,"contact_ratio":1.399,"face_overlap":1.0},
  {"driver":"fx56","driven":"cp64","carrier":"b","type":"external","module":0.48,"centre_distance":28.8,"contact_ratio":1.405,"face_overlap":1.0},
  {"driver":"sa61","driven":"sa40","carrier":"b","type":"external","module":0.48,"centre_distance":24.24,"contact_ratio":1.392,"face_overlap":1.0},
  {"driver":"sa40","driven":"sa68","carrier":"b","type":"external","module":0.48,"centre_distance":25.92,"contact_ratio":1.395,"face_overlap":1.0},
  {"driver":"sa86s","driven":"sa86o","carrier":"b","type":"external","module":0.48,"centre_distance":41.28,"contact_ratio":1.423,"face_overlap":1.0},
  {"driver":"ju45","driven":"ju40","carrier":"b","type":"external","module":0.48,"centre_distance":20.4,"contact_ratio":1.382,"face_overlap":1.0},
  {"driver":"ju40","driven":"ju43","carrier":"b","type":"external","module":0.48,"centre_distance":19.92,"contact_ratio":1.381,"face_overlap":1.0},
  {"driver":"ju65s","driven":"ju65o","carrier":"b","type":"external","module":0.48,"centre_distance":31.2,"contact_ratio":1.41,"face_overlap":1.0},
  {"driver":"ma38","driven":"ma40","carrier":"b","type":"external","module":0.48,"centre_distance":18.72,"contact_ratio":1.376,"face_overlap":1.0},
  {"driver":"ma40","driven":"ma71","carrier":"b","type":"external","module":0.48,"centre_distance":26.64,"contact_ratio":1.396,"face_overlap":1.0},
  {"driver":"ma80s","driven":"ma80o","carrier":"b","type":"external","module":0.48,"centre_distance":38.4,"contact_ratio":1.42,"face_overlap":1.0},
  {"driver":"a1","driven":"b1","carrier":"frame","type":"crown"},
  {"driver":"b0","driven":"q1","carrier":"moon","type":"crown"}
 ],
 "pin_slots":[
  {"id":"lunar","pin_gear":"k1","slot_gear":"k2","carrier":"e_table","pin_radius":9.6,"offset":1.1,"offset_dir_local_deg":-38.0,"note":"Hipparchan lunar anomaly, amplitude asin(1.1/9.6) = 6.58 deg; slot spans 8.5..10.7 from K'"},
  {"id":"saturn","pin_gear":"sa68","slot_gear":"sa86s","carrier":"b","pin_radius":14.37,"offset":1.5,"offset_dir_local_deg":180.0},
  {"id":"jupiter","pin_gear":"ju43","slot_gear":"ju65s","carrier":"b","pin_radius":8.22,"offset":1.58,"offset_dir_local_deg":180.0},
  {"id":"mars","pin_gear":"ma71","slot_gear":"ma80s","carrier":"b","pin_radius":10.0,"offset":6.58,"offset_dir_local_deg":330.0}
 ],
 "followers":[
  {"id":"mercury","body":"t_mercury","epicycle_body":"x_me20","i":36.0,"pin_d":14.04,"pin_phase_deg":0.0,"layer":[12.6,13.6],"pin_layer_span":[12.6,15.9],"note":"pin on the me20 disk (L7) pointing back into the L5 slot; slot spans i-d..i+d = 21.96..50.04","epicycle_axis_xy_in_b":[32.3565856668,-15.7813612844]},
  {"id":"venus","body":"t_venus","epicycle_body":"x_r1","i":27.8,"pin_d":20.01,"pin_phase_deg":0.0,"layer":[13.75,14.75],"pin_layer_span":[13.75,15.9],"note":"pin on the r1 disk (L7) pointing back into the L6 slot; slot spans 7.79..47.81","epicycle_axis_xy_in_b":[-25.1953564796,11.7487876764]},
  {"id":"trueSun","body":"t_trueSun","epicycle_body":"x_su56","i":39.711744,"pin_d":1.654656,"pin_phase_deg":84.5,"layer":[24.6,25.4],"pin_layer_span":[24.6,34.0],"note":"eccentric pin fixed to su56 (C0) reaching back through a CP hole to the T1 follower; d = i/24 (Hipparchus e = 1/24)","epicycle_axis_xy_in_b":[-34.3913790731,19.8558719656]}
 ],
 "targets":[
  {"name":"crank","expr":"a","value":"223/48","cycle":"crank turns per year (magnitude)","source":"definition"},
  {"name":"mean Sun","expr":"b","value":"1","cycle":"tropical year","source":"F21"},
  {"name":"Moon (mean sidereal)","expr":"moon","value":"254/19","cycle":"254 sidereal months in 19 years","source":"F06"},
  {"name":"lunar apsidal line","expr":"e_table","value":"-477/4237","cycle":"8.8826 yr","source":"F06"},
  {"name":"lunar anomaly phase (k1 relative to e3)","expr":"k@e_table","value":"56165/4237","cycle":"anomalistic month","source":"F06"},
  {"name":"Moon phase (q1 relative to Moon pointer, magnitude)","expr":"q@moon","value":"235/19","cycle":"synodic month","source":"F06/F21"},
  {"name":"Metonic pointer","expr":"n","value":"-5/19","cycle":"5 turns = 19 years = 235 synodic months","source":"F06"},
  {"name":"Olympiad pointer","expr":"o","value":"1/4","cycle":"4-year games cycle","source":"F08"},
  {"name":"Callippic pointer","expr":"cal","value":"-1/76","cycle":"76 years","source":"F08"},
  {"name":"Saros pointer","expr":"g","value":"-940/4237","cycle":"4 turns = 223 synodic months","source":"F06"},
  {"name":"Exeligmos pointer","expr":"i","value":"-235/12711","cycle":"1 turn = 3 Saros","source":"F06"},
  {"name":"Dragon Hand (nodes)","expr":"t_nodes","value":"-5/93","cycle":"18.6 years retrograde","source":"F21 (hypothetical)"},
  {"name":"draconic month (Moon - nodes)","expr":"moon-t_nodes","value":"23717/1767","cycle":"draconic month","source":"derived"},
  {"name":"Mercury epicycle relative to b1","expr":"x_me20@b","value":"1513/480","cycle":"1513 synodic periods in 480 years","source":"F21 (hypothetical)"},
  {"name":"Venus epicycle relative to b1","expr":"x_r1@b","value":"289/462","cycle":"289 synodic periods in 462 years","source":"F21 (hypothetical)"},
  {"name":"true-Sun epicycle absolute","expr":"x_su56","value":"0","cycle":"translation only; follower mean +1","source":"F21 (hypothetical)"},
  {"name":"Mars pin gear relative to CP","expr":"x_ma71@b","value":"133/284","cycle":"133 synodic periods in 284 years; output 151/284","source":"F21 (hypothetical)"},
  {"name":"Jupiter pin gear relative to CP","expr":"x_ju43@b","value":"315/344","cycle":"315 synodic periods in 344 years; output 29/344","source":"F21 (hypothetical)"},
  {"name":"Saturn pin gear relative to CP","expr":"x_sa68@b","value":"427/442","cycle":"427 synodic periods in 442 years; output 15/442","source":"F21 (hypothetical)"},
  {"name":"Mars output","expr":"t_mars","value":"151/284","cycle":"sidereal 1.8808 yr","source":"F21 (hypothetical)"},
  {"name":"Jupiter output","expr":"t_jupiter","value":"29/344","cycle":"sidereal 11.862 yr","source":"F21 (hypothetical)"},
  {"name":"Saturn output","expr":"t_saturn","value":"15/442","cycle":"sidereal 29.467 yr","source":"F21 (hypothetical)"}
 ],
 "axes_world_xy":{
  "B":[0.0,0.0],
  "M":[0.0,45.5],
  "E":[14.1105021486,-11.0150973556],
  "L":[19.8733147053,14.2941163638],
  "C":[-7.8890642192,-23.1739738876],
  "D":[-13.0732908379,-38.4156284896],
  "N":[0.0,62.976],
  "G":[0.0,-82.524],
  "F":[19.7178722445,-73.4599900645],
  "O":[-24.40035,62.976],
  "cal":[24.40035,62.976],
  "P":[12.7649722263,76.7098262717],
  "H":[11.5058982134,-96.2361955318],
  "I":[-0.2561529074,-107.5226876793],
  "spA":[16.5726315789,28.7046399099],
  "spB":[23.3826859022,-13.5],
  "spC":[-12.8,-22.1702503369],
  "me20":[32.3565856668,-15.7813612844],
  "me40":[28.2742081463,-1.3475747479],
  "r1":[-25.1953564796,11.7487876764],
  "vn26":[-11.0704837376,-6.6362336799],
  "Dblock":[-27.5396078403,15.9],
  "cp52":[-8.865162115,24.3568327308],
  "su56":[-34.3913790731,19.8558719656],
  "cp64":[2.5100853911,-28.690407305],
  "sa86s":[20.64,35.7495286682],
  "sa68":[22.14,35.7495286682],
  "sa40":[-1.0610691422,47.3062059874],
  "ju65s":[27.0199925981,-15.6],
  "ju43":[28.5999925981,-15.6],
  "ju40":[22.0873900365,-34.4253129556],
  "ma80s":[-19.2,-33.2553755053],
  "ma71":[-24.8984471569,-29.9653755053],
  "ma40":[-3.851213673,-46.2964367897]
 },
 "axes_e3_local_xy":{"K":[20.1730752923,-15.7609337683],"Kp":[21.0398871213,-16.4381613912]}
}
```
