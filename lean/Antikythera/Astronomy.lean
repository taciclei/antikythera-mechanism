import Antikythera.Kinematics

/-!
# The astronomy of the Antikythera Mechanism

The theorems below state what the gearing *computes*, for **any** rate vector `ω` satisfying the
gear-contact constraints `Kinematics ω` (the proofs use `determined` or single gear contacts, never
a numerical choice of crank speed). Rates are mean rates in turns per year, positive = clockwise
seen from the front (so a negative rate on a back-dial pointer means clockwise seen from the back).

* Exact cycle theorems (sections `Crank`, `SunAndMoon`, `LunarAnomaly`, `BackDials`,
  `LunarNodes`, `Planets`) are homogeneous linear identities: they hold whatever the speed and
  sense in which the crank is turned, so they never assume `ω .b = 1`. The two sense-of-rotation
  theorems (`olympiad_counter_rotates`, `dragon_hand_retrograde`) only assume that the crank
  moves (`ω .b ≠ 0`).
* Accuracy theorems (section `Accuracy`) compare the periods implied by the gearing with modern
  values (spec `reference_values_days`). They are the only statements about days, so they add the
  hypothesis `ω .b = 1` (b1 makes one turn per tropical year) and take 1 tropical year =
  365.2422 days. A body turning at `r` turns per year has period `365.2422 / |r|` days.

Sources:
* Price 1974: D. J. de Solla Price, *Gears from the Greeks*, Trans. Am. Philos. Soc. 64 (7).
* Freeth et al. 2006: *Decoding the ancient Greek astronomical calculator known as the Antikythera
  Mechanism*, Nature 444, 587–591.
* Freeth et al. 2008: *Calendars with Olympiad display and eclipse prediction on the Antikythera
  Mechanism*, Nature 454, 614–617.
* Freeth et al. 2021: *A model of the Cosmos in the ancient Greek Antikythera Mechanism*,
  Sci. Rep. 11, 5821. The Dragon Hand and all the planetary and true-Sun gearing come from this
  reconstruction and are **hypothetical**: no gear of those trains survives except r1. The
  mean-Sun input b0 of the Moon-phase crown pair is hypothetical as well (spec gear status).
-/

namespace Antikythera

/-! ## The crank -/
section Crank

/-- **Crank ratio.** The crown pinion a1 (48 teeth) on the hand crank drives the main wheel b1
(223 teeth): 223 crank turns advance the year wheel by 48 turns, so one crank turn moves the mean
Sun by 48/223 of a year (about 78.6 days). Source: b1 = 223 teeth from the X-ray CT of Freeth et
al. 2006 (Nature); a1 = 48 is the count adopted in this model (surviving gear, count uncertain). -/
theorem crank_ratio (ω : Body → ℝ) (h : Kinematics ω) : 48 * ω .a = 223 * ω .b :=
  h.crown_a1_b1

end Crank

/-! ## Sun and Moon on the front dial -/
section SunAndMoon

/-- **Sidereal month (254 in 19 years).** The Moon pointer makes 254 turns (sidereal months) while
b1 makes 19 (years): the train b2–c1, c2–d1, d2–e2, then e1–b3 through the 50:50 unit on e3,
has ratio (64/38)(48/24)(127/32) = 254/19, and d2 has the prime count 127 = 254/2.
Source: Price 1974 (who identified the 254/19 ratio); confirmed by Freeth et al. 2006 (Nature). -/
theorem sidereal_month_cycle (ω : Body → ℝ) (h : Kinematics ω) :
    19 * ω .moon = 254 * ω .b := by
  have d := determined ω h
  rw [d .moon]
  simp only [rate]
  ring

/-- **Metonic cycle (235 synodic months in 19 years).** The synodic rate of the Moon (its rate
relative to the mean Sun, `ω .moon - ω .b`) is 235/19 times the year: 254 sidereal months minus
the 19 turns of the Sun give 235 lunations in 19 years. Source: the Metonic relation read from
the gearing by Price 1974 and Freeth et al. 2006 (Nature). -/
theorem metonic_cycle (ω : Body → ℝ) (h : Kinematics ω) :
    19 * (ω .moon - ω .b) = 235 * ω .b := by
  have d := determined ω h
  rw [d .moon]
  simp only [rate]
  ring

/-- **Moon phase.** The half-silvered phase ball `q`, driven through the 20:20 crown pair b0–q1,
turns relative to the Moon pointer at exactly the synodic rate `ω .moon - ω .b`: one turn per
synodic month, i.e. one full cycle of phases per lunation. The mean-Sun input gear b0 is
hypothetical (spec gear status). Source: Freeth et al. 2006 (Nature); Freeth et al. 2021
(Sci. Rep.). -/
theorem moon_phase (ω : Body → ℝ) (h : Kinematics ω) : ω .q = ω .moon - ω .b := by
  linear_combination (1 / 20 : ℝ) * h.crown_b0_q1

/-- **Moon phase, 235 per 19 years.** Consequently the phase ball completes 235 cycles in 19 years
(one per synodic month). Source: Freeth et al. 2006 (Nature); Freeth et al. 2021 (Sci. Rep.). -/
theorem moon_phase_cycle (ω : Body → ℝ) (h : Kinematics ω) : 19 * ω .q = 235 * ω .b := by
  have d := determined ω h
  rw [d .q]
  simp only [rate]
  ring

end SunAndMoon

/-! ## Lunar anomaly: the pin-and-slot on the e3 turntable -/
section LunarAnomaly

/-- **The lunar input of the e3 turntable runs backwards.** The pin-and-slot unit on e3 takes its
input from e2 (driven by d2) and delivers its output through e1 (which drives the Moon pipe b3),
and in the mean both e2 and e1 turn at minus the Moon's rate.
This reversal is why the turntable e3 must turn *backwards* (see `apsidal_line`) to represent the
prograde motion of the lunar apsidal line. Source: Freeth et al. 2006 (Nature). -/
theorem lunar_train_reversed (ω : Body → ℝ) (h : Kinematics ω) :
    ω .e_pipe = -ω .moon ∧ ω .e_inner = -ω .moon := by
  have d := determined ω h
  rw [d .e_pipe, d .e_inner, d .moon]
  simp only [rate]
  constructor <;> ring

/-- **Lunar apsidal line (8.88 years).** The turntable e3 makes 477 turns in 4237 = 19·223 years,
i.e. one turn in 4237/477 ≈ 8.883 years, the period of the advance of the Moon's line of apsides.
Its rate is negative: it turns at the apsidal rate but in the reversed sense of the e2/e1 train
(`lunar_train_reversed`), so that the true, prograde apsidal rate is `-ω .e_table`.
Source: Freeth et al. 2006 (Nature). -/
theorem apsidal_line (ω : Body → ℝ) (h : Kinematics ω) :
    4237 * ω .e_table = -477 * ω .b := by
  have d := determined ω h
  rw [d .e_table]
  simp only [rate]
  ring

/-- **Anomalistic month.** The pin gear k1, relative to the turntable e3 that carries the
pin-and-slot, makes 56165 turns in 4237 years: one turn per anomalistic month (27.55 days), the
period of the Moon's variable speed that the pin-and-slot k1–k2 reproduces.
Source: Freeth et al. 2006 (Nature). -/
theorem anomalistic_month_cycle (ω : Body → ℝ) (h : Kinematics ω) :
    4237 * (ω .k - ω .e_table) = 56165 * ω .b := by
  have d := determined ω h
  rw [d .k, d .e_table]
  simp only [rate]
  ring

/-- **Anomalistic = sidereal minus apsidal.** The anomaly rate of the pin gear (k1 relative to e3)
equals the sidereal rate of the Moon minus the prograde apsidal rate `-ω .e_table`: the Moon comes
back to perigee a little later than to the same star because the perigee itself advances.
Written with the turntable's own (negative) rate this reads `ω .moon + ω .e_table`.
Source: Freeth et al. 2006 (Nature). -/
theorem anomalistic_eq_sidereal_sub_apsidal (ω : Body → ℝ) (h : Kinematics ω) :
    ω .k - ω .e_table = ω .moon + ω .e_table := by
  have d := determined ω h
  rw [d .k, d .e_table, d .moon]
  simp only [rate]
  ring

end LunarAnomaly

/-! ## The back dials: calendar and eclipse prediction -/
section BackDials

/-- **Metonic spiral.** The Metonic pointer turns 5 times (the 5 turns of the spiral) in 19 years;
its negative rate means clockwise seen from the back. Source: Freeth et al. 2006 (Nature);
month names and calendar: Freeth et al. 2008 (Nature). -/
theorem metonic_pointer (ω : Body → ℝ) (h : Kinematics ω) : 19 * ω .n = -5 * ω .b := by
  have d := determined ω h
  rw [d .n]
  simp only [rate]
  ring

/-- **Metonic spiral in months.** The Metonic pointer makes 5 turns per 235 synodic months: the
spiral of 235 month cells is traversed once per Metonic cycle. Source: Freeth et al. 2006
(Nature); Freeth et al. 2008 (Nature). -/
theorem metonic_pointer_months (ω : Body → ℝ) (h : Kinematics ω) :
    235 * ω .n = -5 * (ω .moon - ω .b) := by
  have d := determined ω h
  rw [d .n, d .moon]
  simp only [rate]
  ring

/-- **47 months per turn.** Each turn of the Metonic spiral spans 47 = 235/5 synodic months.
Source: Freeth et al. 2006 (Nature). -/
theorem metonic_months_per_turn (ω : Body → ℝ) (h : Kinematics ω) :
    47 * ω .n = -(ω .moon - ω .b) := by
  have d := determined ω h
  rw [d .n, d .moon]
  simp only [rate]
  ring

/-- **Saros spiral.** The Saros pointer makes 4 turns per 223 synodic months, the 18-year eclipse
cycle; its 4-turn spiral has 223 month cells carrying the eclipse glyphs. Source: Freeth et al.
2006 (Nature); eclipse glyphs: Freeth et al. 2008 (Nature). -/
theorem saros_pointer (ω : Body → ℝ) (h : Kinematics ω) :
    223 * ω .g = -4 * (ω .moon - ω .b) := by
  have d := determined ω h
  rw [d .g, d .moon]
  simp only [rate]
  ring

/-- **Exeligmos dial.** The Exeligmos pointer makes one turn per 669 synodic months = 3 Saros, the
whole-day eclipse cycle (the three sectors add 0, 8 and 16 hours to the Saros predictions).
Source: Freeth et al. 2006 (Nature). -/
theorem exeligmos_pointer (ω : Body → ℝ) (h : Kinematics ω) :
    669 * ω .i = -(ω .moon - ω .b) := by
  have d := determined ω h
  rw [d .i, d .moon]
  simp only [rate]
  ring

/-- **Exeligmos = 3 Saros.** The Saros pointer turns 12 times (3 Saros of 4 turns) while the
Exeligmos pointer turns once, in the same sense. Source: Freeth et al. 2006 (Nature). -/
theorem saros_eq_twelve_exeligmos (ω : Body → ℝ) (h : Kinematics ω) : ω .g = 12 * ω .i := by
  have d := determined ω h
  rw [d .g, d .i]
  simp only [rate]
  ring

/-- **Olympiad (Games) dial.** The Olympiad pointer turns once in 4 years, the cycle of the
Panhellenic games. Source: Freeth et al. 2008 (Nature). -/
theorem olympiad_pointer (ω : Body → ℝ) (h : Kinematics ω) : 4 * ω .o = ω .b := by
  have d := determined ω h
  rw [d .o]
  simp only [rate]
  ring

/-- **The Olympiad pointer turns the other way.** Whenever the crank moves, the Olympiad pointer
turns in the opposite sense to the Metonic pointer. When the crank is turned forward
(`ω .b > 0`) this means counterclockwise seen from the back, while the Metonic, Callippic, Saros
and Exeligmos pointers turn clockwise (their rates are negative: `metonic_pointer`,
`callippic_pointer`, `saros_pointer`, `exeligmos_pointer`). This matches the anticlockwise Games
dial reported by Freeth et al. 2008 (Nature). -/
theorem olympiad_counter_rotates (ω : Body → ℝ) (h : Kinematics ω) (hb : ω .b ≠ 0) :
    ω .o * ω .n < 0 := by
  have d := determined ω h
  rw [d .o, d .n]
  simp only [rate]
  nlinarith [sq_pos_of_ne_zero hb]

/-- **Callippic dial.** The Callippic pointer turns once in 76 years (4 Metonic cycles), clockwise
seen from the back. Source: Freeth et al. 2008 (Nature). -/
theorem callippic_pointer (ω : Body → ℝ) (h : Kinematics ω) : 76 * ω .cal = -ω .b := by
  have d := determined ω h
  rw [d .cal]
  simp only [rate]
  ring

/-- **Callippic cycle (940 synodic months in 76 years).** Callippus' cycle of four Metonic cycles:
76 years contain 940 synodic months (and 27 759 days, one day fewer than four Metonic cycles of
6940 days). Source: Freeth et al. 2008 (Nature). -/
theorem callippic_cycle (ω : Body → ℝ) (h : Kinematics ω) :
    76 * (ω .moon - ω .b) = 940 * ω .b := by
  have d := determined ω h
  rw [d .moon]
  simp only [rate]
  ring

/-- **Callippic = 4 Metonic.** The Metonic pointer makes 20 turns (4 passes of its 5-turn spiral)
per turn of the Callippic pointer. Source: Freeth et al. 2008 (Nature). -/
theorem metonic_eq_twenty_callippic (ω : Body → ℝ) (h : Kinematics ω) :
    ω .n = 20 * ω .cal := by
  have d := determined ω h
  rw [d .n, d .cal]
  simp only [rate]
  ring

end BackDials

/-! ## Lunar nodes: the Dragon Hand (hypothetical) -/
section LunarNodes

/-- **Dragon Hand (lunar nodes, 18.6 years).** The Dragon Hand turns 5 times in 93 years, i.e.
once in 18.6 years, with negative rate: the line of the Moon's nodes regresses (counterclockwise
seen from the front). Source: hypothetical (Freeth et al. 2021), Sci. Rep.; train fx49–nd62,
nd64–nd48 carried by b1. -/
theorem dragon_hand (ω : Body → ℝ) (h : Kinematics ω) : 93 * ω .t_nodes = -5 * ω .b := by
  have d := determined ω h
  rw [d .t_nodes]
  simp only [rate]
  ring

/-- **Nodes regress.** Whenever the crank moves, the Dragon Hand turns in the opposite sense to the
mean Sun (retrograde). Source: hypothetical (Freeth et al. 2021), Sci. Rep. -/
theorem dragon_hand_retrograde (ω : Body → ℝ) (h : Kinematics ω) (hb : ω .b ≠ 0) :
    ω .t_nodes * ω .b < 0 := by
  have d := determined ω h
  rw [d .t_nodes]
  simp only [rate]
  nlinarith [sq_pos_of_ne_zero hb]

/-- **Draconic month.** The Moon relative to the Dragon Hand (the Moon's return to the same node)
makes 23717 turns in 1767 = 19·93 years: one draconic month. An eclipse needs a new or full Moon
close to a node, so this month, together with the synodic month, decides which syzygies can be
eclipses. Source: derived from Price 1974 / Freeth et al. 2006 (Moon) and the hypothetical Dragon
Hand (Freeth et al. 2021). -/
theorem draconic_month_cycle (ω : Body → ℝ) (h : Kinematics ω) :
    1767 * (ω .moon - ω .t_nodes) = 23717 * ω .b := by
  have d := determined ω h
  rw [d .moon, d .t_nodes]
  simp only [rate]
  ring

end LunarNodes

/-! ## Planets and true Sun: hypothetical (Freeth et al. 2021) -/
section Planets

/-- **Mercury: 1513 synodic periods in 480 years.** The Mercury epicycle me20, relative to the
carrier b1 (the mean-Sun line), turns 1513 times in 480 years: one turn per synodic period.
Source: hypothetical (Freeth et al. 2021), Sci. Rep. (period relation derived there). -/
theorem mercury_synodic (ω : Body → ℝ) (h : Kinematics ω) :
    480 * (ω .x_me20 - ω .b) = 1513 * ω .b := by
  have d := determined ω h
  rw [d .x_me20]
  simp only [rate]
  ring

/-- **Venus: 289 synodic periods in 462 years.** The surviving gear r1 (63 teeth), as the Venus
epicycle, turns 289 times in 462 years relative to b1: one turn per synodic period (the 462-year
relation is read on the Front Cover Inscription). Source: hypothetical (Freeth et al. 2021),
Sci. Rep. -/
theorem venus_synodic (ω : Body → ℝ) (h : Kinematics ω) :
    462 * (ω .x_r1 - ω .b) = 289 * ω .b := by
  have d := determined ω h
  rw [d .x_r1]
  simp only [rate]
  ring

/-- **Mercury's mean longitude is the Sun's.** The Mercury pointer (a slotted follower on the
epicycle pin) has on average the rate of the mean Sun: an inferior planet only oscillates about
the Sun. Source: hypothetical (Freeth et al. 2021), Sci. Rep. -/
theorem mercury_mean_longitude (ω : Body → ℝ) (h : Kinematics ω) : ω .t_mercury = ω .b :=
  h.follower_mercury

/-- **Venus' mean longitude is the Sun's.** The Venus pointer has on average the rate of the mean
Sun. Source: hypothetical (Freeth et al. 2021), Sci. Rep. -/
theorem venus_mean_longitude (ω : Body → ℝ) (h : Kinematics ω) : ω .t_venus = ω .b :=
  h.follower_venus

/-- **The true-Sun epicycle only translates.** The fixed 56-tooth gear, the 52-tooth idler and the
56-tooth epicycle su56 cancel exactly: su56 does not turn at all, so its eccentric pin describes
an eccentric circle (Hipparchus' eccentric model of the solar anomaly). Source: hypothetical
(Freeth et al. 2021), Sci. Rep. The eccentricity e = 1/24 (Hipparchus' value) is a choice of
this model, not given by Freeth et al. 2021; the theorem does not depend on it. -/
theorem trueSun_epicycle_translates (ω : Body → ℝ) (h : Kinematics ω) : ω .x_su56 = 0 := by
  have d := determined ω h
  rw [d .x_su56]
  simp only [rate]
  ring

/-- **True Sun's mean longitude.** The true-Sun pointer turns on average with the mean Sun, once
per tropical year; it only oscillates about it (equation of centre). Source: hypothetical
(Freeth et al. 2021), Sci. Rep. -/
theorem trueSun_mean_longitude (ω : Body → ℝ) (h : Kinematics ω) : ω .t_trueSun = ω .b :=
  h.follower_trueSun

/-- **Mars: 133 synodic periods in 284 years.** The Mars pin gear ma71, relative to b1, turns 133
times in 284 years. Source: hypothetical (Freeth et al. 2021), Sci. Rep. -/
theorem mars_synodic (ω : Body → ℝ) (h : Kinematics ω) :
    284 * (ω .x_ma71 - ω .b) = 133 * ω .b := by
  have d := determined ω h
  rw [d .x_ma71]
  simp only [rate]
  ring

/-- **Mars: 151 sidereal periods in 284 years.** The Mars pointer makes 151 turns of the zodiac in
284 years (284 = 133 + 151). Source: hypothetical (Freeth et al. 2021), Sci. Rep. -/
theorem mars_sidereal (ω : Body → ℝ) (h : Kinematics ω) : 284 * ω .t_mars = 151 * ω .b := by
  have d := determined ω h
  rw [d .t_mars]
  simp only [rate]
  ring

/-- **Mars: sidereal = solar − synodic.** For a superior planet the synodic rate is the Sun's rate
minus the planet's; the Mars pointer turns at the mean Sun's rate minus that of its pin gear
relative to b1. Source: hypothetical (Freeth et al. 2021), Sci. Rep. -/
theorem mars_sidereal_eq_solar_sub_synodic (ω : Body → ℝ) (h : Kinematics ω) :
    ω .t_mars = ω .b - (ω .x_ma71 - ω .b) := by
  have d := determined ω h
  rw [d .t_mars, d .x_ma71]
  simp only [rate]
  ring

/-- **Jupiter: 315 synodic periods in 344 years.** The Jupiter pin gear ju43, relative to b1,
turns 315 times in 344 years. Source: hypothetical (Freeth et al. 2021), Sci. Rep. -/
theorem jupiter_synodic (ω : Body → ℝ) (h : Kinematics ω) :
    344 * (ω .x_ju43 - ω .b) = 315 * ω .b := by
  have d := determined ω h
  rw [d .x_ju43]
  simp only [rate]
  ring

/-- **Jupiter: 29 sidereal periods in 344 years.** The Jupiter pointer makes 29 turns of the zodiac
in 344 years (344 = 315 + 29). Source: hypothetical (Freeth et al. 2021), Sci. Rep. -/
theorem jupiter_sidereal (ω : Body → ℝ) (h : Kinematics ω) :
    344 * ω .t_jupiter = 29 * ω .b := by
  have d := determined ω h
  rw [d .t_jupiter]
  simp only [rate]
  ring

/-- **Jupiter: sidereal = solar − synodic.**
Source: hypothetical (Freeth et al. 2021), Sci. Rep. -/
theorem jupiter_sidereal_eq_solar_sub_synodic (ω : Body → ℝ) (h : Kinematics ω) :
    ω .t_jupiter = ω .b - (ω .x_ju43 - ω .b) := by
  have d := determined ω h
  rw [d .t_jupiter, d .x_ju43]
  simp only [rate]
  ring

/-- **Saturn: 427 synodic periods in 442 years.** The Saturn pin gear sa68, relative to b1, turns
427 times in 442 years (the 442-year relation is read on the Front Cover Inscription).
Source: hypothetical (Freeth et al. 2021), Sci. Rep. -/
theorem saturn_synodic (ω : Body → ℝ) (h : Kinematics ω) :
    442 * (ω .x_sa68 - ω .b) = 427 * ω .b := by
  have d := determined ω h
  rw [d .x_sa68]
  simp only [rate]
  ring

/-- **Saturn: 15 sidereal periods in 442 years.** The Saturn pointer makes 15 turns of the zodiac
in 442 years (442 = 427 + 15). Source: hypothetical (Freeth et al. 2021), Sci. Rep. -/
theorem saturn_sidereal (ω : Body → ℝ) (h : Kinematics ω) :
    442 * ω .t_saturn = 15 * ω .b := by
  have d := determined ω h
  rw [d .t_saturn]
  simp only [rate]
  ring

/-- **Saturn: sidereal = solar − synodic.**
Source: hypothetical (Freeth et al. 2021), Sci. Rep. -/
theorem saturn_sidereal_eq_solar_sub_synodic (ω : Body → ℝ) (h : Kinematics ω) :
    ω .t_saturn = ω .b - (ω .x_sa68 - ω .b) := by
  have d := determined ω h
  rw [d .t_saturn, d .x_sa68]
  simp only [rate]
  ring

end Planets

/-! ## Accuracy against modern astronomy

With b1 = 1 turn per tropical year of 365.2422 days (`ω .b = 1`), a body turning at `r` turns
per year has period `365.2422 / |r|` days. Reference values: spec `reference_values_days`. The
errors come from the ancient period relations themselves, which the gearing reproduces exactly.

Reference frames. Synodic periods and the anomalistic and draconic months are the same in every
frame. Periods counted against the zodiac (Moon pointer, Dragon Hand, apsidal line, planet
pointers) are not: because b1 is counted in tropical years, the like-for-like modern value is the
period relative to the equinox. The spec gives only sidereal periods for the planets and for the
lunar apsidal line. For the planets these exceed the tropical periods by about 0.05 day for
Mars, 2 days for Jupiter and 12 days for Saturn, and by 1.1 days for the apsidal line. So the
planetary sidereal-period bounds and `apsidal_period_days` compare a tropical-year count with a
sidereal period, and the same holds for `nodal_period_sidereal_days`. Their smallness for Jupiter
and for the nodes comes partly from mixing the two frames.
-/
section Accuracy

/-- **Sidereal month to 0.0005 day.** The Moon pointer's period, 19/254 year = 27.32127 days,
matches the modern sidereal month 27.321661 days within 0.0005 day (34 s). Source: Price 1974;
Freeth et al. 2006 (Nature). -/
theorem sidereal_month_days (ω : Body → ℝ) (h : Kinematics ω) (hb : ω .b = 1) :
    |365.2422 / ω .moon - 27.321661| < 0.0005 := by
  have d := determined ω h
  rw [d .moon, hb]
  norm_num [rate]

/-- **Tropical month to 0.0004 day.** The same period matches the tropical month 27.321582 days
within 0.0004 day: at this precision the gearing does not distinguish the two. Source: Price 1974;
Freeth et al. 2006 (Nature). -/
theorem tropical_month_days (ω : Body → ℝ) (h : Kinematics ω) (hb : ω .b = 1) :
    |365.2422 / ω .moon - 27.321582| < 0.0004 := by
  have d := determined ω h
  rw [d .moon, hb]
  norm_num [rate]

/-- **Synodic month to 0.0004 day.** The Moon-phase period, 19/235 year = 29.53022 days, matches
the modern synodic month 29.530589 days within 0.0004 day (32 s). Source: Freeth et al. 2006
(Nature). -/
theorem synodic_month_days (ω : Body → ℝ) (h : Kinematics ω) (hb : ω .b = 1) :
    |365.2422 / (ω .moon - ω .b) - 29.530589| < 0.0004 := by
  have d := determined ω h
  rw [d .moon, hb]
  norm_num [rate]

/-- **Metonic cycle to 0.09 day.** The 5 turns of the Metonic spiral last 19 tropical years
(6939.6018 days), against 235 modern synodic months (6939.6884 days): error below 0.09 day.
Source: Freeth et al. 2006 (Nature). -/
theorem metonic_cycle_days (ω : Body → ℝ) (h : Kinematics ω) (hb : ω .b = 1) :
    |5 * 365.2422 / |ω .n| - 6939.6884| < 0.09 := by
  have d := determined ω h
  rw [d .n, hb]
  norm_num [rate]

/-- **Saros to 0.09 day.** The 4 turns of the Saros spiral last 223 gear-synodic months
(6585.2392 days), against 223 modern synodic months (6585.3213 days): error below 0.09 day.
Source: Freeth et al. 2006 (Nature). -/
theorem saros_days (ω : Body → ℝ) (h : Kinematics ω) (hb : ω .b = 1) :
    |4 * 365.2422 / |ω .g| - 6585.3213| < 0.09 := by
  have d := determined ω h
  rw [d .g, hb]
  norm_num [rate]

/-- **Exeligmos to 0.25 day.** One turn of the Exeligmos pointer lasts 669 gear-synodic months
(19755.7175 days), against 19755.9639 days: error below 0.25 day. Source: Freeth et al. 2006
(Nature). -/
theorem exeligmos_days (ω : Body → ℝ) (h : Kinematics ω) (hb : ω .b = 1) :
    |365.2422 / |ω .i| - 19755.9639| < 0.25 := by
  have d := determined ω h
  rw [d .i, hb]
  norm_num [rate]

/-- **Callippic cycle to 0.35 day.** One turn of the Callippic pointer lasts 76 tropical years
(27758.4072 days), against 940 modern synodic months (27758.7536 days): error below 0.35 day.
Source: Freeth et al. 2008 (Nature). -/
theorem callippic_cycle_days (ω : Body → ℝ) (h : Kinematics ω) (hb : ω .b = 1) :
    |365.2422 / |ω .cal| - 27758.7536| < 0.35 := by
  have d := determined ω h
  rw [d .cal, hb]
  norm_num [rate]

/-- **Anomalistic month to 0.0013 day.** One turn of k1 relative to e3 lasts 4237/56165 year =
27.55330 days, against the modern anomalistic month 27.55455 days: error below 0.0013 day.
Source: Freeth et al. 2006 (Nature). -/
theorem anomalistic_month_days (ω : Body → ℝ) (h : Kinematics ω) (hb : ω .b = 1) :
    |365.2422 / (ω .k - ω .e_table) - 27.55455| < 0.0013 := by
  have d := determined ω h
  rw [d .k, d .e_table, hb]
  norm_num [rate]

/-- **Lunar apsidal period to 11.7 days.** One turn of the e3 turntable lasts 4237/477 years =
3244.30 days (8.883 years), against the modern apsidal period relative to the stars, 3232.6054
days (8.850 years): the gearing is 11.7 days (0.36 %) slow, the least accurate lunar period of
the mechanism. Against the period relative to the equinox, about 3231.5 days, it is about
12.8 days (0.40 %) slow (see the section header). Source: Freeth et al. 2006 (Nature). -/
theorem apsidal_period_days (ω : Body → ℝ) (h : Kinematics ω) (hb : ω .b = 1) :
    |365.2422 / |ω .e_table| - 3232.6054| < 11.7 := by
  have d := determined ω h
  rw [d .e_table, hb]
  norm_num [rate]

/-- **Nodal period (tropical) to 4.9 days.** One turn of the Dragon Hand lasts 93/5 years =
6793.505 days, against the modern regression of the nodes relative to the equinox, 6798.38 days:
error below 4.9 days (0.07 %). Source: hypothetical (Freeth et al. 2021), Sci. Rep. -/
theorem nodal_period_days (ω : Body → ℝ) (h : Kinematics ω) (hb : ω .b = 1) :
    |365.2422 / |ω .t_nodes| - 6798.38| < 4.9 := by
  have d := determined ω h
  rw [d .t_nodes, hb]
  norm_num [rate]

/-- **Nodal period (sidereal) to 0.025 day.** The same 6793.505 days (93/5 tropical years) lie
within 0.025 day of the regression of the nodes relative to the stars, 6793.48 days. This
closeness mixes frames (see the section header). Counted in sidereal years of 365.25636 days,
93/5 years are 6793.77 days, 0.29 day from the sidereal value. The like-for-like tropical
comparison is `nodal_period_days`. Source: hypothetical (Freeth et al. 2021), Sci. Rep. -/
theorem nodal_period_sidereal_days (ω : Body → ℝ) (h : Kinematics ω) (hb : ω .b = 1) :
    |365.2422 / |ω .t_nodes| - 6793.48| < 0.025 := by
  have d := determined ω h
  rw [d .t_nodes, hb]
  norm_num [rate]

/-- **Draconic month to 0.0004 day.** The Moon's period relative to the Dragon Hand,
1767/23717 year = 27.21183 days, matches the modern draconic month 27.212221 days within
0.0004 day. Source: derived; Dragon Hand hypothetical (Freeth et al. 2021), Sci. Rep. -/
theorem draconic_month_days (ω : Body → ℝ) (h : Kinematics ω) (hb : ω .b = 1) :
    |365.2422 / (ω .moon - ω .t_nodes) - 27.212221| < 0.0004 := by
  have d := determined ω h
  rw [d .moon, d .t_nodes, hb]
  norm_num [rate]

/-- **Mercury's synodic period to 0.007 day.** One turn of the Mercury epicycle relative to b1
lasts 480/1513 year = 115.8733 days, against 115.88 days. Source: hypothetical (Freeth et al.
2021), Sci. Rep. -/
theorem mercury_synodic_days (ω : Body → ℝ) (h : Kinematics ω) (hb : ω .b = 1) :
    |365.2422 / (ω .x_me20 - ω .b) - 115.88| < 0.007 := by
  have d := determined ω h
  rw [d .x_me20, hb]
  norm_num [rate]

/-- **Venus' synodic period to 0.04 day.** One turn of the Venus epicycle r1 relative to b1 lasts
462/289 year = 583.8820 days, against 583.92 days. Source: hypothetical (Freeth et al. 2021),
Sci. Rep. -/
theorem venus_synodic_days (ω : Body → ℝ) (h : Kinematics ω) (hb : ω .b = 1) :
    |365.2422 / (ω .x_r1 - ω .b) - 583.92| < 0.04 := by
  have d := determined ω h
  rw [d .x_r1, hb]
  norm_num [rate]

/-- **Mars' synodic period to 0.025 day.** The time between two conjunctions of the Mars pointer
with the mean Sun, 284/133 year = 779.9157 days, against 779.94 days. Source: hypothetical
(Freeth et al. 2021), Sci. Rep. -/
theorem mars_synodic_days (ω : Body → ℝ) (h : Kinematics ω) (hb : ω .b = 1) :
    |365.2422 / (ω .b - ω .t_mars) - 779.94| < 0.025 := by
  have d := determined ω h
  rw [d .t_mars, hb]
  norm_num [rate]

/-- **Jupiter's synodic period to 0.013 day.** The time between two conjunctions of the Jupiter
pointer with the mean Sun, 344/315 year = 398.8677 days, against 398.88 days. Source:
hypothetical (Freeth et al. 2021), Sci. Rep. -/
theorem jupiter_synodic_days (ω : Body → ℝ) (h : Kinematics ω) (hb : ω .b = 1) :
    |365.2422 / (ω .b - ω .t_jupiter) - 398.88| < 0.013 := by
  have d := determined ω h
  rw [d .t_jupiter, hb]
  norm_num [rate]

/-- **Saturn's synodic period to 0.018 day.** The time between two conjunctions of the Saturn
pointer with the mean Sun, 442/427 year = 378.0727 days, against 378.09 days. Source:
hypothetical (Freeth et al. 2021), Sci. Rep. -/
theorem saturn_synodic_days (ω : Body → ℝ) (h : Kinematics ω) (hb : ω .b = 1) :
    |365.2422 / (ω .b - ω .t_saturn) - 378.09| < 0.018 := by
  have d := determined ω h
  rw [d .t_saturn, hb]
  norm_num [rate]

/-- **Mars' sidereal period to 0.035 day.** One turn of the Mars pointer through the zodiac,
284/151 year = 686.9456 days, against the modern sidereal period 686.98 days (the tropical period,
about 686.93 days, is within 0.016 day). Source: hypothetical (Freeth et al. 2021), Sci. Rep. -/
theorem mars_sidereal_days (ω : Body → ℝ) (h : Kinematics ω) (hb : ω .b = 1) :
    |365.2422 / ω .t_mars - 686.98| < 0.035 := by
  have d := determined ω h
  rw [d .t_mars, hb]
  norm_num [rate]

/-- **Jupiter's sidereal period to 0.061 day.** One turn of the Jupiter pointer, 344/29 years =
4332.528 days, against the modern sidereal period 4332.589 days. The frames are mixed (see the
section header): against the tropical period, about 4330.6 days, the error is about 1.9 days.
Source: hypothetical (Freeth et al. 2021), Sci. Rep. -/
theorem jupiter_sidereal_days (ω : Body → ℝ) (h : Kinematics ω) (hb : ω .b = 1) :
    |365.2422 / ω .t_jupiter - 4332.589| < 0.061 := by
  have d := determined ω h
  rw [d .t_jupiter, hb]
  norm_num [rate]

/-- **Saturn's sidereal period to 3.3 days.** One turn of the Saturn pointer, 442/15 years =
10762.47 days, against the modern sidereal period 10759.22 days: 3.25 days (0.03 %) long. The
frames are mixed (see the section header): against the tropical period, about 10746.9 days, the
gearing is about 15.5 days (0.14 %) long. Source: hypothetical (Freeth et al. 2021), Sci. Rep. -/
theorem saturn_sidereal_days (ω : Body → ℝ) (h : Kinematics ω) (hb : ω .b = 1) :
    |365.2422 / ω .t_saturn - 10759.22| < 3.3 := by
  have d := determined ω h
  rw [d .t_saturn, hb]
  norm_num [rate]

end Accuracy

end Antikythera
