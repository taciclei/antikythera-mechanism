# Troisième revue : vérification de la version 3

> Objet : `study/architecture.md` (version 3), `spec/architecture.json` et `tools/arch_*.py`.
> Méthode : lecture du code ; `python3 architecture.py --check` (64 s, reproduit) ; sondes Python sur les `items`
> (sens par tour, tenons, entraxes, recontrôle strict par id exact, plans libres pour les couples d'entrée,
> plus grande roue libre par demi-bloc). Aucun fichier du projet modifié, sauf celui-ci.

## Verdict

La version 3 corrige vraiment N1, N3, N4 et N6 à N10. Le sens L/Y vaut +1 dans les 7 tours, comme `trains.json`.
`--check` est reproduit : 368 objets, 0 collision, 507 roues. Le recontrôle strict ne cache aucun recouvrement réel.
Deux points restent ouverts. N2 n'est corrigé que sur le papier : les couples 1:1 de L et de ϖ n'ont aucun plan libre.
N5 l'est en partie : le budget du bloc Lune oublie deux différentiels (78 mm pour 60). Pas de bloquant.
La 3D peut commencer pour les tours, E4, E3 et E1 ; le bloc Lune doit être repris d'abord.

## Suivi de la seconde revue

| Id | Corrigé ? | Preuve courte |
|---|---|---|
| N1 | oui | Reprise 24 → fou → 24 (+1) dans les 7 tours. Trains à 2 couples extérieurs (+1) ; Mercure 3 ext. + fou (+1). L/Y = +1 = `sign` partout. Tenons de z 113 (Mercure, Neptune : 122) à 137, haut du pont. Seules les roues des plans 1–2 passent sous le tenon ; aucune roue du plan 0. |
| N2 | partiellement | Arrivées à 50,00 / 50,00 / 36,00 mm de M. +6 roues comptées. Mais les roues 100 (L) et 72 (ϖ) ne trouvent aucun plan : défaut A. |
| N3 | oui | `prec_bas#z` en (21,3 ; −109,4), z 39–98, à 38 mm du centre du bloc (r 46). Jeu mini 1,12 mm (couronne de `temps_Y`). Roue de 131 en z 89–92, tringle en z 92–105 : séparées en z. Couche 13 mm pour Ø 11,2 + 1. |
| N4 | oui | Roues r 12, partenaires à ±23 mm. Couvercle : écart mini 14,0 ≥ 12,2 mm. Tringle de Jupiter (x −191) à 38,5 mm de l'axe de Vénus ; Saturne (x −79) à 49 mm de la tellurion. |
| N5 | partiellement | Budgets écrits et vérifiés par le script. Mais le bloc Lune oublie 2 différentiels et le 30:155 ; Laplace et temps sans marge : défaut B. |
| N6 | oui | `prec_avant` : arbre droit en (0 ; −65,6), z 39–288,5, 0 roue. Reste une liaison interne absente : défaut C. |
| N7 | oui | Coq en z 87–89 ; `axe_neptune#bas` et `prec#a1` ont un palier bas et un palier dans P4. |
| N8 | oui | « Onze sorties » aux § 1 et 9. 9 demi-roues comptées. Niveau de pile 51/9 = 5,67 mm : roue + ciseau + jeu passent. |
| N9 | oui | Recontrôle strict refait : 37 paires masquées, toutes voulues, 0 réelle. La règle de groupe `tour_*` reste, sans effet. |
| N10 | oui | Somme 507 refaite. 19 couronnes de 96 pesées. λ_T supprimée (aucune pièce). `lune_Y#z1` listée. Petits restes : défaut D. |

## Nouveaux défauts

### Bloquant

Aucun.

### Important

**A. Deux couples d'entrée du bloc Lune ne trouvent aucun plan (suite de N2).**
- Un 1:1 à 50 mm demande deux roues de r 25,5 ; à 36 mm, de r 18,5. Ces roues ne sont pas modélisées.
- Sonde : roue de 100 sur `moon_L#a3`, essayée dans les 20 plans de z 9 à 69. Aucun plan libre.
  - `moon_L#a2` est à 24,25 mm (entraxe du 22:75) et traverse tout l'étage (z 9–72) : −3,25 mm.
  - Au-dessus de z 39, `moon_perigee#a2` est à 15,8 mm : −11,7 mm.
- Roue de 72 sur `moon_perigee#a2` (qui commence à z 39) : `moon_L#a3`, à 15,8 mm, la coupe dans tous les plans (−4,7 mm).
- Côté M, au-dessus de z 39 : la 72 touche `moon_true#z0` (20,0 mm de M, −0,5) et `orr_moon#z0` (19,2 mm, −1,3).
  La 100 y touche aussi `gamma#z0` (−1,8). Sous z 39, l'arbre du périgée n'existe pas.
- Le 100:100 de Ω passe : plans libres en z 9–27 et 39–66.
- Ce n'est pas dans l'enveloppe estimée : `moon_L#a2` est à 74,3 mm de M, hors du bloc (r 50).
- Correctif :
  - mettre les 3 couples d'entrée dans la recherche, comme pièces ;
  - pour L et ϖ, de petites roues avec un fou : roue 40 (r 10,5) → fou → roue 40. Elle dégage a2 (24,25 mm)
    et l'arbre voisin (15,8 mm) ; côté M, elle passe à 6,7 mm de `orr_moon#z0`. Le sens est gardé. +2 roues ;
  - sonde : L en moitié basse (fou de 64, z 21–24, jeu mini 9,8 mm) ; ϖ en z 42–45 (fou de 36, jeu mini 3,3 mm) ;
  - ou écarter l'arrivée de L (arc 100–300°) d'au moins 22 mm de l'arbre ϖ, et arrêter `moon_L#a2` par un coq.

**B. Hauteur des blocs : le bloc Lune déborde, Laplace et temps n'ont pas de marge (suite de N5).**
- Bloc Lune : 19 plans = 15 roues coaxiales + copie de l'UAK (4). Son contenu a pourtant deux différentiels,
  `annual_eq` et `evection_carrier` (couples 80:20 et 40:20), et le couple 30:155 (roue Ø 78,5).
  Avec la règle du script (différentiel plat = 3 plans) : 19 + 6 + 1 = 26 plans, soit 78 mm pour 60.
  Sans compter les étages non linéaires de la cascade ni la coulisse d'éclipse.
- Laplace : le § 7 compte « cadran jovien : 4 couples », le budget 3 plans. Quatre roues menées coaxiales au
  cadran demandent 4 plans : 18 plans, 54 mm pour 51.
- Bloc du temps : 60 mm pour 60, sans marge.
  - Ses différentiels sont « plats » ; `trains.json` les donne coniques (`realisation: bevel`). Choix non reporté.
  - Sa moitié haute (z 39–69) est traversée par 7 arbres. La plus grande roue libre y a r 25.
  - La copie de l'UAK (r 28), la roue de 120 (r 30,5) et la 179 (r 36,2) vont donc en moitié basse : 10 plans.
- Correctif : compter les différentiels du bloc Lune ; lui donner 20 à 30 mm de plus (m1/m2, caisse ≈ 390–400 mm)
  ou sortir ses différentiels du bloc. Écrire les différentiels plats dans `trains.json`. Garder 1 à 2 plans de marge.

### Mineur

**C. La liaison interne de la précession manque.**
- `prec_bas#z` (21,3 ; −109,4) et `prec_avant#z0` (0 ; −65,6) portent tous deux la vitesse de la roue de 131.
  Ils sont à 48,8 mm. Rien ne les relie, aucune roue n'est comptée, et le § 8 donne `prec_avant` « int, + » sans ce maillon.
- Un 1:1 direct donnerait des sens opposés à l'anneau tropique et au 15:179 du bloc : l'un des deux serait faux.
  Une roue r 24,4 sur `prec_avant` toucherait `vers_edt#z0` (16,8 mm) dans la moitié haute.
- Correctif simple : finir la tringle `prec_bas` sur l'arbre de `prec_avant`, qui descend déjà dans le bloc.
  Sonde : le tracé direct passe à 0,49 mm de `axe_neptune#bas` ; tourner le couple 10:131 de quelques degrés.
  Cela supprime aussi `prec_bas#z`. Sinon : 2 roues + fou (+3 roues).

**D. Comptes et textes.**
- § 6 : « Leur roue finale est la première roue du couple d'entrée » est un reste de la v2. Il contredit N2.
- § 8 : « ext → fou → ext » donne − avec la règle du § 8 (le fou inverse). Écrire « ext → ext (par un fou) ».
- § 5 : la colonne « Arbres (entrée → sortie) » finit par le tenon du fou, pas par la sortie.
- Copie de l'UAK du bloc du temps : 1 roue comptée. Un couple en demande 2 (ou 0 si coaxiale à `temps_Y#z1`,
  ce que r 28 à 31,6 mm du centre interdit).
- Couples d'entrée du bloc Lune (−) : le sens se règle déjà par la conique d'arrivée de chaque bus. Le dire.
- § 3.3 : Mercure et Vénus « suiveur F ». `mechanisms.md` dit : suiveur en O de l'UAK.

**E. Précision de l'équation du temps.**
- Sans λ_T, l'EdT vient de la copie de l'UAK du bloc : 0,05° de λ, soit 12 s. Le § 11 garde « 3,1 s au plus ».
- Correctif : écrire ≈ 15 s au pire, ou régler la copie sur l'UAK maîtresse au montage.

**F. Prises : centre de la roue de F.**
- Le modèle centre la roue de F sur l'axe. Elle tourne autour de F, à 0,4–3,7 mm. La partenaire va donc à F + 23 mm.
- Les marges tiennent : la plus juste devient 7,5 − 3,7 = 3,8 mm (`orr_mars#prise_axe` – `orr_earth#r0`).
- La bague de Ø 18 garde une paroi de 1,3 mm autour du tube (r 4) pour Mars. Juste, mais faisable.

## Points confirmés

- `--check` : 368 objets, 13 trains, 0 collision, 0 hors platine, 8 interfaces, 507 roues, 24,0 kg,
  caisse 470 × 360 × 370 mm. Profondeur : 344 − (−26) = 370. Orrery : 118 + 5 ≤ 185 mm.
- Entraxes : les 44 engrènements des trains placés sont exacts (écart < 0,02 mm), modules compris (0,55 et 0,7).
- Sens (N1) : reprise par fou dans les 7 tours (16 à 96 dents) ; Vénus et Neptune placées (fou de 96 à 30 mm).
  La conique d'arrivée du bus fixe le sens du tube ; L et la copie de la Terre suivent avec +1.
- Tenons : le fou de 96 de Vénus est au-dessus de la 124 (z 110–113) et de la 189 (z 107–110) ; le tenon
  s'arrête à z 113. Même schéma pour les 6 autres. Les tenons traversent B et C sans contact.
- Recontrôle strict (liens par id exact seulement) : 37 paires masquées par le groupe ou le nom d'axe.
  - 7 UAK sur leur axe, 7 arbres L dans leur tube Y, 7 roues de prise, 7 couronnes de bus, 7 roues de reprise sur le tube ;
  - 2 sur l'arbre de Neptune : le pignon de 10, et la 131 dont la tête arrive au fond du pignon taillé (jeu 0,0).
  - Toutes voulues. Aucune réelle.
- Liens exacts vers un bloc : 41 recouvrements, tous voulus (arbres d'entrée et de sortie, tubes de la pile,
  croix de Malte, arbres géocentriques dans leur module).
- Précession : 10/131 sur l'arbre L de Neptune prolongé (z 87–107) ; tringle à 4,3 mm de cet arbre.
- Arrivées au bloc Lune : `moon_node#a2` et `moon_L#a3` à 50,00 mm de M, `moon_perigee#a2` à 36,00 mm.
- Pièces déplacées : `tellurion#z0` à 3,06 mm de la couronne de `temps_J` ; cette couronne à 2,19 mm de
  `vers_horloge#z0`. `temps_Y#r0` à 1,02 mm de `vers_edt#z0`. Tout ≥ 1 mm.
- Échange Uranus–Neptune : aucun conflit ; la roue `saros#w3` sous le tenon d'Uranus est en z 33–36.
- Roues : 196 + 4 + 33 + 21 + 90 + 4 × 8 + 5 + 3 + 8 + 4 + 0 + 6 + 4 + 1 + 3 + 3 + 4 + 49 + 12 + 2 + 8 + 6 + 9
  + 3 + 1 = 507.
- Couvercle : 11 tringles, de x −191 à 191 ; écart mini 14,0 mm (tellurion – Terre).
