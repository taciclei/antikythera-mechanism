-- GÉNÉRÉ par v2/tools/make_lean_v2.py depuis v2/spec/trains.json et v2/spec/architecture.json.
-- Ne pas éditer à la main : relancer le générateur.

import AnticythereV2.Kinematics

/-!
# Rapports exacts des trains d'engrenages

Pour chaque train de trains.json (candidats `ratio`) : la vitesse de sortie vaut le produit des menantes
sur le produit des menées (avec le signe du train) fois la vitesse de la source, ce produit vaut le rapport
exact réduit (`ratio`), et la vitesse rapportée à l'arbre-jour J vaut `rate_vs_J`. Les théorèmes
`sens_*` vérifient le sens physique (`phys`, + = horaire vu de face) : le rapport de Willis signé
(engrènement extérieur −a/b, intérieur ou chaîne +a/b, pignon fou −1) vaut phys(sortie) · phys(source) ·
|rapport|.
-/

namespace AnticythereV2

/-- `W` (Roue de la semaine (1 tour en 7 jours)) : ω W = (10 / 70) · ω J ; rapport exact 1/7, soit 1/7 tour par tour de J. -/
theorem ratio_W (ω : Shaft → ℚ) (h : Kinematics ω) :
    ω .W = (10 / 70) * ω .J ∧ ω .W = (1 / 7) * ω .J ∧
    (10 / 70 : ℚ) = 1 / 7 := by
  have r_W : ω .W = ω .J * (1 / 7) := determined ω h .W
  refine ⟨?_, ?_, ?_⟩
  · linear_combination r_W
  · linear_combination r_W
  · norm_num

/-- `Y` (Roue de l’année Y : longitude moyenne de la Terre, repère J2000 (Soleil moyen = Y + 180°)) : ω Y = (31·19·10 / 180·144·83) · ω J ; rapport exact 589/215136, soit 589/215136 tour par tour de J. -/
theorem ratio_Y (ω : Shaft → ℚ) (h : Kinematics ω) :
    ω .Y = (31 * 19 * 10 / (180 * 144 * 83)) * ω .J ∧ ω .Y = (589 / 215136) * ω .J ∧
    (31 * 19 * 10 / (180 * 144 * 83) : ℚ) = 589 / 215136 := by
  have r_Y : ω .Y = ω .J * (589 / 215136) := determined ω h .Y
  refine ⟨?_, ?_, ?_⟩
  · linear_combination r_Y
  · linear_combination r_Y
  · norm_num

/-- `mercury_L` (Mercure : longitude moyenne héliocentrique (repère J2000)) : ω mercury_L = (37·64·73 / 17·31·79) · ω Y ; rapport exact 172864/41633, soit 102638/9028989 tour par tour de J. -/
theorem ratio_mercury_L (ω : Shaft → ℚ) (h : Kinematics ω) :
    ω .mercury_L = (37 * 64 * 73 / (17 * 31 * 79)) * ω .Y ∧ ω .mercury_L = (102638 / 9028989) * ω .J ∧
    (37 * 64 * 73 / (17 * 31 * 79) : ℚ) = 172864 / 41633 := by
  have r_mercury_L : ω .mercury_L = ω .J * (102638 / 9028989) := determined ω h .mercury_L
  have r_Y : ω .Y = ω .J * (589 / 215136) := determined ω h .Y
  refine ⟨?_, ?_, ?_⟩
  · linear_combination r_mercury_L + (-172864 / 41633 : ℚ) * r_Y
  · linear_combination r_mercury_L
  · norm_num

/-- `venus_L` (Vénus : longitude moyenne héliocentrique (repère J2000)) : ω venus_L = (124·166 / 67·189) · ω Y ; rapport exact 20584/12663, soit 18259/4102812 tour par tour de J. -/
theorem ratio_venus_L (ω : Shaft → ℚ) (h : Kinematics ω) :
    ω .venus_L = (124 * 166 / (67 * 189)) * ω .Y ∧ ω .venus_L = (18259 / 4102812) * ω .J ∧
    (124 * 166 / (67 * 189) : ℚ) = 20584 / 12663 := by
  have r_venus_L : ω .venus_L = ω .J * (18259 / 4102812) := determined ω h .venus_L
  have r_Y : ω .Y = ω .J * (589 / 215136) := determined ω h .Y
  refine ⟨?_, ?_, ?_⟩
  · linear_combination r_venus_L + (-20584 / 12663 : ℚ) * r_Y
  · linear_combination r_venus_L
  · norm_num

/-- `mars_L` (Mars : longitude moyenne héliocentrique (repère J2000)) : ω mars_L = (97·41 / 88·85) · ω Y ; rapport exact 3977/7480, soit 2342453/1609217280 tour par tour de J. -/
theorem ratio_mars_L (ω : Shaft → ℚ) (h : Kinematics ω) :
    ω .mars_L = (97 * 41 / (88 * 85)) * ω .Y ∧ ω .mars_L = (2342453 / 1609217280) * ω .J ∧
    (97 * 41 / (88 * 85) : ℚ) = 3977 / 7480 := by
  have r_mars_L : ω .mars_L = ω .J * (2342453 / 1609217280) := determined ω h .mars_L
  have r_Y : ω .Y = ω .J * (589 / 215136) := determined ω h .Y
  refine ⟨?_, ?_, ?_⟩
  · linear_combination r_mars_L + (-3977 / 7480 : ℚ) * r_Y
  · linear_combination r_mars_L
  · norm_num

/-- `jupiter_L` (Jupiter : longitude moyenne héliocentrique (repère J2000)) : ω jupiter_L = (10·16 / 26·73) · ω Y ; rapport exact 80/949, soit 2945/12760254 tour par tour de J. -/
theorem ratio_jupiter_L (ω : Shaft → ℚ) (h : Kinematics ω) :
    ω .jupiter_L = (10 * 16 / (26 * 73)) * ω .Y ∧ ω .jupiter_L = (2945 / 12760254) * ω .J ∧
    (10 * 16 / (26 * 73) : ℚ) = 80 / 949 := by
  have r_jupiter_L : ω .jupiter_L = ω .J * (2945 / 12760254) := determined ω h .jupiter_L
  have r_Y : ω .Y = ω .J * (589 / 215136) := determined ω h .Y
  refine ⟨?_, ?_, ?_⟩
  · linear_combination r_jupiter_L + (-80 / 949 : ℚ) * r_Y
  · linear_combination r_jupiter_L
  · norm_num

/-- `saturn_L` (Saturne : longitude moyenne héliocentrique (repère J2000)) : ω saturn_L = (10·11 / 41·79) · ω Y ; rapport exact 110/3239, soit 32395/348412752 tour par tour de J. -/
theorem ratio_saturn_L (ω : Shaft → ℚ) (h : Kinematics ω) :
    ω .saturn_L = (10 * 11 / (41 * 79)) * ω .Y ∧ ω .saturn_L = (32395 / 348412752) * ω .J ∧
    (10 * 11 / (41 * 79) : ℚ) = 110 / 3239 := by
  have r_saturn_L : ω .saturn_L = ω .J * (32395 / 348412752) := determined ω h .saturn_L
  have r_Y : ω .Y = ω .J * (589 / 215136) := determined ω h .Y
  refine ⟨?_, ?_, ?_⟩
  · linear_combination r_saturn_L + (-110 / 3239 : ℚ) * r_Y
  · linear_combination r_saturn_L
  · norm_num

/-- `uranus_L` (Uranus : longitude moyenne héliocentrique (repère J2000)) : ω uranus_L = (10·10 / 84·100) · ω Y ; rapport exact 1/84, soit 589/18071424 tour par tour de J. -/
theorem ratio_uranus_L (ω : Shaft → ℚ) (h : Kinematics ω) :
    ω .uranus_L = (10 * 10 / (84 * 100)) * ω .Y ∧ ω .uranus_L = (589 / 18071424) * ω .J ∧
    (10 * 10 / (84 * 100) : ℚ) = 1 / 84 := by
  have r_uranus_L : ω .uranus_L = ω .J * (589 / 18071424) := determined ω h .uranus_L
  have r_Y : ω .Y = ω .J * (589 / 215136) := determined ω h .Y
  refine ⟨?_, ?_, ?_⟩
  · linear_combination r_uranus_L + (-1 / 84 : ℚ) * r_Y
  · linear_combination r_uranus_L
  · norm_num

/-- `neptune_L` (Neptune : longitude moyenne héliocentrique (repère J2000)) : ω neptune_L = (12·11 / 148·147) · ω Y ; rapport exact 11/1813, soit 6479/390041568 tour par tour de J. -/
theorem ratio_neptune_L (ω : Shaft → ℚ) (h : Kinematics ω) :
    ω .neptune_L = (12 * 11 / (148 * 147)) * ω .Y ∧ ω .neptune_L = (6479 / 390041568) * ω .J ∧
    (12 * 11 / (148 * 147) : ℚ) = 11 / 1813 := by
  have r_neptune_L : ω .neptune_L = ω .J * (6479 / 390041568) := determined ω h .neptune_L
  have r_Y : ω .Y = ω .J * (589 / 215136) := determined ω h .Y
  refine ⟨?_, ?_, ?_⟩
  · linear_combination r_neptune_L + (-11 / 1813 : ℚ) * r_Y
  · linear_combination r_neptune_L
  · norm_num

/-- `moon_L` (Lune : longitude moyenne (repère J2000)) : ω moon_L = (11·22·19 / 25·75·67) · ω J ; rapport exact 4598/125625, soit 4598/125625 tour par tour de J. -/
theorem ratio_moon_L (ω : Shaft → ℚ) (h : Kinematics ω) :
    ω .moon_L = (11 * 22 * 19 / (25 * 75 * 67)) * ω .J ∧ ω .moon_L = (4598 / 125625) * ω .J ∧
    (11 * 22 * 19 / (25 * 75 * 67) : ℚ) = 4598 / 125625 := by
  have r_moon_L : ω .moon_L = ω .J * (4598 / 125625) := determined ω h .moon_L
  refine ⟨?_, ?_, ?_⟩
  · linear_combination r_moon_L
  · linear_combination r_moon_L
  · norm_num

/-- `moon_perigee` (Lune : porte-satellite du périgée ϖ (étage d’anomalie)) : ω moon_perigee = (47·26 / 105·103) · ω Y ; rapport exact 1222/10815, soit 359879/1163347920 tour par tour de J. -/
theorem ratio_moon_perigee (ω : Shaft → ℚ) (h : Kinematics ω) :
    ω .moon_perigee = (47 * 26 / (105 * 103)) * ω .Y ∧ ω .moon_perigee = (359879 / 1163347920) * ω .J ∧
    (47 * 26 / (105 * 103) : ℚ) = 1222 / 10815 := by
  have r_moon_perigee : ω .moon_perigee = ω .J * (359879 / 1163347920) := determined ω h .moon_perigee
  have r_Y : ω .Y = ω .J * (589 / 215136) := determined ω h .Y
  refine ⟨?_, ?_, ?_⟩
  · linear_combination r_moon_perigee + (-1222 / 10815 : ℚ) * r_Y
  · linear_combination r_moon_perigee
  · norm_num

/-- `moon_node` (Lune : porte-nœuds Ω (aiguille du Dragon, étage de réduction, coulisse d’éclipse)) : ω moon_node = (-12·21 / 43·109) · ω Y ; rapport exact -252/4687, soit -4123/28009512 tour par tour de J. -/
theorem ratio_moon_node (ω : Shaft → ℚ) (h : Kinematics ω) :
    ω .moon_node = (-(12 * 21) / (43 * 109)) * ω .Y ∧ ω .moon_node = (-4123 / 28009512) * ω .J ∧
    (-(12 * 21) / (43 * 109) : ℚ) = -252 / 4687 := by
  have r_moon_node : ω .moon_node = ω .J * (-4123 / 28009512) := determined ω h .moon_node
  have r_Y : ω .Y = ω .J * (589 / 215136) := determined ω h .Y
  refine ⟨?_, ?_, ?_⟩
  · linear_combination r_moon_node + (252 / 4687 : ℚ) * r_Y
  · linear_combination r_moon_node
  · norm_num

/-- `precession_ring` (Anneau du zodiaque tropique (précession ; 1 tour rétrograde en ~25 766 ans)) : ω precession_ring = (-10·15 / 131·179) · ω neptune_L ; rapport exact -150/23449, soit -161975/1524347454672 tour par tour de J. -/
theorem ratio_precession_ring (ω : Shaft → ℚ) (h : Kinematics ω) :
    ω .precession_ring = (-(10 * 15) / (131 * 179)) * ω .neptune_L ∧ ω .precession_ring = (-161975 / 1524347454672) * ω .J ∧
    (-(10 * 15) / (131 * 179) : ℚ) = -150 / 23449 := by
  have r_precession_ring : ω .precession_ring = ω .J * (-161975 / 1524347454672) := determined ω h .precession_ring
  have r_neptune_L : ω .neptune_L = ω .J * (6479 / 390041568) := determined ω h .neptune_L
  refine ⟨?_, ?_, ?_⟩
  · linear_combination r_precession_ring + (150 / 23449 : ℚ) * r_neptune_L
  · linear_combination r_precession_ring
  · norm_num

/-- `eot_dial` (Aiguille de l’équation du temps (agrandissement ×10)) : ω eot_dial = (120 / 12) · ω eot ; rapport exact 10, soit 0 tour par tour de J. -/
theorem ratio_eot_dial (ω : Shaft → ℚ) (h : Kinematics ω) :
    ω .eot_dial = (120 / 12) * ω .eot ∧ ω .eot_dial = 0 * ω .J ∧
    (120 / 12 : ℚ) = 10 := by
  have r_eot_dial : ω .eot_dial = ω .J * 0 := determined ω h .eot_dial
  have r_eot : ω .eot = ω .J * 0 := determined ω h .eot
  refine ⟨?_, ?_, ?_⟩
  · linear_combination r_eot_dial + (-10 : ℚ) * r_eot
  · linear_combination r_eot_dial
  · norm_num

/-- `tellurion` (Globe-tellurion de l’orrery (chaîne 1:1 le long du bras de la Terre : angle absolu = S)) : ω tellurion = (40 / 40) · ω stellar ; rapport exact 1, soit 215725/215136 tour par tour de J. -/
theorem ratio_tellurion (ω : Shaft → ℚ) (h : Kinematics ω) :
    ω .tellurion = (40 / 40) * ω .stellar ∧ ω .tellurion = (215725 / 215136) * ω .J ∧
    (40 / 40 : ℚ) = 1 := by
  have r_tellurion : ω .tellurion = ω .J * (215725 / 215136) := determined ω h .tellurion
  have r_stellar : ω .stellar = ω .J * (215725 / 215136) := determined ω h .stellar
  refine ⟨?_, ?_, ?_⟩
  · linear_combination r_tellurion + (-1 : ℚ) * r_stellar
  · linear_combination r_tellurion
  · norm_num

/-- `cal_prog4` (Roue-programme de 4 ans (came C4)) : ω cal_prog4 = (15 / 60) · ω cal_sum ; rapport exact 1/4, soit 100/146097 tour par tour de J. -/
theorem ratio_cal_prog4 (ω : Shaft → ℚ) (h : Kinematics ω) :
    ω .cal_prog4 = (15 / 60) * ω .cal_sum ∧ ω .cal_prog4 = (100 / 146097) * ω .J ∧
    (15 / 60 : ℚ) = 1 / 4 := by
  have r_cal_prog4 : ω .cal_prog4 = ω .J * (100 / 146097) := determined ω h .cal_prog4
  have r_cal_sum : ω .cal_sum = ω .J * (400 / 146097) := determined ω h .cal_sum
  refine ⟨?_, ?_, ?_⟩
  · linear_combination r_cal_prog4 + (-1 / 4 : ℚ) * r_cal_sum
  · linear_combination r_cal_prog4
  · norm_num

/-- `cal_prog100` (Roue-programme de 100 ans (came C100)) : ω cal_prog100 = (12·12 / 60·60) · ω cal_prog4 ; rapport exact 1/25, soit 4/146097 tour par tour de J. -/
theorem ratio_cal_prog100 (ω : Shaft → ℚ) (h : Kinematics ω) :
    ω .cal_prog100 = (12 * 12 / (60 * 60)) * ω .cal_prog4 ∧ ω .cal_prog100 = (4 / 146097) * ω .J ∧
    (12 * 12 / (60 * 60) : ℚ) = 1 / 25 := by
  have r_cal_prog100 : ω .cal_prog100 = ω .J * (4 / 146097) := determined ω h .cal_prog100
  have r_cal_prog4 : ω .cal_prog4 = ω .J * (100 / 146097) := determined ω h .cal_prog4
  refine ⟨?_, ?_, ?_⟩
  · linear_combination r_cal_prog100 + (-1 / 25 : ℚ) * r_cal_prog4
  · linear_combination r_cal_prog100
  · norm_num

/-- `cal_prog400` (Roue-programme de 400 ans (came C400)) : ω cal_prog400 = (15 / 60) · ω cal_prog100 ; rapport exact 1/4, soit 1/146097 tour par tour de J. -/
theorem ratio_cal_prog400 (ω : Shaft → ℚ) (h : Kinematics ω) :
    ω .cal_prog400 = (15 / 60) * ω .cal_prog100 ∧ ω .cal_prog400 = (1 / 146097) * ω .J ∧
    (15 / 60 : ℚ) = 1 / 4 := by
  have r_cal_prog400 : ω .cal_prog400 = ω .J * (1 / 146097) := determined ω h .cal_prog400
  have r_cal_prog100 : ω .cal_prog100 = ω .J * (4 / 146097) := determined ω h .cal_prog100
  refine ⟨?_, ?_, ?_⟩
  · linear_combination r_cal_prog400 + (-1 / 4 : ℚ) * r_cal_prog100
  · linear_combination r_cal_prog400
  · norm_num

/-- `orrery_earth` (Orrery : tube de Terre (renvoi d’angle 1:1 vers le couvercle)) : ω orrery_earth = (40 / 40) · ω earth_true ; rapport exact 1, soit 589/215136 tour par tour de J. -/
theorem ratio_orrery_earth (ω : Shaft → ℚ) (h : Kinematics ω) :
    ω .orrery_earth = (40 / 40) * ω .earth_true ∧ ω .orrery_earth = (589 / 215136) * ω .J ∧
    (40 / 40 : ℚ) = 1 := by
  have r_orrery_earth : ω .orrery_earth = ω .J * (589 / 215136) := determined ω h .orrery_earth
  have r_earth_true : ω .earth_true = ω .J * (589 / 215136) := determined ω h .earth_true
  refine ⟨?_, ?_, ?_⟩
  · linear_combination r_orrery_earth + (-1 : ℚ) * r_earth_true
  · linear_combination r_orrery_earth
  · norm_num

/-- `orrery_mercury` (Orrery : tube de Mercure (renvoi d’angle 1:1 vers le couvercle)) : ω orrery_mercury = (40 / 40) · ω mercury_true ; rapport exact 1, soit 102638/9028989 tour par tour de J. -/
theorem ratio_orrery_mercury (ω : Shaft → ℚ) (h : Kinematics ω) :
    ω .orrery_mercury = (40 / 40) * ω .mercury_true ∧ ω .orrery_mercury = (102638 / 9028989) * ω .J ∧
    (40 / 40 : ℚ) = 1 := by
  have r_orrery_mercury : ω .orrery_mercury = ω .J * (102638 / 9028989) := determined ω h .orrery_mercury
  have r_mercury_true : ω .mercury_true = ω .J * (102638 / 9028989) := determined ω h .mercury_true
  refine ⟨?_, ?_, ?_⟩
  · linear_combination r_orrery_mercury + (-1 : ℚ) * r_mercury_true
  · linear_combination r_orrery_mercury
  · norm_num

/-- `orrery_venus` (Orrery : tube de Vénus (renvoi d’angle 1:1 vers le couvercle)) : ω orrery_venus = (40 / 40) · ω venus_true ; rapport exact 1, soit 18259/4102812 tour par tour de J. -/
theorem ratio_orrery_venus (ω : Shaft → ℚ) (h : Kinematics ω) :
    ω .orrery_venus = (40 / 40) * ω .venus_true ∧ ω .orrery_venus = (18259 / 4102812) * ω .J ∧
    (40 / 40 : ℚ) = 1 := by
  have r_orrery_venus : ω .orrery_venus = ω .J * (18259 / 4102812) := determined ω h .orrery_venus
  have r_venus_true : ω .venus_true = ω .J * (18259 / 4102812) := determined ω h .venus_true
  refine ⟨?_, ?_, ?_⟩
  · linear_combination r_orrery_venus + (-1 : ℚ) * r_venus_true
  · linear_combination r_orrery_venus
  · norm_num

/-- `orrery_mars` (Orrery : tube de Mars (renvoi d’angle 1:1 vers le couvercle)) : ω orrery_mars = (40 / 40) · ω mars_true ; rapport exact 1, soit 2342453/1609217280 tour par tour de J. -/
theorem ratio_orrery_mars (ω : Shaft → ℚ) (h : Kinematics ω) :
    ω .orrery_mars = (40 / 40) * ω .mars_true ∧ ω .orrery_mars = (2342453 / 1609217280) * ω .J ∧
    (40 / 40 : ℚ) = 1 := by
  have r_orrery_mars : ω .orrery_mars = ω .J * (2342453 / 1609217280) := determined ω h .orrery_mars
  have r_mars_true : ω .mars_true = ω .J * (2342453 / 1609217280) := determined ω h .mars_true
  refine ⟨?_, ?_, ?_⟩
  · linear_combination r_orrery_mars + (-1 : ℚ) * r_mars_true
  · linear_combination r_orrery_mars
  · norm_num

/-- `orrery_jupiter` (Orrery : tube de Jupiter (renvoi d’angle 1:1 vers le couvercle)) : ω orrery_jupiter = (40 / 40) · ω jupiter_true ; rapport exact 1, soit 2945/12760254 tour par tour de J. -/
theorem ratio_orrery_jupiter (ω : Shaft → ℚ) (h : Kinematics ω) :
    ω .orrery_jupiter = (40 / 40) * ω .jupiter_true ∧ ω .orrery_jupiter = (2945 / 12760254) * ω .J ∧
    (40 / 40 : ℚ) = 1 := by
  have r_orrery_jupiter : ω .orrery_jupiter = ω .J * (2945 / 12760254) := determined ω h .orrery_jupiter
  have r_jupiter_true : ω .jupiter_true = ω .J * (2945 / 12760254) := determined ω h .jupiter_true
  refine ⟨?_, ?_, ?_⟩
  · linear_combination r_orrery_jupiter + (-1 : ℚ) * r_jupiter_true
  · linear_combination r_orrery_jupiter
  · norm_num

/-- `orrery_saturn` (Orrery : tube de Saturne (renvoi d’angle 1:1 vers le couvercle)) : ω orrery_saturn = (40 / 40) · ω saturn_true ; rapport exact 1, soit 32395/348412752 tour par tour de J. -/
theorem ratio_orrery_saturn (ω : Shaft → ℚ) (h : Kinematics ω) :
    ω .orrery_saturn = (40 / 40) * ω .saturn_true ∧ ω .orrery_saturn = (32395 / 348412752) * ω .J ∧
    (40 / 40 : ℚ) = 1 := by
  have r_orrery_saturn : ω .orrery_saturn = ω .J * (32395 / 348412752) := determined ω h .orrery_saturn
  have r_saturn_true : ω .saturn_true = ω .J * (32395 / 348412752) := determined ω h .saturn_true
  refine ⟨?_, ?_, ?_⟩
  · linear_combination r_orrery_saturn + (-1 : ℚ) * r_saturn_true
  · linear_combination r_orrery_saturn
  · norm_num

/-- `orrery_uranus` (Orrery : tube de Uranus (renvoi d’angle 1:1 vers le couvercle)) : ω orrery_uranus = (40 / 40) · ω uranus_true ; rapport exact 1, soit 589/18071424 tour par tour de J. -/
theorem ratio_orrery_uranus (ω : Shaft → ℚ) (h : Kinematics ω) :
    ω .orrery_uranus = (40 / 40) * ω .uranus_true ∧ ω .orrery_uranus = (589 / 18071424) * ω .J ∧
    (40 / 40 : ℚ) = 1 := by
  have r_orrery_uranus : ω .orrery_uranus = ω .J * (589 / 18071424) := determined ω h .orrery_uranus
  have r_uranus_true : ω .uranus_true = ω .J * (589 / 18071424) := determined ω h .uranus_true
  refine ⟨?_, ?_, ?_⟩
  · linear_combination r_orrery_uranus + (-1 : ℚ) * r_uranus_true
  · linear_combination r_orrery_uranus
  · norm_num

/-- `orrery_neptune` (Orrery : tube de Neptune (renvoi d’angle 1:1 vers le couvercle)) : ω orrery_neptune = (40 / 40) · ω neptune_true ; rapport exact 1, soit 6479/390041568 tour par tour de J. -/
theorem ratio_orrery_neptune (ω : Shaft → ℚ) (h : Kinematics ω) :
    ω .orrery_neptune = (40 / 40) * ω .neptune_true ∧ ω .orrery_neptune = (6479 / 390041568) * ω .J ∧
    (40 / 40 : ℚ) = 1 := by
  have r_orrery_neptune : ω .orrery_neptune = ω .J * (6479 / 390041568) := determined ω h .orrery_neptune
  have r_neptune_true : ω .neptune_true = ω .J * (6479 / 390041568) := determined ω h .neptune_true
  refine ⟨?_, ?_, ?_⟩
  · linear_combination r_orrery_neptune + (-1 : ℚ) * r_neptune_true
  · linear_combination r_orrery_neptune
  · norm_num

/-- `mars_epicyclet` (Mars : épicyclet correcteur (angle absolu 3L − 2ϖ, ϖ figé : couple 3:1)) : ω mars_epicyclet = (60 / 20) · ω mars_L ; rapport exact 3, soit 2342453/536405760 tour par tour de J. -/
theorem ratio_mars_epicyclet (ω : Shaft → ℚ) (h : Kinematics ω) :
    ω .mars_epicyclet = (60 / 20) * ω .mars_L ∧ ω .mars_epicyclet = (2342453 / 536405760) * ω .J ∧
    (60 / 20 : ℚ) = 3 := by
  have r_mars_epicyclet : ω .mars_epicyclet = ω .J * (2342453 / 536405760) := determined ω h .mars_epicyclet
  have r_mars_L : ω .mars_L = ω .J * (2342453 / 1609217280) := determined ω h .mars_L
  refine ⟨?_, ?_, ?_⟩
  · linear_combination r_mars_epicyclet + (-3 : ℚ) * r_mars_L
  · linear_combination r_mars_epicyclet
  · norm_num

/-- `mercury_counter_arm` (Mercure : bras (a − b)/2 à l’angle ϖ − E (inverseur conique coaxial 1:1)) : ω mercury_counter_arm = (-40 / 40) · ω mercury_E ; rapport exact -1, soit -102638/9028989 tour par tour de J. -/
theorem ratio_mercury_counter_arm (ω : Shaft → ℚ) (h : Kinematics ω) :
    ω .mercury_counter_arm = (-40 / 40) * ω .mercury_E ∧ ω .mercury_counter_arm = (-102638 / 9028989) * ω .J ∧
    (-40 / 40 : ℚ) = -1 := by
  have r_mercury_counter_arm : ω .mercury_counter_arm = ω .J * (-102638 / 9028989) := determined ω h .mercury_counter_arm
  have r_mercury_E : ω .mercury_E = ω .J * (102638 / 9028989) := determined ω h .mercury_E
  refine ⟨?_, ?_, ?_⟩
  · linear_combination r_mercury_counter_arm + r_mercury_E
  · linear_combination r_mercury_counter_arm
  · norm_num

/-- `saros` (Aiguille du Saros (1 tour = 223 lunaisons)) : ω saros = (13·21 / 46·107) · ω Y ; rapport exact 273/4922, soit 53599/352966464 tour par tour de J. -/
theorem ratio_saros (ω : Shaft → ℚ) (h : Kinematics ω) :
    ω .saros = (13 * 21 / (46 * 107)) * ω .Y ∧ ω .saros = (53599 / 352966464) * ω .J ∧
    (13 * 21 / (46 * 107) : ℚ) = 273 / 4922 := by
  have r_saros : ω .saros = ω .J * (53599 / 352966464) := determined ω h .saros
  have r_Y : ω .Y = ω .J * (589 / 215136) := determined ω h .Y
  refine ⟨?_, ?_, ?_⟩
  · linear_combination r_saros + (-273 / 4922 : ℚ) * r_Y
  · linear_combination r_saros
  · norm_num

/-- `exeligmos` (Aiguille de l’Exeligmos (1 tour = 3 Saros)) : ω exeligmos = (20 / 60) · ω saros ; rapport exact 1/3, soit 53599/1058899392 tour par tour de J. -/
theorem ratio_exeligmos (ω : Shaft → ℚ) (h : Kinematics ω) :
    ω .exeligmos = (20 / 60) * ω .saros ∧ ω .exeligmos = (53599 / 1058899392) * ω .J ∧
    (20 / 60 : ℚ) = 1 / 3 := by
  have r_exeligmos : ω .exeligmos = ω .J * (53599 / 1058899392) := determined ω h .exeligmos
  have r_saros : ω .saros = ω .J * (53599 / 352966464) := determined ω h .saros
  refine ⟨?_, ?_, ?_⟩
  · linear_combination r_exeligmos + (-1 / 3 : ℚ) * r_saros
  · linear_combination r_exeligmos
  · norm_num

/-- `ganymede` (Ganymède (train direct)) : ω ganymede = (167·10·29 / 131·23·115) · ω J ; rapport exact 9686/69299, soit 9686/69299 tour par tour de J. -/
theorem ratio_ganymede (ω : Shaft → ℚ) (h : Kinematics ω) :
    ω .ganymede = (167 * 10 * 29 / (131 * 23 * 115)) * ω .J ∧ ω .ganymede = (9686 / 69299) * ω .J ∧
    (167 * 10 * 29 / (131 * 23 * 115) : ℚ) = 9686 / 69299 := by
  have r_ganymede : ω .ganymede = ω .J * (9686 / 69299) := determined ω h .ganymede
  refine ⟨?_, ?_, ?_⟩
  · linear_combination r_ganymede
  · linear_combination r_ganymede
  · norm_num

/-- `nu` (Arbre ν = n_Io − 2n_Eu (ligne des conjonctions à −ν)) : ω nu = (16·19·16 / 115·145·142) · ω J ; rapport exact 2432/1183925, soit 2432/1183925 tour par tour de J. -/
theorem ratio_nu (ω : Shaft → ℚ) (h : Kinematics ω) :
    ω .nu = (16 * 19 * 16 / (115 * 145 * 142)) * ω .J ∧ ω .nu = (2432 / 1183925) * ω .J ∧
    (16 * 19 * 16 / (115 * 145 * 142) : ℚ) = 2432 / 1183925 := by
  have r_nu : ω .nu = ω .J * (2432 / 1183925) := determined ω h .nu
  refine ⟨?_, ?_, ?_⟩
  · linear_combination r_nu
  · linear_combination r_nu
  · norm_num

/-- `callisto` (Callisto (train direct, hors résonance)) : ω callisto = (51·35·39 / 122·89·107) · ω J ; rapport exact 69615/1161806, soit 69615/1161806 tour par tour de J. -/
theorem ratio_callisto (ω : Shaft → ℚ) (h : Kinematics ω) :
    ω .callisto = (51 * 35 * 39 / (122 * 89 * 107)) * ω .J ∧ ω .callisto = (69615 / 1161806) * ω .J ∧
    (51 * 35 * 39 / (122 * 89 * 107) : ℚ) = 69615 / 1161806 := by
  have r_callisto : ω .callisto = ω .J * (69615 / 1161806) := determined ω h .callisto
  refine ⟨?_, ?_, ?_⟩
  · linear_combination r_callisto
  · linear_combination r_callisto
  · norm_num

/-- `gmst_direct` (Variante : temps sidéral par un train direct depuis J (au lieu du différentiel)) : ω gmst_direct = (197·151·18 / 164·148·22) · ω J ; rapport exact 267723/266992, soit 267723/266992 tour par tour de J. -/
theorem ratio_gmst_direct (ω : Shaft → ℚ) (h : Kinematics ω) :
    ω .gmst_direct = (197 * 151 * 18 / (164 * 148 * 22)) * ω .J ∧ ω .gmst_direct = (267723 / 266992) * ω .J ∧
    (197 * 151 * 18 / (164 * 148 * 22) : ℚ) = 267723 / 266992 := by
  have r_gmst_direct : ω .gmst_direct = ω .J * (267723 / 266992) := determined ω h .gmst_direct
  refine ⟨?_, ?_, ?_⟩
  · linear_combination r_gmst_direct
  · linear_combination r_gmst_direct
  · norm_num

/-- `saros_223` (Variante : Saros exact avec une roue de 223 dents (hommage à b1)) : ω saros_223 = (20·10 / 223·200) · ω synodic ; rapport exact 1/223, soit 305067401/2008966860000 tour par tour de J. -/
theorem ratio_saros_223 (ω : Shaft → ℚ) (h : Kinematics ω) :
    ω .saros_223 = (20 * 10 / (223 * 200)) * ω .synodic ∧ ω .saros_223 = (305067401 / 2008966860000) * ω .J ∧
    (20 * 10 / (223 * 200) : ℚ) = 1 / 223 := by
  have r_saros_223 : ω .saros_223 = ω .J * (305067401 / 2008966860000) := determined ω h .saros_223
  have r_synodic : ω .synodic = ω .J * (305067401 / 9008820000) := determined ω h .synodic
  refine ⟨?_, ?_, ?_⟩
  · linear_combination r_saros_223 + (-1 / 223 : ℚ) * r_synodic
  · linear_combination r_saros_223
  · norm_num

/-- `mars_apsides` (Option : plateau d’apsides de Mars (1 tour en ~81 000 ans)) : ω mars_apsides = (-14 / 44) · ω precession_ring ; rapport exact -7/22, soit 14725/435527844192 tour par tour de J. -/
theorem ratio_mars_apsides (ω : Shaft → ℚ) (h : Kinematics ω) :
    ω .mars_apsides = (-14 / 44) * ω .precession_ring ∧ ω .mars_apsides = (14725 / 435527844192) * ω .J ∧
    (-14 / 44 : ℚ) = -7 / 22 := by
  have r_mars_apsides : ω .mars_apsides = ω .J * (14725 / 435527844192) := determined ω h .mars_apsides
  have r_precession_ring : ω .precession_ring = ω .J * (-161975 / 1524347454672) := determined ω h .precession_ring
  refine ⟨?_, ?_, ?_⟩
  · linear_combination r_mars_apsides + (7 / 22 : ℚ) * r_precession_ring
  · linear_combination r_mars_apsides
  · norm_num

/-- Sens physique de `W` : 1 inversion(s) (engrènements extérieurs) depuis `J` (phys -1) donnent phys +1, avec |rapport| = 1/7. -/
theorem sens_W :
    (-10 / 70 : ℚ) = (1) * (-1) * (1 / 7) := by
  norm_num

/-- Sens physique de `Y` : 3 inversion(s) (engrènements extérieurs) depuis `J` (phys -1) donnent phys +1, avec |rapport| = 589/215136. -/
theorem sens_Y :
    (-31 / 180 : ℚ) * (-19 / 144) * (-10 / 83) = (1) * (-1) * (589 / 215136) := by
  norm_num

/-- Sens physique de `mercury_L` : 4 inversion(s) (engrènements extérieurs, pignon fou) depuis `Y` (phys +1) donnent phys +1, avec |rapport| = 172864/41633. -/
theorem sens_mercury_L :
    (-37 / 17 : ℚ) * (-64 / 31) * (-73 / 79) * (-1) = (1) * (1) * (172864 / 41633) := by
  norm_num

/-- Sens physique de `venus_L` : 2 inversion(s) (engrènements extérieurs) depuis `Y` (phys +1) donnent phys +1, avec |rapport| = 20584/12663. -/
theorem sens_venus_L :
    (-124 / 67 : ℚ) * (-166 / 189) = (1) * (1) * (20584 / 12663) := by
  norm_num

/-- Sens physique de `mars_L` : 2 inversion(s) (engrènements extérieurs) depuis `Y` (phys +1) donnent phys +1, avec |rapport| = 3977/7480. -/
theorem sens_mars_L :
    (-97 / 88 : ℚ) * (-41 / 85) = (1) * (1) * (3977 / 7480) := by
  norm_num

/-- Sens physique de `jupiter_L` : 2 inversion(s) (engrènements extérieurs) depuis `Y` (phys +1) donnent phys +1, avec |rapport| = 80/949. -/
theorem sens_jupiter_L :
    (-10 / 26 : ℚ) * (-16 / 73) = (1) * (1) * (80 / 949) := by
  norm_num

/-- Sens physique de `saturn_L` : 2 inversion(s) (engrènements extérieurs) depuis `Y` (phys +1) donnent phys +1, avec |rapport| = 110/3239. -/
theorem sens_saturn_L :
    (-10 / 41 : ℚ) * (-11 / 79) = (1) * (1) * (110 / 3239) := by
  norm_num

/-- Sens physique de `uranus_L` : 2 inversion(s) (engrènements extérieurs) depuis `Y` (phys +1) donnent phys +1, avec |rapport| = 1/84. -/
theorem sens_uranus_L :
    (-10 / 84 : ℚ) * (-10 / 100) = (1) * (1) * (1 / 84) := by
  norm_num

/-- Sens physique de `neptune_L` : 2 inversion(s) (engrènements extérieurs) depuis `Y` (phys +1) donnent phys +1, avec |rapport| = 11/1813. -/
theorem sens_neptune_L :
    (-12 / 148 : ℚ) * (-11 / 147) = (1) * (1) * (11 / 1813) := by
  norm_num

/-- Sens physique de `moon_L` : 3 inversion(s) (engrènements extérieurs) depuis `J` (phys -1) donnent phys +1, avec |rapport| = 4598/125625. -/
theorem sens_moon_L :
    (-11 / 25 : ℚ) * (-22 / 75) * (-19 / 67) = (1) * (-1) * (4598 / 125625) := by
  norm_num

/-- Sens physique de `moon_perigee` : 2 inversion(s) (engrènements extérieurs) depuis `Y` (phys +1) donnent phys +1, avec |rapport| = 1222/10815. -/
theorem sens_moon_perigee :
    (-47 / 105 : ℚ) * (-26 / 103) = (1) * (1) * (1222 / 10815) := by
  norm_num

/-- Sens physique de `moon_node` : 3 inversion(s) (engrènements extérieurs, pignon fou) depuis `Y` (phys +1) donnent phys -1, avec |rapport| = 252/4687. -/
theorem sens_moon_node :
    (-12 / 43 : ℚ) * (-21 / 109) * (-1) = (-1) * (1) * (252 / 4687) := by
  norm_num

/-- Sens physique de `precession_ring` : 1 inversion(s) (engrènements extérieurs) depuis `neptune_L` (phys +1) donnent phys -1, avec |rapport| = 150/23449. -/
theorem sens_precession_ring :
    (-10 / 131 : ℚ) * (15 / 179) = (-1) * (1) * (150 / 23449) := by
  norm_num

/-- Sens physique de `mars_epicyclet` : 1 inversion(s) (engrènements extérieurs) depuis `mars_L` (phys +1) donnent phys -1, avec |rapport| = 3. -/
theorem sens_mars_epicyclet :
    (-60 / 20 : ℚ) = (-1) * (1) * 3 := by
  norm_num

/-- Sens physique de `saros` : 2 inversion(s) (engrènements extérieurs) depuis `Y` (phys +1) donnent phys +1, avec |rapport| = 273/4922. -/
theorem sens_saros :
    (-13 / 46 : ℚ) * (-21 / 107) = (1) * (1) * (273 / 4922) := by
  norm_num

/-- Sens physique de `exeligmos` : 1 inversion(s) (engrènements extérieurs) depuis `saros` (phys +1) donnent phys -1, avec |rapport| = 1/3. -/
theorem sens_exeligmos :
    (-20 / 60 : ℚ) = (-1) * (1) * (1 / 3) := by
  norm_num

/-- Sens physique de `ganymede` : 3 inversion(s) (engrènements extérieurs) depuis `J` (phys -1) donnent phys +1, avec |rapport| = 9686/69299. -/
theorem sens_ganymede :
    (-167 / 131 : ℚ) * (-10 / 23) * (-29 / 115) = (1) * (-1) * (9686 / 69299) := by
  norm_num

/-- Sens physique de `nu` : 3 inversion(s) (engrènements extérieurs) depuis `J` (phys -1) donnent phys +1, avec |rapport| = 2432/1183925. -/
theorem sens_nu :
    (-16 / 115 : ℚ) * (-19 / 145) * (-16 / 142) = (1) * (-1) * (2432 / 1183925) := by
  norm_num

/-- Sens physique de `callisto` : 3 inversion(s) (engrènements extérieurs) depuis `J` (phys -1) donnent phys +1, avec |rapport| = 69615/1161806. -/
theorem sens_callisto :
    (-51 / 122 : ℚ) * (-35 / 89) * (-39 / 107) = (1) * (-1) * (69615 / 1161806) := by
  norm_num

/-- Sens physique de `gmst_direct` : 3 inversion(s) (engrènements extérieurs) depuis `J` (phys -1) donnent phys +1, avec |rapport| = 267723/266992. -/
theorem sens_gmst_direct :
    (-197 / 164 : ℚ) * (-151 / 148) * (-18 / 22) = (1) * (-1) * (267723 / 266992) := by
  norm_num

/-- Sens physique de `mars_apsides` : 1 inversion(s) (engrènements extérieurs) depuis `precession_ring` (phys -1) donnent phys +1, avec |rapport| = 7/22. -/
theorem sens_mars_apsides :
    (-14 / 44 : ℚ) = (1) * (-1) * (7 / 22) := by
  norm_num

end AnticythereV2
