# Machine d'Anticythère : une reconstitution 3D fonctionnelle et vérifiée

[English](README.md) · **Français** · [Español](README.es.md) · [Deutsch](README.de.md) · [Italiano](README.it.md) · [Português](README.pt.md) · [Ελληνικά](README.el.md) · [中文](README.zh.md) · [日本語](README.ja.md)

[![Lean proofs](https://github.com/taciclei/antikythera-mechanism/actions/workflows/lean.yml/badge.svg)](https://github.com/taciclei/antikythera-mechanism/actions/workflows/lean.yml)

![Le mécanisme reconstitué, vue de trois quarts avant](docs/images/front34.jpg)

https://github.com/user-attachments/assets/430b3e08-be21-4612-8b2e-c7baaac96c85

https://github.com/user-attachments/assets/cf6afd77-1e15-478a-950b-eb82811933c0


La machine d'Anticythère est un calculateur astronomique en bronze, actionné par une manivelle, construit en Grèce au 2e ou au 1er siècle av. J.-C. et retrouvé dans une épave en 1901. C'est la plus ancienne machine à engrenages complexe connue. Ce dépôt en contient une reconstitution 3D complète réalisée sous **Blender 5.2** :

- les **69 roues dentées** ont leur nombre de dents réel ;
- les dents ont un profil en développante de cercle conjugué : chaque couple de roues engrène donc et fonctionne réellement ;
- chaque train d'engrenages a été **vérifié en fractions exactes** par rapport au cycle astronomique qu'il modélise ;
- les pièces ont fait l'objet d'une **vérification des collisions** sur toute l'amplitude du mouvement.

L'ensemble a été construit en une seule passe par Claude Opus 5.5 à partir d'un unique prompt maître autosuffisant ([`PROMPT_OPUS.md`](PROMPT_OPUS.md)), puis vérifié de manière indépendante.

## Points forts

- **69 roues dentées**, classées selon leur degré de certitude :
  - 30 **conservées**, physiquement présentes dans les fragments (tomodensitométrie) ;
  - 7 **reconstituées**, à partir d'indices solides ;
  - 32 **hypothétiques**, d'après le modèle de Freeth et al. 2021.

  Chaque statut dispose de sa propre collection Blender, ce qui permet de masquer ou d'afficher chaque groupe.
- **Des mathématiques exactes.** 1 tour de la grande roue b1 correspond à 1 an. Le mécanisme possède exactement **un degré de liberté** (la manivelle), et les 22 cibles concordent exactement sous forme de fractions (extrait ci-dessous).

  | Sortie | Vitesse exacte (tours/an) | Cycle |
  |---|---|---|
  | Lune (moyenne) | 254/19 | 254 mois sidéraux en 19 ans |
  | Cadran métonique | −5/19 | 5 tours = 19 ans = 235 mois lunaires |
  | Cadran du saros | −940/4237 | 4 tours = 223 mois lunaires |
  | Nœuds lunaires (aiguille du Dragon) | −5/93 | 18.6 ans, en sens rétrograde |
  | Vénus | 289/462 par rapport à b1 | 289 périodes synodiques en 462 ans |
- **Prouvé formellement en Lean 4.** [`lean/`](lean/README.md) contient 193 théorèmes, vérifiés par le noyau de Lean avec Mathlib, sans aucun `sorry` :
  - la cinématique des vitesses moyennes possède exactement **un degré de liberté**, et chaque vitesse découle des nombres de dents ;
  - les 22 cibles sont atteintes, tout comme le cycle métonique, le saros, l'exeligmos, le cycle callippique et le cycle des olympiades, ainsi que les relations entre les périodes planétaires ;
  - les 37 entraxes sont exacts à 10⁻⁶ mm près ;
  - les systèmes à goupille et fente conservent leurs vitesses moyennes, et l'amplitude de l'anomalie lunaire est comprise entre 6.579° et 6.581°.

  Des tests de mutation montrent que Lean rejette un nombre de dents erroné, une cible erronée ou un axe mal placé.
- **Il fonctionne mécaniquement.**
  - Les entraxes sont exacts à 10⁻⁶ mm près, et chaque rapport de conduite est ≥ 1.2.
  - On relève **0 interpénétration** sur des milliers d'échantillons 3D (BVH) : chaque engrènement sur un pas de denture, chaque cycle goupille-fente, et 168 paires de pièces à 240 positions de la manivelle.
- **La Lune accélère et ralentit grâce à des roues circulaires**, et non ovales. Un système à goupille et fente monté sur le plateau tournant e3 reproduit l'anomalie lunaire d'Hipparque (±6.58°).
- **Les planètes rétrogradent au bon moment.** Mars, Jupiter et Saturne entrent en mouvement rétrograde à l'opposition (180° ± 0.03°), et Mercure et Vénus restent dans les limites de leurs élongations maximales.
- **Une seule manivelle entraîne tout.** Tout le mouvement découle de `AM_Controller["crank"]`, exprimé en années, par l'intermédiaire de pilotes (drivers) à expression simple : le fichier s'anime donc sans qu'il soit nécessaire d'activer les scripts Python.
- **Un affichage lisible.** Chacune des sept « planètes » antiques a sa propre couleur et une étiquette qui la suit (Soleil, Lune, Mercure, Vénus, Mars, Jupiter, Saturne), le tout accompagné d'une légende.
- **Un éclairage de musée.** La scène comprend un fond de cyclorama sombre et des boîtes à lumière (softboxes) aux tons chauds, avec un rendu colorimétrique AgX. Cette mise en scène a été retenue parmi trois propositions rendues côte à côte.
- **Vue éclatée.** Faites varier `AM_Controller["explode"]` de 0 à 1 : chaque pièce coulisse le long de l'axe d'empilement.
- **Impression 3D.** Un fichier STL par pièce plus un 3MF complet, selon trois profils : résine ×1, résine ×1.5 et FDM ×2.

| Cadran avant | Cadrans arrière |
|---|---|
| ![Cadran avant avec les planètes colorées et étiquetées](docs/images/front.jpg) | ![Spirales métonique et du saros](docs/images/back.jpg) |

| Vue éclatée | Intérieur, mécanisme ouvert |
|---|---|
| ![Image fixe de la vue éclatée](docs/images/exploded.jpg) | ![Image extraite de la vidéo en vue éclatée](docs/images/exploded_video_frame.jpg) |

## Vidéos

- [`antikythera.mp4`](build/out/renders/antikythera.mp4) : 20 s. La manivelle fait défiler 4 ans ; les planètes, la Lune et les cadrans arrière se mettent tous en mouvement.
- [`antikythera_eclate.mp4`](build/out/renders/antikythera_eclate.mp4) : vue éclatée de 15 s. Le mécanisme s'ouvre couche par couche tandis que les engrenages continuent de tourner, puis se referme.

Les planètes qui, par moments, **reculent** dans les vidéos ne sont pas le signe d'un bogue. Il s'agit du **mouvement rétrograde** observé depuis la Terre, que le mécanisme a justement été conçu pour montrer. L'aiguille du Dragon (les nœuds lunaires) tourne toujours à rebours.

## Démarrage rapide

1. Installez **Blender 5.2** ou une version ultérieure.
2. Ouvrez [`build/out/am.blend`](build/out/am.blend) et appuyez sur **Espace** pour lancer l'animation.
3. Sélectionnez `AM_Controller` et modifiez ses propriétés personnalisées :
   - `crank` : années ; 1 correspond à un tour de b1 ;
   - `explode` : de 0 à 1 ;
   - `patina` : 0 pour un bronze neuf, 1 pour une patine de musée.
4. Dans l'Outliner (Synoptique), masquez des collections :
   - `AM_CASE` et `AM_DIALS` pour voir les engrenages ;
   - `AM_HYPOTHETICAL` pour ne garder que ce qui est attesté ;
   - `AM_LABELS` pour retirer les étiquettes ;
   - `AM_STAGE` pour retirer le dispositif d'éclairage.
5. Cliquez sur n'importe quelle pièce pour lire ses propriétés personnalisées : `status`, `role`, `teeth`, `module` et `sources`.

### Relancer la vérification

Utilisez le Python fourni avec Blender. Les chemins ci-dessous valent pour macOS ; adaptez-les sur les autres systèmes.

```sh
PY=/Applications/Blender.app/Contents/Resources/5.2/python/bin/python3.13
BL=/Applications/Blender.app/Contents/MacOS/Blender

$PY tools/validate_spec.py          # exact linear solve (1 DOF, 22 targets), centre distances, collision screening
$PY tools/check_kinematics.py       # pin-and-slot laws, followers, elongations, retrogrades, solar apogee
cd build && $PY -m unittest discover -s tests && $PY -m am.verify --stage all && cd ..
$BL -b build/out/am.blend --python-exit-code 1 -P tools/crosscheck_blend.py   # Blender rotations vs an independent solver
```

[`build/README.md`](build/README.md) détaille chaque étape de construction, de vérification, d'export et de rendu, à raison d'une commande par étape.

### Vérifier les preuves formelles (Lean 4)

Installez [elan](https://lean-lang.org/install) une fois pour toutes, puis :

```sh
cd lean
lake exe cache get    # download the compiled Mathlib (about 5 GB)
lake build            # check every proof; warnings are errors, so success means no sorry
cd ..
python3 tools/lean_mutation_test.py   # Lean must reject 9 deliberately wrong mechanisms
```

[`lean/README.md`](lean/README.md) détaille ce qui est prouvé, module par module, et ce qui ne l'est pas.

### Tout reconstruire à partir du prompt maître

Dans un dossier **vide**, avec [Claude Code](https://claude.com/claude-code) :

```sh
claude -p --model 'claude-opus-5-5[1m]' --effort xhigh --permission-mode acceptEdits \
  --allowedTools Bash Read Write Edit Glob Grep < PROMPT_OPUS.md
```

- [`prompts/PROMPT_OPUS_v1_validated.md`](prompts/PROMPT_OPUS_v1_validated.md) est la version exacte qui a produit cette construction en une seule passe (89 min).
- [`PROMPT_OPUS.md`](PROMPT_OPUS.md) correspond à la v1.2. Elle ajoute les couleurs et les étiquettes des planètes, la mise en scène muséale, le curseur d'éclatement et la vidéo en vue éclatée. Tous ces éléments ont été intégrés à cette construction après coup, à l'aide des scripts de `tools/`, et la v1.2 n'a pas encore été relancée de zéro.

## Comment il a été réalisé

1. **Recherche.** Des agents travaillant en parallèle ont lu les sources primaires : Freeth et al. 2006, 2008 et 2021 (avec les informations supplémentaires), Price 1974, Budiselic et al. 2020, Woan & Bayley 2024, Anastasiou et al. 2014, entre autres. Les résultats ont été harmonisés en un seul jeu de données, puis contrôlés par un agent sceptique.
2. **Spécification.** [`spec/antikythera.json`](spec/antikythera.json) constitue l'unique source de vérité. Il fournit le nombre de dents, le module, la position de l'axe, la plage en z et l'alésage de chaque roue, ainsi que chaque arbre, goujon, bossage, goupille, cadran et matériau. Il est généré par `tools/make_spec.py`, qui corrige 22 impossibilités géométriques présentes dans les données publiées (par exemple, b2 ne peut pas engrener à la fois avec c1 et avec l1 aux distances publiées). Chaque entraxe est résolu de manière exacte.
3. **Contrôles indépendants.** `tools/validate_spec.py` et `tools/check_kinematics.py` ne partagent aucun code avec le générateur, et des tests de mutation confirment qu'ils détectent les erreurs injectées.
4. **Dentures de champ par enveloppe.** `tools/crown_envelope.py` calcule les dents des roues de champ a1 et q1 comme la région que les dents de la roue conjuguée ne balaient jamais. `tools/test_crowns_blender.py` les vérifie ensuite par BVH dans Blender.
5. **Revues contradictoires.** Deux séries de relecteurs indépendants ont examiné les données, l'API de Blender (testée en conditions réelles), l'exécutabilité et la géométrie, et ont relevé 5 points bloquants et environ 60 autres problèmes. Tous ont été corrigés.
6. **Construction en une seule passe** par une nouvelle session Opus 5.5, à partir du seul prompt : 131 tours de dialogue, environ 5 000 lignes de code, et tous les critères d'acceptation au vert.
7. **Vérification indépendante** du résultat : tests, contrôles exacts, contrôle BVH complet, et comparaison croisée de chaque corps de `am.blend` avec le solveur indépendant (7·10⁻⁷ rad).
8. **Preuves formelles.** `tools/make_lean.py` traduit la spécification en Lean 4. La cinématique, les cibles et les entraxes sont prouvés à partir de celle-ci. Des modules écrits à la main y ajoutent l'analyse des systèmes à goupille et fente ainsi que l'astronomie, et des relecteurs contradictoires et des tests de mutation ont vérifié que chaque énoncé dit bien ce qu'il annonce.

## Organisation du dépôt

```
PROMPT_OPUS.md            master prompt (v1.2), self-contained; embeds the full JSON spec + SHA-256
prompts/                  the prompt version validated by the one-pass build (v1)
spec/antikythera.json     single source of truth (gears, axes, shafts, trains, dials, staging, video)
research/                 raw multi-agent research results with source URLs
tools/                    spec generator, validators, crown envelopes, Lean generator, annotation/staging/explode/render scripts
lean/                     Lean 4 + Mathlib proofs: kinematics, targets, centre distances, pin-and-slot, astronomy
build/                    the project generated by the one-pass build (am/, blender_scripts/, tests/, README)
build/out/                am.blend, verification report (report.md/html), checks, print files, renders, videos
docs/                     dossier (HTML) and images
```

## Limites, en toute honnêteté

- Les trains planétaires, les nœuds lunaires et le Soleil vrai suivent le modèle **hypothétique** de Freeth et al. 2021. Une animation qui fonctionne ne prouve pas la manière dont l'original a été construit.
- Certaines grandeurs ne sont pas publiées. Pour celles-ci, la spécification recourt à des valeurs par défaut documentées, recensées dans `spec/antikythera.json` → `unresolved_defaults` :
  - les angles des axes sur la plaque arrière ;
  - les rayons des anneaux du cosmos ;
  - les phases de départ (l'époque n'est pas calibrée).
- Les preuves Lean couvrent la cinématique des vitesses moyennes, les cibles, les entraxes ainsi que les lois des systèmes à goupille et fente et des suiveurs. Le rapport de conduite, le recouvrement axial des dentures, l'interférence de taillage et les collisions sont vérifiés par les outils Python et dans Blender, pas en Lean.
- Les dents sont des développantes conjuguées (crémaillère à 30°, qui correspond à la dent antique en triangle équilatéral), et non les triangles limés à la main de l'original.
- Les couleurs des planètes ne servent qu'à la lisibilité ; elles n'ont rien d'historique.

## Sources principales

- T. Freeth et al., "A Model of the Cosmos in the ancient Greek Antikythera Mechanism", *Scientific Reports* 11, 5821 (2021), avec ses informations supplémentaires (Supplementary Information).
- T. Freeth et al., "Decoding the ancient Greek astronomical calculator known as the Antikythera Mechanism", *Nature* 444, 587 (2006).
- T. Freeth, A. Jones, J. Steele, Y. Bitsakis, "Calendars with Olympiad display and eclipse prediction on the Antikythera Mechanism", *Nature* 454, 614 (2008).
- T. Freeth & A. Jones, "The Cosmos in the Antikythera Mechanism", ISAW Papers 4 (2012).
- D. de Solla Price, *Gears from the Greeks* (1974).
- C. Budiselic et al. (2020) ; G. Woan & J. Bayley (2024) : nombre de trous de l'anneau calendaire.
- M. Anastasiou et al. (2014) : les spirales des cadrans arrière.

La liste complète, avec les URL, se trouve dans `spec/antikythera.json` → `sources`.

## Licence

- **Code** : MIT ([`LICENSE`](LICENSE)).
- **Rendus, vidéos, modèle 3D, fichiers d'impression et textes** : CC BY 4.0 ([`LICENSE-MEDIA.md`](LICENSE-MEDIA.md)).
- **Données savantes** : merci de citer les travaux ci-dessus.

---

Réalisé avec [Claude Code](https://claude.com/claude-code) (Claude Opus 5 / 5.5) pour taciclei.
