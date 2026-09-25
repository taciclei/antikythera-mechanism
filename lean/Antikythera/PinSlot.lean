import Mathlib
import Antikythera.Kinematics

/-!
# The Antikythera Mechanism: the nonlinear couplings (pin-and-slot and followers)

The linear model `Antikythera.Kinematics` only speaks about MEAN rates. Two kinds of coupling of
the mechanism are not linear in the angles:

* the four **pin-and-slot** couplings (`lunar`, `saturn`, `jupiter`, `mars`). A pin at radius `r`
  on the driving gear engages a radial slot in a second gear whose axis is offset by `e` in the
  direction `β`. The spec law (angles relative to the carrier) is
  `θ₂ = θ₁ + atan2 (e sin (θ₁ - β)) (r - e cos (θ₁ - β))`, with `0 ≤ e < r`;
* the three **followers** (Mercury, Venus, true Sun). The spec law is
  `θ_F = θ_b + g₀ + atan2 (d sin λ) (i + d cos λ)`, with `0 ≤ d < i`.

`Kinematics` replaces them by the fields `pinslot_*` ("mean rate of the slot gear = mean rate of
the pin gear") and `follower_*` ("mean rate of the follower = rate of `b`"). This file shows that
these replacements are exact for mean rates, and it measures the periodic deviation that they leave
out.

## Main results

* `atan2_eq_arctan`: the spec's `atan2` (Mathlib's `Complex.arg`) equals `arctan (y / x)` when
  `x > 0`.
* `denom_pos`, `follower_denom_pos`: the denominators `r - e cos φ` and `i + d cos λ` are positive.
* `abs_tan_lag_le`, `tan_lag_arccos`: `|e sin φ / (r - e cos φ)| ≤ |e| / √(r² - e²)`, with
  equality at `cos φ = e / r`.
* `arctan_eq_arcsin_div`: `arctan (e / √(r² - e²)) = arcsin (e / r)`.
* `isGreatest_abs_lag`, `isGreatest_abs_followerLag`: the largest angular deviation of a
  pin-and-slot (resp. a follower) is exactly `arcsin (e / r)` (resp. `arcsin (d / i)`).
* `hasDerivAt_slotAngle`, `strictMono_slotAngle`, `speedRatio_mem`: relative to the carrier, the
  slot gear turns smoothly and strictly monotonically with the pin gear, at an instantaneous speed
  ratio between `r / (r + e)` and `r / (r - e)`.
* `abs_net_sub_le`, `tendsto_meanRate_sub`, `HasMeanRate.of_bounded_lag`: a bounded lag changes the
  net angle turned by at most `2 M` and does not change the mean rate.
* `pinSlot_hasMeanRate`, `follower_hasMeanRate`, and the seven instances `lunar_meanRate`, …,
  `trueSun_meanRate`: a slot gear has the mean rate of its pin gear, a follower that of `b`.
* `kinematics_nonlinear_fields`: formally, the spec laws imply the seven fields `pinslot_*` and
  `follower_*` of `Kinematics`.
* `lunar_amplitude_deg`: `6.579° < arcsin (1.1 / 9.6) < 6.581°` (Hipparchus' lunar anomaly), and
  bounds at 0.1° or better for Saturn, Jupiter, Mars, Mercury, Venus and the true Sun.

## Units and sign conventions

Angles are in radians and time `t` is in years. The spec laws use math-convention angles
(counterclockwise seen from the front), while `Kinematics` uses turns per year with clockwise
positive. A body with `Kinematics` rate `ω x` therefore has mean angular rate `-2π · ω x` in the
sense of `HasMeanRate`. The mean-rate theorems hold for every real rate, and equality of rates in
one unit is equality in the other (see `kinematics_nonlinear_fields`).
-/

namespace Antikythera.PinSlot

open Real Filter Topology Set

/-! ## 1. The two-argument arctangent -/

/-- The two-argument arctangent `atan2 y x` of the spec: the polar angle, in `(-π, π]`, of the
point `(x, y)`. It is Mathlib's `Complex.arg` of `x + y i`. -/
noncomputable def atan2 (y x : ℝ) : ℝ :=
  Complex.arg ⟨x, y⟩

/-- For a point in the right half-plane (`x > 0`), the spec's `atan2 y x` is the ordinary
`arctan (y / x)`. It is therefore a smooth function there, with values in `(-π/2, π/2)`. -/
theorem atan2_eq_arctan (y : ℝ) {x : ℝ} (hx : 0 < x) : atan2 y x = arctan (y / x) := by
  have h : |atan2 y x| < π / 2 := Complex.abs_arg_lt_pi_div_two_iff.2 (Or.inl hx)
  obtain ⟨h1, h2⟩ := abs_lt.1 h
  have htan : tan (atan2 y x) = y / x := Complex.tan_arg _
  rw [← htan, arctan_tan h1 h2]

/-- `|arctan x| = arctan |x|`, because `arctan` is odd and increasing. -/
theorem abs_arctan (x : ℝ) : |arctan x| = arctan |x| := by
  rcases le_total 0 x with hx | hx
  · rw [abs_of_nonneg hx, abs_of_nonneg (arctan_nonneg.2 hx)]
  · rw [abs_of_nonpos hx, arctan_neg, abs_of_nonpos (by simpa using arctan_strictMono.monotone hx)]

/-! ## 2. The pin-and-slot law -/

/-- The lag of a pin-and-slot coupling: the signed angle (counterclockwise positive, the spec's math
convention) by which the slot gear is ahead of the pin gear when the pin, measured from the
direction `β` of the axis offset, is at phase `φ`. `r` is the pin radius and `e` the offset between
the two axes. -/
noncomputable def lag (r e φ : ℝ) : ℝ :=
  atan2 (e * sin φ) (r - e * cos φ)

/-- The spec's pin-and-slot law: the angle of the slot gear when the pin gear is at angle `θ₁`, for
pin radius `r`, axis offset `e` and offset direction `β`. Both angles are relative to the carrier
(spec `conventions.pin_slot_formula`). -/
noncomputable def slotAngle (r e β θ₁ : ℝ) : ℝ :=
  θ₁ + atan2 (e * sin (θ₁ - β)) (r - e * cos (θ₁ - β))

/-- The slot gear is the pin gear plus the lag, evaluated at the pin's phase `θ₁ - β` from the
offset direction. -/
theorem slotAngle_eq (r e β θ₁ : ℝ) : slotAngle r e β θ₁ = θ₁ + lag r e (θ₁ - β) :=
  rfl

/-- The lag depends only on the pin's phase modulo one turn, so the deviation of the slot gear from
the pin gear repeats at every turn of the pin gear. -/
theorem lag_add_two_pi (r e φ : ℝ) : lag r e (φ + 2 * π) = lag r e φ := by
  simp only [lag, sin_add_two_pi, cos_add_two_pi]

/-- An offset smaller than the pin radius forces a positive pin radius. -/
theorem pos_of_abs_lt {e r : ℝ} (h : |e| < r) : 0 < r :=
  lt_of_le_of_lt (abs_nonneg e) h

/-- The spec's hypothesis `0 ≤ e < r` in the form `|e| < r` used below. -/
theorem abs_lt_of_nonneg_of_lt {e r : ℝ} (he : 0 ≤ e) (h : e < r) : |e| < r := by
  rwa [abs_of_nonneg he]

/-- The offset is smaller than the pin radius (`|e| < r`). So the vector from the slot gear's axis
to the pin always has a positive component `r - e cos φ` along the pin's radius: the slot never
points more than a quarter turn away from the pin's radius. -/
theorem denom_pos {r e : ℝ} (h : |e| < r) (φ : ℝ) : 0 < r - e * cos φ := by
  have : e * cos φ ≤ |e| :=
    calc e * cos φ ≤ |e * cos φ| := le_abs_self _
      _ = |e| * |cos φ| := abs_mul _ _
      _ ≤ |e| * 1 := by gcongr; exact abs_cos_le_one φ
      _ = |e| := mul_one _
  linarith

/-- Because the denominator is positive, the spec's `atan2` in the pin-and-slot law is an ordinary
`arctan`. The slot gear angle is then a smooth function of the pin gear angle, with no jump between
branches. -/
theorem lag_eq_arctan {r e : ℝ} (h : |e| < r) (φ : ℝ) :
    lag r e φ = arctan (e * sin φ / (r - e * cos φ)) :=
  atan2_eq_arctan _ (denom_pos h φ)

/-- The lag varies continuously with the pin's phase: the slot gear never jumps. -/
theorem continuous_lag {r e : ℝ} (h : |e| < r) : Continuous (lag r e) := by
  rw [show lag r e = fun φ => arctan (e * sin φ / (r - e * cos φ)) from funext (lag_eq_arctan h)]
  exact continuous_arctan.comp ((continuous_const.mul continuous_sin).div
    (continuous_const.sub (continuous_const.mul continuous_cos)) fun φ => (denom_pos h φ).ne')

/-- The slot gear always stays within a quarter turn of the pin gear: `|δ| < π/2`. -/
theorem abs_lag_lt_pi_div_two {r e : ℝ} (h : |e| < r) (φ : ℝ) : |lag r e φ| < π / 2 := by
  rw [lag_eq_arctan h, abs_lt]
  exact ⟨neg_pi_div_two_lt_arctan _, arctan_lt_pi_div_two _⟩

/-- `r² - e² > 0` when `|e| < r`. -/
theorem sq_sub_sq_pos {r e : ℝ} (h : |e| < r) : 0 < r ^ 2 - e ^ 2 := by
  have : e ^ 2 < r ^ 2 := by
    rw [← sq_abs]; exact pow_lt_pow_left₀ h (abs_nonneg e) two_ne_zero
  linarith

/-- The key algebraic identity: after clearing denominators, the lag bound is
`e² (r - e cos φ)² - (e sin φ)² (r² - e²) = e² (r cos φ - e)² ≥ 0`. -/
theorem lag_identity (r e φ : ℝ) :
    (e * sin φ) ^ 2 * (r ^ 2 - e ^ 2) = (e * (r - e * cos φ)) ^ 2 - (e * (r * cos φ - e)) ^ 2 := by
  linear_combination (e ^ 2 * (r ^ 2 - e ^ 2)) * sin_sq_add_cos_sq φ

/-- The tangent of the lag never exceeds `|e| / √(r² - e²)` in absolute value. This is the sharp
bound on the angular deviation of the slot gear from the pin gear. -/
theorem abs_tan_lag_le {r e : ℝ} (h : |e| < r) (φ : ℝ) :
    |e * sin φ / (r - e * cos φ)| ≤ |e| / √(r ^ 2 - e ^ 2) := by
  have hD := denom_pos h φ
  have hre := sq_sub_sq_pos h
  have hs := Real.sqrt_pos.2 hre
  have hs2 := Real.sq_sqrt hre.le
  rw [abs_div, abs_of_pos hD, div_le_div_iff₀ hD hs]
  have key : (|e * sin φ| * √(r ^ 2 - e ^ 2)) ^ 2 ≤ (|e| * (r - e * cos φ)) ^ 2 :=
    calc (|e * sin φ| * √(r ^ 2 - e ^ 2)) ^ 2 = (e * sin φ) ^ 2 * (r ^ 2 - e ^ 2) := by
          rw [mul_pow, sq_abs, hs2]
      _ ≤ (|e| * (r - e * cos φ)) ^ 2 := by
          have habs : (|e| * (r - e * cos φ)) ^ 2 = (e * (r - e * cos φ)) ^ 2 := by
            rw [mul_pow, mul_pow, sq_abs]
          rw [lag_identity, habs]
          linarith [sq_nonneg (e * (r * cos φ - e))]
  exact (pow_le_pow_iff_left₀ (by positivity) (mul_nonneg (abs_nonneg e) hD.le)
    two_ne_zero).1 key

/-- `√(1 - (e/r)²) = √(r² - e²) / r`. -/
theorem sqrt_one_sub_div_sq {r e : ℝ} (h : |e| < r) :
    √(1 - (e / r) ^ 2) = √(r ^ 2 - e ^ 2) / r := by
  have hr := pos_of_abs_lt h
  rw [show 1 - (e / r) ^ 2 = (r ^ 2 - e ^ 2) / r ^ 2 by field_simp,
    Real.sqrt_div' _ (sq_nonneg r), Real.sqrt_sq hr.le]

/-- `|e / r| < 1` when `|e| < r`. -/
theorem abs_div_lt_one {r e : ℝ} (h : |e| < r) : |e / r| < 1 := by
  have hr := pos_of_abs_lt h
  rw [abs_div, abs_of_pos hr, div_lt_one hr]
  exact h

/-- The bound is attained: when the pin's phase satisfies `cos φ = e / r`, the tangent of the lag is
exactly `e / √(r² - e²)`. -/
theorem tan_lag_arccos {r e : ℝ} (h : |e| < r) :
    e * sin (arccos (e / r)) / (r - e * cos (arccos (e / r))) = e / √(r ^ 2 - e ^ 2) := by
  have hr := pos_of_abs_lt h
  obtain ⟨hx1, hx2⟩ := abs_lt.1 (abs_div_lt_one h)
  have hre := sq_sub_sq_pos h
  have hs0 := (Real.sqrt_pos.2 hre).ne'
  have hs2 := Real.sq_sqrt hre.le
  rw [sin_arccos, cos_arccos hx1.le hx2.le, sqrt_one_sub_div_sq h]
  have hden : r - e * (e / r) = (r ^ 2 - e ^ 2) / r := by field_simp
  rw [hden, div_eq_div_iff (div_pos hre hr).ne' hs0]
  field_simp
  rw [hs2]

/-- The classical identity `arctan (e / √(r² - e²)) = arcsin (e / r)`: the largest lag, as an
angle, is `arcsin (e / r)`. -/
theorem arctan_eq_arcsin_div {r e : ℝ} (h : |e| < r) :
    arctan (e / √(r ^ 2 - e ^ 2)) = arcsin (e / r) := by
  have hr := pos_of_abs_lt h
  obtain ⟨hx1, hx2⟩ := abs_lt.1 (abs_div_lt_one h)
  rw [arcsin_eq_arctan ⟨hx1, hx2⟩, sqrt_one_sub_div_sq h]
  congr 1
  field_simp

/-- The slot gear never leads or trails the pin gear by more than `arcsin (|e| / r)`. -/
theorem abs_lag_le {r e : ℝ} (h : |e| < r) (φ : ℝ) : |lag r e φ| ≤ arcsin (|e| / r) := by
  have h' : |(|e|)| < r := by rwa [abs_abs]
  rw [lag_eq_arctan h, abs_arctan, ← arctan_eq_arcsin_div h', sq_abs]
  exact arctan_strictMono.monotone (abs_tan_lag_le h φ)

/-- The largest lag in absolute value is reached when the pin's phase is `arccos (e / r)`. The lag
there is exactly `arcsin (e / r)` (its maximum for `e ≥ 0`, its minimum for `e < 0`). -/
theorem lag_arccos {r e : ℝ} (h : |e| < r) : lag r e (arccos (e / r)) = arcsin (e / r) := by
  rw [lag_eq_arctan h, tan_lag_arccos h, arctan_eq_arcsin_div h]

/-- The amplitude of a pin-and-slot coupling with `0 ≤ e < r` is exactly `arcsin (e / r)`. It
bounds the angle between the slot gear and the pin gear, and some pin phase attains it. -/
theorem isGreatest_abs_lag {r e : ℝ} (he : 0 ≤ e) (her : e < r) :
    IsGreatest (range fun φ => |lag r e φ|) (arcsin (e / r)) := by
  have h := abs_lt_of_nonneg_of_lt he her
  have hr := pos_of_abs_lt h
  refine ⟨⟨arccos (e / r), ?_⟩, ?_⟩
  · show |lag r e (arccos (e / r))| = arcsin (e / r)
    rw [lag_arccos h, abs_of_nonneg (arcsin_nonneg.2 (div_nonneg he hr.le))]
  · rintro _ ⟨φ, rfl⟩
    have := abs_lag_le h φ
    rwa [abs_of_nonneg he] at this

/-- The amplitude `arcsin (|e| / r)` is less than a quarter turn. -/
theorem arcsin_div_lt_pi_div_two {r e : ℝ} (h : |e| < r) : arcsin (|e| / r) < π / 2 := by
  have hr := pos_of_abs_lt h
  exact arcsin_lt_pi_div_two.2 ((div_lt_one hr).2 h)

/-- The pin-and-slot law keeps the slot gear within `arcsin (|e| / r)` of the pin gear, whatever the
pin gear's angle. -/
theorem abs_slotAngle_sub_le {r e : ℝ} (h : |e| < r) (β θ₁ : ℝ) :
    |slotAngle r e β θ₁ - θ₁| ≤ arcsin (|e| / r) := by
  rw [slotAngle_eq, add_sub_cancel_left]
  exact abs_lag_le h _

/-! ### Instantaneous motion of the slot gear -/

/-- `r² - 2 r e cos φ + e²` is the squared distance from the slot gear's axis to the pin. It is
positive when `|e| < r`, so the pin never passes through the slot gear's axis. -/
theorem pinDist_sq_pos {r e : ℝ} (h : |e| < r) (φ : ℝ) :
    0 < r ^ 2 - 2 * r * e * cos φ + e ^ 2 := by
  have hD := denom_pos h φ
  nlinarith [sin_sq_add_cos_sq φ, sq_nonneg (e * sin φ), mul_pos hD hD]

/-- The instantaneous speed ratio of a pin-and-slot at pin phase `φ`: the slot gear's angular speed
divided by the pin gear's, both measured relative to the carrier. -/
noncomputable def speedRatio (r e φ : ℝ) : ℝ :=
  r * (r - e * cos φ) / (r ^ 2 - 2 * r * e * cos φ + e ^ 2)

/-- Rate of change of the lag with the pin's phase:
`(e r cos φ - e²) / (r² - 2 r e cos φ + e²)`. -/
theorem hasDerivAt_lag {r e : ℝ} (h : |e| < r) (φ : ℝ) :
    HasDerivAt (lag r e) ((e * r * cos φ - e ^ 2) / (r ^ 2 - 2 * r * e * cos φ + e ^ 2)) φ := by
  have hD := denom_pos h φ
  have hN := pinDist_sq_pos h φ
  rw [show lag r e = fun φ => arctan (e * sin φ / (r - e * cos φ)) from funext (lag_eq_arctan h)]
  have h1 : HasDerivAt (fun φ => e * sin φ) (e * cos φ) φ := (hasDerivAt_sin φ).const_mul e
  have h2 : HasDerivAt (fun φ => r - e * cos φ) (e * sin φ) φ := by
    simpa using ((hasDerivAt_cos φ).const_mul e).const_sub r
  convert (h1.div h2 hD.ne').arctan using 1
  simp only [Pi.div_apply]
  field_simp
  have hid : (r - e * cos φ) ^ 2 + e ^ 2 * sin φ ^ 2 = r * (r - e * cos φ * 2) + e ^ 2 := by
    linear_combination e ^ 2 * sin_sq_add_cos_sq φ
  rw [hid, mul_div_assoc, div_self (by nlinarith), mul_one]
  linear_combination e ^ 2 * sin_sq_add_cos_sq φ

/-- The slot gear's angle is a differentiable function of the pin gear's angle, with derivative
`speedRatio r e (θ₁ - β)`. -/
theorem hasDerivAt_slotAngle {r e : ℝ} (h : |e| < r) (β θ₁ : ℝ) :
    HasDerivAt (slotAngle r e β) (speedRatio r e (θ₁ - β)) θ₁ := by
  have hN := pinDist_sq_pos h (θ₁ - β)
  have hl := (hasDerivAt_lag h (θ₁ - β)).comp θ₁ ((hasDerivAt_id' θ₁).sub_const β)
  convert (hasDerivAt_id' θ₁).add hl using 1
  · funext x
    rfl
  · unfold speedRatio
    rw [mul_one, one_add_div hN.ne']
    congr 1
    ring

/-- The instantaneous speed ratio is positive. -/
theorem speedRatio_pos {r e : ℝ} (h : |e| < r) (φ : ℝ) : 0 < speedRatio r e φ :=
  div_pos (mul_pos (pos_of_abs_lt h) (denom_pos h φ)) (pinDist_sq_pos h φ)

/-- Relative to the carrier, the slot gear's angle is a strictly increasing function of the pin
gear's: while the pin gear turns one way, the slot gear never stops or reverses. -/
theorem strictMono_slotAngle {r e : ℝ} (h : |e| < r) (β : ℝ) : StrictMono (slotAngle r e β) :=
  strictMono_of_deriv_pos fun θ => by
    rw [(hasDerivAt_slotAngle h β θ).deriv]
    exact speedRatio_pos h _

/-- Relative to the carrier, the slot gear's instantaneous speed stays between `r / (r + e)` and
`r / (r - e)` times the pin gear's (reached at phases `π` and `0`). For the lunar pin-and-slot, that
is between `9.6 / 10.7` and `9.6 / 8.5`. -/
theorem speedRatio_mem {r e : ℝ} (he : 0 ≤ e) (her : e < r) (φ : ℝ) :
    r / (r + e) ≤ speedRatio r e φ ∧ speedRatio r e φ ≤ r / (r - e) := by
  have h := abs_lt_of_nonneg_of_lt he her
  have hr := pos_of_abs_lt h
  have hN := pinDist_sq_pos h φ
  have hc1 := cos_le_one φ
  have hc2 := neg_one_le_cos φ
  unfold speedRatio
  constructor
  · rw [div_le_div_iff₀ (by linarith) hN]
    nlinarith [mul_nonneg hr.le (mul_nonneg (mul_nonneg he (sub_nonneg.2 her.le))
      (by linarith : (0 : ℝ) ≤ 1 + cos φ))]
  · rw [div_le_div_iff₀ hN (by linarith)]
    nlinarith [mul_nonneg hr.le (mul_nonneg (mul_nonneg he (by linarith : 0 ≤ r + e))
      (by linarith : (0 : ℝ) ≤ 1 - cos φ))]

/-! ## 3. The followers -/

/-- The lag of a follower (spec: `atan2 (d sin λ) (i + d cos λ)`) at pin phase `ψ` (the spec's
`λ`). Here `i` is the distance from the central axis to the epicycle axis, and `d` the distance of
the pin from the epicycle axis. The lag is the angle, seen from the central axis, between the
epicycle axis and the pin. -/
noncomputable def followerLag (i d ψ : ℝ) : ℝ :=
  atan2 (d * sin ψ) (i + d * cos ψ)

/-- The spec's follower law `θ_F = θ_b + g₀ + atan2 (d sin λ) (i + d cos λ)`: the angle of a
follower pointer (Mercury, Venus, true Sun) when `b` is at `θb` and the pin's phase on the epicycle
is `ψ`. -/
noncomputable def followerAngle (i d g₀ θb ψ : ℝ) : ℝ :=
  θb + g₀ + atan2 (d * sin ψ) (i + d * cos ψ)

/-- A follower is `b` plus the constant `g₀` plus its lag. -/
theorem followerAngle_eq (i d g₀ θb ψ : ℝ) :
    followerAngle i d g₀ θb ψ = θb + (g₀ + followerLag i d ψ) := by
  unfold followerAngle followerLag
  ring

/-- When `|d| < i` the denominator `i + d cos λ` of the follower law stays positive: the follower's
geometry never degenerates. -/
theorem follower_denom_pos {i d : ℝ} (h : |d| < i) (ψ : ℝ) : 0 < i + d * cos ψ := by
  have := denom_pos (e := -d) (by rwa [abs_neg]) ψ
  linarith

/-- The follower law's `atan2` is an ordinary `arctan`. -/
theorem followerLag_eq_arctan {i d : ℝ} (h : |d| < i) (ψ : ℝ) :
    followerLag i d ψ = arctan (d * sin ψ / (i + d * cos ψ)) :=
  atan2_eq_arctan _ (follower_denom_pos h ψ)

/-- A follower is a pin-and-slot with the offset reversed: `followerLag i d ψ = -lag i (-d) ψ`. -/
theorem followerLag_eq_neg_lag {i d : ℝ} (h : |d| < i) (ψ : ℝ) :
    followerLag i d ψ = -lag i (-d) ψ := by
  have h' : |-d| < i := by rwa [abs_neg]
  rw [followerLag_eq_arctan h, lag_eq_arctan h', ← arctan_neg]
  congr 1
  rw [show i - -d * cos ψ = i + d * cos ψ by ring]
  ring

/-- A follower never departs from `b + g₀` by more than `arcsin (|d| / i)`. -/
theorem abs_followerLag_le {i d : ℝ} (h : |d| < i) (ψ : ℝ) :
    |followerLag i d ψ| ≤ arcsin (|d| / i) := by
  have h' : |-d| < i := by rwa [abs_neg]
  have := abs_lag_le h' ψ
  rw [abs_neg] at this
  rwa [followerLag_eq_neg_lag h, abs_neg]

/-- The largest follower lag is reached at phase `arccos (-d / i)`, where it equals
`arcsin (d / i)`. For Mercury and Venus, whose epicycle axis stands for the mean Sun, this is the
greatest elongation. -/
theorem followerLag_arccos {i d : ℝ} (h : |d| < i) :
    followerLag i d (arccos (-d / i)) = arcsin (d / i) := by
  have h' : |-d| < i := by rwa [abs_neg]
  rw [followerLag_eq_neg_lag h, lag_arccos h', neg_div, arcsin_neg, neg_neg]

/-- The amplitude of a follower with `0 ≤ d < i` is exactly `arcsin (d / i)`. -/
theorem isGreatest_abs_followerLag {i d : ℝ} (hd : 0 ≤ d) (hdi : d < i) :
    IsGreatest (range fun ψ => |followerLag i d ψ|) (arcsin (d / i)) := by
  have h := abs_lt_of_nonneg_of_lt hd hdi
  have hi := pos_of_abs_lt h
  refine ⟨⟨arccos (-d / i), ?_⟩, ?_⟩
  · show |followerLag i d (arccos (-d / i))| = arcsin (d / i)
    rw [followerLag_arccos h, abs_of_nonneg (arcsin_nonneg.2 (div_nonneg hd hi.le))]
  · rintro _ ⟨ψ, rfl⟩
    have := abs_followerLag_le h ψ
    rwa [abs_of_nonneg hd] at this

/-! ## 4. Mean rates -/

/-- `θ` turns at mean rate `ω`: the average rate `(θ T - θ 0) / T` over `[0, T]` tends to `ω` as
`T → ∞`. The rates of `Kinematics` are mean rates in this sense, up to the factor `-2π` (see the
module docstring). -/
def HasMeanRate (θ : ℝ → ℝ) (ω : ℝ) : Prop :=
  Tendsto (fun T => (θ T - θ 0) / T) atTop (𝓝 ω)

/-- A motion has at most one mean rate. -/
theorem HasMeanRate.unique {θ : ℝ → ℝ} {ω ω' : ℝ} (h : HasMeanRate θ ω) (h' : HasMeanRate θ ω') :
    ω = ω' :=
  tendsto_nhds_unique h h'

/-- A gear turning at constant speed, `θ t = θ₀ + ω t`, has mean rate `ω`. -/
theorem hasMeanRate_uniform (θ₀ ω : ℝ) : HasMeanRate (fun t => θ₀ + ω * t) ω := by
  unfold HasMeanRate
  refine tendsto_const_nhds.congr' ?_
  filter_upwards [eventually_ne_atTop 0] with T hT
  field_simp
  ring

/-- If `θ₂ = θ₁ + δ` with `|δ| ≤ M`, the net angles turned by the two bodies over any interval
`[0, T]` differ by at most `2 M`. -/
theorem abs_net_sub_le {θ₁ θ₂ δ : ℝ → ℝ} {M : ℝ} (h : ∀ t, θ₂ t = θ₁ t + δ t)
    (hδ : ∀ t, |δ t| ≤ M) (T : ℝ) : |(θ₂ T - θ₂ 0) - (θ₁ T - θ₁ 0)| ≤ 2 * M := by
  rw [h T, h 0]
  have h1 := abs_le.1 (hδ T)
  have h2 := abs_le.1 (hδ 0)
  rw [abs_le]
  constructor <;> linarith [h1.1, h1.2, h2.1, h2.2]

/-- A bounded lag disappears in the average: the difference between the average rates of `θ₂` and
`θ₁` over `[0, T]` tends to `0` as `T → ∞`. -/
theorem tendsto_meanRate_sub {θ₁ θ₂ δ : ℝ → ℝ} {M : ℝ} (h : ∀ t, θ₂ t = θ₁ t + δ t)
    (hδ : ∀ t, |δ t| ≤ M) :
    Tendsto (fun T => (θ₂ T - θ₂ 0) / T - (θ₁ T - θ₁ 0) / T) atTop (𝓝 0) := by
  refine squeeze_zero_norm' (a := fun T => 2 * M / T) ?_ (tendsto_const_nhds.div_atTop tendsto_id)
  filter_upwards [eventually_gt_atTop 0] with T hT
  rw [Real.norm_eq_abs, ← sub_div, abs_div, abs_of_pos hT]
  gcongr
  exact abs_net_sub_le h hδ T

/-- A body that differs from another by a bounded lag has the same mean rate. -/
theorem HasMeanRate.of_bounded_lag {θ₁ θ₂ δ : ℝ → ℝ} {M ω : ℝ} (h₁ : HasMeanRate θ₁ ω)
    (h : ∀ t, θ₂ t = θ₁ t + δ t) (hδ : ∀ t, |δ t| ≤ M) : HasMeanRate θ₂ ω := by
  have := h₁.add (tendsto_meanRate_sub h hδ)
  rw [add_zero] at this
  exact this.congr fun T => by ring

/-- Two bodies that differ by a bounded lag have equal mean rates, whenever these exist. -/
theorem meanRate_eq_of_bounded_lag {θ₁ θ₂ δ : ℝ → ℝ} {M ω₁ ω₂ : ℝ} (h : ∀ t, θ₂ t = θ₁ t + δ t)
    (hδ : ∀ t, |δ t| ≤ M) (h₁ : HasMeanRate θ₁ ω₁) (h₂ : HasMeanRate θ₂ ω₂) : ω₂ = ω₁ :=
  h₂.unique (h₁.of_bounded_lag h hδ)

/-- **Pin-and-slot, mean rate.** Both gear angles are measured relative to the carrier (spec
`conventions.pin_slot_formula`). Let the carrier have angle `θc`, the pin gear absolute angle
`θ₁`, and the slot gear absolute angle `θ₂ = θc + slotAngle r e β (θ₁ - θc)`. If the pin gear has
mean rate `ω`, then so does the slot gear, whatever the motions. This is the content of the fields
`pinslot_*` of `Kinematics`. -/
theorem pinSlot_hasMeanRate {r e β ω : ℝ} (h : |e| < r) {θc θ₁ θ₂ : ℝ → ℝ}
    (hlaw : ∀ t, θ₂ t = θc t + slotAngle r e β (θ₁ t - θc t)) (h₁ : HasMeanRate θ₁ ω) :
    HasMeanRate θ₂ ω :=
  h₁.of_bounded_lag (δ := fun t => lag r e (θ₁ t - θc t - β))
    (fun t => by rw [hlaw, slotAngle_eq]; ring) fun _ => abs_lag_le h _

/-- **Follower, mean rate.** Let `b` have angle `θb`, and let a follower obey the spec law
`θF = θb + g₀ + atan2 (d sin ψ) (i + d cos ψ)`, where the pin's phase `ψ` moves in any way. If `b`
has mean rate `ω`, then so does the follower. This is the content of the fields `follower_*` of
`Kinematics`. -/
theorem follower_hasMeanRate {i d g₀ ω : ℝ} (h : |d| < i) {θb ψ θF : ℝ → ℝ}
    (hlaw : ∀ t, θF t = followerAngle i d g₀ (θb t) (ψ t)) (hb : HasMeanRate θb ω) :
    HasMeanRate θF ω :=
  hb.of_bounded_lag (δ := fun t => g₀ + followerLag i d (ψ t)) (M := |g₀| + arcsin (|d| / i))
    (fun t => by rw [hlaw, followerAngle_eq])
    fun _ => (abs_add_le _ _).trans (add_le_add le_rfl (abs_followerLag_le h _))

/-- In the form of the `Kinematics` equations: when the pin gear and the slot gear of a pin-and-slot
both have mean rates, these rates are equal. -/
theorem pinSlot_meanRate_eq {r e β ω₁ ω₂ : ℝ} (h : |e| < r) {θc θ₁ θ₂ : ℝ → ℝ}
    (hlaw : ∀ t, θ₂ t = θc t + slotAngle r e β (θ₁ t - θc t)) (h₁ : HasMeanRate θ₁ ω₁)
    (h₂ : HasMeanRate θ₂ ω₂) : ω₂ = ω₁ :=
  h₂.unique (pinSlot_hasMeanRate h hlaw h₁)

/-- In the form of the `Kinematics` equations: when `b` and a follower both have mean rates, these
rates are equal. -/
theorem follower_meanRate_eq {i d g₀ ω₁ ω₂ : ℝ} (h : |d| < i) {θb ψ θF : ℝ → ℝ}
    (hlaw : ∀ t, θF t = followerAngle i d g₀ (θb t) (ψ t)) (hb : HasMeanRate θb ω₁)
    (hF : HasMeanRate θF ω₂) : ω₂ = ω₁ :=
  hF.unique (follower_hasMeanRate h hlaw hb)

/-! ### The seven nonlinear couplings of the mechanism

Each theorem below instantiates the general results with the spec's dimensions (spec `pin_slots`
and `followers`). The hypotheses `0 ≤ e < r` and `0 ≤ d < i` are checked by `norm_num`. The offset
directions `β` (spec `offset_dir_local_deg`) and the constants `g₀` are left arbitrary, which only
makes the statements stronger. -/

/-- Field `pinslot_lunar` of `Kinematics`: pin gear k1 (body `k`) drives slot gear k2 (body `kp`)
on the carrier `e_table`, with `r = 9.6` and `e = 1.1`. The slot gear `kp` has the mean rate of
`k`. -/
theorem lunar_meanRate {β ω : ℝ} {θc θk θkp : ℝ → ℝ}
    (hlaw : ∀ t, θkp t = θc t + slotAngle 9.6 1.1 β (θk t - θc t)) (hk : HasMeanRate θk ω) :
    HasMeanRate θkp ω :=
  pinSlot_hasMeanRate (abs_lt_of_nonneg_of_lt (by norm_num) (by norm_num)) hlaw hk

/-- Field `pinslot_saturn` of `Kinematics`: sa68 (body `x_sa68`) drives sa86s (body `x_sa86s`) on
the carrier `b`, with `r = 14.37` and `e = 1.5`. -/
theorem saturn_meanRate {β ω : ℝ} {θc θ₁ θ₂ : ℝ → ℝ}
    (hlaw : ∀ t, θ₂ t = θc t + slotAngle 14.37 1.5 β (θ₁ t - θc t)) (h₁ : HasMeanRate θ₁ ω) :
    HasMeanRate θ₂ ω :=
  pinSlot_hasMeanRate (abs_lt_of_nonneg_of_lt (by norm_num) (by norm_num)) hlaw h₁

/-- Field `pinslot_jupiter` of `Kinematics`: ju43 (body `x_ju43`) drives ju65s (body `x_ju65s`) on
the carrier `b`, with `r = 8.22` and `e = 1.58`. -/
theorem jupiter_meanRate {β ω : ℝ} {θc θ₁ θ₂ : ℝ → ℝ}
    (hlaw : ∀ t, θ₂ t = θc t + slotAngle 8.22 1.58 β (θ₁ t - θc t)) (h₁ : HasMeanRate θ₁ ω) :
    HasMeanRate θ₂ ω :=
  pinSlot_hasMeanRate (abs_lt_of_nonneg_of_lt (by norm_num) (by norm_num)) hlaw h₁

/-- Field `pinslot_mars` of `Kinematics`: ma71 (body `x_ma71`) drives ma80s (body `x_ma80s`) on the
carrier `b`, with `r = 10.0` and `e = 6.58`. -/
theorem mars_meanRate {β ω : ℝ} {θc θ₁ θ₂ : ℝ → ℝ}
    (hlaw : ∀ t, θ₂ t = θc t + slotAngle 10.0 6.58 β (θ₁ t - θc t)) (h₁ : HasMeanRate θ₁ ω) :
    HasMeanRate θ₂ ω :=
  pinSlot_hasMeanRate (abs_lt_of_nonneg_of_lt (by norm_num) (by norm_num)) hlaw h₁

/-- Field `follower_mercury` of `Kinematics`: the Mercury pointer `t_mercury` follows a pin on
`x_me20` (`i = 36.0`, `d = 14.04`). It has the mean rate of `b`, the mean Sun. -/
theorem mercury_meanRate {g₀ ω : ℝ} {θb ψ θF : ℝ → ℝ}
    (hlaw : ∀ t, θF t = followerAngle 36.0 14.04 g₀ (θb t) (ψ t)) (hb : HasMeanRate θb ω) :
    HasMeanRate θF ω :=
  follower_hasMeanRate (abs_lt_of_nonneg_of_lt (by norm_num) (by norm_num)) hlaw hb

/-- Field `follower_venus` of `Kinematics`: the Venus pointer `t_venus` follows a pin on `x_r1`
(`i = 27.8`, `d = 20.01`). It has the mean rate of `b`. -/
theorem venus_meanRate {g₀ ω : ℝ} {θb ψ θF : ℝ → ℝ}
    (hlaw : ∀ t, θF t = followerAngle 27.8 20.01 g₀ (θb t) (ψ t)) (hb : HasMeanRate θb ω) :
    HasMeanRate θF ω :=
  follower_hasMeanRate (abs_lt_of_nonneg_of_lt (by norm_num) (by norm_num)) hlaw hb

/-- Field `follower_trueSun` of `Kinematics`: the true-Sun pointer `t_trueSun` follows an eccentric
pin on `x_su56` (`i = 39.711744`, `d = 1.654656 = i / 24`). It has the mean rate of `b`. -/
theorem trueSun_meanRate {g₀ ω : ℝ} {θb ψ θF : ℝ → ℝ}
    (hlaw : ∀ t, θF t = followerAngle 39.711744 1.654656 g₀ (θb t) (ψ t)) (hb : HasMeanRate θb ω) :
    HasMeanRate θF ω :=
  follower_hasMeanRate (abs_lt_of_nonneg_of_lt (by norm_num) (by norm_num)) hlaw hb

/-- Hipparchus' lunar anomaly: the lag of the lunar pin-and-slot is at most `arcsin (1.1 / 9.6)` in
absolute value, and that value is reached. The train k2 → e6 → e1 → b3 is 50:50 then 32:32 (spec
`meshes`), so the Moon pointer's angle is `θ_kp - 2 θ_e_table` up to a constant: it deviates from
uniform motion by exactly this lag. -/
theorem lunar_isGreatest : IsGreatest (range fun φ => |lag 9.6 1.1 φ|) (arcsin (1.1 / 9.6)) :=
  isGreatest_abs_lag (by norm_num) (by norm_num)

/-- The Mercury, Venus and true-Sun pointers deviate from `b + g₀` by at most `arcsin (d / i)`, and
that value is reached. For Mercury and Venus it is the greatest elongation from the mean Sun; for
the true Sun it is the largest equation of centre. -/
theorem followers_isGreatest :
    IsGreatest (range fun ψ => |followerLag 36.0 14.04 ψ|) (arcsin (14.04 / 36.0)) ∧
    IsGreatest (range fun ψ => |followerLag 27.8 20.01 ψ|) (arcsin (20.01 / 27.8)) ∧
    IsGreatest (range fun ψ => |followerLag 39.711744 1.654656 ψ|)
      (arcsin (1.654656 / 39.711744)) :=
  ⟨isGreatest_abs_followerLag (by norm_num) (by norm_num),
    isGreatest_abs_followerLag (by norm_num) (by norm_num),
    isGreatest_abs_followerLag (by norm_num) (by norm_num)⟩

/-! ## 5. Numerical amplitudes

The amplitude of each coupling is `arcsin (e / r)` (resp. `arcsin (d / i)`), converted to degrees
by `· * 180 / π`. To bound it, we use `3.141592 < π < 3.141593` (`Real.pi_gt_d6`,
`Real.pi_lt_d6`), the monotonicity of `arcsin`, and Taylor bounds for `sin` at rational points. For
the large angles (Mars, Venus) we use the double-angle formula first. -/

/-- Taylor upper bound `sin t ≤ t - t³/6 + t⁵/100` for `0 ≤ t ≤ 1` (from `Real.sin_bound`). -/
theorem sin_le_taylor {t : ℝ} (h0 : 0 ≤ t) (h1 : t ≤ 1) : sin t ≤ t - t ^ 3 / 6 + t ^ 5 / 100 := by
  have hb := Real.sin_bound (show |t| ≤ 1 by rwa [abs_of_nonneg h0])
  rw [abs_of_nonneg h0] at hb
  linarith [(abs_le.1 hb).2]

/-- Taylor lower bound `t - t³/6 ≤ sin t` for `t ≥ 0`. -/
theorem taylor_le_sin {t : ℝ} (h0 : 0 ≤ t) : t - t ^ 3 / 6 ≤ sin t :=
  sin_ge_sub_cube h0

/-- `sin t = 2 sin (t/2) (1 - 2 sin² (t/4))`: the double-angle formula, applied twice. -/
theorem sin_eq_double (t : ℝ) : sin t = 2 * sin (t / 2) * (1 - 2 * sin (t / 4) ^ 2) := by
  have h1 : sin t = 2 * sin (t / 2) * cos (t / 2) := by
    rw [← sin_two_mul]; congr 1; ring
  have h2 : cos (t / 2) = 1 - 2 * sin (t / 4) ^ 2 := by
    rw [← cos_two_mul_eq_one_sub]; congr 1; ring
  rw [h1, h2]

/-- Upper bound for `sin t` on `[0, 2]`, from the double-angle formula and Taylor bounds at `t/2`
and `t/4`. -/
theorem sin_le_double {t : ℝ} (h0 : 0 ≤ t) (h2 : t ≤ 2) :
    sin t ≤ 2 * (t / 2 - (t / 2) ^ 3 / 6 + (t / 2) ^ 5 / 100) *
      (1 - 2 * (t / 4 - (t / 4) ^ 3 / 6) ^ 2) := by
  have hπ := pi_gt_three
  have hs : sin (t / 2) ≤ t / 2 - (t / 2) ^ 3 / 6 + (t / 2) ^ 5 / 100 :=
    sin_le_taylor (by linarith) (by linarith)
  have hs0 : 0 ≤ sin (t / 2) := sin_nonneg_of_nonneg_of_le_pi (by linarith) (by linarith)
  have hp4 : t / 4 - (t / 4) ^ 3 / 6 ≤ sin (t / 4) := taylor_le_sin (by linarith)
  have hp40 : 0 ≤ t / 4 - (t / 4) ^ 3 / 6 :=
    by nlinarith [mul_nonneg h0 (sub_nonneg.2 h2), mul_nonneg (mul_nonneg h0 h0) (sub_nonneg.2 h2)]
  have hc0 : 0 ≤ 1 - 2 * sin (t / 4) ^ 2 := by
    rw [← cos_two_mul_eq_one_sub]
    exact cos_nonneg_of_mem_Icc ⟨by linarith, by linarith⟩
  have hsq : (t / 4 - (t / 4) ^ 3 / 6) ^ 2 ≤ sin (t / 4) ^ 2 := pow_le_pow_left₀ hp40 hp4 2
  rw [sin_eq_double]
  nlinarith [mul_le_mul_of_nonneg_right hs hc0, mul_le_mul_of_nonneg_left hsq (hs0.trans hs)]

/-- Lower bound for `sin t` on `[0, 2]`, from the double-angle formula and Taylor bounds at `t/2`
and `t/4`. -/
theorem double_le_sin {t : ℝ} (h0 : 0 ≤ t) (h2 : t ≤ 2) :
    2 * (t / 2 - (t / 2) ^ 3 / 6) * (1 - 2 * (t / 4 - (t / 4) ^ 3 / 6 + (t / 4) ^ 5 / 100) ^ 2)
      ≤ sin t := by
  have hπ := pi_gt_three
  have hp : t / 2 - (t / 2) ^ 3 / 6 ≤ sin (t / 2) := taylor_le_sin (by linarith)
  have hp0 : 0 ≤ t / 2 - (t / 2) ^ 3 / 6 :=
    by nlinarith [mul_nonneg h0 (sub_nonneg.2 h2), mul_nonneg (mul_nonneg h0 h0) (sub_nonneg.2 h2)]
  have hs4 : sin (t / 4) ≤ t / 4 - (t / 4) ^ 3 / 6 + (t / 4) ^ 5 / 100 :=
    sin_le_taylor (by linarith) (by linarith)
  have hs40 : 0 ≤ sin (t / 4) := sin_nonneg_of_nonneg_of_le_pi (by linarith) (by linarith)
  have hc0 : 0 ≤ 1 - 2 * sin (t / 4) ^ 2 := by
    rw [← cos_two_mul_eq_one_sub]
    exact cos_nonneg_of_mem_Icc ⟨by linarith, by linarith⟩
  have hsq : sin (t / 4) ^ 2 ≤ (t / 4 - (t / 4) ^ 3 / 6 + (t / 4) ^ 5 / 100) ^ 2 :=
    pow_le_pow_left₀ hs40 hs4 2
  rw [sin_eq_double]
  nlinarith [mul_le_mul_of_nonneg_right hp hc0, mul_le_mul_of_nonneg_left hsq hp0]

/-- Lower bound in degrees: if `sin (l · 3.141593 / 180) < x`, then `arcsin x` exceeds `l`
degrees. -/
theorem lt_arcsin_deg {x l : ℝ} (hl : 0 < l) (hl' : l ≤ 89) (hx : x ≤ 1)
    (h : sin (l * 3.141593 / 180) < x) : l < arcsin x * 180 / π := by
  have hπ := pi_gt_d6
  have ht : l * 3.141593 / 180 ∈ Icc (-(π / 2)) (π / 2) := ⟨by linarith, by linarith⟩
  have h1 := (lt_arcsin_iff_sin_lt ht
    ⟨by linarith [neg_one_le_sin (l * 3.141593 / 180)], hx⟩).2 h
  rw [lt_div_iff₀ pi_pos]
  nlinarith [mul_lt_mul_of_pos_left pi_lt_d6 hl]

/-- Upper bound in degrees: if `x < sin (u · 3.141592 / 180)`, then `arcsin x` is below `u`
degrees. -/
theorem arcsin_deg_lt {x u : ℝ} (hu : 0 < u) (hu' : u ≤ 89) (hx : -1 ≤ x)
    (h : x < sin (u * 3.141592 / 180)) : arcsin x * 180 / π < u := by
  have hπ := pi_gt_d6
  have ht : u * 3.141592 / 180 ∈ Icc (-(π / 2)) (π / 2) := ⟨by linarith, by linarith⟩
  have h1 := (arcsin_lt_iff_lt_sin ⟨hx, by linarith [sin_le_one (u * 3.141592 / 180)]⟩ ht).2 h
  rw [div_lt_iff₀ pi_pos]
  nlinarith [mul_lt_mul_of_pos_left pi_gt_d6 hu]

/-- **Hipparchus' lunar anomaly.** The lunar pin-and-slot (`r = 9.6`, `e = 1.1`) swings the Moon
pointer by at most `arcsin (1.1 / 9.6)`, which lies between `6.579°` and `6.581°`. -/
theorem lunar_amplitude_deg :
    6.579 < arcsin (1.1 / 9.6) * 180 / π ∧ arcsin (1.1 / 9.6) * 180 / π < 6.581 := by
  constructor
  · refine lt_arcsin_deg (by norm_num) (by norm_num) (by norm_num) ?_
    refine lt_of_le_of_lt (sin_le_taylor (by norm_num) (by norm_num)) ?_
    norm_num
  · refine arcsin_deg_lt (by norm_num) (by norm_num) (by norm_num) ?_
    refine lt_of_lt_of_le ?_ (taylor_le_sin (by norm_num))
    norm_num

/-- The lunar anomaly to 0.01°: `6.57° < arcsin (1.1 / 9.6) < 6.59°`. -/
theorem lunar_amplitude_deg' :
    6.57 < arcsin (1.1 / 9.6) * 180 / π ∧ arcsin (1.1 / 9.6) * 180 / π < 6.59 := by
  obtain ⟨h1, h2⟩ := lunar_amplitude_deg
  constructor <;> linarith

/-- The Saturn pin-and-slot (`r = 14.37`, `e = 1.5`) has amplitude between `5.99°` and `6.00°`. -/
theorem saturn_amplitude_deg :
    5.99 < arcsin (1.5 / 14.37) * 180 / π ∧ arcsin (1.5 / 14.37) * 180 / π < 6.00 := by
  constructor
  · refine lt_arcsin_deg (by norm_num) (by norm_num) (by norm_num) ?_
    refine lt_of_le_of_lt (sin_le_taylor (by norm_num) (by norm_num)) ?_
    norm_num
  · refine arcsin_deg_lt (by norm_num) (by norm_num) (by norm_num) ?_
    refine lt_of_lt_of_le ?_ (taylor_le_sin (by norm_num))
    norm_num

/-- The Jupiter pin-and-slot (`r = 8.22`, `e = 1.58`) has amplitude between `11.08°` and
`11.09°`. -/
theorem jupiter_amplitude_deg :
    11.08 < arcsin (1.58 / 8.22) * 180 / π ∧ arcsin (1.58 / 8.22) * 180 / π < 11.09 := by
  constructor
  · refine lt_arcsin_deg (by norm_num) (by norm_num) (by norm_num) ?_
    refine lt_of_le_of_lt (sin_le_taylor (by norm_num) (by norm_num)) ?_
    norm_num
  · refine arcsin_deg_lt (by norm_num) (by norm_num) (by norm_num) ?_
    refine lt_of_lt_of_le ?_ (taylor_le_sin (by norm_num))
    norm_num

/-- The Mars pin-and-slot (`r = 10.0`, `e = 6.58`) has a large amplitude, between `41.1°` and
`41.2°`. -/
theorem mars_amplitude_deg :
    41.1 < arcsin (6.58 / 10.0) * 180 / π ∧ arcsin (6.58 / 10.0) * 180 / π < 41.2 := by
  constructor
  · refine lt_arcsin_deg (by norm_num) (by norm_num) (by norm_num) ?_
    refine lt_of_le_of_lt (sin_le_double (by norm_num) (by norm_num)) ?_
    norm_num
  · refine arcsin_deg_lt (by norm_num) (by norm_num) (by norm_num) ?_
    refine lt_of_lt_of_le ?_ (double_le_sin (by norm_num) (by norm_num))
    norm_num

/-- The Mercury follower (`i = 36.0`, `d = 14.04`) has greatest elongation `arcsin (14.04 / 36)`,
between `22.9°` and `23.0°`. -/
theorem mercury_amplitude_deg :
    22.9 < arcsin (14.04 / 36.0) * 180 / π ∧ arcsin (14.04 / 36.0) * 180 / π < 23.0 := by
  constructor
  · refine lt_arcsin_deg (by norm_num) (by norm_num) (by norm_num) ?_
    refine lt_of_le_of_lt (sin_le_taylor (by norm_num) (by norm_num)) ?_
    norm_num
  · refine arcsin_deg_lt (by norm_num) (by norm_num) (by norm_num) ?_
    refine lt_of_lt_of_le ?_ (taylor_le_sin (by norm_num))
    norm_num

/-- The Venus follower (`i = 27.8`, `d = 20.01`) has greatest elongation `arcsin (20.01 / 27.8)`,
between `46.0°` and `46.1°`. -/
theorem venus_amplitude_deg :
    46.0 < arcsin (20.01 / 27.8) * 180 / π ∧ arcsin (20.01 / 27.8) * 180 / π < 46.1 := by
  constructor
  · refine lt_arcsin_deg (by norm_num) (by norm_num) (by norm_num) ?_
    refine lt_of_le_of_lt (sin_le_double (by norm_num) (by norm_num)) ?_
    norm_num
  · refine arcsin_deg_lt (by norm_num) (by norm_num) (by norm_num) ?_
    refine lt_of_lt_of_le ?_ (double_le_sin (by norm_num) (by norm_num))
    norm_num

/-- The true-Sun follower (`i = 39.711744`, `d = 1.654656`) gives an equation of centre of at most
`arcsin (1.654656 / 39.711744)`, between `2.38°` and `2.39°`. -/
theorem trueSun_amplitude_deg :
    2.38 < arcsin (1.654656 / 39.711744) * 180 / π ∧
      arcsin (1.654656 / 39.711744) * 180 / π < 2.39 := by
  constructor
  · refine lt_arcsin_deg (by norm_num) (by norm_num) (by norm_num) ?_
    refine lt_of_le_of_lt (sin_le_taylor (by norm_num) (by norm_num)) ?_
    norm_num
  · refine arcsin_deg_lt (by norm_num) (by norm_num) (by norm_num) ?_
    refine lt_of_lt_of_le ?_ (taylor_le_sin (by norm_num))
    norm_num

/-! ## 6. The link with `Kinematics`

`Kinematics ω` counts turns per year, clockwise positive; the spec laws use radians,
counterclockwise positive. A body with `Kinematics` rate `ω x` has mean angular rate
`-2π · ω x`. -/

/-- Mean angular rates `-2π · a` and `-2π · b` are equal only if the rates `a` and `b` in turns per
year are equal. -/
theorem eq_of_neg_two_pi_mul {a b : ℝ} (h : -(2 * π) * a = -(2 * π) * b) : a = b :=
  mul_left_cancel₀ (neg_ne_zero.2 (mul_ne_zero two_ne_zero pi_ne_zero)) h

/-- **The seven nonlinear fields of `Kinematics` follow from the spec laws.** Let `θ x t` be the
angle (radians, counterclockwise seen from the front) of body `x` at time `t` (years), and let
every body turn at mean rate `-2π · ω x`. Suppose the four pin-and-slot laws hold (spec
`conventions.pin_slot_formula`, dimensions of `pin_slots`, any offset directions), and so do the
three follower laws (spec `conventions.follower_formula`, dimensions of `followers`, any constants
`g₀`, any pin phases). Then `ω` satisfies the fields `pinslot_lunar`, `pinslot_saturn`,
`pinslot_jupiter`, `pinslot_mars`, `follower_mercury`, `follower_venus` and `follower_trueSun`. -/
theorem kinematics_nonlinear_fields (ω : Body → ℝ) (θ : Body → ℝ → ℝ)
    (hθ : ∀ x, HasMeanRate (θ x) (-(2 * π) * ω x))
    {βL βS βJ βM gMe gVe gSu : ℝ} {ψMe ψVe ψSu : ℝ → ℝ}
    (hL : ∀ t, θ .kp t = θ .e_table t + slotAngle 9.6 1.1 βL (θ .k t - θ .e_table t))
    (hS : ∀ t, θ .x_sa86s t = θ .b t + slotAngle 14.37 1.5 βS (θ .x_sa68 t - θ .b t))
    (hJ : ∀ t, θ .x_ju65s t = θ .b t + slotAngle 8.22 1.58 βJ (θ .x_ju43 t - θ .b t))
    (hM : ∀ t, θ .x_ma80s t = θ .b t + slotAngle 10.0 6.58 βM (θ .x_ma71 t - θ .b t))
    (hMe : ∀ t, θ .t_mercury t = followerAngle 36.0 14.04 gMe (θ .b t) (ψMe t))
    (hVe : ∀ t, θ .t_venus t = followerAngle 27.8 20.01 gVe (θ .b t) (ψVe t))
    (hSu : ∀ t, θ .t_trueSun t = followerAngle 39.711744 1.654656 gSu (θ .b t) (ψSu t)) :
    ω .kp = ω .k ∧ ω .x_sa86s = ω .x_sa68 ∧ ω .x_ju65s = ω .x_ju43 ∧ ω .x_ma80s = ω .x_ma71 ∧
      ω .t_mercury = ω .b ∧ ω .t_venus = ω .b ∧ ω .t_trueSun = ω .b := by
  have pin : ∀ {pinGear slotGear carrier : Body} {r e β : ℝ}, 0 ≤ e → e < r →
      (∀ t, θ slotGear t = θ carrier t + slotAngle r e β (θ pinGear t - θ carrier t)) →
      ω slotGear = ω pinGear :=
    fun he her hlaw => eq_of_neg_two_pi_mul
      (pinSlot_meanRate_eq (abs_lt_of_nonneg_of_lt he her) hlaw (hθ _) (hθ _))
  have fol : ∀ {follower : Body} {i d g₀ : ℝ} {ψ : ℝ → ℝ}, 0 ≤ d → d < i →
      (∀ t, θ follower t = followerAngle i d g₀ (θ .b t) (ψ t)) → ω follower = ω .b :=
    fun hd hdi hlaw => eq_of_neg_two_pi_mul
      (follower_meanRate_eq (abs_lt_of_nonneg_of_lt hd hdi) hlaw (hθ _) (hθ _))
  exact ⟨pin (by norm_num) (by norm_num) hL, pin (by norm_num) (by norm_num) hS,
    pin (by norm_num) (by norm_num) hJ, pin (by norm_num) (by norm_num) hM,
    fol (by norm_num) (by norm_num) hMe, fol (by norm_num) (by norm_num) hVe,
    fol (by norm_num) (by norm_num) hSu⟩

end Antikythera.PinSlot
