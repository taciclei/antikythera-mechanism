# Revue adversariale de l'architecture

> Objet : `study/architecture.md` et son générateur (`tools/arch_*.py`, `tools/architecture.py`).
> Méthode : lecture, puis sondes Python sur `architecture.build(write=False)["items"]`. Aucun fichier modifié.
> Les chiffres « sonde » se reproduisent en quelques lignes avec `arch_geom.xy_gap` et `arch_geom.chain_shapes`.

## Verdict

L'arithmétique est juste : rapports 1:1, manivelle, masse, caisse, budget d'erreur recopié sans faute.
Mais le graphe des mouvements est incomplet : les sept copies de l'UAK Terre, le bloc du temps et le bloc lune
n'ont pas toutes leurs entrées. Et « 0 collision » vaut pour un modèle qui omet les pignons de moyeu, les roues
du carrousel, le prolongement des arbres jusqu'aux platines et les arbres consécutifs d'un même train.
Avec ces pièces, on trouve au moins 20 collisions réelles. L'architecture n'est pas prête pour la 3D.

## Défauts

### Bloquant

**B1. Les copies de l'UAK Terre n'ont pas d'entrée Y.**
- Quoi : le bus amène Y sur l'arbre d'entrée A0 du train moyen, pas sur l'axe de la tour. L'axe ne reçoit que
  la longitude moyenne de la planète (`#out`). Rien n'amène Y à la copie de l'UAK Terre empilée sur l'axe
  (`arch_layout.py:136-142`). Le module n'a donc pas son vecteur Terre.
- Preuve : `architecture.md:39-41` dit « empilés sur le même axe ». Distance A0 → axe de tour (sonde) :
  Vénus 132,3 ; Neptune 78,8 ; Mercure 67,8 ; Mars 48,8 ; Uranus 44,2 ; Jupiter 31,3 ; Saturne 30,9 mm.
  Aucun renvoi, aucune roue comptée.
- Correctif : trains moyens « revenants » (entrée et sortie coaxiales). Un module par couple suffit :
  pour Vénus, m 0,743 puis m 0,4 donnent deux entraxes de 71,0 mm. Le bus arrive alors sur un tube Y de l'axe.
  Sinon, un couple 1:1 A0 → axe par tour, dans un plan libre (+2 à 3 roues par tour).

**B2. Train J → Y : la roue de 144 traverse l'arbre Y.**
- Quoi : l'arbre a2 (−16,2 ; 16,7) porte la roue de 144 (r 36,5). L'arbre Y est à 23,25 mm. Y traverse
  forcément E4/A : il descend vers Y5 (E5) et monte vers Y4 et l'UAK maîtresse. Interpénétration : 15,3 mm.
  De même, la roue de 180 (r 45,5, sur a1) est à 40,75 mm de l'arbre a2.
- Preuve : sonde. La paire est masquée par les liens (`architecture.py:124`). La règle des arbres non
  consécutifs (`arch_geom.py:47-52`, `architecture.md:177-179`) ignore les arbres **consécutifs**.
- Correctif : inverser l'ordre des couples (10:83 d'abord, 31:180 en dernier). La 180 est alors sur Y, et
  l'avant-dernier arbre est à 52,75 mm de Y (> 36,5 + 2,5). Ajouter la règle « roue du couple k sur
  l'arbre k+1 contre l'arbre k+2 » au placement.

**B3. Moyeu Y4 : trois paires de pignons de 24 se chevauchent.**
- Quoi : les sept pignons couchés engrènent la couronne de 96 vers r 24. Un pignon de Ø 13 demande au moins
  34° d'écart. Écarts réels : Jupiter–Saturne 17,9° (corde 7,5 mm), Uranus–Neptune 24,0° (10,0 mm),
  Mercure–Mars 29,3° (12,1 mm).
- Preuve : ces pignons ne sont pas des objets. `arch_place.py:70-73` ne crée que la tringle au départ du
  moyeu ; `architecture.py:83-94` saute l'extrémité côté moyeu.
- Correctif : modéliser le pignon de départ ; imposer l'écart angulaire dans `place_out` ; ou deux couronnes
  Y4 superposées, sur deux couches.

**B4. Carrousel : les roues de 64 sont percées par les arbres voisins.**
- Quoi : roue de 64 (r de tête 16,5) ; arbre voisin (r 2) à 16,56 mm pour les écarts de 30°
  (Uranus–Neptune, Neptune–Dragon) : −1,94 mm. Écarts de 35° (Dragon–Lune, Lune–Mercure) : jeu 0,75 mm,
  sous le jeu de 1 mm. Tous les arbres partent de E1 T1 : l'arbre dont la roue est plus haute traverse le
  plan de l'autre, quel que soit l'ordre.
- Preuve : `arch_layout.py:94, 172-173`. Les roues de 64 ne sont pas modélisées ; le bloc `pile` est lié à
  tous les `car_*`.
- Correctif : écart ≥ 36° (9 × 40° tient sur le cercle) ou rayon de carrousel ≥ 40 mm. Modéliser les roues.

**B5. La boîte de Laplace ne contient pas ses trains.**
- Quoi : le seul train de Ganymède (167:131 · 10:23 · 29:115) demande une enveloppe de r 75,1 mm
  (`chain_shapes`). Le bloc fait r 66 (`arch_layout.py:126, 167`). Il doit aussi loger ν (r min 60,0),
  Callisto (50,3), deux doubleurs et deux différentiels, sur 30 mm d'épaisseur.
- Correctif : bloc sur deux sous-étages (E1 T2 + pile), ou train de Ganymède sans couple 167:131.
  Grossir le bloc sur place le fait sortir de la platine (x = −230 < −223).

### Important

**I1. Précession : le bloc du temps reçoit le mauvais arbre.**
- Quoi : le premier couple 10:131 est sous Neptune ; l'arbre de la 131 descend au bloc du temps (`prec_bas`).
  Le couple 15:179 est à l'avant (`architecture.py:107-120`). Le bloc reçoit donc −10/131 × Neptune,
  179/15 = 11,93 fois la précession. Or `sun_trop` et `lambda_trop` veulent `precession_ring`.
  `prec_avant` porte aussi l'étiquette `precession_ring` (`arch_layout.py:211-213`), à tort.
- Effet (sonde) : temps sidéral faux de 0,153°/an, soit 36,7 s par an et 1,0 h par siècle. L'équation
  du temps dérive de ≈ 2,6 min en 50 ans. Le document annonce −0,063 s/siècle et 3,1 s.
- Correctif : un couple 15:179 de plus dans le bloc du temps (179 dents m 0,5 : Ø 90,5 mm, juste dans
  r 46 s'il est centré). +2 roues.

**I2. Le sens de rotation n'est traité nulle part.**
- Quoi : `architecture.md` ne parle jamais du sens de rotation des arbres, ni de pignon fou. `trains.json` fixe pourtant le
  sens physique de chaque arbre (J −1, Y +1, planètes +1, nœud −1), en supposant des engrènements directs.
  L'architecture ajoute, par chaîne :
  - deux renvois d'angle par tringle. Leur produit vaut +1 ou −1 selon la face de la couronne ou de la
    conique où engrène le pignon. Deux couronnes dentées du même côté inversent le sens ;
  - un couple 64:64 extérieur avant chaque aiguille avant : il inverse toujours ;
  - des couples de prise extérieurs (λ_T, Lune, nœud) : ils inversent.
- Pourquoi c'est grave : le module veut deux bras qui tournent dans le même sens. Les différentiels des
  blocs du temps et lune aussi. L'orrery et les aiguilles avant doivent tourner dans le même sens
  (« toujours dans le même état », `architecture.md:103-104`).
- Correctif : une colonne « signe » par renvoi (±1 par étape), avec le choix de face ou un pignon fou.
  Vérifier que le produit redonne le `phys` de `trains.json`.

**I3. « Jeu nul en marche avant » est faux pour dix sorties.**
- Quoi : `architecture.md:374` et `:426` supposent que la sortie ne s'inverse pas si la manivelle ne
  s'inverse pas. Or les sept longitudes géocentriques rétrogradent : Mercure s'arrête 6 fois par an.
  L'équation du temps oscille, la lunette (λ_J,géo + 90°) et la course γ de la coulisse aussi.
- Effet : à chaque station, l'aiguille perd au moins les 0,68° des renvois de sortie. C'est 3 fois l'erreur
  géométrique (0,21–0,26°), au moment le plus intéressant, la boucle. Le frein à friction proposé
  (`architecture.md:378`) aggrave le cas : il retient l'aiguille pendant que le jeu se rattrape.
- Correctif : ressort de précharge à couple constant (spiral) sur chaque tube de sortie non monotone, ou
  roues à ciseaux sur toute la chaîne aval du suiveur. Ajouter le jeu au budget du § 9.

**I4. Entrées manquantes : bloc du temps, bloc lune, bras de Lune.**
- Bloc du temps (`arch_layout.py:117-119`) : il calcule `stellar` = J + Y, `gmst` = J + `sun_trop` et
  `sun_trop` = Y − précession. Aucun renvoi n'y amène J ni Y. Seuls λ_T et la précession y entrent.
  L'horloge 24 h (`horloge`) en sort pourtant J.
- Bloc lune (`arch_layout.py:110-112`) : évection = 2Y − ϖ, équation annuelle = λ_T − Y, copie de l'UAK Terre.
  Aucun renvoi n'y amène Y.
- Tellurion : « un bras de la Lune » (`architecture.md:112`, `bras_lune` 12 mm). Aucune tringle ne porte la
  Lune au couvercle. Il faudrait une 11ᵉ tringle et un 11ᵉ tube coaxial au centre de l'orrery.
- Correctif : tringles depuis Y5 et J5 vers le bloc du temps, depuis Y5 vers le bloc lune, et une tringle
  Lune vers le couvercle. Au moins 15 roues de plus.

**I5. Arbres non prolongés jusqu'à leurs paliers : 11 collisions cachées.**
- Quoi : chaque arbre de train n'occupe que son sous-étage (`arch_place.py:42-43`). Il n'y a pas de platine
  entre deux sous-étages : un arbre va de platine à platine (E4 : z 57–90 ; E5 : z 3–55).
- Sonde (arbres r 2 prolongés, objets non liés) : 11 collisions. Exemples :
  - arbre intermédiaire de Vénus (B) dans la roue de 180 du train Y (A) : −25,2 mm ;
  - arbre d'entrée de Vénus dans les roues de 180 et 144 : −12,8 et −7,0 mm ;
  - arbre a1 du nœud dans la roue de 103 du périgée : −22,3 mm ;
  - arbre de sortie du périgée dans la couronne d'arrivée du nœud : −9,4 mm ;
  - arbre a1 de `moon_L` dans la roue de 109 du nœud : −1,8 mm.
- Arbres consécutifs (sonde, même train) : la roue de 148 de Neptune (r 37,5) est à 39,5 mm de l'arbre de
  sortie, soit 0 mm de jeu. Cet arbre doit pourtant descendre en A pour le pignon de 10 de la précession, qui
  n'est pas modélisé (`#out` commence à z 75). Mercure : roue de 64 à 13,5 mm de l'arbre d'entrée.
  Lune : roue de 75 à 21,5 mm de la sortie (jeu 0,25 mm). Ces deux-là se règlent par l'ordre des plans.
- Le § 10 dit que le modèle « surestime l'encombrement » (`architecture.md:434-436`). C'est l'inverse.
- Correctif : prolonger les arbres en z jusqu'aux platines, ou prévoir et modéliser des ponts.

**I6. Les couches de tringles sont trop minces.**
- Quoi : couches de 11 mm (12 mm en E3 T1, `arch_layout.py:20-24`). Un pignon conique de 24 sur une
  tringle couchée fait Ø 13 mm. Au moyeu, couronne (≈ 2 mm) plus pignon dont l'axe est 6 mm au-dessus du
  primitif : ≈ 15 mm.
- Pire cas : la conique de 40 dents de l'orrery (`trains.json`, `orrery_*` 40:40, Ø 21) sur la tringle
  d'E3 T1 (axe z 115) occupe z 104,5–125,5. Elle entre de 4,5 mm dans l'UAK (z ≤ 109) et de 2,5 mm dans le
  module (z ≥ 123), à travers P2.
- Correctif : couches ≥ 16 mm (+≈ 30 mm de profondeur), ou coniques plus petites (m 0,4, 20 dents :
  Ø 8,8 mm). Modéliser la conique couchée par son vrai encombrement en z.

**I7. Interfaces du bloc lune et liens trop larges.**
- Quoi : `moon_L`, `moon_perigee` et `moon_node` finissent tous à 50,0 mm de l'axe de la Lune, sur le bord
  du bloc. Leurs roues de sortie entrent dans l'enveloppe de 27,8 mm (109 dents), 26,3 (103) et 17,3 (67).
  Les liens `["lune"]` (`arch_layout.py:152-157`) cachent ces recouvrements.
- Aucun couple ne ramène L, ϖ et Ω sur l'axe. Or la coulisse d'éclipse exige un porte-nœuds coaxial à
  l'unité d'anomalie (`mechanisms.md` § 5.2). Les prises `moon_true` (20,0 mm), `node` (42,9) et
  `gamma` (37,2) ne sont pas comptées, alors que `lambda_T` compte la sienne (`"takeoff": 2`).
- « Recouvrements déclarés » ne liste que les paires bloc–bloc (`arch_report.py:178-190`). Il en manque au
  moins six, dont `lune`/`moon_node#a2` (27,8 mm) et `axe_Y`/`ytrain#a2` (15,3 mm, B2).
- Correctif : lier une pièce à une pièce, pas à un bloc entier. Lister tous les recouvrements liés.
  Ajouter trois couples 1:1 d'entrée et trois de prise.

**I8. Prise héliocentrique vers l'orrery.**
- Quoi : la conique verticale de 40 dents (r 10,5) sur l'axe de tour, en E3 T1, heurte deux tringles
  voisines (sonde) : `orr_jupiter` (x = −156) près de Vénus (−147 ; 92), −3,0 mm ; `gamma` (x = 146)
  près de Mercure (157 ; 102), −1,0 mm.
- Le suiveur F des planètes extérieures est décalé de s·|C_p| de l'axe de tour : de 0,41 mm (Neptune) à
  3,72 mm (Mars) (`modules_results.json`). C'est moins que le rayon de l'axe (4 mm). F ne peut donc pas
  partir vers l'arrière en arbre simple : il faut un palier excentrique autour de l'axe (Ø ≈ 16–18 mm).
  Ce palier n'est pas décrit.
- Correctif : décaler les deux tringles d'au moins 4 mm ; dessiner le palier excentrique de F.

**I9. Le compte des roues oublie 71 roues.**
- Quoi : l'estimation de 87 roues (`trains.py:1166-1168`) valait 7 × 7 (modules : bras et chaîne 1:1),
  8 × 2 (aiguilles), 6 × 2 (cascade lunaire), 2 (couronne de phase) et 4 × 2 (cadran jovien).
  `architecture.md:21-22` la remplace entière par les 166 renvois. Seules les 16 roues d'aiguilles ont un
  équivalent (les couples 64:64). Les 71 autres disparaissent.
- Correctif : 362 + 71 = 433 au minimum. Avec les entrées manquantes (B1, I1, I4, I7), plutôt ≈ 470.
  La masse bouge peu (≈ +0,5 kg).

**I10. Pignons fous non placés.**
- `mercury_L` et `moon_node` ont un pignon fou de 20 dents (`trains.json`, `idler`). `place_out` ne place
  que les couples (`arch_geom.train_arbors`). Pour ces deux trains, un entraxe devient deux : la géométrie
  placée est fausse.

### Mineur

- **M1. « 70/70 arbres placés » surestime** (`architecture.md:27`). C'est une affectation à un nom
  (`arch_report.py:14-29`), options comprises. Seuls 13 trains sont placés arbre par arbre. Les cinq
  arbres de Laplace sont « placés » dans un bloc trop petit (B5).
- **M2. Pile avant** : arbre central Ø 4 (`ARBOR_R`) + 9 × 1,6 mm = **18,4 mm**, pas 17
  (`architecture.md:70`, valeur codée en dur dans `arch_doc.py:111-112`).
- **M3. Jeu avec coniques de 40** : rayon primitif 10 mm, donc **0,45°**, pas 0,43°. Le code prend le
  rayon de tête 10,5 (`arch_report.py:173`), mais le rayon primitif 6,0 pour les 24 dents.
- **M4. Bloc `y_arbre`** : décrit comme « roue de 83 dents du train J→Y » en E5 (`architecture.md:144`).
  La roue est placée en E4/A (`y_roue83`). Le bloc E5 est vide et périmé.
- **M5. Anneau tropique** : la couronne de 179 (m 0,8) a un rayon primitif de 71,6 mm. L'anneau visible est
  à r 112–134, sur la face. Comment l'un mène l'autre à travers la platine-cadran n'est pas dit. Une fente
  annulaire couperait la platine. La couronne (r ≈ 74) n'est pas modélisée.
- **M6. Couvercle** : avec les vrais e et ϖ, le bras de Lune (52 + 12 = 64 mm) entre de 4,7 mm dans la
  rainure de Mars. Les rainures Saturne–Uranus sont à 3,8 mm, Uranus–Neptune à 3,6 mm. Il faut étager
  les hauteurs. Rien n'est dit.
- **M7. Copies de l'UAK Terre** : une tolérance de 0,02 mm sur ρ ≈ 25 mm donne ≈ 0,05° d'écart entre
  le Soleil (UAK maîtresse) et chaque tour. Cet écart se voit aux conjonctions. Il n'est pas au budget.
- **M8. Faces arrière** : vu de dos, un arbre « horaire vu de face » tourne à l'envers. Le sens des
  graduations n'est pas donné (calendrier, éclipses, Saros).
- **M9. Texte** : « tube du Soleil » (`architecture.md:303`) alors que le Soleil est l'arbre central ;
  « E1 → E1 » (`:225`) pour un arbre de E1 T1 à E1 T2.
- **M10. Masse** : les options sont comptées (+387 g : `gmst_direct`, `saros_223`). La couronne de 200 et
  la roue de 155 manquent (≈ −290 g). Les couronnes de 96 sont pesées comme des roues de r 9
  (4,8 g au lieu de 17,6 g, ≈ +190 g). L'effet net est sous 0,3 kg : la conclusion tient.

## Points vérifiés et confirmés

- `python3 architecture.py --check` : 217 objets, 13 trains, 0 collision, 70/70, OK. Reproduit.
- Bus : 96/24 × 24/96 = 1 exactement. Accélérer la tringle 4 fois divise bien la torsion vue à la sortie.
- Manivelle : 24/96 donne 6 h par tour ; × 30 donne 7,5 j ; 48,7 tours par an ; 4 870 par siècle.
- Tableau des renvois : la somme fait bien 166. Et 283 − 87 + 166 = 362 (arithmétique seule, voir I9).
- Masse, poste par poste : 5 184, 6 609, 2 530, 846, 458 et 797 g recalculés. Total 22,4 kg. Caisse
  470 × 360 × 261 mm.
- Jeu des renvois de sortie : 0,03/6 + 0,03/6 + 0,03/16 rad = 0,68°.
- Rangées de modules : 430 et 440 mm. Couloir libre en E2 de y −57 à y 17.
- Faces : cadrans dans la platine, sans chevauchement. Le Saros touche la marge basse (0 mm).
- Couvercle : écart minimal des tringles 15 mm ≥ 14 ; orrery r 118 + 5 ≤ 130,5 mm.
- Anneau des dates : 2π × 97 / 366 = 1,67 mm par jour.
- Budget d'erreur : chiffres conformes à `mechanisms.md` (§ 0, 2.3) et à `trains.md` (Mercure −8,2·10⁻³ °/siècle).
- Accord avec `mechanisms.md` :
  - lunette menée par `jupiter_geo` ;
  - joint de Hooke mené par λ de l'UAK maîtresse et par la précession (au rapport près, I1) ;
  - TSMG = J + Soleil tropique ;
  - tellurion mené par `stellar`, juste dans le repère fixe ;
  - orrery mené par les suiveurs héliocentriques ;
  - coulisse d'éclipse sur le porte-nœuds (dans l'enveloppe ; voir I7 pour la coaxialité).
- Tringles longues (227 mm, Ø 3 mm, laiton) : flèche propre ≈ 0,05 mm ; torsion ≈ 0,04° pour 1 N·mm.
  Acceptable avec des paliers aux deux bouts.
- Dix aiguilles coaxiales : courant dans les grands orreries. Ø 18,4 mm reste raisonnable.
