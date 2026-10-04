-- GÉNÉRÉ par v2/tools/make_lean_v2.py depuis v2/spec/trains.json et v2/spec/architecture.json.
-- Ne pas éditer à la main : relancer le générateur.

import Mathlib

/-!
# Architecture placée : rapports, sens et entraxes

Identités de `architecture.json` confrontées à trains.json. Rapports physiques signés (Willis) :
engrènement extérieur −a/b, intérieur +a/b, pignon fou par deux engrènements extérieurs. HYPOTHÈSE : le bus
(couronne de moyeu → pignon → tringle → pignon → couronne) est compté de même sens ; comme pour les renvois
coniques de `sens` (« côté d'engrènement d'une conique »), c'est un réglage de montage (face des couronnes,
côté des pignons), et CONTRACT.md § 3 fait tourner les couronnes de moyeu au taux signé de la source. Les
items du bus n'ont pas de dents dans architecture.json : 96 et 24 sont lus dans `roues.rows`. Entraxes :
centres des roues en mm, à 3 / 2000 mm près (coordonnées arrondies au µm).
-/

namespace AnticythereV2

/-- Bus des moyeux : la couronne de 96 mène un pignon de 24, la tringle tourne 4 fois plus vite ; à l'arrivée un pignon de 24 mène une couronne de 96 : rapport 1. 11 tringles : venus_L, neptune_L, mercury_L, mars_L, uranus_L, saturn_L, jupiter_L, moon_perigee, saros, moon_node, moon_L (moyeu = source de trains.json). -/
theorem bus_ratio : (96 / 24 : ℚ) = 4 ∧ ((96 / 24) * (24 / 96) : ℚ) = 1 := by
  norm_num

/-- Train `Y` placé (direct) : couples dans l'ordre réel 10:83 · 19:144 · 31:180 ; même produit que trains.json (31:180 · 19:144 · 10:83) et sens phys +1 depuis `J` (phys -1). -/
theorem place_Y :
    ((-10 / 83) * (-19 / 144) * (-31 / 180) : ℚ) =
    (1) * (-1) * (31 * 19 * 10 / (180 * 144 * 83)) := by
  norm_num

/-- Reprise de Y dans la tour de `venus_L` : 24 → pignon fou 96 → 24, rapport 1 et sens +1 (deux engrènements extérieurs). -/
theorem reprise_venus_L : (-(24 : ℚ) / 96) * (-96 / 24) = 1 := by
  norm_num

/-- Train `venus_L` placé (tower, bus Y4a supposé de même sens, reprise) : couples dans l'ordre réel 124:67 · 166:189 ; même produit que trains.json (124:67 · 166:189) et sens phys +1 depuis `Y` (phys +1). -/
theorem place_venus_L :
    ((96 / 24) * (24 / 96) * (-24 / 96) * (-96 / 24) * (-124 / 67) * (-166 / 189) : ℚ) =
    (1) * (1) * (124 * 166 / (67 * 189)) := by
  norm_num

/-- Train `precession_ring` placé (direct) : couples dans l'ordre réel 10:131 + 15:179 hors items ; même produit que trains.json (10:131 · 15:179) et sens phys -1 depuis `neptune_L` (phys +1). -/
theorem place_precession_ring :
    ((-10 / 131) * (15 / 179) : ℚ) =
    (-1) * (1) * (10 * 15 / (131 * 179)) := by
  norm_num

/-- Reprise de Y dans la tour de `neptune_L` : 24 → pignon fou 96 → 24, rapport 1 et sens +1 (deux engrènements extérieurs). -/
theorem reprise_neptune_L : (-(24 : ℚ) / 96) * (-96 / 24) = 1 := by
  norm_num

/-- Train `neptune_L` placé (tower, bus Y4a supposé de même sens, reprise) : couples dans l'ordre réel 12:148 · 11:147 ; même produit que trains.json (12:148 · 11:147) et sens phys +1 depuis `Y` (phys +1). -/
theorem place_neptune_L :
    ((96 / 24) * (24 / 96) * (-24 / 96) * (-96 / 24) * (-12 / 148) * (-11 / 147) : ℚ) =
    (1) * (1) * (12 * 11 / (148 * 147)) := by
  norm_num

/-- Reprise de Y dans la tour de `mercury_L` : 24 → pignon fou 24 → 24, rapport 1 et sens +1 (deux engrènements extérieurs). -/
theorem reprise_mercury_L : (-(24 : ℚ) / 24) * (-24 / 24) = 1 := by
  norm_num

/-- Train `mercury_L` placé (tower, bus Y4a supposé de même sens, reprise) : couples dans l'ordre réel 73:79 (fou 20) · 64:31 · 37:17 ; même produit que trains.json (37:17 · 64:31 · 73:79) et sens phys +1 depuis `Y` (phys +1). -/
theorem place_mercury_L :
    ((96 / 24) * (24 / 96) * (-24 / 24) * (-24 / 24) * (-73 / 20) * (-20 / 79) * (-64 / 31) * (-37 / 17) : ℚ) =
    (1) * (1) * (37 * 64 * 73 / (17 * 31 * 79)) := by
  norm_num

/-- Reprise de Y dans la tour de `mars_L` : 24 → pignon fou 64 → 24, rapport 1 et sens +1 (deux engrènements extérieurs). -/
theorem reprise_mars_L : (-(24 : ℚ) / 64) * (-64 / 24) = 1 := by
  norm_num

/-- Train `mars_L` placé (tower, bus Y4b supposé de même sens, reprise) : couples dans l'ordre réel 97:88 · 41:85 ; même produit que trains.json (97:88 · 41:85) et sens phys +1 depuis `Y` (phys +1). -/
theorem place_mars_L :
    ((96 / 24) * (24 / 96) * (-24 / 64) * (-64 / 24) * (-97 / 88) * (-41 / 85) : ℚ) =
    (1) * (1) * (97 * 41 / (88 * 85)) := by
  norm_num

/-- Reprise de Y dans la tour de `uranus_L` : 24 → pignon fou 64 → 24, rapport 1 et sens +1 (deux engrènements extérieurs). -/
theorem reprise_uranus_L : (-(24 : ℚ) / 64) * (-64 / 24) = 1 := by
  norm_num

/-- Train `uranus_L` placé (tower, bus Y4b supposé de même sens, reprise) : couples dans l'ordre réel 10:84 · 10:100 ; même produit que trains.json (10:84 · 10:100) et sens phys +1 depuis `Y` (phys +1). -/
theorem place_uranus_L :
    ((96 / 24) * (24 / 96) * (-24 / 64) * (-64 / 24) * (-10 / 84) * (-10 / 100) : ℚ) =
    (1) * (1) * (10 * 10 / (84 * 100)) := by
  norm_num

/-- Reprise de Y dans la tour de `saturn_L` : 24 → pignon fou 32 → 24, rapport 1 et sens +1 (deux engrènements extérieurs). -/
theorem reprise_saturn_L : (-(24 : ℚ) / 32) * (-32 / 24) = 1 := by
  norm_num

/-- Train `saturn_L` placé (tower, bus Y4b supposé de même sens, reprise) : couples dans l'ordre réel 10:41 · 11:79 ; même produit que trains.json (10:41 · 11:79) et sens phys +1 depuis `Y` (phys +1). -/
theorem place_saturn_L :
    ((96 / 24) * (24 / 96) * (-24 / 32) * (-32 / 24) * (-10 / 41) * (-11 / 79) : ℚ) =
    (1) * (1) * (10 * 11 / (41 * 79)) := by
  norm_num

/-- Reprise de Y dans la tour de `jupiter_L` : 24 → pignon fou 32 → 24, rapport 1 et sens +1 (deux engrènements extérieurs). -/
theorem reprise_jupiter_L : (-(24 : ℚ) / 32) * (-32 / 24) = 1 := by
  norm_num

/-- Train `jupiter_L` placé (tower, bus Y4a supposé de même sens, reprise) : couples dans l'ordre réel 10:26 · 16:73 ; même produit que trains.json (10:26 · 16:73) et sens phys +1 depuis `Y` (phys +1). -/
theorem place_jupiter_L :
    ((96 / 24) * (24 / 96) * (-24 / 32) * (-32 / 24) * (-10 / 26) * (-16 / 73) : ℚ) =
    (1) * (1) * (10 * 16 / (26 * 73)) := by
  norm_num

/-- Train `moon_perigee` placé (rod, bus Y4b supposé de même sens) : couples dans l'ordre réel 26:103 · 47:105 ; même produit que trains.json (47:105 · 26:103) et sens phys +1 depuis `Y` (phys +1). -/
theorem place_moon_perigee :
    ((96 / 24) * (24 / 96) * (-26 / 103) * (-47 / 105) : ℚ) =
    (1) * (1) * (47 * 26 / (105 * 103)) := by
  norm_num

/-- Train `saros` placé (rod, bus Y5 supposé de même sens) : couples dans l'ordre réel 13:46 · 21:107 ; même produit que trains.json (13:46 · 21:107) et sens phys +1 depuis `Y` (phys +1). -/
theorem place_saros :
    ((96 / 24) * (24 / 96) * (-13 / 46) * (-21 / 107) : ℚ) =
    (1) * (1) * (13 * 21 / (46 * 107)) := by
  norm_num

/-- Train `moon_node` placé (rod, bus Y5 supposé de même sens) : couples dans l'ordre réel 12:43 (fou 20) · 21:109 ; même produit que trains.json (12:43 · 21:109) et sens phys -1 depuis `Y` (phys +1). -/
theorem place_moon_node :
    ((96 / 24) * (24 / 96) * (-12 / 20) * (-20 / 43) * (-21 / 109) : ℚ) =
    (-1) * (1) * (12 * 21 / (43 * 109)) := by
  norm_num

/-- Train `moon_L` placé (rod, bus J5 supposé de même sens) : couples dans l'ordre réel 11:25 · 19:67 · 22:75 ; même produit que trains.json (11:25 · 22:75 · 19:67) et sens phys +1 depuis `J` (phys -1). -/
theorem place_moon_L :
    ((96 / 24) * (24 / 96) * (-11 / 25) * (-19 / 67) * (-22 / 75) : ℚ) =
    (1) * (-1) * (11 * 22 * 19 / (25 * 75 * 67)) := by
  norm_num

/-- Entrée de `moon_L` dans le bloc Lune : 40 → pignon fou 64 → 40 (module 1/2), rapport 1, sens +1, aux entraxes théoriques. -/
theorem moon_input_moon_L :
    (-(40 : ℚ) / 64) * (-64 / 40) = 1 ∧
    (((1 / 2) * (40 + 64) / 2) - 3 / 2000 : ℚ) ^ 2 < ((65.02) - (90.955) : ℚ) ^ 2 + ((-2.1) - (-0.268) : ℚ) ^ 2 ∧
    ((65.02) - (90.955) : ℚ) ^ 2 + ((-2.1) - (-0.268) : ℚ) ^ 2 < (((1 / 2) * (40 + 64) / 2) + 3 / 2000 : ℚ) ^ 2 ∧
    (((1 / 2) * (64 + 40) / 2) - 3 / 2000 : ℚ) ^ 2 < ((90.955) - (112.0) : ℚ) ^ 2 + ((-0.268) - (15.0) : ℚ) ^ 2 ∧
    ((90.955) - (112.0) : ℚ) ^ 2 + ((-0.268) - (15.0) : ℚ) ^ 2 < (((1 / 2) * (64 + 40) / 2) + 3 / 2000 : ℚ) ^ 2 := by
  refine ⟨?_, ?_, ?_, ?_, ?_⟩ <;> norm_num

/-- Entrée de `moon_node` dans le bloc Lune : 40 → pignon fou 96 → 40 (module 1/2), rapport 1, sens +1, aux entraxes théoriques. -/
theorem moon_input_moon_node :
    (-(40 : ℚ) / 96) * (-96 / 40) = 1 ∧
    (((1 / 2) * (40 + 96) / 2) - 3 / 2000 : ℚ) ^ 2 < ((65.02) - (96.392) : ℚ) ^ 2 + ((32.1) - (45.206) : ℚ) ^ 2 ∧
    ((65.02) - (96.392) : ℚ) ^ 2 + ((32.1) - (45.206) : ℚ) ^ 2 < (((1 / 2) * (40 + 96) / 2) + 3 / 2000 : ℚ) ^ 2 ∧
    (((1 / 2) * (96 + 40) / 2) - 3 / 2000 : ℚ) ^ 2 < ((96.392) - (112.0) : ℚ) ^ 2 + ((45.206) - (15.0) : ℚ) ^ 2 ∧
    ((96.392) - (112.0) : ℚ) ^ 2 + ((45.206) - (15.0) : ℚ) ^ 2 < (((1 / 2) * (96 + 40) / 2) + 3 / 2000 : ℚ) ^ 2 := by
  refine ⟨?_, ?_, ?_, ?_, ?_⟩ <;> norm_num

/-- Entrée de `moon_perigee` dans le bloc Lune : 40 → pignon fou 40 → 40 (module 1/2), rapport 1, sens +1, aux entraxes théoriques. -/
theorem moon_input_moon_perigee :
    (-(40 : ℚ) / 40) * (-40 / 40) = 1 ∧
    (((1 / 2) * (40 + 40) / 2) - 3 / 2000 : ℚ) ^ 2 < ((80.82) - (100.767) : ℚ) ^ 2 + ((-3.0) - (-1.548) : ℚ) ^ 2 ∧
    ((80.82) - (100.767) : ℚ) ^ 2 + ((-3.0) - (-1.548) : ℚ) ^ 2 < (((1 / 2) * (40 + 40) / 2) + 3 / 2000 : ℚ) ^ 2 ∧
    (((1 / 2) * (40 + 40) / 2) - 3 / 2000 : ℚ) ^ 2 < ((100.767) - (112.0) : ℚ) ^ 2 + ((-1.548) - (15.0) : ℚ) ^ 2 ∧
    ((100.767) - (112.0) : ℚ) ^ 2 + ((-1.548) - (15.0) : ℚ) ^ 2 < (((1 / 2) * (40 + 40) / 2) + 3 / 2000 : ℚ) ^ 2 := by
  refine ⟨?_, ?_, ?_, ?_, ?_⟩ <;> norm_num

/-- Précession : couple 10:131 (external, placé sous P4) puis 15:179 (internal, bloc du temps) : 10/131 · 15/179 = 150/23449. -/
theorem precession_ratio : (10 / 131 : ℚ) * (15 / 179) = 150 / 23449 := by
  norm_num

/-- Module changé de `neptune_L`, couple 11:147 : m = 11/20 mm, entraxe 43.45 mm, tenu par les centres placés. -/
theorem module_neptune_L_1 :
    (11 / 20) * (11 + 147) / 2 = (43.45 : ℚ) ∧
    (((11 / 20) * (11 + 147) / 2) - 3 / 2000 : ℚ) ^ 2 < ((98.79) - (56.0) : ℚ) ^ 2 + ((-104.455) - (-112.0) : ℚ) ^ 2 ∧
    ((98.79) - (56.0) : ℚ) ^ 2 + ((-104.455) - (-112.0) : ℚ) ^ 2 < (((11 / 20) * (11 + 147) / 2) + 3 / 2000 : ℚ) ^ 2 := by
  refine ⟨?_, ?_, ?_⟩ <;> norm_num

/-- Module changé de `jupiter_L`, couple 10:26 : m = 7/10 mm, entraxe 12.6 mm, tenu par les centres placés. -/
theorem module_jupiter_L_0 :
    (7 / 10) * (10 + 26) / 2 = (12.6 : ℚ) ∧
    (((7 / 10) * (10 + 26) / 2) - 3 / 2000 : ℚ) ^ 2 < ((-193.569) - (-187.269) : ℚ) ^ 2 + ((-111.787) - (-100.875) : ℚ) ^ 2 ∧
    ((-193.569) - (-187.269) : ℚ) ^ 2 + ((-111.787) - (-100.875) : ℚ) ^ 2 < (((7 / 10) * (10 + 26) / 2) + 3 / 2000 : ℚ) ^ 2 := by
  refine ⟨?_, ?_, ?_⟩ <;> norm_num

/-- ytrain#w0 (10 dents) ~ ytrain#w1 (83 dents), module 0.5 : même module et entraxe 23.25 mm à 3 / 2000 mm près. -/
theorem entraxe_ytrain_w0_w1 :
    (0.5 : ℚ) = 0.5 ∧
    (((1 / 2) * (10 + 83) / 2) - 3 / 2000 : ℚ) ^ 2 < ((-50.0) - (-50.0) : ℚ) ^ 2 + ((-20.0) - (3.25) : ℚ) ^ 2 ∧
    ((-50.0) - (-50.0) : ℚ) ^ 2 + ((-20.0) - (3.25) : ℚ) ^ 2 < (((1 / 2) * (10 + 83) / 2) + 3 / 2000 : ℚ) ^ 2 := by
  refine ⟨?_, ?_, ?_⟩ <;> norm_num

/-- ytrain#w2 (19 dents) ~ ytrain#w3 (144 dents), module 0.5 : même module et entraxe 40.75 mm à 3 / 2000 mm près. -/
theorem entraxe_ytrain_w2_w3 :
    (0.5 : ℚ) = 0.5 ∧
    (((1 / 2) * (19 + 144) / 2) - 3 / 2000 : ℚ) ^ 2 < ((-50.0) - (-33.687) : ℚ) ^ 2 + ((3.25) - (40.592) : ℚ) ^ 2 ∧
    ((-50.0) - (-33.687) : ℚ) ^ 2 + ((3.25) - (40.592) : ℚ) ^ 2 < (((1 / 2) * (19 + 144) / 2) + 3 / 2000 : ℚ) ^ 2 := by
  refine ⟨?_, ?_, ?_⟩ <;> norm_num

/-- ytrain#w4 (31 dents) ~ ytrain#w5 (180 dents), module 0.5 : même module et entraxe 52.75 mm à 3 / 2000 mm près. -/
theorem entraxe_ytrain_w4_w5 :
    (0.5 : ℚ) = 0.5 ∧
    (((1 / 2) * (31 + 180) / 2) - 3 / 2000 : ℚ) ^ 2 < ((-33.687) - (0.0) : ℚ) ^ 2 + ((40.592) - (0.0) : ℚ) ^ 2 ∧
    ((-33.687) - (0.0) : ℚ) ^ 2 + ((40.592) - (0.0) : ℚ) ^ 2 < (((1 / 2) * (31 + 180) / 2) + 3 / 2000 : ℚ) ^ 2 := by
  refine ⟨?_, ?_, ?_⟩ <;> norm_num

/-- venus_L#w0 (24 dents) ~ venus_L#w1 (96 dents), module 0.5 : même module et entraxe 30 mm à 3 / 2000 mm près. -/
theorem entraxe_venus_L_w0_w1 :
    (0.5 : ℚ) = 0.5 ∧
    (((1 / 2) * (24 + 96) / 2) - 3 / 2000 : ℚ) ^ 2 < ((-147.0) - (-129.597) : ℚ) ^ 2 + ((92.0) - (67.563) : ℚ) ^ 2 ∧
    ((-147.0) - (-129.597) : ℚ) ^ 2 + ((92.0) - (67.563) : ℚ) ^ 2 < (((1 / 2) * (24 + 96) / 2) + 3 / 2000 : ℚ) ^ 2 := by
  refine ⟨?_, ?_, ?_⟩ <;> norm_num

/-- venus_L#w1 (96 dents) ~ venus_L#w2 (24 dents), module 0.5 : même module et entraxe 30 mm à 3 / 2000 mm près. -/
theorem entraxe_venus_L_w1_w2 :
    (0.5 : ℚ) = 0.5 ∧
    (((1 / 2) * (96 + 24) / 2) - 3 / 2000 : ℚ) ^ 2 < ((-129.597) - (-99.603) : ℚ) ^ 2 + ((67.563) - (68.125) : ℚ) ^ 2 ∧
    ((-129.597) - (-99.603) : ℚ) ^ 2 + ((67.563) - (68.125) : ℚ) ^ 2 < (((1 / 2) * (96 + 24) / 2) + 3 / 2000 : ℚ) ^ 2 := by
  refine ⟨?_, ?_, ?_⟩ <;> norm_num

/-- venus_L#w3 (124 dents) ~ venus_L#w4 (67 dents), module 0.5 : même module et entraxe 47.75 mm à 3 / 2000 mm près. -/
theorem entraxe_venus_L_w3_w4 :
    (0.5 : ℚ) = 0.5 ∧
    (((1 / 2) * (124 + 67) / 2) - 3 / 2000 : ℚ) ^ 2 < ((-99.603) - (-58.25) : ℚ) ^ 2 + ((68.125) - (92.0) : ℚ) ^ 2 ∧
    ((-99.603) - (-58.25) : ℚ) ^ 2 + ((68.125) - (92.0) : ℚ) ^ 2 < (((1 / 2) * (124 + 67) / 2) + 3 / 2000 : ℚ) ^ 2 := by
  refine ⟨?_, ?_, ?_⟩ <;> norm_num

/-- venus_L#w5 (166 dents) ~ venus_L#w6 (189 dents), module 0.5 : même module et entraxe 88.75 mm à 3 / 2000 mm près. -/
theorem entraxe_venus_L_w5_w6 :
    (0.5 : ℚ) = 0.5 ∧
    (((1 / 2) * (166 + 189) / 2) - 3 / 2000 : ℚ) ^ 2 < ((-58.25) - (-147.0) : ℚ) ^ 2 + ((92.0) - (92.0) : ℚ) ^ 2 ∧
    ((-58.25) - (-147.0) : ℚ) ^ 2 + ((92.0) - (92.0) : ℚ) ^ 2 < (((1 / 2) * (166 + 189) / 2) + 3 / 2000 : ℚ) ^ 2 := by
  refine ⟨?_, ?_, ?_⟩ <;> norm_num

/-- neptune_L#w0 (24 dents) ~ neptune_L#w1 (96 dents), module 0.5 : même module et entraxe 30 mm à 3 / 2000 mm près. -/
theorem entraxe_neptune_L_w0_w1 :
    (0.5 : ℚ) = 0.5 ∧
    (((1 / 2) * (24 + 96) / 2) - 3 / 2000 : ℚ) ^ 2 < ((56.0) - (69.715) : ℚ) ^ 2 + ((-112.0) - (-85.318) : ℚ) ^ 2 ∧
    ((56.0) - (69.715) : ℚ) ^ 2 + ((-112.0) - (-85.318) : ℚ) ^ 2 < (((1 / 2) * (24 + 96) / 2) + 3 / 2000 : ℚ) ^ 2 := by
  refine ⟨?_, ?_, ?_⟩ <;> norm_num

/-- neptune_L#w1 (96 dents) ~ neptune_L#w2 (24 dents), module 0.5 : même module et entraxe 30 mm à 3 / 2000 mm près. -/
theorem entraxe_neptune_L_w1_w2 :
    (0.5 : ℚ) = 0.5 ∧
    (((1 / 2) * (96 + 24) / 2) - 3 / 2000 : ℚ) ^ 2 < ((69.715) - (91.844) : ℚ) ^ 2 + ((-85.318) - (-65.063) : ℚ) ^ 2 ∧
    ((69.715) - (91.844) : ℚ) ^ 2 + ((-85.318) - (-65.063) : ℚ) ^ 2 < (((1 / 2) * (96 + 24) / 2) + 3 / 2000 : ℚ) ^ 2 := by
  refine ⟨?_, ?_, ?_⟩ <;> norm_num

/-- neptune_L#w3 (12 dents) ~ neptune_L#w4 (148 dents), module 0.5 : même module et entraxe 40 mm à 3 / 2000 mm près. -/
theorem entraxe_neptune_L_w3_w4 :
    (0.5 : ℚ) = 0.5 ∧
    (((1 / 2) * (12 + 148) / 2) - 3 / 2000 : ℚ) ^ 2 < ((91.844) - (98.79) : ℚ) ^ 2 + ((-65.063) - (-104.455) : ℚ) ^ 2 ∧
    ((91.844) - (98.79) : ℚ) ^ 2 + ((-65.063) - (-104.455) : ℚ) ^ 2 < (((1 / 2) * (12 + 148) / 2) + 3 / 2000 : ℚ) ^ 2 := by
  refine ⟨?_, ?_, ?_⟩ <;> norm_num

/-- neptune_L#w5 (11 dents) ~ neptune_L#w6 (147 dents), module 0.55 : même module et entraxe 43.45 mm à 3 / 2000 mm près. -/
theorem entraxe_neptune_L_w5_w6 :
    (0.55 : ℚ) = 0.55 ∧
    (((11 / 20) * (11 + 147) / 2) - 3 / 2000 : ℚ) ^ 2 < ((98.79) - (56.0) : ℚ) ^ 2 + ((-104.455) - (-112.0) : ℚ) ^ 2 ∧
    ((98.79) - (56.0) : ℚ) ^ 2 + ((-104.455) - (-112.0) : ℚ) ^ 2 < (((11 / 20) * (11 + 147) / 2) + 3 / 2000 : ℚ) ^ 2 := by
  refine ⟨?_, ?_, ?_⟩ <;> norm_num

/-- prec#w0 (10 dents) ~ prec#w1 (131 dents), module 0.5 : même module et entraxe 35.25 mm à 3 / 2000 mm près. -/
theorem entraxe_prec_w0_w1 :
    (0.5 : ℚ) = 0.5 ∧
    (((1 / 2) * (10 + 131) / 2) - 3 / 2000 : ℚ) ^ 2 < ((56.0) - (90.714) : ℚ) ^ 2 + ((-112.0) - (-105.879) : ℚ) ^ 2 ∧
    ((56.0) - (90.714) : ℚ) ^ 2 + ((-112.0) - (-105.879) : ℚ) ^ 2 < (((1 / 2) * (10 + 131) / 2) + 3 / 2000 : ℚ) ^ 2 := by
  refine ⟨?_, ?_, ?_⟩ <;> norm_num

/-- mercury_L#w0 (24 dents) ~ mercury_L#w1 (24 dents), module 0.5 : même module et entraxe 12 mm à 3 / 2000 mm près. -/
theorem entraxe_mercury_L_w0_w1 :
    (0.5 : ℚ) = 0.5 ∧
    (((1 / 2) * (24 + 24) / 2) - 3 / 2000 : ℚ) ^ 2 < ((157.0) - (148.334) : ℚ) ^ 2 + ((102.0) - (93.699) : ℚ) ^ 2 ∧
    ((157.0) - (148.334) : ℚ) ^ 2 + ((102.0) - (93.699) : ℚ) ^ 2 < (((1 / 2) * (24 + 24) / 2) + 3 / 2000 : ℚ) ^ 2 := by
  refine ⟨?_, ?_, ?_⟩ <;> norm_num

/-- mercury_L#w1 (24 dents) ~ mercury_L#w2 (24 dents), module 0.5 : même module et entraxe 12 mm à 3 / 2000 mm près. -/
theorem entraxe_mercury_L_w1_w2 :
    (0.5 : ℚ) = 0.5 ∧
    (((1 / 2) * (24 + 24) / 2) - 3 / 2000 : ℚ) ^ 2 < ((148.334) - (145.065) : ℚ) ^ 2 + ((93.699) - (82.153) : ℚ) ^ 2 ∧
    ((148.334) - (145.065) : ℚ) ^ 2 + ((93.699) - (82.153) : ℚ) ^ 2 < (((1 / 2) * (24 + 24) / 2) + 3 / 2000 : ℚ) ^ 2 := by
  refine ⟨?_, ?_, ?_⟩ <;> norm_num

/-- mercury_L#w3 (73 dents) ~ mercury_L#w5 (20 dents), module 0.5 : même module et entraxe 23.25 mm à 3 / 2000 mm près. -/
theorem entraxe_mercury_L_w3_w5 :
    (0.5 : ℚ) = 0.5 ∧
    (((1 / 2) * (73 + 20) / 2) - 3 / 2000 : ℚ) ^ 2 < ((145.065) - (167.962) : ℚ) ^ 2 + ((82.153) - (78.116) : ℚ) ^ 2 ∧
    ((145.065) - (167.962) : ℚ) ^ 2 + ((82.153) - (78.116) : ℚ) ^ 2 < (((1 / 2) * (73 + 20) / 2) + 3 / 2000 : ℚ) ^ 2 := by
  refine ⟨?_, ?_, ?_⟩ <;> norm_num

/-- mercury_L#w4 (79 dents) ~ mercury_L#w5 (20 dents), module 0.5 : même module et entraxe 24.75 mm à 3 / 2000 mm près. -/
theorem entraxe_mercury_L_w4_w5 :
    (0.5 : ℚ) = 0.5 ∧
    (((1 / 2) * (79 + 20) / 2) - 3 / 2000 : ℚ) ^ 2 < ((183.871) - (167.962) : ℚ) ^ 2 + ((97.075) - (78.116) : ℚ) ^ 2 ∧
    ((183.871) - (167.962) : ℚ) ^ 2 + ((97.075) - (78.116) : ℚ) ^ 2 < (((1 / 2) * (79 + 20) / 2) + 3 / 2000 : ℚ) ^ 2 := by
  refine ⟨?_, ?_, ?_⟩ <;> norm_num

/-- mercury_L#w6 (64 dents) ~ mercury_L#w7 (31 dents), module 0.5 : même module et entraxe 23.75 mm à 3 / 2000 mm près. -/
theorem entraxe_mercury_L_w6_w7 :
    (0.5 : ℚ) = 0.5 ∧
    (((1 / 2) * (64 + 31) / 2) - 3 / 2000 : ℚ) ^ 2 < ((183.871) - (165.678) : ℚ) ^ 2 + ((97.075) - (112.342) : ℚ) ^ 2 ∧
    ((183.871) - (165.678) : ℚ) ^ 2 + ((97.075) - (112.342) : ℚ) ^ 2 < (((1 / 2) * (64 + 31) / 2) + 3 / 2000 : ℚ) ^ 2 := by
  refine ⟨?_, ?_, ?_⟩ <;> norm_num

/-- mercury_L#w8 (37 dents) ~ mercury_L#w9 (17 dents), module 0.5 : même module et entraxe 13.5 mm à 3 / 2000 mm près. -/
theorem entraxe_mercury_L_w8_w9 :
    (0.5 : ℚ) = 0.5 ∧
    (((1 / 2) * (37 + 17) / 2) - 3 / 2000 : ℚ) ^ 2 < ((165.678) - (157.0) : ℚ) ^ 2 + ((112.342) - (102.0) : ℚ) ^ 2 ∧
    ((165.678) - (157.0) : ℚ) ^ 2 + ((112.342) - (102.0) : ℚ) ^ 2 < (((1 / 2) * (37 + 17) / 2) + 3 / 2000 : ℚ) ^ 2 := by
  refine ⟨?_, ?_, ?_⟩ <;> norm_num

/-- mars_L#w0 (24 dents) ~ mars_L#w1 (64 dents), module 0.5 : même module et entraxe 22 mm à 3 / 2000 mm près. -/
theorem entraxe_mars_L_w0_w1 :
    (0.5 : ℚ) = 0.5 ∧
    (((1 / 2) * (24 + 64) / 2) - 3 / 2000 : ℚ) ^ 2 < ((5.0) - (26.08) : ℚ) ^ 2 + ((92.0) - (98.294) : ℚ) ^ 2 ∧
    ((5.0) - (26.08) : ℚ) ^ 2 + ((92.0) - (98.294) : ℚ) ^ 2 < (((1 / 2) * (24 + 64) / 2) + 3 / 2000 : ℚ) ^ 2 := by
  refine ⟨?_, ?_, ?_⟩ <;> norm_num

/-- mars_L#w1 (64 dents) ~ mars_L#w2 (24 dents), module 0.5 : même module et entraxe 22 mm à 3 / 2000 mm près. -/
theorem entraxe_mars_L_w1_w2 :
    (0.5 : ℚ) = 0.5 ∧
    (((1 / 2) * (64 + 24) / 2) - 3 / 2000 : ℚ) ^ 2 < ((26.08) - (37.162) : ℚ) ^ 2 + ((98.294) - (117.3) : ℚ) ^ 2 ∧
    ((26.08) - (37.162) : ℚ) ^ 2 + ((98.294) - (117.3) : ℚ) ^ 2 < (((1 / 2) * (64 + 24) / 2) + 3 / 2000 : ℚ) ^ 2 := by
  refine ⟨?_, ?_, ?_⟩ <;> norm_num

/-- mars_L#w3 (97 dents) ~ mars_L#w4 (88 dents), module 0.5 : même module et entraxe 46.25 mm à 3 / 2000 mm près. -/
theorem entraxe_mars_L_w3_w4 :
    (0.5 : ℚ) = 0.5 ∧
    (((1 / 2) * (97 + 88) / 2) - 3 / 2000 : ℚ) ^ 2 < ((37.162) - (29.13) : ℚ) ^ 2 + ((117.3) - (71.752) : ℚ) ^ 2 ∧
    ((37.162) - (29.13) : ℚ) ^ 2 + ((117.3) - (71.752) : ℚ) ^ 2 < (((1 / 2) * (97 + 88) / 2) + 3 / 2000 : ℚ) ^ 2 := by
  refine ⟨?_, ?_, ?_⟩ <;> norm_num

/-- mars_L#w5 (41 dents) ~ mars_L#w6 (85 dents), module 0.5 : même module et entraxe 31.5 mm à 3 / 2000 mm près. -/
theorem entraxe_mars_L_w5_w6 :
    (0.5 : ℚ) = 0.5 ∧
    (((1 / 2) * (41 + 85) / 2) - 3 / 2000 : ℚ) ^ 2 < ((29.13) - (5.0) : ℚ) ^ 2 + ((71.752) - (92.0) : ℚ) ^ 2 ∧
    ((29.13) - (5.0) : ℚ) ^ 2 + ((71.752) - (92.0) : ℚ) ^ 2 < (((1 / 2) * (41 + 85) / 2) + 3 / 2000 : ℚ) ^ 2 := by
  refine ⟨?_, ?_, ?_⟩ <;> norm_num

/-- uranus_L#w0 (24 dents) ~ uranus_L#w1 (64 dents), module 0.5 : même module et entraxe 22 mm à 3 / 2000 mm près. -/
theorem entraxe_uranus_L_w0_w1 :
    (0.5 : ℚ) = 0.5 ∧
    (((1 / 2) * (24 + 64) / 2) - 3 / 2000 : ℚ) ^ 2 < ((168.0) - (155.45) : ℚ) ^ 2 + ((-112.0) - (-130.069) : ℚ) ^ 2 ∧
    ((168.0) - (155.45) : ℚ) ^ 2 + ((-112.0) - (-130.069) : ℚ) ^ 2 < (((1 / 2) * (24 + 64) / 2) + 3 / 2000 : ℚ) ^ 2 := by
  refine ⟨?_, ?_, ?_⟩ <;> norm_num

/-- uranus_L#w1 (64 dents) ~ uranus_L#w2 (24 dents), module 0.5 : même module et entraxe 22 mm à 3 / 2000 mm près. -/
theorem entraxe_uranus_L_w1_w2 :
    (0.5 : ℚ) = 0.5 ∧
    (((1 / 2) * (64 + 24) / 2) - 3 / 2000 : ℚ) ^ 2 < ((155.45) - (134.121) : ℚ) ^ 2 + ((-130.069) - (-124.677) : ℚ) ^ 2 ∧
    ((155.45) - (134.121) : ℚ) ^ 2 + ((-130.069) - (-124.677) : ℚ) ^ 2 < (((1 / 2) * (64 + 24) / 2) + 3 / 2000 : ℚ) ^ 2 := by
  refine ⟨?_, ?_, ?_⟩ <;> norm_num

/-- uranus_L#w3 (10 dents) ~ uranus_L#w4 (84 dents), module 0.5 : même module et entraxe 23.5 mm à 3 / 2000 mm près. -/
theorem entraxe_uranus_L_w3_w4 :
    (0.5 : ℚ) = 0.5 ∧
    (((1 / 2) * (10 + 84) / 2) - 3 / 2000 : ℚ) ^ 2 < ((134.121) - (142.158) : ℚ) ^ 2 + ((-124.677) - (-102.594) : ℚ) ^ 2 ∧
    ((134.121) - (142.158) : ℚ) ^ 2 + ((-124.677) - (-102.594) : ℚ) ^ 2 < (((1 / 2) * (10 + 84) / 2) + 3 / 2000 : ℚ) ^ 2 := by
  refine ⟨?_, ?_, ?_⟩ <;> norm_num

/-- uranus_L#w5 (10 dents) ~ uranus_L#w6 (100 dents), module 0.5 : même module et entraxe 27.5 mm à 3 / 2000 mm près. -/
theorem entraxe_uranus_L_w5_w6 :
    (0.5 : ℚ) = 0.5 ∧
    (((1 / 2) * (10 + 100) / 2) - 3 / 2000 : ℚ) ^ 2 < ((142.158) - (168.0) : ℚ) ^ 2 + ((-102.594) - (-112.0) : ℚ) ^ 2 ∧
    ((142.158) - (168.0) : ℚ) ^ 2 + ((-102.594) - (-112.0) : ℚ) ^ 2 < (((1 / 2) * (10 + 100) / 2) + 3 / 2000 : ℚ) ^ 2 := by
  refine ⟨?_, ?_, ?_⟩ <;> norm_num

/-- saturn_L#w0 (24 dents) ~ saturn_L#w1 (32 dents), module 0.5 : même module et entraxe 14 mm à 3 / 2000 mm près. -/
theorem entraxe_saturn_L_w0_w1 :
    (0.5 : ℚ) = 0.5 ∧
    (((1 / 2) * (24 + 32) / 2) - 3 / 2000 : ℚ) ^ 2 < ((-56.0) - (-65.382) : ℚ) ^ 2 + ((-112.0) - (-101.609) : ℚ) ^ 2 ∧
    ((-56.0) - (-65.382) : ℚ) ^ 2 + ((-112.0) - (-101.609) : ℚ) ^ 2 < (((1 / 2) * (24 + 32) / 2) + 3 / 2000 : ℚ) ^ 2 := by
  refine ⟨?_, ?_, ?_⟩ <;> norm_num

/-- saturn_L#w1 (32 dents) ~ saturn_L#w2 (24 dents), module 0.5 : même module et entraxe 14 mm à 3 / 2000 mm près. -/
theorem entraxe_saturn_L_w1_w2 :
    (0.5 : ℚ) = 0.5 ∧
    (((1 / 2) * (32 + 24) / 2) - 3 / 2000 : ℚ) ^ 2 < ((-65.382) - (-64.649) : ℚ) ^ 2 + ((-101.609) - (-87.628) : ℚ) ^ 2 ∧
    ((-65.382) - (-64.649) : ℚ) ^ 2 + ((-101.609) - (-87.628) : ℚ) ^ 2 < (((1 / 2) * (32 + 24) / 2) + 3 / 2000 : ℚ) ^ 2 := by
  refine ⟨?_, ?_, ?_⟩ <;> norm_num

/-- saturn_L#w3 (10 dents) ~ saturn_L#w4 (41 dents), module 0.5 : même module et entraxe 12.75 mm à 3 / 2000 mm près. -/
theorem entraxe_saturn_L_w3_w4 :
    (0.5 : ℚ) = 0.5 ∧
    (((1 / 2) * (10 + 41) / 2) - 3 / 2000 : ℚ) ^ 2 < ((-64.649) - (-52.093) : ℚ) ^ 2 + ((-87.628) - (-89.842) : ℚ) ^ 2 ∧
    ((-64.649) - (-52.093) : ℚ) ^ 2 + ((-87.628) - (-89.842) : ℚ) ^ 2 < (((1 / 2) * (10 + 41) / 2) + 3 / 2000 : ℚ) ^ 2 := by
  refine ⟨?_, ?_, ?_⟩ <;> norm_num

/-- saturn_L#w5 (11 dents) ~ saturn_L#w6 (79 dents), module 0.5 : même module et entraxe 22.5 mm à 3 / 2000 mm près. -/
theorem entraxe_saturn_L_w5_w6 :
    (0.5 : ℚ) = 0.5 ∧
    (((1 / 2) * (11 + 79) / 2) - 3 / 2000 : ℚ) ^ 2 < ((-52.093) - (-56.0) : ℚ) ^ 2 + ((-89.842) - (-112.0) : ℚ) ^ 2 ∧
    ((-52.093) - (-56.0) : ℚ) ^ 2 + ((-89.842) - (-112.0) : ℚ) ^ 2 < (((1 / 2) * (11 + 79) / 2) + 3 / 2000 : ℚ) ^ 2 := by
  refine ⟨?_, ?_, ?_⟩ <;> norm_num

/-- jupiter_L#w0 (24 dents) ~ jupiter_L#w1 (32 dents), module 0.5 : même module et entraxe 14 mm à 3 / 2000 mm près. -/
theorem entraxe_jupiter_L_w0_w1 :
    (0.5 : ℚ) = 0.5 ∧
    (((1 / 2) * (24 + 32) / 2) - 3 / 2000 : ℚ) ^ 2 < ((-168.0) - (-180.832) : ℚ) ^ 2 + ((-112.0) - (-117.598) : ℚ) ^ 2 ∧
    ((-168.0) - (-180.832) : ℚ) ^ 2 + ((-112.0) - (-117.598) : ℚ) ^ 2 < (((1 / 2) * (24 + 32) / 2) + 3 / 2000 : ℚ) ^ 2 := by
  refine ⟨?_, ?_, ?_⟩ <;> norm_num

/-- jupiter_L#w1 (32 dents) ~ jupiter_L#w2 (24 dents), module 0.5 : même module et entraxe 14 mm à 3 / 2000 mm près. -/
theorem entraxe_jupiter_L_w1_w2 :
    (0.5 : ℚ) = 0.5 ∧
    (((1 / 2) * (32 + 24) / 2) - 3 / 2000 : ℚ) ^ 2 < ((-180.832) - (-193.569) : ℚ) ^ 2 + ((-117.598) - (-111.787) : ℚ) ^ 2 ∧
    ((-180.832) - (-193.569) : ℚ) ^ 2 + ((-117.598) - (-111.787) : ℚ) ^ 2 < (((1 / 2) * (32 + 24) / 2) + 3 / 2000 : ℚ) ^ 2 := by
  refine ⟨?_, ?_, ?_⟩ <;> norm_num

/-- jupiter_L#w3 (10 dents) ~ jupiter_L#w4 (26 dents), module 0.7 : même module et entraxe 12.6 mm à 3 / 2000 mm près. -/
theorem entraxe_jupiter_L_w3_w4 :
    (0.7 : ℚ) = 0.7 ∧
    (((7 / 10) * (10 + 26) / 2) - 3 / 2000 : ℚ) ^ 2 < ((-193.569) - (-187.269) : ℚ) ^ 2 + ((-111.787) - (-100.875) : ℚ) ^ 2 ∧
    ((-193.569) - (-187.269) : ℚ) ^ 2 + ((-111.787) - (-100.875) : ℚ) ^ 2 < (((7 / 10) * (10 + 26) / 2) + 3 / 2000 : ℚ) ^ 2 := by
  refine ⟨?_, ?_, ?_⟩ <;> norm_num

/-- jupiter_L#w5 (16 dents) ~ jupiter_L#w6 (73 dents), module 0.5 : même module et entraxe 22.25 mm à 3 / 2000 mm près. -/
theorem entraxe_jupiter_L_w5_w6 :
    (0.5 : ℚ) = 0.5 ∧
    (((1 / 2) * (16 + 73) / 2) - 3 / 2000 : ℚ) ^ 2 < ((-187.269) - (-168.0) : ℚ) ^ 2 + ((-100.875) - (-112.0) : ℚ) ^ 2 ∧
    ((-187.269) - (-168.0) : ℚ) ^ 2 + ((-100.875) - (-112.0) : ℚ) ^ 2 < (((1 / 2) * (16 + 73) / 2) + 3 / 2000 : ℚ) ^ 2 := by
  refine ⟨?_, ?_, ?_⟩ <;> norm_num

/-- moon_perigee#w0 (26 dents) ~ moon_perigee#w1 (103 dents), module 0.5 : même module et entraxe 32.25 mm à 3 / 2000 mm près. -/
theorem entraxe_moon_perigee_w0_w1 :
    (0.5 : ℚ) = 0.5 ∧
    (((1 / 2) * (26 + 103) / 2) - 3 / 2000 : ℚ) ^ 2 < ((47.914) - (47.914) : ℚ) ^ 2 + ((10.25) - (-22.0) : ℚ) ^ 2 ∧
    ((47.914) - (47.914) : ℚ) ^ 2 + ((10.25) - (-22.0) : ℚ) ^ 2 < (((1 / 2) * (26 + 103) / 2) + 3 / 2000 : ℚ) ^ 2 := by
  refine ⟨?_, ?_, ?_⟩ <;> norm_num

/-- moon_perigee#w2 (47 dents) ~ moon_perigee#w3 (105 dents), module 0.5 : même module et entraxe 38 mm à 3 / 2000 mm près. -/
theorem entraxe_moon_perigee_w2_w3 :
    (0.5 : ℚ) = 0.5 ∧
    (((1 / 2) * (47 + 105) / 2) - 3 / 2000 : ℚ) ^ 2 < ((47.914) - (80.823) : ℚ) ^ 2 + ((-22.0) - (-3.0) : ℚ) ^ 2 ∧
    ((47.914) - (80.823) : ℚ) ^ 2 + ((-22.0) - (-3.0) : ℚ) ^ 2 < (((1 / 2) * (47 + 105) / 2) + 3 / 2000 : ℚ) ^ 2 := by
  refine ⟨?_, ?_, ?_⟩ <;> norm_num

/-- saros#w0 (13 dents) ~ saros#w1 (46 dents), module 0.5 : même module et entraxe 14.75 mm à 3 / 2000 mm près. -/
theorem entraxe_saros_w0_w1 :
    (0.5 : ℚ) = 0.5 ∧
    (((1 / 2) * (13 + 46) / 2) - 3 / 2000 : ℚ) ^ 2 < ((154.011) - (159.055) : ℚ) ^ 2 + ((-84.069) - (-97.93) : ℚ) ^ 2 ∧
    ((154.011) - (159.055) : ℚ) ^ 2 + ((-84.069) - (-97.93) : ℚ) ^ 2 < (((1 / 2) * (13 + 46) / 2) + 3 / 2000 : ℚ) ^ 2 := by
  refine ⟨?_, ?_, ?_⟩ <;> norm_num

/-- saros#w2 (21 dents) ~ saros#w3 (107 dents), module 0.5 : même module et entraxe 32 mm à 3 / 2000 mm près. -/
theorem entraxe_saros_w2_w3 :
    (0.5 : ℚ) = 0.5 ∧
    (((1 / 2) * (21 + 107) / 2) - 3 / 2000 : ℚ) ^ 2 < ((159.055) - (170.0) : ℚ) ^ 2 + ((-97.93) - (-128.0) : ℚ) ^ 2 ∧
    ((159.055) - (170.0) : ℚ) ^ 2 + ((-97.93) - (-128.0) : ℚ) ^ 2 < (((1 / 2) * (21 + 107) / 2) + 3 / 2000 : ℚ) ^ 2 := by
  refine ⟨?_, ?_, ?_⟩ <;> norm_num

/-- moon_node#w0 (12 dents) ~ moon_node#w2 (20 dents), module 0.5 : même module et entraxe 8 mm à 3 / 2000 mm près. -/
theorem entraxe_moon_node_w0_w2 :
    (0.5 : ℚ) = 0.5 ∧
    (((1 / 2) * (12 + 20) / 2) - 3 / 2000 : ℚ) ^ 2 < ((11.37) - (17.498) : ℚ) ^ 2 + ((45.622) - (40.48) : ℚ) ^ 2 ∧
    ((11.37) - (17.498) : ℚ) ^ 2 + ((45.622) - (40.48) : ℚ) ^ 2 < (((1 / 2) * (12 + 20) / 2) + 3 / 2000 : ℚ) ^ 2 := by
  refine ⟨?_, ?_, ?_⟩ <;> norm_num

/-- moon_node#w1 (43 dents) ~ moon_node#w2 (20 dents), module 0.5 : même module et entraxe 15.75 mm à 3 / 2000 mm près. -/
theorem entraxe_moon_node_w1_w2 :
    (0.5 : ℚ) = 0.5 ∧
    (((1 / 2) * (43 + 20) / 2) - 3 / 2000 : ℚ) ^ 2 < ((33.009) - (17.498) : ℚ) ^ 2 + ((37.745) - (40.48) : ℚ) ^ 2 ∧
    ((33.009) - (17.498) : ℚ) ^ 2 + ((37.745) - (40.48) : ℚ) ^ 2 < (((1 / 2) * (43 + 20) / 2) + 3 / 2000 : ℚ) ^ 2 := by
  refine ⟨?_, ?_, ?_⟩ <;> norm_num

/-- moon_node#w3 (21 dents) ~ moon_node#w4 (109 dents), module 0.5 : même module et entraxe 32.5 mm à 3 / 2000 mm près. -/
theorem entraxe_moon_node_w3_w4 :
    (0.5 : ℚ) = 0.5 ∧
    (((1 / 2) * (21 + 109) / 2) - 3 / 2000 : ℚ) ^ 2 < ((33.009) - (65.015) : ℚ) ^ 2 + ((37.745) - (32.101) : ℚ) ^ 2 ∧
    ((33.009) - (65.015) : ℚ) ^ 2 + ((37.745) - (32.101) : ℚ) ^ 2 < (((1 / 2) * (21 + 109) / 2) + 3 / 2000 : ℚ) ^ 2 := by
  refine ⟨?_, ?_, ?_⟩ <;> norm_num

/-- moon_L#w0 (11 dents) ~ moon_L#w1 (25 dents), module 0.5 : même module et entraxe 9 mm à 3 / 2000 mm près. -/
theorem entraxe_moon_L_w0_w1 :
    (0.5 : ℚ) = 0.5 ∧
    (((1 / 2) * (11 + 25) / 2) - 3 / 2000 : ℚ) ^ 2 < ((13.567) - (22.024) : ℚ) ^ 2 + ((-20.827) - (-17.748) : ℚ) ^ 2 ∧
    ((13.567) - (22.024) : ℚ) ^ 2 + ((-20.827) - (-17.748) : ℚ) ^ 2 < (((1 / 2) * (11 + 25) / 2) + 3 / 2000 : ℚ) ^ 2 := by
  refine ⟨?_, ?_, ?_⟩ <;> norm_num

/-- moon_L#w2 (19 dents) ~ moon_L#w3 (67 dents), module 0.5 : même module et entraxe 21.5 mm à 3 / 2000 mm près. -/
theorem entraxe_moon_L_w2_w3 :
    (0.5 : ℚ) = 0.5 ∧
    (((1 / 2) * (19 + 67) / 2) - 3 / 2000 : ℚ) ^ 2 < ((22.024) - (42.228) : ℚ) ^ 2 + ((-17.748) - (-10.395) : ℚ) ^ 2 ∧
    ((22.024) - (42.228) : ℚ) ^ 2 + ((-17.748) - (-10.395) : ℚ) ^ 2 < (((1 / 2) * (19 + 67) / 2) + 3 / 2000 : ℚ) ^ 2 := by
  refine ⟨?_, ?_, ?_⟩ <;> norm_num

/-- moon_L#w4 (22 dents) ~ moon_L#w5 (75 dents), module 0.5 : même module et entraxe 24.25 mm à 3 / 2000 mm près. -/
theorem entraxe_moon_L_w4_w5 :
    (0.5 : ℚ) = 0.5 ∧
    (((1 / 2) * (22 + 75) / 2) - 3 / 2000 : ℚ) ^ 2 < ((42.228) - (65.015) : ℚ) ^ 2 + ((-10.395) - (-2.101) : ℚ) ^ 2 ∧
    ((42.228) - (65.015) : ℚ) ^ 2 + ((-10.395) - (-2.101) : ℚ) ^ 2 < (((1 / 2) * (22 + 75) / 2) + 3 / 2000 : ℚ) ^ 2 := by
  refine ⟨?_, ?_, ?_⟩ <;> norm_num

end AnticythereV2
