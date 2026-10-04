# Anticythère 2.0 — Les précédents : qui a déjà fait quoi, et ce qu'on en retient

*Recherche documentaire pour `~/antikythera/v2/`. Pages consultées le 3 octobre 2026.*
*Fichier compagnon : `precedents_checks.py`. Il recalcule en fractions exactes les rapports et les chiffres repris ici.*

---

## Comment lire ce document

Chaque fait porte une étiquette de fiabilité :

| Étiquette | Sens |
|---|---|
| **[S]** | Lu dans la source citée [P#]. |
| **[R]** | Rapporté par une source secondaire ou commerciale (presse horlogère, fabricant, maison de vente, résumé de moteur de recherche) et non recoupé. Ne pas l'utiliser comme donnée d'ingénierie sans vérification. |
| **[C#]** | Recalculé ici par `precedents_checks.py` (bloc `[C#]` de sa sortie). |
| **[Lacune]** | Information cherchée mais introuvable en ligne. La piste pour la trouver est notée. |

Les sources [P1]…[P59] sont listées à la fin, avec leur URL.

Le cahier des charges d'Anticythère 2.0 sert de grille de lecture : une seule manivelle, des roues en bronze de 10 à 220 dents, un module d'au moins 0,4 mm, un cadran avant géocentrique et un planétaire héliocentrique couplés, huit planètes avec l'équation du centre, une Lune moderne, le calendrier grégorien, le temps sidéral, l'équation du temps, la précession, les éclipses et les lunes galiléennes.

---

## 0. L'essentiel en une page

| Machine | Date | Ce qui nous concerne | Technique clé | Leçon principale pour v2 |
|---|---|---|---|---|
| Wallingford (St Albans) | v. 1327–1336 | Soleil vrai, Lune, éclipses, temps sidéral | Roue irrégulière de 331 dents (Soleil) | L'inégalité peut se loger dans la roue elle-même, mais elle devient alors invérifiable par fractions |
| Dondi, *Astrarium* | 1348–1364 | 7 cadrans planétaires (géocentriques), fêtes mobiles | Roues ovales à dents irrégulières (Mercure, Lune) | Le pionnier de l'« équation » mécanique. Pas d'années bissextiles |
| Rømer, éclipsarium | 1678–1681 | Éclipses sur 200 ans, à la clé | Deux cames excentriques contrarotatives | Une éclipse se calcule en analogique avec très peu de pièces |
| Huygens, planétaire | 1682 | 6 planètes, orbites excentriques | **Fractions continues** (Saturne 206/7) | La méthode des rapports. Un seul étage donne 1 à 19°/siècle, c'est trop pour nous |
| Graham/Rowley, Wright | v. 1710–1733 | Planétaire **à manivelle**, 4 lunes de Jupiter | Trains épicycloïdaux d'orrery | Le format « orrery sur la boîte » existe depuis 1733 |
| Ferguson, orrery | 1756 | **Fil articulé Terre → planète** (géocentrique), limites d'écliptique, hémisphère | Accessoire amovible | **C'est le précédent direct de notre bras de visée** |
| Hahn, *Weltmaschine* | 1768–1769 | Systèmes **ptolémaïque et copernicien dans la même machine**, lunes de Jupiter | Rapports calculés avec une machine à calculer | Le double affichage existe. Le couplage reste inconnu [Lacune] |
| Eisinga, Franeker | 1774–1781 | Planétaire en temps réel, au plafond | Cerceaux de bois, clous forgés comme dents | Uranus n'a pas trouvé de place : l'échelle linéaire ne marche pas |
| Janvier | 1768–1812 | Sphères mouvantes, excentricités, précession | Traité de 1812 sur les rapports | Peu de chiffres accessibles [Lacune] |
| **Schwilgué, Strasbourg** | 1838–1842 | **Comput grégorien, 5 inégalités lunaires, éclipses, précession, temps sidéral exact** | **Différentiel pour les grands nombres premiers, cames empilées sommant les inégalités** | **Le précédent le plus proche de notre cahier des charges** |
| **Jens Olsen, Copenhague** | 1928–1955 | Calendrier grégorien, Pâques, éclipses, 8 planètes, précession 25 753 ans | « Equation Works » et différentiels | Séparer l'année anomalistique de l'année tropique. Orbites circulaires seulement |
| Sørnes n° 1–4 | 1937–1966 | Précession, 9 planètes, éclipses avec **tranche de Terre tournante** | Train de 1:9 500 000 | Un indicateur du « où » de l'éclipse |
| Patek 89, Andersen, Muller | 1989–1996 | Calendrier séculaire 4/100/400, Pâques, sidéral | Came de 100 ans plus satellite de 400 ans | La règle des 400 ans tient en quelques pièces. Pâques en montre n'est qu'une mémoire de 30 ans |
| Oechslin / Ulysse Nardin | 1985–1992 | Astrolabe, planétaire, tellurium en montre | Roues plutôt que leviers | Compacité et nœuds (« aiguille du dragon ») |
| Van der Klaauw | 1999 ; 2024 | **8 planètes** dont Uranus et Neptune, trajectoires excentriques, 3 338 dents | Module planétaire de montre | Huit planètes, c'est faisable en très petit |
| Hublot 2033-CH01 | 2011 | Recréation moderne d'Anticythère | Mouvement autonome | Le précédent « hommage » |
| Long Now, orrery | 1999– | Planètes calculées en binaire mécanique | Additionneur série à goupilles | L'alternative numérique aux grands rapports |

**Dix leçons à retenir** (détaillées au §2) :

1. **Méthode des rapports.** Huygens a introduit les fractions continues (1682). Schwilgué y a ajouté deux techniques : n'utiliser que de petits nombres premiers (médiantes de Farey) et, surtout, **contourner un grand nombre premier par un train épicycloïdal** qui ajoute une petite correction : 1/R = 1 + 450/(13·47·269), un rapport exact [C1].
2. **Kepler mécanisé.** Presque tous les planétaires (Eisinga, Strasbourg, Olsen, Ulysse Nardin) tournent **en cercles uniformes**. Dondi (roues ovales), Huygens (orbites excentriques), Anticythère (goupille et rainure) et Van der Klaauw (2024, trajectoires excentriques) sont les exceptions.
3. **Couplage géocentrique.** Ferguson (1756) posait un **fil articulé** fixé sur la tige de la Terre et passant dans une fourche posée sur Vénus ou Mercure. Le fil montrait les rétrogradations « vues de la Terre ». Personne, dans nos sources, ne **transmet** cet angle à un cadran.
4. Pour que ce couplage soit juste, **le rayon du maneton planétaire doit varier** (orbite excentrique), pas seulement son angle. Avec un rayon constant, l'erreur géocentrique atteint 6,8° pour Mars et 5,5° pour Mercure. Avec un modèle excentrique-équant, elle tombe à 0,57° et 0,66° [C14].
5. **Lune moderne.** Schwilgué l'a déjà fait en 1842 : anomalie, évection, variation, équation annuelle et nœuds. Les rapports reproduisent les périodes à moins d'une seconde près [C3]. Les amplitudes sont **additionnées par des cylindres-cames empilés**, puis injectées dans le mouvement moyen par un différentiel. Olsen y ajoute les oscillations de l'apside et des nœuds.
6. **Équation du temps.** Schwilgué comme Olsen la décomposent en **équation du centre** (année anomalistique) et **réduction à l'équateur** (année tropique). Une seule « came-haricot » dériverait au fil des siècles, parce que le périhélie se déplace.
7. **Calendrier 4/100/400.** Il tient en peu de pièces : came séculaire de 100 ans plus satellite de 400 ans (Patek 89), ou roue séculaire de 50 dents avancée d'une dent tous les 8 ans (Andersen) [C12]. Le **vrai comput de Pâques** perpétuel n'existe qu'à Strasbourg et chez Olsen. En montre, Pâques n'est qu'une **mémoire de 30 ans**.
8. **Précession.** La valeur de la constante compte peu : 25 753, 25 800 ou 25 806 ans au lieu de 25 772 donnent moins de 0,002°/siècle d'erreur [C9]. Le problème est mécanique : il faut un **rapport d'environ 1:9,4 millions** depuis un axe journalier. La dernière roue de Strasbourg (128 dents) a avancé de moins d'une dent depuis 1842 [C4].
9. **Éclipses.** Le meilleur précédent de la *magnitude* est Strasbourg : l'aiguille lunaire s'allonge ou se raccourcit au gré d'une came nodale, et la superposition des disques montre partielle ou totale. Elle a été vérifiée sur l'éclipse du 15 février 1961. Pour l'*hémisphère*, Ferguson donne une règle (signe de la latitude lunaire) et Sørnes une tranche de Terre tournant en un jour sidéral.
10. **Lunes galiléennes.** Il ne faut **pas** les engrener en 1:2:4 exact. Les périodes réelles sont dans les rapports 2,0073 et 2,0147, et un engrenage 1:2:4 dériverait de 135°/an et 203°/an [C10]. La relation exacte est celle de Laplace, n_Io − 3 n_Europe + 2 n_Ganymède = 0. Un seul différentiel l'impose.

---

## 1. Fiches par machine (ordre chronologique)

Chaque fiche suit le même plan : **ce qu'elle montre**, **comment**, **chiffres publiés**, **limites et échecs**, **leçon pour v2**.

### 1.1 Richard de Wallingford, horloge de St Albans (v. 1327–1336). Bonus

- **Montre** : Soleil à vitesse variable, Lune avec ses phases, étoiles, éclipses de Lune [S P5].
- **Comment** : une roue de 331 dents est « façonnée de manière à entraîner l'image du Soleil à sa vitesse équatoriale vraie », ce qui compense donc l'équation du temps. Ce n'est pas un vrai ovale, mais une roue irrégulière [S P5]. Pour l'éclipse, un disque anti-solaire noir sous lequel la Lune passe quand elle est pleine et proche des nœuds [S P5].
- **Chiffres** : une roue de 120 dents fait un tour en 24 h, une de 115 dents en 23 h 56 min 4,12 s (jour sidéral à 1 partie sur 3 millions près) [S P5]. Mouvement moyen de la Lune à 1,8 ppm près [S P5]. Une autre source donne 7 ppm « théoriques » pour les trains lunaires [R P6]. Une partie sur 3 millions fait encore 4,4°/siècle sur un cadran d'étoiles [C8].
- **Limites** : l'horloge est perdue. Elle est connue par le manuscrit (Bodleian, MS Ashmole 1796) et l'édition de J. D. North (1976) [S P5].
- **Leçon** : dès 1330, les inégalités se mettent **dans la forme d'une roue**. Pour v2, ce choix est mauvais : une roue irrégulière ne se vérifie ni en fraction exacte ni dans Lean. Une goupille dans une rainure ou un excentrique donnent une formule analytique.

### 1.2 Giovanni Dondi dall'Orologio, *Astrarium* (Padoue, 1348–1364)

- **Montre** : sept cadrans d'environ 30 cm (Primum Mobile, Vénus, Mercure, Lune, Saturne, Jupiter, Mars). En dessous, un cadran de 24 h et un tambour-calendrier avec les fêtes fixes, les fêtes mobiles et le nœud ascendant de la Lune [S P1]. Le modèle est géocentrique : épicycles de Ptolémée, déférents et équants [S P1, P2].
- **Comment** : 107 roues et pignons faits à la main [S P1]. Des roues « quasi elliptiques » dont les dents varient en taille et en espacement reproduisent les mouvements irréguliers [S P1]. Pour Mercure : une roue de 146 dents, **deux roues ovales de 24 dents irrégulières** engrenées entre elles, et une roue à denture intérieure de 63 dents menée par un pignon de 20 [S P1]. Une étude de génie mécanique (2018) décrit aussi des engrenages non circulaires pour la Lune, et une grande roue de champ ovale avec un pignon long pour le Soleil vrai [R P3, résumé seul].
- **Chiffres** : Mercure fait 63/20 × 12 = 37 signes 24° par an, pour 37 signes 24° 43′ 23″ « requis par la théorie » [S P1]. Nous retrouvons exactement 189/5 signes [C7].
- **Limites** : **aucune année bissextile**. Dondi conseille d'« arrêter l'horloge un jour entier » [S P1]. L'original est perdu. Le *Tractatus astrarii* survit en douze manuscrits, dont l'autographe (Padoue, Biblioteca Capitolare, MS D39) [S P1]. Il existe au moins huit reconstitutions : sept par Peter Haward (Thwaites & Reed), dont celles de la Smithsonian et du Time Museum, une à La Chaux-de-Fonds (Luigi Pippa) et une à l'Observatoire de Paris [S P1, P2, P4].
- **Leçon** : Dondi est le premier à mécaniser des **inégalités** (Mercure, Lune). La roue ovale garde un rapport *moyen* exact (24:24) et met toute l'inégalité dans le profil. C'est élégant, mais difficile à tailler et à vérifier. **Le calendrier sans bissextile est le contre-exemple de notre cahier des charges.**

### 1.3 Ole Rømer : planétaire, éclipsarium, jovilabe (Paris, 1672–1681). Bonus, éclipses

- **Montre** : un planétaire (Mercure à Saturne autour du Soleil) et un éclipsarium qui calcule les éclipses de Soleil et de Lune [S P8]. Rømer a aussi fait des machines pour les lunes de Jupiter et de Saturne [S P8]. Un « Jovilabium » est daté de 1677 [R].
- **Comment** : l'éclipsarium est un calculateur analogique tourné à la clé. **Deux cames circulaires excentrées tournent en sens contraire** et représentent « tous les mouvements de la Lune ». Deux échelles affichent la décennie et l'année [R P7].
- **Chiffres** : cadrans de 490 mm, meuble de 1 010 mm de haut, environ 27 kg. La machine couvre cent ans de part et d'autre de 1680 et aurait couvert environ 98 % des éclipses sur 200 ans [R P7, selon le fabricant de la réplique]. Elle a été démontrée à Louis XIV le 5 décembre 1681 et réajustée en 1687 [R P7]. L'exemplaire danois est au château de Rosenborg [S P8].
- **Bonus** : Rømer est crédité en 1674 du profil de dent cycloïdal, publié par La Hire en 1694 [S P9]. Schwilgué l'emploie encore à Strasbourg pour réduire les frottements [S P31].
- **Leçon** : pour les éclipses, une **paire d'excentriques** bien phasés vaut mieux qu'un long train. Rømer avait aussi mesuré en 1676 le retard des éclipses d'Io, d'où la vitesse finie de la lumière [S P57]. Nous retrouvons cet effet au §2.7.

### 1.4 Christiaan Huygens, planétaire (La Haye, 1682). Bonus, méthode des rapports

- **Montre** : six planètes autour du Soleil. Les orbites suivent « la conception de Kepler » (excentriques), et la machine rend compte des « alternances de vitesse ». La Lune y figure, et les satellites de Jupiter (4) et de Saturne (5) sont seulement dessinés [S P10].
- **Comment** : octogone de bois de deux pieds de diamètre et six pouces de profondeur, réalisé par Johannes van Ceulen [S P10]. Chaque planète porte un anneau denté. Pour la Lune, un anneau intérieur de 137 dents et des pignons de 12 et 13 [S P10]. **Huygens choisit les dentures par les réduites de fractions continues.** Il réduit le rapport Terre/Saturne 2 640 858 : 77 708 431 à 7 : 206 [S P10]. C'est la première application d'ingénierie des fractions continues (*Descriptio automati planetarii*, 1703) [S P10].
- **Chiffres** (dents roue planétaire / pignon) : Saturne 206/7, Jupiter 166/14, Mars 158/84, Vénus 32/52, Mercure par deux étages (121 ; 7/12 ; 17), soit 847:204 [S P10]. D'après le musée, « en vingt ans, les orbites restent justes à 3,5° près », et la machine se règle sur toute configuration entre 1580 et 1880 [S P11]. Musée Boerhaave, Leyde, inv. V9997 [S P11].
- **Recalcul** [C6], dérive face aux périodes modernes : Saturne +1,2°/siècle, Jupiter +1,2, Mars −1,4, Mercure −5,0, **Vénus −18,8°/siècle** (32/52 = 8/13 n'est que le cycle de 8 ans). Cela fait environ 3,8° en 20 ans pour Vénus, ce qui concorde avec les « 3,5° ».
- **Limites** : un prototype dont les « problèmes techniques sont vite apparus » [S P10].
- **Leçon** : **un seul étage par planète ne suffit pas pour moins de 1°/siècle.** Huygens montre que ses meilleurs rapports à un étage sont à environ 1°/siècle et ses pires à près de 20. Il faut des trains composés à deux ou trois étages (Mercure en avait déjà deux), choisis par réduites *et* médiantes.

### 1.5 Graham, Tompion, Rowley, puis Thomas Wright : naissance de l'« orrery » (v. 1704–1733)

- **Montre** : le Grand Orrery de George II (Thomas Wright, 1733) montre Mercure, Vénus, la Terre, Mars, **Jupiter avec ses quatre lunes**, Saturne avec cinq lunes, le Soleil et la Lune [S P12]. **On le fait tourner avec une manivelle** [S P13].
- **Histoire** : George Graham et Thomas Tompion font un appareil (v. 1710, Oxford). John Rowley le copie (v. 1712) pour Charles Boyle, 4ᵉ comte d'Orrery, qui donne son nom à l'objet [S P14]. Wright, apprenti puis successeur de Rowley, annonce dès 1731 de « grands orreries avec les mouvements de toutes les planètes et satellites, et le vrai mouvement de l'anneau de Saturne » [S P15].
- **Chiffres** : 1 680 × 1 420 × 1 420 mm, 277 kg. Laiton, acajou, acier, ivoire. Science Museum, inv. 1927-1659. Inscription : « All the Machinery of this instrument was made new in 1733 by Tho Wright » [S P12]. Coût : 336 £ [R].
- **Leçon** : le format « **planétaire sur le dessus, tourné à la main, avec les lunes de Jupiter** » est historique. Notre orrery de couvercle s'inscrit dans cette lignée. Les rapports de Wright n'ont pas été trouvés [Lacune].

### 1.6 James Ferguson, l'orrery décrit en 1756. Bonus, **précédent du bras de visée**

Source : *Astronomy explained upon Sir Isaac Newton's principles* (1756), chap. XXII, §434 et §138 [S P16].

- **Montre** : Soleil, Mercure, Vénus, Terre et Lune. Mars, Jupiter et Saturne s'ajoutent à la demande. « Les quatre satellites de Jupiter sont menés autour de lui dans leurs temps propres **par une petite manivelle** », séparée de la principale. Saturne a cinq satellites et un anneau qui garde son parallélisme [S P16].
- **Géocentrique** : « un fil articulé, dont une extrémité est mise dans un trou de la tige qui porte […] la Terre, et le fil couché dans une petite fourche que l'on pose sur Vénus ou Mercure, **montre les mouvements directs et rétrogrades de ces deux planètes, avec leurs temps et lieux stationnaires, vus de la Terre** » [S P16, §434]. Au §138, Ferguson trace les boucles géocentriques au crayon, avec un carton qui suit la Terre en gardant son parallélisme [S P16].
- **Éclipses** : un petit Soleil est gravé à 17° de chaque nœud et une petite Lune à 12°, ce sont les limites des éclipses solaires et lunaires. Si la Lune tombe entre ce repère et le nœud à la nouvelle lune, il y a éclipse de Soleil. Selon le signe de sa latitude et l'inclinaison de l'axe terrestre, « on juge aisément si l'éclipse sera visible dans l'hémisphère nord ou sud » [S P16]. Les nœuds rétrogradent « en 18 ⅔ ans », le chiffre de Ferguson (la valeur moderne est d'environ 18,6 ans).
- **Entraînement** : « une manivelle […] si aisée à mouvoir qu'une horloge pourrait la tourner » [S P16].
- **Leçon** : c'est **exactement** notre principe de couplage. Un bras pivotant sur la Terre de l'orrery et passant par la planète donne la direction géocentrique. Ferguson s'en sert comme d'un accessoire amovible pour les planètes inférieures. Notre travail : (a) le rendre permanent pour huit planètes, (b) **transmettre** l'angle à l'avant, (c) donner au maneton le **bon rayon** (voir §2.3). La règle d'hémisphère de Ferguson est un premier niveau pour notre indicateur d'éclipse.

### 1.7 Philipp Matthäus Hahn, *Weltmaschinen* (Onstmettingen et Ludwigsburg, 1768–1770). Bonus, double affichage

- **Montre** : la « Ludwigsburger Weltmaschine » (1768–1769) réunit « le système ptolémaïque avec la Terre au centre et le système héliocentrique de Copernic ». Elle a des cadrans pour heures, minutes, secondes, mois, quantièmes et jours de la semaine, plus un « compteur de temps du monde » calculé pour 7 777 ans. Elle mesure 226 × 245 × 74 cm [S P18]. Les *Weltmaschinen* de Hahn montrent les systèmes planétaires « jusqu'aux positions des quatre lunes de Jupiter », le tout mené par un mouvement d'horlogerie [S P17].
- **Comment** : Hahn « attachait une importance particulière au calcul exact des roues dentées » pour garder la précision à long terme. Il a conçu une **machine à calculer** en partie pour cela : un train lunaire dérivé de la rotation diurne (début 1773), la différence entre jour solaire et jour sidéral (mai 1773), l'« année des nœuds » (1780) [S P17].
- **Limites** : nous ignorons si le cadran ptolémaïque est **dérivé** du copernicien ou calculé à part [Lacune]. L'analyse technique de référence est celle de L. Oechslin, *Astronomische Uhren und Weltmodelle der Priestermechanik im 18. Jh.* (Neuchâtel, 1996, 3 vol.) [S P17].
- **Leçon** : notre double affichage (géocentrique devant, héliocentrique dessus) a un ancêtre direct. Comme Hahn avec sa machine à calculer, nous calculons les rapports par programme (Python, fractions) et les vérifions dans Lean.

### 1.8 Eise Eisinga, planétaire de Franeker (1774–1781)

- **Montre** : le Soleil, la Lune, la Terre, Mercure, Vénus, Mars, Jupiter et Saturne tournent **en temps réel** au plafond, distances à l'échelle de 1 mm pour un million de km [S P19, P21]. Des cadrans donnent l'heure, la date, les phases et les nœuds de la Lune, le jour de la semaine, les levers et couchers [S P19, P22, P23].
- **Comment** : une seule pendule [S P21], entraînée par neuf poids [S P19, P20] (une autre source en compte huit [R]), mène dans les combles des **cerceaux et disques de chêne dont les « dents » sont des clous forgés à la main** [S P20, P22].
- **Chiffres** : 5 934 clous selon une source [S P20], « 10 000 clous » selon une autre [S P19]. Les deux chiffres sont incompatibles. Mercure fait son tour en 88 jours et Saturne en plus de 29 ans [S P20].
- **Limites** : il faut **recaler à la main tous les quatre ans** (années bissextiles) et changer la planche des millésimes tous les 22 ans. Le pendule, d'un seul métal, est sensible à la température [S P19]. Uranus, découverte en 1781, n'a pas été ajoutée faute de place [S P20, P23]. Remise en état en 1795 après l'exil d'Eisinga [S P22]. Achat par Guillaume Iᵉʳ en 1818 [S P20]. Patrimoine mondial de l'UNESCO depuis le 19 septembre 2023 [S P21]. Le planétaire a été bâti pour désamorcer la panique causée par la prédiction de fin du monde du pasteur Eelco Alta (1774) [S P20].
- **Leçon** : **l'échelle linéaire des distances exclut Uranus et Neptune.** Strasbourg a fait le même constat (§1.10). Notre orrery de couvercle devra avoir des **rayons non linéaires**, compressés ou logarithmiques. Le §2.3 montre que cela n'abîme pas le couplage si le bras de visée travaille sur une géométrie séparée. Deuxième leçon : sans calendrier grégorien mécanisé, un planétaire perpétuel exige des interventions humaines.

### 1.9 Antide Janvier, sphères mouvantes et planétaires (1768–1812)

- **Montre** : à 16 ans, il présente à l'Académie de Besançon (1768) une sphère montrant « les grandeurs des planètes, leurs excentricités, **la rétrogradation des points équinoxiaux** [la précession], les révolutions des satellites » [S P24]. En 1773, un planétaire réduit à 10 pouces est présenté à Louis XV [S P24]. Le 29 avril 1789, une « horloge planétaire, la plus complète encore produite », est remise à Louis XVI pour Versailles [S P24]. En 1806, une machine montre « le système de l'équation du temps par ses causes » [S P24]. Une sphère copernicienne à mouvement de pendule de 1774 (51 × 28 × 28 cm), « réparée par l'auteur en 1825 », montre Mercure, Vénus, Terre-Lune, Mars, Jupiter et Saturne avec son anneau [S P26].
- **Écrits** : *Des révolutions des corps célestes par le mécanisme des rouages* (Paris, Didot, 1812), qui décrit notamment le planétaire de Huygens [S P25] ; *Manuel chronométrique* (1821) ; *Recueil des machines* (1827) [S P27]. La plus grande collection publique est au musée Paul-Dupuy de Toulouse. La sphère de 1768 est au musée du Temps de Besançon [S P24, P27].
- **Limites** : nous n'avons pu lire aucun de ses rapports de denture. Gallica bloque l'accès automatisé [Lacune : télécharger le PDF Gallica à la main et le dépouiller].
- **Leçon** : Janvier traite ensemble l'excentricité et la précession dès 1768, et il explique l'équation du temps **par ses causes**, c'est-à-dire décomposée. C'est le même choix que Schwilgué et Olsen (§2.5).

### 1.10 Jean-Baptiste Schwilgué, horloge astronomique de Strasbourg (1838–1842). **Le précédent clé**

*Sources principales : J. Lefort (1993), d'après A. et T. Ungerer (1922) [P28], et le dossier du club Astro Aspach [P29]. Lefort donne des rapports exacts : nous les avons tous revérifiés [C1–C5].*

- **Montre** : temps moyen et temps civil [S P32]. Calendrier perpétuel avec fêtes mobiles. **Comput ecclésiastique** : nombre d'or, cycle solaire, indiction, lettre dominicale, épacte, date de Pâques [S P33]. Cadran du « temps apparent » avec **positions vraies** du Soleil et de la Lune [S P29]. Phases et **éclipses** [S P30]. Planétaire copernicien de Mercure à Saturne, à l'échelle sauf pour la Lune [S P29, P30]. Globe céleste en jour sidéral avec **précession** [S P29, P30].
- **Comput grégorien** : conçu en 1816, maquette en 1821 présentée à Louis XVIII. Schwilgué l'a trouvé « en cherchant à démontrer qu'il serait impossible » [S P28, P31, P32]. Le comput travaille **une fois par an, le 31 décembre à minuit**, et transmet les nouvelles fêtes mobiles [S P29]. Calendrier : un anneau de **368 secteurs**, avancé d'1/368 de tour chaque nuit. Janvier et février sont peints sur un **secteur mobile à deux positions** qui découvre ou masque le 29 février. La nuit du Nouvel An, l'anneau fait **3 ou 4 pas** selon que l'année est bissextile ou commune [S P29]. L'anneau pascal couvre 123 pas et porte 13 lamelles, de la Septuagésime à la Fête-Dieu [S P29]. L'épacte saute de 10 au lieu de 11 après les années séculaires non bissextiles, et d'autres cas sont « programmés » [S P29].
- **Contraintes de denture** : les roues sont limitées à environ 500 dents, la plus grande trouvée en a 420. Le plus grand nombre premier taillé est **281**, puis 269. Le plus petit pignon a **6** dents [S P28]. Les rapports sont choisis par fractions continues et médiantes de Farey pour ne garder que de **petits facteurs premiers** [S P28].
- **Temps sidéral, deux méthodes** [S P28] :
  - *Exacte* (globe céleste) : avec l'année de Schwilgué (31 556 928 s), R = 164 359/164 809. Le dénominateur est un grand nombre premier, donc on écrit **1/R = 1 + 450/(13·47·269)** et on réalise le « + » par un **train épicycloïdal** (roues 45/72, 18/270, 18/269, 26/100, 18/94). **Nous retrouvons le rapport exact** [C1].
  - *Approchée* (train lunaire) : 271 375/272 118, réalisée par (334·65·300)/(28·341·57) = 12 × 271 375/272 118 [C2]. L'erreur est de 0,92 s par siècle, soit 0,004°/siècle sur un cadran d'étoiles [C2].
- **Planétaire** : périodes en secondes (Mercure 7 600 457 s, Vénus 19 413 685, Mars 59 350 724, Jupiter 374 163 250, Saturne 928 535 410) et réduites choisies par planète. L'erreur maximale est de **13 s sur la période de Jupiter** [S P28], soit 1·10⁻⁴ °/siècle [C5]. **Uranus a été exclue** parce que son aiguille aurait dépassé la place disponible ou écrasé les planètes intérieures [S P29].
- **Inégalités de la Lune et du Soleil** : cinq pour la Lune (anomalie, évection, variation, équation annuelle, nœuds) et trois corrections pour le Soleil [S P28]. Chaque inégalité est tracée sur deux périodes autour d'un **cylindre-came**. Une traverse horizontale monte ou descend en proportion. **Les cylindres sont empilés, chacun posé sur la traverse du précédent, et la traverse du haut porte la somme.** Les plus grandes inégalités sont en haut pour limiter la longueur des pignons [S P28]. Rapports depuis un axe d'un jour moyen [S P28], vérifiés [C3] :

  | Inégalité | Rapport choisi | Période obtenue | Écart |
  |---|---|---|---|
  | Anomalie (mois anomalistique) | 70 209/2 548 | 27 j 13 h 18 min 33,34 s | −0,66 s |
  | Évection | 74 090/2 329 | 31 j 19 h 29 min 11,31 s | −0,14 s |
  | Variation (mois synodique) | 51 649/1 749 | 29 j 12 h 44 min 2,88 s | −0,12 s |
  | Équation annuelle (année anomalistique) | 226 461/620 | 365 j 6 h 13 min 56,13 s | −0,87 s |
  | Nœuds (mois draconitique) | 49 880/1 833 | 27 j 5 h 5 min 35,84 s | +0,04 s |

  La somme passe par des poulies et des tringles jusqu'à un **cadre pivotant** portant deux pignons, de sorte que (c/b)(B/C) = 2. La roue de sortie reçoit alors **le mouvement moyen moins le déplacement du cadre** : c'est un différentiel [S P28].
- **Équation du temps** : deux disques profilés, l'un pour la **réduction à l'équateur**, l'autre pour l'**équation du centre**, « associés » par un mécanisme [S P29].
- **Éclipses** : une came d'environ **18,6 ans allonge ou raccourcit l'aiguille de la Lune**. Le disque lunaire passe au-dessus du Soleil, en dessous, ou le couvre partiellement ou totalement [S P28, P29]. Pour les éclipses de Lune, un disque noir anti-solaire est monté à l'opposé de l'aiguille du Soleil [S P29]. **Henri Bach a vérifié l'affichage le 15 février 1961** : sa photo des aiguilles est très proche de celle de l'éclipse partielle réelle [S P29].
- **Précession** : le globe tourne autour de l'axe du monde en un jour sidéral et, en sens inverse, autour de l'axe de l'écliptique en « 258 siècles environ ». Une roue du train tourne en **25 806 ans** [S P29, P30]. La dernière roue a 128 dents [S P29]. La source dit qu'elle a avancé de « 0,7 dent » en 170 ans ; nous trouvons **0,84 dent** [C4].
- **Limites** : la période des nœuds de son époque (587 371 310 s) contient le facteur premier 58 737 131. Il a fallu l'approcher [S P28]. Les horloges de 1354 et de 1574 s'étaient arrêtées, la seconde en 1788, « bloquée par la crasse d'huile et de poussière » [S P28]. **Tous les mécanismes sont réglables**, ne serait-ce que pour la mise en route [S P28]. Le devis a plus que doublé : 32 400 F prévus, 101 725,90 F votés au total [S P28]. D'après une source secondaire, l'erreur annuelle serait d'au plus 2 s par an [R P37].
- **Leçons** :
  1. **Notre Lune « moderne » a été mécanisée en 1842** (quatre termes plus les nœuds). La question n'est pas de savoir si c'est possible, mais d'en tenir les **amplitudes** à 0,5° près. Les amplitudes de Schwilgué ne sont pas connues [Lacune : Ungerer 1922].
  2. **Le différentiel est l'outil anti-grands-premiers** : 1/R = 1 + petite fraction.
  3. **Un comput annuel discret** (déclenché une fois par an) est plus simple qu'un calcul continu.
  4. Des **embrayages de réglage** pour chaque cadran.
  5. Un orrery à l'échelle exclut Uranus et Neptune.

### 1.11 Jens Olsen, *Verdensur* (Copenhague : calculs 1928, mise en marche 1955)

- **Montre** : douze mouvements [S P34]. Temps moyen, temps sidéral, équation du temps (universelle et locale), temps solaire vrai, levers et couchers, heure mondiale. **Calendrier grégorien** (année, mois, quantième, jour de la semaine) et comput (lettre dominicale, épacte, cycle solaire, indiction, nombre d'or). Période julienne, ciel étoilé avec cercle de précession. **Révolution héliocentrique** : 8 planètes autour d'un Soleil fixe, sur un zodiaque. **Révolution géocentrique** : Soleil, Lune, nœuds, périgée et phase sur l'écliptique. Éclipses [S P34, P35].
- **Comment** : un mouvement caché, l'« **Equation Works** », produit huit vitesses de rotation : ½ année tropique, **année anomalistique**, ½ mois draconitique, ½ mois synodique, **oscillation des nœuds lunaires (173,31001 j)**, **oscillation des apsides lunaires (205,89744 j)**, **évection (31 j 19 h 29 min)** et mois anomalistique (27 j 13 h 18 min) [S P34]. Les anomalies sont **combinées aux mouvements moyens par des différentiels** sur le cadran géocentrique [S P34]. Le calendrier change **de façon discontinue à minuit moyen** [S P34]. Les fêtes mobiles (Pâques, Pentecôte) sont recalculées la nuit du Nouvel An [S P35].
- **Chiffres** : 15 448 pièces selon Wikipédia anglais [S P34], **14 448** selon Wikipédia danois [S P35]. TIME (1956) parle de « 15 000 pièces » et de « 445 roues dentées » [S P36]. La roue la plus rapide fait un tour en 10 s, la plus lente en **25 753 ans** (précession) [S P34]. Selon TIME, l'écart sur le temps sidéral serait de 2/5 de seconde en 300 ans, et le calendrier exécuterait « 570 000 fonctions en six minutes » chaque Nouvel An [R P36, chiffres journalistiques]. Les planètes du cadran héliocentrique décrivent des **orbites circulaires à vitesse constante** (selon Wikipédia) [S P34].
- **Histoire et entretien** : calculs terminés en 1928 et contrôlés par l'astronome Elis Strömgren. Dessins de 1934 à 1936, fabrication de 1943 à 1955. Olsen meurt en 1945 ; Otto Mortensen achève l'horloge et publie *Jens Olsen's Clock: A Technical Description* (1957) [S P34, P35]. Restauration de 1995 à 1997 avec **470 roulements à billes miniatures** et un revêtement nickel-téflon [S P34]. Laiton doré, cadrans rhodiés, tige de pendule en Invar [S P34].
- **Leçons** : (1) Séparer **année anomalistique** et **année tropique** (et ½ année) : c'est la décomposition propre de l'équation du centre et de la réduction à l'équateur. (2) La Lune d'Olsen va **au-delà** de nos quatre termes, avec les oscillations de l'apside et des nœuds. Ce sont des candidats si le budget de 0,5° l'exige. (3) Même Olsen a laissé les planètes **en cercles**. L'équation du centre pour huit planètes serait donc un apport réel de v2. (4) Une grande démultiplication fatigue les pivots : prévoir des paliers.

### 1.12 Rasmus Sørnes, horloges n° 1 à 4 (Norvège, 1937–1966)

- **N° 1** (1937) : balancier électromagnétique alimenté par piles. « La précision des orbites célestes souffrait, car les calculs reposaient sur des calendriers réguliers sans correction complète des irrégularités » [S P37].
- **N° 2** : calendrier julien, qui gagne 1 jour en 128 ans. Le temps sidéral retarde d'une minute en 10 ans. L'erreur sur le mouvement annuel de la Terre est de 0,7 s par an [S P37].
- **N° 3** (1954, musée de Borgarsyssel, Sarpsborg) : ajoute des **mécanismes de correction des irrégularités** et la précession. Le globe céleste fait un tour en **25 800 ans par un train de rapport 1:9 500 000** [S P38]. Nous trouvons 9,42·10⁶ jours en 25 800 ans [C9]. Un orrery à 9 planètes (Pluton en 248 ans) est monté au dos sur un zodiaque gravé dans le verre [S P38]. Éclipses : une aiguille marquée Ω. « Les trois aiguilles ne coïncident exactement que tous les 18,5 ans » [S P38] : la source mélange ici le saros (18,03 ans) et la révolution des nœuds (18,6 ans). **« Au centre du cadran, une tranche sphérique de la Terre tourne en sens inverse une fois par jour sidéral, et sert à indiquer où l'éclipse est visible »** [S P38].
- **N° 4** (achevée en 1966 ou 1967) : calendriers julien et grégorien, Pluton en 248 ans, précession en 25 800 ans, cycle des taches solaires, éclipses [S P37]. Toutes les pièces ont été faites à la main, sauf le pendule, avec des outils qu'il a construits lui-même [S P37, P39]. L'erreur annoncée est de 7 s en 1 000 ans [R P37]. Exposée au Time Museum de Rockford, puis au MSI de Chicago (1999), vendue aux enchères en 2002 pour 295 000 $ [S P39]. Elle est aujourd'hui **introuvable** [S P37, P39].
- **Leçon** : la progression de Sørnes est un **avertissement**. Sans corrections (inégalités, calendrier grégorien), une horloge pourtant soignée dérive à l'œil en quelques décennies. La **tranche de Terre tournant en un jour sidéral** est le meilleur précédent trouvé pour le « où » d'une éclipse.

### 1.13 Calendrier séculaire en montre : Patek Philippe Calibre 89 (1989), Svend Andersen, Franck Muller

- **Patek 89** : 1 728 pièces sur quatre niveaux et 33 complications. Calculs commencés en 1980, prototype en juillet 1988, achèvement en avril 1989 [S P40, P41].
  - *Règle 4/100/400* : une **came séculaire fait un tour en 100 ans, et un satellite à quatre pointes sur sa circonférence fait un tour en 400 ans**, la pointe longue correspondant à la quatrième centaine bissextile. Un levier à quatre gradins neutralise la came des mois les années séculaires communes [S P41].
  - *Pâques* : pas de calcul. C'est une **mémoire mécanique**, une came crénelée qui donne la date de Pâques de 30 années successives (22 mars au 25 avril), plus une seconde came fournie à part pour 29 années de plus (brevet CH 649 673) [S P40].
  - *Temps sidéral* : rapport de 0,9972677 au lieu de 0,9972696 (1,9 ppm), obtenu par une cascade de 32 roues [S P40]. Cela fait **≈ 25°/siècle** sur un cadran d'étoiles [C8]. C'est acceptable sur une montre qu'on remet à l'heure, pas pour une machine à manivelle qui parcourt les siècles.
- **Andersen** : une came de 48 mois fait un tour en 4 ans et avance une roue de réduction d'une dent ; une **roue séculaire de 50 dents avance d'une dent tous les 8 ans**, d'où un tour en 400 ans [S P41, C12].
- **Franck Muller (Aeternitas Mega)** : came séculaire à trois encoches (trois centaines communes) plus un gradin haut pour 2400 [S P41].
- **Leçon** : la règle 4/100/400 tient en **une came de 4 ans, une came de 100 ans et un satellite de 400 ans** (ou une roue de 50 dents). C'est compatible avec nos 10 à 220 dents. Le calendrier grégorien moyen de 365,2425 j dérive lui-même de 44,6 min par siècle face à l'année tropique [C12]. Il faut le dire dans le budget d'erreur, sans le corriger : c'est la règle civile. **Pâques** : une vraie mécanique de comput (Strasbourg, Olsen) ou une mémoire limitée (Patek). Pour une machine sur des siècles, seul le comput est honnête.

### 1.14 Ludwig Oechslin et Ulysse Nardin, « Trilogy of Time » (1985–1992)

- **Astrolabium Galileo Galilei** (1985 ; présenté à la foire de 1984 selon Europa Star) : un mécanisme de **101 pièces** [S P43]. Il affiche les positions du Soleil et de la Lune, les levers et couchers du Soleil et de la Lune, les phases, les étoiles fixes, et les **éclipses par une « aiguille du dragon »** qui doivent coïncider avec les aiguilles du Soleil et de la Lune [S P44]. La « grille » fait un tour en 23 h 56 min 4,1 s [S P44]. La période de l'aiguille du dragon est imprimée « 18 611 ans » dans la source, ce qui est manifestement 18,611 ans [S P44, coquille]. Le fabricant annonce une erreur d'un jour en 144 000 ans, sans préciser sur quelle grandeur [R P42, P44]. Inscrite au *Guinness Book* en 1989 comme la montre la plus complexe [S P47].
- **Planetarium Copernicus** (1988 ; 1989 selon Europa Star) : positions astronomiques du Soleil, de la Lune, de Mercure, Vénus, Mars, Jupiter et Saturne. **Réglable sur n'importe quelle date** [S P45].
- **Tellurium Johannes Kepler** (1992, 99 exemplaires) : la Terre vue du pôle Nord. Un **ressort flexible** sépare le jour de la nuit en se courbant entre les tropiques. Éclipses, nœuds et zodiaque [S P46].
- **Oechslin** : il a restauré l'horloge Farnèse de la Bibliothèque vaticane, construit une réplique de la machine d'Anticythère, et calculé l'horloge Türler (1986–1995) [S P47]. C'est l'auteur de l'étude sur Hahn (§1.7). Ulysse Nardin souligne qu'il emploie **des roues plutôt que les leviers** usuels en horlogerie [S P42].
- **Leçon** : la **mise à date réversible** (Copernicus) est un précédent pour notre manivelle, qui doit tourner dans les deux sens. Le ressort jour/nuit est une idée de terminateur bon marché. Préférer les trains de roues, vérifiables, aux leviers à came.

### 1.15 Christiaan van der Klaauw : planétaires-montres (1999 ; 2024)

- **CVDK Planetarium** (1999) : présenté comme le plus petit planétaire mécanique du monde. Six planètes de Mercure à Saturne en temps réel [R].
- **Grand Planetarium Eccentric** (2024, pour le 50ᵉ anniversaire) : **les huit planètes**, avec leurs périodes réelles de Mercure (87,97 j) à **Uranus (84,02 ans) et Neptune (164,80 ans)**. Trajectoires **excentriques** « au plus près de la réalité », **3 338 dents** au total. L'idée vient du « Kepler's Planetarium Clock » de 1995. Mouvement automatique de 60 h, 3 Hz [S P48, P49].
- **Limites** : le site ne dit pas si la vitesse angulaire varie le long de l'orbite (deuxième loi de Kepler) ni quels rapports sont employés [Lacune].
- **Leçon** : huit planètes dont Uranus et Neptune ont été mécanisées en 2024, au poignet, en environ 3 300 dents. **Notre nouveauté n'est donc pas « 8 planètes »**, mais 8 planètes **avec l'équation du centre, couplées à un affichage géocentrique, à moins de 1°/siècle et vérifiées par preuve**.

### 1.16 Hublot, calibre « Antikythera » 2033-CH01 (2011). Bref

- Mouvement de 495 composants, dévoilé en octobre 2011. Au cadran : calendrier égyptien, calendrier des jeux panhelléniques, zodiaque, Soleil, phase de Lune. Aux ponts : cycles de **Méton, saros, Callippe et exeligmos**. Contrairement à l'original, il marche seul (tourbillon). Trois ou quatre exemplaires prévus, jamais vendus [S P50].
- **Leçon** : un **hommage miniaturisé** à l'original, sans ambition astronomique nouvelle. Notre projet est d'une autre nature : il fait évoluer le contenu, pas la taille.

### 1.17 Long Now Foundation : orrery prototype et « serial bit adder » (1997–). Bonus, alternative numérique

- **Montre** : les six planètes visibles à l'œil nu, Mercure à Saturne [S P51].
- **Comment** : un **additionneur binaire série mécanique** par planète (six disques). Chaque disque porte deux jeux de **27 goupilles** : un jeu fixe (le « programme », c'est-à-dire la constante à ajouter) et un jeu mobile (l'accumulateur). Les positions sont mises à jour deux fois par jour [S P51]. Brevet de W. D. Hillis, déposé le 10 décembre 1997 : « la partie fractionnaire reste dans l'accumulateur, de sorte que les erreurs d'arrondi ne s'accumulent pas » [S P53]. L'horloge prototype de 1999 (Science Museum, Londres) travaille sur 32 bits [S P52].
- **Leçon** : c'est la seule voie qui **échappe complètement** aux rapports d'engrenages, puisque la précision vient du nombre de bits. Elle sort de « l'esprit Anticythère » (roues de bronze, mouvement continu), mais elle peut servir de **contre-exemple** : le jour où un rapport serait intenable dans nos 10 à 220 dents, un compteur à goupilles peut le remplacer.

### 1.18 Raúl Pagès : écarté

Horloger indépendant et restaurateur, passé par l'atelier de restauration de Parmigiani. Ses montres sont le RP1 « Régulateur à détente » et le RP2, une montre heures-minutes-secondes sans complication [S P54]. **Nous n'avons trouvé aucune pièce astronomique publiée.** Il n'est donc pas retenu comme précédent.

---

## 2. Leçons transversales, fonction par fonction

### 2.1 Choisir les rapports

| Qui | Méthode | Plage de dentures | Précision atteinte |
|---|---|---|---|
| Huygens 1682 | Réduites de fractions continues, 1 ou 2 étages | 7–206 | 1 à 19°/siècle selon la planète [C6] |
| Schwilgué 1842 | Réduites, médiantes de Farey, **petits facteurs premiers** | 6–420 (premier max. 281) | Planètes ≤ 1·10⁻⁴ °/siècle [C5] ; périodes lunaires à moins d'une seconde [C3] |
| Schwilgué 1842 | **Différentiel « 1 + ε »** pour un dénominateur premier | idem | **Exact** [C1] |
| Hahn 1773 | Machine à calculer dédiée | ? | ? [Lacune, Oechslin 1996] |
| Patek 1989 | Cascade de 32 roues (sidéral) | ? | 1,9 ppm, soit ≈ 25°/siècle [C8] |
| Long Now | Accumulateur binaire | — | Limité par le nombre de bits |

**À retenir pour v2** (10 à 220 dents, module ≥ 0,4 mm) :

- 220 dents au maximum, c'est moins que Schwilgué (420) mais autant qu'Anticythère (223). Les rapports à grands premiers passeront par **deux ou trois étages** ou par un **différentiel 1 + ε**.
- Notre cible de **< 1°/siècle** demande une précision relative d'environ 6,7·10⁻⁶ pour Mercure (415 tours par siècle) mais seulement de 0,5 % pour Neptune. Le budget doit être réparti planète par planète.
- La sortie de `precedents_checks.py` est le modèle de vérification : chaque rapport en `Fraction`, sa période et sa dérive par siècle, puis la preuve Lean.

### 2.2 L'équation du centre (Kepler)

Précédents : la roue ovale (Dondi ; Wallingford pour le Soleil), l'excentrique et l'équant (Ptolémée, mécanisé par Dondi), la goupille et la rainure (Anticythère, déjà présente dans la spec v1), l'orbite excentrique (Huygens, Van der Klaauw 2024). Eisinga, Strasbourg, Olsen et Ulysse Nardin s'en tiennent au cercle uniforme.

**Lecture chiffrée** [C13], erreur maximale sur la longitude héliocentrique comparée à Kepler exact :

| Planète | e | Goupille et rainure (k = 2e) | Excentrique et équant |
|---|---|---|---|
| Mercure | 0,206 | **2,79°** | 0,90° |
| Vénus | 0,007 | 0,002° | 0,001° |
| Terre | 0,017 | 0,012° | 0,004° |
| Mars | 0,093 | **0,45°** | 0,15° |
| Jupiter | 0,048 | 0,11° | 0,04° |
| Saturne | 0,054 | 0,14° | 0,05° |
| Uranus | 0,047 | 0,10° | 0,04° |
| Neptune | 0,009 | 0,003° | 0,001° |
| Lune (rappel) | 0,055 | 0,13° | — |

La goupille et la rainure laissent une erreur du second ordre d'environ ¾ e² sin 2M, ce qui pose problème pour Mercure. L'équant de Ptolémée, que Dondi savait construire, fait trois fois mieux. **Il faudra trancher dans `study/`** : équant, double goupille, ou excentrique plus correction pour Mercure.

### 2.3 Coupler l'orrery et le cadran géocentrique (le « suiveur »)

- **Précédent direct** : le fil articulé de Ferguson (1756) [S P16]. Le principe de suiveur d'Anticythère est dans la spec v1. Hahn (1769) a les deux systèmes dans la même caisse, mais leur lien est inconnu [Lacune].
- **Non trouvé** : aucune machine qui **transmette** l'angle du bras de visée à des aiguilles. C'est une zone neuve.
- **Point dur chiffré** [C14] (géométrie plane, inclinaisons négligées, périhélies décalés de 37° à titre générique). L'erreur géocentrique maximale dépend de la façon dont l'orrery place les manetons :

| Planète | Angles de Kepler exacts mais **rayon constant** r = a | Modèle **excentrique-équant** (angle et rayon) |
|---|---|---|
| Mercure | 5,5° | 0,66° |
| Vénus | 1,3° | 0,02° |
| Mars | **6,8°** | 0,57° |
| Jupiter | 0,7° | 0,05° |
| Saturne | 0,4° | 0,05° |
| Uranus | 0,2° | 0,04° |
| Neptune | 0,04° | 0,001° |

  **Conséquence** : si l'orrery du couvercle sert aussi de calculateur géocentrique, chaque maneton doit suivre une **orbite excentrique**, avec un rayon qui varie. Le cercle décentré de l'équant suffit au premier ordre. Les **rayons à l'échelle** sont alors indispensables, alors qu'Eisinga et Strasbourg ont dû renoncer à Uranus pour cette raison même. Une piste à étudier : un **orrery d'affichage** aux rayons compressés sur le couvercle, et un **orrery de calcul** à l'échelle sous le plateau, menés par les mêmes arbres. Il faudrait alors deux jeux de bras.

### 2.4 La Lune moderne

- Schwilgué (1842) met en œuvre l'anomalie, l'évection, la variation, l'équation annuelle et les nœuds, avec des cylindres-cames sommés et un différentiel [S P28]. Olsen ajoute les oscillations de l'apside (205,9 j) et des nœuds (173,3 j) [S P34]. Rømer se contente de deux excentriques contrarotatifs [R P7]. Anticythère utilise une goupille et une rainure, à un seul terme.
- **Pour v2** : l'architecture « termes séparés → sommateur → différentiel » est éprouvée depuis 184 ans. Le choix porte sur le **sommateur** : cames empilées comme Schwilgué, chaîne de goupilles et rainures, ou différentiels en cascade comme Olsen. Les amplitudes de Schwilgué restent à trouver [Lacune : Ungerer 1922].

### 2.5 Calendrier, temps sidéral, équation du temps, précession

| Fonction | Précédents | Ce qu'on retient |
|---|---|---|
| Bissextiles 4/100/400 | Strasbourg (secteur mobile janvier-février, 3 ou 4 pas au Nouvel An), Olsen, Patek (came de 100 ans et satellite de 400), Andersen (roue de 50 dents tous les 8 ans), Muller | Faisable en 3 ou 4 pièces. **Contre-exemples** : Dondi (aucune bissextile), Eisinga (recalage tous les 4 ans), Sørnes n° 2 (julien) |
| Jour de la semaine | Strasbourg (lettres dominicales), Olsen | Un cycle de 7 sur le compteur de jours. La lettre dominicale sert aussi à Pâques |
| Pâques | Strasbourg et Olsen (vrai comput) ; Patek (mémoire de 30 ans) | Un vrai comput annuel, discret, déclenché une fois par an |
| Temps sidéral | Wallingford (1/3·10⁶), Strasbourg (exact par différentiel), Patek (1,9 ppm), Astrolabium | Il faut une précision relative d'environ 7,6·10⁻⁸ pour moins de 1°/siècle (1° sur 36 525 × 360,99°). Le différentiel de Schwilgué donne la méthode [C1, C8] |
| Équation du temps | Wallingford (roue irrégulière), Janvier (« par ses causes »), Strasbourg (deux disques), Olsen (année anomalistique et ½ année tropique) | **La décomposer** : équation du centre sur l'année anomalistique, réduction à l'équateur sur l'année tropique |
| Précession | Janvier 1768, Strasbourg (25 806 ans), Olsen (25 753 ans), Sørnes (25 800 ans, 1:9 500 000) | La constante actuelle est de 25 771,6 ans et augmente lentement [S P58]. Une erreur de 0,1 % ne coûte que 0,002°/siècle [C9]. Le défi est la démultiplication (≈ 1:9,4·10⁶ depuis un axe journalier). **Idée v2, sans précédent** : l'orrery travaille naturellement en périodes sidérales et le zodiaque avant en longitudes tropiques. La précession est leur différence. Faire tourner lentement **un seul** anneau (étoiles ou zodiaque) suffit |

### 2.6 Éclipses : magnitude et hémisphère

- **Magnitude** : à Strasbourg, une came nodale de 18,6 ans fait varier le rayon de l'aiguille lunaire, et la superposition des disques montre l'éclipse partielle ou totale. Un disque noir anti-solaire sert aux éclipses de Lune. L'affichage a été vérifié en 1961 [S P28, P29]. Wallingford avait déjà le disque anti-solaire [S P5].
- **Prédiction** : l'éclipsarium de Rømer (deux excentriques) [R P7], l'aiguille du dragon de l'Astrolabium [S P44], les repères à 17° et 12° des nœuds chez Ferguson [S P16].
- **Hémisphère et lieu** : Ferguson juge nord ou sud au signe de la latitude lunaire et à l'inclinaison de l'axe [S P16]. Sørnes a une tranche de Terre qui tourne en un jour sidéral [S P38].
- **Pour v2** : en combinant la **latitude lunaire** (came nodale, comme Strasbourg), le **rayon apparent** (distance Terre-Lune donnée par l'anomalie, pour distinguer totale et annulaire), un **index d'hémisphère** (signe de la latitude, comme Ferguson) et une **Terre tournante** (comme Sørnes), on obtient un « où, à peu près » honnête. Le tracé précis de la bande de centralité reste hors de portée mécanique : il faut le dire.

### 2.7 Les lunes galiléennes

- **Précédents** : Wright 1733 (4 lunes) [S P12] ; Ferguson 1756 (4 lunes **sur une manivelle séparée**) [S P16] ; Hahn (4 lunes) [S P17] ; Huygens (orbites seulement dessinées) [S P10] ; machines de Rømer pour Jupiter [S P8] ; le *jovilabe* du Museo Galileo, deux disques servant au calcul des tables [S P59]. Aucun rapport de denture trouvé [Lacune].
- **Physique, à intégrer dans la spec** [C10] : les périodes (NASA) sont 1,769138, 3,551181, 7,154553 et 16,689017 jours [S P56]. Leurs rapports valent **2,0073 et 2,0147, pas 2**. Un engrenage 1:2:4 strict dériverait de **+135°/an** pour Europe et de **+203°/an** pour Ganymède. La relation **exacte** est celle de Laplace, **λ_Io − 3 λ_Eu + 2 λ_Ga ≈ 180°**, avec une libration de 0,03° [S P55]. Sur les vitesses, cela donne n_Io = 3 n_Eu − 2 n_Ga. **Un différentiel** calcule donc Io à partir d'Europe et de Ganymède, ce qui garantit la résonance par construction.
- **Temps de lumière (Rømer)** : vu de la Terre, la position d'Io est décalée de 1,2° par unité astronomique de distance, soit environ ±1,2° crête à crête sur l'année [C11, S P57]. Il faut décider si le cadran est jovicentrique « vrai » ou « vu de la Terre », et l'écrire.

### 2.8 Taille, entraînement, fiabilité

- **Tailles de référence** : planétaire de Huygens, octogone de 61 cm sur 15 cm [S P10] ; éclipsarium de Rømer, 101 cm de haut et 27 kg, cadrans de 49 cm [R P7] ; Grand Orrery de Wright, 168 cm et 277 kg [S P12] ; Weltmaschine de Hahn, 226 × 245 × 74 cm [S P18] ; Astrarium de Dondi, environ 1 m [S P2]. En montre : 101 pièces pour l'Astrolabium [S P43], 3 338 dents pour le CVDK [S P48]. **Une boîte de l'ordre de 40 à 60 cm**, entre Huygens et Rømer, est donc plausible pour v2.
- **Fiabilité** : prototype de Huygens « vite » en panne [S P10] ; Strasbourg arrêtée par la crasse en 1788 [S P28] ; Olsen rééquipé de 470 roulements [S P34] ; Eisinga sensible à la température [S P19] ; Long Now passé au numérique pour résister à l'usure [S P51]. **Pour v2** : un embrayage de réglage par cadran, une manivelle réversible (comme le Copernicus), des paliers aux arbres lents, un effort de manivelle à vérifier (rapport global d'environ 10⁷).
- **Manivelle ou horloge** : la manivelle est historique (Anticythère, Wright, Ferguson, Rømer). Ferguson note qu'une horloge « pourrait la tourner ». Prévoir un carré d'entraînement pour un moteur éventuel ne coûte rien.

### 2.9 Ce que nous n'avons trouvé chez personne (zone neuve, d'après les sources consultées)

1. Un orrery héliocentrique dont les **angles géocentriques sont transmis** aux aiguilles d'un cadran avant, pour toutes les planètes.
2. L'**équation du centre mécanisée pour Uranus et Neptune**. Le CVDK 2024 dessine des trajectoires excentriques, mais la vitesse variable n'est pas documentée.
3. Les **lunes galiléennes liées par la relation de Laplace** au lieu d'un 1:2:4 approché ou d'une manivelle séparée.
4. Un **indicateur combiné magnitude et hémisphère** d'éclipse. Il en existe des morceaux chez Strasbourg, Ferguson et Sørnes.
5. Une machine astronomique dont **chaque rapport est prouvé** formellement (Lean), comme l'est déjà la v1.

---

## 3. Questions ouvertes et pistes

1. **Mortensen (1957), *Jens Olsen's Clock: A Technical Description*** : les rapports et les montages différentiels d'Olsen. À chercher en bibliothèque, à la KB de Copenhague ou à la BnF.
2. **Ungerer (1922), *L'horloge astronomique de la cathédrale de Strasbourg*** : les amplitudes des cinq inégalités, la figure 9 (rapports planétaires) et le mécanisme séculaire du comput. Voir aussi les travaux de D. Roegel (Loria) [P33].
3. **Janvier (1812)** sur Gallica [P25] : l'accès automatisé est bloqué. Il faut le télécharger à la main pour dépouiller ses tables de dentures.
4. **Oechslin (1996)** sur Hahn : savoir si le cadran ptolémaïque de la *Weltmaschine* est dérivé du copernicien.
5. **Addomine, Figliolini et Pennestrì (2018)** [P3] : l'article complet (payant) sur les roues non circulaires de Dondi, pour le Soleil et la Lune.
6. **Van der Klaauw** : la vitesse angulaire varie-t-elle sur les trajectoires excentriques ? Une question à poser au fabricant.
7. **Divergences de sources à ne pas propager** : Olsen 15 448 ou 14 448 pièces ; Eisinga 5 934 clous, environ 6 000 ou 10 000, et 8 ou 9 poids ; Sørnes « 18,5 ans » (confusion saros/nœuds) ; Astrolabium « 18 611 ans » (coquille) ; Strasbourg « 0,7 dent » (0,84 recalculé) ; dates 1984/1985 et 1988/1989 pour les montres Ulysse Nardin.

---

## 4. Sources

| # | Source | URL |
|---|---|---|
| P1 | Wikipedia, *Astrarium of Giovanni Dondi dall'Orologio* | https://en.wikipedia.org/wiki/Astrarium_of_Giovanni_Dondi_dall%27Orologio |
| P2 | Linda Hall Library, *Giovanni Dondi* | https://www.lindahall.org/about/news/scientist-of-the-day/giovanni-dondi/ |
| P3 | M. Addomine, G. Figliolini, E. Pennestrì, « A landmark in the history of non-circular gears design: the mechanical masterpiece of Dondi's astrarium », *Mechanism and Machine Theory* 122 (2018) | https://doi.org/10.1016/j.mechmachtheory.2017.12.027 · https://www.researchgate.net/publication/322398123 |
| P4 | Science Museum Group, mécanisme de remontage de la reconstitution de l'Astrarium (1961–1974) | https://collection.sciencemuseumgroup.org.uk/objects/co964/winding-mechanism-for-reconstruction-of-dondis-astrarium-1961-1974 |
| P5 | N. Whyte, *The Astronomical Clock of Richard of Wallingford* (d'après J. D. North, 1976) | https://www.nicholaswhyte.info/row.htm |
| P6 | Encyclopedia.com, *Richard of Wallingford* | https://www.encyclopedia.com/science/dictionaries-thesauruses-pictures-and-press-releases/richard-wallingford |
| P7 | Atelier Andersen, *Eclipsareon* (réplique de l'éclipsarium de Rømer) | http://ateliera.dk/eclips.htm |
| P8 | Niels Bohr Institutet, *Ole Rømer's machines* | https://nbi.ku.dk/english/www/roemer/roemer/maskiner |
| P9 | Wikipedia, *Cycloid gear* | https://en.wikipedia.org/wiki/Cycloid_gear |
| P10 | H. H. N. Amin, *Christiaan Huygens' Planetarium*, TU Delft (2008) | https://repository.tudelft.nl/file/File_9d19e25b-d4f5-4c19-a497-3a4a44e7e629 |
| P11 | ESA BR-211, *Titan – Huygens: facets of a genius* (2004) | https://www.esa.int/esapub/br/br211/br211.pdf |
| P12 | Science Museum Group, *George II's Grand Orrery* | https://collection.sciencemuseumgroup.org.uk/objects/co1522/george-iis-grand-orrery |
| P13 | Science Museum, *George III: a royal passion for science* | https://www.sciencemuseum.org.uk/objects-and-stories/george-iii-royal-passion-science |
| P14 | Wikipedia, *Orrery* | https://en.wikipedia.org/wiki/Orrery |
| P15 | Wikipedia, *Thomas Wright (mathematical instrument maker)* | https://en.wikipedia.org/wiki/Thomas_Wright_(mathematical_instrument_maker) |
| P16 | J. Ferguson, *Astronomy explained upon Sir Isaac Newton's principles* (1756), Project Gutenberg, §138 et §434 | https://www.gutenberg.org/files/60619/60619-h/60619-h.htm |
| P17 | E. Anthes, *Philipp Matthäus Hahn – Konstrukteur und Hersteller von Instrumenten* | https://www.rechenschieber.org/hahn.pdf |
| P18 | LEO-BW / Landesmuseum Württemberg, *Die « Ludwigsburger Weltmaschine » von Philipp Matthäus Hahn* | https://www.leo-bw.de/en/detail/-/Detail/details/DOKUMENT/lmw_museumsobjekte/81/Die+%22Ludwigsburger+Weltmaschine%22+von+Philipp+Matth%C3%A4us+Hahn+%5BQuelle+Landesmuseum+W%C3%BCrttemberg%5D |
| P19 | Wikipedia, *Eise Eisinga Planetarium* | https://en.wikipedia.org/wiki/Eise_Eisinga_Planetarium |
| P20 | Canon van Nederland, *Eise Eisinga* | https://www.canonvannederland.nl/en/eiseeisinga |
| P21 | UNESCO, *Eisinga Planetarium in Franeker* | https://whc.unesco.org/en/list/1683/ |
| P22 | Linda Hall Library, *Eise Eisinga* | https://www.lindahall.org/about/news/scientist-of-the-day/eise-eisinga/ |
| P23 | Wikipedia (nl), *Eise Eisinga Planetarium* | https://nl.wikipedia.org/wiki/Eise_Eisinga_Planetarium |
| P24 | AET de Besançon, *Antide Janvier (1751–1835)* | https://aetdebesancon.home.blog/2024/01/18/antide-janvier-1751-1835/ |
| P25 | A. Janvier, *Des révolutions des corps célestes par le mécanisme des rouages* (1812), Gallica | https://gallica.bnf.fr/ark:/12148/bpt6k9642710s.texteImage |
| P26 | Sotheby's 2010, lot 121, sphère mouvante d'Antide Janvier (1774, réparée en 1825) | https://www.sothebys.com/en/auctions/ecatalogue/2010/important-french-furniture-sculptures-and-works-of-art-pf1021/lot.121.html |
| P27 | Wikipedia, *Antide Janvier* | https://en.wikipedia.org/wiki/Antide_Janvier |
| P28 | J. Lefort, *L'horloge astronomique de la cathédrale de Strasbourg* (1993) | https://bibnum.publimath.fr/IST/IST93039.pdf |
| P29 | Astro Aspach, *Les horloges astronomiques de la cathédrale de Strasbourg* | http://astroaspach.fr/astroaspachV2/wp-content/uploads/2015/12/les-trois-horloges-astronomiques-de-la-Cathedrale-de-Strasbourg.pdf |
| P30 | Cathédrale de Strasbourg, *Horloge astronomique* | https://www.cathedrale-strasbourg.fr/horloge-astronomique |
| P31 | Wikipédia, *Horloge astronomique de Strasbourg* | https://fr.wikipedia.org/wiki/Horloge_astronomique_de_Strasbourg |
| P32 | Wikipedia, *Strasbourg astronomical clock* | https://en.wikipedia.org/wiki/Strasbourg_astronomical_clock |
| P33 | D. Roegel, *Le comput ecclésiastique de Schwilgué (1821)* | https://comput1821.github.io/ |
| P34 | Wikipedia, *Jens Olsen's World Clock* | https://en.wikipedia.org/wiki/Jens_Olsen%27s_World_Clock |
| P35 | Wikipedia (da), *Jens Olsens Verdensur* | https://da.wikipedia.org/wiki/Jens_Olsens_Verdensur |
| P36 | TIME, « Science: Master Clock », 23 janvier 1956 | https://time.com/archive/6799377/science-master-clock/ |
| P37 | Wikipedia, *Rasmus Sørnes* | https://en.wikipedia.org/wiki/Rasmus_S%C3%B8rnes |
| P38 | *Have you seen this clock?*, Clock No. 3 | https://www.haveyouseenthisclock.com/clock3.shtml |
| P39 | NRK, *Norwegian farmer's son Rasmus Sørnes…* | https://www.nrk.no/kultur/xl/norwegian-farmer_s-son-rasmus-sornes-made-some-of-the-world_s-most-complicated-astronomical-clocks-1.16193271 |
| P40 | WatchesBySJX, *In-Depth: Patek Philippe Calibre 89* (2026) | https://watchesbysjx.com/2026/06/in-depth-patek-philippe-calibre-89.html |
| P41 | Revolution, *From Here to Eternity: The Secular Perpetual Calendar* | https://revolutionwatch.com/from-here-to-eternity-the-secular-perpetual-calendar/ |
| P42 | Ulysse Nardin, *The astronomical complications* | https://www.ulysse-nardin.com/about-us/unvrs/the-astronomical-complications |
| P43 | Europa Star, *Ulysse Nardin – Astrolabe « Galileo Galilei »* | https://www.europastar.com/swisstime/1004102957-ulysse-nardin-astrolabe-galileo-galilei.html |
| P44 | Italian Watch Spotter, *Ulysse Nardin Astrolabium Galileo Galilei* | https://italianwatchspotter.com/ulysse-nardin-astrolabium/?lang=en |
| P45 | Europa Star, *Ulysse Nardin « Planetarium Copernicus »* | https://www.europastar.com/swisstime/1004104668-ulysse-nardin-plantarium-copernicus.html |
| P46 | Antiquorum, *Tellurium Johannes Kepler*, réf. 871-99 | https://catalog.antiquorum.swiss/en/lots/ulysse-nardin-lot-222-307 |
| P47 | Wikipedia, *Ludwig Oechslin* | https://en.wikipedia.org/wiki/Ludwig_Oechslin |
| P48 | Christiaan van der Klaauw, *CVDK Grand Planetarium Eccentric* | https://www.klaauw.com/eng/cvdk-grand-planetarium-eccentric-manufacture-ckgp1104 |
| P49 | Monochrome Watches, *CVDK Grand Planetarium Eccentric* | https://monochrome-watches.com/christiaan-van-der-klaauw-grand-planetarium-eccentric-only-mechanical-planetarium-watch-in-the-world-displaying-all-8-planets-review-specs-price/ |
| P50 | aBlogtoWatch, *Hublot Antikythera Calibre 2033-CH01* | https://www.ablogtowatch.com/hublot-antikythera-calibre-2033-ch01-watch-is-a-re-imagined-greek-masterpiece/ |
| P51 | Long Now, *Long Now's Orrery Prototype for the 10,000 Year Clock* | https://longnow.org/ideas/orrery-prototype-long-now-interval/ |
| P52 | Wikipedia, *Clock of the Long Now* | https://en.wikipedia.org/wiki/Clock_of_the_Long_Now |
| P53 | W. D. Hillis, brevet US 6 249 485 B1, *Bit serial mechanical adder* | https://patents.google.com/patent/US6249485 |
| P54 | WatchesBySJX, *Hands On: Raúl Pagès RP2* | https://watchesbysjx.com/2025/03/raul-pages-rp2-review.html |
| P55 | Wikipedia, *Orbital resonance* (résonance de Laplace) | https://en.wikipedia.org/wiki/Orbital_resonance |
| P56 | NASA NSSDC, *Jovian Satellite Fact Sheet* | https://nssdc.gsfc.nasa.gov/planetary/factsheet/joviansatfact.html |
| P57 | Wikipedia, *Rømer's determination of the speed of light* | https://en.wikipedia.org/wiki/R%C3%B8mer%27s_determination_of_the_speed_of_light |
| P58 | Wikipedia, *Axial precession* | https://en.wikipedia.org/wiki/Axial_precession |
| P59 | Wikipedia, *Jovilabe* | https://en.wikipedia.org/wiki/Jovilabe |

Données orbitales utilisées par [C13] et [C14] : JPL, *Approximate Positions of the Planets*, table 1 (1800–2050), https://ssd.jpl.nasa.gov/planets/approx_pos.html
