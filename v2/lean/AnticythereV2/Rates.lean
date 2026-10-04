-- GÉNÉRÉ par v2/tools/make_lean_v2.py depuis v2/spec/trains.json et v2/spec/architecture.json.
-- Ne pas éditer à la main : relancer le générateur.

import AnticythereV2.Kinematics

/-!
# Vitesses moyennes et précision

`mean_*` : les unités non linéaires (Kepler, modules vectoriels, cascade lunaire, joint de Hooke…) font un
tour de sortie par tour d'entrée ; leur vitesse MOYENNE est donc la combinaison exacte de leurs entrées, et
vaut `rate_vs_J` tours par tour de J.

`bound_*` : pour J = 1 tour par jour, l'écart entre la vitesse de la machine et la cible (décimale exacte de
constants.json, éphémérides JPL 2000–2100) multiplié par 360 · 36525 (degrés par siècle julien) est sous la
borne du candidat (énoncé exact de trains.json) ; l'erreur relative |machine − cible| / |cible| est en outre
majorée (CONTRACT.md § 6), par un majorant à deux chiffres significatifs. Les cibles sont indépendantes des
dents : un nombre de dents faux (même avec des vitesses déclarées recalculées) fait échouer ces théorèmes.
-/

namespace AnticythereV2

/-- `earth_true` (Terre vraie λ (sortie de l’unité de Kepler de la Terre)) : ω earth_true = (1)·ω Y en moyenne (unité de Kepler (équant bissecté) : un tour par tour) ; 589/215136 tour par tour de J. -/
theorem mean_earth_true (ω : Shaft → ℚ) (h : Kinematics ω) :
    ω .earth_true = ω .Y ∧ ω .earth_true = (589 / 215136) * ω .J := by
  have r_earth_true : ω .earth_true = ω .J * (589 / 215136) := determined ω h .earth_true
  have r_Y : ω .Y = ω .J * (589 / 215136) := determined ω h .Y
  refine ⟨?_, ?_⟩
  · linear_combination r_earth_true + (-1 : ℚ) * r_Y
  · linear_combination r_earth_true

/-- `alpha_sun` (Ascension droite vraie du Soleil α (sortie du joint de Hooke)) : ω alpha_sun = (1)·ω lambda_trop en moyenne (joint de Hooke plié à ε = 23,44° : tan α = cos ε · tan λ, un tour par tour) ; 25041150643/9146084728032 tour par tour de J. -/
theorem mean_alpha_sun (ω : Shaft → ℚ) (h : Kinematics ω) :
    ω .alpha_sun = ω .lambda_trop ∧ ω .alpha_sun = (25041150643 / 9146084728032) * ω .J := by
  have r_alpha_sun : ω .alpha_sun = ω .J * (25041150643 / 9146084728032) := determined ω h .alpha_sun
  have r_lambda_trop : ω .lambda_trop = ω .J * (25041150643 / 9146084728032) := determined ω h .lambda_trop
  refine ⟨?_, ?_⟩
  · linear_combination r_alpha_sun + (-1 : ℚ) * r_lambda_trop
  · linear_combination r_alpha_sun

/-- `mercury_true` (Mercure vraie (sortie de l’unité de Kepler)) : ω mercury_true = (1)·ω mercury_L en moyenne (résolveur de Kepler (RK) + ellipse à deux bras : un tour par tour) ; 102638/9028989 tour par tour de J. -/
theorem mean_mercury_true (ω : Shaft → ℚ) (h : Kinematics ω) :
    ω .mercury_true = ω .mercury_L ∧ ω .mercury_true = (102638 / 9028989) * ω .J := by
  have r_mercury_true : ω .mercury_true = ω .J * (102638 / 9028989) := determined ω h .mercury_true
  have r_mercury_L : ω .mercury_L = ω .J * (102638 / 9028989) := determined ω h .mercury_L
  refine ⟨?_, ?_⟩
  · linear_combination r_mercury_true + (-1 : ℚ) * r_mercury_L
  · linear_combination r_mercury_true

/-- `venus_true` (Vénus vraie (sortie de l’unité de Kepler)) : ω venus_true = (1)·ω venus_L en moyenne (équant bissecté : un tour par tour) ; 18259/4102812 tour par tour de J. -/
theorem mean_venus_true (ω : Shaft → ℚ) (h : Kinematics ω) :
    ω .venus_true = ω .venus_L ∧ ω .venus_true = (18259 / 4102812) * ω .J := by
  have r_venus_true : ω .venus_true = ω .J * (18259 / 4102812) := determined ω h .venus_true
  have r_venus_L : ω .venus_L = ω .J * (18259 / 4102812) := determined ω h .venus_L
  refine ⟨?_, ?_⟩
  · linear_combination r_venus_true + (-1 : ℚ) * r_venus_L
  · linear_combination r_venus_true

/-- `mars_true` (Mars vraie (sortie de l’unité de Kepler)) : ω mars_true = (1)·ω mars_L en moyenne (équant + épicyclet (EQE) : un tour par tour) ; 2342453/1609217280 tour par tour de J. -/
theorem mean_mars_true (ω : Shaft → ℚ) (h : Kinematics ω) :
    ω .mars_true = ω .mars_L ∧ ω .mars_true = (2342453 / 1609217280) * ω .J := by
  have r_mars_true : ω .mars_true = ω .J * (2342453 / 1609217280) := determined ω h .mars_true
  have r_mars_L : ω .mars_L = ω .J * (2342453 / 1609217280) := determined ω h .mars_L
  refine ⟨?_, ?_⟩
  · linear_combination r_mars_true + (-1 : ℚ) * r_mars_L
  · linear_combination r_mars_true

/-- `jupiter_true` (Jupiter vraie (sortie de l’unité de Kepler)) : ω jupiter_true = (1)·ω jupiter_L en moyenne (équant bissecté : un tour par tour) ; 2945/12760254 tour par tour de J. -/
theorem mean_jupiter_true (ω : Shaft → ℚ) (h : Kinematics ω) :
    ω .jupiter_true = ω .jupiter_L ∧ ω .jupiter_true = (2945 / 12760254) * ω .J := by
  have r_jupiter_true : ω .jupiter_true = ω .J * (2945 / 12760254) := determined ω h .jupiter_true
  have r_jupiter_L : ω .jupiter_L = ω .J * (2945 / 12760254) := determined ω h .jupiter_L
  refine ⟨?_, ?_⟩
  · linear_combination r_jupiter_true + (-1 : ℚ) * r_jupiter_L
  · linear_combination r_jupiter_true

/-- `saturn_true` (Saturne vraie (sortie de l’unité de Kepler)) : ω saturn_true = (1)·ω saturn_L en moyenne (équant bissecté : un tour par tour) ; 32395/348412752 tour par tour de J. -/
theorem mean_saturn_true (ω : Shaft → ℚ) (h : Kinematics ω) :
    ω .saturn_true = ω .saturn_L ∧ ω .saturn_true = (32395 / 348412752) * ω .J := by
  have r_saturn_true : ω .saturn_true = ω .J * (32395 / 348412752) := determined ω h .saturn_true
  have r_saturn_L : ω .saturn_L = ω .J * (32395 / 348412752) := determined ω h .saturn_L
  refine ⟨?_, ?_⟩
  · linear_combination r_saturn_true + (-1 : ℚ) * r_saturn_L
  · linear_combination r_saturn_true

/-- `uranus_true` (Uranus vraie (sortie de l’unité de Kepler)) : ω uranus_true = (1)·ω uranus_L en moyenne (équant bissecté : un tour par tour) ; 589/18071424 tour par tour de J. -/
theorem mean_uranus_true (ω : Shaft → ℚ) (h : Kinematics ω) :
    ω .uranus_true = ω .uranus_L ∧ ω .uranus_true = (589 / 18071424) * ω .J := by
  have r_uranus_true : ω .uranus_true = ω .J * (589 / 18071424) := determined ω h .uranus_true
  have r_uranus_L : ω .uranus_L = ω .J * (589 / 18071424) := determined ω h .uranus_L
  refine ⟨?_, ?_⟩
  · linear_combination r_uranus_true + (-1 : ℚ) * r_uranus_L
  · linear_combination r_uranus_true

/-- `neptune_true` (Neptune vraie (sortie de l’unité de Kepler)) : ω neptune_true = (1)·ω neptune_L en moyenne (équant bissecté : un tour par tour) ; 6479/390041568 tour par tour de J. -/
theorem mean_neptune_true (ω : Shaft → ℚ) (h : Kinematics ω) :
    ω .neptune_true = ω .neptune_L ∧ ω .neptune_true = (6479 / 390041568) * ω .J := by
  have r_neptune_true : ω .neptune_true = ω .J * (6479 / 390041568) := determined ω h .neptune_true
  have r_neptune_L : ω .neptune_L = ω .J * (6479 / 390041568) := determined ω h .neptune_L
  refine ⟨?_, ?_⟩
  · linear_combination r_neptune_true + (-1 : ℚ) * r_neptune_L
  · linear_combination r_neptune_true

/-- `mercury_geo` (Mercure : aiguille géocentrique (module vectoriel)) : ω mercury_geo = (1)·ω Y en moyenne (module vectoriel (suiveur) : en moyenne le Soleil (planète intérieure)) ; 589/215136 tour par tour de J. -/
theorem mean_mercury_geo (ω : Shaft → ℚ) (h : Kinematics ω) :
    ω .mercury_geo = ω .Y ∧ ω .mercury_geo = (589 / 215136) * ω .J := by
  have r_mercury_geo : ω .mercury_geo = ω .J * (589 / 215136) := determined ω h .mercury_geo
  have r_Y : ω .Y = ω .J * (589 / 215136) := determined ω h .Y
  refine ⟨?_, ?_⟩
  · linear_combination r_mercury_geo + (-1 : ℚ) * r_Y
  · linear_combination r_mercury_geo

/-- `venus_geo` (Vénus : aiguille géocentrique (module vectoriel)) : ω venus_geo = (1)·ω Y en moyenne (module vectoriel (suiveur) : en moyenne le Soleil (planète intérieure)) ; 589/215136 tour par tour de J. -/
theorem mean_venus_geo (ω : Shaft → ℚ) (h : Kinematics ω) :
    ω .venus_geo = ω .Y ∧ ω .venus_geo = (589 / 215136) * ω .J := by
  have r_venus_geo : ω .venus_geo = ω .J * (589 / 215136) := determined ω h .venus_geo
  have r_Y : ω .Y = ω .J * (589 / 215136) := determined ω h .Y
  refine ⟨?_, ?_⟩
  · linear_combination r_venus_geo + (-1 : ℚ) * r_Y
  · linear_combination r_venus_geo

/-- `mars_geo` (Mars : aiguille géocentrique (module vectoriel)) : ω mars_geo = (1)·ω mars_L en moyenne (module vectoriel (suiveur) : en moyenne la planète (planète extérieure)) ; 2342453/1609217280 tour par tour de J. -/
theorem mean_mars_geo (ω : Shaft → ℚ) (h : Kinematics ω) :
    ω .mars_geo = ω .mars_L ∧ ω .mars_geo = (2342453 / 1609217280) * ω .J := by
  have r_mars_geo : ω .mars_geo = ω .J * (2342453 / 1609217280) := determined ω h .mars_geo
  have r_mars_L : ω .mars_L = ω .J * (2342453 / 1609217280) := determined ω h .mars_L
  refine ⟨?_, ?_⟩
  · linear_combination r_mars_geo + (-1 : ℚ) * r_mars_L
  · linear_combination r_mars_geo

/-- `jupiter_geo` (Jupiter : aiguille géocentrique (module vectoriel)) : ω jupiter_geo = (1)·ω jupiter_L en moyenne (module vectoriel (suiveur) : en moyenne la planète (planète extérieure)) ; 2945/12760254 tour par tour de J. -/
theorem mean_jupiter_geo (ω : Shaft → ℚ) (h : Kinematics ω) :
    ω .jupiter_geo = ω .jupiter_L ∧ ω .jupiter_geo = (2945 / 12760254) * ω .J := by
  have r_jupiter_geo : ω .jupiter_geo = ω .J * (2945 / 12760254) := determined ω h .jupiter_geo
  have r_jupiter_L : ω .jupiter_L = ω .J * (2945 / 12760254) := determined ω h .jupiter_L
  refine ⟨?_, ?_⟩
  · linear_combination r_jupiter_geo + (-1 : ℚ) * r_jupiter_L
  · linear_combination r_jupiter_geo

/-- `saturn_geo` (Saturne : aiguille géocentrique (module vectoriel)) : ω saturn_geo = (1)·ω saturn_L en moyenne (module vectoriel (suiveur) : en moyenne la planète (planète extérieure)) ; 32395/348412752 tour par tour de J. -/
theorem mean_saturn_geo (ω : Shaft → ℚ) (h : Kinematics ω) :
    ω .saturn_geo = ω .saturn_L ∧ ω .saturn_geo = (32395 / 348412752) * ω .J := by
  have r_saturn_geo : ω .saturn_geo = ω .J * (32395 / 348412752) := determined ω h .saturn_geo
  have r_saturn_L : ω .saturn_L = ω .J * (32395 / 348412752) := determined ω h .saturn_L
  refine ⟨?_, ?_⟩
  · linear_combination r_saturn_geo + (-1 : ℚ) * r_saturn_L
  · linear_combination r_saturn_geo

/-- `uranus_geo` (Uranus : aiguille géocentrique (module vectoriel)) : ω uranus_geo = (1)·ω uranus_L en moyenne (module vectoriel (suiveur) : en moyenne la planète (planète extérieure)) ; 589/18071424 tour par tour de J. -/
theorem mean_uranus_geo (ω : Shaft → ℚ) (h : Kinematics ω) :
    ω .uranus_geo = ω .uranus_L ∧ ω .uranus_geo = (589 / 18071424) * ω .J := by
  have r_uranus_geo : ω .uranus_geo = ω .J * (589 / 18071424) := determined ω h .uranus_geo
  have r_uranus_L : ω .uranus_L = ω .J * (589 / 18071424) := determined ω h .uranus_L
  refine ⟨?_, ?_⟩
  · linear_combination r_uranus_geo + (-1 : ℚ) * r_uranus_L
  · linear_combination r_uranus_geo

/-- `neptune_geo` (Neptune : aiguille géocentrique (module vectoriel)) : ω neptune_geo = (1)·ω neptune_L en moyenne (module vectoriel (suiveur) : en moyenne la planète (planète extérieure)) ; 6479/390041568 tour par tour de J. -/
theorem mean_neptune_geo (ω : Shaft → ℚ) (h : Kinematics ω) :
    ω .neptune_geo = ω .neptune_L ∧ ω .neptune_geo = (6479 / 390041568) * ω .J := by
  have r_neptune_geo : ω .neptune_geo = ω .J * (6479 / 390041568) := determined ω h .neptune_geo
  have r_neptune_L : ω .neptune_L = ω .J * (6479 / 390041568) := determined ω h .neptune_L
  refine ⟨?_, ?_⟩
  · linear_combination r_neptune_geo + (-1 : ℚ) * r_neptune_L
  · linear_combination r_neptune_geo

/-- `sun_geo` (Soleil vrai : aiguille géocentrique (= Terre vraie + 180°)) : ω sun_geo = (1)·ω earth_true en moyenne (renvoi 1:1) ; 589/215136 tour par tour de J. -/
theorem mean_sun_geo (ω : Shaft → ℚ) (h : Kinematics ω) :
    ω .sun_geo = ω .earth_true ∧ ω .sun_geo = (589 / 215136) * ω .J := by
  have r_sun_geo : ω .sun_geo = ω .J * (589 / 215136) := determined ω h .sun_geo
  have r_earth_true : ω .earth_true = ω .J * (589 / 215136) := determined ω h .earth_true
  refine ⟨?_, ?_⟩
  · linear_combination r_sun_geo + (-1 : ℚ) * r_earth_true
  · linear_combination r_sun_geo

/-- `mercury_E` (Mercure : arbre de l’anomalie excentrique E (résolveur)) : ω mercury_E = (1)·ω mercury_L en moyenne (boucle M = E − e sin E : un tour par tour) ; 102638/9028989 tour par tour de J. -/
theorem mean_mercury_E (ω : Shaft → ℚ) (h : Kinematics ω) :
    ω .mercury_E = ω .mercury_L ∧ ω .mercury_E = (102638 / 9028989) * ω .J := by
  have r_mercury_E : ω .mercury_E = ω .J * (102638 / 9028989) := determined ω h .mercury_E
  have r_mercury_L : ω .mercury_L = ω .J * (102638 / 9028989) := determined ω h .mercury_L
  refine ⟨?_, ?_⟩
  · linear_combination r_mercury_E + (-1 : ℚ) * r_mercury_L
  · linear_combination r_mercury_E

/-- `moon_true` (Lune vraie : aiguille (sortie de la cascade à 5 étages)) : ω moon_true = (1)·ω moon_L en moyenne (cascade réduction → équation annuelle → évection → anomalie (équant) → variation : un tour par tour) ; 4598/125625 tour par tour de J. -/
theorem mean_moon_true (ω : Shaft → ℚ) (h : Kinematics ω) :
    ω .moon_true = ω .moon_L ∧ ω .moon_true = (4598 / 125625) * ω .J := by
  have r_moon_true : ω .moon_true = ω .J * (4598 / 125625) := determined ω h .moon_true
  have r_moon_L : ω .moon_L = ω .J * (4598 / 125625) := determined ω h .moon_L
  refine ⟨?_, ?_⟩
  · linear_combination r_moon_true + (-1 : ℚ) * r_moon_L
  · linear_combination r_moon_true

/-- `moon_phase` (Boule de phase (rotation relative à l’aiguille de la Lune = Lune vraie − Soleil vrai)) : ω moon_phase = (1)·ω moon_true + (-1)·ω sun_geo en moyenne (couronne 1:1 (48:48) menée par le tube du Soleil vrai) ; 305067401/9008820000 tour par tour de J. -/
theorem mean_moon_phase (ω : Shaft → ℚ) (h : Kinematics ω) :
    ω .moon_phase = ω .moon_true - ω .sun_geo ∧ ω .moon_phase = (305067401 / 9008820000) * ω .J := by
  have r_moon_phase : ω .moon_phase = ω .J * (305067401 / 9008820000) := determined ω h .moon_phase
  have r_moon_true : ω .moon_true = ω .J * (4598 / 125625) := determined ω h .moon_true
  have r_sun_geo : ω .sun_geo = ω .J * (589 / 215136) := determined ω h .sun_geo
  refine ⟨?_, ?_⟩
  · linear_combination r_moon_phase + (-1 : ℚ) * r_moon_true + r_sun_geo
  · linear_combination r_moon_phase

/-- Précision de `Y` (Terre (barycentre Terre-Lune)) : dérive 0.000375°/siècle < 1/1000 et erreur relative |machine − cible| / |cible| ≤ 1.1e-08 (valeur -1.04e-08) ; cible 8999843216329/3287250000000000 tr/j. -/
theorem bound_Y (ω : Shaft → ℚ) (h : Kinematics ω) (hJ : ω .J = 1) :
    |ω .Y - (8999843216329 / 3287250000000000)| * 360 * 36525 < 1 / 1000 ∧
    |ω .Y - (8999843216329 / 3287250000000000)| ≤ (11 / 1000000000) * (8999843216329 / 3287250000000000) := by
  rw [determined ω h .Y, hJ]
  refine ⟨?_, ?_⟩ <;> norm_num [rate, abs_of_neg]

/-- Précision de `mercury_L` (Mercure) : dérive 0.00818°/siècle < 1/100 et erreur relative |machine − cible| / |cible| ≤ 5.5e-08 (valeur -5.48e-08) ; cible 3736816868147/328725000000000 tr/j. -/
theorem bound_mercury_L (ω : Shaft → ℚ) (h : Kinematics ω) (hJ : ω .J = 1) :
    |ω .mercury_L - (3736816868147 / 328725000000000)| * 360 * 36525 < 1 / 100 ∧
    |ω .mercury_L - (3736816868147 / 328725000000000)| ≤ (11 / 200000000) * (3736816868147 / 328725000000000) := by
  rw [determined ω h .mercury_L, hJ]
  refine ⟨?_, ?_⟩ <;> norm_num [rate, abs_of_neg]

/-- Précision de `venus_L` (Vénus) : dérive 0.000864°/siècle < 1/1000 et erreur relative |machine − cible| / |cible| ≤ 1.5e-08 (valeur -1.48e-08) ; cible 9752969205169/2191500000000000 tr/j. -/
theorem bound_venus_L (ω : Shaft → ℚ) (h : Kinematics ω) (hJ : ω .J = 1) :
    |ω .venus_L - (9752969205169 / 2191500000000000)| * 360 * 36525 < 1 / 1000 ∧
    |ω .venus_L - (9752969205169 / 2191500000000000)| ≤ (3 / 200000000) * (9752969205169 / 2191500000000000) := by
  rw [determined ω h .venus_L, hJ]
  refine ⟨?_, ?_⟩ <;> norm_num [rate, abs_of_neg]

/-- Précision de `mars_L` (Mars) : dérive 0.00603°/siècle < 1/100 et erreur relative |machine − cible| / |cible| ≤ 3.2e-07 (valeur 3.15e-07) ; cible 708900075697/487000000000000 tr/j. -/
theorem bound_mars_L (ω : Shaft → ℚ) (h : Kinematics ω) (hJ : ω .J = 1) :
    |ω .mars_L - (708900075697 / 487000000000000)| * 360 * 36525 < 1 / 100 ∧
    |ω .mars_L - (708900075697 / 487000000000000)| ≤ (1 / 3125000) * (708900075697 / 487000000000000) := by
  rw [determined ω h .mars_L, hJ]
  refine ⟨?_, ?_⟩ <;> norm_num [rate, abs_of_nonneg]

/-- Précision de `jupiter_L` (Jupiter) : dérive 0.00221°/siècle < 1/100 et erreur relative |machine − cible| / |cible| ≤ 7.3e-07 (valeur -7.3e-07) ; cible 758680690403/3287250000000000 tr/j. -/
theorem bound_jupiter_L (ω : Shaft → ℚ) (h : Kinematics ω) (hJ : ω .J = 1) :
    |ω .jupiter_L - (758680690403 / 3287250000000000)| * 360 * 36525 < 1 / 100 ∧
    |ω .jupiter_L - (758680690403 / 3287250000000000)| ≤ (73 / 100000000) * (758680690403 / 3287250000000000) := by
  rw [determined ω h .jupiter_L, hJ]
  refine ⟨?_, ?_⟩ <;> norm_num [rate, abs_of_neg]

/-- Précision de `saturn_L` (Saturne) : dérive 0.00403°/siècle < 1/100 et erreur relative |machine − cible| / |cible| ≤ 3.3e-06 (valeur 3.3e-06) ; cible 1528217782691/16436250000000000 tr/j. -/
theorem bound_saturn_L (ω : Shaft → ℚ) (h : Kinematics ω) (hJ : ω .J = 1) :
    |ω .saturn_L - (1528217782691 / 16436250000000000)| * 360 * 36525 < 1 / 100 ∧
    |ω .saturn_L - (1528217782691 / 16436250000000000)| ≤ (33 / 10000000) * (1528217782691 / 16436250000000000) := by
  rw [determined ω h .saturn_L, hJ]
  refine ⟨?_, ?_⟩ <;> norm_num [rate, abs_of_nonneg]

/-- Précision de `uranus_L` (Uranus) : dérive 0.00525°/siècle < 1/100 et erreur relative |machine − cible| / |cible| ≤ 1.3e-05 (valeur 1.22e-05) ; cible 10713967712879/328725000000000000 tr/j. -/
theorem bound_uranus_L (ω : Shaft → ℚ) (h : Kinematics ω) (hJ : ω .J = 1) :
    |ω .uranus_L - (10713967712879 / 328725000000000000)| * 360 * 36525 < 1 / 100 ∧
    |ω .uranus_L - (10713967712879 / 328725000000000000)| ≤ (13 / 1000000) * (10713967712879 / 328725000000000000) := by
  rw [determined ω h .uranus_L, hJ]
  refine ⟨?_, ?_⟩ <;> norm_num [rate, abs_of_nonneg]

/-- Précision de `neptune_L` (Neptune) : dérive 0.00894°/siècle < 1/100 et erreur relative |machine − cible| / |cible| ≤ 4.1e-05 (valeur -4.09e-05) ; cible 21842764007231/1314900000000000000 tr/j. -/
theorem bound_neptune_L (ω : Shaft → ℚ) (h : Kinematics ω) (hJ : ω .J = 1) :
    |ω .neptune_L - (21842764007231 / 1314900000000000000)| * 360 * 36525 < 1 / 100 ∧
    |ω .neptune_L - (21842764007231 / 1314900000000000000)| ≤ (41 / 1000000) * (21842764007231 / 1314900000000000000) := by
  rw [determined ω h .neptune_L, hJ]
  refine ⟨?_, ?_⟩ <;> norm_num [rate, abs_of_neg]

/-- Précision de `moon_L` (Lune : longitude moyenne) : dérive 0.00112°/siècle < 1/100 et erreur relative |machine − cible| / |cible| ≤ 2.4e-09 (valeur 2.33e-09) ; cible 50719519769515700168049329/1385741558474838000000000000 tr/j. -/
theorem bound_moon_L (ω : Shaft → ℚ) (h : Kinematics ω) (hJ : ω .J = 1) :
    |ω .moon_L - (50719519769515700168049329 / 1385741558474838000000000000)| * 360 * 36525 < 1 / 100 ∧
    |ω .moon_L - (50719519769515700168049329 / 1385741558474838000000000000)| ≤ (3 / 1250000000) * (50719519769515700168049329 / 1385741558474838000000000000) := by
  rw [determined ω h .moon_L, hJ]
  refine ⟨?_, ?_⟩ <;> norm_num [rate, abs_of_nonneg]

/-- Précision de `moon_perigee` (Lune : périgée moyen ϖ) : dérive 0.00667°/siècle < 1/100 et erreur relative |machine − cible| / |cible| ≤ 1.7e-06 (valeur 1.64e-06) ; cible 12373063762876851123233/39997336852206000000000000 tr/j. -/
theorem bound_moon_perigee (ω : Shaft → ℚ) (h : Kinematics ω) (hJ : ω .J = 1) :
    |ω .moon_perigee - (12373063762876851123233 / 39997336852206000000000000)| * 360 * 36525 < 1 / 100 ∧
    |ω .moon_perigee - (12373063762876851123233 / 39997336852206000000000000)| ≤ (17 / 10000000) * (12373063762876851123233 / 39997336852206000000000000) := by
  rw [determined ω h .moon_perigee, hJ]
  refine ⟨?_, ?_⟩ <;> norm_num [rate, abs_of_nonneg]

/-- Précision de `moon_node` (Lune : nœud ascendant moyen Ω) : dérive 0.00132°/siècle < 1/100 et erreur relative |machine − cible| / |cible| ≤ 6.8e-07 (valeur 6.8e-07) ; cible -41131596119932372523431/279426805254558000000000000 tr/j. -/
theorem bound_moon_node (ω : Shaft → ℚ) (h : Kinematics ω) (hJ : ω .J = 1) :
    |ω .moon_node - (-41131596119932372523431 / 279426805254558000000000000)| * 360 * 36525 < 1 / 100 ∧
    |ω .moon_node - (-41131596119932372523431 / 279426805254558000000000000)| ≤ (17 / 25000000) * (41131596119932372523431 / 279426805254558000000000000) := by
  rw [determined ω h .moon_node, hJ]
  refine ⟨?_, ?_⟩ <;> norm_num [rate, abs_of_neg]

/-- Précision de `evection_carrier` (Porte-satellite de l’évection 2λ☉ − ϖ) : dérive 0.00742°/siècle < 1/100 et erreur relative |machine − cible| / |cible| ≤ 1.1e-07 (valeur -1.09e-07) ; cible 8265464052038478926311/1599893474088240000000000 tr/j. -/
theorem bound_evection_carrier (ω : Shaft → ℚ) (h : Kinematics ω) (hJ : ω .J = 1) :
    |ω .evection_carrier - (8265464052038478926311 / 1599893474088240000000000)| * 360 * 36525 < 1 / 100 ∧
    |ω .evection_carrier - (8265464052038478926311 / 1599893474088240000000000)| ≤ (11 / 100000000) * (8265464052038478926311 / 1599893474088240000000000) := by
  rw [determined ω h .evection_carrier, hJ]
  refine ⟨?_, ?_⟩ <;> norm_num [rate, abs_of_neg]

/-- Précision de `precession_ring` (Anneau du zodiaque tropique (précession, sens rétrograde)) : dérive 7.94e-07°/siècle < 1/1000000 et erreur relative |machine − cible| / |cible| ≤ 5.7e-07 (valeur -5.68e-07) ; cible -8383169383/78894000000000000 tr/j. -/
theorem bound_precession_ring (ω : Shaft → ℚ) (h : Kinematics ω) (hJ : ω .J = 1) :
    |ω .precession_ring - (-8383169383 / 78894000000000000)| * 360 * 36525 < 1 / 1000000 ∧
    |ω .precession_ring - (-8383169383 / 78894000000000000)| ≤ (57 / 100000000) * (8383169383 / 78894000000000000) := by
  rw [determined ω h .precession_ring, hJ]
  refine ⟨?_, ?_⟩ <;> norm_num [rate, abs_of_nonneg]

/-- Précision de `saros` (Saros) : dérive 0.000988°/siècle < 1/1000 et erreur relative |machine − cible| / |cible| ≤ 5e-07 (valeur 4.95e-07) ; cible 2748124722848952177853/18097284392579034000000000 tr/j. -/
theorem bound_saros (ω : Shaft → ℚ) (h : Kinematics ω) (hJ : ω .J = 1) :
    |ω .saros - (2748124722848952177853 / 18097284392579034000000000)| * 360 * 36525 < 1 / 1000 ∧
    |ω .saros - (2748124722848952177853 / 18097284392579034000000000)| ≤ (1 / 2000000) * (2748124722848952177853 / 18097284392579034000000000) := by
  rw [determined ω h .saros, hJ]
  refine ⟨?_, ?_⟩ <;> norm_num [rate, abs_of_nonneg]

/-- Précision de `exeligmos` (Exeligmos (3 Saros)) : dérive 0.000329°/siècle < 1/1000 et erreur relative |machine − cible| / |cible| ≤ 5e-07 (valeur 4.95e-07) ; cible 2748124722848952177853/54291853177737102000000000 tr/j. -/
theorem bound_exeligmos (ω : Shaft → ℚ) (h : Kinematics ω) (hJ : ω .J = 1) :
    |ω .exeligmos - (2748124722848952177853 / 54291853177737102000000000)| * 360 * 36525 < 1 / 1000 ∧
    |ω .exeligmos - (2748124722848952177853 / 54291853177737102000000000)| ≤ (1 / 2000000) * (2748124722848952177853 / 54291853177737102000000000) := by
  rw [determined ω h .exeligmos, hJ]
  refine ⟨?_, ?_⟩ <;> norm_num [rate, abs_of_nonneg]

/-- Précision de `ganymede` (Ganymède) : dérive 0.00023°/siècle < 1/1000 et erreur relative |machine − cible| / |cible| ≤ 1.3e-10 (valeur -1.25e-10) ; cible 50317609207/360000000000 tr/j. -/
theorem bound_ganymede (ω : Shaft → ℚ) (h : Kinematics ω) (hJ : ω .J = 1) :
    |ω .ganymede - (50317609207 / 360000000000)| * 360 * 36525 < 1 / 1000 ∧
    |ω .ganymede - (50317609207 / 360000000000)| ≤ (13 / 100000000000) * (50317609207 / 360000000000) := by
  rw [determined ω h .ganymede, hJ]
  refine ⟨?_, ?_⟩ <;> norm_num [rate, abs_of_neg]

/-- Précision de `nu` (Arbre ν (la ligne des conjonctions tourne à −ν)) : dérive 0.000632°/siècle < 1/1000 et erreur relative |machine − cible| / |cible| ≤ 2.4e-08 (valeur -2.34e-08) ; cible 1479012641/720000000000 tr/j. -/
theorem bound_nu (ω : Shaft → ℚ) (h : Kinematics ω) (hJ : ω .J = 1) :
    |ω .nu - (1479012641 / 720000000000)| * 360 * 36525 < 1 / 1000 ∧
    |ω .nu - (1479012641 / 720000000000)| ≤ (3 / 125000000) * (1479012641 / 720000000000) := by
  rw [determined ω h .nu, hJ]
  refine ⟨?_, ?_⟩ <;> norm_num [rate, abs_of_neg]

/-- Précision de `europa` (Europe) : dérive 0.00111°/siècle < 1/100 et erreur relative |machine − cible| / |cible| ≤ 3e-10 (valeur -3e-10) ; cible 20274944947/72000000000 tr/j. -/
theorem bound_europa (ω : Shaft → ℚ) (h : Kinematics ω) (hJ : ω .J = 1) :
    |ω .europa - (20274944947 / 72000000000)| * 360 * 36525 < 1 / 100 ∧
    |ω .europa - (20274944947 / 72000000000)| ≤ (3 / 10000000000) * (20274944947 / 72000000000) := by
  rw [determined ω h .europa, hJ]
  refine ⟨?_, ?_⟩ <;> norm_num [rate, abs_of_neg]

/-- Précision de `io` (Io) : dérive 0.00283°/siècle < 1/100 et erreur relative |machine − cible| / |cible| ≤ 3.9e-10 (valeur -3.81e-10) ; cible 6782965193/12000000000 tr/j. -/
theorem bound_io (ω : Shaft → ℚ) (h : Kinematics ω) (hJ : ω .J = 1) :
    |ω .io - (6782965193 / 12000000000)| * 360 * 36525 < 1 / 100 ∧
    |ω .io - (6782965193 / 12000000000)| ≤ (39 / 100000000000) * (6782965193 / 12000000000) := by
  rw [determined ω h .io, hJ]
  refine ⟨?_, ?_⟩ <;> norm_num [rate, abs_of_neg]

/-- Précision de `callisto` (Callisto) : dérive 0.00252°/siècle < 1/100 et erreur relative |machine − cible| / |cible| ≤ 3.2e-09 (valeur 3.2e-09) ; cible 7190357059/120000000000 tr/j. -/
theorem bound_callisto (ω : Shaft → ℚ) (h : Kinematics ω) (hJ : ω .J = 1) :
    |ω .callisto - (7190357059 / 120000000000)| * 360 * 36525 < 1 / 100 ∧
    |ω .callisto - (7190357059 / 120000000000)| ≤ (1 / 312500000) * (7190357059 / 120000000000) := by
  rw [determined ω h .callisto, hJ]
  refine ⟨?_, ?_⟩ <;> norm_num [rate, abs_of_nonneg]

/-- Précision de `synodic` (Lune : élongation moyenne D) : dérive 0.00157°/siècle < 1/100 et erreur relative |machine − cible| / |cible| ≤ 3.6e-09 (valeur 3.52e-09) ; cible 2748124722848952177853/81153741670758000000000 tr/j. -/
theorem bound_synodic (ω : Shaft → ℚ) (h : Kinematics ω) (hJ : ω .J = 1) :
    |ω .synodic - (2748124722848952177853 / 81153741670758000000000)| * 360 * 36525 < 1 / 100 ∧
    |ω .synodic - (2748124722848952177853 / 81153741670758000000000)| ≤ (9 / 2500000000) * (2748124722848952177853 / 81153741670758000000000) := by
  rw [determined ω h .synodic, hJ]
  refine ⟨?_, ?_⟩ <;> norm_num [rate, abs_of_nonneg]

/-- Précision de `saros_223` (Saros) : dérive 7.04e-06°/siècle < 1/100000 et erreur relative |machine − cible| / |cible| ≤ 3.6e-09 (valeur 3.52e-09) ; cible 2748124722848952177853/18097284392579034000000000 tr/j. -/
theorem bound_saros_223 (ω : Shaft → ℚ) (h : Kinematics ω) (hJ : ω .J = 1) :
    |ω .saros_223 - (2748124722848952177853 / 18097284392579034000000000)| * 360 * 36525 < 1 / 100000 ∧
    |ω .saros_223 - (2748124722848952177853 / 18097284392579034000000000)| ≤ (9 / 2500000000) * (2748124722848952177853 / 18097284392579034000000000) := by
  rw [determined ω h .saros_223, hJ]
  refine ⟨?_, ?_⟩ <;> norm_num [rate, abs_of_nonneg]

/-- Précision de `mars_apsides` (Ligne des apsides de Mars (option)) : dérive 0.00066°/siècle < 1/1000 et erreur relative |machine − cible| / |cible| ≤ 0.0015 (valeur 0.00149) ; cible 1479672137/43830000000000000 tr/j. -/
theorem bound_mars_apsides (ω : Shaft → ℚ) (h : Kinematics ω) (hJ : ω .J = 1) :
    |ω .mars_apsides - (1479672137 / 43830000000000000)| * 360 * 36525 < 1 / 1000 ∧
    |ω .mars_apsides - (1479672137 / 43830000000000000)| ≤ (3 / 2000) * (1479672137 / 43830000000000000) := by
  rw [determined ω h .mars_apsides, hJ]
  refine ⟨?_, ?_⟩ <;> norm_num [rate, abs_of_nonneg]

/-- Précision de `moon_D` (Lune : élongation moyenne D) : dérive 0.00157°/siècle < 1/100 et erreur relative |machine − cible| / |cible| ≤ 3.6e-09 (valeur 3.52e-09) ; cible 2748124722848952177853/81153741670758000000000 tr/j. -/
theorem bound_moon_D (ω : Shaft → ℚ) (h : Kinematics ω) (hJ : ω .J = 1) :
    |ω .moon_L - ω .Y - (2748124722848952177853 / 81153741670758000000000)| * 360 * 36525 < 1 / 100 ∧
    |ω .moon_L - ω .Y - (2748124722848952177853 / 81153741670758000000000)| ≤ (9 / 2500000000) * (2748124722848952177853 / 81153741670758000000000) := by
  rw [determined ω h .moon_L, determined ω h .Y, hJ]
  refine ⟨?_, ?_⟩ <;> norm_num [rate, abs_of_nonneg]

/-- Précision de `moon_F` (Lune : argument de latitude F) : dérive 0.00243°/siècle < 1/100 et erreur relative |machine − cible| / |cible| ≤ 5.1e-09 (valeur 5.04e-09) ; cible 367720484618036149891/10006491101985000000000 tr/j. -/
theorem bound_moon_F (ω : Shaft → ℚ) (h : Kinematics ω) (hJ : ω .J = 1) :
    |ω .moon_L - ω .moon_node - (367720484618036149891 / 10006491101985000000000)| * 360 * 36525 < 1 / 100 ∧
    |ω .moon_L - ω .moon_node - (367720484618036149891 / 10006491101985000000000)| ≤ (51 / 10000000000) * (367720484618036149891 / 10006491101985000000000) := by
  rw [determined ω h .moon_L, determined ω h .moon_node, hJ]
  refine ⟨?_, ?_⟩ <;> norm_num [rate, abs_of_nonneg]

/-- Précision de `moon_Mp` (Lune : anomalie moyenne M′) : dérive 0.00555°/siècle < 1/100 et erreur relative |machine − cible| / |cible| ≤ 1.2e-08 (valeur -1.16e-08) ; cible 203885543841116306153/5617974285630000000000 tr/j. -/
theorem bound_moon_Mp (ω : Shaft → ℚ) (h : Kinematics ω) (hJ : ω .J = 1) :
    |ω .moon_L - ω .moon_perigee - (203885543841116306153 / 5617974285630000000000)| * 360 * 36525 < 1 / 100 ∧
    |ω .moon_L - ω .moon_perigee - (203885543841116306153 / 5617974285630000000000)| ≤ (3 / 250000000) * (203885543841116306153 / 5617974285630000000000) := by
  rw [determined ω h .moon_L, determined ω h .moon_perigee, hJ]
  refine ⟨?_, ?_⟩ <;> norm_num [rate, abs_of_neg]

end AnticythereV2
