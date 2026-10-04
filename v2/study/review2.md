# Seconde revue : vérification de la version 2

> Objet : `study/architecture.md` (version 2), `spec/architecture.json` et `tools/arch_*.py`.
> Méthode : lecture du code ; `python3 architecture.py --check` (59 s, reproduit) ; sondes Python sur les
> `items` de `architecture.json` ; un recontrôle strict des collisions (liens par id exact, groupe de tour,
> groupe de renvoi) ; une seule relance du placement, avec la reprise par pignon fou imposée. Aucun fichier
> du projet modifié.

## Verdict

La version 2 corrige l'essentiel de la v1. Toutes les entrées existent. B2, B3, B4, I4, I6, I9 et I10 sont réglés.
Le vérificateur est sain pour les pièces modélisées : le recontrôle strict ne trouve que 2 vrais recouvrements cachés.
Mais la reprise 1:1 directe a introduit une erreur de sens : dans 4 tours, la planète tourne à l'envers de la Terre.
Avec un pignon fou, Vénus et Neptune ne se placent plus. Les couples d'entrée du bloc Lune changent les rapports.
L'arbre de précession n'atteint pas le bloc du temps. Pas encore prêt pour la 3D : corriger N1 à N4 d'abord.

## Suivi des défauts de la première revue

| Id | Corrigé ? | Preuve courte |
|---|---|---|
| B1 | partiellement | Tube Y modélisé (`axe_*#tubeY`, puis `#haut` jusqu'à z 164). Mais le sens est faux dans 4 tours (N1). |
| B2 | oui | La 144 est à 52,75 mm de Y : jeu 14,25 mm. La 180 est sur Y : 6,35 mm de J, 2,6 mm de a1. |
| B3 | oui | Pignons modélisés, deux couronnes Y4. Écart mini 42,5° (Y5) : jeu 1,3 mm. Y4a 7,5 ; Y4b 1,6 ; J5 1,5 mm. |
| B4 | oui | 9 × 40° sur r 32. Roue de 64 à 3,39 mm de l'arbre voisin. Roues, tubes et tringles contrôlés. |
| B5 | partiellement | En plan, oui : r 79,1 = 75,1 + 4 ; x −222,5 ≥ −223. En z, non : voir N5. |
| I1 | oui (rapport) | Le bloc reçoit −10/131 · L_Nep, puis 15/179 : 150/23449 = `precession_ring`. Mais l'arbre n'y arrive pas (N3). |
| I2 | partiellement | Tableau des sens par renvoi, juste. Faux pour les reprises des tours (N1). |
| I3 | partiellement | Le défaut est reconnu. Le remède retenu est peu réaliste et non compté (N8). |
| I4 | oui | `temps_J`, `temps_Y`, `lambda_T`, `prec_bas` ; `lune_Y` ; `orr_moon` (11ᵉ tringle). |
| I5 | oui | Arbres E4 de z 68 à 98, E5 de 9 à 36. Exceptions : descente de `prec_bas` absente (N3), paliers bas (N7). |
| I6 | oui | Couches de 15 mm, coniques m 0,4 (Ø 10,4). |
| I7 | partiellement | Liens pièce à pièce, interfaces listées. Mais les couples d'entrée du bloc Lune sont faux (N2). |
| I8 | non | Tringles écartées, mais à 1,0 mm pile (Jupiter–Vénus). La bague excentrique annoncée ne tient pas avec la prise à 12 mm (N4). |
| I9 | oui | 71 roues internes comptées. Somme 497 refaite ligne à ligne. |
| I10 | oui | Fous placés aux bons entraxes : Mercure 23,25 et 24,75 mm ; nœud 8,0 et 15,75 mm. |
| M1 | oui | Texte : « 13 roue par roue, les autres dans des blocs ». |
| M2 | oui | 4 + 9 × 1,6 = 18,4 mm. |
| M3 | oui | 0,03/4,8 × 2 + 0,03/16 rad = 0,82°. |
| M4 | oui | Bloc `y_arbre` supprimé. Reste un lien périmé `y_arbre` sur `axe_Y` (sans effet). |
| M5 | oui | Pignon de 15 (m 0,8) à 65,6 = 71,6 − 6,0 mm du centre, par un trou de la platine. |
| M6 | oui | Hauteurs étagées annoncées (sans cotes). |
| M7 | oui | 0,05° ajouté au budget. |
| M8 | oui | Sens des graduations arrière donné. |
| M9 | oui | Textes corrigés. |
| M10 | oui | Options exclues ; couronne de 200 pesée. |

## Nouveaux défauts

### Bloquant

**N1. Dans 4 tours, la longitude moyenne tourne à l'envers.**
- Quoi : le tube Y mène à la fois la copie de l'UAK Terre et l'entrée du train. La reprise directe est un couple
  extérieur : signe −1. Les trains de Vénus, Mars, Uranus et Neptune ont 2 couples extérieurs : signe +1.
  Donc L = −k · Y_tube. Or `trains.json` veut L et Y dans le même sens (`sign` +1, `phys` +1).
- La conique d'arrivée du bus ne règle rien. Elle fixe le sens du tube, donc aussi celui de la copie de l'UAK Terre.
  Le § 8 (« réglage : conique d'arrivée du bus sur le tube Y ») est faux.
- Mercure, Jupiter et Saturne sont justes : reprise par fou (+1).
- Effet : le module reçoit une planète et une Terre qui tournent en sens contraires. Les longitudes géocentriques
  de 4 planètes sont fausses. La précession, prise sur L de Neptune, change aussi de signe.
- Sonde : placement relancé avec la seule reprise par fou (`TRANSFER_CD = []`). Mars et Uranus se placent (fou de 96).
  **Vénus et Neptune échouent**, et la précession n'est plus placée. Cause : l'arbre du fou est à ≤ 30 mm de l'axe.
  Il va de la platine au pont, et traverse la roue finale (r 47,75 pour Vénus, 40,98 pour Neptune).
- Correctif : un filtre de signe dans `place_train`. Pour Vénus et Neptune : fou sur un tenon porté par le pont,
  qui ne descend pas au plan de la roue finale ; ou un inverseur entre tube Y et copie de l'UAK Terre
  (+3 roues par tour). Recompter les roues (+4 au moins).

### Important

**N2. Les couples d'entrée du bloc Lune changent les rapports.**
- Le document dit : « la roue finale de chaque train est la menante ». Il compte 3 roues.
- `moon_L` : roue de 75 à 50,0 mm de l'axe M. Il faut 125 dents sur M. L sort × 0,600.
- `moon_node` : roue de 109 à 50,0 mm. Il faut 91 dents. Ω sort × 1,198.
- `moon_perigee` : sa roue finale (103) est en E4, à z 71–74. Le bloc est à z 9–33 : elle ne peut pas mener.
  À 36,0 mm, un engrènement direct voudrait 41 dents (× 2,51).
- Correctif : des couples 1:1 dédiés, une roue neuve sur chaque arbre de sortie. 100:100 (entraxe 50) pour L et Ω,
  72:72 (entraxe 36) pour ϖ. +3 roues. Ou replacer les arrivées à 37,5 / 54,5 / 51,5 mm de M.

**N3. L'arbre de précession n'atteint pas le bloc du temps.**
- `prec_bas` s'arrête en E5 T2 (z 51–66), à (38,2 ; −89,8). Le bloc est à z 9–33. Aucun segment z n'est modélisé.
  Les 4 roues sont pourtant comptées.
- Sonde : un arbre r 2 de z 58,5 à 21 en ce point entre de **13,6 mm** dans la couronne d'arrivée de `temps_Y`
  (r 20 à (30 ; −88), z 36–51).
- Recouvrement caché par le nom : la tringle et sa conique sont dans la couche de la roue de 131 (z 63–66).
  En plan, elles la recouvrent de 34,8 mm. Le lien « prec » (base avant « # ») le masque. Sous la roue, il reste
  12 mm pour une conique de Ø 11,2 plus 1 mm de jeu : −0,2 mm.
- Correctif : finir `prec_bas` ailleurs sur le bord du bloc. Sonde : (37,6 ; −64,3) et (36,3 ; −61,1) sont libres
  (tringle de 67 à 71 mm, descente sans contact). Modéliser le segment z. Donner 1 mm de plus à la couche.

**N4. La bague du suiveur F ne tient pas avec la prise à 12 mm.**
- Le § 10.3 fait tourner F sur une bague excentrique de Ø 16–18 mm autour de l'axe. Or la roue de prise de F
  est modélisée à r 6,5 (24 dents), avec sa partenaire à 12 mm (16 mm pour Uranus).
- Sonde : une bague r 9 recouvre la roue partenaire de 3,5 mm (Mars, Jupiter, Saturne, Neptune), de 1,5 mm (Uranus).
  La roue de F, enfilée sur la bague, demande un rayon primitif ≥ ≈ 11 mm (≥ 45 dents m 0,5) : entraxe ≥ ≈ 23 mm.
- À +23 mm, la tringle de Jupiter passe à 2 mm de l'axe de Vénus (r 4) : collision. Celle de Saturne passe à 5 mm
  de la tringle du tellurion : il en faut 12,2 au couvercle.
- Correctif : entraxe ≈ 23 mm ; prise côté −x pour Jupiter et Saturne (sorties à x −191 et −79). Écart mini au
  couvercle : 16 mm. Modéliser la bague et la roue de F.

**N5. La capacité en z des blocs n'est pas vérifiée, et semble insuffisante.**
- Laplace (E1 pile, 30 mm) : trois trains de 3 couples empilés font 27 mm. Il faut encore 2 doubleurs,
  2 différentiels, le cadran jovien (4 couples) et la coulisse de la lunette : au moins 6 plans de plus.
- Bloc Lune (24 mm) : sur l'axe M, au moins 15 roues coaxiales (entrées L, ϖ, Ω, Y ; 4 prises ; 6 couples
  de cascade ; 48:48), soit 45 mm. S'y ajoutent la copie de l'UAK Terre (17 mm en E3) et la roue de 155 (Ø 78,5).
- Bloc du temps (24 mm) : 5 différentiels coniques (couples 40:20), joint de Hooke à 23,44°, roue de 120 (Ø 61),
  roue de 179 (Ø 72,4) et son fou. Huit arbres de renvoi descendent dans sa moitié haute (z 21–33), entre 11 et
  41 mm de son centre. Les grandes roues n'ont donc que m1 : 12 mm, 4 plans.
- Correctif : un bilan de plans par bloc, comme pour les trains. Prolonger les blocs Lune et temps vers E5 T1–T2,
  hors des tringles. Sinon, un sous-étage de plus en E5 (+15 à 20 mm de profondeur).

### Mineur

- **N6. `prec_avant` : tringle de 8,0 mm** avec une conique de Ø 11,2 à chaque bout. Elles se chevauchent de 3,0 mm
  (masqué par le groupe). Un arbre droit à (0 ; −65,6) semble suffire : −4 roues. À vérifier en E1 T1.
- **N7. Arbres de précession sans palier bas.** `axe_neptune#bas` et `prec#a1` finissent à z 51, dans une couche
  de tringles, sans platine ni pont. La 131 (Ø 66,5) est en porte-à-faux sous P4. Ajouter un coq vers z 48–51.
- **N8. Jeu.** Des ciseaux sur des coniques m 0,4 de Ø 10,4 sont peu réalistes. Ils ne sont comptés ni en roues ni
  en masse. Un ressort spiral à couple constant par tube de sortie (11) précharge toute la chaîne. Le § 1 dit
  « dix sorties », le § 9 en liste 11.
- **N9. Vérificateur : règles de noms encore larges.** `linked()` accepte la base avant « # » et le groupe.
  `horloge` et `edt` sont à la fois un bloc et un renvoi. Recontrôle strict : 29 paires masquées par ces règles.
  28 sont voulues (roue sur son tube, couronne sur l'axe, conique sur son arbre). Une est réelle : `prec#w1`
  contre `prec_bas#r0` (N3). Le groupe de renvoi cache aussi N6. Correctif : liens par id exact.
- **N10. Comptes et interfaces.** Ajouter +4 fous (N1) et +3 roues (N2). Les couronnes de 96 sont pesées 25 fois ;
  il y en a 19 (+44 g, négligeable). Interfaces non listées : `lune_Y#z1` au bord du bloc Lune (48,5 + 2 > 50) ;
  les 3 roues de `lambda_T` (70,5 mm, dans le plan de l'UAK maîtresse), non modélisées.

## Points confirmés

- `--check` : 363 objets, 13 trains, 0 collision, 497 roues, 23,6 kg, caisse 470 × 360 × 310 mm. Reproduit.
- Roues : 196 = 283 − 87 ; la somme du § 7 fait bien 497. Les 71 roues internes y sont.
- Masse : la somme des postes fait 23 610 g. Avec l'aluminium : 20,1 kg.
- Caisse : 450 + 8 + 12 = 470 ; 340 + 20 = 360 ; profondeur 257 + 27 + 26 = 310 mm.
- Jeu : 0,82° reproduit.
- Budget d'erreur : identique à `mechanisms.md` § 2.5, 3.3, 4.4, 4.5 et 5.2. (Neptune : 0,025° arrondi à 0,03°.)
- Précession : 10/131 × 15/179 = 150/23449, le rapport de `precession_ring`. L'étiquette de `prec_avant` est juste.
- Modules changés : Neptune 11:147 en m 0,55, entraxe placé 43,45 = 0,55 × 158/2 ; la roue de 148 dégage l'axe
  de 3,95 mm. Jupiter 10:26 en m 0,7, entraxe 12,6 mm. Les rapports restent 11/1813 et 80/949.
- Arbre L de Neptune prolongé (z 51–68) : rien sur son chemin en P4 et E5 T2.
- Arbre de sortie du périgée (z 21–98) : 7,7 mm de la tringle `lune_Y`, 3,4 mm de sa couronne. Rien d'autre.
- Échange Uranus–Neptune : Neptune passe près du bloc du temps. Aucun conflit de module (r 55 tous deux).
- Carrousel : pas de 40°, roue de 64 à 3,39 mm de l'arbre voisin, à 13,5 mm des roues de tube.
- Moyeux : pignons espacés d'au moins 42,5° partout.
- Couvercle : 11 tringles, écart mini 15 mm ≥ 12,2 ; orrery 118 + 5 ≤ 155 mm.
- Entrées : temps (J, Y, λ_T, précession), Lune (Y, L, ϖ, Ω), tellurion (temps sidéral et bras de Lune),
  lunette (`jupiter_geo`), copies de l'UAK Terre (tube Y). Toutes existent, au sens près (N1).
- Recontrôle strict des pièces modélisées : hors N3 et N6, aucun recouvrement réel caché.
