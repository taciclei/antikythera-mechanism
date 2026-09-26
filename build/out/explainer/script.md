# Le ciel dans une boîte : comment lire la machine d'Anticythère

Script de la voix off et découpage du film explicatif.
Version du 25 septembre 2026 (relue et corrigée). Texte parlé seul : `narration.txt` (un paragraphe par chapitre, séparés par `---`).

## Fiche technique

| | |
|---|---|
| Durée visée | environ 2 min 45 s (165 s, carton final compris) |
| Texte parlé | 385 mots (390 en lisant les années en toutes lettres). Débit posé : 2,3 à 2,4 mots par seconde selon le chapitre, jamais plus, pour garder de courtes pauses |
| Voix | française, calme, ton documentaire, vouvoiement |
| Look | atelier en lumière du jour (`tools/staging_atelier.py`, collection AM_ATELIER). Bronze clair, patine faible (0,15) sauf au chapitre 1. Graphismes crème et encre, accents or et bronze, lettres grecques en or |
| Manivelle | `AM_Controller["crank"]` en années. Le temps avance globalement du début à la fin du film, de 0 à 9,6 ans (sauf les éclairs du plan 1.2, le retour en arrière du plan 2.2 et la reprise du plan 4.3) |
| Compteur | Coin haut gauche, à partir du chapitre 2 : « Temps écoulé : X ans Y j » (Y = partie décimale × 365,2422). Il indique un temps relatif, jamais une date historique, parce que l'époque du modèle n'est pas calibrée |
| Règles | Chaque fait vient de la fiche vérifiée (`faits.md`). Planètes, Soleil vrai et aiguille du Dragon sont marqués « hypothèse ». Les signes d'éclipse sont marqués « calculés par notre modèle ». La machine n'est pas présentée comme un instrument de navigation |

## Ligne de temps de la manivelle

Les instants ci-dessous ont été recontrôlés le 25 septembre avec `tools/explainer/engine.py` (machine non calée, identique aux drivers de `am.blend` à 6,4e-7 rad près, voir `validate_blend.json`). Les signes d'éclipse viennent de `glyphs.json` (`modele_epoque_t0`, règle `limits`), la même table que la page web. Il faudra quand même recontrôler dans Blender avant le rendu, avec la méthode de `tools/crosscheck_blend.py`.

| Chap. | Manivelle (ans) | Ce qui se passe dans notre modèle |
|---|---|---|
| 1 | 0 (explode 1 → 0, patina 1 → 0,15). Éclairs du plan 1.2 à 9,014 · 0,99 · 2,31 · 5,95 | la machine se remonte |
| 2 | 0 → 0,6 → 0,7 → 0,3 → 0,972 | nouvelle lune à 0,972 : aiguilles de la Lune et du Soleil superposées, boule noire |
| 3 | 0,972 → 1,009 | pleine lune à 1,009 : Lune vers 182° (2° dans ΧΗΛΑΙ), sphère dorée vers 5° et aiguille de date vers 3° (dans ΚΡΙΟΣ) |
| 4 | 1,009 → 2,10 → 2,52 | Mars s'arrête vers 2,213, recule jusqu'à 2,413 environ, puis repart (opposition vers 2,31) |
| 5 | 2,52 → 5,95 | Jeux (étiquettes actuelles du modèle) : ΟΛΥΜΠΙΑ (an 1) jusqu'à 2,911, puis ΙΣΘΜΙΑ (an 2, étiquette fausse, voir note 2), ΠΥΘΙΑ (an 3, dès 3,911), ΝΕΜΕΑ (an 4, dès 4,911), et de nouveau ΟΛΥΜΠΙΑ dès 5,911 |
| 6 | 5,95 → 8,66 (rapide) → 8,98 (lent) → 9,014 | l'aiguille du Saros quitte la case 107 (signe Η) à 8,651. Les cases 108 à 111 sont sans signe. Elle entre dans la case 112 à 8,975 (signe calculé « Σ Η »). Nouvelle lune à 8,976 (Lune à 15,1° du nœud), pleine lune à 9,014 (Lune à 0,5° de l'aiguille du Dragon). L'Exeligmos est dans le secteur vide (+0 h) |
| 7 | 9,014 → 9,13 → 9,60 | le Soleil passe vers 47° (17° dans ΤΑΥΡΟΣ), puis vers 216° (ΣΚΟΡΠΙΟΣ) |

---

## 1. Le ciel dans une boîte (environ 24 s)

> Il y a plus de deux mille ans, quelqu'un a enfermé le ciel dans une boîte : éclipses, phases de la Lune, planètes, et même les Jeux olympiques. En 1900, des pêcheurs d'éponges découvrent l'épave d'Anticythère. En 1902, sur un bloc de bronze rongé, apparaît une roue dentée. Apprenons à lire cette machine.

| Plan | Durée | Cadrage | Action | Textes à l'écran | Schéma 2D |
|---|---|---|---|---|---|
| 1.1 | 0-6,5 s | Atelier inondé de lumière, boîtier en bois fermé sur l'établi (mode `case`), lent travelling avant | Rien ne bouge (crank 0). Il faut accrocher le regard dans les 5 premières secondes : un rai de soleil glisse sur le boîtier | (aucun) | (aucun) |
| 1.2 | 6,5-10,5 s | Quatre plans serrés d'une seconde sur la reconstruction (patine 0,15), calés sur l'énumération | « éclipses » : face avant à 9,014 (Soleil, Lune et aiguille du Dragon alignés, sans signe d'éclipse) ; « phases » : boule des phases à 0,99 (moitié claire) ; « planètes » : sphères et étiquettes à 2,31 ; « Jeux » : secteur ΟΛΥΜΠΙΑ à 5,95 | (aucun) | (aucun) |
| 1.3 | 10,5-14,5 s | Carte animée, mer agitée | Un point « épave » pulse près d'Anticythère | « Printemps 1900 » · « Pêcheurs d'éponges de Symi » · « 40–50 m de fond » | Carte stylisée : Péloponnèse, Cythère, Anticythère, Crète |
| 1.4 | 14,5-24 s | Gros plan en lumière rasante sur une roue corrodée, puis recul jusqu'au trois-quarts avant (`front34`) | patina 1, explode 1 (pièces dispersées), lente rotation de la caméra. Sur « Apprenons… » (vers 20,5 s) : explode 1 → 0 et patina 1 → 0,15, les pièces se remontent et le bronze s'éclaircit | « 1902 : une roue dentée » · « 82 fragments · ≈ 1/3 » · « 30 roues dentées conservées », puis « Notre reconstruction · 69 roues » | (aucun) |

## 2. La manivelle, c'est le temps (environ 14 s)

> Voici notre reconstruction. Sur le côté, une manivelle. Tournez-la : toutes les aiguilles avancent ensemble. En avant, le temps passe ; en arrière, il remonte. Un peu plus de quatre tours et demi : une année.

| Plan | Durée | Cadrage | Action | Textes à l'écran | Schéma 2D |
|---|---|---|---|---|---|
| 2.1 | 0-6,5 s | Gros plan sur la manivelle, côté droit (arbre a) | crank 0 → 0,6. Le compteur apparaît | « La manivelle = le temps » · compteur « Temps écoulé » | (aucun) |
| 2.2 | 6,5-10 s | Trois-quarts avant, toutes les aiguilles dans le champ | Sur « En avant » : crank 0,6 → 0,7. Sur « en arrière » : 0,7 → 0,3, tout recule et le compteur redescend | « En arrière : le passé » | (aucun) |
| 2.3 | 10-14 s | Face avant, grande roue b1 surlignée derrière le cadran (léger fantôme) | crank 0,3 → 0,972, en accélérant | « ≈ 4,6 tours = 1 an » · « Grande roue : 1 tour/an » | (aucun) |

## 3. Lire la face avant (environ 24 s)

> Devant, deux anneaux : le calendrier égyptien de trois cent soixante-cinq jours, et le zodiaque. La sphère dorée, c'est le Soleil : il donne la date et son signe. La Lune fait le tour en un mois, à vitesse variable, comme la vraie. Sa petite boule montre la phase. Aiguilles superposées : noire, nouvelle lune. Opposées : blanche… pleine lune.

| Plan | Durée | Cadrage | Action | Textes à l'écran | Schéma 2D |
|---|---|---|---|---|---|
| 3.1 | 0-6 s | Face avant rapprochée (`CAM_front_close`) | crank fixé à 0,972. Un reflet balaie l'anneau extérieur, puis l'anneau intérieur | « Calendrier égyptien · 365 j » · « Zodiaque · 12 signes » | (aucun) |
| 3.2 | 6-11 s | Même cadrage | La sphère dorée et l'aiguille de date s'allument. Deux traits fins partent vers l'anneau extérieur (date) et l'anneau intérieur (signe) | « Soleil : date + signe » · en petit : « Sphère dorée : citée par l'inscription · son engrenage : hypothèse » | (aucun) |
| 3.3 | 11-16,5 s | Aiguille de la Lune | L'aiguille est surlignée, crank toujours à 0,972 (superposée au Soleil) | « Lune : 1 tour/mois » · « Vitesse variable (Hipparque) » | Option : petite courbe de vitesse de la Lune sur un mois |
| 3.4 | 16,5-24 s | Très gros plan sur la boule des phases, en incrustation dans la face avant | La boule est noire au départ. Sur « Opposées », crank 0,972 → 1,009, puis tenue 1 s sur la boule blanche | « Superposées : nouvelle lune » · « Opposées : pleine lune » · « Lune dans ΧΗΛΑΙ (Balance) » | Petit schéma vu de dessus (Soleil, Terre, Lune) : la Lune passe de « entre les deux » à « opposée » |

## 4. Les planètes, une hypothèse (environ 17 s)

> Autour du centre, cinq petites sphères : les planètes, lues sur le zodiaque. Leurs engrenages ont presque tous disparu : c'est une reconstruction, une hypothèse. Regardez Mars : sa sphère s'arrête… puis recule, comme dans le ciel quand la Terre dépasse Mars.

| Plan | Durée | Cadrage | Action | Textes à l'écran | Schéma 2D |
|---|---|---|---|---|---|
| 4.1 | 0-9 s | Face avant rapprochée, étiquettes des planètes visibles (AM_LABELS) | crank 1,009 → 2,10 à vitesse moyenne | « Planètes : lire sur le zodiaque » · « Hypothèse · Freeth et al. 2021 » · « Couleurs modernes » | (aucun) |
| 4.2 | 9-13 s | Cadrage serré sur la sphère rouge de Mars et son anneau | crank 2,10 → 2,52 lentement. Arrêt vers 2,213, recul jusqu'à 2,413 environ. Une traînée lumineuse sur l'anneau montre l'aller-retour | « Station » · « Rétrogradation » · « “stêrigmos” dans l'inscription » | (aucun) |
| 4.3 | 13-17 s | Écran partagé : la machine à gauche, le schéma à droite | Reprise de la même plage de manivelle (compteur masqué pendant la reprise), synchronisée avec le schéma | « Vue de la Terre » · « La Terre dépasse Mars » | Soleil au centre, orbites de la Terre et de Mars. Les lignes de visée Terre → Mars se projettent sur une bande d'étoiles et y dessinent une boucle |

## 5. Le dos : les mois et les Jeux (environ 18 s)

> Retournons la machine. En haut, une spirale de deux cent trente-cinq mois : dix-neuf ans. Chaque case, un mois, avec son nom. Dedans, un petit cadran fait un tour en quatre ans. Tournons… Olympia ! Cette année, les Jeux olympiques. L'année, pas le jour.

| Plan | Durée | Cadrage | Action | Textes à l'écran | Schéma 2D |
|---|---|---|---|---|---|
| 5.1 | 0-2,5 s | Orbite de 180° autour de la machine, jusqu'à `CAM_back_close` | crank 2,52 → 2,6 | (aucun) | (aucun) |
| 5.2 | 2,5-9,5 s | Spirale du haut (Méton) | crank 2,6 → 3,0. Le curseur est surligné dans le sillon | « 235 mois = 19 ans » · « 1 case = 1 mois » · « Mois corinthiens » | Case agrandie, illustrative, d'après Freeth et al. 2008 : « Phoinikaios… an 1 » |
| 5.3 | 9,5-18 s | Petit cadran des Jeux, en gros plan | crank 3,0 → 5,95, rapide puis ralenti. L'aiguille arrive sur ΟΛΥΜΠΙΑ vers 5,911 et le secteur s'illumine. Les étiquettes du cadran sont remplacées par les paires historiques dans la copie de travail (note 2), sinon le secteur de l'an 2 contredit le bandeau | « 1 tour = 4 ans » · « Olympia : année des Jeux » · « L'année, pas le jour » | Bandeau des 4 années d'origine (Freeth et al. 2008, Iversen 2017) : « An 1 : Isthmia, Olympia » · « An 2 : Nemea, Naa » · « An 3 : Isthmia, Pythia » · « An 4 : Nemea, Halieia » |

## 6. Prédire une éclipse (environ 30 s)

> En bas, le Saros : deux cent vingt-trois mois, puis les éclipses reviennent. La plupart des cases sont vides. Tournons… Une case gravée ! Sigma : éclipse de Lune. Êta : de Soleil. Puis l'heure ; ce cadran y ajoute zéro, huit ou seize heures. Devant, la pleine lune tombe sur l'aiguille du Dragon, hypothétique elle aussi : une éclipse est possible. Attention : ces signes sont calculés par notre modèle. Et la machine ne disait pas où l'observer.

| Plan | Durée | Cadrage | Action | Textes à l'écran | Schéma 2D |
|---|---|---|---|---|---|
| 6.1 | 0-7,5 s | Spirale du bas (Saros), face arrière | crank 5,95 → 8,66, rapide. Les cases gravées calculées clignotent au passage de l'aiguille (la dernière est la case 107, Η) | « Saros : 223 mois » · « ≈ 18 ans 11 jours » · « Cycle babylonien » | (aucun) |
| 6.2 | 7,5-13 s | Même cadrage, plus serré sur l'aiguille | crank 8,66 → 8,98, lent. Les cases vides 108 à 111 défilent, puis l'aiguille entre dans la case 112 (à 8,975) et le signe « Σ Η » s'allume | « Case vide : pas d'éclipse » · « Σ = éclipse de Lune » · « Η = éclipse de Soleil » · en petit : « Signe calculé par notre modèle » | (aucun) |
| 6.3 | 13-17,5 s | Très gros plan sur le signe, puis panoramique vers le petit cadran Exeligmos | crank fixé. L'aiguille de l'Exeligmos est dans le secteur vide | « ΩΡ + chiffre = heure » · « Exeligmos : +0, +8, +16 h » · « Ici : +0 h » · « Lettre d'index → détails » | Anatomie d'un signe, marquée « exemple » : Σ, ΩΡ + chiffre, lettre d'index. La case 112 elle-même ne porte ni heure ni lettre (note 1) |
| 6.4 | 17,5-23,5 s | Coupe vers la face avant rapprochée | crank 8,98 → 9,014. La Lune vient se poser sur un bout de l'aiguille du Dragon, le Soleil est à l'autre bout ; l'aiguille s'illumine. La boule passe du noir au blanc | « Aiguille du Dragon : hypothèse » · « Dragon = nœuds de la Lune » · « Pleine lune sur le Dragon : éclipse possible » | (aucun) |
| 6.5 | 23,5-30 s | Schéma plein écran, puis retour sur la machine | La Lune traverse l'ombre de la Terre et s'assombrit | « Signes calculés par notre modèle » · « Possible · pas le lieu » | Géométrie d'une éclipse de Lune : Soleil, Terre, cône d'ombre, Lune |

## 7. Et la navigation ? (environ 38 s)

> Servait-elle à naviguer ? Non : ni viseur, ni latitude, ni longitude. C'est un calculateur du ciel. Mais regardez ces plaques : un calendrier des étoiles. Quand le Soleil atteint la lettre ksi, on lit : « La Pléiade se lève le matin. » Bien plus tard, pour Végèce, la mer est sûre après ce lever. Déjà Hésiode avertissait : quand les Pléiades « tombent dans la noire mer », rentre tes navires. La machine ne disait pas où aller, mais quand partir. La voici reconstruite, ses rapports prouvés mathématiquement, en accès libre. Et vous, quelle date allez-vous lui demander ?

| Plan | Durée | Cadrage | Action | Textes à l'écran | Schéma 2D |
|---|---|---|---|---|---|
| 7.1 | 0-6,5 s | Plan large de l'atelier (mode `wide`), trois-quarts avant, fenêtre ouverte sur le ciel et les collines (le décor actuel ne montre pas la mer ; pour la voir, ajouter une bande de mer dans `exterior_material()`) | crank fixé à 9,014 | « Pas un instrument de navigation » · « Ni viseur, ni latitude, ni longitude » · « Calculateur du ciel » | (aucun) |
| 7.2 | 6,5-16 s | Face avant, les deux plaques du parapegme surlignées | crank 9,014 → 9,13 (Soleil vers 47°, ΤΑΥΡΟΣ). Un Ξ en surimpression sur l'échelle du zodiaque, sous le Soleil. La ligne s'écrit en surimpression sur la plaque du haut | « Parapegme : calendrier des étoiles » · « Ξ : la Pléiade se lève » | (aucun) |
| 7.3 | 16-21 s | Schéma plein écran, puis bref retour sur l'anneau égyptien | Aube de mai : les Pléiades se lèvent à l'est avant le Soleil. Une barre de saison se remplit. Au retour, ΠΑΧΩΝ s'illumine sur l'anneau | « Végèce (IVe-Ve s. apr. J.-C.) » · « Mer sûre : 27 mai–14 sept. » · « ΠΑΧΩΝ : mois cité par Végèce » | Mer à l'aube, amas des Pléiades au-dessus de l'horizon est. Barre de saison (d'après Végèce) |
| 7.4 | 21-31 s | Schéma en incrustation sur la machine, puis retour plein cadre sur la machine à « La machine ne disait pas… » | crank 9,13 → 9,60 (Soleil vers 216°, ΣΚΟΡΠΙΟΣ). Dans le schéma, les Pléiades plongent dans une mer grise et ventée. Aucune ligne de parapegme n'est incrustée ici : le coucher des Pléiades n'est pas conservé sur la machine | « Hésiode, Les Travaux et les Jours » · « Fin oct.–début nov. : quitter la mer » · « Végèce : mer fermée du 11 nov. au 10 mars » · « Pas où aller : quand partir » | Pléiades se couchant dans la mer à l'aube, vagues |
| 7.5 | 31-35 s | Plan large de l'atelier au soleil, lente orbite de la caméra | explode 0 → 0,3 → 0 (la machine « respire »), la manivelle tourne doucement | « 69 roues · 30 conservées » · « Rapports prouvés (Lean 4) » · « Code et modèle libres · GitHub » · « taciclei » | (aucun) |
| 7.6 | 35-38 s | Carton final sur fond crème, la machine en fondu derrière | Les étapes apparaissent ensemble, puis la question | « 1. Tournez la manivelle » · « 2. Soleil : date, saison » · « 3. Lune : place, phase » · « 4. Planètes : place (hypothèse) » · « 5. Dos : mois, Jeux » · « 6. Signe : éclipse, heure » · « Et vous, quelle date ? » | (aucun) |

---

## Notes de réalisation

### Ce que le modèle ne montre pas encore (à compléter en 2D ou dans une copie de travail, jamais dans `am.blend`)

1. **Signes d'éclipse.** Dans la spec, la spirale du Saros n'a que des « placeholders ». Les signes affichés viennent de `glyphs.json` (`modele_epoque_t0`, règle `limits` : Σ si la pleine lune est à 10,8° au plus du nœud, Η si la nouvelle lune est à 17° au plus). C'est la table que lit aussi la page web ; la règle `freeth2014` donne les mêmes signes pour les cases 106 à 112. Case 112 : nouvelle lune à 8,976 (15,1° du nœud, donc Η) et pleine lune à 9,014 (0,5°, donc Σ). Le signe est donc « Σ Η » (Σ d'abord, comme sur l'original). La case 107 porte un Η, les cases 108 à 111 sont vides. Avant elles : 106 Σ, 101 Η, 100 Σ, 95 Η, 89 Η, 83 Σ Η, 77 Σ Η. **L'heure n'est pas calculée** : `glyphs.json` n'en donne pas, et elle n'aurait pas de sens tant que l'époque n'est pas calée. On n'écrit donc ni ΩΡ ni lettre d'index sur la case 112, et l'anatomie du plan 6.3 est un schéma marqué « exemple ».
2. **Cadran des Jeux.** Le modèle porte un seul nom par secteur (spec : ΙΣΘΜΙΑ, ΟΛΥΜΠΙΑ, ΝΕΜΕΑ, ΠΥΘΙΑ). Quand on tourne vers l'avant, on lit ΟΛΥΜΠΙΑ (an 1) → ΙΣΘΜΙΑ (an 2) → ΠΥΘΙΑ (an 3) → ΝΕΜΕΑ (an 4). Les ans 1, 3 et 4 portent bien une des deux fêtes historiques, mais l'an 2 est faux : l'original y porte Nemea et Naa, pas Isthmia. Comme le plan 5.3 passe sur ce secteur pendant que le bandeau affiche « An 2 : Nemea, Naa », il faut, dans la copie de travail, remplacer les quatre étiquettes par les paires historiques. Index 0 de la spec (an 2) : ΝΕΜΕΑ ΝΑΑ. Index 1 (an 1) : ΙΣΘΜΙΑ ΟΛΥΜΠΙΑ. Index 2 (an 4) : ΝΕΜΕΑ ΑΛΙΕΙΑ. Index 3 (an 3) : ΙΣΘΜΙΑ ΠΥΘΙΑ.
3. **Parapegme et lettres-repères.** Les plaques du modèle portent un texte provisoire, et l'échelle du zodiaque n'a pas de lettres. Le Ξ et la ligne « La Pléiade se lève le matin » sont donc des surimpressions. Leur position (Soleil vers 17° du Taureau, en écho au nombre 17 de la ligne Ξ) sert seulement d'illustration.
4. **Cases de Méton.** Elles ne portent pas de noms dans le modèle. L'incrustation « Phoinikaios… an 1 » est une illustration d'après Freeth et al. 2008.
5. **Soleil.** La sphère dorée (Soleil vrai, mécanisme hypothétique) et l'aiguille de date (Soleil moyen) s'écartent de 2,4° au plus. Au plan 3.2, on les surligne ensemble.
6. **Anneau égyptien.** Il était amovible dans l'original, mais il est fixe dans le modèle. Le film ne s'en sert pas pour lire une date historique.
7. **Fenêtre de l'atelier.** Le décor actuel (`exterior_material()`) montre un ciel et des collines, pas la mer. Le plan 7.1 s'en contente, sauf si l'on ajoute une bande de mer au décor.

### Mentions d'honnêteté obligatoires à l'écran

- Chap. 3 : « Sphère dorée : citée par l'inscription · son engrenage : hypothèse ».
- Chap. 4 : « Hypothèse · Freeth et al. 2021 » et « Couleurs modernes ».
- Chap. 6 : « Signe calculé par notre modèle » dès que le signe s'allume, « Aiguille du Dragon : hypothèse », « Signes calculés par notre modèle ». L'anatomie du signe est marquée « exemple ».
- Chap. 7 : « Pas un instrument de navigation ». Végèce est daté (IVe-Ve s. apr. J.-C.), donc bien après la machine, et la voix le dit (« Bien plus tard »). Hésiode et Végèce témoignent de la tradition des saisons de navigation : aucun des deux ne parle de la machine.
- À ne jamais écrire ni dire : « premier ordinateur », « construite par Archimède », « date exacte des Jeux », « découverte en 1901 ». L'épave a été trouvée en 1900 et la machine remarquée en 1902.
- Crédit : « taciclei », comme dans `LICENSE` et le README. Ne pas écrire de nom complet tant que l'auteur ne l'a pas donné.

### Prononciation (synthèse vocale)

Anticythère : « an-ti-si-tèr » · Végèce : « vé-jèss » · Hésiode : « é-zi-ode » · Pléiade : « plé-yade » · Saros : « sa-ross » · ksi : « ksi » · Sigma : « sig-ma » · Êta : « è-ta » · Olympia : « o-lin-pi-a ». Aucun mot grec n'est prononcé en dehors de Sigma, Êta, ksi et Olympia : les autres restent à l'écran.

### Sources par chapitre (fiche `faits.md`)

1. Découverte : WHOI, NAM, Jones 2020, Freeth et al. 2021.
2. Manivelle : guide de lecture, spec (223/48 tours de manivelle par an).
3. Face avant : Bitsakis & Jones 2016, Freeth et al. 2006, Freeth & Jones 2012, Freeth et al. 2021 (Soleil vrai hypothétique).
4. Planètes : Freeth & Jones 2012, Freeth et al. 2021.
5. Dos : Freeth et al. 2008 (+ SI), Iversen 2017, Jones 2020, NAM.
6. Éclipses : Freeth et al. 2008 SI, Freeth 2014, Freeth 2019. Signes : notre modèle (`glyphs.json`).
7. Navigation : Freeth et al. 2021, Jones 2017, Bitsakis & Jones 2016, Hésiode (trad. Leconte de Lisle), Végèce IV, 39. Preuves : README (193 théorèmes Lean 4).
