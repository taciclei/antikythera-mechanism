# Preuves Lean 4 d'Anticythère 2.0

Ce dossier est un paquet Lake (`anticythere_v2`) construit sur [Mathlib](https://github.com/leanprover-community/mathlib4).
Ses théorèmes portent sur la machine moderne de `v2/` (pas sur la reconstruction historique, voir `lean/` pour la v1).
Les fichiers `AnticythereV2/*.lean` sont **générés** par `v2/tools/make_lean_v2.py` à partir de
`v2/spec/trains.json` et `v2/spec/architecture.json` ; ils ne s'éditent pas à la main. Seule exception,
`AnticythereV2/Mechanisms.lean` est **écrit à la main** (comme `PinSlot.lean` en v1) : le générateur le lit, le
contrôle, l'importe dans la racine et dans l'audit, mais ne le réécrit jamais (voir plus bas).

Un `lake build` réussi signifie :

- chaque théorème est entièrement prouvé : `warningAsError = true`, donc aucun `sorry` ne passe ;
- aucun théorème n'utilise d'axiome autre que `propext`, `Classical.choice`, `Quot.sound` (pas de `sorryAx`, pas de
  `native_decide`) : `AnticythereV2/Audit.lean` le vérifie pour chaque déclaration et exige au moins 249 théorèmes
  documentés (201 générés + 48 écrits à la main, chacun de ces derniers vérifié par son nom) ;
- les énoncés sont ceux du générateur : la CI régénère et compare (`git diff --exit-code v2/lean`).

Les preuves générées n'utilisent que `norm_num`, `decide` (`decide +kernel` pour les 400 années du calendrier),
`ring` et `linear_combination` (avec `rw`/`simp only`/`push_cast` pour déplier les définitions, et une récurrence
forte pour étendre le calendrier à toutes les années) ; tout y est énoncé dans ℚ ou ℕ. `Mechanisms.lean` travaille
dans ℝ (et ℝ³ pour le joint de Hooke) avec la trigonométrie, les valeurs intermédiaires et les dérivées de Mathlib.

## Ce qui est prouvé (249 théorèmes : 201 générés, 48 écrits à la main)

| Module | Contenu | Théorèmes |
|---|---|---|
| `Kinematics` | Les 70 arbres, une loi de transmission moyenne par arbre (dents des `stages`, différentiels, unités, pas à pas). `determined` : toute famille de vitesses admissible vaut ω J · `rate`, où `rate` est la table **déclarée** (`rate_turns_per_day`) ; `consistent`, `moves`, `one_dof` (un seul degré de liberté). | 4 |
| `Ratios` | Les 36 candidats `ratio` : sortie = produit des couples × source, produit = rapport exact réduit, vitesse rapportée à J = `rate_vs_J`. Plus 21 `sens_*` : rapport de Willis signé (extérieur −a/b, intérieur ou chaîne +a/b, pignon fou −1) = phys(sortie) · phys(source) · \|rapport\|. | 57 |
| `Rates` | Les 20 `mean_rate` (unités non linéaires : vitesse moyenne = combinaison exacte des entrées) et les 26 `bound` : \|vitesse − cible\| · 360 · 36525 < borne (dérive en degrés par siècle, énoncé exact du candidat) **et** erreur relative \|vitesse − cible\| ≤ r · \|cible\| (r = majorant à deux chiffres, CONTRACT § 6) ; cibles = décimales exactes de `constants.json`. | 46 |
| `Identities` | Les 14 `identity` (évection, temps sidéral, équation du temps de moyenne nulle, Laplace Io–Europe–Ganymède, anneau des dates…) et les 2 `decide` : `calendar` (pour **tout** n, les cames C4, C100, C400 lues le 28 février font sauter le 29 février exactement les années communes de 2000 + n ; 400 cas puis périodicité) et `week_400` (146097 = 7 · 20871), avec `skips_400`, `skip_periodic`, `leap_periodic`, `calendar_400`, `week_wheel`. Les prémisses du modèle des cames sont prouvées depuis `Kinematics` : `calendar_gearing` (366 positions de l'anneau, un pas de croix = une position, périodes 1464 / 36600 / 146400 des cames, 400 tours en 146097 jours) et `skip_rate` (303 sauts comptés sur les cames / 146097 jours = vitesse de la croix de saut). | 23 |
| `Architecture` | Les 13 trains placés roue par roue (`place_*` : bus, reprise, couples dans l'ordre réel, pignons fous → même produit que trains.json et bon sens), 7 reprises 24 → fou → 24 (rapport 1, sens +1), le bus 96/24 · 24/96 = 1, les 3 entrées du bloc Lune 40 → fou → 40, la précession 10/131 · 15/179 = 150/23449, les 2 modules changés (0,55 · 158 / 2 = 43,45 ; 0,7 · 36 / 2 = 12,6) et les entraxes des 44 couples placés. | 71 |
| `Mechanisms` (écrit à la main) | Identités exactes des mécanismes non linéaires : module vectoriel (G − O = s·(planète − Terre), planètes extérieures et intérieures, pivots O et F), ellipse à deux bras contrarotatifs et distance au foyer a(1 − e cos E), équation de Kepler (∃! E, résolveur continu, croissant, dérivable, sans point mort ; boucle coulisse–crémaillère–différentiel), équant bissecté (goupille unique et continue), accouplement d'Oldham, joint de Hooke = réduction à l'équateur. Détail ci-dessous. | 48 |
| `Audit` | Axiomes standard seulement, chaque théorème écrit à la main vérifié par son nom, nombre minimal de théorèmes (générés + écrits à la main). | — |

## Modèle et limites

- `ω x` est une vitesse **moyenne** en tours par jour, signée dans le sens astronomique direct (`conventions.sign`).
  Les unités non linéaires (Kepler, modules vectoriels, cascade lunaire, joint de Hooke) font un tour par tour : leur
  loi dans `Kinematics` est l'égalité des vitesses moyennes. `Mechanisms` prouve les identités géométriques exactes
  de leur mouvement instantané (mécanismes idéalisés), sans les relier à `Kinematics` ni aux dimensions des pièces
  (`v2/spec/kepler.json`, contrôlées en Python) ; la cascade lunaire n'y est pas traitée.
- La croix de saut est un pas à pas de 303 pas pour 146097 jours ; `skips_400` prouve que c'est le nombre d'années
  communes en 400 ans, et `calendar` que les cames le réalisent année par année.
- Le bus (couronne de moyeu → pignon → tringle → pignon → couronne) est compté de rapport 1 et de même sens : c'est
  une **hypothèse** de montage (CONTRACT § 3 fait tourner les couronnes de moyeu au taux signé de la source), non
  vérifiée par Lean ; ses dents (96, 24) sont lues dans le texte de `roues.rows`. Géométrie de `items` : les deux
  pignons sont entre les deux axes (à 17,2 mm de chaque centre, du côté de l'autre axe) ; avec les deux couronnes
  taillées sur la même face, le bus INVERSERAIT le sens. Il faut donc des couronnes sur des faces opposées (un
  pignon dessus, l'autre dessous) : contrainte à respecter par le modèle 3D. Les couples coniques des renvois ne
  sont pas dans `items` avec leurs dents.
- Entraxes : centres de `architecture.json` (arrondis au µm), tolérance 1,5 µm. Les dents des entrées du bloc Lune
  sont déduites de leurs rayons (r = m z / 2 + m) et recoupées avec `sens`.
- Les bornes `bound_*` suivent l'énoncé exact des candidats (dérive en °/siècle, borne indépendante des dents) ;
  le second conjoint majore l'erreur relative par un r calculé sur la machine elle-même (il la caractérise, ce
  n'est pas une exigence indépendante).
- Hors de Lean : recouvrement des dentures, collisions, interférences (contrôles Python et Blender).

## Construire

Mathlib est prise **par chemin** dans `../../lean/.lake/packages/mathlib` (celle de la v1, déjà compilée) ;
`lake-manifest.json` déclare aussi par chemin ses dépendances (batteries, Qq, aesop…) : rien n'est téléchargé et
rien n'est écrit dans `lean/`.

```sh
cd lean && lake exe cache get && cd ..          # une fois : Mathlib compilée pour lean/ (≈ 5 Go)
python3 v2/tools/make_lean_v2.py                # régénère v2/lean/AnticythereV2*.lean
cd v2/lean && lake build                        # ≈ 1 min ; « audit : 249 théorèmes documentés (201 générés + 48 écrits à la main …) »
cd ../.. && python3 v2/tools/lean_v2_mutation_test.py   # ≈ 3,5 min
```

Le test de mutation change **un** nombre de dents dans une copie temporaire de la spécification (Y 31 → 32,
nœuds 109 → 110 dans trains.json ; roue placée de Vénus 67 → 68 dans architecture.json ; Callisto 51 → 52 avec les
vitesses déclarées et le candidat `ratio` recalculés, mutant « cohérent » que seules les bornes peuvent rejeter),
régénère un paquet complet dans un dossier temporaire avec `--no-check` (Python ne bloque pas : Lean seul juge ;
`Mechanisms.lean` y est recopié tel quel) et lance `lake build`. Chaque mutant doit échouer avec une erreur Lean dans le fichier attendu (`Kinematics`,
`Kinematics`, `Architecture`, `Rates`) ; le témoin non muté doit compiler.

La CI (`.github/workflows/lean-v2.yml`) installe elan, lance `lake exe cache get` dans `lean/`, régénère, vérifie que
le dépôt est à jour, puis compile `v2/lean`.

## Le fichier écrit à la main : `AnticythereV2/Mechanisms.lean`

Plan `ℝ × ℝ`, `u φ = (cos φ, sin φ)`, norme euclidienne explicite (`nsq`, `deucl`, reliée à la distance de
`WithLp 2 (ℝ × ℝ)` par `deucl_eq_dist`). Sources : `v2/research/mechanisms.md` § 1.2, § 2.3, § 4.5, § 8 et
`v2/tools/kepler/CONTRACT.md`. Théorèmes principaux (48 en tout, avec les lemmes de géométrie plane) :

| Mécanisme | Théorèmes |
|---|---|
| Module vectoriel (§ 2.3) | `module_exterieur`, `module_interieur` : si planète = C_p + a_p·u(φ_p), Terre = C_T + a_T·u(φ_T), G = P₁ + s·a_p·u(φ_p) + s·a_T·u(φ_T + π) (bras échangés pour Mercure et Vénus) et O = P₁ + s·(C_T − C_p), alors G − O = s·(planète − Terre) ; `suiveur_geocentrique` (le suiveur en O lit la direction et la distance géocentriques) ; `pivot_heliocentrique` (F = P₁ − s·C_p) ; `ecart_pivots` (O − F = s·C_T) ; `chaine_un_un` (la chaîne 1:1 conserve l'angle absolu). |
| Ellipse à deux bras (§ 1.2 e) | `deux_bras` : ((a+b)/2)·u(ϖ+E) + ((a−b)/2)·u(ϖ−E) = rot ϖ (a cos E, b sin E) ; `deux_bras_mem_ellipse` ; `deux_bras_dist_foyer` : avec c = a e et b² = a²(1 − e²), distance au foyer = a(1 − e cos E). |
| Résolveur de Kepler (§ 1.2 e) | `kepler_strictMono`, `kepler_continuous`, `kepler_surjective`, `kepler_existsUnique` (0 ≤ e < 1 : ∀ M ∃! E, E − e sin E = M) ; `kepler_deriv_mem` (dM/dE ∈ [1 − e, 1 + e]) ; `kepler_solution` (la solution est continue, strictement croissante, 1/(1 − e)-lipschitzienne, dérivable de dérivée 1/(1 − e cos E)) ; `boucle_resolveur`, `boucle_resolveur_existsUnique` (x = R_y sin E, ρ_p δ = x, M = E − δ, R_y/ρ_p = e ⟺ Kepler) ; `resolveur_mercure` (3,084/15 = 0,2056, facteur dans [0,79 ; 1,21]). |
| Équant bissecté (§ 1.2 b) | `equant_rayon_unique` : \|Q − C\| = eρ, 0 ≤ e < 1 ⟹ toute demi-droite issue de Q coupe le cercle pour un unique t > 0 ; `equant_point` (forme close `tEquant`) ; `tEquant_continuous`, `equant_goupille_continuous`. |
| Accouplement d'Oldham | `oldham_modulo_pi` (languettes à angle droit parallèles aux rainures ⟹ même rotation modulo π) ; `eq_of_modulo_pi_of_continuous`, `oldham_meme_rotation` (par continuité depuis l'égalité : même rotation) ; `oldham_centre_cercle` (le disque décrit le cercle de diamètre O₁O₂). |
| Joint de Hooke (§ 4.5) | `hooke_geometrie` ; `hooke_croisillon` : branches du croisillon perpendiculaires ⟺ sin φ cos λ = cos ε cos φ sin λ ; `hooke_tan` (tan φ = cos ε tan λ) ; `ascensionDroite_relation`, `ascensionDroite_existe` (réduction à l'équateur, même loi) ; `hooke_ascensionDroite_modulo_pi`, `hooke_egale_ascensionDroite` (avec calage à l'instant 0, la sortie du joint EST l'ascension droite). |

Règles (contrôlées par `v2/tools/lean_v2/hand.py` à chaque génération) : un seul `namespace AnticythereV2.Mechanisms`,
une docstring par théorème (sinon l'audit ne le compterait pas), et, hors commentaires, ni `sorry`, `admit`,
`native_decide`, `axiom`, `private` (un nom privé échapperait à l'audit), `set_option`, `opaque`, `unsafe`,
`implemented_by`, `extern`, ni métaprogrammation (`run_cmd`, `elab`, `macro`…). Après avoir ajouté ou renommé un
théorème, relancer `python3 v2/tools/make_lean_v2.py` : la liste des noms et le seuil de `Audit.lean` suivent (la CI
refuse un `Audit.lean` en retard, et un nom disparu fait échouer la compilation).

Non prouvé ici : l'équant comme goupille-rainure menée par la rainure (monotonie stricte de la manivelle, vitesse
moyenne, écart borné : l'analogue de `isGreatest_abs_lag` de la v1), l'épicyclet correcteur de Mars (EQE),
l'équation du temps L − α elle-même (simple différentiel) et toute valeur numérique des pièces.
