# Anticythère 2.0 — contrat de la phase 3D et Lean

> Ce document fixe les conventions communes. Chaque module le respecte à la lettre ; en cas de doute, il l'emporte.
> Ce n'est pas une reconstruction historique : c'est la machine moderne de `v2/`. Aucun fichier hors de `v2/` n'est
> modifié, sauf `.github/workflows/lean-v2.yml` (CI) et `.gitignore` (sorties lourdes).

## 1. Sources de vérité (lecture seule)

- `v2/spec/trains.json` : 70 arbres, rapports exacts (`shafts[]`, `rate_turns_per_day` en fraction, `phys` = sens),
  `lean_candidates` (98), `conventions`.
- `v2/spec/architecture.json` : architecture vérifiée (version 4). Clés utiles :
  - `items[]` : chaque pièce. `kind` = `cyl` (`c` = centre xy, `r`, `z` = [z0, z1]) ou `rod` (`p`, `q`, `r`, `z`).
    Roues : `wheel` (`train` ou `renvoi`), `teeth`, `m` (module), `role` (`menante`, `menee`, `fou`, `reprise`,
    `reprise_fou`), `train`, `arbor`, `partners` (ids des roues engrenées), `mesh_kind` (`external`/`internal`).
    Arbres de train : `train`, `arbor`. Pièces de renvoi : `route`, `shaft`. Blocs : `block: true`.
  - `trains_places{}` : par train, `ordre_couples` (ordre réel des couples), `reprise`, `idler_stage`, `arbors`.
  - `etages`, `platines_z`, `faces`, `tours`, `blocs`, `renvois`, `moyeux`, `carrousel_deg`, `budget_erreur`.
- `v2/research/constants.json` et `v2/research/sources/horizons/*.csv.gz` : constantes et éphémérides JPL 2000–2100.
- Code v1 réutilisable (lecture seule, à copier dans `v2/blender/lib/` avec la mention de l'origine) :
  `build/am/involute.py` (classe `Involute`, `contact_ratio`, `mesh_phase`), `build/am/outline.py` (cercles, fenêtres,
  `ccw`/`cw`), `build/blender_scripts/meshing.py` (`triangulate`, `check_mesh`), `build/blender_scripts/materials.py`.

## 2. Repère, unités, temps, sens

- **Unités** : 1 unité Blender = 1 mm (`unit_settings`: METRIC, MILLIMETERS, `scale_length` = 0.001).
- **Repère** : identique au repère machine de `architecture.json`. Blender X = x (droite vu de face), Y = y (haut),
  Z = z (vers l'observateur de la face avant). La face avant regarde +Z, la face arrière −Z, le couvercle +Y.
- **Temps** : un Empty `V2_Controleur` porte la propriété `jours` = jours depuis J2000.0 (2000-01-01 12:00 TT, sans
  ΔT). Animation de référence : 2026-01-01 → 2027-01-01, 1 image par jour (366 images, 24 i/s).
- **Sens** : `phys` = +1 est le sens **horaire vu de face** (comme la v1), donc une rotation négative autour de +Z.
  Rotation d'une pièce : `angle = −2π · phys · |taux| · jours + phase` (radians), autour de son axe.
  Pour une tringle, l'axe est sa direction (de `p` vers `q`) ; pour une tringle verticale, +Y.
- **Taux** : en tours par jour, fractions exactes de `trains.json` converties en flottant au dernier moment.

## 3. `v2/spec/scene.json` (produit par `v2/tools/scene_model.py`, Python pur)

```json
{"meta": {...}, "controller": {"name": "V2_Controleur", "j0": "J2000.0", "start_jd": ..., "frames": 366},
 "parts": [
   {"id": "venus_L#w6", "kind": "gear", "c": [x, y], "z": [z0, z1], "teeth": 189, "m": 0.5,
    "mesh": "external", "axis": [0, 0, 1], "rate": 0.0123, "phys": 1, "phase": 0.0,
    "motion": "linear", "meshes_with": ["venus_L#w5"], "collection": "V2_Trains", "label": "…", "source": "item id"},
   {"id": "venus_L#a1", "kind": "arbor", "c": [...], "z": [...], "r": 2.0, "motion": "linear", "rate": ..., ...},
   {"id": "geo_mars#r1", "kind": "rod", "p": [...], "q": [...], "z": [...], "r": 1.5, "motion": "linear", ...},
   {"id": "lune", "kind": "block", "c": [...], "r": 50, "z": [...], "motion": "fixed", "label": "à dessiner"},
   ...]}
```

- `kind` : `gear` (roue droite à développante), `crown` (couronne de moyeu, 96 dents m 0,4, dessinée comme une roue de
  champ), `bevel` (conique m 0,4, dessinée comme un tronc de cône denté simple), `arbor`, `tube`, `rod`, `block`
  (enveloppe translucide « à dessiner »), `plate`, `axis` (axe de tour), `misc`.
- `motion` : `linear` (taux constant, pilote Blender), `ephem:<clé>` (angle calculé par `ephem.py` et cuit en
  images clés), `fixed` ; `kepler` : pièces des tours de Kepler (§ 8).
- **Taux des arbres de train** : partir du taux de la sortie dans `trains.json` (`rate_turns_per_day`, `phys`) et
  remonter la chaîne `ordre_couples` (chaque couple extérieur inverse le sens, chaque pignon fou aussi) jusqu'à
  l'entrée. Contrôle obligatoire : le taux recalculé de l'entrée vaut celui de Y (ou J) à 1e-12 près.
- **Taux des renvois** : arbre et coniques d'un renvoi = taux de son `shaft` ; tringle de moyeu = 4 × ; couronnes de
  moyeu = taux de la source (Y ou J).
- **Phases** : pour chaque couple engrené, la phase de la menée fait tomber une dent dans un creux de la menante à
  `jours` = 0 (formule `mesh_phase` de la v1).
- **Sorties non linéaires** (`ephem:`) : aiguilles géocentriques, Soleil vrai, Lune vraie, Dragon, boule de phase,
  orrery, tellurion, cadrans jovien, équation du temps, aiguille de γ. Les arbres internes des blocs ne sont pas
  dessinés (blocs).

## 4. Modules et responsabilités

| Fichier | Rôle | Dépend de |
|---|---|---|
| `v2/tools/scene_model.py` + `v2/tests/test_scene_model.py` | architecture.json → scene.json (taux, phases, sens) | trains.json, architecture.json |
| `v2/tools/ephem.py` + `v2/tests/test_ephem.py` | angles des sorties en fonction des jours (Kepler J2000 + séculaire, Lune 5 termes, nœud, temps sidéral, EdT, Galiléens) ; validé contre `research/sources/horizons` | constants.json |
| `v2/blender/lib/` | copies v1 : involute, outline, triangulate (+ en-tête « copié de build/… ») | — |
| `v2/blender/parts.py` | constructeurs de maillages par `kind` (roues dentées vraies, coniques, couronnes, arbres, tringles, platines percées, blocs translucides) ; matériaux | lib/ |
| `v2/blender/faces.py` | cadrans avant et arrière, aiguilles, orrery et tellurion du couvercle, caisse et verre | architecture.json (`faces`) |
| `v2/blender/animate.py` | contrôleur, pilotes `linear`, images clés `ephem:` | scene.json, ephem.py |
| `v2/blender/check.py` | contrôles dans Blender : maillages variétés, recouvrement BVH des couples engrenés sur N échantillons, recouvrement statique entre pièces non liées | scene.json |
| `v2/blender/build_v2.py` | assemblage → `v2/out/v2.blend` | tout |
| `v2/blender/render_v2.py` | rendus : face avant, arrière, couvercle, coupe (vue éclatée), étages | v2.blend |
| `v2/tools/make_lean_v2.py` + `v2/lean/` | preuves Lean 4 (voir § 6) | trains.json, architecture.json |

Chaque module Blender expose des fonctions pures de `bpy` quand c'est possible et un `main()` testable en
`blender -b --factory-startup --python-exit-code 1 -P <script> -- <args>`.

## 5. Commandes

```
PY=/Applications/Blender.app/Contents/Resources/5.2/python/bin/python3.13   # numpy, pas de scipy
BL=/Applications/Blender.app/Contents/MacOS/Blender
cd ~/antikythera/v2
$PY tools/scene_model.py            # → spec/scene.json
$PY -m unittest discover -s tests -v
$BL -b --factory-startup --python-exit-code 1 -P blender/build_v2.py      # → out/v2.blend
$BL -b out/v2.blend --python-exit-code 1 -P blender/check.py -- --samples 24
$BL -b out/v2.blend --python-exit-code 1 -P blender/render_v2.py -- --quick
```
Sorties lourdes dans `v2/out/` (ignoré par git). Longues commandes sous `caffeinate -i`.

## 6. Lean (`v2/lean/`)

- Paquet Lake `anticythere_v2`, `lean-toolchain` identique à `lean/` (v4.35.0-rc3), Mathlib **par chemin** :
  `[[require]] name = "mathlib"  path = "../../lean/.lake/packages/mathlib"` (déjà compilée ; ne pas retélécharger).
  `warningAsError = true`.
- `v2/tools/make_lean_v2.py` génère `v2/lean/AnticythereV2/*.lean` depuis `trains.json` et `architecture.json` :
  - `Ratios.lean` : les 36 `ratio` (produit des couples = rapport exact) ;
  - `Rates.lean` : les 20 `mean_rate` et 26 `bound` (erreur relative ≤ borne, en ℚ) ;
  - `Identities.lean` : les 14 `identity` (Laplace, différentiels, temps sidéral…) et les 2 `decide` (calendrier) ;
  - `Architecture.lean` : identités de l'architecture : bus 96/24 · 24/96 = 1 ; reprises 24 → fou → 24 = 1 et sens +1 ;
    entrées Lune 40 → fou → 40 = 1 ; train J → Y réordonné = même produit ; précession 10/131 · 15/179 = 150/23449 ;
    entraxes des modules changés (0,55 · 158 / 2 = 43,45 ; 0,7 · 36 / 2 = 12,6) ;
  - `Audit.lean` : axiomes ⊆ {propext, Classical.choice, Quot.sound}, nombre de théorèmes ≥ seuil (comme `lean/`).
- `Mechanisms.lean`, **écrit à la main** (48 théorèmes) : identité du module vectoriel, ellipse à deux bras, équation
  de Kepler et boucle du résolveur, équant, Oldham, joint de Hooke. Le générateur le lit sans le réécrire
  (`tools/lean_v2/hand.py` refuse `sorry`, `axiom`, `set_option`…) ; `Audit.lean` vérifie chacun par son nom.
- `v2/tools/lean_v2_mutation_test.py` : mutants (un nombre de dents changé) qui doivent échouer.
- `.github/workflows/lean-v2.yml` : régénère, vérifie que le dépôt est à jour, compile (après `lake exe cache get`
  dans `lean/` pour fournir Mathlib au chemin).

## 7. Règles de travail

- Petits pas ; fichiers produits par des scripts ; jamais plus de ~250 lignes par écriture.
- Tester chaque module seul avant de le livrer. Ne pas lancer de rendu lourd (Cycles) : EEVEE ou Workbench, aperçus.
- Ne pas modifier les fichiers des autres modules ; signaler une incohérence du contrat plutôt que la contourner.

## 8. Tours de Kepler (phase K2)

> Inactif tant que `v2/spec/kepler.json` n'existe pas : la chaîne des § 3 à 5 est alors inchangée (mêmes objets, mêmes
> rapports hors durées, aucune clé `kepler`).

- **Sources** : `v2/spec/kepler.json` (schéma : `v2/tools/kepler/CONTRACT.md` § 5) et l'API `v2/tools/kepler/`, importée
  par `sys.path` : `motion.pose(part, state) → (x, y, θ)` (repère machine, mm, θ trigonométrique autour de +z, pièce
  posée à son pivot) et `state_from_jours(tour, jours) → {"L", "LT"}` (de `motion.py`, sinon de `frame.py`).
- **Chemins** : `--kepler-spec F --kepler-tools D` après `--` (build_v2, animate, check), sinon `V2_KEPLER_SPEC` et
  `V2_KEPLER_TOOLS`, sinon (animate, check) les chemins enregistrés par build_v2 dans `scene["v2_kepler_spec"]` et
  `scene["v2_kepler_tools"]`, sinon les défauts. Une spec donnée explicitement mais absente est une erreur.
  `build_v2.py -- --out DIR` (ou `V2_OUT`) change le dossier de sortie (défaut `v2/out`).
- **Scène** (`kepler_build.prepare_scene`) : les blocs remplacés ne sont plus construits (`uak_<p>`, `mod_<p>` ;
  `terre_maitre` pour la tour `earth`/`terre` ; ou la liste `towers.<p>.replaces`), ni les pièces d'override
  `{"remove": true}` ou `{"replaced_by": …}` ; leurs noms sont ôtés des `links`, `meshes_with`, `engages`. Overrides
  (`towers.<p>.overrides` : liste de `{"id": …, champs}` ou dictionnaire id → champs) : les champs `c z p q r r_in
  width axis phase` remplacent ceux de `scene.json` ; une pièce `synth` coaxiale à sa `source` déplacée suit son centre.
- **Objets** (`kepler_build.build_kepler`, `kepler_geom.py`) : un objet par pièce, nom = id (`#` → `.`), collection
  `V2_Kepler/V2_Kepler_<tour>`, parent Empty fixe `V2_K_<tour>` posé à l'origine de la tour (`towers.<p>.origin`,
  `center` ou `c`, sinon le centre de `axe_<p>`, sinon 0), qui porte `kepler_origin`. Maillage : formes 2D du repère
  local, îlots triangulés par CDT avec leurs trous et extrudés de z0 à z1 (variété fermée, normales sortantes) ; îlots
  qui se recouvrent : union booléenne exacte. `gear` : roue à développante de `parts.gear_loops` (`teeth`, `m`, dent 0
  sur +x local, jeu 0,03 mm), alésage `gear.bore`, sinon trou rond centré des formes, sinon support coaxial lié
  + 0,05. Origine au pivot, z au milieu de la couche, pose de repos = pose au 2026-01-01. Propriétés : `part_id kind
  tower kepler=1 law pivot z motion links meshes_with axis source label role` (+ `teeth m r_pitch ra bore` des roues,
  `union`). Matériaux par `kind` (ou `material`) : laiton (roue, bras, manivelle, crémaillère, tube), acier (goupille,
  arbre, coulisseau, suiveur), bronze (disque d'Oldham, bagues).
- **`motion = "kepler"`** (animate.py) : images clés LINEAR, une par `step_days`, de `location` x, y (repère de
  `V2_K_<tour>`) et `rotation_euler[2]` = θ, avec (x, y, θ) = `pose(pièce, state_from_jours(tour, jours))` ; θ déroulé
  (`np.unwrap`, pas de saut de 2π) puis recentré d'un multiple de 2π ; `kepler_max_step_rad` (plus grand pas de θ entre
  deux clés, doit rester ≪ π) est rendu dans les statistiques. Une roue de `scene.json` engrenée par une roue Kepler
  à pivot fixe (`gear.mesh_with`) devient menée : `motion = "kepler"`, `kepler_follow` = id de la menante,
  θ = `follow_ratio` · θ_menante + `follow_offset` (−z₁/z₂ ; une dent de la menée dans un creux de la menante sur la
  ligne des centres, règle de `scene_model`), rotation seule. Loi `fixed` : `motion = "fixed"`.
- **Contrôle** (`check.py`, section `kepler` de `out/check.json` et verdict global ; `kepler_check.py`) : maillages
  Kepler stricts ; relecture des images clés aux jours 0, 1, 57, 183, 300, 365 contre `pose` (`--kepler-tol-mm` 1e-4,
  `--kepler-tol-rad` 1e-5 : float32) ; interférences sur au moins `--kepler-states` (48 → grille 7 × 7) états (L, LT)
  de [0, 2π)² construits à la main (L décalé d'une fraction de tour propre à chaque tour ; L = LT gardé pour une
  tour où L vaut LT) plus `--kepler-traj` (12) instants de 2026 : pièces posées directement (T(x, y, z milieu)·Rz(θ)
  en double, sans les images clés), BVH entre pièces Kepler non liées dont les z se recouvrent et entre pièces Kepler
  et autres pièces de la scène non liées dont les z se recouvrent (à leur pose de la première image). Échec :
  recouvrement de surface ou pièce noyée dans un solide fermé ; contact avec un bloc : signalé. Les couples engrenés
  Kepler passent aussi par le contrôle des couples (sur 2026) et les pièces Kepler par le contrôle statique.
- **Test** : `$BL -b --factory-startup --python-exit-code 1 -P blender/test_kepler_build.py [-- --full] [--keep]`
  (fausse tour de `kepler_fake.py` et faux `motion.py`/`frame.py` dans un dossier temporaire ; cas d'interférence
  volontaire qui doit être détecté ; `--full` : build_v2.py et check.py en sous-processus).
