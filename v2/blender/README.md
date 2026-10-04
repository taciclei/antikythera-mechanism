# Anticythère 2.0 — la maquette 3D et les preuves Lean

> ⚠️ **Ce n'est pas une reconstruction historique.** C'est la machine moderne de `v2/`, construite dans Blender
> à partir de l'architecture vérifiée (`v2/spec/architecture.json`, version 4).

Les conventions communes sont dans [`CONTRACT.md`](CONTRACT.md) :
- repère et unités ;
- temps, compté en jours depuis J2000 ;
- sens de rotation, comme dans la v1 ;
- schéma de `scene.json` et découpage en modules.

## Construire et vérifier

```
PY=/Applications/Blender.app/Contents/Resources/5.2/python/bin/python3.13
BL=/Applications/Blender.app/Contents/MacOS/Blender
cd ~/antikythera/v2
$PY tools/architecture.py                    # → spec/architecture.json (placement déterministe, ~1 min)
$PY tools/scene_model.py                     # architecture.json → spec/scene.json (taux, sens, phases)
python3 tools/make_lean_v2.py && (cd lean && lake build)   # 201 théorèmes, dont les entraxes réellement placés
$PY -m unittest discover -s tests            # 55 tests (scène, éphémérides)
$BL -b --factory-startup --python-exit-code 1 -P blender/build_v2.py          # → out/v2.blend
$BL -b out/v2.blend --python-exit-code 1 -P blender/check.py -- --samples 24   # → out/check.json
$BL -b out/v2.blend --python-exit-code 1 -P blender/render_v2.py [-- --quick]  # → out/renders/
```

## Ce que contient la maquette

- **415 pièces de la mécanique.**
  - 153 roues droites à développante de 30°, avec dents vraies, jeu de 0,03 mm et fenêtres d'allègement ;
  - 19 couronnes de moyeu et 72 coniques ;
  - 72 arbres, 14 tubes et 8 axes de tour ;
  - 40 tringles et 6 platines percées.
- **28 blocs translucides étiquetés.** Ce sont les mécanismes encore « à dessiner » : unités de Kepler, modules,
  cascade de la Lune, temps, calendrier, Laplace.
- **135 objets de faces :**
  - le cadran avant, avec ses 10 aiguilles, la boule de phase, l'anneau tropique, l'horloge 24 h, l'équation du
    temps et le cadran de Jupiter ;
  - les cadrans arrière : calendrier grégorien, éclipses, Saros et Exeligmos ;
  - l'orrery du couvercle, avec le tellurion, le bras de la Lune et l'aiguille d'ombre ;
  - la caisse en chêne et la manivelle.
- **L'animation.**
  - Un contrôleur `V2_Controleur` porte `jours`, compté depuis J2000. L'animation couvre 2026, à raison d'une image
    par jour.
  - Chaque pièce linéaire est pilotée par l'expression `−2π · phys · |taux| · jours + phase`, avec les taux exacts de
    `trains.json`.
  - Les sorties astronomiques (aiguilles, orrery, cadrans) sont cuites jour par jour depuis `tools/ephem.py`.

## Ce qui a été vérifié (`out/check.json`)

| Contrôle | Résultat |
|---|---|
| Maillages (variétés, sans face d'aire nulle, volume positif) | 477 objets, 0 défaut |
| Couples engrenés, BVH sur 24 instants répartis sur un tour | **133 contacts** (67 couples droits, 66 contacts couronne/conique), **0 recouvrement** |
| Recouvrements statiques entre pièces non liées | 183 paires testées, 0 collision |
| Angles relus contre la formule du contrat | écart max 4,8·10⁻⁷ rad |
| Taux des trains recalculés depuis la sortie | égaux à ceux de Y ou J (`trains.json`) à 10⁻¹² près |

## Éphémérides (`tools/ephem.py`)

Écart maximal en longitude géocentrique sur 2000–2100, contre les tables JPL Horizons du dossier
`research/sources/` :

| Corps | Écart max |
|---|---|
| Soleil | 0,007° |
| Mercure | 0,013° |
| Vénus | 0,020° |
| Mars | 0,053° |
| Jupiter | 0,18° |
| Saturne | 0,37° (0,17° jusqu'en 2050) |
| Uranus | 0,059° |
| Neptune | 0,026° |

**Les autres sorties :**
- **Lune** : termes principaux de Meeus. L'écart reste sous 0,35° contre la formule de l'Almanach, à toutes les
  phases.
- **Calendrier** : exact.
- **Lunes de Jupiter** : longitudes moyennes, à environ 1° près.

## Preuves Lean 4 (`v2/lean/`)

`python3 tools/make_lean_v2.py` génère **201 théorèmes** depuis `trains.json` et `architecture.json`.

| Fichier | Théorèmes |
|---|---|
| Kinematics | 4 |
| Ratios | 57 |
| Rates | 46 |
| Identities | 23 |
| Architecture | 71 |

`Architecture` couvre les bus 1:1, les reprises par pignon fou, les entrées du bloc Lune, la précession et les
entraxes des modules changés.

`lake build` compile sans avertissement. Mathlib vient par chemin de `lean/`, sans téléchargement. L'audit vérifie que
les 201 théorèmes ne dépendent que des axiomes `propext`, `Classical.choice` et `Quot.sound`.

`tools/lean_v2_mutation_test.py` change un nombre de dents ; la compilation doit alors échouer. L'intégration
continue est dans `.github/workflows/lean-v2.yml`.

## Limites connues

- **Blocs non dessinés.** Les blocs sont des enveloppes : leurs mécanismes internes (UAK, modules, cascade lunaire,
  différentiels) ne sont pas encore modélisés pièce par pièce. Les aiguilles montrent donc la sortie calculée par
  `ephem.py`, et non le mouvement d'engrenages internes.
- **Couronnes et coniques simplifiées.** Elles sont dessinées comme des roues de champ et des troncs de cône dentés.
  Elles sont contrôlées par BVH, mais leurs profils ne sont pas exacts.
- **Planètes de l'orrery.** Leurs boules tournent sur leur rayon moyen et ne suivent pas les rainures elliptiques.
- **Éléments décoratifs absents :** la coulisse γ, les perles de la lunette et le voyant « bissextile ».
