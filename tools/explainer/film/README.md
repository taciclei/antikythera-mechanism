# Film « Le ciel dans une boîte » : ligne de temps

Ce dossier décrit le film explicatif image par image (25 i/s, 1920 × 1080, 4 009 images, 2 min 40,36 s), à partir de
la voix off, du découpage relu (`build/out/explainer/script.md`) et du moteur astronomique
(`tools/explainer/engine.py`, identique aux drivers de Blender). Il ne rend rien et n'ouvre jamais `am.blend` ni
`am_atelier.blend` en écriture. Le montage (rendu Blender, incrustations, mixage) lit `timeline.json`.

| Fichier | Rôle |
|---|---|
| `filmlib.py` | chemins, temps ↔ image, réimplémentation exacte des interpolations de clés de Blender (CONSTANT, LINEAR, SINE, QUAD, CUBIC), texte du compteur |
| `words.py` | horodatage mot à mot de la voix (STT parakeet local) → `film/words.json` |
| `timeline.py` | la ligne de temps : plans, manivelle, caméras, surlignages, callouts, incrustations, sous-titres, placement audio ; lance ensuite `verify_beats.py` |
| `verify_beats.py` | contrôles : lectures de la machine avec `engine.py`, synchro avec la voix, audio, sous-titres, mise en page, objets du `.blend` |
| `build_film.py` | (Blender) la scène du film `film/film.blend`, construite depuis `am_atelier.blend` (lu seulement) et `timeline.json`, puis contrôlée → `film/film_check.json` |
| `anchors.py` | (Blender) position 2D image par image des ancres des callouts, dans `film.blend` → `film/anchors.json` |
| `render_frames.py` | (Blender) rendu EEVEE reprenable des images 3D du film (et de l'incrustation 3.4), réglages finaux et banc d'essai |
| `composite.py` | (venv) montage image par image : 3D, schémas, incrustations, callouts et filets, compteur, titres, sous-titres, fondus → `film/comp/%05d.png` |
| `encode.py` | (venv) encodage H.264 + AAC avec le mixage de la voix de `audio_placement.json`, puis contrôle du MP4 |

## Commandes

```sh
PY=/Applications/Blender.app/Contents/Resources/5.2/python/bin/python3.13
$PY tools/explainer/film/timeline.py                 # écrit les 3 sorties + verification.json (code 1 si ERREUR)
$PY tools/explainer/film/timeline.py --no-verify     # sorties seules
$PY tools/explainer/film/verify_beats.py --audio --blend   # tous les contrôles, dont le rendu de la piste voix
                                                     #   (ffmpeg, fichier temporaire) et am_atelier.blend en lecture
~/voxtral-tts/bin/python tools/explainer/film/words.py     # seulement si la voix change

BL=/Applications/Blender.app/Contents/MacOS/Blender
$BL -b build/out/am_atelier.blend --factory-startup --python-exit-code 1 -P tools/explainer/film/build_film.py
                                                     # film.blend (≈ 3 s) puis contrôles -> film_check.json (code 1 si échec)
$BL -b build/out/explainer/film/film.blend --factory-startup --python-exit-code 1 \
    -P tools/explainer/film/build_film.py -- --verify-only           # contrôles seuls
$BL -b build/out/explainer/film/film.blend --factory-startup --python-exit-code 1 \
    -P tools/explainer/film/anchors.py                              # anchors.json (≈ 5 s)
$BL -b build/out/explainer/film/film.blend --factory-startup --python-exit-code 1 \
    -P tools/explainer/film/render_frames.py -- --res 1920x1080 --out build/out/explainer/film/frames --start 1 --end 4009
```

À relancer dans cet ordre après toute modification de `timeline.py` : `timeline.py`, `build_film.py`, `anchors.py`, puis
le rendu (les images déjà rendues sont gardées : effacer celles des plans modifiés).

`timeline.py` tourne en quelques secondes. Il appelle deux fois le Python du venv `~/voxtral-tts` (sans rien écrire) :
`inserts.timing()` pour les métadonnées des incrustations tant que `build/out/explainer/inserts/timing.json` n'existe
pas, et `overlay.callout_size()` pour mesurer les boîtes des callouts avec les vraies polices.

## Entrées et sorties

Entrées : `voice/timing.json`, `voice/narration.srt`, `voice/ch1.wav` … `ch7.wav`, `film/words.json`,
`diagrams/timing.json` et les séquences PNG, `tools/explainer/inserts.py`, `tools/explainer/overlay.py`,
`tools/explainer/engine.py`.

Sorties (dans `build/out/explainer/film/`) :

- `timeline.json` : la ligne de temps complète (format ci-dessous) ;
- `subtitles_film.srt` : les 46 répliques de `narration.srt` recalées sur le temps du film ;
- `audio_placement.json` : départ de chaque fichier de chapitre (s, image, échantillon à 24 et 48 kHz) et la commande
  ffmpeg qui fabrique la piste voix du film (adelay par chapitre, complétée à la durée du film, 48 kHz) ;
- `verification.json` : résultat de chaque contrôle (OK, ERROR, WARN, INFO).

## Conventions

- **Images** : l'image f (numérotée à partir de 1) commence à t = (f − 1) / 25 s. Toutes les plages d'images sont
  **inclusives**. Les demi-images s'arrondissent vers le haut (`filmlib.frame_of`).
- **Voix** : chaque fichier de chapitre est posé entier, sans coupe ni fondu : 0,6 s de pré-roll, puis un silence après
  chaque chapitre choisi pour l'image (1,4 s après le chapitre 1 pour le remontage, 2,97 s après le 4 pour l'écran
  partagé et l'orbite), et un carton muet de 4 s à la fin. Les coupes précèdent le mot de 2 images (`CUT_LEAD`).
- **Manivelle** (`controller`) : `AM_Controller["crank"]` (années), `["explode"]` et `["patina"]` sont des listes de clés
  `{f, v, ipo, ease}`. L'interpolation d'une clé vaut pour l'intervalle qui la **suit** (comme Blender). Il faut régler
  l'easing explicitement dans Blender. Les valeurs sont en float32 et `frames[].crank` est la valeur exacte que
  Blender évaluera à chaque image.
- **Plans** (`segments`) : `kind` vaut `3d` (rendu plein cadre), `split` (3D décentrée, `shift_x` 0,25, et schéma à
  droite), `diagram` (schéma plein cadre, pas de 3D), `map` (carte plein cadre, pas de 3D) ou `card` (carton final
  sur la 3D en fondu). `mode` vaut `case`, `front`, `back`, `front_to_back` ou `wide` (éclairage et décor).
- **Caméras** : une pose `{f, target, az, el, dist, lens, up, shift, ease}` place la caméra en
  target + dist · (cos el cos az, cos el sin az, sin el) (monde, degrés, mm), visant la cible. La cible est un point,
  `{anchor, crank}` (l'ancre à cette manivelle) ou `{track: anchor}` (suivie à chaque image). `ease` est l'easing du
  mouvement vers la pose suivante. `inset` est une seconde caméra rendue dans un rectangle (plan 3.4).
- **Ancres** (`anchors`) : points des objets du `.blend` (centre, point porté, tip d'une aiguille…), à projeter à
  chaque image par le montage.
- **Callouts** : textes français avec des images d'entrée et de sortie (recadrées sur le plan). Ils suivent la charte
  de `overlay.py`. `zone` donne la pile (`haut_droite`, `haut_gauche`, `bas_gauche`, `bas_droite`) et `stack` le rang
  dans la pile. `item` est à passer tel quel à `overlay.render_callouts(items, zone)` : `{text | sub, kind}`, avec
  `kind` qui vaut `normal`, `hyp` (violet), `modele` (vert-de-gris) ou `illustration`. `size_px` est la boîte mesurée.
  `anchor` désigne l'objet visé (utile pour un filet), et `pos` la position voulue à l'origine (elle ne sert plus
  qu'au choix de la zone).
- **Incrustations** (`overlays`) : calques de `inserts.py`. Chacun a une table `map` `[image_du_film, image_de_la_séquence]`,
  `box_px` (la boîte occupée) et, si besoin, l'ancre sur laquelle le translater (Ξ et ligne du parapegme). Les titres
  de chapitre apparaissent 0,2 s après le début du premier plan de chaque chapitre.
- **Schémas** (`segments[].diagram`) : table `map` du même type ; 4.3 et 7.4 (jusqu'à `inset_until`) sont en écran
  partagé ou en incrustation.
- **Beats** : images où la machine doit montrer une lecture précise. `check` et `params` décrivent le test,
  `window` les images permises pour rester synchrone avec la voix, `hold` les images où la manivelle ne bouge pas.
- **Sous-titres** : `start`/`end` en secondes du film, `in`/`out` en images. `burn_in` vaut false sous le carton final,
  qui porte déjà la question et les crédits. `over` liste les plans plein écran sans 3D placés sous la réplique.

## Format de `timeline.json`

| Clé | Contenu |
|---|---|
| `title`, `fps`, `resolution`, `frame_start`, `frame_end`, `total_seconds` | 25, [1920, 1080], 1, 4009, 160,36 |
| `conventions` | les règles ci-dessus, en bref |
| `audio[]` | = `audio_placement.json` `clips` : `{chapter, file, start_s, start_frame, start_sample_24k, start_sample_48k, duration_s, end_s}` |
| `chapters[]` | `{n, audio_start_s, audio_start_frame, audio_end_s, frames, seconds, shots}` |
| `segments[]` | un par plan : `{id, chapter, kind, t0, t1, frames, seconds, render_3d, mode, cadrage, camera {name, poses}, inset?, diagram?, inset_until?, callouts[], texts_in_picture?, labels?, mars_trail?, ghost_b1?, counter?, counter_from?, flash?, crank_note?, sunbeam?, card?}` |
| `overlays[]` | `{sequence, segment, dir, pattern, images, rgba, box_px, placement, frames, map, anchor?, crank_sync?, background?, texts?}` |
| `overlays_source` | d'où viennent les métadonnées des incrustations |
| `layout` | `{counter_box_px, zones, stack_gap_px}` (charte `overlay.py`) |
| `anchors{}` | `nom -> {type center·point·radial·tip·at_crank, object, …}` |
| `controller` | `{crank, explode, patina}` : listes de clés |
| `highlights[]` | `{id, targets, kind glow·sweep·ghost, color, keys [{f, v}], sweep?, width_deg?}` ; les cibles `FILM_*` (FILM_b1_ghost, FILM_games_wedge, FILM_phase_halo) sont créées par `build_film.py` |
| `blinks_6_1[]` | `{cell, glyph, frame_entry, crank_entry}` : les cases à signe calculé que l'aiguille du Saros traverse en 6.1 |
| `beats[]` | `{id, segment, frame, crank, check, params, expect, word, word_frames, window, hold}` |
| `engine_instants` | `{olympia_entry, saros_entry {case: manivelle}, mars_stations, mars_opposition}` |
| `subtitles[]` | `{i, chapter, start, end, in, out, text, segments, over, burn_in}` |
| `frames[]` | `{f, seg, crank, explode, patina, counter}` pour chacune des 4 009 images |

## Plans (état du 25 septembre 2026, régénérer avec `timeline.py`)

| Chap. | Voix (s) | Images | Plans (images) |
|---|---|---|---|
| 1 | 0,60-21,16 | 1-608 | 1.1 1-121 · 1.2a 122-143 · 1.2b 144-175 · 1.2c 176-211 · 1.2d 212-241 · 1.3 carte 242-355 · 1.4 356-608 |
| 2 | 22,56-34,62 | 609-893 | 2.1 609-724 · 2.2 725-802 · 2.3 803-893 |
| 3 | 35,62-58,70 | 894-1493 | 3.1 894-1039 · 3.2 1040-1151 · 3.3 1152-1255 · 3.4 1256-1493 |
| 4 | 59,70-74,73 | 1494-1938 | 4.1 1494-1723 · 4.2 1724-1815 · 4.3 écran partagé 1816-1938 |
| 5 | 77,70-93,32 | 1939-2353 | 5.1 orbite 1939-2000 · 5.2 2001-2121 · 5.3 2122-2353 |
| 6 | 94,32-121,83 | 2354-3071 | 6.1 2354-2472 · 6.2 2473-2668 · 6.3 2669-2766 · 6.4 2767-2914 · 6.5a schéma 2915-3006 · 6.5b 3007-3071 |
| 7 | 122,83-156,34 | 3072-4009 | 7.1 3072-3241 · 7.2 3242-3431 · 7.3a schéma 3432-3491 · 7.3b 3492-3519 · 7.4 3520-3733 · 7.5 3734-3847 · 7.6 carton 3848-4009 |

## Synchronisations vérifiées (beats)

| Beat | Plan | Image | Manivelle | Sur |
|---|---|---|---|---|
| éclair éclipses : pleine lune sur le Dragon | 1.2a | 127 | 9,0140 | « éclipses » |
| éclair phases : boule à moitié claire | 1.2b | 149 | 0,9900 | « phases » |
| éclair Jeux : ΙΣΘΜΙΑ ΟΛΥΜΠΙΑ | 1.2d | 217 | 5,9500 | « Jeux » |
| nouvelle lune, aiguilles superposées | 3.4 | 1308 | 0,9720 | « Aiguilles superposées » |
| pleine lune, Lune dans ΧΗΛΑΙ, Soleil dans ΚΡΙΟΣ | 3.4 | 1446 | 1,0090 | « blanche… pleine lune » |
| Mars : 1re station (2,2134) | 4.2 | 1779 | 2,2169 | « s'arrête » |
| Mars recule au plus vite (opposition 2,3133) | 4.2 | 1799 | 2,3174 | « puis recule » |
| Mars : 2e station (2,4131), juste avant la coupe | 4.2 | 1815 | 2,4200 | fin de « recule » |
| reprise 2,10 → 2,52 avec le schéma | 4.3 | 1816 | 2,1000 | « comme dans le ciel » |
| l'aiguille entre dans ΙΣΘΜΙΑ ΟΛΥΜΠΙΑ (5,9111) | 5.3 | 2226 | 5,9158 | « Olympia » |
| l'aiguille du Saros entre dans la case 112 (Σ Η) | 6.2 | 2551 | 8,9751 | « Une case gravée » |
| Exeligmos dans le secteur vide (+0 h) | 6.3 | 2669-2766 | 8,9800 | « zéro » |
| pleine lune sur l'aiguille du Dragon (0,41°) | 6.4 | 2834 | 9,0140 | « tombe sur l'aiguille du Dragon » |
| Soleil à 16,8° dans ΤΑΥΡΟΣ | 7.2 | 3363 | 9,1300 | « ksi » |
| Soleil dans ΣΚΟΡΠΙΟΣ (entrée à l'image 3619) | 7.4 | 3628 | 9,6000 | « tombent dans la noire mer » |

Choix faits dans cette version :

- **4.2** : un seul intervalle QUAD ease-in, de 2,10 à 2,42, entre la première et la dernière image du plan. La
  manivelle ne s'arrête jamais, elle accélère. La 1re station tombe sur « s'arrête », l'opposition sur « recule » et
  la 2e station juste avant la coupe. Le plan 4.3 rejoue ensuite 2,10 → 2,52 image par image avec le schéma
  `retrograde_split`. La version précédente était fausse : sa dernière clé (2,52) était écrasée par la première clé
  de 4.3 (2,10), si bien que la manivelle **reculait** de 2,2135 à 2,10 pendant « puis recule ».
- **3.4 et 5.3** : la manivelle suit la colonne « manivelle » des incrustations `phases` et `games_banner`. L'image 91
  de `phases` tombe sur « Opposées » et l'image 95 de `games_banner` sur « Olympia ». Le schéma et la machine
  montrent ainsi la même chose à chaque image.
- **7.4** : le Soleil atteint ΣΚΟΡΠΙΟΣ pendant « tombent dans la noire mer ». C'est là que les callouts disent
  « Fin oct.–début nov. » et « mer fermée du 11 nov. ». La rampe est à vitesse de croisière (`cruise()`), pour que
  l'aiguille de la Lune tourne moins vite.
- **Compteur** : visible de « Tournez-la » (2.1) jusqu'à 7.5, y compris dans l'écran partagé 7.4. Il est masqué au
  chapitre 1, pendant la reprise 4.3, sur les schémas plein écran et sur le carton.
- **Textes en double** : les callouts qui répétaient le texte d'une incrustation ou d'un schéma ont été retirés
  (carte 1.3, légendes de 3.4, « Mois corinthiens », anatomie du signe en 6.3, textes de Végèce en 7.3a, « La Terre
  dépasse Mars » en 4.3). Les mentions d'honnêteté restent présentes, soit dans un callout, soit dans l'image.

## Contrôles (`verify_beats.py`)

Dernier passage : 58 OK, 0 ERREUR, 3 AVERTISSEMENTS (avec `--audio --blend`).

- Clés → images : la manivelle recalculée depuis les clés est identique à `frames[]` sur les 4 009 images.
- La manivelle ne recule que dans 2.2 (« en arrière ») et aux sauts prévus (éclairs 1.2, retour à 0, reprise 4.3).
- Chaque beat est vérifié avec `engine.py` (phase, signe, nœud, secteur des Jeux, case et signe du Saros, vitesse de
  Mars, heures de l'Exeligmos), avec sa fenêtre de synchronisation sur les mots et la tenue de la manivelle.
- Les cases gravées qui clignotent en 6.1 sont celles que l'aiguille traverse (77, 83, 89, 95, 100, 101, 106, 107 Η).
- Audio : durée et fréquence des 7 WAV, placement sans chevauchement, commande ffmpeg. Avec `--audio`, la piste est
  rendue puis mesurée : 160,36 s, la voix démarre 0,15 à 0,19 s après chaque départ, silence total entre les
  chapitres, voix présente sous chacune des 46 répliques.
- Sous-titres : textes identiques à `narration.srt`, décalages conservés dans chaque chapitre, aucune superposition,
  les 373 mots de la voix tombent dans une réplique.
- Mise en page : boîtes mesurées avec les polices de la charte. Aucun callout ne touche un autre callout, le
  compteur, une incrustation, l'incrustation 3D ou un titre de chapitre. Tous restent entre y = 54 et y = 880.
- `--blend` : les 40 objets cités existent dans `am_atelier.blend` ; le secteur des Jeux porte « ΙΣΘΜΙΑ ΟΛΥΜΠΙΑ »,
  la case 112 « Σ Η » et le mois 8 « ΠΑΧΩΝ ».

Avertissements restants, à régler au montage :

1. 16 callouts restent moins de 2 s à l'écran (tenue minimale de la charte) ; le débit de la voix ne laisse pas plus.
2. Les incrustations de `inserts.py` ne sont pas encore rendues : `~/voxtral-tts/bin/python tools/explainer/inserts.py`.
3. Les répliques 3 (carte), 34, 35 (schéma éclipse) et 41 (schéma lever des Pléiades) passent sur des images plein
   écran dont le bas porte du texte. Il faut monter la boîte des sous-titres ou la rendre plus opaque sur ces plans.

## Scène Blender (`build_film.py` → `film.blend`)

`am_atelier.blend` est ouvert en lecture ; la scène est enregistrée sous `build/out/explainer/film/film.blend` (le script
refuse d'écrire `am.blend` ou `am_atelier.blend`). Tout suit `timeline.json` :

- **Scène** « Antikythera », images 1-4009, 25 i/s, 1920 × 1080, EEVEE avec les réglages de `render_frames.DEFAULTS`.
- **Manivelle** : clés de `controller` sur `AM_Controller["crank"]`, `["explode"]`, `["patina"]` (action
  FILM_controller, l'action de démonstration AM_crank est détachée), interpolation et easing **explicites**. Contrôle :
  la F-courbe évaluée sur les 4 009 images redonne `frames[]` (3 893 valeurs identiques en float32, écart max
  9,5e-7 an = 1 ulp), et la valeur évaluée par le depsgraph est identique sur 120 images (beats, bords de plans).
- **Caméras** : une par plan (CAM_1_1 … CAM_7_5, collection FILM_CAMERAS), cuites sur chaque image de leur plan
  (position, rotation, focale, décentrement) depuis les poses ; cibles `{anchor, crank}` et `{track}` calculées avec
  `anchors.Anchors`. Un marqueur par plan rendu lie sa caméra ; CAM_7_5 continue sous le carton 7.6. Les plans
  partagés gardent le décentrement 0,25 (machine dans la moitié gauche). L'incrustation 3.4 (CAM_3_4_ball, qui suit
  la boule) est rendue par une seconde scène FILM_inset_3_4 (mêmes collections, 480 × 480).
- **Mise en scène par plan** (clés CONSTANT sur hide_render / hide_viewport) : `case` = boîtier fermé (AM_CASE) sur
  l'établi ; `front` et `wide` = atelier et éclairage avant ; `back` = établi et lumières en miroir, nœuds du monde
  « mirror » = −1 et « refl_gain » = 1,3 ; `front_to_back` (5.1) bascule quand l'orbite passe el = 0 (image 1971) ;
  étiquettes des planètes (AM_LABELS) seulement en 1.2c et 4.1-4.3 ; les plans sans 3D gardent l'état précédent.
- **Surlignages** : chaque objet visé reçoit sa **propre copie** de ses matériaux (lien du slot sur l'objet), avec
  Add Shader (surface d'origine + Emission) ; la force est un nœud Value clé (LINEAR) = valeur de la clé × gain. Gains
  réglés sur les images de test : bronze 0,3, gravures 0,45, sphères 0,35 (au-delà de ~0,8 le bronze au soleil vire au
  blanc) ; les lettres posées sur une zone qui brille restent sombres pour rester lisibles (ΙΣΘΜΙΑ ΟΛΥΜΠΙΑ sur le
  secteur, lignes du parapegme). `sweep` (anneaux 3.1) : fenêtre angulaire lissée de `width_deg` qui tourne avec
  l'angle clé. `AM_bronze` et `AM_engraving` restent sans émission.
- **Objets FILM** (lueur additive, sans ombre) : FILM_b1_ghost (b1 aplatie juste au-dessus du cadran, portée par B_b,
  2.3) ; FILM_games_wedge (secteur de ΙΣΘΜΙΑ ΟΛΥΜΠΙΑ, ±45° autour de son étiquette, 5.3) ; FILM_phase_halo (anneau
  autour de la boule des phases, porté par la Lune, 3.4, invisible dans l'incrustation) ; FILM_mars_trail (arc rouge
  sur l'anneau de Mars, de la plus petite à la plus grande longitude atteinte depuis le début du plan, 4.2 puis 4.3) ;
  FILM_sunblind (panneau à fente verticale de 190 mm hors de la fenêtre, visible des seules ombres, 1.1 : le rai de
  soleil traverse le couvercle ; clés du timeline = centre de la fente en largeurs de fenêtre).

### Contrôles de `film.blend` (`film_check.json`)

24 contrôles OK : clés → `frames[]`, manivelle évaluée, caméra liée au début / milieu / fin de chaque plan, mise en
scène de chaque image rendue, surlignages (valeur au sommet, matériaux partagés intacts), et, **à chaque beat**, les
aiguilles lues dans Blender (méthode de `validate_blend.py`) comparées à `engine.py` : écart max 5,2e-7 rad. Les
lectures sont refaites depuis les angles de Blender : élongation et boule (pleine lune 179,1°, 0,9999), signes du
Soleil et de la Lune, Lune à 0,41° du nœud, secteur des Jeux (ΝΕΜΕΑ ΑΛΙΕΙΑ → ΙΣΘΜΙΑ ΟΛΥΜΠΙΑ entre 2225 et 2226, et
étiquette gravée sous l'aiguille), case du Saros (111 → 112, curseur au rayon du moteur à < 0,05 mm, signe « Σ Η »
à côté), vitesses de Mars par différences finies dans Blender (stations 1779 et 1815, rétrogradation, deux stations
dans la reprise 4.3 aux images 1855 et 1898). `verify_beats.py` repasse aussi sur les manivelles de Blender.

## Ancres (`anchors.py` → `anchors.json`)

Pour chaque ancre utilisée par un plan rendu (callout, extrémité de trait `lines_2d`, calque translaté, cible suivie),
une ligne par image du plan : `[image, x_px, y_px, profondeur_mm, dans_l_image, masquée]` (image 1920 × 1080, origine
en haut à gauche, décentrement inclus ; à 960 × 540, diviser par 2). 25 ancres, 4 647 lignes. Pendant leur callout,
toutes les ancres sont dans l'image sauf 2 images en 2.1 (la manivelle frôle le bord) et les 4 premières images de
« Exeligmos : +0, +8, +16 h » (le panoramique arrive) : faire apparaître le filet quand `dans_l_image` vaut 1.
`masquée` est indicatif (le centre du cadran est sous le moyeu, par exemple).

## Rendu (`render_frames.py`)

Seules les images des plans `render_3d` sont rendues (3d, split, carton : 3 743 images), plus les 238 images de
l'incrustation 3.4 dans `DIR/inset_3_4/`. Chaque image est écrite sous un nom temporaire puis renommée ; une image
présente et non vide est sautée (reprise après interruption) ; `DIR/render_log.jsonl` garde le temps de chaque image.
`--res 960x540` rend à 50 % (même cadrage).

Réglages finaux (`DEFAULTS`) : EEVEE **28 échantillons**, ray tracing écran à pleine résolution (rugosité max 0,55,
qualité 0,6, débruité), fast GI « global illumination » (résolution 1/2, 8 pas, 2 rayons), ombres (16 pas, échelle 1,
pool 1024), filtre 1,5 px. Le Mac est un MacBook Air M4 **sans ventilateur** : un long rendu tourne bridé, 1,35 à
1,9 fois plus lent qu'à froid ; les mesures « chaud » valent pour le film entier.

| Réglage (1920 × 1080) | froid s/image | chaud s/image | aspect |
|---|---|---|---|
| 16 éch., ray tracing, GI et ombres allégés | 1,39 | – | grain sur les plans larges |
| 24 éch., pleine qualité | – | 3,57 | léger grain (couvercle, établi) |
| **28 éch., pleine qualité (retenu)** | – | **4,10** | propre (écart à 48 éch. : 0,3-1,0 / 255) |
| 32 éch., ombres 8 pas, GI 6 pas | – | 4,26 | plus bruité que 28 |
| 32 éch., pleine qualité | 2,37 | 4,57 | |
| 48 éch., pleine qualité (référence) | 3,39 | 6,58 | |

Banc officiel (`--bench 3`, images 460 éclatée, 2560 dos, 3150 atelier large, machine chaude) : **3,87 s/image**
(4,38 · 3,49 · 3,73), `film/bench/bench.json`. Estimation pour le film : 3 743 images × 3,9-4,1 s = **4,0 à 4,3 h**,
plus environ 4 min pour les 238 images de l'incrustation 3.4 (480 × 480, ≈ 1 s chacune, non mesuré en série).

Images de test (960 × 540, 16 échantillons) : `film/test_frames/` : 0060 boîtier et rai de soleil · 0460 vue éclatée
patinée · 0850 fantôme de b1 et manivelle · 1100 Soleil surligné · 1446 pleine lune (+ `inset_3_4/1446`) · 1799 Mars
rétrograde et sa traînée · 1870 écran partagé 4.3 · 2240 secteur ΙΣΘΜΙΑ ΟΛΥΜΠΙΑ · 2560 case 112 « Σ Η » · 2834 pleine
lune sur le Dragon · 3363 parapegme et Soleil dans ΤΑΥΡΟΣ · 3628 écran partagé 7.4, Soleil dans ΣΚΟΡΠΙΟΣ.

Cadrages corrigés dans `timeline.py` après les images de test (sans effet sur la manivelle ni les beats) : 2.3 (cible
[18, −8, 34], 660 → 630 mm : la manivelle de « ≈ 4,6 tours = 1 an » reste dans l'image) ; 6.3 (le panoramique arrive
sur l'Exeligmos à « zéro » − 0,1 s, le callout entre sur « y ajoute ») ; 7.4 (820 → 800 mm : tout le cadran tient dans
les 936 px de gauche, à côté du schéma).

## Montage (`composite.py`) et encodage (`encode.py`)

```sh
VPY=~/voxtral-tts/bin/python
nice -n 10 $VPY tools/explainer/film/composite.py --only-available          # images dont la 3D est rendue -> film/comp/
nice -n 10 $VPY tools/explainer/film/composite.py --placeholder --scale 0.5 # animatique 960 x 540 -> film/preview_comp/
$VPY tools/explainer/film/composite.py --frames 1446,3363 --placeholder --out /tmp/essai   # quelques images
nice -n 10 $VPY tools/explainer/film/encode.py                                # film/comp -> film/film.mp4 (CRF 18, slow)
$VPY tools/explainer/film/encode.py --preview --frames-dir build/out/explainer/film/preview_comp \
    --out build/out/explainer/film/animatic_placeholder.mp4                   # aperçu 960 x 540 avec la voix
```

`composite.py` travaille avec 3 processus au plus (≈ 0,06 s par image en 1080p, 4 min pour le film entier une fois la
3D rendue). Il reprend là où il s'est arrêté : une image écrite est sautée, sauf si elle a été faite sur un fond
provisoire et que la 3D existe maintenant, ou si la 3D est plus récente (métadonnées PNG `comp_src`, `comp_version`).
`encode.py` refuse une séquence incomplète, sauf `--allow-missing` (l'image précédente est tenue). Il écrit
`<sortie>.check.json` : durée 160,36 s à une image près (conteneur, vidéo, audio décodé), 4 009 images, H.264 yuv420p
BT.709, AAC 48 kHz stéréo, niveau de la voix.

Ordre des calques : fond (3D, schéma, carte, ou carton = fond + machine de 100 à 25 %) ; écran partagé ; incrustation
3.4 (cadre crème de 3 px, ombre de la charte, entrée 8 images) ; incrustations 2D ; callouts et filets ; compteur ;
titres de chapitre ; sous-titres ; fondus au noir (ouverture 12 images, fermeture sur la dernière seconde).

Choix de montage :

- **Callouts** : dessinés avec `overlay.draw_callout` (charte identique à `render_callouts`), entrée 8 images, sortie
  6 images, glissement 10 px, ombre portée calculée sur toute la pile. Dans une pile, la place d'un callout ne s'ouvre
  ou ne se referme en douceur que s'il pousse un callout déjà là ou qui reste après lui (dans la première moitié de
  son entrée, la seconde moitié de sa sortie) ; des callouts qui sortent ensemble s'effacent sur place (avant, ils se
  repliaient les uns sur les autres : 5.2, 7.4, 7.5).
- **Filets** : trait crème de 2,4 px sur un halo d'encre, anneau de 12 px autour de l'ancre, déroulé en 8 images. Le
  départ est le point du bord de la boîte (ou d'un coin) le plus proche qui ne traverse ni la boîte, ni une autre
  boîte, ni une incrustation, ni le sous-titre. Pas de filet quand l'ancre est hors de l'image, sous une incrustation,
  sous la boîte du sous-titre affiché (élargie de 16 px) ou sous la zone de sécurité (y > 1026) ; le filet s'efface
  alors en 5 images. Sur une inscription gravée (ΙΣΘΜΙΑ ΟΛΥΜΠΙΑ, ΠΑΧΩΝ, signe de la case 112), il s'arrête avant,
  sur un point. Pas de filet pour « Parapegme : calendrier des étoiles » (les deux plaques sont surlignées ; un filet
  croiserait celui de « Ξ : la Pléiade se lève » ou traverserait tout le cadran). Pas de filet non plus pour « Lune
  dans ΧΗΛΑΙ » (3.4) : la pointe de la Lune est au bord haut de l'image, sous le compteur.
- **Ancres calculées au montage** (`VIRTUAL_ANCHORS`, `LEADER_TARGET`) : points du monde projetés avec la caméra du
  plan (poses de la timeline à cible fixe, même calcul que `build_film.pose_params`, écart aux ancres de
  `anchors.json` < 0,07 px). 2.1 : le filet de « La manivelle = le temps » glisse du bouton à l'axe de la manivelle
  (106, 0, 19,16) avant qu'elle tourne (images 652-659), puis reste sur l'axe : le bouton tourne de ≈ 15° par image
  et sortait sans cesse de l'image. 2.3 : « ≈ 4,6 tours = 1 an » vise aussi l'axe (≈ 1460-1484, 902-919 px, à
  droite du sous-titre) ; « Grande roue : 1 tour/an » passe en haut à gauche et vise le bord denté du fantôme de b1
  (rayon 65 mm, az 220°) au lieu du moyeu central (son filet traversait l'autre callout). 3.1 : les ancres de la
  timeline tombaient dans la boîte des sous-titres ; « Calendrier égyptien » vise l'anneau extérieur à az 85° et
  « Zodiaque » l'anneau intérieur à az 45° (en haut à droite, sous leurs callouts).
- **6.3** : `glyph_anatomy` (boîte x 1064-1824) couvrait la moitié droite de l'Exeligmos et son aiguille dès
  l'arrivée du panoramique (2725). Il est retimé (`OVERLAY_RETIME`) : construit en 2669-2708 (ΩΡ + chiffre sur
  « l'heure »), tenu pendant le panoramique, sorti en 2725-2733 ; « Ici : +0 h » passe en haut à droite, près de
  l'aiguille (son filet croisait celui de « Exeligmos »).
- **7.2** : « Ξ : la Pléiade se lève » rejoint la pile du haut à gauche, sous « Ξ et ligne du parapegme :
  illustration » ; son filet descend droit sur le repère Ξ au lieu de traverser tout le cadran (moyeu et aiguilles)
  depuis le haut à droite. Un changement de zone sans position propre (`CALLOUT_ZONE_OVERRIDE` avec la seule clé
  `zone`) rejoint la pile de la zone ; avec `x`/`y`, il forme une pile à part.
- **Titres de chapitre** : pendant l'entrée, la boîte s'ouvre de gauche à droite mais le texte apparaît déjà en
  entier ; ce qui dépasse le bord droit de la boîte est masqué (images 8 à 14 de chaque titre).
- **Parapegme** : Ξ translaté sur `sign_under_sun` ; la ligne (1 007 px de large, plus que la plaque) réduite à 0,62
  et posée sur la moitié basse de la plaque du haut (`parapegma_top` + 170 px), gardée dans la zone de sécurité.
- **Schémas plein écran sous les sous-titres** (avertissement 3) : 6.5a et 7.3a sont réduits d'un bloc (0,905 et
  0,821, échelle constante sur le plan, bords prolongés) pour que leur texte du bas reste au-dessus de la boîte des
  sous-titres. L'éclipse garde le Soleil coupé par le bord gauche (point fixe x = 0). En 6.5a, « Signes calculés par
  notre modèle » passe en haut à gauche (en bas, il masquait le début de « l'aiguille du Dragon… (hypothèse) »).
- **Sous-titres** : 3 images de fondu ; centrés sur la moitié gauche pendant l'écran partagé 4.3 (le schéma occupe
  la droite, légende comprise) ; décalés à droite du cartouche « Printemps 1900 » sur la carte 1.3.
- **Compteur** : fondu d'entrée de 8 images sur « Tournez-la » ; il suit les coupes de plan ; il s'efface en
  12 images sous le carton.
- **7.4** : `pleiades_coucher` dans `rect_px` avec le même cadre que 3.4, entrée 8 images, sortie 6 images avant
  `inset_until`. **5.1** : la bascule d'éclairage (image 1971) est adoucie en mêlant les images 1970 et 1971 au tiers
  (`--no-bascule-blend` pour l'enlever).

## Reste à faire au montage

- Relancer `composite.py --only-available` à mesure que le rendu avance (ou une fois à la fin), puis `encode.py`.
- Regarder les plans dont les filets n'ont pu être vus que sur les images de test (anciens cadrages) : 3.2 (traits
  `lines_2d`), 6.3, 7.3b, et la bascule de 5.1 (2.1, 2.3 et 3.1 sont vérifiés sur le rendu final).
- 3.4 (cadrage 3D, voir le rapport de relecture) : l'étiquette ΧΗΛΑΙ est hors de l'image (au-dessus du bord haut,
  derrière le compteur) pendant « Lune dans ΧΗΛΑΙ (Balance) » (1451-1492).
- `verify_beats.py` (mise en page) ne connaît pas les réglages du montage : zones changées (6.5a, 2.3, 6.3, 7.2), sortie
  avancée de `glyph_anatomy`, sous-titres décalés (4.3, 1.3), ligne du parapegme.
- Une musique éventuelle doit rester 18 dB sous la voix (à ajouter dans le filtre de `encode.py`).
