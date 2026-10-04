# Anticythère 2.0 — constantes astronomiques modernes

*Fichier généré par `v2/tools/build_constants.py` (ne pas éditer à la main). Données : `constants.json`. Sources consultées le 2026-10-03.*

## Conventions

- **Époque** : J2000.0 = JD 2451545,0 **TT** (1er janvier 2000, 12 h TT). **T** = siècles juliens de 36 525 jours depuis J2000.0 ; Simon et al. (1994) utilisent *t* en millénaires.
- **Unités** : degrés (°), secondes d'arc (″), jours de 86 400 s, unités astronomiques (au).
- **Deux repères** : *sidéral* = écliptique et équinoxe **fixes** de J2000 (c'est ce que doit reproduire l'orrery du dessus) ; *tropique* = équinoxe **de la date** (c'est ce que lit un zodiaque attaché à l'équinoxe, comme sur le cadran avant). La différence entre les deux est la précession générale p_A ≈ 1,397° par siècle — **plus que l'objectif de 1°/siècle** : il faut donc soit tout entraîner en sidéral et faire tourner lentement l'anneau zodiacal (1 tour en 25 772 ans), soit ajouter p_A à chaque rapport.
- **Temps** : les éphémérides sont en TT ; la manivelle compte des jours solaires moyens (UT1). ΔT = TT − UT1 ≈ 69,1 s en 2026 (USNO) : 0,6′ sur la Lune, négligeable.
- **Vérifications croisées** : 255 comparaisons entre au moins deux sources ; **238 conformes**, **17 écarts expliqués**, **0 à surveiller** (liste complète en fin de document).

## 0. Synthèse pour la conception

- **Moyens mouvements planétaires** : viser les taux DE441 ajustés sur 2000–2100 (§ 2.2) ; JPL table 1 est équivalente à < 0,1°/siècle près. Les taux séculaires classiques (VSOP87/Simon, Meeus) sont faux de 0,46°/siècle pour Saturne sur ce siècle (grande inégalité).
- **Deux repères** : l'orrery (dessus) tourne en sidéral ; le zodiaque (avant) lit des longitudes tropiques. Écart = précession 1,397°/siècle, à mécaniser (anneau zodiacal : 1 tour en 25 772 ans) ou à intégrer aux rapports.
- **Lune** (objectif ~0,5°) : équation du centre + évection + variation + équation annuelle → erreur max 0,46° ; + réduction à l'écliptique → 0,35°. Latitude : 5,128 sin F + 3 termes → 0,18°.
- **Équation du centre des planètes** : tenon-mortaise (k = 2e) suffisant sauf Mars (0,45°) et Mercure (2,79°) ; l'équant ramène Mars à 0,15° mais laisse Mercure à 0,89°.
- **Temps** : jour sidéral moyen 86 164,0905 s (366,2422 jours sidéraux par année tropique) ; équation du temps = 9,86 min × (½ an) + 7,66 min × (1 an) + termes < 0,7 min ; calendrier grégorien 146 097 j / 400 ans = 20 871 semaines exactes.
- **Éclipses** : Saros 223 lunaisons (6585,321 j) ≈ 242 mois draconitiques ≈ 239 anomalistiques ; γ ≈ 5,22 sin F rayons terrestres donne magnitude et hémisphère (signe de γ).
- **Satellites galiléens** : n_Io − 3 n_Europe + 2 n_Ganymède = 0 (à 1e-9 °/j près) ; périodes sidérales 1,769138 / 3,551181 / 7,154553 / 16,689018 j ; conjonctions Io–Europe tous les 3,5255 j, ligne des conjonctions en rotation rétrograde en 486,8 j.
- **Hors de portée / négligeable** (§ 7) : nutation (17″), aberration (20″), ΔT (~1 min), libration de Laplace (< 0,07°), perturbations planétaires à courte période (jusqu'à 0,23° pour Saturne).

## 1. Terre : années, précession, obliquité, rotation

| Grandeur | Valeur | Source principale | Contrôle |
|---|---|---|---|
| Année tropique moyenne (J2000) | 365,2421896698 j (= 365 j 5 h 48 min 45,19 s) − 6,15×10⁻⁶ T | Laskar 1986 via McCarthy & Seidelmann 2009 | Simon 1994 (taux de date) : 365,2421904021 ; Simon + p_A IAU 2006 : 365,2421904692 |
| Année de l'équinoxe de mars (2000) | 365,242374 j | Meeus & Savoie 1992 | — (c'est elle qui compte pour le calendrier) |
| Année sidérale | 365,256363004 j | Simon 1994 (λ J2000) | Wikipedia « Year » 365,256363004 ; NSSDC 365,256 |
| Année anomalistique | 365,259635842 j | IERS 2010 (l′) | Simon (λ − ϖ) 365,259635842 ; Wikipedia 365,259636 |
| Année draconitique (des éclipses) | 346,62007588 j | IERS 2010 (F − D) | Wikipedia 346,620075883 |
| Année grégorienne | 365,2425 j = 146097/400 | règle 4/100/400 | 146 097 j = 20 871 semaines exactement |
| Précession générale p_A (IAU 2006) | 5028,796195″/siècle + 1,1054348″ T² = 50,288″/an | Capitaine et al. 2003 | ψ_A − χ_A cos ε₀ (IERS) = 5028,7962 ; Simon 1994 : 5028,82 ; IAU 1976 : 5029,0966 |
| Période de précession | 25771,6 ans | 1 296 000″ / 50,28796″ | Wikipedia 25 771,6 ans |
| Obliquité moyenne ε₀ (IAU 2006) | 84 381,406″ = 23° 26′ 21,406″ = 23,43927944° | IERS 2010 éq. 5.40 | IAU 1980 (Meeus) : 84 381,448″ (écart 0,042″) |
| Variation de l'obliquité | −46,836769″/siècle (−0,01301°/siècle) | IERS 2010 | IAU 1980 : −46,8150″ ; long terme 22,04°–24,50°, période 41 040 ans |
| Jour sidéral moyen (équinoxe) | 86164,0905 s = 23 h 56 min 4,0905 s | IERS (ERA + précession en AR) | Wikipedia 86 164,0905 s |
| Jour stellaire (ERA, étoiles fixes) | 86164,0989 s | IERS 2010 éq. 5.14 | +8,4 ms vs jour sidéral |
| Rapport temps sidéral / solaire moyen | 1,002737909345 | IERS 2010 | Meeus (Aoki 1982) 1,00273790935 |
| Jours sidéraux par année tropique | 366,2421897 | exact (un tour de plus) | — |

**Calendrier grégorien.** Bissextile si divisible par 4, sauf les siècles non divisibles par 400 (97 bissextiles en 400 ans). Dérive : 1 jour en 3222 ans par rapport à l'année tropique moyenne, 1 jour en 7937 ans par rapport à l'année de l'équinoxe de mars (Wikipedia donne ~3 236 ans avec 365,2422). Jour de la semaine : floor(JD + 1,5) mod 7 (0 = dimanche) ; le 1er janvier 2000 était un samedi.

**Équation du temps** (E = temps solaire vrai − temps solaire moyen ; formule de Smart reprise par Meeus 28.3) :

E = y sin 2L₀ − 2e sin M + 4ey sin M cos 2L₀ − ½y² sin 4L₀ − 5/4 e² sin 2M, avec y = tan²(ε/2).

| Terme | Amplitude | Période |
|---|---|---|
| y sin 2L₀ (obliquité) | 9,863 min | ½ année |
| −2e sin M (excentricité) | 7,659 min | année anomalistique |
| 4ey sin M cos 2L₀ | 0,659 min | mixte |
| −½y² sin 4L₀ | 0,212 min | ¼ année |
| −5/4 e² sin 2M | 0,080 min | ½ année anomalistique |

Extrêmes 2026 (formule ci-dessus) : −14,22 min le 2026-02-11 et +16,49 min le 2026-11-03 (Wikipedia : −14 min 15 s le 11 février, +16 min 25 s le 3 novembre). Les deux termes principaux (Wikipedia : 7,66 et 9,87 min) se mécanisent avec deux cames ou deux tenons-mortaises (1 tour/an et 2 tours/an). La courbe dérive lentement : le périhélie avance de 1,72°/siècle par rapport à l'équinoxe.

## 2. Planètes : éléments, moyens mouvements, périodes

Quatre jeux de taux, qui ne se valent pas pour le même usage :

- **DE441 ajusté sur 2000–2100** (JPL Horizons, éléments osculateurs, ajustement linéaire de L = Ω + ω + M ; barycentriques pour Jupiter–Pluton afin d'éliminer l'oscillation du Soleil autour du barycentre) : **taux recommandé pour la machine** (fenêtre visée 2000–2100).
- **JPL table 1** (Standish & Williams) : ajustement *local* 1800–2050 ; éléments de départ (a, e, i, ϖ, Ω) et contrôle principal du taux.
- **JPL tables 2a + 2b** : ajustement 3000 av. J.-C. – 3000 apr. J.-C., avec un terme périodique en M pour Jupiter–Neptune (grandes inégalités).
- **Simon et al. 1994** (VSOP87/JASON84) : éléments moyens *séculaires* ; ils ne contiennent pas les grandes inégalités.

### 2.1 Éléments J2000 (JPL table 1, repère J2000) et taux par siècle

| Planète | a (au) | e | i (°) | L (°) | ϖ (°) | Ω (°) | L̇ (°/siècle) | ϖ̇ (°/siècle) | Ω̇ (°/siècle) |
|---|---|---|---|---|---|---|---|---|---|
| Mercure | 0,38709927 | 0,20563593 | 7,00497902 | 252,25032350 | 77,45779628 | 48,33076593 | 149472,67411175 | 0,16047689 | −0,12534081 |
| Vénus | 0,72333566 | 0,00677672 | 3,39467605 | 181,97909950 | 131,60246718 | 76,67984255 | 58517,81538729 | 0,00268329 | −0,27769418 |
| Terre (barycentre Terre-Lune) | 1,00000261 | 0,01671123 | −0,00001531 | 100,46457166 | 102,93768193 | 0,0 | 35999,37244981 | 0,32327364 | 0,0 |
| Mars | 1,52371034 | 0,09339410 | 1,84969142 | −4,55343205 | −23,94362959 | 49,55953891 | 19140,30268499 | 0,44441088 | −0,29257343 |
| Jupiter | 5,20288700 | 0,04838624 | 1,30439695 | 34,39644051 | 14,72847983 | 100,47390909 | 3034,74612775 | 0,21252668 | 0,20469106 |
| Saturne | 9,53667594 | 0,05386179 | 2,48599187 | 49,95424423 | 92,59887831 | 113,66242448 | 1222,49362201 | −0,41897216 | −0,28867794 |
| Uranus | 19,18916464 | 0,04725744 | 0,77263783 | 313,23810451 | 170,95427630 | 74,01692503 | 428,48202785 | 0,40805281 | 0,04240589 |
| Neptune | 30,06992276 | 0,00859048 | 1,77004347 | −55,12002969 | 44,96476227 | 131,78422574 | 218,45945325 | −0,32241464 | −0,00508664 |
| Pluton (optionnel) | 39,48211675 | 0,24882730 | 17,14001206 | 238,92903833 | 224,06891629 | 110,30393684 | 145,20780515 | −0,04062942 | −0,01183482 |

*ė, i̇, ȧ : voir `constants.json`. Pluton : table JPL archivée (2019), retirée depuis des tables actuelles.*

### 2.2 Moyens mouvements recommandés pour les rapports d'engrenages

Base : DE441 ajusté 2000–2100 (repère J2000 = sidéral). Tropique = sidéral + p_A (IAU 2006). « Précision relative » = erreur relative de rapport qui produit 1° d'erreur de longitude moyenne par siècle.

| Planète | °/siècle (sidéral) | tours/jour (sidéral) | tours/année tropique (sidéral, orrery) | tours/année tropique (tropique, zodiaque) | Période sidérale (j) | Période synodique (j) | Précision relative pour 1°/siècle |
|---|---|---|---|---|---|---|---|
| Mercure | 149472,67473 | 0,011367607782 | 4,15192995762 | 4,15196875923 | 87,9693 | 115,877 | 6,7e-06 |
| Vénus | 58517,81523 | 0,00445036240254 | 1,62546010873 | 1,62549891034 | 224,7008 | 583,921 | 1,7e-05 |
| Terre (barycentre Terre-Lune) | 35999,37287 | 0,00273780309265 | 0,999961196446 | 0,999999998056 | 365,2564 | — | 2,8e-05 |
| Mars | 19140,30204 | 0,00145564697268 | 0,531663687689 | 0,531702489299 | 686,9798 | 779,936 | 5,2e-05 |
| Jupiter | 3034,72276 | 0,000230794947267 | 0,0842960519045 | 0,0843348535145 | 4332,8505 | 398,882 | 0,00033 |
| Saturne | 1222,57423 | 9,297849465e-05 | 0,0339596689782 | 0,0339984705882 | 10755,1752 | 378,097 | 0,00082 |
| Uranus | 428,55871 | 3,25924943733e-05 | 0,0119041540117 | 0,0119429556218 | 30681,9106 | 369,657 | 0,0023 |
| Neptune | 218,42764 | 1,66117301751e-05 | 0,00606730470336 | 0,0061061063134 | 60198,4254 | 367,486 | 0,0046 |
| Pluton | 145,16465 | 1,10399766929e-05 | 0,00403226526123 | 0,00407106687127 | 90579,9014 | 366,735 | 0,0069 |

### 2.3 Quel taux viser ? (écart entre jeux d'éléments, °/siècle, repère J2000)

| Planète | DE441 2000–2100 (recommandé) | Incertitude d'ajustement | JPL T1 (1800–2050) | JPL 2a+2b sur 2000–2100 | Simon 1994 séculaire | T1 − DE441 | Séculaire − DE441 | Résidu non linéaire 2000–2100 (°) |
|---|---|---|---|---|---|---|---|---|
| Mercure | 149472,6747 | ≤ 0,005 | 149472,6741 | 149472,6749 | 149472,6746 | −0,001 | −0,000 | 0,000 |
| Vénus | 58517,8152 | ≤ 0,005 | 58517,8154 | 58517,8156 | 58517,8157 | 0,000 | 0,000 | 0,000 |
| Terre (barycentre Terre-Lune) | 35999,3729 | ≤ 0,005 | 35999,3724 | 35999,3731 | 35999,3729 | −0,000 | −0,000 | 0,000 |
| Mars | 19140,3020 | ≤ 0,005 | 19140,3027 | 19140,2993 | 19140,2993 | 0,001 | −0,003 | 0,000 |
| Jupiter | 3034,7228 | ±0,003 | 3034,7461 | 3034,6676 | 3034,9057 | 0,023 | 0,183 | 0,003 |
| Saturne | 1222,5742 | ±0,044 | 1222,4936 | 1222,6903 | 1222,1138 | −0,081 | −0,460 | 0,008 |
| Uranus | 428,5587 | ±0,035 | 428,4820 | 428,5281 | 428,4670 | −0,077 | −0,092 | 0,002 |
| Neptune | 218,4276 | ±0,047 | 218,4595 | 218,4451 | 218,4862 | 0,032 | 0,059 | 0,001 |

**Lecture.** JPL table 1 et DE441 (2000–2100) s'accordent à mieux que 0,08°/siècle pour toutes les planètes : l'un ou l'autre convient pour l'objectif de 1°/siècle. Les taux *séculaires* (Simon 1994) s'en écartent de +0,18°/siècle pour Jupiter et de −0,46°/siècle pour Saturne : sur 2000–2100 la *grande inégalité* Jupiter–Saturne (période ~900 ans) ralentit Jupiter et accélère Saturne. Ces écarts restent sous l'objectif mais en consomment près de la moitié pour Saturne : il faut viser le taux *local*. « Incertitude d'ajustement » = écart entre éléments osculateurs héliocentriques et barycentriques (Jupiter–Pluton ; ≤ 0,005°/siècle estimé pour les planètes intérieures, dont l'ajustement a un résidu RMS ≤ 0,006°) ; « résidu non linéaire » = ce qu'aucun rapport constant ne peut suivre sur le siècle (négligeable).

| Grande inégalité (JPL 2b) | Amplitude (°) | Période (ans) | Pente max (°/siècle) |
|---|---|---|---|
| Jupiter | 0,361 | 939 | 0,242 |
| Saturne | 0,883 | 939 | 0,591 |
| Uranus | 0,993 | 4694 | 0,133 |
| Neptune | 0,691 | 4694 | 0,092 |

*Schlyter donne pour le seul terme 2M_J − 5M_S : 0,332° (Jupiter) et 0,812° (Saturne), période 918 ans.*

### 2.4 Équation du centre (Kepler) et ce qu'un mécanisme en fait

Série de Kepler : ν − M = c₁ sin M + c₂ sin 2M + c₃ sin 3M + … avec c₁ = 2e − e³/4, c₂ = 5/4 e², c₃ = 13/12 e³. Le tenon-mortaise d'Anticythère (cercle excentrique vu d'un point décalé, k = 2e) donne k sin M + k²/2 sin 2M + k³/3 sin 3M : le 2ᵉ harmonique vaut 2e² au lieu de 1,25 e². L'équant « bissecté » de Ptolémée (centre décalé de e, point d'équant à 2e) est exact au 2ᵉ ordre en e.

| Planète | e | Max ν − M (°) | c₁ (°) | c₂ (°) | Erreur max tenon-mortaise k=2e (°) | Erreur max équant (°) | Erreur max 1er harmonique seul (°) |
|---|---|---|---|---|---|---|---|
| Mercure | 0,20563593 | 23,6809 | 23,4407 | 2,9816 | 2,7900 | 0,8949 | 3,3390 |
| Vénus | 0,00677672 | 0,7766 | 0,7766 | 0,0033 | 0,0020 | 0,0007 | 0,0033 |
| Terre (barycentre Terre-Lune) | 0,01671123 | 1,9150 | 1,9149 | 0,0200 | 0,0124 | 0,0041 | 0,0202 |
| Mars | 0,09339410 | 10,7129 | 10,6905 | 0,6227 | 0,4463 | 0,1493 | 0,6529 |
| Jupiter | 0,04838624 | 5,5461 | 5,5430 | 0,1675 | 0,1098 | 0,0368 | 0,1716 |
| Saturne | 0,05386179 | 6,1742 | 6,1699 | 0,2076 | 0,1374 | 0,0460 | 0,2131 |
| Uranus | 0,04725744 | 5,4167 | 5,4138 | 0,1598 | 0,1045 | 0,0350 | 0,1636 |
| Neptune | 0,00859048 | 0,9844 | 0,9844 | 0,0053 | 0,0032 | 0,0011 | 0,0053 |
| Pluton | 0,24882730 | 28,7225 | 28,2957 | 4,3337 | 4,5880 | 1,4170 | 4,9920 |

**Conséquence.** Le tenon-mortaise simple (k = 2e) reste sous 0,15° pour Vénus, Terre (barycentre Terre-Lune), Jupiter, Saturne, Uranus, Neptune. Pour **Mars** il laisse 0,45° (équant : 0,15°) et pour **Mercure** 2,79° (équant : 0,89°) : Mercure demande un mécanisme plus fidèle que l'équant (3ᵉ harmonique, ou ellipse réelle). Ce sont des erreurs *héliocentriques* : vues de la Terre elles sont amplifiées ou réduites selon le rapport des distances (rapport r/Δ : Mars à l'opposition ×2,5 à ×3,6 ; Mercure ×0,2 à ×0,9).

## 3. Lune

### 3.1 Arguments moyens (Meeus ch. 47, équinoxe de la date ; T en siècles juliens)

| Argument | Valeur à J2000 (°) | Taux (°/siècle) | Contrôle IERS 2010 / Simon 1994 (°/siècle) |
|---|---|---|---|
| L′ longitude moyenne | 218,3164477 | 481267,88123421 | 481267,8811957 |
| D élongation | 297,8501921 | 445267,1114034 | 445267,1114469 |
| M anomalie moyenne du Soleil | 357,5291092 | 35999,0502909 | 35999,0502911 |
| M′ anomalie moyenne de la Lune | 134,9633964 | 477198,8675055 | 477198,8675605 |
| F argument de latitude | 93,2720950 | 483202,0175233 | 483202,0174577 |
| Ω nœud ascendant | 125,0445479 | −1934,1362891 | −1934,1362620 |
| ϖ périgée | 83,3532465 | 4069,0137287 | 4069,0136352 |

### 3.2 Mois et périodes

| Période | Simon 1994 / IERS 2010 (j) | Chapront et al. 2002 (j) | Autre contrôle |
|---|---|---|---|
| Mois sidéral | 27,321661551 | 27,321661554 + 2,17e-07 T | NSSDC 27,3217 |
| Mois tropique | 27,321582249 | 27,321582252 + 1,82e-07 T | IERS table 5.1a : 27,321582 |
| Mois synodique | 29,530588858 | 29,530588861 + 2,52e-07 T | Meeus 49.1 : 29,530588861 |
| Mois anomalistique | 27,554549882 | 27,554549886 − 1,01e-06 T | NASA : 27,554550 |
| Mois draconitique | 27,212220821 | 27,212220815 + 4,14e-07 T | IERS table 5.1a : 27,212221 |
| Révolution des nœuds (tropique) | 6798,3835 (18,6134 ans) | — | IERS 6798,3837 |
| Révolution des nœuds (sidérale) | 6793,4770 | — | NASA 6793,48 |
| Révolution du périgée (tropique) | 3231,4957 (8,8475 ans) | — | IERS 3231,4956 |
| Révolution du périgée (sidérale) | 3232,6054 | — | NASA dit 3231,6 « par rapport aux étoiles » : c'est en fait la valeur tropique |
| Période de l'évection (2D − M′) | 31,8119 | — | — |

### 3.3 Inégalités périodiques en longitude (degrés)

| Terme | Argument | Meeus 47.A | Brown 1919 | Almanach | Schlyter | Période de l'argument (j) |
|---|---|---|---|---|---|---|
| équation du centre | M′ | 6,288774 | 6,2886 | 6,29 | — | 27,555 |
| évection | 2D − M′ | 1,274027 | 1,2739 | 1,27 | 1,274 | 31,812 |
| variation | 2D | 0,658314 | 0,6583 | 0,66 | 0,658 | 14,765 |
| équation du centre (2ᵉ harmonique) | 2M′ | 0,213618 | 0,2136 | 0,21 | — | 13,777 |
| équation annuelle | M | −0,185116 | −0,1856 | −0,19 | −0,186 | 365,260 |
| réduction à l'écliptique | 2F | −0,114332 | −0,1144 | −0,11 | — | 13,606 |
| terme 2D − 2M′ | 2D − 2M′ | 0,058793 | — | — | 0,059 | 205,892 |
| terme 2D − M − M′ | 2D − M − M′ | 0,057066 | — | — | 0,057 | 34,847 |
| terme 2D + M′ | 2D + M′ | 0,053322 | — | — | 0,053 | 9,614 |
| terme 2D − M | 2D − M | 0,045758 | — | — | 0,046 | 15,387 |
| terme M − M′ | M − M′ | −0,040923 | — | — | −0,041 | 29,803 |
| inégalité parallactique | D | −0,034720 | −0,0347 | — | −0,035 | 29,531 |
| terme M + M′ | M + M′ | −0,030383 | — | — | −0,031 | 25,622 |

*Les termes en M sont multipliés par E = 1 − 0,002516 T (excentricité terrestre décroissante).*

### 3.4 Latitude (degrés)

| Terme | Argument | Meeus 47.B | Almanach | Schlyter |
|---|---|---|---|---|
| terme principal | F | 5,128122 | 5,13 | — |
| terme M′ + F | M′ + F | 0,280602 | 0,28 | — |
| terme M′ − F | M′ − F | 0,277693 | 0,28 | — |
| évection en latitude | 2D − F | 0,173237 | 0,17 | 0,173 |
| terme 2D − M′ + F | 2D − M′ + F | 0,055413 | — | 0,055 |
| terme 2D − M′ − F | 2D − M′ − F | 0,046271 | — | 0,046 |
| terme 2D + F | 2D + F | 0,032573 | — | 0,033 |
| terme 2M′ + F | 2M′ + F | 0,017198 | — | 0,017 |

**Inclinaison : trois valeurs à ne pas confondre.** 5,128° est le coefficient de sin F (à utiliser pour β) ; 5,145° est l'inclinaison moyenne classique (NASA) ; 5,157° est la moyenne de l'inclinaison osculatrice (Simon 1994). L'inclinaison réelle oscille entre ~5,0° et 5,3° (période 173 j).

### 3.5 Budget d'erreur de la longitude lunaire (2000–2100)

Référence : série complète de Meeus 47.A (60 termes + 3 additifs, précision ~10″). On retire progressivement des termes et on mesure l'erreur restante (pas de 0,05 j sur 100 ans).

| Modèle mécanisé | Erreur max (°) | Erreur RMS (°) |
|---|---|---|
| longitude moyenne seule | 8,030 | 4,570 |
| + équation du centre (6,289 sin M′) | 2,560 | 1,040 |
| + 2ᵉ harmonique (0,214 sin 2M′) | 2,500 | 1,030 |
| + évection (1,274) | 1,230 | 0,499 |
| + variation (0,658) | 0,626 | 0,179 |
| + équation annuelle (0,186) | 0,461 | 0,122 |
| + réduction à l'écliptique (0,114) | 0,347 | 0,091 |
| + 4 termes suivants (2D − 2M′, 2D − M − M′, 2D + M′, 2D − M) | 0,179 | 0,050 |
| + M − M′, inégalité parallactique, M + M′ | 0,098 | 0,023 |
| tenon-mortaise (k = 6,2888°) + évection + variation + annuelle + réduction | 0,415 | 0,130 |

| Latitude | Erreur max (°) | Erreur RMS (°) |
|---|---|---|
| 5,128 sin F seul | 0,810 | 0,310 |
| + M′ + F, M′ − F | 0,352 | 0,136 |
| + 2D − F (évection en latitude) | 0,179 | 0,059 |

**Lecture.** Avec équation du centre (2 harmoniques) + évection + variation + équation annuelle, l'erreur reste sous 0,46° (RMS 0,12°) : l'objectif « ~0,5° » est tenu. La réduction à l'écliptique la ramène à 0,35°, les quatre termes suivants à 0,18°. Réaliser l'équation du centre par un tenon-mortaise (comme à Anticythère) au lieu des deux harmoniques exacts coûte 0,07° d'erreur max (0,35 → 0,41°), à cause de son 2ᵉ harmonique trop fort (0,345° au lieu de 0,214°).

## 4. Éclipses

| Cycle | Lunaisons | Jours | Mois draconitiques | Mois anomalistiques | Années tropiques | Décalage géographique (°, + = vers l'ouest) |
|---|---|---|---|---|---|---|
| Saros | 223 | 6585,3213 | 241,999 | 238,992 | 18,0300 | 115,7 |
| Inex | 358 | 10571,9508 | 388,500 | 383,674 | 28,9450 | −17,7 |
| Exeligmos | 669 | 19755,9639 | 725,996 | 716,976 | 54,0900 | −13,0 |
| Metonic | 235 | 6939,6884 | 255,021 | 251,853 | 19,0002 | −112,2 |
| Tritos | 135 | 3986,6295 | 146,501 | 144,681 | 10,9150 | −133,4 |
| Callippic | 940 | 27758,7535 | 1020,084 | 1007,411 | 76,0010 | −88,7 |

Contrôles : Saros 6585,32 j (Wikipedia), 6585,3223 j (page NASA : coquille, 223 × 29,530589 = 6585,3213) ; 242 mois draconitiques = 6585,3575 j et 239 anomalistiques = 6585,5375 j (NASA) ; Inex 10 571,9509 j (NASA). Année draconitique : 346,620076 j ; saison d'éclipses tous les 173,31 j.

**Limites écliptiques** (distance Soleil–nœud à la syzygie) :

| Type | Min (°) | Max (°) | Source |
|---|---|---|---|
| Éclipse de Soleil (partielle) | 15,39 | 18,59 | NASA (Espenak) ; Wikipedia « 15 à 18° » ; Meeus (via Holmes) 18° 24′ |
| Éclipse de Soleil centrale | ~10 | ~12 | Wikipedia (Littmann, Espenak & Willcox) |
| Éclipse de Lune (ombre) | 9,6 | 12,2 | calcul géométrique ; Meeus (via Holmes) 12° 08′ |
| Éclipse de Lune pénombrale | 15,3 | 17,1 | NASA (page des éclipses lunaires) |

Estimation géométrique (sin Δλ = tan β_lim / tan i) : Soleil 15,32–18,35°, Lune (ombre) 9,60–12,23° — cohérent avec les sources.

**Magnitude et hémisphère (Meeus ch. 54).** γ (distance de l'axe de l'ombre au centre de la Terre, en rayons terrestres) ≈ 5,22 sin F + petits termes (Q = 5,2207 − 0,3299 cos M′ ; P = 0,207 sin M − 0,0392 sin M′). Pas d'éclipse si |sin F| > 0,36. Soleil : éclipse centrale si |γ| < 0,9972 ; partielle si |γ| < 1,5433 + u ; magnitude partielle = (1,5433 + u − |γ|)/(0,5461 + 2u). Lune : magnitude d'ombre = (1,0128 − u − |γ|)/0,5450 ; pénombrale = (1,5573 + u − |γ|)/0,5450 (u ≈ 0,0059 + 0,0046 cos M − 0,0182 cos M′). **Signe de γ (donc de sin F près du nœud) = hémisphère** : γ > 0, ombre au nord pour une éclipse de Soleil (Wikipedia « Gamma »). C'est mécanisable : sin F s'obtient par une manivelle–coulisse sur l'arbre draconitique.

Chaque Saros décale l'éclipse de ~8 h, soit ~116° vers l'ouest ; l'Exeligmos (3 Saros) la ramène presque à la même longitude.

## 5. Satellites galiléens

| Satellite | n (°/j, Lieske E5) | Période sidérale (j) | NSSDC (j) | Période synodique / Soleil (j) | P du JPL (j) — anomalistique | Périjove (ans) |
|---|---|---|---|---|---|---|
| Io | 203,48895579 | 1,769138 | 1,769138 | 1,769860 | 1,762732 | 1,333 |
| Europe | 101,374724735 | 3,551181 | 3,551181 | 3,554094 | 3,525463 | 1,394 |
| Ganymède | 50,317609207 | 7,154553 | 7,154553 | 7,166386 | 7,155588 | 68,301 |
| Callisto | 21,571071177 | 16,689018 | 16,689017 | 16,753549 | 16,690440 | 277,921 |

**Résonance de Laplace** : n_Io − 3 n_Europe + 2 n_Ganymède = −1e-09 °/j (E5) ; Φ_L = λ_Io − 3λ_Europe + 2λ_Ganymède = 180° ± libration. n_Io − 2 n_Europe = n_Europe − 2 n_Ganymède = 0,739506 °/j : la ligne des conjonctions Io–Europe rétrograde en 486,8 j (conjonctions Io–Europe tous les 3,5255 j, Europe–Ganymède tous les 7,0509 j ; jamais de triple conjonction). Rapports de périodes : Europe/Io = 2,00729, Ganymède/Europe = 2,01470, Callisto/Ganymède = 2,33264 (hors résonance). Libration : période ~2071 j (Lieske 1998, cité par Celletti et al. 2021), amplitude 0,03° (Sinclair 1975, Wikipedia) à 0,066° (Lieske, cité de seconde main) — **désaccord entre sources, et de toute façon hors de portée d'un engrenage**.

**Attention :** la colonne « P » des éléments moyens du JPL (Io 1,762732 j, Europe 3,525463 j) n'est *pas* la période sidérale : c'est la période de l'anomalie moyenne d'une ellipse en précession rapide (périjove forcé d'Io et d'Europe : 1,33 et 1,39 an). Les périodes sidérales sont 1,769138 et 3,551181 j.

**Vu de la Terre** : temps de lumière 32,7–53,8 min (effet Rømer : ~16,6 min d'écart entre opposition et conjonction) ; l'angle Soleil–Terre vu de Jupiter atteint 11,8°, ce qui décale les phénomènes d'Io jusqu'à ~1,4 h. Le suiveur héliocentrique → géocentrique de l'orrery peut reproduire ce décalage angulaire, pas le temps de lumière.

## 6. Pluton (optionnel, signalé)

Planète naine depuis 2006, retirée des tables JPL actuelles (valeurs : table JPL archivée de 2019). e = 0,2488, i = 17,14° ; période sidérale (DE441 2000–2100, barycentrique) 90580 j vs 90 560 j (NSSDC) et 90553 j (JPL T1 archivée) ; rapport Pluton/Neptune = 1,5047 (résonance 3:2). Équation du centre max 28,72° : le tenon-mortaise simple ferait 4,6° d'erreur.

## 7. Ce qui est négligeable ou hors de portée

| Effet | Amplitude | ≈ degrés |
|---|---|---|
| nutation en longitude | 17,2'' (18,6 ans) | 0,0048 |
| aberration annuelle | 20,5'' | 0,0057 |
| Terre vs barycentre Terre-Lune | ~6'' sur la longitude du Soleil | 0,0020 |
| DeltaT (TT - UT1) en 2026 | 69 s -> 0,6' sur la Lune | 0,0105 |
| libration de la résonance de Laplace | 0,03-0,066 deg | 0,0660 |
| termes lunaires < 0,03 deg (au-delà des 13 premiers) | somme quadratique ~0,05 deg | 0,0500 |
| écart repère de date vs (J2000 + p_A) pour lambda planétaire | ≤ 2,3''/siècle | 0,0007 |
| perturbations planétaires autres que les grandes inégalités | < 0,06 deg (Jupiter), < 0,23 deg (Saturne) | 0,2300 |

## 8. Écarts entre sources (à retenir)

1. **Saturne : période sidérale 10 759 j ou 10 756 j ?** Le NSSDC (mis à jour en 2025) donne 10 755,70 j, proche du taux *local* (JPL T1 : 10 755,93 j ; DE441 2000–2100 : 10 755,18 j) ; la v1 utilisait l'ancienne valeur NSSDC 10 759,22 j, qui correspond au taux séculaire (Simon 1994 : 10 759,2 j). Les deux sont « justes » : la grande inégalité Jupiter–Saturne fait varier la vitesse apparente.
2. **Meeus table 31.A vs Simon 1994** : +0,277″/siècle sur certaines planètes (Meeus garde la constante de précession IAU 1976). Négligeable.
3. **Repère de date ≠ J2000 + p_A** pour λ planétaire : jusqu'à 2,3″/siècle (Mercure), dû au mouvement de l'écliptique. Négligeable.
4. **Obliquité** : IAU 2006 (84 381,406″) vs IAU 1980 (84 381,448″) : 0,042″, redéfinition de l'écliptique.
5. **Mois lunaires** : Simon 1994 vs Chapront 2002 : < 1×10⁻⁸ j.
6. **Périgée lunaire** : la page NASA donne 3231,6 j « par rapport aux étoiles », mais c'est la période tropique (3231,50 j) ; la période sidérale est 3232,60 j.
7. **Saros** : la page NASA écrit 6585,3223 j au lieu de 6585,3213 j (coquille de 1,4 min).
8. **Inclinaison lunaire** : 5,128° (coefficient de sin F), 5,145° (moyenne classique), 5,157° (moyenne osculatrice).
9. **Libration de Laplace** : 0,03° (Sinclair 1975) vs 0,066° (Lieske, de seconde main) ; période 2071 j.
10. **JPL « P » des satellites** : période anomalistique, pas sidérale (Io −0,36 %, Europe −0,72 %).
11. **Limites écliptiques** : les valeurs publiées dépendent des définitions (nœud vrai/moyen, mouvement pendant l'éclipse, pénombre) : 15,4–18,6° (Soleil), ~9,6–12,2° (Lune, ombre), 15,3–17,1° (Lune, pénombre).
12. **F14 de l'IERS (p_A = 0,02438175 rad/siècle = 5029,10″)** est l'ancienne valeur, gardée seulement comme argument de nutation.

**Valeurs à une seule source (non recoupées)** : année de l'équinoxe de mars 365,242374 j (Meeus & Savoie via Wikipedia) ; plage d'obliquité à long terme 22,04°–24,50° et période 41 040 ans (Laskar via Wikipedia) ; plage d'inclinaison lunaire 5,0°–5,3° (NASA) ; ΔT 2026 = 69,1 s (USNO, prédiction) ; limites d'éclipse centrale ~10–12° (Wikipedia) et pénombrale 15,3–17,1° (NASA) ; amplitude de libration de Laplace (deux valeurs discordantes). Les coefficients γ de Meeus ch. 54 ne sont recoupés que pour les seuils (0,9972 ; ~1,55).

**Régénérer** : `python3.13 v2/tools/fetch_horizons_rates.py` (réseau, JPL Horizons) puis `python3.13 v2/tools/build_constants.py` (hors ligne), avec le Python de Blender.

## 9. Toutes les vérifications croisées

| Statut | Comparaison | A | Source A | B | Source B | A − B | Tolérance | Unité |
|---|---|---|---|---|---|---|---|---|
| ok | p_A IAU 2006 vs psi_A - chi_A cos eps0 (IERS 2010) | 5028,796195 | CAPITAINE2003 | 5028,79619575 | IERS2010 | −7,52e-07 | 0,01 | ''/siècle |
| ok | p_A IAU 2006 vs Simon 1994 (Williams 1991) | 5028,796195 | CAPITAINE2003 | 5028,82 | SIMON1994 | −0,0238 | 0,05 | ''/siècle |
| expliqué | p_A IAU 2006 vs IAU 1976 | 5028,796195 | CAPITAINE2003 | 5029,0966 | SIMON1994 | −0,3 | 0,05 | ''/siècle |
| expliqué | p_A IAU 2006 vs IERS 2010 F14 (Kinoshita & Souchay 1990, rad/siècle) | 5028,796195 | CAPITAINE2003 | 5029,09693972 | IERS2010 | −0,301 | 0,05 | ''/siècle |
| ok | Année tropique moyenne : Laskar (J2000) vs Simon 1994 (taux de date) | 365,24218967 | LASKAR1986_TY | 365,242190402 | SIMON1994 | −7,32e-07 | 2e-06 | jours |
| ok | Année tropique : Laskar vs (taux sidéral Simon + p_A IAU 2006) | 365,24218967 | LASKAR1986_TY | 365,242190469 | SIMON1994+CAPITAINE2003 | −7,99e-07 | 2e-06 | jours |
| ok | Année tropique : Laskar vs JPL table 1 (EMB, ajustement 1800-2050) + p_A | 365,24218967 | LASKAR1986_TY | 365,242194595 | JPL_APPROX | −4,93e-06 | 2e-05 | jours |
| ok | Année sidérale : Simon 1994 vs Wikipedia 'Year' | 365,256363004 | SIMON1994 | 365,256363004 | WIKI_YEAR | 1,93e-10 | 2e-08 | jours |
| ok | Année sidérale : Simon 1994 vs NSSDC (3 décimales) | 365,256363004 | SIMON1994 | 365,256 | NSSDC | 0,000363 | 0,0006 | jours |
| ok | Année anomalistique : l' IERS vs (lambda - varpi) Simon | 365,259635842 | IERS2010 | 365,259635842 | SIMON1994 | 1,1e-10 | 1e-07 | jours |
| ok | Année anomalistique : IERS vs Wikipedia 'Year' | 365,259635842 | IERS2010 | 365,259636 | WIKI_YEAR | −1,58e-07 | 1e-06 | jours |
| ok | Obliquité J2000 : IAU 2006 (84381,406'') vs IAU 1980 (84381,448'') | 84381,406 | IERS2010 | 84381,448 | MEEUS1998 | −0,042 | 0,05 | '' |
| ok | Taux d'obliquité : IAU 2006 vs IAU 1980 | −46,836769 | IERS2010 | −46,815 | MEEUS1998 | −0,0218 | 0,05 | ''/siècle |
| expliqué | Rapport temps sidéral moyen / temps solaire moyen : IERS (ERA + précession en AR) vs Meeus | 1,00273790934 | IERS2010 | 1,00273790935 | MEEUS1998 | −5,03e-12 | 2e-12 | sans unité |
| ok | Jour sidéral moyen (s) : dérivé IERS vs Wikipedia 86164,0905 s | 86164,0905313 | IERS2010 | 86164,0905 | WIKI_SIDEREAL | 3,13e-05 | 0,0001 | s |
| ok | EdT : amplitude du terme d'obliquité (min) -- tan^2(eps/2) vs Wikipedia | 9,86277750523 | MEEUS1998 | 9,863 | WIKI_EOT | −0,000222 | 0,01 | min |
| ok | EdT : amplitude du terme d'excentricité (min) -- 2e vs Wikipedia | 7,6586737687 | MEEUS1998 | 7,659 | WIKI_EOT | −0,000326 | 0,01 | min |
| ok | EdT minimum (min) : formule de Smart 2026 vs Wikipedia (-14 min 15 s, 11 févr.) | −14,2243215593 | MEEUS1998 | −14,25 | WIKI_EOT | 0,0257 | 0,1 | min |
| ok | EdT maximum (min) : formule de Smart 2026 vs Wikipedia (+16 min 25 s, 3 nov.) | 16,4905736448 | MEEUS1998 | 16,4166666667 | WIKI_EOT | 0,0739 | 0,1 | min |
| ok | Cycle grégorien : 146097 j = 20871 semaines exactement | 20871 | WIKI_GREGORIAN | 20871 | WIKI_GREGORIAN | 0 | 0 | semaines |
| ok | Jour de la semaine de JD 2451545.0 (2000-01-01) : 6 = samedi | 6 | MEEUS1998 | 6 | WIKI_GREGORIAN | 0 | 0 | indice (0 = dimanche) |
| ok | Année tropique : Laskar vs (taux EMB DE441 2000-2100 + p_A) | 365,24218967 | LASKAR1986_TY | 365,24219038 | JPL_HORIZONS+CAPITAINE2003 | −7,1e-07 | 2e-05 | jours |
| ok | Mercure : taux de L (deg/siècle), JPL T1 (1800-2050) vs DE441 ajusté 2000-2100 | 149472,674112 | JPL_APPROX | 149472,674726 | JPL_HORIZONS | −0,000614 | 0,1 | deg/siècle |
| ok | Mercure : taux de L (deg/siècle), DE441 2000-2100 vs Simon (séculaire) | 149472,674726 | JPL_HORIZONS | 149472,674636 | SIMON1994 | 9e-05 | 0,1 | deg/siècle |
| ok | Mercure : taux de L (deg/siècle), JPL T1 (local 1800-2050) vs Simon (séculaire) | 149472,674112 | JPL_APPROX | 149472,674636 | SIMON1994 | −0,000524 | 0,01 | deg/siècle |
| ok | Mercure : taux de L Simon 5.8 vs IERS 2010 eq. 5.44 | 149472,674636 | SIMON1994 | 149472,674636 | IERS2010 | 1,16e-09 | 2e-06 | deg/siècle |
| ok | Mercure : taux de L de date, Simon 5.9 vs Meeus 31.A | 149474,072172 | SIMON1994 | 149474,072249 | MEEUS1998 | −7,69e-05 | 0,0001 | deg/siècle |
| ok | Mercure : (taux de date - taux J2000) Simon vs constante de précession de Simon | 5031,131055 | SIMON1994 | 5028,82 | SIMON1994 | 2,31 | 2,5 | ''/siècle |
| ok | Mercure : L0 à J2000, Simon 1994 (transcrit) vs Meeus 31.A | 252,25090552 | SIMON1994 | 252,250906 | MEEUS1998 | −4,8e-07 | 5e-07 | deg |
| ok | Mercure : e0 à J2000, Simon 1994 (transcrit) vs Meeus 31.A | 0,2056317526 | SIMON1994 | 0,20563175 | MEEUS1998 | 2,6e-09 | 6e-09 |  |
| ok | Mercure : i0 à J2000, Simon 1994 (transcrit) vs Meeus 31.A | 7,00498625 | SIMON1994 | 7,004986 | MEEUS1998 | 2,5e-07 | 5e-07 | deg |
| ok | Mercure : Omega0 à J2000, Simon 1994 (transcrit) vs Meeus 31.A | 48,33089304 | SIMON1994 | 48,330893 | MEEUS1998 | 4e-08 | 5e-07 | deg |
| ok | Mercure : varpi0 à J2000, Simon 1994 (transcrit) vs Meeus 31.A | 77,45611904 | SIMON1994 | 77,456119 | MEEUS1998 | 4e-08 | 5e-07 | deg |
| ok | Mercure : de/dT, Simon 1994 (transcrit) vs Meeus 31.A | 2,040653e-05 | SIMON1994 | 2,0407e-05 | MEEUS1998 | −4,7e-10 | 1,5e-09 | /siècle |
| ok | Mercure : taux de varpi de date, Simon 5.9 (transcrit) vs Meeus 31.A | 1,55640073472 | SIMON1994 | 1,5564776 | MEEUS1998 | −7,69e-05 | 0,0001 | deg/siècle |
| ok | Mercure : taux de Omega de date, Simon 5.9 (transcrit) vs Meeus 31.A | 1,18611151222 | SIMON1994 | 1,1861883 | MEEUS1998 | −7,68e-05 | 0,0001 | deg/siècle |
| ok | Mercure : période sidérale (j), JPL T1 vs NSSDC | 87,9692564419 | JPL_APPROX | 87,969 | NSSDC | 0,000256 | 0,0018 | jours |
| ok | Mercure : période synodique (j), calculée (DE441 2000-2100) vs NSSDC | 115,8774776 | JPL_HORIZONS | 115,88 | NSSDC | −0,00252 | 0,02 | jours |
| ok | Mercure : période tropique (j), JPL T1 + p_A vs NSSDC | 87,9684343383 | JPL_APPROX+CAPITAINE2003 | 87,968 | NSSDC | 0,000434 | 0,0018 | jours |
| ok | Mercure : excentricité J2000, JPL T1 vs NSSDC | 0,20563593 | JPL_APPROX | 0,20563069 | NSSDC | 5,24e-06 | 0,0006 |  |
| ok | Mercure : longitude moyenne J2000 (deg), JPL T1 vs NSSDC | 252,2503235 | JPL_APPROX | 252,25084 | NSSDC | −0,000517 | 0,7 | deg |
| ok | Vénus : taux de L (deg/siècle), JPL T1 (1800-2050) vs DE441 ajusté 2000-2100 | 58517,8153873 | JPL_APPROX | 58517,815231 | JPL_HORIZONS | 0,000156 | 0,1 | deg/siècle |
| ok | Vénus : taux de L (deg/siècle), DE441 2000-2100 vs Simon (séculaire) | 58517,815231 | JPL_HORIZONS | 58517,815676 | SIMON1994 | −0,000445 | 0,1 | deg/siècle |
| ok | Vénus : taux de L (deg/siècle), JPL T1 (local 1800-2050) vs Simon (séculaire) | 58517,8153873 | JPL_APPROX | 58517,815676 | SIMON1994 | −0,000289 | 0,01 | deg/siècle |
| ok | Vénus : taux de L Simon 5.8 vs IERS 2010 eq. 5.44 | 58517,815676 | SIMON1994 | 58517,815676 | IERS2010 | −4,37e-11 | 2e-06 | deg/siècle |
| ok | Vénus : taux de L de date, Simon 5.9 vs Meeus 31.A | 58519,2129533 | SIMON1994 | 58519,2130302 | MEEUS1998 | −7,69e-05 | 0,0001 | deg/siècle |
| ok | Vénus : (taux de date - taux J2000) Simon vs constante de précession de Simon | 5030,198441 | SIMON1994 | 5028,82 | SIMON1994 | 1,38 | 2,5 | ''/siècle |
| ok | Vénus : L0 à J2000, Simon 1994 (transcrit) vs Meeus 31.A | 181,97980085 | SIMON1994 | 181,979801 | MEEUS1998 | −1,5e-07 | 5e-07 | deg |
| ok | Vénus : e0 à J2000, Simon 1994 (transcrit) vs Meeus 31.A | 0,0067719164 | SIMON1994 | 0,00677192 | MEEUS1998 | −3,6e-09 | 6e-09 |  |
| ok | Vénus : i0 à J2000, Simon 1994 (transcrit) vs Meeus 31.A | 3,39466189 | SIMON1994 | 3,394662 | MEEUS1998 | −1,1e-07 | 5e-07 | deg |
| ok | Vénus : Omega0 à J2000, Simon 1994 (transcrit) vs Meeus 31.A | 76,67992019 | SIMON1994 | 76,67992 | MEEUS1998 | 1,9e-07 | 5e-06 | deg |
| ok | Vénus : varpi0 à J2000, Simon 1994 (transcrit) vs Meeus 31.A | 131,563703 | SIMON1994 | 131,563703 | MEEUS1998 | 0 | 5e-07 | deg |
| ok | Vénus : de/dT, Simon 1994 (transcrit) vs Meeus 31.A | −4,776521e-05 | SIMON1994 | −4,7765e-05 | MEEUS1998 | −2,1e-10 | 1,5e-09 | /siècle |
| ok | Vénus : taux de varpi de date, Simon 5.9 (transcrit) vs Meeus 31.A | 1,40215196694 | SIMON1994 | 1,4022288 | MEEUS1998 | −7,68e-05 | 0,0001 | deg/siècle |
| ok | Vénus : taux de Omega de date, Simon 5.9 (transcrit) vs Meeus 31.A | 0,901043787778 | SIMON1994 | 0,9011206 | MEEUS1998 | −7,68e-05 | 0,0001 | deg/siècle |
| ok | Vénus : période sidérale (j), JPL T1 vs NSSDC | 224,700801166 | JPL_APPROX | 224,701 | NSSDC | −0,000199 | 0,0045 | jours |
| ok | Vénus : période synodique (j), calculée (DE441 2000-2100) vs NSSDC | 583,9213826 | JPL_HORIZONS | 583,92 | NSSDC | 0,00138 | 0,02 | jours |
| ok | Vénus : période tropique (j), JPL T1 + p_A vs NSSDC | 224,695437426 | JPL_APPROX+CAPITAINE2003 | 224,695 | NSSDC | 0,000437 | 0,0045 | jours |
| ok | Vénus : excentricité J2000, JPL T1 vs NSSDC | 0,00677672 | JPL_APPROX | 0,00677323 | NSSDC | 3,49e-06 | 0,0006 |  |
| ok | Vénus : longitude moyenne J2000 (deg), JPL T1 vs NSSDC | 181,9790995 | JPL_APPROX | 181,97973 | NSSDC | −0,00063 | 0,7 | deg |
| ok | Terre (barycentre Terre-Lune) : taux de L (deg/siècle), JPL T1 (1800-2050) vs DE441 ajusté 2000-2100 | 35999,3724498 | JPL_APPROX | 35999,3728653 | JPL_HORIZONS | −0,000416 | 0,1 | deg/siècle |
| ok | Terre (barycentre Terre-Lune) : taux de L (deg/siècle), DE441 2000-2100 vs Simon (séculaire) | 35999,3728653 | JPL_HORIZONS | 35999,3728565 | SIMON1994 | 8,81e-06 | 0,1 | deg/siècle |
| ok | Terre (barycentre Terre-Lune) : taux de L (deg/siècle), JPL T1 (local 1800-2050) vs Simon (séculaire) | 35999,3724498 | JPL_APPROX | 35999,3728565 | SIMON1994 | −0,000407 | 0,01 | deg/siècle |
| ok | Terre (barycentre Terre-Lune) : taux de L Simon 5.8 vs IERS 2010 eq. 5.44 | 35999,3728565 | SIMON1994 | 35999,3728565 | IERS2010 | 2,39e-09 | 2e-06 | deg/siècle |
| ok | Terre (barycentre Terre-Lune) : taux de L de date, Simon 5.9 vs Meeus 31.A | 36000,769751 | SIMON1994 | 36000,7698278 | MEEUS1998 | −7,68e-05 | 0,0001 | deg/siècle |
| ok | Terre (barycentre Terre-Lune) : (taux de date - taux J2000) Simon vs constante de précession de Simon | 5028,82 | SIMON1994 | 5028,82 | SIMON1994 | 0 | 2,5 | ''/siècle |
| ok | Terre (barycentre Terre-Lune) : L0 à J2000, Simon 1994 (transcrit) vs Meeus 31.A | 100,46645683 | SIMON1994 | 100,466457 | MEEUS1998 | −1,7e-07 | 5e-07 | deg |
| ok | Terre (barycentre Terre-Lune) : e0 à J2000, Simon 1994 (transcrit) vs Meeus 31.A | 0,0167086342 | SIMON1994 | 0,01670863 | MEEUS1998 | 4,2e-09 | 6e-09 |  |
| ok | Terre (barycentre Terre-Lune) : varpi0 à J2000, Simon 1994 (transcrit) vs Meeus 31.A | 102,93734808 | SIMON1994 | 102,937348 | MEEUS1998 | 8e-08 | 5e-07 | deg |
| ok | Terre (barycentre Terre-Lune) : de/dT, Simon 1994 (transcrit) vs Meeus 31.A | −4,203654e-05 | SIMON1994 | −4,2037e-05 | MEEUS1998 | 4,6e-10 | 1,5e-09 | /siècle |
| ok | Terre (barycentre Terre-Lune) : taux de varpi de date, Simon 5.9 (transcrit) vs Meeus 31.A | 1,71945980278 | SIMON1994 | 1,7195366 | MEEUS1998 | −7,68e-05 | 0,0001 | deg/siècle |
| ok | Terre (barycentre Terre-Lune) : période sidérale (j), JPL T1 vs NSSDC | 365,256367131 | JPL_APPROX | 365,256 | NSSDC | 0,000367 | 0,0073 | jours |
| ok | Terre (barycentre Terre-Lune) : période tropique (j), JPL T1 + p_A vs NSSDC | 365,242194595 | JPL_APPROX+CAPITAINE2003 | 365,242 | NSSDC | 0,000195 | 0,0073 | jours |
| ok | Terre (barycentre Terre-Lune) : excentricité J2000, JPL T1 vs NSSDC | 0,01671123 | JPL_APPROX | 0,01671022 | NSSDC | 1,01e-06 | 0,0006 |  |
| ok | Terre (barycentre Terre-Lune) : longitude moyenne J2000 (deg), JPL T1 vs NSSDC | 100,46457166 | JPL_APPROX | 100,46435 | NSSDC | 0,000222 | 0,7 | deg |
| ok | Mars : taux de L (deg/siècle), JPL T1 (1800-2050) vs DE441 ajusté 2000-2100 | 19140,302685 | JPL_APPROX | 19140,3020438 | JPL_HORIZONS | 0,000641 | 0,1 | deg/siècle |
| ok | Mars : taux de L (deg/siècle), DE441 2000-2100 vs Simon (séculaire) | 19140,3020438 | JPL_HORIZONS | 19140,2993039 | SIMON1994 | 0,00274 | 0,1 | deg/siècle |
| ok | Mars : taux de L (deg/siècle), JPL T1 (local 1800-2050) vs Simon (séculaire) | 19140,302685 | JPL_APPROX | 19140,2993039 | SIMON1994 | 0,00338 | 0,01 | deg/siècle |
| ok | Mars : taux de L Simon 5.8 vs IERS 2010 eq. 5.44 | 19140,2993039 | SIMON1994 | 19140,2993039 | IERS2010 | −1,05e-09 | 2e-06 | deg/siècle |
| ok | Mars : taux de L de date, Simon 5.9 vs Meeus 31.A | 19141,6963703 | SIMON1994 | 19141,6964471 | MEEUS1998 | −7,68e-05 | 0,0001 | deg/siècle |
| ok | Mars : (taux de date - taux J2000) Simon vs constante de précession de Simon | 5029,439081 | SIMON1994 | 5028,82 | SIMON1994 | 0,619 | 2,5 | ''/siècle |
| ok | Mars : L0 à J2000, Simon 1994 (transcrit) vs Meeus 31.A | 355,43299958 | SIMON1994 | 355,433 | MEEUS1998 | −4,2e-07 | 0,0005 | deg |
| ok | Mars : e0 à J2000, Simon 1994 (transcrit) vs Meeus 31.A | 0,0934006477 | SIMON1994 | 0,09340065 | MEEUS1998 | −2,3e-09 | 6e-09 |  |
| ok | Mars : i0 à J2000, Simon 1994 (transcrit) vs Meeus 31.A | 1,84972648 | SIMON1994 | 1,849726 | MEEUS1998 | 4,8e-07 | 5e-07 | deg |
| ok | Mars : Omega0 à J2000, Simon 1994 (transcrit) vs Meeus 31.A | 49,55809321 | SIMON1994 | 49,558093 | MEEUS1998 | 2,1e-07 | 5e-07 | deg |
| ok | Mars : varpi0 à J2000, Simon 1994 (transcrit) vs Meeus 31.A | 336,06023395 | SIMON1994 | 336,060234 | MEEUS1998 | −5e-08 | 5e-07 | deg |
| ok | Mars : de/dT, Simon 1994 (transcrit) vs Meeus 31.A | 9,048438e-05 | SIMON1994 | 9,0484e-05 | MEEUS1998 | 3,8e-10 | 1,5e-09 | /siècle |
| ok | Mars : taux de varpi de date, Simon 5.9 (transcrit) vs Meeus 31.A | 1,84096805278 | SIMON1994 | 1,8410449 | MEEUS1998 | −7,68e-05 | 0,0001 | deg/siècle |
| ok | Mars : taux de Omega de date, Simon 5.9 (transcrit) vs Meeus 31.A | 0,772019093333 | SIMON1994 | 0,7720959 | MEEUS1998 | −7,68e-05 | 0,0001 | deg/siècle |
| ok | Mars : période sidérale (j), JPL T1 vs NSSDC | 686,979731533 | JPL_APPROX | 686,98 | NSSDC | −0,000268 | 0,014 | jours |
| ok | Mars : période synodique (j), calculée (DE441 2000-2100) vs NSSDC | 779,9362218 | JPL_HORIZONS | 779,94 | NSSDC | −0,00378 | 0,02 | jours |
| expliqué | Mars : période tropique (j), JPL T1 + p_A vs NSSDC | 686,929598387 | JPL_APPROX+CAPITAINE2003 | 686,972 | NSSDC | −0,0424 | 0,014 | jours |
| ok | Mars : excentricité J2000, JPL T1 vs NSSDC | 0,0933941 | JPL_APPROX | 0,09341233 | NSSDC | −1,82e-05 | 0,0006 |  |
| ok | Mars : longitude moyenne J2000 (deg), JPL T1 vs NSSDC | 355,44656795 | JPL_APPROX | 355,45332 | NSSDC | −0,00675 | 0,7 | deg |
| ok | Jupiter : taux de L (deg/siècle), JPL T1 (1800-2050) vs DE441 ajusté 2000-2100 | 3034,74612775 | JPL_APPROX | 3034,72276161 | JPL_HORIZONS | 0,0234 | 0,1 | deg/siècle |
| expliqué | Jupiter : taux de L (deg/siècle), DE441 2000-2100 vs Simon (séculaire) | 3034,72276161 | JPL_HORIZONS | 3034,90566055 | SIMON1994 | −0,183 | 0,1 | deg/siècle |
| expliqué | Jupiter : taux de L (deg/siècle), JPL T1 (local 1800-2050) vs Simon (séculaire) | 3034,74612775 | JPL_APPROX | 3034,90566055 | SIMON1994 | −0,16 | 0,01 | deg/siècle |
| ok | Jupiter : taux de L Simon 5.8 vs IERS 2010 eq. 5.44 | 3034,90566055 | SIMON1994 | 3034,90566056 | IERS2010 | −2,05e-09 | 2e-06 | deg/siècle |
| ok | Jupiter : taux de L de date, Simon 5.9 vs Meeus 31.A | 3036,30277485 | SIMON1994 | 3036,3027748 | MEEUS1998 | 4,81e-08 | 0,0001 | deg/siècle |
| ok | Jupiter : (taux de date - taux J2000) Simon vs constante de précession de Simon | 5029,611462 | SIMON1994 | 5028,82 | SIMON1994 | 0,791 | 2,5 | ''/siècle |
| ok | Jupiter : L0 à J2000, Simon 1994 (transcrit) vs Meeus 31.A | 34,35151874 | SIMON1994 | 34,351519 | MEEUS1998 | −2,6e-07 | 5e-07 | deg |
| ok | Jupiter : e0 à J2000, Simon 1994 (transcrit) vs Meeus 31.A | 0,0484979255 | SIMON1994 | 0,04849793 | MEEUS1998 | −4,5e-09 | 6e-09 |  |
| ok | Jupiter : i0 à J2000, Simon 1994 (transcrit) vs Meeus 31.A | 1,30326698 | SIMON1994 | 1,303267 | MEEUS1998 | −2e-08 | 5e-07 | deg |
| ok | Jupiter : Omega0 à J2000, Simon 1994 (transcrit) vs Meeus 31.A | 100,46440702 | SIMON1994 | 100,464407 | MEEUS1998 | 2e-08 | 5e-07 | deg |
| ok | Jupiter : varpi0 à J2000, Simon 1994 (transcrit) vs Meeus 31.A | 14,33120687 | SIMON1994 | 14,331207 | MEEUS1998 | −1,3e-07 | 5e-07 | deg |
| ok | Jupiter : de/dT, Simon 1994 (transcrit) vs Meeus 31.A | 0,00016322542 | SIMON1994 | 0,000163225 | MEEUS1998 | 4,2e-10 | 1,5e-09 | /siècle |
| ok | Jupiter : taux de varpi de date, Simon 5.9 (transcrit) vs Meeus 31.A | 1,61263517361 | SIMON1994 | 1,6126352 | MEEUS1998 | −2,64e-08 | 0,0001 | deg/siècle |
| ok | Jupiter : taux de Omega de date, Simon 5.9 (transcrit) vs Meeus 31.A | 1,02097742972 | SIMON1994 | 1,0209774 | MEEUS1998 | 2,97e-08 | 0,0001 | deg/siècle |
| expliqué | Jupiter : période sidérale (j), JPL T1 vs NSSDC | 4332,81712752 | JPL_APPROX | 4332,589 | NSSDC | 0,228 | 0,087 | jours |
| ok | Jupiter : période sidérale (j), NSSDC vs Simon 1994 séculaire | 4332,589 | NSSDC | 4332,58936873 | SIMON1994 | −0,000369 | 0,01 | jours |
| ok | Jupiter : période synodique (j), calculée (DE441 2000-2100) vs NSSDC | 398,8818313 | JPL_HORIZONS | 398,88 | NSSDC | 0,00183 | 0,02 | jours |
| expliqué | Jupiter : période tropique (j), JPL T1 + p_A vs NSSDC | 4330,82365769 | JPL_APPROX+CAPITAINE2003 | 4330,595 | NSSDC | 0,229 | 0,087 | jours |
| ok | Jupiter : excentricité J2000, JPL T1 vs NSSDC | 0,04838624 | JPL_APPROX | 0,04839266 | NSSDC | −6,42e-06 | 0,0006 |  |
| ok | Jupiter : longitude moyenne J2000 (deg), JPL T1 vs NSSDC | 34,39644051 | JPL_APPROX | 34,40438 | NSSDC | −0,00794 | 0,7 | deg |
| ok | Saturne : taux de L (deg/siècle), JPL T1 (1800-2050) vs DE441 ajusté 2000-2100 | 1222,49362201 | JPL_APPROX | 1222,57422615 | JPL_HORIZONS | −0,0806 | 0,1 | deg/siècle |
| expliqué | Saturne : taux de L (deg/siècle), DE441 2000-2100 vs Simon (séculaire) | 1222,57422615 | JPL_HORIZONS | 1222,11384881 | SIMON1994 | 0,46 | 0,1 | deg/siècle |
| expliqué | Saturne : taux de L (deg/siècle), JPL T1 (local 1800-2050) vs Simon (séculaire) | 1222,49362201 | JPL_APPROX | 1222,11384881 | SIMON1994 | 0,38 | 0,01 | deg/siècle |
| ok | Saturne : taux de L Simon 5.8 vs IERS 2010 eq. 5.44 | 1222,11384881 | SIMON1994 | 1222,11384881 | IERS2010 | 1,85e-09 | 2e-06 | deg/siècle |
| ok | Saturne : taux de L de date, Simon 5.9 vs Meeus 31.A | 1223,51106862 | SIMON1994 | 1223,5110686 | MEEUS1998 | 2,17e-08 | 0,0001 | deg/siècle |
| ok | Saturne : (taux de date - taux J2000) Simon vs constante de précession de Simon | 5029,991306 | SIMON1994 | 5028,82 | SIMON1994 | 1,17 | 2,5 | ''/siècle |
| ok | Saturne : L0 à J2000, Simon 1994 (transcrit) vs Meeus 31.A | 50,0774443 | SIMON1994 | 50,077444 | MEEUS1998 | 3e-07 | 5e-07 | deg |
| ok | Saturne : e0 à J2000, Simon 1994 (transcrit) vs Meeus 31.A | 0,0555481426 | SIMON1994 | 0,05554814 | MEEUS1998 | 2,6e-09 | 6e-09 |  |
| ok | Saturne : i0 à J2000, Simon 1994 (transcrit) vs Meeus 31.A | 2,48887878 | SIMON1994 | 2,488879 | MEEUS1998 | −2,2e-07 | 5e-07 | deg |
| ok | Saturne : Omega0 à J2000, Simon 1994 (transcrit) vs Meeus 31.A | 113,66550252 | SIMON1994 | 113,665503 | MEEUS1998 | −4,8e-07 | 5e-07 | deg |
| ok | Saturne : varpi0 à J2000, Simon 1994 (transcrit) vs Meeus 31.A | 93,05723748 | SIMON1994 | 93,057237 | MEEUS1998 | 4,8e-07 | 5e-07 | deg |
| ok | Saturne : de/dT, Simon 1994 (transcrit) vs Meeus 31.A | −0,00034664062 | SIMON1994 | −0,000346641 | MEEUS1998 | 3,8e-10 | 1,5e-09 | /siècle |
| ok | Saturne : taux de varpi de date, Simon 5.9 (transcrit) vs Meeus 31.A | 1,96376131806 | SIMON1994 | 1,9637613 | MEEUS1998 | 1,81e-08 | 0,0001 | deg/siècle |
| ok | Saturne : taux de Omega de date, Simon 5.9 (transcrit) vs Meeus 31.A | 0,877088020833 | SIMON1994 | 0,877088 | MEEUS1998 | 2,08e-08 | 0,0001 | deg/siècle |
| ok | Saturne : période sidérale (j), JPL T1 vs NSSDC | 10755,8843361 | JPL_APPROX | 10755,699 | NSSDC | 0,185 | 11 | jours |
| expliqué | Saturne : période sidérale (j), NSSDC vs Simon 1994 séculaire | 10755,699 | NSSDC | 10759,2267388 | SIMON1994 | −3,53 | 0,01 | jours |
| ok | Saturne : période synodique (j), calculée (DE441 2000-2100) vs NSSDC | 378,096907 | JPL_HORIZONS | 378,09 | NSSDC | 0,00691 | 0,02 | jours |
| ok | Saturne : période tropique (j), JPL T1 + p_A vs NSSDC | 10743,608104 | JPL_APPROX+CAPITAINE2003 | 10746,94 | NSSDC | −3,33 | 11 | jours |
| ok | Saturne : excentricité J2000, JPL T1 vs NSSDC | 0,05386179 | JPL_APPROX | 0,0541506 | NSSDC | −0,000289 | 0,0006 |  |
| ok | Saturne : longitude moyenne J2000 (deg), JPL T1 vs NSSDC | 49,95424423 | JPL_APPROX | 49,94432 | NSSDC | 0,00992 | 0,7 | deg |
| ok | Uranus : taux de L (deg/siècle), JPL T1 (1800-2050) vs DE441 ajusté 2000-2100 | 428,48202785 | JPL_APPROX | 428,558708515 | JPL_HORIZONS | −0,0767 | 0,1 | deg/siècle |
| ok | Uranus : taux de L (deg/siècle), DE441 2000-2100 vs Simon (séculaire) | 428,558708515 | JPL_HORIZONS | 428,466998315 | SIMON1994 | 0,0917 | 0,1 | deg/siècle |
| expliqué | Uranus : taux de L (deg/siècle), JPL T1 (local 1800-2050) vs Simon (séculaire) | 428,48202785 | JPL_APPROX | 428,466998315 | SIMON1994 | 0,015 | 0,01 | deg/siècle |
| ok | Uranus : taux de L Simon 5.8 vs IERS 2010 eq. 5.44 | 428,466998315 | SIMON1994 | 428,466998313 | IERS2010 | 1,66e-09 | 2e-06 | deg/siècle |
| ok | Uranus : taux de L de date, Simon 5.9 vs Meeus 31.A | 429,8640561 | SIMON1994 | 429,8640561 | MEEUS1998 | 2,78e-10 | 0,0001 | deg/siècle |
| ok | Uranus : (taux de date - taux J2000) Simon vs constante de précession de Simon | 5029,408028 | SIMON1994 | 5028,82 | SIMON1994 | 0,588 | 2,5 | ''/siècle |
| ok | Uranus : L0 à J2000, Simon 1994 (transcrit) vs Meeus 31.A | 314,05500511 | SIMON1994 | 314,055005 | MEEUS1998 | 1,1e-07 | 5e-07 | deg |
| ok | Uranus : e0 à J2000, Simon 1994 (transcrit) vs Meeus 31.A | 0,0463812221 | SIMON1994 | 0,04638122 | MEEUS1998 | 2,1e-09 | 6e-09 |  |
| ok | Uranus : i0 à J2000, Simon 1994 (transcrit) vs Meeus 31.A | 0,77319689 | SIMON1994 | 0,773197 | MEEUS1998 | −1,1e-07 | 5e-07 | deg |
| ok | Uranus : Omega0 à J2000, Simon 1994 (transcrit) vs Meeus 31.A | 74,00595701 | SIMON1994 | 74,005957 | MEEUS1998 | 1e-08 | 5e-07 | deg |
| ok | Uranus : varpi0 à J2000, Simon 1994 (transcrit) vs Meeus 31.A | 173,00529106 | SIMON1994 | 173,005291 | MEEUS1998 | 6e-08 | 5e-07 | deg |
| ok | Uranus : de/dT, Simon 1994 (transcrit) vs Meeus 31.A | −2,729293e-05 | SIMON1994 | −2,7293e-05 | MEEUS1998 | 7e-11 | 1,5e-09 | /siècle |
| ok | Uranus : taux de varpi de date, Simon 5.9 (transcrit) vs Meeus 31.A | 1,48637896278 | SIMON1994 | 1,486379 | MEEUS1998 | −3,72e-08 | 0,0001 | deg/siècle |
| ok | Uranus : taux de Omega de date, Simon 5.9 (transcrit) vs Meeus 31.A | 0,521127750556 | SIMON1994 | 0,5211278 | MEEUS1998 | −4,94e-08 | 0,0001 | deg/siècle |
| ok | Uranus : période sidérale (j), JPL T1 vs NSSDC | 30687,4014436 | JPL_APPROX | 30685,4 | NSSDC | 2 | 31 | jours |
| expliqué | Uranus : période sidérale (j), NSSDC vs Simon 1994 séculaire | 30685,4 | NSSDC | 30688,4778798 | SIMON1994 | −3,08 | 0,01 | jours |
| ok | Uranus : période synodique (j), calculée (DE441 2000-2100) vs NSSDC | 369,6569874 | JPL_HORIZONS | 369,66 | NSSDC | −0,00301 | 0,02 | jours |
| ok | Uranus : période tropique (j), JPL T1 + p_A vs NSSDC | 30587,6829971 | JPL_APPROX+CAPITAINE2003 | 30588,74 | NSSDC | −1,06 | 31 | jours |
| ok | Uranus : excentricité J2000, JPL T1 vs NSSDC | 0,04725744 | JPL_APPROX | 0,04716771 | NSSDC | 8,97e-05 | 0,0006 |  |
| ok | Uranus : longitude moyenne J2000 (deg), JPL T1 vs NSSDC | 313,23810451 | JPL_APPROX | 313,23218 | NSSDC | 0,00592 | 0,7 | deg |
| ok | Neptune : taux de L (deg/siècle), JPL T1 (1800-2050) vs DE441 ajusté 2000-2100 | 218,45945325 | JPL_APPROX | 218,427640072 | JPL_HORIZONS | 0,0318 | 0,1 | deg/siècle |
| ok | Neptune : taux de L (deg/siècle), DE441 2000-2100 vs Simon (séculaire) | 218,427640072 | JPL_HORIZONS | 218,486200207 | SIMON1994 | −0,0586 | 0,1 | deg/siècle |
| expliqué | Neptune : taux de L (deg/siècle), JPL T1 (local 1800-2050) vs Simon (séculaire) | 218,45945325 | JPL_APPROX | 218,486200207 | SIMON1994 | −0,0267 | 0,01 | deg/siècle |
| ok | Neptune : taux de L Simon 5.8 vs IERS 2010 eq. 5.44 | 218,486200207 | SIMON1994 | 218,486200208 | IERS2010 | −1,27e-09 | 2e-06 | deg/siècle |
| ok | Neptune : taux de L de date, Simon 5.9 vs Meeus 31.A | 219,883309244 | SIMON1994 | 219,8833092 | MEEUS1998 | 4,36e-08 | 0,0001 | deg/siècle |
| ok | Neptune : (taux de date - taux J2000) Simon vs constante de précession de Simon | 5029,592533 | SIMON1994 | 5028,82 | SIMON1994 | 0,773 | 2,5 | ''/siècle |
| ok | Neptune : L0 à J2000, Simon 1994 (transcrit) vs Meeus 31.A | 304,34866548 | SIMON1994 | 304,348665 | MEEUS1998 | 4,8e-07 | 5e-07 | deg |
| ok | Neptune : e0 à J2000, Simon 1994 (transcrit) vs Meeus 31.A | 0,009455747 | SIMON1994 | 0,00945575 | MEEUS1998 | −3e-09 | 6e-09 |  |
| ok | Neptune : i0 à J2000, Simon 1994 (transcrit) vs Meeus 31.A | 1,76995259 | SIMON1994 | 1,769953 | MEEUS1998 | −4,1e-07 | 5e-07 | deg |
| ok | Neptune : Omega0 à J2000, Simon 1994 (transcrit) vs Meeus 31.A | 131,78405702 | SIMON1994 | 131,784057 | MEEUS1998 | 2e-08 | 5e-07 | deg |
| ok | Neptune : varpi0 à J2000, Simon 1994 (transcrit) vs Meeus 31.A | 48,12027554 | SIMON1994 | 48,120276 | MEEUS1998 | −4,6e-07 | 5e-07 | deg |
| ok | Neptune : de/dT, Simon 1994 (transcrit) vs Meeus 31.A | 6,03263e-06 | SIMON1994 | 6,033e-06 | MEEUS1998 | −3,7e-10 | 1,5e-09 | /siècle |
| ok | Neptune : taux de varpi de date, Simon 5.9 (transcrit) vs Meeus 31.A | 1,42629568194 | SIMON1994 | 1,4262957 | MEEUS1998 | −1,81e-08 | 0,0001 | deg/siècle |
| ok | Neptune : taux de Omega de date, Simon 5.9 (transcrit) vs Meeus 31.A | 1,10220393306 | SIMON1994 | 1,1022039 | MEEUS1998 | 3,31e-08 | 0,0001 | deg/siècle |
| ok | Neptune : période sidérale (j), JPL T1 vs NSSDC | 60189,6590163 | JPL_APPROX | 60189,018 | NSSDC | 0,641 | 60 | jours |
| expliqué | Neptune : période sidérale (j), NSSDC vs Simon 1994 séculaire | 60189,018 | NSSDC | 60182,2906324 | SIMON1994 | 6,73 | 0,01 | jours |
| ok | Neptune : période synodique (j), calculée (DE441 2000-2100) vs NSSDC | 367,4860996 | JPL_HORIZONS | 367,49 | NSSDC | −0,0039 | 0,02 | jours |
| ok | Neptune : période tropique (j), JPL T1 + p_A vs NSSDC | 59807,2356489 | JPL_APPROX+CAPITAINE2003 | 59799,9 | NSSDC | 7,34 | 60 | jours |
| ok | Neptune : excentricité J2000, JPL T1 vs NSSDC | 0,00859048 | JPL_APPROX | 0,00858587 | NSSDC | 4,61e-06 | 0,0006 |  |
| ok | Neptune : longitude moyenne J2000 (deg), JPL T1 vs NSSDC | 304,87997031 | JPL_APPROX | 304,88003 | NSSDC | −5,97e-05 | 0,7 | deg |
| ok | Pluton : taux de L (deg/siècle), JPL T1 (1800-2050) vs DE441 ajusté 2000-2100 | 145,20780515 | JPL_APPROX | 145,164653535 | JPL_HORIZONS | 0,0432 | 0,1 | deg/siècle |
| ok | Pluton : période sidérale (j), JPL T1 vs NSSDC | 90552,9836114 | JPL_APPROX | 90560 | NSSDC | −7,02 | 91 | jours |
| ok | Pluton : période synodique (j), calculée (DE441 2000-2100) vs NSSDC | 366,7351939 | JPL_HORIZONS | 366,73 | NSSDC | 0,00519 | 0,02 | jours |
| ok | Pluton : excentricité J2000, JPL T1 vs NSSDC | 0,2488273 | JPL_APPROX | 0,24880766 | NSSDC | 1,96e-05 | 0,0006 |  |
| ok | Pluton : longitude moyenne J2000 (deg), JPL T1 vs NSSDC | 238,92903833 | JPL_APPROX | 238,92881 | NSSDC | 0,000228 | 0,7 | deg |
| ok | Soleil : 1er terme de l'équation du centre (deg), Meeus vs série de Kepler (e Simon) | 1,914602 | MEEUS1998 | 1,9146016254 | SIMON1994 | 3,75e-07 | 0,0002 | deg |
| ok | Soleil : 2e terme de l'équation du centre (deg), Meeus vs 5/4 e^2 | 0,019993 | MEEUS1998 | 0,0199946841341 | SIMON1994 | −1,68e-06 | 1e-05 | deg |
| ok | Jupiter : amplitude de la grande inégalité (deg), JPL 2b vs Schlyter | 0,361477145216 | JPL_APPROX | 0,332 | SCHLYTER | 0,0295 | 0,08 | deg |
| ok | Saturne : amplitude de la grande inégalité (deg), JPL 2b vs Schlyter | 0,883475694596 | JPL_APPROX | 0,812 | SCHLYTER | 0,0715 | 0,08 | deg |
| ok | Mois sidereal (j) : Simon 1994 / IERS vs Chapront et al. 2002 | 27,3216615512 | SIMON1994 | 27,321661554 | CHAPRONT2002 | −2,83e-09 | 2e-08 | jours |
| ok | Mois tropical (j) : Simon 1994 / IERS vs Chapront et al. 2002 | 27,3215822492 | SIMON1994 | 27,321582252 | CHAPRONT2002 | −2,77e-09 | 2e-08 | jours |
| ok | Mois synodic (j) : Simon 1994 / IERS vs Chapront et al. 2002 | 29,5305888577 | SIMON1994 | 29,530588861 | CHAPRONT2002 | −3,29e-09 | 2e-08 | jours |
| ok | Mois anomalistic (j) : Simon 1994 / IERS vs Chapront et al. 2002 | 27,5545498824 | SIMON1994 | 27,554549886 | CHAPRONT2002 | −3,64e-09 | 2e-08 | jours |
| ok | Mois draconic (j) : Simon 1994 / IERS vs Chapront et al. 2002 | 27,2122208206 | SIMON1994 | 27,212220815 | CHAPRONT2002 | 5,56e-09 | 2e-08 | jours |
| ok | Lune : taux de D (deg/siècle), Meeus ch. 47 vs IERS 2010 (Simon 1994) | 445267,111403 | MEEUS1998 | 445267,111447 | IERS2010 | −4,35e-05 | 0,0002 | deg/siècle |
| ok | Lune : taux de M_prime (deg/siècle), Meeus ch. 47 vs IERS 2010 (Simon 1994) | 477198,867505 | MEEUS1998 | 477198,86756 | IERS2010 | −5,5e-05 | 0,0002 | deg/siècle |
| ok | Lune : taux de F (deg/siècle), Meeus ch. 47 vs IERS 2010 (Simon 1994) | 483202,017523 | MEEUS1998 | 483202,017458 | IERS2010 | 6,56e-05 | 0,0002 | deg/siècle |
| ok | Lune : taux de Omega (deg/siècle), Meeus ch. 47 vs IERS 2010 (Simon 1994) | −1934,1362891 | MEEUS1998 | −1934,13626197 | IERS2010 | −2,71e-05 | 0,0002 | deg/siècle |
| ok | Lune : taux de M_sun (deg/siècle), Meeus ch. 47 vs IERS 2010 (Simon 1994) | 35999,0502909 | MEEUS1998 | 35999,0502911 | IERS2010 | −2,39e-07 | 0,0002 | deg/siècle |
| ok | Lune : taux de L' (deg/siècle, de date), Meeus vs Simon (b.3) | 481267,881234 | MEEUS1998 | 481267,881196 | SIMON1994 | 3,85e-05 | 0,0002 | deg/siècle |
| ok | Lune : taux du périgée (deg/siècle, de date), Meeus vs Simon (b.3) | 4069,0137287 | MEEUS1998 | 4069,01363525 | SIMON1994 | 9,34e-05 | 0,001 | deg/siècle |
| ok | Mois synodique de Meeus (49.1) vs Chapront 2002 | 29,530588861 | MEEUS1998 | 29,530588861 | CHAPRONT2002 | 0 | 1e-09 | jours |
| ok | Mois sidéral : Simon vs NSSDC 27,3217 | 27,3216615512 | SIMON1994 | 27,3217 | NSSDC_MOON | −3,84e-05 | 6e-05 | jours |
| ok | Période des nœuds (tropique, j) : Simon vs IERS table 5.1a (6798,3837) | 6798,38347407 | SIMON1994 | 6798,3837 | IERS2010 | −0,000226 | 0,001 | jours |
| ok | Période des nœuds (sidérale, j) : Simon vs NASA (6793,48) | 6793,47700989 | SIMON1994 | 6793,48 | NASA_ECL | −0,00299 | 0,01 | jours |
| ok | Période du périgée (tropique, j) : Simon vs IERS table 5.1a (3231,4956) | 3231,49568389 | SIMON1994 | 3231,4956 | IERS2010 | 8,39e-05 | 0,001 | jours |
| expliqué | Période du périgée (j) : Simon (sidérale) vs NASA (3231,6 j, dite 'par rapport aux étoiles') | 3232,60543898 | SIMON1994 | 3231,6 | NASA_ECL | 1,01 | 0,1 | jours |
| ok | Année draconitique (j) : (F - D) IERS vs Wikipedia 'Year' 346,620075883 | 346,620075881 | IERS2010 | 346,620075883 | WIKI_YEAR | −1,85e-09 | 5e-06 | jours |
| ok | Lune, longitude, equation_du_centre (deg) : Meeus 47.A vs Brown (Wikipedia) | 6,288774 | MEEUS1998 | 6,28861111111 | WIKI_LUNAR_THEORY | 0,000163 | 0,0006 | deg |
| ok | Lune, longitude, equation_du_centre (deg) : Meeus 47.A vs Almanach (2 décimales) | 6,288774 | MEEUS1998 | 6,29 | AA_LOWPREC | −0,00123 | 0,006 | deg |
| ok | Lune, longitude, évection (deg) : Meeus 47.A vs Brown (Wikipedia) | 1,274027 | MEEUS1998 | 1,27388888889 | WIKI_LUNAR_THEORY | 0,000138 | 0,0006 | deg |
| ok | Lune, longitude, évection (deg) : Meeus 47.A vs Almanach (2 décimales) | 1,274027 | MEEUS1998 | 1,27 | AA_LOWPREC | 0,00403 | 0,006 | deg |
| ok | Lune, longitude, variation (deg) : Meeus 47.A vs Brown (Wikipedia) | 0,658314 | MEEUS1998 | 0,658333333333 | WIKI_LUNAR_THEORY | −1,93e-05 | 0,0006 | deg |
| ok | Lune, longitude, variation (deg) : Meeus 47.A vs Almanach (2 décimales) | 0,658314 | MEEUS1998 | 0,66 | AA_LOWPREC | −0,00169 | 0,006 | deg |
| ok | Lune, longitude, equation_du_centre_2e_harmonique (deg) : Meeus 47.A vs Brown (Wikipedia) | 0,213618 | MEEUS1998 | 0,213611111111 | WIKI_LUNAR_THEORY | 6,89e-06 | 0,0006 | deg |
| ok | Lune, longitude, equation_du_centre_2e_harmonique (deg) : Meeus 47.A vs Almanach (2 décimales) | 0,213618 | MEEUS1998 | 0,21 | AA_LOWPREC | 0,00362 | 0,006 | deg |
| ok | Lune, longitude, equation_annuelle (deg) : Meeus 47.A vs Brown (Wikipedia) | −0,185116 | MEEUS1998 | −0,185555555556 | WIKI_LUNAR_THEORY | 0,00044 | 0,0006 | deg |
| ok | Lune, longitude, equation_annuelle (deg) : Meeus 47.A vs Almanach (2 décimales) | −0,185116 | MEEUS1998 | −0,19 | AA_LOWPREC | 0,00488 | 0,006 | deg |
| ok | Lune, longitude, reduction_a_l_ecliptique (deg) : Meeus 47.A vs Brown (Wikipedia) | −0,114332 | MEEUS1998 | −0,114444444444 | WIKI_LUNAR_THEORY | 0,000112 | 0,0006 | deg |
| ok | Lune, longitude, reduction_a_l_ecliptique (deg) : Meeus 47.A vs Almanach (2 décimales) | −0,114332 | MEEUS1998 | −0,11 | AA_LOWPREC | −0,00433 | 0,006 | deg |
| ok | Lune, longitude, terme_2D_moins_2Mp (deg) : Meeus 47.A vs Schlyter (3 décimales) | 0,058793 | MEEUS1998 | 0,059 | SCHLYTER | −0,000207 | 0,0006 | deg |
| ok | Lune, longitude, terme_2D_moins_M_moins_Mp (deg) : Meeus 47.A vs Schlyter (3 décimales) | 0,057066 | MEEUS1998 | 0,057 | SCHLYTER | 6,6e-05 | 0,0006 | deg |
| ok | Lune, longitude, terme_2D_plus_Mp (deg) : Meeus 47.A vs Schlyter (3 décimales) | 0,053322 | MEEUS1998 | 0,053 | SCHLYTER | 0,000322 | 0,0006 | deg |
| ok | Lune, longitude, terme_2D_moins_M (deg) : Meeus 47.A vs Schlyter (3 décimales) | 0,045758 | MEEUS1998 | 0,046 | SCHLYTER | −0,000242 | 0,0006 | deg |
| ok | Lune, longitude, terme_M_moins_Mp (deg) : Meeus 47.A vs Schlyter (3 décimales) | −0,040923 | MEEUS1998 | −0,041 | SCHLYTER | 7,7e-05 | 0,0006 | deg |
| ok | Lune, longitude, inegalite_parallactique (deg) : Meeus 47.A vs Brown (Wikipedia) | −0,03472 | MEEUS1998 | −0,0347222222222 | WIKI_LUNAR_THEORY | 2,22e-06 | 0,0006 | deg |
| expliqué | Lune, longitude, terme_M_plus_Mp (deg) : Meeus 47.A vs Schlyter (3 décimales) | −0,030383 | MEEUS1998 | −0,031 | SCHLYTER | 0,000617 | 0,0006 | deg |
| ok | Lune, latitude, terme_principal_sinF (deg) : Meeus 47.B vs Almanach | 5,128122 | MEEUS1998 | 5,13 | AA_LOWPREC | −0,00188 | 0,006 | deg |
| ok | Lune, latitude, Mp_plus_F (deg) : Meeus 47.B vs Almanach | 0,280602 | MEEUS1998 | 0,28 | AA_LOWPREC | 0,000602 | 0,006 | deg |
| ok | Lune, latitude, Mp_moins_F (deg) : Meeus 47.B vs Almanach | 0,277693 | MEEUS1998 | 0,28 | AA_LOWPREC | −0,00231 | 0,006 | deg |
| ok | Lune, latitude, evection_en_latitude_2D_moins_F (deg) : Meeus 47.B vs Almanach | 0,173237 | MEEUS1998 | 0,17 | AA_LOWPREC | 0,00324 | 0,006 | deg |
| ok | Lune, latitude, evection_en_latitude_2D_moins_F (deg) : Meeus 47.B vs Schlyter | 0,173237 | MEEUS1998 | 0,173 | SCHLYTER | 0,000237 | 0,0006 | deg |
| ok | Lune, latitude, 2D_moins_Mp_plus_F (deg) : Meeus 47.B vs Schlyter | 0,055413 | MEEUS1998 | 0,055 | SCHLYTER | 0,000413 | 0,0006 | deg |
| ok | Lune, latitude, 2D_moins_Mp_moins_F (deg) : Meeus 47.B vs Schlyter | 0,046271 | MEEUS1998 | 0,046 | SCHLYTER | 0,000271 | 0,0006 | deg |
| ok | Lune, latitude, 2D_plus_F (deg) : Meeus 47.B vs Schlyter | 0,032573 | MEEUS1998 | 0,033 | SCHLYTER | −0,000427 | 0,0006 | deg |
| ok | Lune, latitude, 2Mp_plus_F (deg) : Meeus 47.B vs Schlyter | 0,017198 | MEEUS1998 | 0,017 | SCHLYTER | 0,000198 | 0,0006 | deg |
| ok | Lune : parallaxe moyenne (deg), Almanach vs asin(6378,14/385000,56) Meeus | 0,9508 | AA_LOWPREC | 0,94923815474 | MEEUS1998 | 0,00156 | 0,002 | deg |
| ok | Saros (j) : 223 x mois synodique vs Wikipedia 'Éclipse cycle' | 6585,32131527 | CHAPRONT2002 | 6585,32 | WIKI_ECL_CYCLE | 0,00132 | 0,006 | jours |
| ok | Saros (j) : 223 x mois synodique vs NASA (6585,3223) | 6585,32131527 | CHAPRONT2002 | 6585,3223 | NASA_ECL | −0,000985 | 0,002 | jours |
| ok | 242 mois draconitiques (j) vs NASA 6585,3575 | 6585,35743858 | SIMON1994 | 6585,3575 | NASA_ECL | −6,14e-05 | 0,001 | jours |
| ok | 239 mois anomalistiques (j) vs NASA 6585,5375 | 6585,53742188 | SIMON1994 | 6585,5375 | NASA_ECL | −7,81e-05 | 0,001 | jours |
| ok | Inex (j) : 358 x mois synodique vs NASA 10571,9509 | 10571,9508111 | CHAPRONT2002 | 10571,9509 | NASA_ECL | −8,89e-05 | 0,001 | jours |
| ok | Exeligmos (j) vs Wikipedia 19755,96 | 19755,9639458 | CHAPRONT2002 | 19755,96 | WIKI_ECL_CYCLE | 0,00395 | 0,006 | jours |
| ok | Cycle de Meton 235 lunaisons (j) vs Wikipedia 6939,69 | 6939,68838156 | CHAPRONT2002 | 6939,69 | WIKI_ECL_CYCLE | −0,00162 | 0,006 | jours |
| ok | Limite écliptique solaire max (deg) : géométrie vs NASA (18,59) | 18,3454479758 | calcul | 18,59 | NASA_ECL | −0,245 | 0,4 | deg |
| ok | Limite écliptique solaire min (deg) : géométrie vs NASA (15,39) | 15,3214369 | calcul | 15,39 | NASA_ECL | −0,0686 | 0,3 | deg |
| ok | Limite écliptique lunaire (ombre) max (deg) : géométrie vs Meeus via Holmes (12 deg 08') | 12,2279571008 | calcul | 12,1333333333 | HOLMES_ECL | 0,0946 | 0,3 | deg |
| ok | io : période sidérale (j), Lieske E5 vs NSSDC | 1,76913778245 | LIESKE_E5 | 1,769138 | NSSDC_JOVSAT | −2,18e-07 | 2e-06 | jours |
| ok | io : période synodique / Soleil (j), E5 - Jupiter (JPL) vs Meeus ch. 44 | 1,7698604363 | LIESKE_E5+JPL_APPROX | 1,76986047432 | MEEUS1998 | −3,8e-08 | 2e-06 | jours |
| ok | io : 'P' de la table JPL = période anomalistique ? (360/(n - varpi')) | 1,76273265562 | LIESKE_E5+JPL_SAT | 1,762732 | JPL_SAT | 6,56e-07 | 0,002 | jours |
| ok | europa : période sidérale (j), Lieske E5 vs NSSDC | 3,55118103591 | LIESKE_E5 | 3,551181 | NSSDC_JOVSAT | 3,59e-08 | 2e-06 | jours |
| ok | europa : période synodique / Soleil (j), E5 - Jupiter (JPL) vs Meeus ch. 44 | 3,55409397471 | LIESKE_E5+JPL_APPROX | 3,5540941296 | MEEUS1998 | −1,55e-07 | 2e-06 | jours |
| ok | europa : 'P' de la table JPL = période anomalistique ? (360/(n - varpi')) | 3,5265844909 | LIESKE_E5+JPL_SAT | 3,525463 | JPL_SAT | 0,00112 | 0,002 | jours |
| ok | ganymede : période sidérale (j), Lieske E5 vs NSSDC | 7,15455296215 | LIESKE_E5 | 7,154553 | NSSDC_JOVSAT | −3,79e-08 | 2e-06 | jours |
| ok | ganymede : période synodique / Soleil (j), E5 - Jupiter (JPL) vs Meeus ch. 44 | 7,16638643903 | LIESKE_E5+JPL_APPROX | 7,16638706477 | MEEUS1998 | −6,26e-07 | 2,1e-06 | jours |
| ok | ganymede : 'P' de la table JPL = période anomalistique ? (360/(n - varpi')) | 7,15660541074 | LIESKE_E5+JPL_SAT | 7,155588 | JPL_SAT | 0,00102 | 0,002 | jours |
| ok | callisto : période sidérale (j), Lieske E5 vs NSSDC | 16,6890182247 | LIESKE_E5 | 16,689017 | NSSDC_JOVSAT | 1,22e-06 | 2e-06 | jours |
| ok | callisto : période synodique / Soleil (j), E5 - Jupiter (JPL) vs Meeus ch. 44 | 16,7535490547 | LIESKE_E5+JPL_APPROX | 16,7535524512 | MEEUS1998 | −3,4e-06 | 5,9e-06 | jours |
| ok | callisto : 'P' de la table JPL = période anomalistique ? (360/(n - varpi')) | 16,6917624603 | LIESKE_E5+JPL_SAT | 16,69044 | JPL_SAT | 0,00132 | 0,002 | jours |
| ok | Relation de Laplace n1 - 3 n2 + 2 n3 (deg/j), E5 | −1e-09 | LIESKE_E5 | 0 | theorie | −1e-09 | 1e-06 | deg/jour |
| ok | Pluton : période sidérale (j), JPL T1 (archivée) vs NSSDC | 90579,9013725 | JPL_APPROX_2019 | 90560 | NSSDC | 19,9 | 3e+02 | jours |

**Notes sur les écarts :**

- *p_A IAU 2006 vs psi_A - chi_A cos eps0 (IERS 2010)* — Relation géométrique au 1er ordre entre précession lunisolaire (psi_A), précession planétaire (chi_A) et précession générale.
- *p_A IAU 2006 vs Simon 1994 (Williams 1991)* — Écart de 0,024''/siècle = 2,4 ms d'arc par an : négligeable pour la machine.
- *p_A IAU 2006 vs IAU 1976* — IAU 1976 (Lieske 1977) était trop grande de ~0,3''/siècle ; c'est la constante utilisée par Meeus table 31.A (voir écart Meeus/Simon ci-dessous). Effet : 0,3''/siècle, négligeable.
- *p_A IAU 2006 vs IERS 2010 F14 (Kinoshita & Souchay 1990, rad/siècle)* — F14 de l'IERS est la valeur ancienne (~IAU 1976) utilisée seulement comme argument de nutation planétaire.
- *Année tropique : Laskar vs JPL table 1 (EMB, ajustement 1800-2050) + p_A* — Le taux JPL est un ajustement local 1800-2050 (inclut des perturbations à longue période) : écart ~1 s/an attendu.
- *Obliquité J2000 : IAU 2006 (84381,406'') vs IAU 1980 (84381,448'')* — Écart de 0,042'' : redéfinition (écliptique inertielle vs rotationnelle, Chapront 2002). Négligeable.
- *Rapport temps sidéral moyen / temps solaire moyen : IERS (ERA + précession en AR) vs Meeus* — Écart 5e-12 (0,4 microseconde par jour) : Meeus arrondit à 11 décimales le rapport d'Aoki et al. 1982 (GMST fonction de UT1), alors que le GMST IAU 2006 sépare ERA(UT1) et précession(TT). Sans effet mécanique.
- *Année tropique : Laskar vs (taux EMB DE441 2000-2100 + p_A)* — Ajustement d'éléments osculateurs sur 100 ans : écart attendu ~1e-6 j.
- *Mercure : taux de L (deg/siècle), JPL T1 (1800-2050) vs DE441 ajusté 2000-2100* — Tolérance 0,1 deg/siècle = 1/10 de l'objectif de la machine.
- *Mercure : taux de L de date, Simon 5.9 vs Meeus 31.A* — Meeus 31.A ajoute ici la différence de constante de précession IAU 1976 - Williams 1991 (+0,277''/siècle = +7,7e-5 deg/siècle) ; pour Jupiter-Neptune il reprend Simon à l'identique.
- *Mercure : (taux de date - taux J2000) Simon vs constante de précession de Simon* — Passer du repère J2000 au repère de date n'ajoute pas exactement p_A à lambda (mouvement de l'écliptique, inclinaison et nœud) : jusqu'à 2,3''/siècle (Mercure). Négligeable (<0,001 deg/siècle).
- *Mercure : L0 à J2000, Simon 1994 (transcrit) vs Meeus 31.A* — Tolérance = demi-unité du dernier chiffre de Meeus.
- *Mercure : e0 à J2000, Simon 1994 (transcrit) vs Meeus 31.A* — Tolérance = demi-unité du dernier chiffre de Meeus.
- *Mercure : i0 à J2000, Simon 1994 (transcrit) vs Meeus 31.A* — Tolérance = demi-unité du dernier chiffre de Meeus.
- *Mercure : Omega0 à J2000, Simon 1994 (transcrit) vs Meeus 31.A* — Tolérance = demi-unité du dernier chiffre de Meeus.
- *Mercure : varpi0 à J2000, Simon 1994 (transcrit) vs Meeus 31.A* — Tolérance = demi-unité du dernier chiffre de Meeus.
- *Mercure : taux de varpi de date, Simon 5.9 (transcrit) vs Meeus 31.A* — Écart possible de 7,7e-5 deg/siècle (constante de précession IAU 1976 chez Meeus).
- *Mercure : taux de Omega de date, Simon 5.9 (transcrit) vs Meeus 31.A* — Écart possible de 7,7e-5 deg/siècle (constante de précession IAU 1976 chez Meeus).
- *Vénus : taux de L (deg/siècle), JPL T1 (1800-2050) vs DE441 ajusté 2000-2100* — Tolérance 0,1 deg/siècle = 1/10 de l'objectif de la machine.
- *Vénus : taux de L de date, Simon 5.9 vs Meeus 31.A* — Meeus 31.A ajoute ici la différence de constante de précession IAU 1976 - Williams 1991 (+0,277''/siècle = +7,7e-5 deg/siècle) ; pour Jupiter-Neptune il reprend Simon à l'identique.
- *Vénus : (taux de date - taux J2000) Simon vs constante de précession de Simon* — Passer du repère J2000 au repère de date n'ajoute pas exactement p_A à lambda (mouvement de l'écliptique, inclinaison et nœud) : jusqu'à 2,3''/siècle (Mercure). Négligeable (<0,001 deg/siècle).
- *Vénus : L0 à J2000, Simon 1994 (transcrit) vs Meeus 31.A* — Tolérance = demi-unité du dernier chiffre de Meeus.
- *Vénus : e0 à J2000, Simon 1994 (transcrit) vs Meeus 31.A* — Tolérance = demi-unité du dernier chiffre de Meeus.
- *Vénus : i0 à J2000, Simon 1994 (transcrit) vs Meeus 31.A* — Tolérance = demi-unité du dernier chiffre de Meeus.
- *Vénus : Omega0 à J2000, Simon 1994 (transcrit) vs Meeus 31.A* — Tolérance = demi-unité du dernier chiffre de Meeus.
- *Vénus : varpi0 à J2000, Simon 1994 (transcrit) vs Meeus 31.A* — Tolérance = demi-unité du dernier chiffre de Meeus.
- *Vénus : taux de varpi de date, Simon 5.9 (transcrit) vs Meeus 31.A* — Écart possible de 7,7e-5 deg/siècle (constante de précession IAU 1976 chez Meeus).
- *Vénus : taux de Omega de date, Simon 5.9 (transcrit) vs Meeus 31.A* — Écart possible de 7,7e-5 deg/siècle (constante de précession IAU 1976 chez Meeus).
- *Terre (barycentre Terre-Lune) : taux de L (deg/siècle), JPL T1 (1800-2050) vs DE441 ajusté 2000-2100* — Tolérance 0,1 deg/siècle = 1/10 de l'objectif de la machine.
- *Terre (barycentre Terre-Lune) : taux de L de date, Simon 5.9 vs Meeus 31.A* — Meeus 31.A ajoute ici la différence de constante de précession IAU 1976 - Williams 1991 (+0,277''/siècle = +7,7e-5 deg/siècle) ; pour Jupiter-Neptune il reprend Simon à l'identique.
- *Terre (barycentre Terre-Lune) : (taux de date - taux J2000) Simon vs constante de précession de Simon* — Passer du repère J2000 au repère de date n'ajoute pas exactement p_A à lambda (mouvement de l'écliptique, inclinaison et nœud) : jusqu'à 2,3''/siècle (Mercure). Négligeable (<0,001 deg/siècle).
- *Terre (barycentre Terre-Lune) : L0 à J2000, Simon 1994 (transcrit) vs Meeus 31.A* — Tolérance = demi-unité du dernier chiffre de Meeus.
- *Terre (barycentre Terre-Lune) : e0 à J2000, Simon 1994 (transcrit) vs Meeus 31.A* — Tolérance = demi-unité du dernier chiffre de Meeus.
- *Terre (barycentre Terre-Lune) : varpi0 à J2000, Simon 1994 (transcrit) vs Meeus 31.A* — Tolérance = demi-unité du dernier chiffre de Meeus.
- *Terre (barycentre Terre-Lune) : taux de varpi de date, Simon 5.9 (transcrit) vs Meeus 31.A* — Écart possible de 7,7e-5 deg/siècle (constante de précession IAU 1976 chez Meeus).
- *Mars : taux de L (deg/siècle), JPL T1 (1800-2050) vs DE441 ajusté 2000-2100* — Tolérance 0,1 deg/siècle = 1/10 de l'objectif de la machine.
- *Mars : taux de L de date, Simon 5.9 vs Meeus 31.A* — Meeus 31.A ajoute ici la différence de constante de précession IAU 1976 - Williams 1991 (+0,277''/siècle = +7,7e-5 deg/siècle) ; pour Jupiter-Neptune il reprend Simon à l'identique.
- *Mars : (taux de date - taux J2000) Simon vs constante de précession de Simon* — Passer du repère J2000 au repère de date n'ajoute pas exactement p_A à lambda (mouvement de l'écliptique, inclinaison et nœud) : jusqu'à 2,3''/siècle (Mercure). Négligeable (<0,001 deg/siècle).
- *Mars : L0 à J2000, Simon 1994 (transcrit) vs Meeus 31.A* — Tolérance = demi-unité du dernier chiffre de Meeus.
- *Mars : e0 à J2000, Simon 1994 (transcrit) vs Meeus 31.A* — Tolérance = demi-unité du dernier chiffre de Meeus.
- *Mars : i0 à J2000, Simon 1994 (transcrit) vs Meeus 31.A* — Tolérance = demi-unité du dernier chiffre de Meeus.
- *Mars : Omega0 à J2000, Simon 1994 (transcrit) vs Meeus 31.A* — Tolérance = demi-unité du dernier chiffre de Meeus.
- *Mars : varpi0 à J2000, Simon 1994 (transcrit) vs Meeus 31.A* — Tolérance = demi-unité du dernier chiffre de Meeus.
- *Mars : taux de varpi de date, Simon 5.9 (transcrit) vs Meeus 31.A* — Écart possible de 7,7e-5 deg/siècle (constante de précession IAU 1976 chez Meeus).
- *Mars : taux de Omega de date, Simon 5.9 (transcrit) vs Meeus 31.A* — Écart possible de 7,7e-5 deg/siècle (constante de précession IAU 1976 chez Meeus).
- *Mars : période tropique (j), JPL T1 + p_A vs NSSDC* — Définition différente : la 'période tropique' NSSDC de Mars (686,972 j) est l'année tropique martienne, rapportée à l'équinoxe de Mars (précession propre ~170 000 ans) ; rapportée à l'équinoxe terrestre elle vaut 686,930 j.
- *Jupiter : taux de L (deg/siècle), JPL T1 (1800-2050) vs DE441 ajusté 2000-2100* — Tolérance 0,1 deg/siècle = 1/10 de l'objectif de la machine.
- *Jupiter : taux de L (deg/siècle), DE441 2000-2100 vs Simon (séculaire)* — Sur 2000-2100 la grande inégalité Jupiter-Saturne accélère Saturne et ralentit Jupiter par rapport à leur mouvement séculaire.
- *Jupiter : taux de L (deg/siècle), JPL T1 (local 1800-2050) vs Simon (séculaire)* — Écart = pente locale des grandes inégalités (Jupiter-Saturne ~900 ans, Uranus-Neptune ~4700 ans).
- *Jupiter : (taux de date - taux J2000) Simon vs constante de précession de Simon* — Passer du repère J2000 au repère de date n'ajoute pas exactement p_A à lambda (mouvement de l'écliptique, inclinaison et nœud) : jusqu'à 2,3''/siècle (Mercure). Négligeable (<0,001 deg/siècle).
- *Jupiter : L0 à J2000, Simon 1994 (transcrit) vs Meeus 31.A* — Tolérance = demi-unité du dernier chiffre de Meeus.
- *Jupiter : e0 à J2000, Simon 1994 (transcrit) vs Meeus 31.A* — Tolérance = demi-unité du dernier chiffre de Meeus.
- *Jupiter : i0 à J2000, Simon 1994 (transcrit) vs Meeus 31.A* — Tolérance = demi-unité du dernier chiffre de Meeus.
- *Jupiter : Omega0 à J2000, Simon 1994 (transcrit) vs Meeus 31.A* — Tolérance = demi-unité du dernier chiffre de Meeus.
- *Jupiter : varpi0 à J2000, Simon 1994 (transcrit) vs Meeus 31.A* — Tolérance = demi-unité du dernier chiffre de Meeus.
- *Jupiter : taux de varpi de date, Simon 5.9 (transcrit) vs Meeus 31.A* — Écart possible de 7,7e-5 deg/siècle (constante de précession IAU 1976 chez Meeus).
- *Jupiter : taux de Omega de date, Simon 5.9 (transcrit) vs Meeus 31.A* — Écart possible de 7,7e-5 deg/siècle (constante de précession IAU 1976 chez Meeus).
- *Jupiter : période sidérale (j), JPL T1 vs NSSDC* — NSSDC donne la période séculaire (Simon 1994 : 4332,589 j), pas le taux local 1800-2050.
- *Jupiter : période sidérale (j), NSSDC vs Simon 1994 séculaire* — Les périodes NSSDC des planètes géantes ne suivent pas une règle unique (Jupiter = séculaire ; Saturne, Uranus, Neptune = ni séculaire ni exactement le taux JPL T1) : origine non documentée. Pour la machine, utiliser les taux JPL explicites, pas ces périodes.
- *Jupiter : période tropique (j), JPL T1 + p_A vs NSSDC* — NSSDC donne pour Jupiter la période séculaire (Simon 1994 : 4332,589 j) et non le taux local 1800-2050 (4332,817 j) ; voir le contrôle jupiter.sidereal_period_nssdc_vs_simon.
- *Jupiter : longitude moyenne J2000 (deg), JPL T1 vs NSSDC* — Les deux sont des ajustements (pas des éléments moyens au sens strict) ; les grandes inégalités expliquent les écarts pour les planètes géantes.
- *Saturne : taux de L (deg/siècle), JPL T1 (1800-2050) vs DE441 ajusté 2000-2100* — Tolérance 0,1 deg/siècle = 1/10 de l'objectif de la machine.
- *Saturne : taux de L (deg/siècle), DE441 2000-2100 vs Simon (séculaire)* — Sur 2000-2100 la grande inégalité Jupiter-Saturne accélère Saturne et ralentit Jupiter par rapport à leur mouvement séculaire.
- *Saturne : taux de L (deg/siècle), JPL T1 (local 1800-2050) vs Simon (séculaire)* — Écart = pente locale des grandes inégalités (Jupiter-Saturne ~900 ans, Uranus-Neptune ~4700 ans).
- *Saturne : (taux de date - taux J2000) Simon vs constante de précession de Simon* — Passer du repère J2000 au repère de date n'ajoute pas exactement p_A à lambda (mouvement de l'écliptique, inclinaison et nœud) : jusqu'à 2,3''/siècle (Mercure). Négligeable (<0,001 deg/siècle).
- *Saturne : L0 à J2000, Simon 1994 (transcrit) vs Meeus 31.A* — Tolérance = demi-unité du dernier chiffre de Meeus.
- *Saturne : e0 à J2000, Simon 1994 (transcrit) vs Meeus 31.A* — Tolérance = demi-unité du dernier chiffre de Meeus.
- *Saturne : i0 à J2000, Simon 1994 (transcrit) vs Meeus 31.A* — Tolérance = demi-unité du dernier chiffre de Meeus.
- *Saturne : Omega0 à J2000, Simon 1994 (transcrit) vs Meeus 31.A* — Tolérance = demi-unité du dernier chiffre de Meeus.
- *Saturne : varpi0 à J2000, Simon 1994 (transcrit) vs Meeus 31.A* — Tolérance = demi-unité du dernier chiffre de Meeus.
- *Saturne : taux de varpi de date, Simon 5.9 (transcrit) vs Meeus 31.A* — Écart possible de 7,7e-5 deg/siècle (constante de précession IAU 1976 chez Meeus).
- *Saturne : taux de Omega de date, Simon 5.9 (transcrit) vs Meeus 31.A* — Écart possible de 7,7e-5 deg/siècle (constante de précession IAU 1976 chez Meeus).
- *Saturne : période sidérale (j), JPL T1 vs NSSDC* — NSSDC (mise à jour 2025) : 10755,70 j, proche du taux local JPL (10755,93 j) ; l'ancienne valeur NSSDC 10759,22 j (utilisée dans la v1) est la période séculaire (Simon : 10759,23 j).
- *Saturne : période sidérale (j), NSSDC vs Simon 1994 séculaire* — Les périodes NSSDC des planètes géantes ne suivent pas une règle unique (Jupiter = séculaire ; Saturne, Uranus, Neptune = ni séculaire ni exactement le taux JPL T1) : origine non documentée. Pour la machine, utiliser les taux JPL explicites, pas ces périodes.
- *Saturne : longitude moyenne J2000 (deg), JPL T1 vs NSSDC* — Les deux sont des ajustements (pas des éléments moyens au sens strict) ; les grandes inégalités expliquent les écarts pour les planètes géantes.
- *Uranus : taux de L (deg/siècle), JPL T1 (1800-2050) vs DE441 ajusté 2000-2100* — Tolérance 0,1 deg/siècle = 1/10 de l'objectif de la machine.
- *Uranus : taux de L (deg/siècle), JPL T1 (local 1800-2050) vs Simon (séculaire)* — Écart = pente locale des grandes inégalités (Jupiter-Saturne ~900 ans, Uranus-Neptune ~4700 ans).
- *Uranus : (taux de date - taux J2000) Simon vs constante de précession de Simon* — Passer du repère J2000 au repère de date n'ajoute pas exactement p_A à lambda (mouvement de l'écliptique, inclinaison et nœud) : jusqu'à 2,3''/siècle (Mercure). Négligeable (<0,001 deg/siècle).
- *Uranus : L0 à J2000, Simon 1994 (transcrit) vs Meeus 31.A* — Tolérance = demi-unité du dernier chiffre de Meeus.
- *Uranus : e0 à J2000, Simon 1994 (transcrit) vs Meeus 31.A* — Tolérance = demi-unité du dernier chiffre de Meeus.
- *Uranus : i0 à J2000, Simon 1994 (transcrit) vs Meeus 31.A* — Tolérance = demi-unité du dernier chiffre de Meeus.
- *Uranus : Omega0 à J2000, Simon 1994 (transcrit) vs Meeus 31.A* — Tolérance = demi-unité du dernier chiffre de Meeus.
- *Uranus : varpi0 à J2000, Simon 1994 (transcrit) vs Meeus 31.A* — Tolérance = demi-unité du dernier chiffre de Meeus.
- *Uranus : taux de varpi de date, Simon 5.9 (transcrit) vs Meeus 31.A* — Écart possible de 7,7e-5 deg/siècle (constante de précession IAU 1976 chez Meeus).
- *Uranus : taux de Omega de date, Simon 5.9 (transcrit) vs Meeus 31.A* — Écart possible de 7,7e-5 deg/siècle (constante de précession IAU 1976 chez Meeus).
- *Uranus : période sidérale (j), NSSDC vs Simon 1994 séculaire* — Les périodes NSSDC des planètes géantes ne suivent pas une règle unique (Jupiter = séculaire ; Saturne, Uranus, Neptune = ni séculaire ni exactement le taux JPL T1) : origine non documentée. Pour la machine, utiliser les taux JPL explicites, pas ces périodes.
- *Uranus : longitude moyenne J2000 (deg), JPL T1 vs NSSDC* — Les deux sont des ajustements (pas des éléments moyens au sens strict) ; les grandes inégalités expliquent les écarts pour les planètes géantes.
- *Neptune : taux de L (deg/siècle), JPL T1 (1800-2050) vs DE441 ajusté 2000-2100* — Tolérance 0,1 deg/siècle = 1/10 de l'objectif de la machine.
- *Neptune : taux de L (deg/siècle), JPL T1 (local 1800-2050) vs Simon (séculaire)* — Écart = pente locale des grandes inégalités (Jupiter-Saturne ~900 ans, Uranus-Neptune ~4700 ans).
- *Neptune : (taux de date - taux J2000) Simon vs constante de précession de Simon* — Passer du repère J2000 au repère de date n'ajoute pas exactement p_A à lambda (mouvement de l'écliptique, inclinaison et nœud) : jusqu'à 2,3''/siècle (Mercure). Négligeable (<0,001 deg/siècle).
- *Neptune : L0 à J2000, Simon 1994 (transcrit) vs Meeus 31.A* — Tolérance = demi-unité du dernier chiffre de Meeus.
- *Neptune : e0 à J2000, Simon 1994 (transcrit) vs Meeus 31.A* — Tolérance = demi-unité du dernier chiffre de Meeus.
- *Neptune : i0 à J2000, Simon 1994 (transcrit) vs Meeus 31.A* — Tolérance = demi-unité du dernier chiffre de Meeus.
- *Neptune : Omega0 à J2000, Simon 1994 (transcrit) vs Meeus 31.A* — Tolérance = demi-unité du dernier chiffre de Meeus.
- *Neptune : varpi0 à J2000, Simon 1994 (transcrit) vs Meeus 31.A* — Tolérance = demi-unité du dernier chiffre de Meeus.
- *Neptune : taux de varpi de date, Simon 5.9 (transcrit) vs Meeus 31.A* — Écart possible de 7,7e-5 deg/siècle (constante de précession IAU 1976 chez Meeus).
- *Neptune : taux de Omega de date, Simon 5.9 (transcrit) vs Meeus 31.A* — Écart possible de 7,7e-5 deg/siècle (constante de précession IAU 1976 chez Meeus).
- *Neptune : période sidérale (j), NSSDC vs Simon 1994 séculaire* — Les périodes NSSDC des planètes géantes ne suivent pas une règle unique (Jupiter = séculaire ; Saturne, Uranus, Neptune = ni séculaire ni exactement le taux JPL T1) : origine non documentée. Pour la machine, utiliser les taux JPL explicites, pas ces périodes.
- *Neptune : longitude moyenne J2000 (deg), JPL T1 vs NSSDC* — Les deux sont des ajustements (pas des éléments moyens au sens strict) ; les grandes inégalités expliquent les écarts pour les planètes géantes.
- *Pluton : taux de L (deg/siècle), JPL T1 (1800-2050) vs DE441 ajusté 2000-2100* — Tolérance 0,1 deg/siècle = 1/10 de l'objectif de la machine.
- *Jupiter : amplitude de la grande inégalité (deg), JPL 2b vs Schlyter* — JPL 2b est un ajustement de M (perturbation globale) sur 6000 ans ; Schlyter donne le seul terme 2Mj-5Ms. Même ordre de grandeur.
- *Saturne : amplitude de la grande inégalité (deg), JPL 2b vs Schlyter* — JPL 2b est un ajustement de M (perturbation globale) sur 6000 ans ; Schlyter donne le seul terme 2Mj-5Ms. Même ordre de grandeur.
- *Mois sidereal (j) : Simon 1994 / IERS vs Chapront et al. 2002* — Simon 1994 (ajustement DE200/LE200) vs Chapront 2002 (tirs laser-Lune) : écart <1e-8 j, soit <1 ms par mois.
- *Mois tropical (j) : Simon 1994 / IERS vs Chapront et al. 2002* — Simon 1994 (ajustement DE200/LE200) vs Chapront 2002 (tirs laser-Lune) : écart <1e-8 j, soit <1 ms par mois.
- *Mois synodic (j) : Simon 1994 / IERS vs Chapront et al. 2002* — Simon 1994 (ajustement DE200/LE200) vs Chapront 2002 (tirs laser-Lune) : écart <1e-8 j, soit <1 ms par mois.
- *Mois anomalistic (j) : Simon 1994 / IERS vs Chapront et al. 2002* — Simon 1994 (ajustement DE200/LE200) vs Chapront 2002 (tirs laser-Lune) : écart <1e-8 j, soit <1 ms par mois.
- *Mois draconic (j) : Simon 1994 / IERS vs Chapront et al. 2002* — Simon 1994 (ajustement DE200/LE200) vs Chapront 2002 (tirs laser-Lune) : écart <1e-8 j, soit <1 ms par mois.
- *Lune : taux de D (deg/siècle), Meeus ch. 47 vs IERS 2010 (Simon 1994)* — Meeus 47 provient d'ELP 2000-82 / Chapront-Touzé & Chapront 1991 ; écarts de quelques 1e-5 deg/siècle.
- *Lune : taux de M_prime (deg/siècle), Meeus ch. 47 vs IERS 2010 (Simon 1994)* — Meeus 47 provient d'ELP 2000-82 / Chapront-Touzé & Chapront 1991 ; écarts de quelques 1e-5 deg/siècle.
- *Lune : taux de F (deg/siècle), Meeus ch. 47 vs IERS 2010 (Simon 1994)* — Meeus 47 provient d'ELP 2000-82 / Chapront-Touzé & Chapront 1991 ; écarts de quelques 1e-5 deg/siècle.
- *Lune : taux de Omega (deg/siècle), Meeus ch. 47 vs IERS 2010 (Simon 1994)* — Meeus 47 provient d'ELP 2000-82 / Chapront-Touzé & Chapront 1991 ; écarts de quelques 1e-5 deg/siècle.
- *Lune : taux de M_sun (deg/siècle), Meeus ch. 47 vs IERS 2010 (Simon 1994)* — Meeus 47 provient d'ELP 2000-82 / Chapront-Touzé & Chapront 1991 ; écarts de quelques 1e-5 deg/siècle.
- *Période du périgée (j) : Simon (sidérale) vs NASA (3231,6 j, dite 'par rapport aux étoiles')* — La valeur NASA (0,11140 deg/j) est en fait le taux par rapport à l'équinoxe (tropique : 3231,50 j) ; la période sidérale est 3232,60 j. Incohérence de la page NASA.
- *Lune, longitude, equation_annuelle (deg) : Meeus 47.A vs Brown (Wikipedia)* — Équation annuelle : Meeus la multiplie en plus par E = 1 - 0,002516 T.
- *Lune, longitude, terme_2D_moins_2Mp (deg) : Meeus 47.A vs Schlyter (3 décimales)* — Schlyter n'est pas un simple arrondi de Meeus (autre théorie, éléments osculateurs) : écart de 0,0006 deg, sans conséquence.
- *Lune, longitude, terme_2D_moins_M_moins_Mp (deg) : Meeus 47.A vs Schlyter (3 décimales)* — Schlyter n'est pas un simple arrondi de Meeus (autre théorie, éléments osculateurs) : écart de 0,0006 deg, sans conséquence.
- *Lune, longitude, terme_2D_plus_Mp (deg) : Meeus 47.A vs Schlyter (3 décimales)* — Schlyter n'est pas un simple arrondi de Meeus (autre théorie, éléments osculateurs) : écart de 0,0006 deg, sans conséquence.
- *Lune, longitude, terme_2D_moins_M (deg) : Meeus 47.A vs Schlyter (3 décimales)* — Schlyter n'est pas un simple arrondi de Meeus (autre théorie, éléments osculateurs) : écart de 0,0006 deg, sans conséquence.
- *Lune, longitude, terme_M_moins_Mp (deg) : Meeus 47.A vs Schlyter (3 décimales)* — Schlyter n'est pas un simple arrondi de Meeus (autre théorie, éléments osculateurs) : écart de 0,0006 deg, sans conséquence.
- *Lune, longitude, terme_M_plus_Mp (deg) : Meeus 47.A vs Schlyter (3 décimales)* — Schlyter n'est pas un simple arrondi de Meeus (autre théorie, éléments osculateurs) : écart de 0,0006 deg, sans conséquence.
- *Saros (j) : 223 x mois synodique vs NASA (6585,3223)* — La page NASA donne 6585,3223 j alors que 223 x 29,530589 = 6585,3213 j : coquille de la page (écart 1,4 min).
- *Limite écliptique solaire max (deg) : géométrie vs NASA (18,59)* — Calcul statique (Lune immobile) ; la NASA tient compte du mouvement relatif pendant l'événement.
- *io : période synodique / Soleil (j), E5 - Jupiter (JPL) vs Meeus ch. 44* — Tolérance = arrondi du taux de Meeus (7 décimales) + choix du taux de Jupiter.
- *io : 'P' de la table JPL = période anomalistique ? (360/(n - varpi'))* — La colonne P du JPL est la période de l'anomalie moyenne (ellipse en précession), pas la période sidérale. Pour Io et Europe le périjove forcé rétrograde en ~1,3-1,4 an (lié à la résonance), d'où P plus courte de 0,4-0,7 %.
- *europa : période synodique / Soleil (j), E5 - Jupiter (JPL) vs Meeus ch. 44* — Tolérance = arrondi du taux de Meeus (7 décimales) + choix du taux de Jupiter.
- *europa : 'P' de la table JPL = période anomalistique ? (360/(n - varpi'))* — La colonne P du JPL est la période de l'anomalie moyenne (ellipse en précession), pas la période sidérale. Pour Io et Europe le périjove forcé rétrograde en ~1,3-1,4 an (lié à la résonance), d'où P plus courte de 0,4-0,7 %.
- *ganymede : période synodique / Soleil (j), E5 - Jupiter (JPL) vs Meeus ch. 44* — Tolérance = arrondi du taux de Meeus (6 décimales) + choix du taux de Jupiter.
- *ganymede : 'P' de la table JPL = période anomalistique ? (360/(n - varpi'))* — La colonne P du JPL est la période de l'anomalie moyenne (ellipse en précession), pas la période sidérale. Pour Io et Europe le périjove forcé rétrograde en ~1,3-1,4 an (lié à la résonance), d'où P plus courte de 0,4-0,7 %.
- *callisto : période synodique / Soleil (j), E5 - Jupiter (JPL) vs Meeus ch. 44* — Tolérance = arrondi du taux de Meeus (5 décimales) + choix du taux de Jupiter.
- *callisto : 'P' de la table JPL = période anomalistique ? (360/(n - varpi'))* — La colonne P du JPL est la période de l'anomalie moyenne (ellipse en précession), pas la période sidérale. Pour Io et Europe le périjove forcé rétrograde en ~1,3-1,4 an (lié à la résonance), d'où P plus courte de 0,4-0,7 %.
- *Pluton : période sidérale (j), JPL T1 (archivée) vs NSSDC* — Le taux JPL est local (1800-2050) ; Pluton est fortement perturbé par Neptune (résonance 3:2).

## 10. Sources

- **JPL_APPROX** — E.M. Standish & J.G. Williams, 'Keplerian Elements for Approximate Positions of the Major Planets', JPL Solar System Dynamics (tables 1, 2a, 2b). https://ssd.jpl.nasa.gov/planets/approx_pos.html — copie locale : `v2/research/sources/jpl_approx_pos_2026-10-03.txt`
- **JPL_APPROX_2019** — Same JPL tables, archived text version that still contained Pluto (Wayback Machine, 2019). https://web.archive.org/web/2019/https://ssd.jpl.nasa.gov/txt/p_elem_t1.txt ; https://web.archive.org/web/2019/https://ssd.jpl.nasa.gov/txt/p_elem_t2.txt — copie locale : `v2/research/sources/jpl_p_elem_t1_archived_2019.txt`
- **SIMON1994** — J.-L. Simon, P. Bretagnon, J. Chapront, M. Chapront-Touzé, G. Francou, J. Laskar, 'Numerical expressions for precession formulae and mean elements for the Moon and the planets', A&A 282, 663-683 (1994) -- sect. 3.4-3.5 (Moon), 5.8 (planets, J2000), 5.9 (planets, of date). VSOP87 / JASON84 / ELP 2000-82 mean elements. https://articles.adsabs.harvard.edu/pdf/1994A%26A...282..663S ; https://ui.adsabs.harvard.edu/abs/1994A&A...282..663S
- **IERS2010** — IERS Conventions (2010), IERS Technical Note 36, chapter 5 (G. Petit & B. Luzum eds.): eq. 5.14 (ERA), 5.32 (GMST), 5.39-5.40 (IAU 2006 precession, obliquity), 5.43 (Delaunay arguments, Simon et al. 1994), 5.44 (planetary mean longitudes), table 5.1a (lunar periods), table 5.3a (nutation). https://iers-conventions.obspm.fr/content/chapter5/icc5.pdf
- **MEEUS1998** — J. Meeus, Astronomical Algorithms, 2nd ed., Willmann-Bell (1998): ch. 12, 22, 25, 28, 31 (table 31.A), 44, 47 (tables 47.A/47.B), 49, 54. Book not online: coefficients transcribed through the open-source (MIT) implementation soniakeys/meeus, files planetelements.go, moonposition.go, jupitermoons.go, eqtime.go, nutation.go, solar.go, sidereal.go, moonphase.go, eclipse.go. https://github.com/soniakeys/meeus/tree/master/v3
- **CAPITAINE2003** — N. Capitaine, P.T. Wallace, J. Chapront, 'Expressions for IAU 2000 precession quantities', A&A 412, 567 (2003) = IAU 2006 precession (P03); general precession p_A quoted through Wikipedia 'Axial precession'. https://en.wikipedia.org/wiki/Axial_precession ; https://doi.org/10.1051/0004-6361:20031539
- **LASKAR1986_TY** — Mean tropical year polynomial (McCarthy & Seidelmann 2009, from Laskar 1986), quoted by Wikipedia 'Tropical year'; also the equinox/solstice years of Meeus & Savoie (1992). https://en.wikipedia.org/wiki/Tropical_year
- **CHAPRONT2002** — J. Chapront, M. Chapront-Touzé, G. Francou, 'A new determination of lunar orbital parameters, precession constant and tidal acceleration from LLR measurements', A&A 387, 700 (2002); month lengths quoted by Wikipedia 'Lunar month'. https://en.wikipedia.org/wiki/Lunar_month ; https://doi.org/10.1051/0004-6361:20020420
- **NSSDC** — NASA NSSDCA Planetary Fact Sheets (D.R. Williams; pages updated Jan 2024 - May 2025). https://nssdc.gsfc.nasa.gov/planetary/factsheet/ — copie locale : `v2/research/sources/nssdc_factsheets_extract_2026-10-03.json`
- **NSSDC_MOON** — NASA NSSDCA Moon Fact Sheet. https://nssdc.gsfc.nasa.gov/planetary/factsheet/moonfact.html
- **NSSDC_JOVSAT** — NASA NSSDCA Jovian Satellite Fact Sheet. https://nssdc.gsfc.nasa.gov/planetary/factsheet/joviansatfact.html
- **JPL_SAT** — JPL SSD, Planetary Satellite Mean Elements (ephemeris JUP365, Jacobson 2021). https://ssd.jpl.nasa.gov/sats/elem/sep.html — copie locale : `v2/research/sources/jpl_sat_mean_elements_galilean_2026-10-03.txt`
- **LIESKE_E5** — J.H. Lieske, 'Galilean satellite ephemerides E5', A&A Suppl. 129, 205 (1998); mean longitudes l1..l4 as given in Meeus ch. 44 (soniakeys jupitermoons.go). https://github.com/soniakeys/meeus/blob/master/v3/jupitermoons/jupitermoons.go
- **CELLETTI2021** — A. Celletti et al., 'Laplace-like resonances with tidal effects', A&A (2021), arXiv:2109.02694 -- 'Lieske (1998) observed ... Phi_L = 180 deg up to a libration with small amplitude and period of about 2071 days'. https://arxiv.org/abs/2109.02694
- **WIKI_RESONANCE** — Wikipedia 'Orbital resonance' (Laplace resonance; libration amplitude 0.03 deg, period ~2000 d, citing Sinclair 1975). https://en.wikipedia.org/wiki/Orbital_resonance
- **NASA_ECL** — F. Espenak (NASA GSFC eclipse web site): 'Periodicity of Solar Eclipses', 'Periodicity of Lunar Eclipses', 'Saros', 'Eclipses and the Moon's Orbit'. https://eclipse.gsfc.nasa.gov/SEsaros/SEperiodicity.html ; https://eclipse.gsfc.nasa.gov/SEhelp/moonorbit.html ; https://eclipse.gsfc.nasa.gov/SEsaros/SEsaros.html ; https://eclipse.gsfc.nasa.gov/LEsaros/LEperiodicity.html
- **WIKI_ECL_CYCLE** — Wikipedia 'Eclipse cycle' (table from Meeus 1991/1997). https://en.wikipedia.org/wiki/Eclipse_cycle
- **WIKI_SOLAR_ECLIPSE** — Wikipedia 'Solar eclipse' (Sun within about 15 to 18 deg of a node; 10 to 12 deg for central eclipses -- Littmann, Espenak & Willcox, Totality). https://en.wikipedia.org/wiki/Solar_eclipse
- **WIKI_GAMMA** — Wikipedia 'Gamma (eclipse)' (central limit 0.9972; partial limit 1.525-1.571; sign conventions; Meeus). https://en.wikipedia.org/wiki/Gamma_(eclipse)
- **HOLMES_ECL** — S. Holmes, 'Eclipses - the theory' (quotes Meeus' major ecliptic limits 18 deg 24' solar, 12 deg 08' lunar). Secondary, non-academic source: used only as an indicator. https://freehostspace.firstcloudit.com/steveholmes/eclfact1.htm
- **WIKI_EOT** — Wikipedia 'Equation of time' (two-sine approximation; component amplitudes 7.66 and 9.87 min; extremes; Hughes et al. 1989, MNRAS 238, 1529). https://en.wikipedia.org/wiki/Equation_of_time
- **WIKI_SIDEREAL** — Wikipedia 'Sidereal time' (Urban & Seidelmann 2013, Explanatory Supplement 3rd ed.). https://en.wikipedia.org/wiki/Sidereal_time
- **WIKI_GREGORIAN** — Wikipedia 'Gregorian calendar'. https://en.wikipedia.org/wiki/Gregorian_calendar
- **WIKI_AXIAL_TILT** — Wikipedia 'Axial tilt' (IAU 2006 and IAU 1976/1980 obliquity polynomials; long-term range and 41,040-yr period, Laskar). https://en.wikipedia.org/wiki/Axial_tilt
- **WIKI_YEAR** — Wikipedia 'Year' (sidereal year 365.256363004 d, anomalistic year 365.259636 d, draconic year 346.620075883 d). https://en.wikipedia.org/wiki/Year
- **WIKI_LUNAR_THEORY** — Wikipedia 'Lunar theory' (main longitude terms of E.W. Brown, Tables of the Motion of the Moon, 1919). https://en.wikipedia.org/wiki/Lunar_theory
- **AA_LOWPREC** — Astronomical Almanac low-precision lunar formulae (Brown-based), quoted in D.G. Simpson, 'An alternative lunar ephemeris model for on-board flight software use', NASA GSFC Flight Mechanics Symposium (1999), eq. 1-3. https://caps.gsfc.nasa.gov/simpson/pubs/slunar.pdf
- **SCHLYTER** — P. Schlyter, 'Computing planetary positions' (sect. 9-10: lunar perturbations; Jupiter-Saturn great inequality). https://stjarnhimlen.se/comp/ppcomp.html
- **JPL_HORIZONS** — JPL Horizons API, ephemeris DE441: osculating elements of the planetary system barycenters (heliocentric and SSB-centred), ecliptic & equinox J2000, TDB, 2000-01-01 to 2100-01-01 every 10 d; linear least-squares fit of L = Omega + omega + M (v2/tools/fetch_horizons_rates.py). https://ssd.jpl.nasa.gov/api/horizons.api — copie locale : `v2/research/sources/horizons/horizons_rates_2000_2100.json (+ raw rows *.csv.gz)`
- **USNO_DT** — USNO, TT-UT predictions (deltat.preds). https://maia.usno.navy.mil/ser7/deltat.preds — copie locale : `v2/research/sources/usno_deltat_preds.txt`

