-- GÉNÉRÉ par v2/tools/make_lean_v2.py depuis v2/spec/trains.json et v2/spec/architecture.json.
-- Ne pas éditer à la main : relancer le générateur.

import AnticythereV2.Kinematics

/-!
# Identités exactes et calendrier

Différentiels (évection, temps sidéral, Laplace des satellites de Jupiter, anneau des dates…) : chaque
identité de trains.json est vraie pour TOUTE famille de vitesses admissibles, et donne `rate_vs_J`.
Calendrier : les cames C4, C100, C400 des roues-programmes, lues le 28 février, font sauter le 29 février
exactement les années communes, pour toute année à partir de 2000 ; 400 années grégoriennes font un nombre
entier de semaines. Les prémisses du modèle (positions de l'anneau, périodes des cames, vitesse moyenne de
la croix de saut) sont prouvées depuis `Kinematics` (`calendar_gearing`, `skip_rate`).
-/

namespace AnticythereV2

/-- `evection_carrier` (Lune : porte-satellite de l’évection 2λ☉ − ϖ (différentiel, sans nouveau rapport approché)) : ω evection_carrier = (2)·ω Y + (-1)·ω moon_perigee ; 1502539/290836980 tour par tour de J. -/
theorem identity_evection_carrier (ω : Shaft → ℚ) (h : Kinematics ω) :
    ω .evection_carrier = 2 * ω .Y - ω .moon_perigee ∧ ω .evection_carrier = (1502539 / 290836980) * ω .J := by
  have r_evection_carrier : ω .evection_carrier = ω .J * (1502539 / 290836980) := determined ω h .evection_carrier
  have r_Y : ω .Y = ω .J * (589 / 215136) := determined ω h .Y
  have r_moon_perigee : ω .moon_perigee = ω .J * (359879 / 1163347920) := determined ω h .moon_perigee
  refine ⟨?_, ?_⟩
  · linear_combination r_evection_carrier + (-2 : ℚ) * r_Y + r_moon_perigee
  · linear_combination r_evection_carrier

/-- `sun_trop` (Soleil moyen tropique X = Y + p (différentiel)) : ω sun_trop = (1)·ω Y + (-1)·ω precession_ring ; 25041150643/9146084728032 tour par tour de J. -/
theorem identity_sun_trop (ω : Shaft → ℚ) (h : Kinematics ω) :
    ω .sun_trop = ω .Y - ω .precession_ring ∧ ω .sun_trop = (25041150643 / 9146084728032) * ω .J := by
  have r_sun_trop : ω .sun_trop = ω .J * (25041150643 / 9146084728032) := determined ω h .sun_trop
  have r_Y : ω .Y = ω .J * (589 / 215136) := determined ω h .Y
  have r_precession_ring : ω .precession_ring = ω .J * (-161975 / 1524347454672) := determined ω h .precession_ring
  refine ⟨?_, ?_⟩
  · linear_combination r_sun_trop + (-1 : ℚ) * r_Y + r_precession_ring
  · linear_combination r_sun_trop

/-- `stellar` (Rotation stellaire S = J + Y (différentiel ; mène le globe-tellurion)) : ω stellar = (1)·ω J + (1)·ω Y ; 215725/215136 tour par tour de J. -/
theorem identity_stellar (ω : Shaft → ℚ) (h : Kinematics ω) :
    ω .stellar = ω .J + ω .Y ∧ ω .stellar = (215725 / 215136) * ω .J := by
  have r_stellar : ω .stellar = ω .J * (215725 / 215136) := determined ω h .stellar
  have r_Y : ω .Y = ω .J * (589 / 215136) := determined ω h .Y
  refine ⟨?_, ?_⟩
  · linear_combination r_stellar + (-1 : ℚ) * r_Y
  · linear_combination r_stellar

/-- `gmst` (Temps sidéral moyen (TSMG) = J + X (différentiel)) : ω gmst = (1)·ω J + (1)·ω sun_trop ; 9171125878675/9146084728032 tour par tour de J. -/
theorem identity_gmst (ω : Shaft → ℚ) (h : Kinematics ω) :
    ω .gmst = ω .J + ω .sun_trop ∧ ω .gmst = (9171125878675 / 9146084728032) * ω .J := by
  have r_gmst : ω .gmst = ω .J * (9171125878675 / 9146084728032) := determined ω h .gmst
  have r_sun_trop : ω .sun_trop = ω .J * (25041150643 / 9146084728032) := determined ω h .sun_trop
  refine ⟨?_, ?_⟩
  · linear_combination r_gmst + (-1 : ℚ) * r_sun_trop
  · linear_combination r_gmst

/-- `lambda_trop` (Soleil vrai tropique λ + p (entrée du joint de Hooke)) : ω lambda_trop = (1)·ω earth_true + (-1)·ω precession_ring ; 25041150643/9146084728032 tour par tour de J. -/
theorem identity_lambda_trop (ω : Shaft → ℚ) (h : Kinematics ω) :
    ω .lambda_trop = ω .earth_true - ω .precession_ring ∧ ω .lambda_trop = (25041150643 / 9146084728032) * ω .J := by
  have r_lambda_trop : ω .lambda_trop = ω .J * (25041150643 / 9146084728032) := determined ω h .lambda_trop
  have r_earth_true : ω .earth_true = ω .J * (589 / 215136) := determined ω h .earth_true
  have r_precession_ring : ω .precession_ring = ω .J * (-161975 / 1524347454672) := determined ω h .precession_ring
  refine ⟨?_, ?_⟩
  · linear_combination r_lambda_trop + (-1 : ℚ) * r_earth_true + r_precession_ring
  · linear_combination r_lambda_trop

/-- `eot` (Équation du temps EdT = X − α (différentiel ; vitesse moyenne nulle)) : ω eot = (1)·ω sun_trop + (-1)·ω alpha_sun ; 0 tour par tour de J. -/
theorem identity_eot (ω : Shaft → ℚ) (h : Kinematics ω) :
    ω .eot = ω .sun_trop - ω .alpha_sun ∧ ω .eot = 0 * ω .J := by
  have r_eot : ω .eot = ω .J * 0 := determined ω h .eot
  have r_sun_trop : ω .sun_trop = ω .J * (25041150643 / 9146084728032) := determined ω h .sun_trop
  have r_alpha_sun : ω .alpha_sun = ω .J * (25041150643 / 9146084728032) := determined ω h .alpha_sun
  refine ⟨?_, ?_⟩
  · linear_combination r_eot + (-1 : ℚ) * r_sun_trop + r_alpha_sun
  · linear_combination r_eot

/-- `cal_sum` (Anneau des dates (366 positions) = (croix principale + croix de saut)/61) : ω cal_sum = (1/61)·ω cal_cross_main + (1/61)·ω cal_cross_skip ; 400/146097 tour par tour de J. -/
theorem identity_cal_sum (ω : Shaft → ℚ) (h : Kinematics ω) :
    ω .cal_sum = 1 / 61 * ω .cal_cross_main + 1 / 61 * ω .cal_cross_skip ∧ ω .cal_sum = (400 / 146097) * ω .J := by
  have r_cal_sum : ω .cal_sum = ω .J * (400 / 146097) := determined ω h .cal_sum
  have r_cal_cross_main : ω .cal_cross_main = ω .J * (1 / 6) := determined ω h .cal_cross_main
  have r_cal_cross_skip : ω .cal_cross_skip = ω .J * (101 / 292194) := determined ω h .cal_cross_skip
  refine ⟨?_, ?_⟩
  · linear_combination r_cal_sum + (-1 / 61 : ℚ) * r_cal_cross_main + (-1 / 61 : ℚ) * r_cal_cross_skip
  · linear_combination r_cal_sum

/-- `annual_eq` (Lune : moteur de l’équation annuelle (3/31)(λ☉ vrai − λ☉ moyen) (vitesse moyenne nulle)) : ω annual_eq = (3/31)·ω earth_true + (-3/31)·ω Y ; 0 tour par tour de J. -/
theorem identity_annual_eq (ω : Shaft → ℚ) (h : Kinematics ω) :
    ω .annual_eq = 3 / 31 * ω .earth_true - 3 / 31 * ω .Y ∧ ω .annual_eq = 0 * ω .J := by
  have r_annual_eq : ω .annual_eq = ω .J * 0 := determined ω h .annual_eq
  have r_earth_true : ω .earth_true = ω .J * (589 / 215136) := determined ω h .earth_true
  have r_Y : ω .Y = ω .J * (589 / 215136) := determined ω h .Y
  refine ⟨?_, ?_⟩
  · linear_combination r_annual_eq + (-3 / 31 : ℚ) * r_earth_true + (3 / 31 : ℚ) * r_Y
  · linear_combination r_annual_eq

/-- `europa` (Europe = 2·Ganymède + ν (différentiel)) : ω europa = (2)·ω ganymede + (1)·ω nu ; 1004501316/3567166025 tour par tour de J. -/
theorem identity_europa (ω : Shaft → ℚ) (h : Kinematics ω) :
    ω .europa = 2 * ω .ganymede + ω .nu ∧ ω .europa = (1004501316 / 3567166025) * ω .J := by
  have r_europa : ω .europa = ω .J * (1004501316 / 3567166025) := determined ω h .europa
  have r_ganymede : ω .ganymede = ω .J * (9686 / 69299) := determined ω h .ganymede
  have r_nu : ω .nu = ω .J * (2432 / 1183925) := determined ω h .nu
  refine ⟨?_, ?_⟩
  · linear_combination r_europa + (-2 : ℚ) * r_ganymede + (-1 : ℚ) * r_nu
  · linear_combination r_europa

/-- `io` (Io = 2·Europe + ν (différentiel)) : ω io = (2)·ω europa + (1)·ω nu ; 2016330248/3567166025 tour par tour de J. -/
theorem identity_io (ω : Shaft → ℚ) (h : Kinematics ω) :
    ω .io = 2 * ω .europa + ω .nu ∧ ω .io = (2016330248 / 3567166025) * ω .J := by
  have r_io : ω .io = ω .J * (2016330248 / 3567166025) := determined ω h .io
  have r_europa : ω .europa = ω .J * (1004501316 / 3567166025) := determined ω h .europa
  have r_nu : ω .nu = ω .J * (2432 / 1183925) := determined ω h .nu
  refine ⟨?_, ?_⟩
  · linear_combination r_io + (-2 : ℚ) * r_europa + (-1 : ℚ) * r_nu
  · linear_combination r_io

/-- `synodic` (Variante : arbre synodique moyen D = L − Y (différentiel)) : ω synodic = (1)·ω moon_L + (-1)·ω Y ; 305067401/9008820000 tour par tour de J. -/
theorem identity_synodic (ω : Shaft → ℚ) (h : Kinematics ω) :
    ω .synodic = ω .moon_L - ω .Y ∧ ω .synodic = (305067401 / 9008820000) * ω .J := by
  have r_synodic : ω .synodic = ω .J * (305067401 / 9008820000) := determined ω h .synodic
  have r_moon_L : ω .moon_L = ω .J * (4598 / 125625) := determined ω h .moon_L
  have r_Y : ω .Y = ω .J * (589 / 215136) := determined ω h .Y
  refine ⟨?_, ?_⟩
  · linear_combination r_synodic + (-1 : ℚ) * r_moon_L + r_Y
  · linear_combination r_synodic

/-- ω io − 3 ω europa + 2 ω ganymede = 0 (Laplace, exact par construction). -/
theorem identity_io_laplace (ω : Shaft → ℚ) (h : Kinematics ω) :
    ω .io - 3 * ω .europa + 2 * ω .ganymede = 0 := by
  have r_io : ω .io = ω .J * (2016330248 / 3567166025) := determined ω h .io
  have r_europa : ω .europa = ω .J * (1004501316 / 3567166025) := determined ω h .europa
  have r_ganymede : ω .ganymede = ω .J * (9686 / 69299) := determined ω h .ganymede
  linear_combination r_io + (-3 : ℚ) * r_europa + (2 : ℚ) * r_ganymede

/-- vitesse moyenne de l’équation du temps = 0. -/
theorem identity_eot_mean_zero (ω : Shaft → ℚ) (h : Kinematics ω) :
    ω .eot = 0 := by
  have r_eot : ω .eot = ω .J * 0 := determined ω h .eot
  linear_combination r_eot

/-- ω gmst = ω J + ω Y − ω precession_ring. -/
theorem identity_gmst_sum (ω : Shaft → ℚ) (h : Kinematics ω) :
    ω .gmst = ω .J + ω .Y - ω .precession_ring := by
  have r_gmst : ω .gmst = ω .J * (9171125878675 / 9146084728032) := determined ω h .gmst
  have r_Y : ω .Y = ω .J * (589 / 215136) := determined ω h .Y
  have r_precession_ring : ω .precession_ring = ω .J * (-161975 / 1524347454672) := determined ω h .precession_ring
  linear_combination r_gmst + (-1 : ℚ) * r_Y + r_precession_ring

/-- Année bissextile du calendrier grégorien (règle civile). -/
def leap (y : ℕ) : Bool := y % 4 == 0 && (y % 100 != 0 || y % 400 == 0)

/-- Came C4 sur `cal_prog4` (1/4 tour par tour de l'anneau des dates) : à la lecture du 28 février de l'année 2000 + n (anneau à n + 58/366 tours), elle est à (366 * n + 58)/1464 de tour ; levée sur [241/1464, 1339/1464] (arc `C4` de `gregorian_simulation`). -/
def camC4 (n : ℕ) : Bool := decide (241 ≤ (366 * n + 58) % 1464) && decide ((366 * n + 58) % 1464 ≤ 1339)

/-- Came C100 sur `cal_prog100` (1/100 tour par tour de l'anneau des dates) : à la lecture du 28 février de l'année 2000 + n (anneau à n + 58/366 tours), elle est à (366 * n + 58)/36600 de tour ; levée sur [36475/36600, 241/36600] (arc `C100` de `gregorian_simulation`). -/
def camC100 (n : ℕ) : Bool := decide (36475 ≤ (366 * n + 58) % 36600) || decide ((366 * n + 58) % 36600 ≤ 241)

/-- Came C400 sur `cal_prog400` (1/400 tour par tour de l'anneau des dates) : à la lecture du 28 février de l'année 2000 + n (anneau à n + 58/366 tours), elle est à (366 * n + 58)/146400 de tour ; levée sur [18358/146400, 128158/146400] (arc `C400` de `gregorian_simulation`). -/
def camC400 (n : ℕ) : Bool := decide (18358 ≤ (366 * n + 58) % 146400) && decide ((366 * n + 58) % 146400 ≤ 128158)

/-- La croix de saut avance (on saute le 29 février) si C4 ∨ (C100 ∧ C400). -/
def skipFeb29 (n : ℕ) : Bool := camC4 n || (camC100 n && camC400 n)

/-- Les 400 années 2000…2399 : la croix de saut avance exactement les années communes. -/
theorem calendar_400 : ∀ n < 400, skipFeb29 n = !leap (2000 + n) := by
  decide +kernel

/-- En 400 ans la croix de saut fait 303 pas pendant 146097 jours : c'est le `mean_steps_per_day` = 101/48699 de `cal_cross_skip` utilisé dans `Kinematics`. -/
theorem skips_400 : ((List.range 400).filter skipFeb29).length = 303 ∧
    400 * 365 + ((List.range 400).filter (fun n => leap (2000 + n))).length = 146097 := by
  decide +kernel

/-- Lien Lean entre les cames et `Kinematics` : les 303 pas comptés sur les cames en 400 ans, divisés par les 146097 jours, sont la vitesse moyenne de la croix de saut `cal_cross_skip` dans `Kinematics` (6 pas par tour). -/
theorem skip_rate (ω : Shaft → ℚ) (h : Kinematics ω) :
    (((List.range 400).filter skipFeb29).length : ℚ) * ω .J =
    ((400 * 365 + ((List.range 400).filter (fun n => leap (2000 + n))).length : ℕ) : ℚ) *
      (6 * ω .cal_cross_skip) := by
  rw [skips_400.1, skips_400.2]
  push_cast
  linear_combination (-146097 : ℚ) * h.cal_cross_skip

/-- Les trois cames reviennent à la même position tous les 400 ans (366 · 400 est un multiple des trois périodes). -/
theorem skip_periodic (n : ℕ) : skipFeb29 (n + 400) = skipFeb29 n := by
  have hC4 : (366 * (n + 400) + 58) % 1464 = (366 * n + 58) % 1464 := by
    rw [show 366 * (n + 400) + 58 = 366 * n + 58 + 100 * 1464 by ring, Nat.add_mul_mod_self_right]
  have hC100 : (366 * (n + 400) + 58) % 36600 = (366 * n + 58) % 36600 := by
    rw [show 366 * (n + 400) + 58 = 366 * n + 58 + 4 * 36600 by ring, Nat.add_mul_mod_self_right]
  have hC400 : (366 * (n + 400) + 58) % 146400 = (366 * n + 58) % 146400 := by
    rw [show 366 * (n + 400) + 58 = 366 * n + 58 + 1 * 146400 by ring, Nat.add_mul_mod_self_right]
  simp only [skipFeb29, camC4, camC100, camC400, hC4, hC100, hC400]

/-- La règle grégorienne est périodique de 400 ans. -/
theorem leap_periodic (n : ℕ) : leap (2000 + (n + 400)) = leap (2000 + n) := by
  have h4 : (2000 + (n + 400)) % 4 = (2000 + n) % 4 := by
    rw [show 2000 + (n + 400) = 2000 + n + 100 * 4 by ring, Nat.add_mul_mod_self_right]
  have h100 : (2000 + (n + 400)) % 100 = (2000 + n) % 100 := by
    rw [show 2000 + (n + 400) = 2000 + n + 4 * 100 by ring, Nat.add_mul_mod_self_right]
  have h400 : (2000 + (n + 400)) % 400 = (2000 + n) % 400 := by
    rw [show 2000 + (n + 400) = 2000 + n + 1 * 400 by ring, Nat.add_mul_mod_self_right]
  simp only [leap, h4, h100, h400]

/-- **Calendrier** (pour tout n : saute(n) ↔ ¬ bissextile(2000 + n) (400 cas par decide + périodicité de 400 ans des trois cames)) : pour TOUT n, la machine saute le 29 février l'année 2000 + n si et seulement si elle n'est pas bissextile (400 cas par `decide`, puis périodicité de 400 ans des trois cames). -/
theorem calendar (n : ℕ) : skipFeb29 n = true ↔ ¬ leap (2000 + n) = true := by
  have key : skipFeb29 n = !leap (2000 + n) := by
    induction n using Nat.strong_induction_on with
    | _ n ih =>
      rcases Nat.lt_or_ge n 400 with hn | hn
      · exact calendar_400 n hn
      · obtain ⟨k, rfl⟩ := Nat.exists_eq_add_of_le' hn
        rw [skip_periodic, leap_periodic]
        exact ih k (Nat.lt_add_of_pos_right (by norm_num))
  rw [key]
  cases leap (2000 + n) <;> decide

/-- Prémisses du modèle des cames, tirées des dents (`Kinematics`) : un pas de l'une ou l'autre croix (6 fentes) avance l'anneau des dates d'une de ses 366 positions ; les cames C4, C100, C400 tournent de 1/1464, 1/36600, 1/146400 de tour par position (les modules des définitions `cam*`) ; l'anneau fait 400 tours en 146097 jours. -/
theorem calendar_gearing (ω : Shaft → ℚ) (h : Kinematics ω) :
    366 * ω .cal_sum = 6 * ω .cal_cross_main + 6 * ω .cal_cross_skip ∧
    1464 * ω .cal_prog4 = 366 * ω .cal_sum ∧
    36600 * ω .cal_prog100 = 366 * ω .cal_sum ∧
    146400 * ω .cal_prog400 = 366 * ω .cal_sum ∧
    146097 * ω .cal_sum = 400 * ω .J := by
  have r_cal_sum : ω .cal_sum = ω .J * (400 / 146097) := determined ω h .cal_sum
  have r_cal_cross_main : ω .cal_cross_main = ω .J * (1 / 6) := determined ω h .cal_cross_main
  have r_cal_cross_skip : ω .cal_cross_skip = ω .J * (101 / 292194) := determined ω h .cal_cross_skip
  have r_cal_prog4 : ω .cal_prog4 = ω .J * (100 / 146097) := determined ω h .cal_prog4
  have r_cal_prog100 : ω .cal_prog100 = ω .J * (4 / 146097) := determined ω h .cal_prog100
  have r_cal_prog400 : ω .cal_prog400 = ω .J * (1 / 146097) := determined ω h .cal_prog400
  refine ⟨?_, ?_, ?_, ?_, ?_⟩
  · linear_combination (366 : ℚ) * r_cal_sum + (-6 : ℚ) * r_cal_cross_main + (-6 : ℚ) * r_cal_cross_skip
  · linear_combination (1464 : ℚ) * r_cal_prog4 + (-366 : ℚ) * r_cal_sum
  · linear_combination (36600 : ℚ) * r_cal_prog100 + (-366 : ℚ) * r_cal_sum
  · linear_combination (146400 : ℚ) * r_cal_prog400 + (-366 : ℚ) * r_cal_sum
  · linear_combination (146097 : ℚ) * r_cal_sum

/-- 146097 = 7 · 20871 : les 146097 jours de 400 années grégoriennes font 20871 semaines entières ; le jour de la semaine se répète donc tous les 400 ans. -/
theorem week_400 : (146097 : ℕ) = 7 * 20871 ∧
    400 * 365 + ((List.range 400).filter (fun n => leap (2000 + n))).length = 146097 := by
  decide +kernel

/-- La roue de la semaine `W` fait exactement 20871 tours en 146097 jours (tours de J). -/
theorem week_wheel (ω : Shaft → ℚ) (h : Kinematics ω) :
    146097 * ω .W = 20871 * ω .J := by
  have r_W : ω .W = ω .J * (1 / 7) := determined ω h .W
  linear_combination (146097 : ℚ) * r_W

end AnticythereV2
