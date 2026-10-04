-- GÉNÉRÉ par v2/tools/make_lean_v2.py depuis v2/spec/trains.json et v2/spec/architecture.json.
-- Ne pas éditer à la main : relancer le générateur.

import Mathlib

/-!
# Anticythère 2.0 : cinématique moyenne des 70 arbres

`ω x` est la vitesse MOYENNE de l'arbre `x`, en tours par jour, signée dans le sens astronomique direct
(`conventions.sign` de trains.json : + = longitudes croissantes) ; `J` est l'arbre-jour (entrée, 1 tour par
jour solaire moyen). `Kinematics ω` réunit une loi par arbre, écrite depuis `shafts[]` : train (produit des
dents), différentiel (combinaison exacte), unité non linéaire (un tour par tour : vitesses moyennes égales),
pas à pas (croix de Malte). `rate` est la table des vitesses DÉCLARÉES (`rate_turns_per_day`).

Résultats : `determined` (toute vitesse admissible vaut ω J · rate : la table déclarée découle des dents),
`consistent` (la table vérifie toutes les lois, pour toute vitesse de J), `moves` (la machine peut tourner) et
`one_dof` (les vitesses admissibles forment exactement une droite : un seul degré de liberté).
Les sens physiques (`phys`) et la géométrie sont traités dans `Ratios` et `Architecture`.
-/

namespace AnticythereV2

/-- Les 70 arbres de `trains.json` (`shafts[]`), dans l'ordre du fichier. -/
inductive Shaft where
  | J -- input : Arbre-jour J (manivelle ; 1 tour par jour solaire moyen)
  | W -- train : Roue de la semaine (1 tour en 7 jours)
  | Y -- train : Roue de l’année Y : longitude moyenne de la Terre, repère J2000 (Soleil moyen = Y + 180°)
  | mercury_L -- train : Mercure : longitude moyenne héliocentrique (repère J2000)
  | venus_L -- train : Vénus : longitude moyenne héliocentrique (repère J2000)
  | mars_L -- train : Mars : longitude moyenne héliocentrique (repère J2000)
  | jupiter_L -- train : Jupiter : longitude moyenne héliocentrique (repère J2000)
  | saturn_L -- train : Saturne : longitude moyenne héliocentrique (repère J2000)
  | uranus_L -- train : Uranus : longitude moyenne héliocentrique (repère J2000)
  | neptune_L -- train : Neptune : longitude moyenne héliocentrique (repère J2000)
  | moon_L -- train : Lune : longitude moyenne (repère J2000)
  | moon_perigee -- train : Lune : porte-satellite du périgée ϖ (étage d’anomalie)
  | moon_node -- train : Lune : porte-nœuds Ω (aiguille du Dragon, étage de réduction, coulisse d’éclipse)
  | evection_carrier -- diff : Lune : porte-satellite de l’évection 2λ☉ − ϖ (différentiel, sans nouveau rapport approché)
  | precession_ring -- train : Anneau du zodiaque tropique (précession ; 1 tour rétrograde en ~25 766 ans)
  | sun_trop -- diff : Soleil moyen tropique X = Y + p (différentiel)
  | stellar -- diff : Rotation stellaire S = J + Y (différentiel ; mène le globe-tellurion)
  | gmst -- diff : Temps sidéral moyen (TSMG) = J + X (différentiel)
  | earth_true -- unit : Terre vraie λ (sortie de l’unité de Kepler de la Terre)
  | lambda_trop -- diff : Soleil vrai tropique λ + p (entrée du joint de Hooke)
  | alpha_sun -- unit : Ascension droite vraie du Soleil α (sortie du joint de Hooke)
  | eot -- diff : Équation du temps EdT = X − α (différentiel ; vitesse moyenne nulle)
  | eot_dial -- train : Aiguille de l’équation du temps (agrandissement ×10)
  | tellurion -- train : Globe-tellurion de l’orrery (chaîne 1:1 le long du bras de la Terre : angle absolu = S)
  | cal_cross_main -- stepper : Croix de Malte principale (6 fentes ; 1 pas par jour)
  | cal_cross_skip -- stepper : Croix de saut (6 fentes ; 1 pas la nuit du 28 février des années communes)
  | cal_sum -- diff : Anneau des dates (366 positions) = (croix principale + croix de saut)/61
  | cal_prog4 -- train : Roue-programme de 4 ans (came C4)
  | cal_prog100 -- train : Roue-programme de 100 ans (came C100)
  | cal_prog400 -- train : Roue-programme de 400 ans (came C400)
  | mercury_true -- unit : Mercure vraie (sortie de l’unité de Kepler)
  | venus_true -- unit : Vénus vraie (sortie de l’unité de Kepler)
  | mars_true -- unit : Mars vraie (sortie de l’unité de Kepler)
  | jupiter_true -- unit : Jupiter vraie (sortie de l’unité de Kepler)
  | saturn_true -- unit : Saturne vraie (sortie de l’unité de Kepler)
  | uranus_true -- unit : Uranus vraie (sortie de l’unité de Kepler)
  | neptune_true -- unit : Neptune vraie (sortie de l’unité de Kepler)
  | mercury_geo -- unit : Mercure : aiguille géocentrique (module vectoriel)
  | venus_geo -- unit : Vénus : aiguille géocentrique (module vectoriel)
  | mars_geo -- unit : Mars : aiguille géocentrique (module vectoriel)
  | jupiter_geo -- unit : Jupiter : aiguille géocentrique (module vectoriel)
  | saturn_geo -- unit : Saturne : aiguille géocentrique (module vectoriel)
  | uranus_geo -- unit : Uranus : aiguille géocentrique (module vectoriel)
  | neptune_geo -- unit : Neptune : aiguille géocentrique (module vectoriel)
  | sun_geo -- unit : Soleil vrai : aiguille géocentrique (= Terre vraie + 180°)
  | orrery_earth -- train : Orrery : tube de Terre (renvoi d’angle 1:1 vers le couvercle)
  | orrery_mercury -- train : Orrery : tube de Mercure (renvoi d’angle 1:1 vers le couvercle)
  | orrery_venus -- train : Orrery : tube de Vénus (renvoi d’angle 1:1 vers le couvercle)
  | orrery_mars -- train : Orrery : tube de Mars (renvoi d’angle 1:1 vers le couvercle)
  | orrery_jupiter -- train : Orrery : tube de Jupiter (renvoi d’angle 1:1 vers le couvercle)
  | orrery_saturn -- train : Orrery : tube de Saturne (renvoi d’angle 1:1 vers le couvercle)
  | orrery_uranus -- train : Orrery : tube de Uranus (renvoi d’angle 1:1 vers le couvercle)
  | orrery_neptune -- train : Orrery : tube de Neptune (renvoi d’angle 1:1 vers le couvercle)
  | mars_epicyclet -- train : Mars : épicyclet correcteur (angle absolu 3L − 2ϖ, ϖ figé : couple 3:1)
  | mercury_E -- unit : Mercure : arbre de l’anomalie excentrique E (résolveur)
  | mercury_counter_arm -- train : Mercure : bras (a − b)/2 à l’angle ϖ − E (inverseur conique coaxial 1:1)
  | annual_eq -- diff : Lune : moteur de l’équation annuelle (3/31)(λ☉ vrai − λ☉ moyen) (vitesse moyenne nulle)
  | moon_true -- unit : Lune vraie : aiguille (sortie de la cascade à 5 étages)
  | moon_phase -- unit : Boule de phase (rotation relative à l’aiguille de la Lune = Lune vraie − Soleil vrai)
  | saros -- train : Aiguille du Saros (1 tour = 223 lunaisons)
  | exeligmos -- train : Aiguille de l’Exeligmos (1 tour = 3 Saros)
  | ganymede -- train : Ganymède (train direct)
  | nu -- train : Arbre ν = n_Io − 2n_Eu (ligne des conjonctions à −ν)
  | europa -- diff : Europe = 2·Ganymède + ν (différentiel)
  | io -- diff : Io = 2·Europe + ν (différentiel)
  | callisto -- train : Callisto (train direct, hors résonance)
  | gmst_direct -- train : Variante : temps sidéral par un train direct depuis J (au lieu du différentiel)
  | synodic -- diff : Variante : arbre synodique moyen D = L − Y (différentiel)
  | saros_223 -- train : Variante : Saros exact avec une roue de 223 dents (hommage à b1)
  | mars_apsides -- train : Option : plateau d’apsides de Mars (1 tour en ~81 000 ans)
  deriving DecidableEq, Repr

/-- Les lois de transmission moyennes, une par arbre (sauf l'entrée `J`). -/
structure Kinematics (ω : Shaft → ℚ) : Prop where
  /-- `W` : Roue de la semaine (1 tour en 7 jours). Train 10:70 (ext) depuis `J`, signe +1 : Π menées · ω W = signe · Π menantes · ω J. -/
  W : 70 * ω .W = 10 * ω .J
  /-- `Y` : Roue de l’année Y : longitude moyenne de la Terre, repère J2000 (Soleil moyen = Y + 180°). Train 31:180 (ext) · 19:144 (ext) · 10:83 (ext) depuis `J`, signe +1 : Π menées · ω Y = signe · Π menantes · ω J. -/
  Y : 180 * 144 * 83 * ω .Y = 31 * 19 * 10 * ω .J
  /-- `mercury_L` : Mercure : longitude moyenne héliocentrique (repère J2000). Train 37:17 (ext) · 64:31 (ext) · 73:79 (ext), pignon fou de 20 depuis `Y`, signe +1 : Π menées · ω mercury_L = signe · Π menantes · ω Y. -/
  mercury_L : 17 * 31 * 79 * ω .mercury_L = 37 * 64 * 73 * ω .Y
  /-- `venus_L` : Vénus : longitude moyenne héliocentrique (repère J2000). Train 124:67 (ext) · 166:189 (ext) depuis `Y`, signe +1 : Π menées · ω venus_L = signe · Π menantes · ω Y. -/
  venus_L : 67 * 189 * ω .venus_L = 124 * 166 * ω .Y
  /-- `mars_L` : Mars : longitude moyenne héliocentrique (repère J2000). Train 97:88 (ext) · 41:85 (ext) depuis `Y`, signe +1 : Π menées · ω mars_L = signe · Π menantes · ω Y. -/
  mars_L : 88 * 85 * ω .mars_L = 97 * 41 * ω .Y
  /-- `jupiter_L` : Jupiter : longitude moyenne héliocentrique (repère J2000). Train 10:26 (ext) · 16:73 (ext) depuis `Y`, signe +1 : Π menées · ω jupiter_L = signe · Π menantes · ω Y. -/
  jupiter_L : 26 * 73 * ω .jupiter_L = 10 * 16 * ω .Y
  /-- `saturn_L` : Saturne : longitude moyenne héliocentrique (repère J2000). Train 10:41 (ext) · 11:79 (ext) depuis `Y`, signe +1 : Π menées · ω saturn_L = signe · Π menantes · ω Y. -/
  saturn_L : 41 * 79 * ω .saturn_L = 10 * 11 * ω .Y
  /-- `uranus_L` : Uranus : longitude moyenne héliocentrique (repère J2000). Train 10:84 (ext) · 10:100 (ext) depuis `Y`, signe +1 : Π menées · ω uranus_L = signe · Π menantes · ω Y. -/
  uranus_L : 84 * 100 * ω .uranus_L = 10 * 10 * ω .Y
  /-- `neptune_L` : Neptune : longitude moyenne héliocentrique (repère J2000). Train 12:148 (ext) · 11:147 (ext) depuis `Y`, signe +1 : Π menées · ω neptune_L = signe · Π menantes · ω Y. -/
  neptune_L : 148 * 147 * ω .neptune_L = 12 * 11 * ω .Y
  /-- `moon_L` : Lune : longitude moyenne (repère J2000). Train 11:25 (ext) · 22:75 (ext) · 19:67 (ext) depuis `J`, signe +1 : Π menées · ω moon_L = signe · Π menantes · ω J. -/
  moon_L : 25 * 75 * 67 * ω .moon_L = 11 * 22 * 19 * ω .J
  /-- `moon_perigee` : Lune : porte-satellite du périgée ϖ (étage d’anomalie). Train 47:105 (ext) · 26:103 (ext) depuis `Y`, signe +1 : Π menées · ω moon_perigee = signe · Π menantes · ω Y. -/
  moon_perigee : 105 * 103 * ω .moon_perigee = 47 * 26 * ω .Y
  /-- `moon_node` : Lune : porte-nœuds Ω (aiguille du Dragon, étage de réduction, coulisse d’éclipse). Train 12:43 (ext) · 21:109 (ext), pignon fou de 20 depuis `Y`, signe -1 : Π menées · ω moon_node = signe · Π menantes · ω Y. -/
  moon_node : 43 * 109 * ω .moon_node = -(12 * 21) * ω .Y
  /-- `evection_carrier` : Lune : porte-satellite de l’évection 2λ☉ − ϖ (différentiel, sans nouveau rapport approché). Différentiel. -/
  evection_carrier : ω .evection_carrier = 2 * ω .Y - ω .moon_perigee
  /-- `precession_ring` : Anneau du zodiaque tropique (précession ; 1 tour rétrograde en ~25 766 ans). Train 10:131 (ext) · 15:179 (int) depuis `neptune_L`, signe -1 : Π menées · ω precession_ring = signe · Π menantes · ω neptune_L. -/
  precession_ring : 131 * 179 * ω .precession_ring = -(10 * 15) * ω .neptune_L
  /-- `sun_trop` : Soleil moyen tropique X = Y + p (différentiel). Différentiel. -/
  sun_trop : ω .sun_trop = ω .Y - ω .precession_ring
  /-- `stellar` : Rotation stellaire S = J + Y (différentiel ; mène le globe-tellurion). Différentiel. -/
  stellar : ω .stellar = ω .J + ω .Y
  /-- `gmst` : Temps sidéral moyen (TSMG) = J + X (différentiel). Différentiel. -/
  gmst : ω .gmst = ω .J + ω .sun_trop
  /-- `earth_true` : Terre vraie λ (sortie de l’unité de Kepler de la Terre). Unité non linéaire (unité de Kepler (équant bissecté) : un tour par tour) : un tour de sortie par tour d'entrée, donc égalité des vitesses MOYENNES. -/
  earth_true : ω .earth_true = ω .Y
  /-- `lambda_trop` : Soleil vrai tropique λ + p (entrée du joint de Hooke). Différentiel. -/
  lambda_trop : ω .lambda_trop = ω .earth_true - ω .precession_ring
  /-- `alpha_sun` : Ascension droite vraie du Soleil α (sortie du joint de Hooke). Unité non linéaire (joint de Hooke plié à ε = 23,44° : tan α = cos ε · tan λ, un tour par tour) : un tour de sortie par tour d'entrée, donc égalité des vitesses MOYENNES. -/
  alpha_sun : ω .alpha_sun = ω .lambda_trop
  /-- `eot` : Équation du temps EdT = X − α (différentiel ; vitesse moyenne nulle). Différentiel. -/
  eot : ω .eot = ω .sun_trop - ω .alpha_sun
  /-- `eot_dial` : Aiguille de l’équation du temps (agrandissement ×10). Train 120:12 (ext) depuis `eot`, signe +1 : Π menées · ω eot_dial = signe · Π menantes · ω eot. -/
  eot_dial : 12 * ω .eot_dial = 120 * ω .eot
  /-- `tellurion` : Globe-tellurion de l’orrery (chaîne 1:1 le long du bras de la Terre : angle absolu = S). Train 40:40 (chaîne) depuis `stellar`, signe +1 : Π menées · ω tellurion = signe · Π menantes · ω stellar. -/
  tellurion : 40 * ω .tellurion = 40 * ω .stellar
  /-- `cal_cross_main` : Croix de Malte principale (6 fentes ; 1 pas par jour). Pas à pas : 6 pas par tour, 1 pas par jour en moyenne (jour = tour de J). -/
  cal_cross_main : 6 * ω .cal_cross_main = 1 * ω .J
  /-- `cal_cross_skip` : Croix de saut (6 fentes ; 1 pas la nuit du 28 février des années communes). Pas à pas : 6 pas par tour, 303 / 146097 pas par jour en moyenne (jour = tour de J). -/
  cal_cross_skip : 6 * ω .cal_cross_skip = 303 / 146097 * ω .J
  /-- `cal_sum` : Anneau des dates (366 positions) = (croix principale + croix de saut)/61. Différentiel. -/
  cal_sum : ω .cal_sum = 1 / 61 * ω .cal_cross_main + 1 / 61 * ω .cal_cross_skip
  /-- `cal_prog4` : Roue-programme de 4 ans (came C4). Train 15:60 (ext) depuis `cal_sum`, signe +1 : Π menées · ω cal_prog4 = signe · Π menantes · ω cal_sum. -/
  cal_prog4 : 60 * ω .cal_prog4 = 15 * ω .cal_sum
  /-- `cal_prog100` : Roue-programme de 100 ans (came C100). Train 12:60 (ext) · 12:60 (ext) depuis `cal_prog4`, signe +1 : Π menées · ω cal_prog100 = signe · Π menantes · ω cal_prog4. -/
  cal_prog100 : 60 * 60 * ω .cal_prog100 = 12 * 12 * ω .cal_prog4
  /-- `cal_prog400` : Roue-programme de 400 ans (came C400). Train 15:60 (ext) depuis `cal_prog100`, signe +1 : Π menées · ω cal_prog400 = signe · Π menantes · ω cal_prog100. -/
  cal_prog400 : 60 * ω .cal_prog400 = 15 * ω .cal_prog100
  /-- `mercury_true` : Mercure vraie (sortie de l’unité de Kepler). Unité non linéaire (résolveur de Kepler (RK) + ellipse à deux bras : un tour par tour) : un tour de sortie par tour d'entrée, donc égalité des vitesses MOYENNES. -/
  mercury_true : ω .mercury_true = ω .mercury_L
  /-- `venus_true` : Vénus vraie (sortie de l’unité de Kepler). Unité non linéaire (équant bissecté : un tour par tour) : un tour de sortie par tour d'entrée, donc égalité des vitesses MOYENNES. -/
  venus_true : ω .venus_true = ω .venus_L
  /-- `mars_true` : Mars vraie (sortie de l’unité de Kepler). Unité non linéaire (équant + épicyclet (EQE) : un tour par tour) : un tour de sortie par tour d'entrée, donc égalité des vitesses MOYENNES. -/
  mars_true : ω .mars_true = ω .mars_L
  /-- `jupiter_true` : Jupiter vraie (sortie de l’unité de Kepler). Unité non linéaire (équant bissecté : un tour par tour) : un tour de sortie par tour d'entrée, donc égalité des vitesses MOYENNES. -/
  jupiter_true : ω .jupiter_true = ω .jupiter_L
  /-- `saturn_true` : Saturne vraie (sortie de l’unité de Kepler). Unité non linéaire (équant bissecté : un tour par tour) : un tour de sortie par tour d'entrée, donc égalité des vitesses MOYENNES. -/
  saturn_true : ω .saturn_true = ω .saturn_L
  /-- `uranus_true` : Uranus vraie (sortie de l’unité de Kepler). Unité non linéaire (équant bissecté : un tour par tour) : un tour de sortie par tour d'entrée, donc égalité des vitesses MOYENNES. -/
  uranus_true : ω .uranus_true = ω .uranus_L
  /-- `neptune_true` : Neptune vraie (sortie de l’unité de Kepler). Unité non linéaire (équant bissecté : un tour par tour) : un tour de sortie par tour d'entrée, donc égalité des vitesses MOYENNES. -/
  neptune_true : ω .neptune_true = ω .neptune_L
  /-- `mercury_geo` : Mercure : aiguille géocentrique (module vectoriel). Unité non linéaire (module vectoriel (suiveur) : en moyenne le Soleil (planète intérieure)) : un tour de sortie par tour d'entrée, donc égalité des vitesses MOYENNES. -/
  mercury_geo : ω .mercury_geo = ω .Y
  /-- `venus_geo` : Vénus : aiguille géocentrique (module vectoriel). Unité non linéaire (module vectoriel (suiveur) : en moyenne le Soleil (planète intérieure)) : un tour de sortie par tour d'entrée, donc égalité des vitesses MOYENNES. -/
  venus_geo : ω .venus_geo = ω .Y
  /-- `mars_geo` : Mars : aiguille géocentrique (module vectoriel). Unité non linéaire (module vectoriel (suiveur) : en moyenne la planète (planète extérieure)) : un tour de sortie par tour d'entrée, donc égalité des vitesses MOYENNES. -/
  mars_geo : ω .mars_geo = ω .mars_L
  /-- `jupiter_geo` : Jupiter : aiguille géocentrique (module vectoriel). Unité non linéaire (module vectoriel (suiveur) : en moyenne la planète (planète extérieure)) : un tour de sortie par tour d'entrée, donc égalité des vitesses MOYENNES. -/
  jupiter_geo : ω .jupiter_geo = ω .jupiter_L
  /-- `saturn_geo` : Saturne : aiguille géocentrique (module vectoriel). Unité non linéaire (module vectoriel (suiveur) : en moyenne la planète (planète extérieure)) : un tour de sortie par tour d'entrée, donc égalité des vitesses MOYENNES. -/
  saturn_geo : ω .saturn_geo = ω .saturn_L
  /-- `uranus_geo` : Uranus : aiguille géocentrique (module vectoriel). Unité non linéaire (module vectoriel (suiveur) : en moyenne la planète (planète extérieure)) : un tour de sortie par tour d'entrée, donc égalité des vitesses MOYENNES. -/
  uranus_geo : ω .uranus_geo = ω .uranus_L
  /-- `neptune_geo` : Neptune : aiguille géocentrique (module vectoriel). Unité non linéaire (module vectoriel (suiveur) : en moyenne la planète (planète extérieure)) : un tour de sortie par tour d'entrée, donc égalité des vitesses MOYENNES. -/
  neptune_geo : ω .neptune_geo = ω .neptune_L
  /-- `sun_geo` : Soleil vrai : aiguille géocentrique (= Terre vraie + 180°). Unité non linéaire (renvoi 1:1) : un tour de sortie par tour d'entrée, donc égalité des vitesses MOYENNES. -/
  sun_geo : ω .sun_geo = ω .earth_true
  /-- `orrery_earth` : Orrery : tube de Terre (renvoi d’angle 1:1 vers le couvercle). Train 40:40 (conique) depuis `earth_true`, signe +1 : Π menées · ω orrery_earth = signe · Π menantes · ω earth_true. -/
  orrery_earth : 40 * ω .orrery_earth = 40 * ω .earth_true
  /-- `orrery_mercury` : Orrery : tube de Mercure (renvoi d’angle 1:1 vers le couvercle). Train 40:40 (conique) depuis `mercury_true`, signe +1 : Π menées · ω orrery_mercury = signe · Π menantes · ω mercury_true. -/
  orrery_mercury : 40 * ω .orrery_mercury = 40 * ω .mercury_true
  /-- `orrery_venus` : Orrery : tube de Vénus (renvoi d’angle 1:1 vers le couvercle). Train 40:40 (conique) depuis `venus_true`, signe +1 : Π menées · ω orrery_venus = signe · Π menantes · ω venus_true. -/
  orrery_venus : 40 * ω .orrery_venus = 40 * ω .venus_true
  /-- `orrery_mars` : Orrery : tube de Mars (renvoi d’angle 1:1 vers le couvercle). Train 40:40 (conique) depuis `mars_true`, signe +1 : Π menées · ω orrery_mars = signe · Π menantes · ω mars_true. -/
  orrery_mars : 40 * ω .orrery_mars = 40 * ω .mars_true
  /-- `orrery_jupiter` : Orrery : tube de Jupiter (renvoi d’angle 1:1 vers le couvercle). Train 40:40 (conique) depuis `jupiter_true`, signe +1 : Π menées · ω orrery_jupiter = signe · Π menantes · ω jupiter_true. -/
  orrery_jupiter : 40 * ω .orrery_jupiter = 40 * ω .jupiter_true
  /-- `orrery_saturn` : Orrery : tube de Saturne (renvoi d’angle 1:1 vers le couvercle). Train 40:40 (conique) depuis `saturn_true`, signe +1 : Π menées · ω orrery_saturn = signe · Π menantes · ω saturn_true. -/
  orrery_saturn : 40 * ω .orrery_saturn = 40 * ω .saturn_true
  /-- `orrery_uranus` : Orrery : tube de Uranus (renvoi d’angle 1:1 vers le couvercle). Train 40:40 (conique) depuis `uranus_true`, signe +1 : Π menées · ω orrery_uranus = signe · Π menantes · ω uranus_true. -/
  orrery_uranus : 40 * ω .orrery_uranus = 40 * ω .uranus_true
  /-- `orrery_neptune` : Orrery : tube de Neptune (renvoi d’angle 1:1 vers le couvercle). Train 40:40 (conique) depuis `neptune_true`, signe +1 : Π menées · ω orrery_neptune = signe · Π menantes · ω neptune_true. -/
  orrery_neptune : 40 * ω .orrery_neptune = 40 * ω .neptune_true
  /-- `mars_epicyclet` : Mars : épicyclet correcteur (angle absolu 3L − 2ϖ, ϖ figé : couple 3:1). Train 60:20 (ext) depuis `mars_L`, signe +1 : Π menées · ω mars_epicyclet = signe · Π menantes · ω mars_L. -/
  mars_epicyclet : 20 * ω .mars_epicyclet = 60 * ω .mars_L
  /-- `mercury_E` : Mercure : arbre de l’anomalie excentrique E (résolveur). Unité non linéaire (boucle M = E − e sin E : un tour par tour) : un tour de sortie par tour d'entrée, donc égalité des vitesses MOYENNES. -/
  mercury_E : ω .mercury_E = ω .mercury_L
  /-- `mercury_counter_arm` : Mercure : bras (a − b)/2 à l’angle ϖ − E (inverseur conique coaxial 1:1). Train 40:40 (conique) depuis `mercury_E`, signe -1 : Π menées · ω mercury_counter_arm = signe · Π menantes · ω mercury_E. -/
  mercury_counter_arm : 40 * ω .mercury_counter_arm = -40 * ω .mercury_E
  /-- `annual_eq` : Lune : moteur de l’équation annuelle (3/31)(λ☉ vrai − λ☉ moyen) (vitesse moyenne nulle). Différentiel. -/
  annual_eq : ω .annual_eq = 3 / 31 * ω .earth_true - 3 / 31 * ω .Y
  /-- `moon_true` : Lune vraie : aiguille (sortie de la cascade à 5 étages). Unité non linéaire (cascade réduction → équation annuelle → évection → anomalie (équant) → variation : un tour par tour) : un tour de sortie par tour d'entrée, donc égalité des vitesses MOYENNES. -/
  moon_true : ω .moon_true = ω .moon_L
  /-- `moon_phase` : Boule de phase (rotation relative à l’aiguille de la Lune = Lune vraie − Soleil vrai). Unité non linéaire (couronne 1:1 (48:48) menée par le tube du Soleil vrai) : un tour de sortie par tour d'entrée, donc égalité des vitesses MOYENNES. -/
  moon_phase : ω .moon_phase = ω .moon_true - ω .sun_geo
  /-- `saros` : Aiguille du Saros (1 tour = 223 lunaisons). Train 13:46 (ext) · 21:107 (ext) depuis `Y`, signe +1 : Π menées · ω saros = signe · Π menantes · ω Y. -/
  saros : 46 * 107 * ω .saros = 13 * 21 * ω .Y
  /-- `exeligmos` : Aiguille de l’Exeligmos (1 tour = 3 Saros). Train 20:60 (ext) depuis `saros`, signe +1 : Π menées · ω exeligmos = signe · Π menantes · ω saros. -/
  exeligmos : 60 * ω .exeligmos = 20 * ω .saros
  /-- `ganymede` : Ganymède (train direct). Train 167:131 (ext) · 10:23 (ext) · 29:115 (ext) depuis `J`, signe +1 : Π menées · ω ganymede = signe · Π menantes · ω J. -/
  ganymede : 131 * 23 * 115 * ω .ganymede = 167 * 10 * 29 * ω .J
  /-- `nu` : Arbre ν = n_Io − 2n_Eu (ligne des conjonctions à −ν). Train 16:115 (ext) · 19:145 (ext) · 16:142 (ext) depuis `J`, signe +1 : Π menées · ω nu = signe · Π menantes · ω J. -/
  nu : 115 * 145 * 142 * ω .nu = 16 * 19 * 16 * ω .J
  /-- `europa` : Europe = 2·Ganymède + ν (différentiel). Différentiel. -/
  europa : ω .europa = 2 * ω .ganymede + ω .nu
  /-- `io` : Io = 2·Europe + ν (différentiel). Différentiel. -/
  io : ω .io = 2 * ω .europa + ω .nu
  /-- `callisto` : Callisto (train direct, hors résonance). Train 51:122 (ext) · 35:89 (ext) · 39:107 (ext) depuis `J`, signe +1 : Π menées · ω callisto = signe · Π menantes · ω J. -/
  callisto : 122 * 89 * 107 * ω .callisto = 51 * 35 * 39 * ω .J
  /-- `gmst_direct` : Variante : temps sidéral par un train direct depuis J (au lieu du différentiel). Train 197:164 (ext) · 151:148 (ext) · 18:22 (ext) depuis `J`, signe +1 : Π menées · ω gmst_direct = signe · Π menantes · ω J. -/
  gmst_direct : 164 * 148 * 22 * ω .gmst_direct = 197 * 151 * 18 * ω .J
  /-- `synodic` : Variante : arbre synodique moyen D = L − Y (différentiel). Différentiel. -/
  synodic : ω .synodic = ω .moon_L - ω .Y
  /-- `saros_223` : Variante : Saros exact avec une roue de 223 dents (hommage à b1). Train 20:223 (ext) · 10:200 (ext) depuis `synodic`, signe +1 : Π menées · ω saros_223 = signe · Π menantes · ω synodic. -/
  saros_223 : 223 * 200 * ω .saros_223 = 20 * 10 * ω .synodic
  /-- `mars_apsides` : Option : plateau d’apsides de Mars (1 tour en ~81 000 ans). Train 14:44 (ext) depuis `precession_ring`, signe -1 : Π menées · ω mars_apsides = signe · Π menantes · ω precession_ring. -/
  mars_apsides : 44 * ω .mars_apsides = -14 * ω .precession_ring

/-- Vitesses déclarées par trains.json (`rate_turns_per_day`), en tours par jour, pour J = 1. -/
def rate : Shaft → ℚ
  | .J => 1
  | .W => 1 / 7
  | .Y => 589 / 215136
  | .mercury_L => 102638 / 9028989
  | .venus_L => 18259 / 4102812
  | .mars_L => 2342453 / 1609217280
  | .jupiter_L => 2945 / 12760254
  | .saturn_L => 32395 / 348412752
  | .uranus_L => 589 / 18071424
  | .neptune_L => 6479 / 390041568
  | .moon_L => 4598 / 125625
  | .moon_perigee => 359879 / 1163347920
  | .moon_node => -4123 / 28009512
  | .evection_carrier => 1502539 / 290836980
  | .precession_ring => -161975 / 1524347454672
  | .sun_trop => 25041150643 / 9146084728032
  | .stellar => 215725 / 215136
  | .gmst => 9171125878675 / 9146084728032
  | .earth_true => 589 / 215136
  | .lambda_trop => 25041150643 / 9146084728032
  | .alpha_sun => 25041150643 / 9146084728032
  | .eot => 0
  | .eot_dial => 0
  | .tellurion => 215725 / 215136
  | .cal_cross_main => 1 / 6
  | .cal_cross_skip => 101 / 292194
  | .cal_sum => 400 / 146097
  | .cal_prog4 => 100 / 146097
  | .cal_prog100 => 4 / 146097
  | .cal_prog400 => 1 / 146097
  | .mercury_true => 102638 / 9028989
  | .venus_true => 18259 / 4102812
  | .mars_true => 2342453 / 1609217280
  | .jupiter_true => 2945 / 12760254
  | .saturn_true => 32395 / 348412752
  | .uranus_true => 589 / 18071424
  | .neptune_true => 6479 / 390041568
  | .mercury_geo => 589 / 215136
  | .venus_geo => 589 / 215136
  | .mars_geo => 2342453 / 1609217280
  | .jupiter_geo => 2945 / 12760254
  | .saturn_geo => 32395 / 348412752
  | .uranus_geo => 589 / 18071424
  | .neptune_geo => 6479 / 390041568
  | .sun_geo => 589 / 215136
  | .orrery_earth => 589 / 215136
  | .orrery_mercury => 102638 / 9028989
  | .orrery_venus => 18259 / 4102812
  | .orrery_mars => 2342453 / 1609217280
  | .orrery_jupiter => 2945 / 12760254
  | .orrery_saturn => 32395 / 348412752
  | .orrery_uranus => 589 / 18071424
  | .orrery_neptune => 6479 / 390041568
  | .mars_epicyclet => 2342453 / 536405760
  | .mercury_E => 102638 / 9028989
  | .mercury_counter_arm => -102638 / 9028989
  | .annual_eq => 0
  | .moon_true => 4598 / 125625
  | .moon_phase => 305067401 / 9008820000
  | .saros => 53599 / 352966464
  | .exeligmos => 53599 / 1058899392
  | .ganymede => 9686 / 69299
  | .nu => 2432 / 1183925
  | .europa => 1004501316 / 3567166025
  | .io => 2016330248 / 3567166025
  | .callisto => 69615 / 1161806
  | .gmst_direct => 267723 / 266992
  | .synodic => 305067401 / 9008820000
  | .saros_223 => 305067401 / 2008966860000
  | .mars_apsides => 14725 / 435527844192

/-- **Cohérence** : pour toute vitesse `t` de J, les vitesses `t · rate` vérifient les 69 lois (aucune boucle surcontrainte). -/
theorem consistent (t : ℚ) : Kinematics (fun x => t * rate x) := by
  constructor <;> simp only [rate] <;> ring

/-- **Détermination** : toute famille de vitesses qui vérifie les lois vaut ω J · rate ; la table déclarée découle donc des seuls nombres de dents et coefficients. -/
theorem determined (ω : Shaft → ℚ) (h : Kinematics ω) : ∀ x, ω x = ω .J * rate x := by
  have h_J : ω .J = ω .J * 1 := by ring
  have h_W : ω .W = ω .J * (1 / 7) := by
    linear_combination (1 / 70 : ℚ) * h.W + (1 / 7 : ℚ) * h_J
  have h_Y : ω .Y = ω .J * (589 / 215136) := by
    linear_combination (1 / 2151360 : ℚ) * h.Y + (589 / 215136 : ℚ) * h_J
  have h_mercury_L : ω .mercury_L = ω .J * (102638 / 9028989) := by
    linear_combination (1 / 41633 : ℚ) * h.mercury_L + (172864 / 41633 : ℚ) * h_Y
  have h_venus_L : ω .venus_L = ω .J * (18259 / 4102812) := by
    linear_combination (1 / 12663 : ℚ) * h.venus_L + (20584 / 12663 : ℚ) * h_Y
  have h_mars_L : ω .mars_L = ω .J * (2342453 / 1609217280) := by
    linear_combination (1 / 7480 : ℚ) * h.mars_L + (3977 / 7480 : ℚ) * h_Y
  have h_jupiter_L : ω .jupiter_L = ω .J * (2945 / 12760254) := by
    linear_combination (1 / 1898 : ℚ) * h.jupiter_L + (80 / 949 : ℚ) * h_Y
  have h_saturn_L : ω .saturn_L = ω .J * (32395 / 348412752) := by
    linear_combination (1 / 3239 : ℚ) * h.saturn_L + (110 / 3239 : ℚ) * h_Y
  have h_uranus_L : ω .uranus_L = ω .J * (589 / 18071424) := by
    linear_combination (1 / 8400 : ℚ) * h.uranus_L + (1 / 84 : ℚ) * h_Y
  have h_neptune_L : ω .neptune_L = ω .J * (6479 / 390041568) := by
    linear_combination (1 / 21756 : ℚ) * h.neptune_L + (11 / 1813 : ℚ) * h_Y
  have h_moon_L : ω .moon_L = ω .J * (4598 / 125625) := by
    linear_combination (1 / 125625 : ℚ) * h.moon_L + (4598 / 125625 : ℚ) * h_J
  have h_moon_perigee : ω .moon_perigee = ω .J * (359879 / 1163347920) := by
    linear_combination (1 / 10815 : ℚ) * h.moon_perigee + (1222 / 10815 : ℚ) * h_Y
  have h_moon_node : ω .moon_node = ω .J * (-4123 / 28009512) := by
    linear_combination (1 / 4687 : ℚ) * h.moon_node + (-252 / 4687 : ℚ) * h_Y
  have h_evection_carrier : ω .evection_carrier = ω .J * (1502539 / 290836980) := by
    linear_combination h.evection_carrier + (2 : ℚ) * h_Y + (-1 : ℚ) * h_moon_perigee
  have h_precession_ring : ω .precession_ring = ω .J * (-161975 / 1524347454672) := by
    linear_combination (1 / 23449 : ℚ) * h.precession_ring + (-150 / 23449 : ℚ) * h_neptune_L
  have h_sun_trop : ω .sun_trop = ω .J * (25041150643 / 9146084728032) := by
    linear_combination h.sun_trop + (1 : ℚ) * h_Y + (-1 : ℚ) * h_precession_ring
  have h_stellar : ω .stellar = ω .J * (215725 / 215136) := by
    linear_combination h.stellar + (1 : ℚ) * h_J + (1 : ℚ) * h_Y
  have h_gmst : ω .gmst = ω .J * (9171125878675 / 9146084728032) := by
    linear_combination h.gmst + (1 : ℚ) * h_J + (1 : ℚ) * h_sun_trop
  have h_earth_true : ω .earth_true = ω .J * (589 / 215136) := by
    linear_combination h.earth_true + (1 : ℚ) * h_Y
  have h_lambda_trop : ω .lambda_trop = ω .J * (25041150643 / 9146084728032) := by
    linear_combination h.lambda_trop + (1 : ℚ) * h_earth_true + (-1 : ℚ) * h_precession_ring
  have h_alpha_sun : ω .alpha_sun = ω .J * (25041150643 / 9146084728032) := by
    linear_combination h.alpha_sun + (1 : ℚ) * h_lambda_trop
  have h_eot : ω .eot = ω .J * 0 := by
    linear_combination h.eot + (1 : ℚ) * h_sun_trop + (-1 : ℚ) * h_alpha_sun
  have h_eot_dial : ω .eot_dial = ω .J * 0 := by
    linear_combination (1 / 12 : ℚ) * h.eot_dial + (10 : ℚ) * h_eot
  have h_tellurion : ω .tellurion = ω .J * (215725 / 215136) := by
    linear_combination (1 / 40 : ℚ) * h.tellurion + (1 : ℚ) * h_stellar
  have h_cal_cross_main : ω .cal_cross_main = ω .J * (1 / 6) := by
    linear_combination (1 / 6 : ℚ) * h.cal_cross_main + (1 / 6 : ℚ) * h_J
  have h_cal_cross_skip : ω .cal_cross_skip = ω .J * (101 / 292194) := by
    linear_combination (1 / 6 : ℚ) * h.cal_cross_skip + (101 / 292194 : ℚ) * h_J
  have h_cal_sum : ω .cal_sum = ω .J * (400 / 146097) := by
    linear_combination h.cal_sum + (1 / 61 : ℚ) * h_cal_cross_main + (1 / 61 : ℚ) * h_cal_cross_skip
  have h_cal_prog4 : ω .cal_prog4 = ω .J * (100 / 146097) := by
    linear_combination (1 / 60 : ℚ) * h.cal_prog4 + (1 / 4 : ℚ) * h_cal_sum
  have h_cal_prog100 : ω .cal_prog100 = ω .J * (4 / 146097) := by
    linear_combination (1 / 3600 : ℚ) * h.cal_prog100 + (1 / 25 : ℚ) * h_cal_prog4
  have h_cal_prog400 : ω .cal_prog400 = ω .J * (1 / 146097) := by
    linear_combination (1 / 60 : ℚ) * h.cal_prog400 + (1 / 4 : ℚ) * h_cal_prog100
  have h_mercury_true : ω .mercury_true = ω .J * (102638 / 9028989) := by
    linear_combination h.mercury_true + (1 : ℚ) * h_mercury_L
  have h_venus_true : ω .venus_true = ω .J * (18259 / 4102812) := by
    linear_combination h.venus_true + (1 : ℚ) * h_venus_L
  have h_mars_true : ω .mars_true = ω .J * (2342453 / 1609217280) := by
    linear_combination h.mars_true + (1 : ℚ) * h_mars_L
  have h_jupiter_true : ω .jupiter_true = ω .J * (2945 / 12760254) := by
    linear_combination h.jupiter_true + (1 : ℚ) * h_jupiter_L
  have h_saturn_true : ω .saturn_true = ω .J * (32395 / 348412752) := by
    linear_combination h.saturn_true + (1 : ℚ) * h_saturn_L
  have h_uranus_true : ω .uranus_true = ω .J * (589 / 18071424) := by
    linear_combination h.uranus_true + (1 : ℚ) * h_uranus_L
  have h_neptune_true : ω .neptune_true = ω .J * (6479 / 390041568) := by
    linear_combination h.neptune_true + (1 : ℚ) * h_neptune_L
  have h_mercury_geo : ω .mercury_geo = ω .J * (589 / 215136) := by
    linear_combination h.mercury_geo + (1 : ℚ) * h_Y
  have h_venus_geo : ω .venus_geo = ω .J * (589 / 215136) := by
    linear_combination h.venus_geo + (1 : ℚ) * h_Y
  have h_mars_geo : ω .mars_geo = ω .J * (2342453 / 1609217280) := by
    linear_combination h.mars_geo + (1 : ℚ) * h_mars_L
  have h_jupiter_geo : ω .jupiter_geo = ω .J * (2945 / 12760254) := by
    linear_combination h.jupiter_geo + (1 : ℚ) * h_jupiter_L
  have h_saturn_geo : ω .saturn_geo = ω .J * (32395 / 348412752) := by
    linear_combination h.saturn_geo + (1 : ℚ) * h_saturn_L
  have h_uranus_geo : ω .uranus_geo = ω .J * (589 / 18071424) := by
    linear_combination h.uranus_geo + (1 : ℚ) * h_uranus_L
  have h_neptune_geo : ω .neptune_geo = ω .J * (6479 / 390041568) := by
    linear_combination h.neptune_geo + (1 : ℚ) * h_neptune_L
  have h_sun_geo : ω .sun_geo = ω .J * (589 / 215136) := by
    linear_combination h.sun_geo + (1 : ℚ) * h_earth_true
  have h_orrery_earth : ω .orrery_earth = ω .J * (589 / 215136) := by
    linear_combination (1 / 40 : ℚ) * h.orrery_earth + (1 : ℚ) * h_earth_true
  have h_orrery_mercury : ω .orrery_mercury = ω .J * (102638 / 9028989) := by
    linear_combination (1 / 40 : ℚ) * h.orrery_mercury + (1 : ℚ) * h_mercury_true
  have h_orrery_venus : ω .orrery_venus = ω .J * (18259 / 4102812) := by
    linear_combination (1 / 40 : ℚ) * h.orrery_venus + (1 : ℚ) * h_venus_true
  have h_orrery_mars : ω .orrery_mars = ω .J * (2342453 / 1609217280) := by
    linear_combination (1 / 40 : ℚ) * h.orrery_mars + (1 : ℚ) * h_mars_true
  have h_orrery_jupiter : ω .orrery_jupiter = ω .J * (2945 / 12760254) := by
    linear_combination (1 / 40 : ℚ) * h.orrery_jupiter + (1 : ℚ) * h_jupiter_true
  have h_orrery_saturn : ω .orrery_saturn = ω .J * (32395 / 348412752) := by
    linear_combination (1 / 40 : ℚ) * h.orrery_saturn + (1 : ℚ) * h_saturn_true
  have h_orrery_uranus : ω .orrery_uranus = ω .J * (589 / 18071424) := by
    linear_combination (1 / 40 : ℚ) * h.orrery_uranus + (1 : ℚ) * h_uranus_true
  have h_orrery_neptune : ω .orrery_neptune = ω .J * (6479 / 390041568) := by
    linear_combination (1 / 40 : ℚ) * h.orrery_neptune + (1 : ℚ) * h_neptune_true
  have h_mars_epicyclet : ω .mars_epicyclet = ω .J * (2342453 / 536405760) := by
    linear_combination (1 / 20 : ℚ) * h.mars_epicyclet + (3 : ℚ) * h_mars_L
  have h_mercury_E : ω .mercury_E = ω .J * (102638 / 9028989) := by
    linear_combination h.mercury_E + (1 : ℚ) * h_mercury_L
  have h_mercury_counter_arm : ω .mercury_counter_arm = ω .J * (-102638 / 9028989) := by
    linear_combination (1 / 40 : ℚ) * h.mercury_counter_arm + (-1 : ℚ) * h_mercury_E
  have h_annual_eq : ω .annual_eq = ω .J * 0 := by
    linear_combination h.annual_eq + (3 / 31 : ℚ) * h_earth_true + (-3 / 31 : ℚ) * h_Y
  have h_moon_true : ω .moon_true = ω .J * (4598 / 125625) := by
    linear_combination h.moon_true + (1 : ℚ) * h_moon_L
  have h_moon_phase : ω .moon_phase = ω .J * (305067401 / 9008820000) := by
    linear_combination h.moon_phase + (1 : ℚ) * h_moon_true + (-1 : ℚ) * h_sun_geo
  have h_saros : ω .saros = ω .J * (53599 / 352966464) := by
    linear_combination (1 / 4922 : ℚ) * h.saros + (273 / 4922 : ℚ) * h_Y
  have h_exeligmos : ω .exeligmos = ω .J * (53599 / 1058899392) := by
    linear_combination (1 / 60 : ℚ) * h.exeligmos + (1 / 3 : ℚ) * h_saros
  have h_ganymede : ω .ganymede = ω .J * (9686 / 69299) := by
    linear_combination (1 / 346495 : ℚ) * h.ganymede + (9686 / 69299 : ℚ) * h_J
  have h_nu : ω .nu = ω .J * (2432 / 1183925) := by
    linear_combination (1 / 2367850 : ℚ) * h.nu + (2432 / 1183925 : ℚ) * h_J
  have h_europa : ω .europa = ω .J * (1004501316 / 3567166025) := by
    linear_combination h.europa + (2 : ℚ) * h_ganymede + (1 : ℚ) * h_nu
  have h_io : ω .io = ω .J * (2016330248 / 3567166025) := by
    linear_combination h.io + (2 : ℚ) * h_europa + (1 : ℚ) * h_nu
  have h_callisto : ω .callisto = ω .J * (69615 / 1161806) := by
    linear_combination (1 / 1161806 : ℚ) * h.callisto + (69615 / 1161806 : ℚ) * h_J
  have h_gmst_direct : ω .gmst_direct = ω .J * (267723 / 266992) := by
    linear_combination (1 / 533984 : ℚ) * h.gmst_direct + (267723 / 266992 : ℚ) * h_J
  have h_synodic : ω .synodic = ω .J * (305067401 / 9008820000) := by
    linear_combination h.synodic + (1 : ℚ) * h_moon_L + (-1 : ℚ) * h_Y
  have h_saros_223 : ω .saros_223 = ω .J * (305067401 / 2008966860000) := by
    linear_combination (1 / 44600 : ℚ) * h.saros_223 + (1 / 223 : ℚ) * h_synodic
  have h_mars_apsides : ω .mars_apsides = ω .J * (14725 / 435527844192) := by
    linear_combination (1 / 44 : ℚ) * h.mars_apsides + (-7 / 22 : ℚ) * h_precession_ring
  intro x
  cases x
  · exact h_J
  · exact h_W
  · exact h_Y
  · exact h_mercury_L
  · exact h_venus_L
  · exact h_mars_L
  · exact h_jupiter_L
  · exact h_saturn_L
  · exact h_uranus_L
  · exact h_neptune_L
  · exact h_moon_L
  · exact h_moon_perigee
  · exact h_moon_node
  · exact h_evection_carrier
  · exact h_precession_ring
  · exact h_sun_trop
  · exact h_stellar
  · exact h_gmst
  · exact h_earth_true
  · exact h_lambda_trop
  · exact h_alpha_sun
  · exact h_eot
  · exact h_eot_dial
  · exact h_tellurion
  · exact h_cal_cross_main
  · exact h_cal_cross_skip
  · exact h_cal_sum
  · exact h_cal_prog4
  · exact h_cal_prog100
  · exact h_cal_prog400
  · exact h_mercury_true
  · exact h_venus_true
  · exact h_mars_true
  · exact h_jupiter_true
  · exact h_saturn_true
  · exact h_uranus_true
  · exact h_neptune_true
  · exact h_mercury_geo
  · exact h_venus_geo
  · exact h_mars_geo
  · exact h_jupiter_geo
  · exact h_saturn_geo
  · exact h_uranus_geo
  · exact h_neptune_geo
  · exact h_sun_geo
  · exact h_orrery_earth
  · exact h_orrery_mercury
  · exact h_orrery_venus
  · exact h_orrery_mars
  · exact h_orrery_jupiter
  · exact h_orrery_saturn
  · exact h_orrery_uranus
  · exact h_orrery_neptune
  · exact h_mars_epicyclet
  · exact h_mercury_E
  · exact h_mercury_counter_arm
  · exact h_annual_eq
  · exact h_moon_true
  · exact h_moon_phase
  · exact h_saros
  · exact h_exeligmos
  · exact h_ganymede
  · exact h_nu
  · exact h_europa
  · exact h_io
  · exact h_callisto
  · exact h_gmst_direct
  · exact h_synodic
  · exact h_saros_223
  · exact h_mars_apsides

/-- **La machine peut tourner** : il existe des vitesses admissibles avec J à 1 tour par jour ; les hypothèses des autres théorèmes ne sont pas contradictoires. -/
theorem moves : ∃ ω : Shaft → ℚ, Kinematics ω ∧ ω .J = 1 := by
  exact ⟨fun x => 1 * rate x, consistent 1, by simp [rate]⟩

/-- **Un seul degré de liberté** : l'ensemble des vitesses admissibles est exactement la droite {t · rate} (une droite et non un point, puisque rate J = 1). -/
theorem one_dof : {ω : Shaft → ℚ | Kinematics ω} = Set.range (fun t : ℚ => fun x => t * rate x) := by
  ext ω
  constructor
  · intro h
    exact ⟨ω .J, funext fun x => (determined ω h x).symm⟩
  · rintro ⟨t, rfl⟩
    exact consistent t

end AnticythereV2
