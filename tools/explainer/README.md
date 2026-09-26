# Moteur astronomique de l'explainer

`engine.py` calcule ce que **montre** la machine d'Anticythère reconstruite (spec `spec/antikythera.json`, modèle
Freeth et al. 2021) et le traduit en lectures humaines en français : position du Soleil dans le zodiaque, date du
calendrier égyptien, Lune et sa phase, planètes et rétrogradations, aiguille du Dragon, cadrans de Méton, de
Callippe, des Jeux, de Saros (avec glyphes d'éclipse) et d'Exeligmos. Il sert au film (voix off, dates) et à la page
web « Comment lire la machine d'Anticythère » (via `engine_export.json`).

Pur Python 3 + numpy. Il ne lit que `spec/antikythera.json`. Utiliser le Python de Blender :

```sh
PY=/Applications/Blender.app/Contents/Resources/5.2/python/bin/python3.13
$PY tools/explainer/engine.py --selftest                 # 25 vérifications
$PY tools/explainer/engine.py read --date 2026-08-12T17:47   # machine calée, lecture complète
$PY tools/explainer/engine.py read --t 0 --model         # machine telle que am.blend (manivelle 0)
$PY tools/explainer/engine.py events --from 2026-01-01 --to 2028-12-31 --no-syzygies
$PY tools/explainer/engine.py all                        # glyphs.json, report.json, engine_export.json
# validation contre Blender (sur une COPIE de am.blend, jamais enregistrée)
cp build/out/am.blend /tmp/am_copy.blend
/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup /tmp/am_copy.blend \
    --python-exit-code 1 -P tools/explainer/validate_blend.py
```

Sorties (dans `build/out/explainer/`) : `glyphs.json` (tables de glyphes), `report.json` (dérive, éclipses
2026-2028 contre la NASA, Olympiades, machine contre ciel réel), `engine_export.json` (tout pour le portage JS),
`validate_blend.json` (comparaison avec Blender).

## API Python

| Fonction | Rôle |
|---|---|
| `Machine()` / `get_machine(calibrated)` | machine non calée (identique aux drivers de `am.blend`) ou calée J2000 |
| `state(t)`, `Machine.state(t)` | angles locaux et monde de tous les corps, `psi` des aiguilles arrière, rayons des curseurs, longitudes affichées (t scalaire ou tableau) |
| `read(t)`, `read_date('2026-08-12T17:47')` | lecture complète en français |
| `calibrate(epoch_jd)` | machine calée sur les éléments moyens réels à une époque (défaut J2000.0) |
| `glyph_table(machine, t_debut_cycle, rule)` | glyphes Σ/Η des 223 cases d'un cycle de Saros, calculés par la machine |
| `freeth2014_eym()` | table historique reconstruite (Eclipse Year Model de Freeth 2014) |
| `machine_events(date_from, date_to)` | nouvelles/pleines lunes, éclipses prédites, secteurs des Jeux, débuts/fins de rétrogradation |
| `compare_with_nasa(m)`, `drift_report(m)`, `olympiad_check(m)`, `compare_sky(m)`, `real_sky(jd)` | rapports |
| `jd_from_date`, `date_from_jd`, `parse_date`, `format_jd`, `t_from_jd`, `jd_from_t`, `egyptian_date` | temps |
| `blender_offsets(m, t_ref)` | constantes à ajouter aux drivers pour filmer de vraies dates (voir plus bas) |

Temps : `t = (JD_TT − 2451545.0) / 365.2422` (années de manivelle ; 1 an = 1 tour de b1 = 1 année tropique).
Les dates avant le 15 octobre 1582 sont juliennes ; années astronomiques (−204 = 205 av. J.-C.).

## Conventions (identiques aux drivers)

- Angle local d'un corps linéaire : `∓2π·fmod(t·n/d, 1)` (+ phase de calage), taux relatifs exacts de la spec.
  Goupille-rainure : `slot = p + atan2(e·sin(p−β), r − e·cos(p−β))`. Lune : `e_inner = e_table − kp`,
  `moon = −e_inner`. Planètes supérieures : `θ = θ_b − slot`. Suiveurs (Mercure, Vénus, Soleil vrai) :
  `θ = θ_b + g0 + atan2(d·sin λ, i + d·cos λ)`. Boule de phase : `q = θ_b − θ_moon` (0 = nouvelle lune).
- Longitude affichée (croît dans le sens horaire vu de face, 0 = début de ΚΡΙΟΣ sur +x) : `λ = −(θ_monde + marqueur)`.
  Tête (+x) de l'aiguille du Dragon = nœud ascendant (convention).
- Aiguilles arrière : `psi` = angle monde (horaire vu de l'arrière depuis 12 h). Spirales : `psi` sur 5 tours (Méton)
  ou 4 tours (Saros) comme le driver du curseur ; rayon par la spirale à deux centres (Anastasiou et al. 2014) ou
  par la même table linéaire que la F-curve du driver.
- Phases de la Lune : nouvelle lune, premier croissant, premier quartier, gibbeuse croissante, pleine lune,
  gibbeuse décroissante, dernier quartier, dernier croissant (phases principales à ±7,5°) ; fraction éclairée
  `(1 − cos D)/2`, D = élongation Lune − Soleil moyen (c'est ce que montre la boule).
- Mois dans l'année du cycle de Méton : convention moyenne (le mois appartient à l'année solaire du modèle où il
  commence), pas le schéma d'intercalation historique.

## Glyphes d'éclipse (étape 3)

Pour chaque case (un mois lunaire), la machine donne l'instant de la nouvelle et de la pleine lune (la boule de phase
passe à 0 ou 180°) et, à cet instant, la distance de l'aiguille de la Lune au nœud le plus proche (aiguille du Dragon).

- Règle `limits` (défaut) : Η si la distance est ≤ 17,0° à la nouvelle lune (F. Espenak, NASA « Periodicity of Solar
  Eclipses » : « within about 17° of a node », fourchette 15,39°-18,59°) ; Σ si la distance est ≤ 10,8° à la pleine lune
  (limite par l'ombre, calculée à partir de la géométrie moyenne par `ecliptic_limits()`, fourchette 10,1°-11,8°).
- Règle `freeth2014` : les seuils de l'EYM de Freeth 2014 transposés en degrés (20 EYu = 16,1° ; 7 EYu = 5,65° au sud
  pour le Soleil, vu depuis la Grèce ; pas de 2e Σ le mois suivant).
- Cases : machine non calée, bornes aux conjonctions moyennes, Η = nouvelle lune qui ouvre la case ; machine calée,
  cases commençant au 1er croissant (nouvelle lune moyenne + 2/38 de mois, Freeth 2014), Σ au milieu, Η = nouvelle lune
  qui termine la case.

Résultats (`glyphs.json`) comparés au cadran historique, 51 cases à glyphe, 38 Σ, 28 Η (Freeth 2014 ; notre
`freeth2014_eym()` redonne exactement ces nombres et le motif lunaire babylonien 8-7-8-7-8) :

| Table | cases | Σ | Η | écarts entre Σ (mois) |
|---|---|---|---|---|
| Historique (EYM Freeth 2014) | 51 | 38 | 28 | 6 ×33, 5 ×5 |
| Machine non calée, règle `limits` | 55 | 28 | 42 | 6 ×23, 17 ×5 |
| Machine non calée, règle `freeth2014` | 52 | 38 | 26 | 6 ×33, 5 ×5 (8-7-8-7-8) |
| Machine calée sur le 12 mai 205 av. J.-C., règle `freeth2014` | 50 | 38 | 26 | 37 Σ et 26 Η aux **mêmes cases** que Freeth, sans décalage |

La limite physique compte moins d'éclipses de Lune (l'ombre seule) et plus d'éclipses de Soleil (visibles n'importe où
sur Terre) que le cadran antique, qui prédisait les « possibilités » lunaires babyloniennes et seulement les éclipses
de Soleil visibles depuis la Grèce. Les 4 cases qui diffèrent en 205 av. J.-C. sont à la limite exacte (20 ou 7 EYu).

## Calage sur le ciel réel (étape 4)

Les **rapports d'engrenages ne changent pas** ; on choisit seulement les phases (angles à t = 0) pour qu'à l'époque
les mouvements moyens coïncident avec les éléments moyens de Meeus (*Astronomical Algorithms*, éq. 25.2-3, 47.1-7,
table 31.A, équinoxe de la date) : Soleil moyen (b), apogée solaire (su56), longitude moyenne et anomalie de la Lune
(e_table, k), nœud (t_nodes), longitudes moyennes des planètes (goupilles sa68/ju43/ma71, épicycles me20/r1).
Cadrans arrière : on compte les lunaisons réelles depuis des repères historiques. Saros : 1re pleine lune du cadran le
12 mai 205 av. J.-C. (Freeth 2014) ; Méton et Callippe : solstice d'été de 330 av. J.-C. (28 juin julien, début du
1er cycle de Callippe) ; Exeligmos : 3 Saros ; Jeux : l'aiguille entre dans ΟΛΥΜΠΙΑ au solstice d'été moyen des
années olympiques antiques (776 av. J.-C. et tous les 4 ans).

Dérive des rapports anciens (°/siècle, modèle − réel, `report.json`) : Lune +5,6 (phases en avance de 0,46 jour
par siècle), anomalie lunaire +21,6, périgée lunaire −16,1, nœuds −1,4, argument de latitude +6,9, apogée solaire −1,7,
Mercure +4,1, Vénus +1,5, Mars −0,4, Jupiter −1,4, Saturne −1,8. Au-delà de quelques siècles de l'époque, il faut
recaler (`calibrate(autre_époque)`).

Éclipses 2026-2028 (NASA, 14 éclipses) : la machine calée J2000 prédit, à la bonne syzygie, les 6 éclipses de Soleil
et les 5 éclipses de Lune par l'ombre sauf celle du 12 janvier 2028 (magnitude 0,066 ; Lune à 11,4° du nœud, limite
10,8°), et une des 3 pénombrales. Écart d'horaire : de −9,5 h à +3,5 h (Lune hipparquienne sans évection, Soleil moyen).
Aucune fausse alerte. Le cadran de Saros (table du cycle précédent, principe même du Saros) donne les mêmes
prédictions, sauf la pénombrale du 20 février 2027.

Jeux : calé sur le cycle antique, le cadran montre ΙΣΘΜΙΑ ΟΛΥΜΠΙΑ aux étés 2025 et 2029, et ΝΕΜΕΑ ΑΛΙΕΙΑ pendant
les Jeux de Los Angeles 2028 (4e année de l'olympiade) : sans année 0, les années olympiques antiques prolongées sont
celles ≡ 1 (mod 4), alors que les Jeux modernes (depuis 1896) tombent les années divisibles par 4. Chaque secteur
porte les deux fêtes de son année, comme l'original (spec `labels`, Freeth et al. 2008 SI, Iversen 2017) : an 1
ΙΣΘΜΙΑ ΟΛΥΜΠΙΑ, an 2 ΝΕΜΕΑ ΝΑΑ, an 3 ΙΣΘΜΙΑ ΠΥΘΙΑ, an 4 ΝΕΜΕΑ ΑΛΙΕΙΑ ; `games_fr()` donne le nom français.

Machine contre ciel réel 2026-2028 (`report.json`, référence Meeus + JPL) : Soleil vrai ≤ 0,5°, Lune ≤ 4,6°,
Mercure ≤ 11,4°, Vénus ≤ 3,7°, Mars ≤ 8,0°, Jupiter ≤ 7,3°, Saturne ≤ 6,0° (pas d'anomalie zodiacale dans le
modèle) ; débuts de rétrogradation à 0-6 jours des vrais.

## Validation contre Blender (étape 1)

`validate_blend.py` pose `AM_Controller["crank"]` à 22 valeurs (de −4712,5 à 9999,75), lit toutes les rotations des
Empties `B_*`, les rotations monde des aiguilles, des 6 sphères planétaires, de la boule de phase et des aiguilles
arrière, et la position des curseurs : **erreur max 6,4e-7 rad** (critère 1e-4), curseurs 1e-5 mm. Blender lit la
variable de driver en **float32** : une manivelle non représentable (ex. 2026,6131) s'écarte de 5e-3 rad du calcul
float64 ; on reproduit Blender à 1e-7 rad en arrondissant `t` en float32 d'abord.

## Pour le film : filmer de vraies dates

`apply_calibration_blend.py` ajoute aux drivers d'une **copie** de `am.blend` les constantes `blender_offsets()` :
décalage temporel exact de tous les engrenages plus phases de calage. La manivelle devient locale : `crank = t − t_ref`.
Vérifié à 7,7e-7 rad. Garder `|crank|` sous ~10 ans (précision float32). Limite : en très gros plan, les dents des
quelques sorties recalées ne sont plus exactement en prise avec leurs voisines.

## Portage JavaScript

`engine_export.json` contient : taux exacts en fractions (`corps`), paramètres goupille-rainure, suiveurs, marqueurs,
spirales, cadrans secondaires, libellés grecs et français, formules en clair, phases (`cale_J2000`), époque et
repères du calage, dérive, limites, glyphes (non calé, calé J2000 avec `t_debut_cycle`, historique EYM) et des
**vecteurs de test** (états et lectures à plusieurs t) pour vérifier le portage. En JS, `fmod` = opérateur `%`
(même signe que le dividende, comme en C).

## Honnêteté

Les trains planétaires, le Soleil vrai et l'aiguille du Dragon sont **hypothétiques** (Freeth et al. 2021). Les
glyphes sont **calculés par notre modèle**, sauf la table EYM qui reproduit la reconstruction publiée de Freeth 2014.
Le calage moderne sert à la démonstration : les constructeurs antiques calaient la machine sur leur propre époque.
La machine n'était **pas** un instrument de navigation.

## Sources

- T. Freeth, *Eclipse Prediction on the Ancient Greek Astronomical Calculating Machine Known as the Antikythera
  Mechanism*, PLoS ONE 9(7):e103275 (2014) : 51 glyphes, 38 Σ, 28 Η, EYM, FM1 = −204 mai 12.
- T. Freeth et al., *A Model of the Cosmos in the ancient Greek Antikythera Mechanism*, Sci. Rep. 11:5821 (2021).
- J. Meeus, *Astronomical Algorithms*, 2e éd. (ch. 7, 25, 31, 47) ; JPL, *Approximate Positions of the Planets*,
  https://ssd.jpl.nasa.gov/planets/approx_pos.html (table 1800-2050).
- F. Espenak (NASA/GSFC) : https://eclipse.gsfc.nasa.gov/SEdecade/SEdecade2021.html,
  https://eclipse.gsfc.nasa.gov/LEdecade/LEdecade2021.html, https://eclipse.gsfc.nasa.gov/SEsaros/SEperiodicity.html.
- J. Evans, *The History and Practice of Ancient Astronomy* (1998) p. 186-187 : cycle de Callippe (330 av. J.-C.).
- Ère de Nabonassar (1 Thot = 26 février 747 av. J.-C., JD 1448638) pour l'année vague égyptienne.
