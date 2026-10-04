# Tours de Kepler — contrat de conception (phase K1, Python pur)

> Anticythère 2.0, machine moderne (pas une reconstruction historique). Ce contrat fixe les conventions communes aux
> agents de la phase K1 ; en cas de doute, il l'emporte. La phase K2 (Blender, Lean, page) viendra après et ne lira
> que `v2/spec/kepler.json` et `v2/tools/kepler/` (API de `motion.py`).

## 1. Ce qu'on dessine

Pour chacune des 7 tours (`mercury venus mars jupiter saturn uranus neptune`), la chaîne de calcul complète, pièce par
pièce, sous l'étage des trains (E4) :

1. **E3, couche `uak` (z 187–204)** : l'UAK de la planète (entrée L sur l'axe de la tour) et la **copie de l'UAK
   Terre** (entrée Y, tube coaxial sur le même axe). Les arbres L et Y arrivent par `axe_<p>#haut` (r 4, z 155–221).
2. **E3, couche `T1` (z 204–219), platine P2 (z 219–221)** : passage des sorties vers E2 ; roue de prise
   héliocentrique (46 dents, m 0,5, r 12) qui mène `orr_<p>#prise` à 23 mm (côté `L.TAKEOFF`).
3. **E2, couche `mod` (z 221–249)** : le module vectoriel (bras 1, chaîne 1:1, bras 2, suiveur O géocentrique vers
   l'avant, suiveur F héliocentrique vers l'arrière pour les planètes extérieures).
4. **Au centre** : l'**UAK maîtresse de la Terre** (`terre_maitre`, E3 `uak`, r 28) : entrée Y sur `axe_Y` (finit à
   z 195,5), sortie Soleil vrai sur `axe_soleil` (centre, de z 195,5 vers l'avant), prise de l'orrery
   `orr_earth#prise_axe` (r 8,5, E3 T1) vers `orr_earth#prise` à 16 mm.

Mécanismes (voir `v2/research/mechanisms.md` §1–2, `research/calc/kepler_models.py`, `modules_results.json`) :
équant bissecté (Vénus, Jupiter, Saturne, Uranus, Neptune, Terre), équant + épicyclet EQE (Mars), résolveur de
Kepler RK + ellipse à deux bras (Mercure, bloc r 42). Les modules suivent §2.3 (identité du décalage du pivot).

## 2. Données figées

- Éléments : `research/constants.json`, `planets.<p>.jpl_table1_1800_2050` (et `earth`), **évalués en 2050.0**
  (T = 0,5 siècle) pour a, e, ϖ (formes figées, repère fixe J2000). L₀ = L à J2000 (table 1).
- Longitudes moyennes de la machine : L(j) = L₀ + 360°·rate·j, rate = `rate_turns_per_day` (Fraction) des arbres
  `<p>_L` et `Y` de `spec/trains.json`, j = jours depuis J2000.
- Échelles et bras des modules : `research/calc/modules_results.json` (point de départ ; on peut changer s, en le
  justifiant, par exemple pour que bras = m·(z₀ + z_fou) exactement).

## 3. Repère, angles, sens

- Repère machine (mm) : x à droite, y en haut, z vers l'observateur de la face avant. Axe de la tour = `L.TOWERS[p]`.
- **Longitude → direction machine** : comme le cadran avant (φ = −λ, 0° en haut, horaire vu de face),
  u(λ) = (sin λ, cos λ). Toute position héliocentrique (x_h, y_h) du plan de l'écliptique se dessine en
  s·(r sin λ, r cos λ) : c'est un miroir, qui conserve distances et identités vectorielles.
- Angle de pièce θ (radians) : rotation trigonométrique autour de +z dans le repère machine (θ = 0 : axe local x
  le long de +x). Une pièce dont le « nez » montre la longitude λ a θ = π/2 − λ.

## 4. Paquet `v2/tools/kepler/` (numpy seul ; pas de scipy, pas de shapely, pas de bpy)

| Fichier | Rôle |
|---|---|
| `frame.py` | constantes figées (éléments 2050, L₀, taux Fraction), u(λ), θ(λ), `state_from_jours(p, j)` → `{"L": rad, "LT": rad}` (longitudes moyennes continues) |
| `geom2d.py` | formes 2D (cercle, anneau, oblong, rainure, polygone avec trous) ; transformations ; distance minimale vectorisée entre formes ; point dans forme |
| `laws.py` | lois exactes : équant, EQE, Kepler (Newton), modules (G, O, F), suiveurs ; formes fermées de référence |
| `parts.py` | schéma d'une pièce (§5), constructeurs (bras rainuré, manivelle à goupille, disques d'Oldham, bagues, roues) |
| `tower_eq.py`, `tower_mars.py`, `tower_mercury.py`, `earth_master.py` | une fonction `build(p) -> Tower` par type |
| `motion.py` | `pose(part, state) -> (x, y, θ)` ; `outputs(p, state)` (φ_C,p, φ_C,T, λ_géo, λ_hélio) ; utilisé par K2 |
| `verify.py` | CLI : `$PY tools/kepler/verify.py [--quick]` → `spec/kepler_report.json`, code de sortie ≠ 0 si un contrôle échoue |
| `export.py` | → `spec/kepler.json` (§5) |
| `../../tests/test_kepler.py` | tests unitaires (unittest) |

Fichiers courts (≤ ~250 lignes par écriture). Docstrings et commentaires en français, comme le reste de `v2/tools`.

## 5. Pièce (`spec/kepler.json` → `towers.<p>.parts[]`)

```json
{"id": "mars#uak_bras", "tower": "mars", "kind": "slotted_arm|crank|pin|oldham_disc|bush|gear|arm|follower|tube|arbor|slider|rack|plate_bush",
 "z": [z0, z1], "shapes": [{"type": "polygon", "outer": [[x, y], ...], "holes": [[[x, y], ...]]} | {"type": "circle", "c": [x, y], "r": r}],
 "gear": {"teeth": 46, "m": 0.5, "mesh_with": ["..."]} ,          // facultatif ; formes = cercle de tête pour le contrôle
 "motion": {"law": "<clé>", "pivot": [x, y]},                     // pose donnée par motion.pose ; "fixed" pour une pièce fixe
 "links": ["ids des pièces en contact voulu (goupille/rainure, palier, engrènement, Oldham)"],
 "label": "texte français court", "role": "…"}
```
Formes dans le **repère local** de la pièce (origine au pivot, θ = 0). Toutes les longueurs en mm.
`towers.<p>` porte aussi : `inputs`, `outputs` (arbre, point xy, z, loi), `overrides` (pièces de `architecture.json`
déplacées, par exemple la roue de prise centrée en F et sa partenaire à 23 mm de F, ou l'arbre `geo_<p>#z0` en O),
`budget_z` (plans utilisés), `params` (ρ, s, bras, nombres de dents).

## 6. Contrôles obligatoires (`verify.py`)

1. **Exactitude des lois** : la sortie calculée *à partir de la géométrie des pièces* (goupille dans la rainure, etc.)
   égale la forme fermée à 1e-9 rad ; identité du module G − O = s·(planète − Terre) à 1e-9 mm.
2. **Contre les éphémérides** (`tools/ephem.py`, 2000–2100, pas ≤ 2 j) : λ géocentrique (suiveur O) vs
   `geo_longitude`, λ héliocentrique vs `helio_longitude`, Soleil vs `sun_longitude`. Écart max ≤ budget §2.5 de
   `mechanisms.md` × 1,2 + 0,01° (Me 0,26 · Vé 0,21 · Ma 0,24 · Ju 0,07 · Sa 0,08 · Ur 0,05 · Ne 0,02 ; Soleil 0,01).
3. **Contraintes** : goupille toujours dans sa rainure (marge ≥ 0,3 mm aux extrémités), jeu goupille/rainure 0,02 mm ;
   course des disques d'Oldham dans leurs rainures ; entraxes d'engrènement = m(z₁ + z₂)/2 à 1e-9 ; angle de
   transmission des goupilles ≤ 60°.
4. **Interférences sur tout l'espace d'état** : grille (L, LT) ∈ [0, 2π)² d'au moins 72 × 72 (plus la trajectoire
   2026 jour par jour) ; pour toute paire de pièces non liées dont les z se recouvrent : distance 2D ≥ 0,5 mm. Les
   pièces liées : contrôle du contact voulu à la place.
5. **Encombrement** : chaque pièce dans sa couche (z) ; pièces mobiles de E3 `uak` dans r ≤ 28 (Mercure 42) autour de
   l'axe ; module dans r ≤ R + 5 ; aucune collision (z et xy, jeu 0,5 mm) avec les pièces de `architecture.json`
   non liées (arbres, tringles, roues de prise, blocs voisins), compte tenu des `overrides`.
6. **Fabricabilité** : épaisseur de pièce ≥ 1 mm, jeu axial entre plans ≥ 0,3 mm, largeur de bras ≥ 1,5 mm, paroi
   ≥ 0,8 mm, goupille Ø ≥ 1 mm, rayon de roue ≥ module·(z/2 + 1), dents dans [10, 220], m ≥ 0,4.

Tout résultat va dans `spec/kepler_report.json` : par tour, chiffres et `ok`. Rien n'est « supposé » : un contrôle
non fait est un échec.

## 7. Règles de travail

- Ne modifier que `v2/tools/kepler/`, `v2/tests/test_kepler*.py`, `v2/spec/kepler.json`,
  `v2/spec/kepler_report.json`, `v2/study/kepler.md`. Lecture seule pour tout le reste. Pas de git, pas de Blender.
- Python : `PY=/Applications/Blender.app/Contents/Resources/5.2/python/bin/python3.13` (numpy). Lancer depuis
  `~/antikythera/v2`. `verify.py --quick` < 1 min ; complet < 5 min.
- Une impossibilité (place, budget z) se signale dans le rapport (`requested_changes`) avec le minimum nécessaire ;
  ne pas tricher sur les contrôles.
