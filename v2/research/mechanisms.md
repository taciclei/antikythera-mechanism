# Anticythère 2.0 — Mécanismes : la meilleure réalisation de chaque sous-système

*Recherche du 3 octobre 2026. Les chiffres viennent des scripts de `research/calc/`, en Python et numpy. Aucun n'est estimé à la main. Les commandes pour les refaire sont au § 9.*

## Comment lire ce document

- Chaque section suit le même plan : le problème, les mécanismes possibles, les chiffres, la recommandation, puis ce qui reste hors de portée.
- Sauf mention « rms », une erreur est un **maximum** sur 2000–2100, échantillonné toutes les 6 heures (toutes les 1,2 h pour la Lune).
- Ce document se limite à la **géométrie des mécanismes**. Les erreurs de rapports d'engrenages (moyens mouvements) font l'objet d'une étude séparée. Ici, chaque mécanisme reçoit les **mêmes** longitudes moyennes que la référence.
- Les valeurs des constantes sont dans `constants.md`, l'histoire des machines dans `precedents.md`. Ce document les recoupe sans les répéter.
- Notations : e (excentricité), a (demi-grand axe), M (anomalie moyenne), E (anomalie excentrique), ν (anomalie vraie), ϖ (longitude du périhélie), λ (longitude écliptique), s (échelle d'un module en mm par unité astronomique, ua).
- « Goupille et rainure » désigne le *pin-and-slot* d'Anticythère, soit, dans la spec v1, une goupille portée par une roue qui glisse dans la rainure radiale d'une autre roue dont l'axe est décalé.

---

## 0. L'essentiel

| Sous-système | Mécanisme recommandé | Précision attendue |
|---|---|---|
| **Kepler** (angle héliocentrique et distance) | Pour 6 planètes, l'**équant à excentricité bissectée**, c'est-à-dire *une* goupille et rainure menée par la rainure : un bras rainuré tourne uniformément autour du point équant, une manivelle tourne autour du centre de l'orbite. Mars ajoute un **épicyclet correcteur** (e²). Mercure utilise un **résolveur mécanique de l'équation de Kepler** (différentiel, coulisse écossaise et crémaillère) suivi d'une ellipse à deux bras contrarotatifs | Erreur de modèle sur l'angle héliocentrique : Mercure 0 (exact), Mars 0,02°, les autres ≤ 0,05° |
| **Héliocentrique vers géocentrique** | **Un module vectoriel par planète**, sur axes fixes. C'est le suiveur d'Anticythère appliqué à un *mini-orrery de calcul à l'échelle exacte* (deux bras, un suiveur), et non à l'orrery du couvercle. Les excentricités entrent par les angles des manivelles et par un **décalage du pivot du suiveur**, sans aucune pièce de plus. L'orrery du couvercle est mené par les mêmes arbres | Erreur géocentrique maximale de la géométrie seule, 2000–2100 : Me 0,26° · Vé 0,21° · Ma 0,24° · Ju 0,07° · Sa 0,08° · Ur 0,05° · Ne 0,02°. S'y ajoutent les tolérances (0,03–0,12° pour 0,02 mm) et la physique hors Kepler (Ju 0,11°, Sa 0,17°) |
| **Lune** | **Cascade de 5 étages** « à la table e d'Anticythère » : réduction à l'écliptique, équation annuelle (différentiel), évection, anomalie en équant, variation | Longitude : 0,26° maximum, 0,10° rms. Latitude aux syzygies : 0,05° |
| **Calendrier grégorien** | Un **arbre-jour maître**. Un anneau de 366 positions avancé par croix de Malte, plus un pas de « saut » du 29 février. Des **roues-programmes continues** 1:4, 1:25 et 1:4 menées par l'anneau, avec une logique à cames | Exact. Simulé sans faute de 1582 à 6000. Marges de came ±45°, ±1,8° et ±45° |
| Jour de la semaine | 1:7 depuis l'arbre-jour | Exact |
| **Temps sidéral** | Un différentiel qui somme l'heure solaire moyenne, le Soleil moyen et la précession | Identité exacte (écart de 0,06 s par siècle à la formule IAU). Il reste l'erreur du rapport de l'année |
| **Équation du temps** | Un **joint de Hooke** plié à ε = 23,44° (la réduction à l'équateur, exacte) monté *après* l'unité de Kepler de la Terre, avec une entrée de précession | ≤ 3 s sur 2000–2100. Une came fixe taillée pour 2050 donne 8 s |
| **Précession** | Un seul anneau (le zodiaque tropique) tourne une fois en 25 771,6 ans par rapport à la caisse, qui sert de repère fixe J2000 | 4 couples de roues 23·14·14·12 / 212·208·208·152 : 2,5·10⁻⁹. Un écart de 0,1 % suffirait |
| **Éclipses** | Une coulisse écossaise sur le **porte-nœuds**, menée par **la goupille de l'unité d'anomalie lunaire**. Elle donne directement γ ∝ r·sin F, la distance comprise. Des échelles de magnitude linéaires en γ. Un **globe-ombre** (Terre en tellurion, aiguille d'ombre décalée de γ) pour le lieu | Validé contre le canon NASA 2001–2100 : 449 éclipses sur 452 détectées, et toutes les erreurs sont à \|γ\| ≈ 1,55. γ à ±0,03 près. Heure à ±0,53 h. Magnitude d'ombre ±0,09 (0,04 rms). Totale ou annulaire : 147 sur 147. Lieu du maximum à 1,4° rms en latitude et 4,1° rms en longitude. Hémisphère juste dans 99 % des cas |
| **Lunes galiléennes** | Une **boîte de Laplace** : Ganymède et ν viennent de deux trains. Europe = 2·Ganymède + ν, Io = 2·Europe + ν, avec deux doubleurs et deux différentiels. La relation de Laplace est donc **exacte par construction**. Un **cadran jovien** et une **lunette** à coulisses écossaises orientée par le module géocentrique de Jupiter | Dérive des trains à 3 couples < 0,001° par siècle. Résidu physique de ±0,5 à 1,1° (inégalités) et ±1,5° pour Io (temps de lumière) |

**Les trois idées neuves du document** (aucune trouvée chez les précédents de `precedents.md`) :

1. **Le décalage du pivot du suiveur.** Dans un module, deux bras de longueur constante tournent aux angles « autour du centre » des deux équants. La somme vectorielle est exacte si l'on décale le pivot du suiveur de s·(C_Terre − C_planète), où C est le centre de chaque orbite excentrique. Toute l'excentricité tient donc dans la position d'un trou.
2. **Le résolveur mécanique de l'équation de Kepler.** C'est une boucle fermée entre un différentiel et une coulisse écossaise, qui impose M = E − e sin E. Mercure y gagne une position exacte.
3. **La coulisse d'éclipse menée par la goupille d'anomalie.** La coulisse calcule le produit r·sin F, la distance comprise, sans multiplicateur.

---

## 1. Le mouvement de Kepler (équation du centre)

### 1.1 Ce qu'il faut reproduire

L'anomalie vraie s'écarte de l'anomalie moyenne selon une série connue :

ν − M = 2e sin M + (5/4) e² sin 2M + e³ [(13/12) sin 3M − (1/4) sin M] + O(e⁴),
avec la distance r = a (1 − e cos E).

**Un point décide de tout le reste du document.** Pour l'**orrery** (vue héliocentrique), seul l'**angle** compte. Pour le **cadran géocentrique**, il faut l'angle **et la distance** au Soleil, car la direction Terre-planète dépend des deux vecteurs. Un mécanisme bon en angle mais faux en distance donne des erreurs géocentriques de plusieurs degrés (§ 2.2, ligne « goupille et rainure + bras constant »).

### 1.2 Cinq mécanismes candidats

**(a) Goupille et rainure simple** (Anticythère, Freeth 2006 et 2021 [F06, F21]). La sortie vaut θ₂ = θ₁ + atan2(k sin θ₁, 1 − k cos θ₁), avec k = décalage/rayon. C'est l'**excentrique simple d'Hipparque** vu du centre de la roue à rainure. Pour viser 2e sin M au premier ordre, on prend k = 2e. Le mécanisme ne fournit que l'angle. Si on lui associe un cercle, celui-ci est décentré de 2e, d'où une variation de distance **deux fois trop grande**.

**(b) Équant à excentricité bissectée** (Ptolémée). La planète parcourt un cercle de rayon ρ centré en C. Son mouvement est uniforme vu du point équant Q. L'observateur, au foyer O, est symétrique de Q par rapport à C, avec QC = CO = eρ. **Mécanisme** : trois axes parallèles Q, C, O alignés sur la ligne des apsides.
- Un bras rainuré pivote en Q et tourne uniformément à l'anomalie moyenne.
- Une manivelle de rayon ρ pivote en C. Sa goupille glisse dans la rainure du bras.
- C'est **une seule** goupille et rainure, menée côté rainure. L'angle de la manivelle, noté φ_C, est la sortie « angle autour du centre ».
- On peut ajouter un suiveur rainuré pivoté en O, qui passe par la goupille et donne l'anomalie vraie (sortie « angle vu du foyer »).
- La distance est juste au premier ordre, grâce au cercle centré en eρ.

**(c) Équant + épicyclet correcteur (« EQE »).** L'erreur de position de l'équant vaut presque exactement (e²/4)·a·[u(3M) − u(M)], où u(x) est le vecteur unitaire d'angle x (analyse de Fourier, `kepler_models.py`). Deux retouches suffisent :
- raccourcir la manivelle de e²a/4 ;
- ajouter au bout un **épicyclet** de rayon e²a/4 dont l'angle absolu vaut 3M (ou 3L − 2ϖ en longitude). On l'obtient par un couple 3:1 sur l'arbre de M.

C'est l'épicyclet de Copernic, mis au service de Kepler.

**(d) Foyer vide (Ward, 1653 [W53]).** La planète suit l'ellipse vraie, avec un mouvement uniforme vu du foyer vide. L'erreur est −(1/4) e² sin 2M : **pas meilleure que l'équant** en angle, et il faut tailler une ellipse. Écarté.

**(e) Résolveur mécanique de l'équation de Kepler (« RK »).** On veut l'anomalie excentrique E telle que M = E − e sin E.
- Une manivelle de rayon R_y, calée sur l'arbre E, mène une **coulisse écossaise** (*Scotch yoke*), ce qui donne x = R_y sin E.
- Une crémaillère portée par la coulisse fait tourner un pignon de rayon ρ_p de δ = (R_y/ρ_p) sin E. On choisit R_y/ρ_p = e, par exemple R_y = 3,084 mm et ρ_p = 15 mm pour Mercure.
- Un **différentiel** relie M (mené par le train du temps), E et δ par M = E − δ. La boucle est fermée, et E est imposé.
- Le facteur de transmission dM/dE = 1 − e cos E reste dans [0,79 ; 1,21] pour Mercure. Il n'y a jamais de point mort, et n'importe quel membre peut mener.
- L'ellipse exacte s'obtient ensuite par **deux bras contrarotatifs** : (a + b)/2 à l'angle ϖ + E et (a − b)/2 à l'angle ϖ − E, centrés au centre de l'ellipse, qui est à ae du foyer.

Ces boucles qui résolvent une équation implicite sont celles des calculateurs de conduite de tir de 1944 (différentiels, résolveurs, cames) [OP1140]. Le résultat est **exact**. Le prix est un différentiel, une coulisse, une crémaillère, plus un bras minuscule, car (a − b)/2 vaut 0,0107·a pour Mercure.

### 1.3 Erreurs en fonction de e (développements vérifiés numériquement)

| Mécanisme | Erreur d'angle (vu du foyer) | Erreur de position | Max à e = 0,1 | Max à e = 0,2056 |
|---|---|---|---|---|
| Goupille et rainure, k = 2e | +(3/4) e² sin 2M + O(e³) | ≈ 2e·a (distance doublée) | 0,52° | 2,79° |
| Équant bissecté | −(1/4) e² sin 2M − e³[(1/2) sin M + (1/6) sin 3M] | ≈ e²a/2 | 0,17° | 0,89° |
| Équant + épicyclet | e³[(1/8) sin M − (7/24) sin 3M] | ≈ 0,58 e³ a | 0,024° | 0,19° |
| Foyer vide (Ward) | −(1/4) e² sin 2M | 0 en rayon | ≈ équant | ≈ équant |
| Résolveur de Kepler | 0 | 0 | 0 | 0 |

Ordre de grandeur historique : pour Mars, l'équant bissecté se trompe de 0,149° ≈ 9′. C'est l'écart que Kepler n'a pas pu accepter dans l'*Astronomia nova*, les fameuses « 8 minutes » [AN].

Pour l'**angle seul**, il existe une variante d'équant optimisée : centre en 1,25e à 1,28e au lieu de e, équant en 2e. L'erreur d'angle tombe à 0,37° pour Mercure et 0,036° pour Mars, mais la distance devient fausse au premier ordre. Cette variante convient à l'orrery, pas au calcul géocentrique.

### 1.4 Par planète : erreur de modèle sur l'angle héliocentrique, éléments J2000

| Corps | e | 2e (°) | Goupille et rainure | Équant | Équant + épicyclet | Position, équant (·a) | Position, EQE (·a) |
|---|---|---|---|---|---|---|---|
| Mercure | 0,2056 | 23,56 | 2,79° | 0,895° | 0,195° | 0,0217 | 0,0054 |
| Vénus | 0,0068 | 0,78 | 0,002° | 0,0007° | ~0 | 0,00002 | ~0 |
| Terre | 0,0167 | 1,92 | 0,012° | 0,004° | 0,0001° | 0,00014 | 0,000003 |
| Mars | 0,0934 | 10,70 | 0,446° | 0,149° | 0,019° | 0,0044 | 0,00049 |
| Jupiter | 0,0484 | 5,55 | 0,110° | 0,037° | 0,003° | 0,0012 | 0,00007 |
| Saturne | 0,0539 | 6,17 | 0,137° | 0,046° | 0,004° | 0,0015 | 0,00009 |
| Uranus | 0,0473 | 5,42 | 0,105° | 0,035° | 0,003° | 0,0011 | 0,00006 |
| Neptune | 0,0086 | 0,98 | 0,003° | 0,001° | ~0 | 0,00004 | ~0 |
| Lune (anomalie) | 0,0549 | 6,29 | 0,143° | 0,048° | 0,004° | 0,0015 | 0,0001 |

### 1.5 Recommandation par planète

- **Mercure : résolveur de Kepler.** C'est le cas difficile, et la pièce maîtresse « 2026 » de la machine. L'équant + épicyclet (0,19°) est la solution de repli.
- **Mars : équant + épicyclet.** L'équant seul laisse 0,60° d'erreur géocentrique à l'opposition (§ 2.5).
- **Terre, Vénus, Jupiter, Saturne, Uranus, Neptune : équant bissecté**, soit une goupille et rainure menée par la rainure.

Pour la Terre, l'équant est **obligatoire**, et non un simple excentrique : la distance Terre-Soleil pèse sur Vénus et Mars (§ 2.2).

**Unité d'angle képlérienne (UAK)**, une par planète, à une échelle confortable (ρ ≈ 20–30 mm) :
- les axes Q, C, O, séparés de eρ : 6,2 mm pour Mercure, 2,8 mm pour Mars, 1,0–1,6 mm pour les géantes à ρ = 30 mm. Pour Vénus, Neptune et la Terre, l'écart tombe sous 0,6 mm. On le réalise par des **bagues excentriques** (un palier annulaire autour d'un moyeu fixe) plutôt que par deux arbres ;
- l'entrée : l'arbre de longitude moyenne de la planète. La ligne des apsides est figée dans la caisse (§ 4.6) ;
- les sorties : φ_C (angle autour du centre), qui sert aux modules, et l'anomalie vraie par un suiveur en O, qui sert à l'orrery.

### 1.6 Ce que le modèle plan ne fait pas, chiffré

- **Inclinaison** (réduction à l'écliptique). Le mécanisme est plan. L'erreur atteint 0,21° en héliocentrique pour Mercure (tan²(i/2) = 0,0037 rad), soit **0,25° en géocentrique**, et 0,19° en géocentrique pour Vénus à la conjonction inférieure. C'est le premier poste résiduel pour ces deux planètes.
  Un joint de Hooke plié à i reproduirait exactement tan(λ − Ω) = cos i tan u, mais il ne s'insère pas dans un module plan. Une orbite physiquement inclinée de 7°, dont le suiveur lirait la projection, est possible mais délicate. Je ne la recommande pas.
- **Dérive séculaire de e et de ϖ** (formes d'orbites figées en 2050, repère fixe J2000). Erreur géocentrique maximale :

| Fenêtre | Mercure | Vénus | Mars | Jupiter | Saturne | Uranus | Neptune |
|---|---|---|---|---|---|---|---|
| 2050 ± 50 ans | 0,02° | 0,02° | **0,18°** | 0,02° | 0,04° | 0,004° | 0,001° |
| 2050 ± 100 ans | 0,03° | 0,04° | **0,33°** | 0,04° | 0,06° | 0,009° | 0,001° |
| 2050 ± 200 ans | 0,07° | 0,09° | **0,70°** | 0,07° | 0,16° | 0,02° | 0,003° |
| 2050 ± 500 ans | 0,17° | 0,23° | **1,88°** | 0,19° | 0,41° | 0,05° | 0,006° |

  Seul Mars compte. Remède à l'esprit antique : un **réglage séculaire**, c'est-à-dire une bague excentrique graduée que l'on tourne d'un cran par siècle, comme l'anneau égyptien d'Anticythère que l'on déplaçait à la main. Le remède mécanique serait un plateau d'apsides tournant d'un tour en 80 000 ans.
- **Perturbations planétaires.** Les éléments de Kepler du JPL (table 1, 1800–2050) s'écartent des éphémérides DE de 15″ (Mercure), 20″ (Vénus), 40″ (Mars), **400″ = 0,11° (Jupiter)**, **600″ = 0,17° (Saturne)**, 50″ (Uranus) et 10″ (Neptune) [JPL].
  Sur des millénaires, la **grande inégalité** domine (table 2b du JPL) : ±0,36° pour Jupiter et ±0,88° pour Saturne (période 939 ans), ±0,99° pour Uranus et ±0,69° pour Neptune (période 4 693 ans).
  Ces termes **sont mécanisables** : une roue très lente (939 ans) portant deux manivelles déphasées attaque, par deux différentiels, les arbres de longitude moyenne de Jupiter et de Saturne. Une seconde roue (4 693 ans) fait de même pour Uranus et Neptune. C'est inutile pour un siècle, car les éléments de la table 1 absorbent déjà la phase actuelle. C'est une option pour une machine « valable 3 000 ans ».

---

## 2. De l'héliocentrique au géocentrique

### 2.1 Pourquoi on ne peut pas viser sur l'orrery du couvercle

La direction Terre→planète vaut atan2(r_p sin l_p − r_T sin l_T, r_p cos l_p − r_T cos l_T). Elle ne dépend que du **rapport** r_p/r_T. Si l'orrery comprime les rayons de façon non uniforme, ce rapport est faux, et un bras de visée pivoté sur la Terre de l'orrery se trompe. Orbites circulaires moyennes, sur 2000–2100 :

| Compression des rayons (Terre) | Mercure | Vénus | Mars | Jupiter | Saturne | Uranus | Neptune |
|---|---|---|---|---|---|---|---|
| Espacement régulier de 20 mm (Terre à 70 mm) | 2,9° | 1,1° | 14,4° | **30,4°** | 27,4° | 25,1° | 22,6° |
| Racine carrée, 60·√a (60 mm) | 18,0° | 19,3° | 19,2° | 15,6° | 13,1° | 10,3° | 8,6° |
| Logarithmique, 70 + 40 ln a (70 mm) | 4,9° | 12,9° | 18,5° | 21,0° | 20,4° | 19,0° | 18,1° |
| *Pour comparaison : écart maximal vrai entre géocentrique et héliocentrique (la boucle à montrer)* | 180° | 180° | 47,4° | 11,9° | 6,4° | 3,2° | 1,95° |

Pour les planètes extérieures, l'erreur de compression **dépasse de 2 à 10 fois l'effet même que l'on veut montrer** (la rétrogradation). À l'échelle vraie, si Mercure a le rayon minimal raisonnable de 15 mm, Neptune est à **1,17 m** du centre. Le couvercle ne peut donc pas être à l'échelle.

### 2.2 Quatre architectures comparées

| Architecture | Exactitude | Complexité | Robustesse | Verdict |
|---|---|---|---|---|
| **A. Bras de visée sur un orrery à l'échelle vraie** (suiveur d'Anticythère sur la Terre de l'orrery, angle renvoyé au centre par chaînes 1:1, puis à l'avant) | Exacte si l'orrery reproduit les orbites képlériennes (rainures et angles exacts) | 7 bras empilés sur la Terre mobile, 7 chaînes sur le bras de la Terre, 7 tubes coaxiaux, 7 renvois d'angle **imbriqués** vers le cadran avant | Faible : bras longs, collisions avec les boules et les lunes | **Impossible pour les géantes** (Neptune à 1,2 m). Possible pour Mercure–Mars seulement : si la Terre est à 50 mm, Mars est à 83 mm à l'aphélie |
| **B. Pivots « Terre-relais »** (sur l'orrery comprimé, chaque planète extérieure a sa propre Terre, à r_p/R_p sur une barre qui tourne avec la Terre) | Bonne en angle si les orbites de l'orrery sont exactes. La distance Terre-Soleil n'est pas suivie : Ju 0,22°, Sa 0,15°, Ur 0,07°, Ne 0,04° | 4 pivots mobiles, 4 chaînes sur la barre, et le même problème de renvoi vers l'avant | Faible | Spectaculaire, mais ne convient pas comme chaîne de calcul |
| **C. Modules vectoriels sur axes fixes** (le mini-orrery de calcul de Freeth, avec Kepler, à l'échelle exacte dans un petit volume, un par planète ; § 2.3) | Exacte au modèle de Kepler près : voir le tableau suivant | Environ 10 pièces par planète (UAK, 2 bras, 1 chaîne de 3 roues, 1 suiveur, 1 renvoi 1:1) | Bonne : axes fixes, sorties sur arbres, aucun bras long | **Recommandé** |
| **D. Trains géocentriques purs** (Ptolémée : déférent et épicycle sans calcul héliocentrique) | Mathématiquement identique à C | Identique | Identique | C'est C, avec un autre vocabulaire. On garde C, qui expose le lien avec l'orrery |

Erreur géocentrique maximale selon le modèle de Kepler utilisé **dans les modules**. Ces chiffres comprennent l'inclinaison et la dérive séculaire sur 2000–2100.

| Modèle | Mercure | Vénus | Mars | Jupiter | Saturne | Uranus | Neptune |
|---|---|---|---|---|---|---|---|
| Moyen mouvement seul (cercle) | 12,0° | 5,3° | 33,2° | 6,9° | 6,7° | 5,7° | 1,0° |
| Goupille et rainure k = 2e + bras constant (à la v1) | 5,4° | 1,2° | 9,0° | 0,83° | 0,53° | 0,27° | 0,05° |
| Équant | 0,85° | 0,21° | 0,71° | 0,07° | 0,08° | 0,05° | 0,02° |
| Équant + épicyclet | 0,34° | 0,20° | 0,24° | 0,03° | 0,06° | 0,02° | 0,02° |
| Kepler exact (résolveur) | 0,26° | 0,20° | 0,21° | 0,02° | 0,06° | 0,02° | 0,02° |
| Équant + épicyclet, mais **distance Terre-Soleil constante** | 0,64° | **1,55°** | **1,53°** | 0,22° | 0,15° | 0,07° | 0,04° |

**Lecture.**
1. Un angle presque juste ne suffit pas, comme le montre la ligne « goupille et rainure + bras constant » : il faut aussi les distances.
2. La distance Terre-Soleil (e = 0,0167) **compte** pour Vénus et Mars, jusqu'à 1,5° quand elle est figée.
3. Le résolveur exact ne gagne sur l'équant + épicyclet qu'en dessous du seuil fixé par l'inclinaison.

### 2.3 Le module vectoriel recommandé

**Principe.** Chaque module est un orrery réduit à deux vecteurs, à l'**échelle exacte** s (mm/ua). La direction de G par rapport à O est la longitude géocentrique :

```
            bras 2 (petit vecteur), longueur A2, angle absolu α2
                    o---------o G  ← goupille du suiveur
                   / roue du bout (angle absolu α2, chaîne 1:1)
  bras 1 (A1, α1) /
     P1 o--------o
        |  ↖ décalage fixe Δ = s·(C_T − C_p)
        O  ← pivot du suiveur rainuré (sortie géocentrique), arbre vers l'avant
```

- **Planètes extérieures** (Mars à Neptune). Le bras 1 est le vecteur héliocentrique de la planète : A1 = a_p·s, α1 = φ_C,p (angle de manivelle de son UAK). Le bras 2 est le vecteur Terre→Soleil : A2 = a_T·s, α2 = φ_C,T + 180°.
- **Planètes intérieures** (Mercure, Vénus). Les rôles s'échangent : le bras 1 est le Soleil (a_T·s, φ_C,T + 180°), le bras 2 est la planète (a_p·s, φ_C,p).
- **L'identité qui fait tout.** La position vraie, au modèle d'équant près, vaut C_p + a_p·u(φ_C,p), où C_p est le centre de l'orbite excentrique (à a_p e_p du Soleil, côté aphélie). Il en va de même pour la Terre. On a donc
  G − P1 = s·(planète − Terre) − s·(C_p − C_T).
  Le **pivot du suiveur se place en O = P1 + s·(C_T − C_p)**, et G − O = s·(planète − Terre) **exactement**.
  Toute l'excentricité des deux orbites tient ainsi dans deux angles de manivelle, déjà fournis par les UAK, et dans la position d'un trou. Aucune plaque ne doit rester parallèle, aucun joint d'Oldham n'est nécessaire.
- **Le bras 2 est mené par une chaîne 1:1** le long du bras 1 : roue sur un tube au pivot P1, pignon fou sur le bras, roue égale au bout. Une telle chaîne conserve l'angle **absolu**, comme le montage de la Terre dans un orrery classique ou de l'épicycle chez Freeth.
- **Mars (EQE)** ajoute un bras minuscule à l'angle absolu 3L − 2ϖ, de 0,087 mm à l'échelle choisie, réalisé par une bague excentrique. Il faut aussi raccourcir le bras 1 de e²/4.
- **Mercure (RK)** a deux bras planète au lieu d'un : (a + b)/2 = 15,83 mm à ϖ + E, et (a − b)/2 = 0,17 mm à ϖ − E. Le pivot est décalé du centre de l'ellipse, à ae.
- **Sortie héliocentrique.** Pour une planète extérieure, le Soleil du module est le point fixe F = P1 − s·C_p. Un second suiveur pivoté en F et passant par l'extrémité du bras 1 donne la **longitude héliocentrique vraie** pour l'orrery. F et O sont à s·|C_T| l'un de l'autre (0,03–0,4 mm). Les deux suiveurs prennent donc leurs arbres de part et d'autre de la platine, l'un vers l'avant, l'autre vers l'arrière.

**Dimensions proposées.** Ces valeurs sont calculées (`modules_results.json`). R est le rayon balayé par G.

| Module | Imbrication | R (mm) | s (mm/ua) | Bras planète | Bras Soleil | Décalage de C_p | Décalage de C_T | \|G\| min–max | Erreur du suiveur pour 0,02 mm |
|---|---|---|---|---|---|---|---|---|---|
| Mercure (RK) | intérieure | 60 | 41,3 | 15,83 + 0,17 | 41,3 | 3,29 | 0,69 | 22,7–60 | 0,05° |
| Vénus (EQ) | intérieure | 70 | 40,3 | 29,2 | 40,3 | 0,20 | 0,67 | 10,7–70 | 0,11° |
| Mars (EQE) | extérieure | 70 | 26,2 | 39,9 (+0,087) | 26,2 | 3,72 | 0,44 | 9,7–70 | 0,12° |
| Jupiter (EQ) | extérieure | 50 | 7,75 | 40,3 | 7,75 | 1,95 | 0,13 | 30,6–50 | 0,04° |
| Saturne (EQ) | extérieure | 50 | 4,53 | 43,2 | 4,53 | 2,33 | 0,08 | 36,4–50 | 0,03° |
| Uranus (EQ) | extérieure | 50 | 2,37 | 45,5 | 2,37 | 2,15 | 0,04 | 41,0–50 | 0,03° |
| Neptune (EQ) | extérieure | 50 | 1,60 | 48,2 | 1,60 | 0,41 | 0,03 | 46,2–50 | 0,025° |

Le bras Soleil de Neptune (1,6 mm) et celui d'Uranus (2,4 mm) ont la taille de l'épicycle de Saturne de la v1 (1,5 mm). La **sensibilité aux tolérances** est maximale quand la planète est proche : la goupille G est alors près de O, et une erreur de position δ donne δ/|G|. Vénus et Mars demandent donc les plus grands modules et la meilleure précision. C'est de la physique, et non un défaut de conception : la planète bouge vite à ce moment-là.

**Bonus pédagogique.** Dans chaque module, la goupille G **dessine l'orbite géocentrique de la planète, boucles de rétrogradation comprises**. Une fenêtre sur un module (Mars, Vénus) montre la boucle telle que l'astronome la voit, ce qu'aucune aiguille ne fait.

### 2.4 Couplage avec l'orrery du couvercle

- **Couplage par les arbres, pas par la visée.** Les UAK (et le résolveur de Mercure) mènent à la fois les modules et l'orrery. Les deux affichages sont donc toujours dans le **même état mécanique**.
- **Sources de l'orrery.** Les longitudes héliocentriques viennent des suiveurs en F (planètes extérieures) ou des suiveurs en O des UAK (Mercure, Vénus, Terre). Chacune monte par un renvoi d'angle 1:1 (pignons coniques ou roue de champ, comme a1/b1) jusqu'à un tube coaxial au Soleil de l'orrery.
- **Forme des orbites, visible.** Chaque bras de l'orrery est **rainuré**. La boule de la planète est sur un coulisseau qui suit une **rainure fixe** du couvercle : un cercle décentré de e·ρ_affiché, ou l'ellipse vraie, avec le Soleil au foyer. L'orbite de Mercure apparaît nettement excentrique : périhélie à 23,8 mm, aphélie à 36,2 mm si a = 30 mm. Les rayons affichés peuvent être comprimés librement, puisque les angles héliocentriques restent exacts.
- **Option « démonstrateur de visée »** (sans rôle de calcul). La partie intérieure de l'orrery est **à l'échelle vraie** : Mercure à 19 mm, Vénus à 36, la Terre à 50, Mars à 76 mm. Pour Mercure, Vénus et Mars, de vrais bras de visée pivotés sur la Terre de l'orrery reproduisent alors exactement les aiguilles avant. C'est le principe du suiveur rendu visible, et le fil articulé de Ferguson en 1756 [precedents.md § 1.6]. Les géantes, comprimées, n'ont pas de bras de visée : l'erreur serait de 20 à 30°.

### 2.5 Budget d'erreur géocentrique par planète (2000–2100, formes figées en 2050)

| Planète | Mécanisme | Modèle | Inclinaison | Séculaire | **Géométrie totale** | Physique hors Kepler [JPL] | Tolérance 0,02 mm |
|---|---|---|---|---|---|---|---|
| Mercure | RK + 2 bras | 0 | 0,25° | 0,02° | **0,26°** | 15″ | 0,05° |
| Vénus | EQ | 0,02° | 0,19° | 0,02° | **0,21°** | 20″ | 0,11° |
| Mars | EQE | 0,06° | 0,07° | 0,18° | **0,24°** | 40″ | 0,12° |
| Jupiter | EQ | 0,05° | 0,01° | 0,02° | **0,07°** | 0,11° | 0,04° |
| Saturne | EQ | 0,05° | 0,03° | 0,04° | **0,08°** | 0,17° | 0,03° |
| Uranus | EQ | 0,04° | 0,003° | 0,02° | **0,05°** | 50″ | 0,03° |
| Neptune | EQ | 0,001° | 0,014° | 0,004° | **0,02°** | 10″ | 0,025° |

Les colonnes ne s'additionnent pas exactement, car les maxima n'arrivent pas au même instant. La colonne « géométrie totale » est un calcul direct.

**À transmettre à l'étude des rapports d'engrenages.** Une erreur de longitude moyenne héliocentrique δ devient, au plus près de la Terre, une erreur géocentrique δ·r/Δ :
- ×3,7 pour Mars (r = 1,38, Δ = 0,37 ua) ;
- ×2,8 pour Vénus ;
- environ ×1 pour Mercure et la Terre (l'erreur sur la Terre se reporte sur toutes les planètes).

L'objectif « < 1° par siècle » sur la longitude moyenne devrait donc être resserré à **≤ 0,1°/siècle pour Mars, Vénus et la Terre**, si l'on veut moins de 0,5° géocentrique.

### 2.6 Hors de portée

- La latitude des planètes (affichage) : non demandée. Elle serait possible par des orbites inclinées, mais n'est pas recommandée.
- L'aberration (20″) et le temps de lumière des planètes (Mercure, environ 0,01°) : négligeables.
- La nutation (17″) : négligeable.

---

## 3. La Lune moderne

### 3.1 Les termes et ce qu'ils coûtent

Référence : la série tronquée d'ELP-2000/82 (Meeus, ch. 47, 60 termes en longitude et 60 en latitude, environ 10″) [M47]. Erreur maximale sur 2000–2100 quand on garde les N premiers termes, sommés exactement :

| Termes gardés | Ajouté | Erreur max | rms |
|---|---|---|---|
| 0 | longitude moyenne seule | 8,03° | 4,57° |
| 1 | anomalie 6,289° sin M′ | 2,56° | 1,04° |
| 2 | + évection 1,274° sin(2D − M′) | 1,39° | 0,52° |
| 3 | + variation 0,658° sin 2D | 0,77° | 0,23° |
| 4 | + 0,214° sin 2M′ (second harmonique de l'anomalie) | 0,63° | 0,18° |
| 5 | + équation annuelle −0,185° sin M | 0,46° | 0,12° |
| 6 | + réduction à l'écliptique −0,114° sin 2F | 0,35° | 0,09° |
| 10 | (+ 2D−2M′, 2D−M−M′, 2D+M′, 2D−M) | 0,18° | 0,05° |
| 13 | | 0,10° | 0,02° |
| 59 | tout | 0,006° | 0,003° |

Périodes des arguments : anomalie 27,555 j, évection 31,812 j, variation 14,765 j, équation annuelle 365,26 j, réduction (2F) 13,606 j.

### 3.2 Un étage par terme, à la manière de la table e

Chaque étage est un **porte-satellite** qui tourne à la vitesse de la phase β du terme. Il porte une goupille et rainure, ou un équant, dont l'entrée est la longitude qui arrive. La table e d'Anticythère fait déjà cela pour l'anomalie [F06].

| Étage | Terme | Porte-satellite (vitesse) | Mécanisme | Dimensions indicatives |
|---|---|---|---|---|
| Anomalie | 6,289° sin M′ + 0,214° sin 2M′ | **périgée** : 0,113028 tr/an (8,85 ans) | **Équant** (UAK) : e = k/2 = 0,05488, sortie par un suiveur au foyer. L'équant donne e² sin 2M′ = 0,173°, contre 0,214° réels. La goupille et rainure de la v1 (k = 2e) donnerait 0,345° | ρ = 20 mm : QC = CO = **1,10 mm**, le même décalage que la v1 (1,1 mm) |
| Évection | 1,274° sin(2D − M′) = 1,274° sin(λ − β_év) avec β_év = 2λ☉ − ϖ | **2λ☉ − ϖ** : 1,887015 tr/an | Goupille et rainure, k = 0,02224 | ρ = 30 mm, décalage de 0,667 mm |
| Variation | 0,658° sin 2D | **Soleil moyen** : 1 tr/an | Étage « doublé » : montée 2:1, goupille et rainure sur 2(λ − λ☉) avec k = 0,02298, redescente 1:2 | ρ = 30 mm, décalage de 0,689 mm |
| Réduction à l'écliptique | −0,114° sin 2F | **nœuds** (aiguille du Dragon) : −0,053726 tr/an | Étage doublé, k = −0,00399 (décalage inversé). Variantes : joint de Hooke plié à 5,145° entre deux différentiels (exact), ou suppression (+0,09°) | ρ = 30 mm, décalage de **0,12 mm** (bague excentrique) |
| Équation annuelle | −0,185° sin M | — | **Différentiel**, qui ajoute −0,0967 × (équation du centre du Soleil). Cette quantité est déjà dans la machine : c'est l'écart entre le Soleil vrai et le Soleil moyen, à la sortie de l'UAK de la Terre | Rapport 15:155 = 0,09677, contre 0,09668 visé (0,1 %) |

### 3.3 Sommer : en cascade ou en parallèle ?

- **En parallèle** (comme les machines à marées de Kelvin [K]). Chaque terme est un sinus pur produit par une coulisse écossaise sur son argument. Une chaîne sur poulies, ou une pile de différentiels, fait la somme, et un différentiel l'ajoute à la longitude moyenne. Il n'y a pas de termes croisés.
- **En cascade** (comme la table e). Chaque étage lit la sortie du précédent, ce qui crée des termes croisés d'ordre k₁k₂.

Résultats sur 2000–2100. Les 120 ordres possibles de la cascade ont été essayés.

| Sommation (anomalie, évection, variation, équation annuelle, réduction) | Erreur max | rms |
|---|---|---|
| Parallèle, sinus purs (6 termes) | 0,347° | 0,091° |
| Cascade, le meilleur ordre : **réduction → équation annuelle → évection → anomalie → variation** | **0,261°** | **0,100°** |
| Cascade, le pire ordre | 0,396° | 0,136° |
| Cascade sans la réduction | 0,354° | 0,129° |
| Cascade sans l'équation annuelle | 0,424° | 0,167° |
| Cascade sans la variation | 0,836° | 0,424° |
| Anomalie seule (v1, goupille et rainure) | 2,52° | 1,03° |

**Recommandation : la cascade, dans l'ordre réduction → équation annuelle → évection → anomalie (équant) → variation.**
- Elle tient ≤ 0,26°, mieux que la somme parallèle. Les termes croisés de la cascade imitent en partie de vrais termes lunaires. Le couplage évection × anomalie produit ainsi +0,07° sin(2D − 2M′), pour +0,059° réels.
- Elle n'utilise que des roues, des goupilles et rainures et un différentiel, ce qui reste dans l'esprit de la machine.
- Placer l'anomalie **avant** la variation sert l'éclipse (§ 5). La goupille de l'unité d'anomalie porte alors la longitude vraie, moins la variation, et la variation **s'annule aux syzygies** (sin 2D = 0).

Ajouter d'autres termes reste possible, à environ 0,05° par terme. Leurs arguments sont des combinaisons entières de D, M, M′ et F : elles se forment par différentiels à partir des quatre arbres déjà présents, **sans nouveau rapport approché**.

### 3.4 Latitude et distance

- **Latitude.** On prend β = asin(sin i · sin F_vrai), avec F_vrai = λ_vrai − Ω, différence entre l'aiguille de la Lune et l'aiguille du Dragon.

| Modèle de latitude | Erreur max (tout le temps) | Aux syzygies |
|---|---|---|
| 5,128° sin F_moyen | 0,81° | 0,52° |
| i = 5,145°, F_vrai | 0,18° | 0,16° |
| i = 5,145°, F_vrai, + 0,173° sin(2D − F) | 0,07° | 0,05° |
| **i_eff = 5,0°, F_vrai** (échelle d'éclipse) | 0,30° | **0,05°** |

  Aux syzygies, sin(2D − F) = −sin F. Le terme 0,173° revient donc à une **inclinaison efficace de 5,0°** : l'orbite est en effet la moins inclinée quand les nœuds pointent vers le Soleil. Une seule coulisse sert les deux usages, avec deux graduations : 5,145° pour l'affichage courant, 5,0° pour l'éclipse.
- **Distance.** C'est le rayon de la goupille de l'unité d'anomalie, au premier ordre en e. Il manque l'évection en distance (±1 %). Le § 5 l'utilise directement.

### 3.5 Hors de portée

- Les termes au-delà de 0,05° : possibles un par un, mais chacun coûte un étage.
- L'accélération séculaire (−0,0016° par siècle sur la longitude moyenne) : négligeable sur un siècle, 0,6° sur 20 siècles.
- ΔT (§ 4.7).

---

## 4. Calendrier et temps

### 4.1 La base de temps : un arbre-jour maître

Le calendrier grégorien compte des **jours**. Pour qu'il soit exact, l'arbre maître doit faire **1 tour par jour solaire moyen**. Les rapports « par an » ne peuvent pas être exacts avec des roues de 10 à 220 dents :
- 146 097 = 3³ × 7 × 773 jours par 400 ans ;
- 1 461 = 3 × 487 jours par 4 ans.

773 et 487 sont premiers et dépassent 220 dents. Les cycles longs se font donc par **comptage** (pas à pas), et non par rapport d'engrenage.

Tous les trains astronomiques partent de l'arbre-jour. La manivelle peut mener l'arbre-jour directement (1 tour = 1 jour, pour les heures, le temps sidéral et la Lune), ou par une seconde entrée plus rapide, par exemple 1 tour pour un mois ou un an. C'est la même chaîne d'engrenages, donc rien ne se désynchronise. Ce point relève de l'architecture générale et reste ouvert.

### 4.2 Le calendrier grégorien (4/100/400)

- **L'anneau des dates** porte 366 positions, du 1ᵉʳ janvier au 31 décembre, 29 février compris. Les mois sont **gravés sur l'anneau**, comme l'anneau égyptien d'Anticythère. Il n'y a donc aucune logique de fin de mois.
- **Avance quotidienne** : une croix de Malte à 6 fentes menée par l'arbre-jour, réversible et à verrouillage positif. Elle fait 1/6 de tour par jour. Il reste à réduire de 1:61 vers l'anneau. Comme 61 est premier, deux réalisations sont possibles :
  - une **vis sans fin à un filet et une roue de 61 dents** ;
  - un anneau à 366 crans tenu par un sautoir. Ce n'est pas un engrenage de transmission : l'exception à la règle des 220 dents est justifiée, comme l'étaient les 365 trous de l'anneau égyptien.
- **Le saut du 29 février.** Les années communes, l'anneau doit avancer de **2 positions** dans la nuit du 28 février au 1ᵉʳ mars. Une seconde croix de Malte, menée au même instant, apporte un pas de plus par un différentiel. Sa goupille est **escamotable** : elle n'est engagée que si la logique dit « année commune » et si l'anneau est au 28 février.
- **Les roues-programmes** sont **continues**, menées par l'anneau, qui fait exactement 1 tour par an civil puisque chaque année compte 366 pas : roue de 4 ans (1:4), roue de 100 ans (1:25 depuis la précédente), roue de 400 ans (1:4). Les rapports possibles sont 15:60, 12:60 × 12:60 et 15:60.
- **La logique.** On saute le 29 février si C4 est vrai, ou si C100 et C400 sont vrais ensemble :
  - C4 : came de la roue de 4 ans, levée pendant les 3 années non multiples de 4. Secteurs de 90°, centrés sur l'instant de lecture (le 28 février), soit une marge de **±45°** ;
  - C100 : came de la roue de 100 ans, levée l'année séculaire seulement. Secteur de 3,6°, marge **±1,8°**, soit ±½ an ;
  - C400 : came de la roue de 400 ans, levée pour les 3 siècles non multiples de 400. Secteurs de 90°, marge **±45°**.
  
  L'ET se réalise par des leviers en série, le OU par deux leviers sur la même goupille.
- **Vérification.** La logique simulée (`calendar_time.py`) est juste pour **chaque année de 1582 à 6000**.
- **Réversibilité.** Tout est fonction de la position : croix de Malte, cames continues, goupille engagée par came. La machine tourne donc à l'envers sans perdre le calendrier, ce que les quantièmes perpétuels de montre ne garantissent pas.
- **Précédents.** Schwilgué à Strasbourg (1843, premier comput grégorien automatique), Olsen (1955), la roue de 400 ans de la Patek Philippe Calibre 89 [S, O, PP89 ; precedents.md § 1.10–1.13].
- **Limite honnête.** L'année grégorienne (365,2425 j) dépasse l'année tropique de 0,031 jour par siècle, soit un jour en 3 200 ans environ. C'est la règle civile, pas une erreur de la machine.

### 4.3 Jour de la semaine

Un rapport 1:7 depuis l'arbre-jour, par exemple 10:70, ou une croix à 7 positions. C'est exact, car 146 097 jours font 20 871 semaines rondes. Il n'y a donc aucune interaction avec la logique grégorienne.

### 4.4 Temps sidéral

On a l'identité TSMG = heure solaire moyenne + longitude moyenne du Soleil (tropique) + 12 h. Un **différentiel** somme donc l'arbre-jour et l'arbre du Soleil moyen, comme le faisait Schwilgué.
- Le rapport obtenu, 1 + 1/365,24219 = 1,0027379093, s'écarte de **0,06 s par siècle** de la vitesse IAU (1,00273790935). L'identité est donc exacte.
- L'erreur réelle est celle du rapport de l'année : une erreur relative δ donne δ × 100 tours par siècle, soit 0,86 s par siècle pour δ = 10⁻⁷.
- Si les trains tournent dans le repère fixe (§ 4.6), il faut ajouter la précession. Le moyen le plus simple est de graver la couronne 24 h sidérale sur une bague menée par le même train lent que l'anneau de précession. Sans cette correction, l'erreur serait de 5,6 min par siècle.

### 4.5 Équation du temps

On a EdT = L☉ moyen − α☉ vrai. Les deux causes se mécanisent séparément :
1. **L'excentricité** (±7,66 min). Elle est déjà calculée, puisque l'UAK de la Terre donne le Soleil vrai λ.
2. **La réduction à l'équateur** (±9,87 min). On a tan α = cos ε · tan λ. C'est **exactement** la loi d'un **joint de Hooke** dont les deux arbres font l'angle ε = 23,44°, calé à 90° près pour avoir la forme cos ε plutôt que 1/cos ε. Hooke lui-même a relevé (1667–1676) que son joint reproduit la marche de l'ombre d'un cadran solaire, et en a proposé un « cadran mécanique » [H].

Il reste un différentiel, L moyen − α, puis un agrandissement ×10 pour un cadran lisible. La sortie α donne aussi l'ascension droite du Soleil.

| Réalisation (référence : Meeus, Soleil de la date, ε de la date) | Erreur max 2000–2100 |
|---|---|
| **Hooke + UAK de la Terre figée en 2050 + entrée de précession** (2 différentiels) | **3,1 s** |
| La même chose, sans entrée de précession | 32 s |
| Came classique taillée pour 2050, tournant avec le Soleil moyen | 8,0 s |

L'EdT de référence va de −14,2 à +16,5 min. Sur un siècle, la came suffit. Le joint de Hooke se justifie par la cohérence, puisque l'EdT vient du même Soleil vrai que l'aiguille, et par la durée : la came dérive avec le périhélie, d'environ 2 min en 1 000 ans.

### 4.6 Précession et choix du repère

**Recommandation : tous les trains tournent dans le repère fixe J2000**, celui des étoiles et de la caisse. Les **pivots excentriques de Kepler sont fixés à la caisse**.

Dans le repère tropique, les périhélies avancent de 1,4° par siècle, presque entièrement à cause de la précession. Une goupille figée y coûterait 2e × 1,4° : **0,57° par siècle pour Mercure**, contre 0,02° dans le repère fixe (§ 1.6).

- **L'anneau du zodiaque tropique** (avant) tourne de −1 tour en **25 771,6 années tropiques** par rapport à la caisse (5 028,796″ par siècle, IAU 2006 [P03]). La couronne des constellations reste fixe. On lit les aiguilles sur l'un ou l'autre.
- **Le train de précession**, depuis l'arbre de l'année : 4 couples 23·14·14·12 / 212·208·208·152 (erreur 2,5·10⁻⁹). Autre choix : une vis sans fin 1:100 suivie de 3 couples 179·10·10 / 216·189·113 (erreur 3·10⁻⁹). Une erreur de 0,1 % ne coûte que 0,0014° par siècle. Olsen s'en est tenu à 25 753 ans, Schwilgué à 25 806 ans [precedents.md].
- **Qui a besoin de la précession** : l'EdT (§ 4.5), le temps sidéral (§ 4.4) et la lecture tropique. Les éclipses n'en ont pas besoin, car seules les différences Soleil–Lune–nœud comptent.

### 4.7 Hors de portée

- **ΔT** (TT − UT, environ +69 s en 2026, avenir imprévisible) : l'arbre-jour est un temps uniforme. Les heures affichées (éclipses en particulier) sont en TT, à environ 1 min près. On peut prévoir un réglage manuel.
- La nutation (±17″ et ±1,1 s sur le temps sidéral) : négligeable.
- Le comput pascal n'était pas demandé. Strasbourg et Olsen montrent qu'il est faisable (precedents.md).

---

## 5. Éclipses

### 5.1 La géométrie en une quantité, γ

γ est la distance, en rayons terrestres, entre l'axe de l'ombre et le centre de la Terre (éclipse de Soleil), ou entre la Lune et l'axe de l'ombre de la Terre (éclipse de Lune). On a γ ≈ sin β · cos 5,3° / sin π☾, où π☾ est la parallaxe de la Lune, inversement proportionnelle à sa distance r. **La magnitude est linéaire en |γ|** (Meeus, ch. 54), avec u ≈ 0,0059 le rayon du cône d'ombre :
- éclipse de Lune, magnitude d'ombre = (1,0128 − u − |γ|)/0,5450 ;
- éclipse de Lune, magnitude de pénombre = (1,5573 + u − |γ|)/0,5450 ;
- éclipse de Soleil partielle, magnitude = (1,5433 + u − |γ|)/(0,5461 + 2u).

Limites (apogée → périgée) :

| Événement | \|γ\| < | β limite | Distance au nœud F |
|---|---|---|---|
| Soleil, éclipse quelque part | 1,549 | 1,40° → 1,59° | 16,3° → 18,6° |
| Soleil, éclipse centrale | 0,997 | 0,90° → 1,03° | 10,4° → 11,8° |
| Lune, pénombre | 1,563 | 1,41° → 1,61° | 16,4° → 18,8° |
| Lune, ombre partielle | 1,007 | 0,91° → 1,04° | 10,5° → 12,0° |
| Lune, totale | 0,462 | 0,42° → 0,48° | 4,8° → 5,5° |

### 5.2 Le prédicteur mécanique

Une **coulisse écossaise sur le porte-nœuds** (l'aiguille du Dragon), dont la manivelle est **la goupille même de l'unité d'anomalie lunaire**. Cette goupille est à la distance r et à la longitude vraie (moins la variation, nulle aux syzygies). Le déplacement de la coulisse le long de la ligne des nœuds vaut r·sin(λ − Ω), qui est **proportionnel à γ**. La coulisse calcule donc le produit « distance × sinus » sans multiplicateur.

L'importance de la distance, chiffrée (`eclipses.py`) :

| Coulisse | Erreur sur γ (max) | Magnitude d'ombre (rms / max) | Éclipses détectées |
|---|---|---|---|
| r·sin F (distance comprise) | **0,029–0,035** | **0,041 / 0,093** | **449 / 452** |
| sin F, distance constante | 0,09–0,13 | 0,098 / 0,26 | 443 / 452 |

**L'affichage** : un index sur la coulisse lit une **échelle gravée en γ, doublée d'échelles de magnitude** (Lune ombre, Lune pénombre, Soleil), qui sont linéaires. On la lit au moment où les aiguilles du Soleil et de la Lune s'alignent (nouvelle Lune) ou s'opposent (pleine Lune). Une éclipse a lieu si l'index est dans la zone gravée.

**Totale ou annulaire.** On compare le diamètre apparent de la Lune, donné par le rayon de l'unité d'anomalie, à celui du Soleil, donné par le rayon de l'UAK de la Terre. Un petit index à deux secteurs, « Lune plus grosse » ou « plus petite », suffit. Le test donne **147 éclipses centrales sur 147 bien classées** (les hybrides comptent comme justes), avec une magnitude centrale à 0,011 rms près (0,021 au maximum).

### 5.3 Validation contre le canon NASA (2001–2100)

On fait tourner la machine simulée : Lune en cascade (§ 3.3), latitude avec i_eff = 5,0°, Soleil donné par l'UAK de la Terre, distances données par les unités. Les syzygies sont détectées **sur ses propres aiguilles**. On compare aux 224 éclipses de Soleil et 228 éclipses de Lune du *Five Millennium Canon* [NASA].

| Grandeur | Soleil | Lune |
|---|---|---|
| Éclipses détectées | 223 / 224, 1 fausse alarme | 226 / 228, 1 fausse alarme |
| Erreurs de détection | toutes à \|γ\| = 1,54–1,56, c'est-à-dire des éclipses rasantes d'un millième de magnitude | toutes à \|γ\| = 1,55–1,57, des pénombrales rasantes |
| Heure du maximum | ±0,53 h max (0,23 h rms) | ±0,51 h max (0,22 h rms) |
| γ | ±0,029 (0,013 rms) | ±0,035 (0,014 rms) |
| Magnitude | centrale ±0,021 | ombre ±0,093 (0,041 rms) |

### 5.4 Saros et Exeligmos : gardés, avec un sens nouveau

- 223 lunaisons durent 6 585,321 j, 242 mois draconitiques 6 585,357 j, 239 mois anomalistiques 6 585,537 j.
- À chaque Saros, le nœud se décale de **0,48°** et l'anomalie de 2,8°. Une série dure donc de 1 200 à 1 500 ans. Des glyphes gravés pour une époque (par exemple 2026–2044) restent justes pendant quelques cycles seulement. La v2, qui calcule les éclipses par la géométrie, n'en dépend plus.
- Le cadran du Saros devient un **compteur de retour** : « cette éclipse revient dans 18 ans, 10 ou 11 jours et 8 h, **116° plus à l'ouest** ». L'aiguille de l'Exeligmos corrige le décalage, car 3 Saros font 19 755,96 j, soit −0,036 j et environ 13° de longitude.
- **Rapport.** Le Saros vaut 1/223 de l'arbre synodique. Comme 223 est premier, le rapport exact demande une **roue de 223 dents**, l'exception même de b1 dans la machine antique, que l'on peut garder en hommage. Sans cette exception : 12·12 / 197·163 (3·10⁻⁵, soit 0,04 case par siècle) ou 155·29·10 / 219·219·209 (10⁻⁷).

### 5.5 Où ? Le globe-ombre

**Le mécanisme.**
- La Terre de l'orrery est montée en **tellurion** : axe incliné de 23,44° et maintenu parallèle par une chaîne 1:1, rotation sidérale par une chaîne venue de l'arbre du temps sidéral.
- Une **aiguille d'ombre** horizontale, portée par le bras de la Terre, vise le globe depuis la direction du Soleil.
- L'aiguille est décalée verticalement, perpendiculairement à l'écliptique, de γ·R_globe. Une crémaillère et un pignon reportent la course de la coulisse d'éclipse par un tube et une chaîne d'environ 6 pièces.

Au moment de la syzygie, **le point où l'aiguille touche le globe est le lieu du maximum de l'éclipse**. Le tellurion fait de lui-même la projection, saisons et équation du temps comprises. Une seconde aiguille côté nuit, à la même hauteur, montre le point zénithal d'une éclipse de Lune : l'éclipse est visible dans un rayon d'environ 90° autour.

**La validation.** Elle porte sur la projection exacte que réalise le globe, appliquée aux grandeurs de la machine, et non sur un raccourci.

| | Latitude | Longitude | Hémisphère juste |
|---|---|---|---|
| Soleil, 122 éclipses centrales (\|γ\| < 0,9) | 1,4° rms (5,2° max) | 4,1° rms (20° max) | 99 % |
| Lune, point zénithal (228) | 0,29° rms | 3,4° rms (7,8° max) | — |
| *Raccourci « latitude = δ☉ + asin γ » sans globe* | 2,7° rms (15° max) | — | — |

**Ce qu'il faut dire honnêtement :**
- l'erreur de longitude vient surtout de l'heure, ±0,5 h, soit ±7,5° ;
- ΔT est ignoré (environ 0,3°) ;
- **la bande de centralité** (largeur, tracé, durée) **n'est pas montrée**. Seul le point du maximum l'est ;
- pour |γ| > 1, l'aiguille passe à côté du globe : l'éclipse est partielle, près du pôle situé de ce côté ;
- le globe donne un « où, à peu près » : environ 500 km rms, jusqu'à 2 000 km dans le pire cas. Ce n'est pas une carte.

---

## 6. Les lunes galiléennes

### 6.1 Données et résonance

Moyens mouvements (théorie E5 de Lieske, via Meeus ch. 44 [M44]), en °/jour : Io 203,48895579, Europe 101,374724735, Ganymède 50,317609207, Callisto 21,571071177. Les périodes sidérales sont de 1,769138, 3,551181, 7,154553 et 16,689018 j.

La relation de Laplace, n_Io − 3n_Eu + 2n_Ga = −1·10⁻⁹ °/j, est donc exacte. Elle se lit comme **deux conjonctions qui tournent ensemble** :

n_Io − 2n_Eu = n_Eu − 2n_Ga = **ν = 0,7395063 °/j**,

soit une période de **486,81 j** pour la ligne des conjonctions Io–Europe et Europe–Ganymède. Le rapport « 1:2:4 » n'est pas strict : 1:2:4 exact dériverait de plus de 100° par an [precedents.md § 2.7].

### 6.2 La boîte de Laplace

On construit les lunes à partir de **Ganymède et de ν**, en n'utilisant que des doublements :

```
arbre-jour ─┬─ train G (3 couples) ─────────── Ganymède ─┬──────────────── λ_Ga
            │                                           ×2
            ├─ train ν (3 couples) ── ν ──────────────► (+) ─ Europe ─┬─ λ_Eu
            │                          └──────────────────────────► ×2 (+) ─ λ_Io
            └─ train C (3 couples) ─────────── Callisto ────────────────────── λ_Ca
```

- Io = 2·Europe + ν et Europe = 2·Ganymède + ν, par deux doubleurs 2:1 et deux différentiels. La relation de Laplace est **exacte par construction**, quels que soient les rapports choisis.
- L'**arbre ν** devient une aiguille, comme celle du Dragon : la « ligne des conjonctions ». C'est la façon la plus parlante de montrer la résonance.
- Trains depuis l'arbre-jour (1 tour par jour), avec des roues de 10 à 220 dents :

| Arbre | 3 couples | Erreur relative | Dérive par siècle |
|---|---|---|---|
| Ganymède (0,13977114 tr/j) | 167·58·14 / 161·131·46 | 1,3·10⁻¹⁰ | −0,0002° |
| ν (0,00205418 tr/j) | 54·17·11 / 185·182·146 | 1,2·10⁻⁸ | (sur Io : −0,0001°) |
| Callisto (0,05991964 tr/j) | 137·111·10 / 167·167·91 | 5,7·10⁻¹⁰ | +0,0004° |
| *Variante à 2 couples* : Ganymède 157·34 / 211·181, Callisto 117·13 / 167·152 | | 10⁻⁷ | Io +0,72°, Callisto −0,10° |

### 6.3 Affichages

- **Le cadran jovien** (recommandé), sur axe fixe en façade ou sur le côté : Jupiter au centre et quatre bras sur des tubes coaxiaux menés directement par la boîte de Laplace. Les mouvements sont rapides : Io fait 206 tours par an. Ils se voient bien en mode « heure ».
- **La lunette.** Une barre, sur le même axe, est tournée à l'angle λ_Jupiter,géo + 90°. Cet angle vient du **module géocentrique de Jupiter** (§ 2.3) par un renvoi 1:1. Chaque bras de lune porte une goupille engagée dans une **coulisse écossaise** guidée par la barre. Les coulisseaux s'y placent à x_i = a_i·sin(λ_i − λ_J,géo). C'est **ce que l'on voit à la jumelle** : les satellites à l'est ou à l'ouest de Jupiter, à l'échelle de 5,9, 9,4, 15,0 et 26,4 rayons joviens. Un coulisseau qui passe derrière ou devant le disque signale une occultation ou un passage. Le signe de cos(λ_i − λ_J,géo) se lit sur le bras.
- **Sur l'orrery (option).** Une copie du système sur la Jupiter du couvercle demande de faire monter les quatre angles absolus par des chaînes 1:1 le long du bras de Jupiter (ou trois angles, avec une seconde boîte de Laplace au bout du bras). C'est faisable, mais lourd, et on peut le réserver à l'esthétique.

### 6.4 Précision : ce que la cinématique ne fait pas

- **Les inégalités des lunes elles-mêmes** (E5) : Io ±0,47° sin 2(l₁ − l₂), Europe ±1,06° sin 2(l₂ − l₃), Ganymède ±0,16° et ±0,09° (excentricités), Callisto ±0,84° (excentricité). Chacune serait une goupille et rainure de plus. Ce n'est pas recommandé : l'effet sur un coulisseau est d'au plus 0,4 rayon jovien, pour Callisto.
- **Le temps de lumière** (l'effet Rømer, 1676). La distance Terre–Jupiter varie de 3,95 à 6,45 ua, soit 20,8 min. En retard apparent, cela donne ±1,47° pour Io, ±0,73° pour Europe, ±0,36° pour Ganymède et ±0,16° pour Callisto.
  C'est mécanisable : on ajoute à l'arbre ν et à Callisto une correction proportionnelle à la distance Terre–Jupiter, que le **suiveur du module de Jupiter** fournit déjà (la position radiale de G). Ce serait un clin d'œil à Rømer, qui a tiré de ce retard la première mesure de la vitesse de la lumière. C'est optionnel.
- **La libration de Laplace** (quelques centièmes de degré [L18]) : négligeable.

---

## 7. Hors de portée : synthèse honnête

| Effet | Ordre de grandeur | Statut |
|---|---|---|
| Inclinaison de Mercure et de Vénus en longitude géocentrique | 0,25° / 0,19° | Accepté (joint de Hooke ou orbite inclinée possibles, mais pas dans un module plan) |
| Dérive séculaire de Mars | 0,33° à ±100 ans, 0,70° à ±200 ans | Réglage séculaire à la main (bague graduée), ou plateau d'apsides tournant |
| Grande inégalité Jupiter–Saturne | ±0,36° / ±0,88° (939 ans) | Absorbée par les éléments sur ±1 siècle. Option : roue de 939 ans et deux différentiels |
| Uranus–Neptune | ±0,99° / ±0,69° (4 693 ans) | Même remarque |
| Termes lunaires < 0,05° | Total résiduel 0,26° max | Un étage par terme si l'on veut descendre plus bas |
| Bande de centralité des éclipses | — | Non mécanisable de façon réaliste. Seul le point du maximum est montré |
| ΔT | ~1 min (2026), imprévisible | Réglage manuel |
| Nutation et aberration | 17″ / 20″ | Négligées |
| Tolérances de fabrication | δ/\|G\| : 0,03–0,12° pour 0,02 mm | Demandent un usinage moderne (CNC, électroérosion à fil) pour les bagues excentriques de 0,09 à 0,7 mm |
| Bras minuscules : épicyclet de Mars 0,087 mm, ellipse de Mercure 0,17 mm, réduction lunaire 0,12 mm | — | Ce sont les seules cotes sous 0,2 mm. On peut agrandir : avec des modules de R = 100 mm, l'épicyclet de Mars passe à 0,12 mm et l'ellipse de Mercure à 0,29 mm. Avec ρ = 50 mm, la réduction lunaire passe à 0,2 mm |

---

## 8. À prouver en Lean 4 (identités exactes, à la manière de `PinSlot.lean`)

1. **Module vectoriel** : G − O = s·(planète − Terre) avec O = P1 + s(C_T − C_p), pour les deux imbrications (identité vectorielle).
2. **Équant = une goupille et rainure menée par la rainure.** La manivelle est strictement monotone, sa vitesse moyenne est celle de l'entrée, et l'écart d'angle est borné. C'est l'analogue de `isGreatest_abs_lag`.
3. **Résolveur de Kepler.** Pour 0 ≤ e < 1, l'application E ↦ E − e sin E est un difféomorphisme strictement croissant de ℝ (dérivée ≥ 1 − e > 0). La boucle fermée a donc une solution unique et continue.
4. **Ellipse à deux bras** : ((a+b)/2)·u(E) + ((a−b)/2)·u(−E) = (a cos E, b sin E).
5. **Joint de Hooke** : la loi de sortie tan θ₂ = cos β · tan θ₁, et EdT = L − α.
6. **Grégorien** : la logique C4 ∨ (C100 ∧ C400), avec les cames centrées, égale la règle bissextile pour toute année. On peut le faire par `decide` sur un cycle de 400 ans plus la périodicité.
7. **Laplace** : avec Eu = 2Ga + ν et Io = 2Eu + ν, on a Io − 3Eu + 2Ga = 0 exactement, quels que soient les rapports.
8. **Temps sidéral** : TSMG = heure + Soleil moyen + précession (identité de vitesses).
9. **Fractions** : précession 54096/1394139136, trains galiléens, 15/155 pour l'équation annuelle, 1/223 ou ses approximations, avec leurs erreurs relatives bornées.

---

## 9. Reproduire les calculs

Python de Blender : `BPY=/Applications/Blender.app/Contents/Resources/5.2/python/bin/python3.13`, puis `cd ~/antikythera/v2/research/calc`.

| Script | Contenu | Résultats |
|---|---|---|
| `kepler_models.py` | Goupille et rainure, équant, foyer vide, Kepler exact ; harmoniques de l'erreur | console |
| `geocentric.py` | Budget géocentrique par planète (JPL table 1, 3D), compression, distances, tolérances | `geocentric_results.json` |
| `secular_longterm.py` | Formes figées sur ±50 à ±500 ans, grande inégalité (JPL tables 2a et 2b) | `secular_results.json` |
| `modules_and_eclipse_limits.py` | Dimensions des modules, limites d'éclipse, nombres du Saros | `modules_results.json` |
| `moon.py` | Meeus ch. 47 complet, termes cumulés, cascades, latitude | `moon_results.json` |
| `eclipses.py` | Machine simulée contre le canon NASA 2001–2100 (`data/*.csv`) | `eclipses_results.json` |
| `calendar_time.py` | Cames grégoriennes 1582–6000, temps sidéral, EdT (Hooke ou came), précession, trains galiléens | `calendar_time_results.json` |
| `gear_search.py` | Recherche exhaustive de trains de 2 à 4 couples (10–220 dents) | — |

Chaque script tourne en 10 s au plus : `$BPY geocentric.py`, `$BPY moon.py`, etc. Il faut lancer `geocentric.py` avant `modules_and_eclipse_limits.py`, qui lit son JSON.

---

## 10. Sources

- [F06] Freeth et al. 2006, *Decoding the ancient Greek astronomical calculator known as the Antikythera Mechanism*, Nature 444 : la goupille et rainure lunaire. https://www.nature.com/articles/nature05357
- [F21] Freeth et al. 2021, *A Model of the Cosmos in the ancient Greek Antikythera Mechanism*, Sci. Rep. 11:5821 : trains planétaires, suiveurs, épicycles. https://pmc.ncbi.nlm.nih.gov/articles/PMC7955085/
- [JPL] Standish & Williams, *Keplerian Elements for Approximate Positions of the Major Planets* (tables 1, 2a, 2b ; erreurs nominales). https://ssd.jpl.nasa.gov/planets/approx_pos.html
- [M47] Meeus, *Astronomical Algorithms*, ch. 47 (position de la Lune), tables transcrites dans soniakeys/meeus (MIT). https://github.com/soniakeys/meeus/blob/master/v3/moonposition/moonposition.go
- [M44] Meeus, ch. 44 (satellites de Jupiter, théorie E5 de Lieske). https://github.com/soniakeys/meeus/blob/master/v3/jupitermoons/jupitermoons.go
- [NASA] Espenak & Meeus, *Five Millennium Canon* : catalogues 2001–2100 des éclipses de Soleil et de Lune (γ, magnitude, lieu du maximum). https://eclipse.gsfc.nasa.gov/SEcat5/SE2001-2100.html et https://eclipse.gsfc.nasa.gov/LEcat5/LE2001-2100.html
- [H] Hooke et le joint universel appliqué aux cadrans solaires et à l'horloge-cadran (Mills, Notes Rec. R. Soc.). https://www.researchgate.net/publication/250902707_Robert_Hooke's_'universal_joint'_and_its_application_to_sundials_and_the_sundial-clock ; https://en.wikipedia.org/wiki/Universal_joint
- [K] Machines à prédire les marées de Kelvin (coulisses écossaises et sommation par fil et poulies). https://en.wikipedia.org/wiki/Tide-predicting_machine ; https://tidesandcurrents.noaa.gov/predmach.html
- [OP1140] US Navy, *Basic Fire Control Mechanisms* (1944) : différentiels, cames, résolveurs, boucles de calcul. https://maritime.org/doc/op1140/index.php
- [W53] Seth Ward, hypothèse du foyer vide (1653), d'après Boulliau. https://words.fromoldbooks.org/Hutton-Mathematical-and-Philosophical-Dictionary/w/ward-dr-seth.html
- [AN] Kepler, *Astronomia nova* (1609), l'écart de 8′ de l'hypothèse vicariante. https://en.wikipedia.org/wiki/Astronomia_nova
- [S] L'horloge astronomique de Strasbourg (Schwilgué, 1838–1843 ; comput grégorien automatique). https://en.wikipedia.org/wiki/Strasbourg_astronomical_clock ; https://en.wikipedia.org/wiki/Jean-Baptiste_Schwilgu%C3%A9
- [O] L'horloge universelle de Jens Olsen (1955 ; le rouage le plus lent fait 1 tour en 25 753 ans). https://en.wikipedia.org/wiki/Jens_Olsen%27s_World_Clock
- [PP89] Patek Philippe Calibre 89 (quantième séculaire, roue de 400 ans). https://watchesbysjx.com/2026/06/in-depth-patek-philippe-calibre-89.html
- [L18] Lari 2018, *Element history of the Laplace resonance*, A&A 617, A35. https://www.aanda.org/articles/aa/full_html/2018/09/aa32856-18/aa32856-18.html
- [P03] Capitaine, Wallace & Chapront 2003 (précession IAU 2006 : 5 028,796195″ par siècle) ; résumé : https://en.wikipedia.org/wiki/Axial_precession
- Joint d'Oldham et accouplement de Schmidt (transmission entre arbres parallèles décalés, envisagée puis rendue inutile par le décalage du pivot du suiveur). https://en.wikipedia.org/wiki/Schmidt_coupling
- Documents parallèles de ce dossier : `research/constants.md` (valeurs) et `research/precedents.md` (machines historiques).
