-- ÉCRIT À LA MAIN (pas généré). `v2/tools/make_lean_v2.py` le lit (compte de ses théorèmes, mots interdits),
-- le recopie avec le paquet et l'importe dans `AnticythereV2.lean` et `AnticythereV2/Audit.lean`.

import Mathlib

/-!
# Mécanismes non linéaires d'Anticythère 2.0 : les identités exactes

Les fichiers générés (`Kinematics`, `Ratios`, `Rates`, …) ne parlent que de vitesses MOYENNES : une unité de
Kepler, un module vectoriel ou un joint de Hooke y fait « un tour par tour ». Ce fichier, écrit à la main sur le
modèle de `lean/Antikythera/PinSlot.lean` (v1), prouve les identités géométriques exactes sur lesquelles reposent
ces mécanismes (`v2/research/mechanisms.md` § 1.2, § 2.3, § 4.5, § 8 ; `v2/tools/kepler/CONTRACT.md`).

1. **Module vectoriel** (§ 2.3) : `module_exterieur`, `module_interieur` (G − O = s·(planète − Terre), le pivot
   du suiveur étant en O = P₁ + s·(C_T − C_p)), `suiveur_geocentrique` (le suiveur en O lit la longitude
   géocentrique), `pivot_heliocentrique` (F = P₁ − s·C_p), `ecart_pivots` (O − F = s·C_T) et `chaine_un_un`
   (la chaîne 1:1 le long du bras conserve l'angle absolu).
2. **Ellipse à deux bras contrarotatifs** (§ 1.2 e) : `deux_bras` (((a+b)/2)·u(ϖ+E) + ((a−b)/2)·u(ϖ−E) =
   rot ϖ (a cos E, b sin E)), `deux_bras_mem_ellipse`, `deux_bras_dist_foyer` (distance au foyer a(1 − e cos E)).
3. **Résolveur de Kepler** (§ 1.2 e) : `kepler_existsUnique` (∀ M ∃! E, E − e sin E = M pour 0 ≤ e < 1),
   `kepler_strictMono`, `kepler_surjective`, `kepler_deriv_mem` (dM/dE = 1 − e cos E ∈ [1 − e, 1 + e]),
   `kepler_inv_deriv_mem` (dE/dM ∈ [1/(1 + e), 1/(1 − e)]), `kepler_solution` (la solution est continue,
   strictement croissante, lipschitzienne et dérivable), `boucle_resolveur` et `boucle_resolveur_existsUnique`
   (coulisse écossaise + crémaillère + différentiel ⟺ équation de Kepler, un seul état par M),
   `resolveur_mercure` (valeurs d'exemple 3,084 mm / 15 mm).
4. **Équant bissecté** (§ 1.2 b) : `equant_rayon_unique` (toute demi-droite issue du point équant Q coupe le
   cercle en un seul point), `equant_point`, `tEquant_continuous`, `equant_goupille_continuous` (la goupille est
   définie et se déplace continûment à chaque instant).
5. **Accouplement d'Oldham** : `parallele_iff` (directions parallèles ⟺ angles égaux modulo π),
   `oldham_modulo_pi` (les deux arbres ont la même rotation modulo π), `eq_of_modulo_pi_of_continuous` et
   `oldham_meme_rotation` (même rotation, par continuité depuis l'égalité), `oldham_centre_cercle` (le disque
   intermédiaire décrit le cercle de diamètre O₁O₂).
6. **Joint de Hooke** (§ 4.5) : `hooke_geometrie` (le modèle dans ℝ³), `hooke_croisillon` (branches du croisillon
   perpendiculaires ⟺ sin φ cos λ = cos ε cos φ sin λ), `hooke_tan` (tan φ = cos ε tan λ),
   `ascensionDroite_relation` et `ascensionDroite_existe` (tan α = cos ε tan λ, réduction à l'équateur),
   `hooke_ascensionDroite_modulo_pi`, `hooke_egale_ascensionDroite` (la sortie du joint calé est l'ascension droite).

Lemmes de géométrie plane : `deucl_eq_dist`, `nsq_u`, `u_add_pi`, `deucl_eq_iff`, `nsq_rot`, `rot_neg_rot`,
`rot_sub`, `nsq_add_smul_u`, `cross_u`.

## Conventions

Plan : `ℝ × ℝ`, angles en radians dans le sens trigonométrique, `u φ = (cos φ, sin φ)`. Le contrat des tours de
Kepler dessine une longitude λ en `(sin λ, cos λ)` (CONTRACT § 3) : c'est l'image de `u λ` par la symétrie
d'axe x = y, isométrie linéaire qui conserve les identités vectorielles et les distances ci-dessous. La norme de
`ℝ × ℝ` dans Mathlib est la norme sup : la norme euclidienne est donc écrite explicitement (`nsq`, `deucl`), et
`deucl_eq_dist` la relie à la distance de `WithLp 2 (ℝ × ℝ)`, le plan euclidien de Mathlib.

## Ce qui n'est pas prouvé ici

Les longueurs et angles numériques des pièces (`v2/spec/kepler.json`), les collisions et les jeux restent du
ressort des contrôles Python (`v2/tools/kepler/verify.py`). Les mécanismes sont idéalisés : goupilles
ponctuelles, rainures et languettes sans jeu, roulement sans glissement. Ne sont pas formalisés : l'équant comme
goupille-rainure menée (monotonie stricte de la manivelle, vitesse moyenne, écart borné, analogue de
`isGreatest_abs_lag` en v1), l'épicyclet correcteur de Mars (EQE) et le lien avec les vitesses de `Kinematics`.
-/

namespace AnticythereV2.Mechanisms

open Real

noncomputable section

/-! ## 0. Le plan euclidien -/

/-- Vecteur unitaire d'angle `φ` (radians, sens trigonométrique) : `u φ = (cos φ, sin φ)`. -/
def u (φ : ℝ) : ℝ × ℝ := (cos φ, sin φ)

/-- Carré de la norme euclidienne d'un vecteur du plan. -/
def nsq (v : ℝ × ℝ) : ℝ := v.1 ^ 2 + v.2 ^ 2

/-- Distance euclidienne de deux points du plan. -/
def deucl (P Q : ℝ × ℝ) : ℝ := √(nsq (P - Q))

/-- Produit scalaire du plan. -/
def dot (v w : ℝ × ℝ) : ℝ := v.1 * w.1 + v.2 * w.2

/-- Produit vectoriel du plan (déterminant) : nul si et seulement si les deux vecteurs sont parallèles. -/
def cross (v w : ℝ × ℝ) : ℝ := v.1 * w.2 - v.2 * w.1

/-- Rotation d'angle `ϖ` du plan. -/
def rot (ϖ : ℝ) (v : ℝ × ℝ) : ℝ × ℝ := (cos ϖ * v.1 - sin ϖ * v.2, sin ϖ * v.1 + cos ϖ * v.2)

/-- `deucl` est la distance du plan euclidien de Mathlib (`WithLp 2 (ℝ × ℝ)`, norme L²). -/
theorem deucl_eq_dist (P Q : ℝ × ℝ) : deucl P Q = dist (WithLp.toLp 2 P) (WithLp.toLp 2 Q) := by
  rw [WithLp.prod_dist_eq_of_L2]
  simp [deucl, nsq, Real.dist_eq, sq_abs]

/-- Le vecteur `u φ` est unitaire. -/
theorem nsq_u (φ : ℝ) : nsq (u φ) = 1 := by
  simp only [nsq, u]
  exact cos_sq_add_sin_sq φ

/-- Retourner un bras de 180° change son vecteur de signe : `u (φ + π) = -u φ`. -/
theorem u_add_pi (φ : ℝ) : u (φ + π) = -u φ := by
  ext <;> simp [u, cos_add_pi, sin_add_pi]

/-- Critère de distance : pour `r ≥ 0`, `deucl P Q = r` équivaut à `|P − Q|² = r²`. -/
theorem deucl_eq_iff {P Q : ℝ × ℝ} {r : ℝ} (hr : 0 ≤ r) : deucl P Q = r ↔ nsq (P - Q) = r ^ 2 := by
  have h0 : 0 ≤ nsq (P - Q) := by unfold nsq; positivity
  rw [deucl, Real.sqrt_eq_iff_mul_self_eq h0 hr, sq]

/-- Une rotation conserve la norme : `|rot ϖ v|² = |v|²`. -/
theorem nsq_rot (ϖ : ℝ) (v : ℝ × ℝ) : nsq (rot ϖ v) = nsq v := by
  simp only [nsq, rot]
  linear_combination (v.1 ^ 2 + v.2 ^ 2) * sin_sq_add_cos_sq ϖ

/-- La rotation d'angle `-ϖ` défait la rotation d'angle `ϖ`. -/
theorem rot_neg_rot (ϖ : ℝ) (v : ℝ × ℝ) : rot (-ϖ) (rot ϖ v) = v := by
  ext
  · simp only [rot, cos_neg, sin_neg]
    linear_combination v.1 * sin_sq_add_cos_sq ϖ
  · simp only [rot, cos_neg, sin_neg]
    linear_combination v.2 * sin_sq_add_cos_sq ϖ

/-- Une rotation est linéaire : `rot ϖ v − rot ϖ w = rot ϖ (v − w)`. -/
theorem rot_sub (ϖ : ℝ) (v w : ℝ × ℝ) : rot ϖ v - rot ϖ w = rot ϖ (v - w) := by
  ext <;> simp only [rot, Prod.fst_sub, Prod.snd_sub] <;> ring

/-! ## 1. Le module vectoriel (§ 2.3)

Chaque module est un orrery réduit à deux vecteurs, à l'échelle `s` (mm/ua). La position vraie d'une planète, au
modèle d'équant près, est `C_p + a_p·u φ_p` (centre `C_p` de son orbite excentrique, rayon `a_p`, angle de
manivelle `φ_p` de son unité de Kepler) ; de même pour la Terre. Le bras 1 part du pivot fixe `P₁`, le bras 2 est
porté au bout du bras 1 ; la goupille `G` est au bout du bras 2. -/

/-- **Module vectoriel, planète extérieure** (Mars à Neptune). Bras 1 = vecteur héliocentrique de la planète
(longueur s·a_p, angle φ_p), bras 2 = vecteur Terre → Soleil (longueur s·a_T, angle φ_T + π). Avec le pivot du
suiveur en `O = P₁ + s·(C_T − C_p)`, on a exactement `G − O = s·(planète − Terre)`. -/
theorem module_exterieur {s a_p a_T φ_p φ_T : ℝ} {P₁ C_p C_T planete terre G O : ℝ × ℝ}
    (h_planete : planete = C_p + a_p • u φ_p) (h_terre : terre = C_T + a_T • u φ_T)
    (hG : G = P₁ + (s * a_p) • u φ_p + (s * a_T) • u (φ_T + π))
    (hO : O = P₁ + s • (C_T - C_p)) :
    G - O = s • (planete - terre) := by
  subst h_planete h_terre hG hO
  rw [u_add_pi]
  module

/-- **Module vectoriel, planète intérieure** (Mercure, Vénus) : les bras sont échangés, le bras 1 est le Soleil
(s·a_T, φ_T + π) et le bras 2 la planète (s·a_p, φ_p). Même pivot, même identité `G − O = s·(planète − Terre)`. -/
theorem module_interieur {s a_p a_T φ_p φ_T : ℝ} {P₁ C_p C_T planete terre G O : ℝ × ℝ}
    (h_planete : planete = C_p + a_p • u φ_p) (h_terre : terre = C_T + a_T • u φ_T)
    (hG : G = P₁ + (s * a_T) • u (φ_T + π) + (s * a_p) • u φ_p)
    (hO : O = P₁ + s • (C_T - C_p)) :
    G - O = s • (planete - terre) := by
  subst h_planete h_terre hG hO
  rw [u_add_pi]
  module

/-- **Le suiveur en O lit la longitude géocentrique.** Si `G − O = s·(planète − Terre)` avec `s > 0`, la rainure
du suiveur pivoté en O passe par G à l'angle θ et à la distance r (G − O = r·u θ) exactement quand la planète est
vue de la Terre dans la direction θ, à la distance r / s. -/
theorem suiveur_geocentrique {s r θ : ℝ} {planete terre G O : ℝ × ℝ} (hs : 0 < s)
    (h : G - O = s • (planete - terre)) :
    G - O = r • u θ ↔ planete - terre = (r / s) • u θ := by
  rw [h]
  constructor
  · intro h'
    rw [div_eq_inv_mul, mul_smul, ← h', smul_smul, inv_mul_cancel₀ hs.ne', one_smul]
  · intro h'
    rw [h', smul_smul, mul_div_cancel₀ r hs.ne']

/-- **Pivot héliocentrique** (planète extérieure) : avec le Soleil du module au point fixe `F = P₁ − s·C_p`, le
bout du bras 1 vérifie `(P₁ + s·a_p·u φ_p) − F = s·(planète − Soleil)`, le Soleil étant à l'origine. -/
theorem pivot_heliocentrique {s a_p φ_p : ℝ} {P₁ C_p planete soleil F : ℝ × ℝ}
    (h_planete : planete = C_p + a_p • u φ_p) (h_soleil : soleil = 0) (hF : F = P₁ - s • C_p) :
    (P₁ + (s * a_p) • u φ_p) - F = s • (planete - soleil) := by
  subst h_planete h_soleil hF
  module

/-- Les deux pivots des suiveurs sont décalés de `O − F = s·C_T` (de 0,03 à 0,4 mm selon les modules). -/
theorem ecart_pivots {s : ℝ} {P₁ C_p C_T O F : ℝ × ℝ}
    (hO : O = P₁ + s • (C_T - C_p)) (hF : F = P₁ - s • C_p) : O - F = s • C_T := by
  subst hO hF
  module

/-- **La chaîne 1:1 le long du bras conserve l'angle absolu.** Roue de `z` dents sur le tube en P₁ (angle absolu
α₀), pignon fou de `z_f` dents sur le bras (angle θ), roue de `z` dents au bout (angle absolu α₂). Formule de
Willis relativement au bras (deux engrènements extérieurs) : α₂ − θ = (−z/z_f)·(−z_f/z)·(α₀ − θ). Alors α₂ = α₀,
quel que soit l'angle du bras. -/
theorem chaine_un_un {z z_f α₀ α₂ θ : ℝ} (hz : z ≠ 0) (hf : z_f ≠ 0)
    (hW : α₂ - θ = (-(z / z_f)) * (-(z_f / z)) * (α₀ - θ)) : α₂ = α₀ := by
  have h1 : (-(z / z_f)) * (-(z_f / z)) = 1 := by field_simp
  rw [h1, one_mul] at hW
  linarith

/-! ## 2. L'ellipse par deux bras contrarotatifs (§ 1.2 e, Mercure)

Deux bras centrés au centre de l'ellipse : `(a + b)/2` à l'angle `ϖ + E` et `(a − b)/2` à l'angle `ϖ − E`. -/

/-- **Deux bras contrarotatifs** : `((a+b)/2)·u(ϖ+E) + ((a−b)/2)·u(ϖ−E) = rot ϖ (a cos E, b sin E)`. -/
theorem deux_bras (a b ϖ E : ℝ) :
    ((a + b) / 2) • u (ϖ + E) + ((a - b) / 2) • u (ϖ - E) = rot ϖ (a * cos E, b * sin E) := by
  ext <;> simp [u, rot, cos_add, sin_add, cos_sub, sin_sub] <;> ring

/-- L'ellipse de demi-axes `a` (le long de la direction `ϖ`) et `b`, centrée à l'origine, tournée de `ϖ` : les
points dont les coordonnées dans le repère des apsides, `(x, y) = rot (−ϖ) P`, vérifient `(x/a)² + (y/b)² = 1`. -/
def ellipse (a b ϖ : ℝ) : Set (ℝ × ℝ) :=
  {P | ((rot (-ϖ) P).1 / a) ^ 2 + ((rot (-ϖ) P).2 / b) ^ 2 = 1}

/-- Le point des deux bras est sur l'ellipse de demi-axes `a`, `b` tournée de `ϖ`, pour toute anomalie `E`. -/
theorem deux_bras_mem_ellipse {a b : ℝ} (ha : a ≠ 0) (hb : b ≠ 0) (ϖ E : ℝ) :
    ((a + b) / 2) • u (ϖ + E) + ((a - b) / 2) • u (ϖ - E) ∈ ellipse a b ϖ := by
  rw [deux_bras]
  simp only [ellipse, Set.mem_ofPred_eq, rot_neg_rot]
  rw [mul_div_cancel_left₀ _ ha, mul_div_cancel_left₀ _ hb]
  exact cos_sq_add_sin_sq E

/-- **Distance au foyer** : avec `c = a·e` et `b² = a²(1 − e²)` (0 ≤ e ≤ 1, a ≥ 0), le foyer côté périhélie est
`rot ϖ (c, 0)`, et le point des deux bras en est à la distance `a(1 − e cos E)` : la loi r = a(1 − e cos E). -/
theorem deux_bras_dist_foyer {a b c e : ℝ} (ha : 0 ≤ a) (he0 : 0 ≤ e) (he1 : e ≤ 1)
    (hc : c = a * e) (hb : b ^ 2 = a ^ 2 * (1 - e ^ 2)) (ϖ E : ℝ) :
    deucl (((a + b) / 2) • u (ϖ + E) + ((a - b) / 2) • u (ϖ - E)) (rot ϖ (c, 0)) = a * (1 - e * cos E) := by
  have hpos : 0 ≤ a * (1 - e * cos E) := by
    apply mul_nonneg ha
    nlinarith [cos_le_one E, mul_le_mul_of_nonneg_left (cos_le_one E) he0]
  rw [deux_bras, deucl_eq_iff hpos, rot_sub, nsq_rot]
  simp only [nsq, Prod.fst_sub, Prod.snd_sub, sub_zero, hc]
  linear_combination (sin E) ^ 2 * hb + (a ^ 2 - a ^ 2 * e ^ 2) * cos_sq_add_sin_sq E

/-! ## 3. Le résolveur de Kepler (§ 1.2 e)

L'anomalie moyenne `M` (menée par le train du temps) et l'anomalie excentrique `E` sont liées par l'équation de
Kepler `M = E − e sin E`. Le résolveur ferme une boucle (coulisse écossaise, crémaillère, différentiel) qui
impose cette relation ; il faut qu'elle ait une solution et une seule, qui dépende continûment de `M`. -/

/-- La fonction de Kepler : `kepler e E = E − e sin E` (anomalie moyenne en fonction de l'anomalie excentrique). -/
def kepler (e E : ℝ) : ℝ := E - e * sin E

/-- Dérivée de la fonction de Kepler : `dM/dE = 1 − e cos E`. -/
theorem hasDerivAt_kepler (e E : ℝ) : HasDerivAt (kepler e) (1 - e * cos E) E :=
  (hasDerivAt_id' E).sub ((hasDerivAt_sin E).const_mul e)

/-- **Pas de point mort** : pour `e ≥ 0`, le facteur de transmission `dM/dE = 1 − e cos E` reste dans
`[1 − e, 1 + e]`. -/
theorem kepler_deriv_mem {e : ℝ} (he0 : 0 ≤ e) (E : ℝ) : 1 - e * cos E ∈ Set.Icc (1 - e) (1 + e) := by
  constructor
  · nlinarith [mul_le_mul_of_nonneg_left (cos_le_one E) he0]
  · nlinarith [mul_le_mul_of_nonneg_left (neg_one_le_cos E) he0]

/-- Pour `0 ≤ e < 1`, le facteur de transmission est strictement positif : `0 < 1 − e cos E`. -/
theorem kepler_deriv_pos {e : ℝ} (he0 : 0 ≤ e) (he1 : e < 1) (E : ℝ) : 0 < 1 - e * cos E := by
  have := (kepler_deriv_mem he0 E).1
  linarith

/-- Facteur de transmission inverse : `dE/dM = 1/(1 − e cos E) ∈ [1/(1 + e), 1/(1 − e)]` pour `0 ≤ e < 1`. -/
theorem kepler_inv_deriv_mem {e : ℝ} (he0 : 0 ≤ e) (he1 : e < 1) (E : ℝ) :
    (1 - e * cos E)⁻¹ ∈ Set.Icc (1 + e)⁻¹ (1 - e)⁻¹ :=
  ⟨inv_anti₀ (kepler_deriv_pos he0 he1 E) (kepler_deriv_mem he0 E).2,
    inv_anti₀ (sub_pos.2 he1) (kepler_deriv_mem he0 E).1⟩

/-- Encadrement des accroissements : pour `e ≥ 0` et `x ≤ y`,
`(1 − e)(y − x) ≤ M(y) − M(x) ≤ (1 + e)(y − x)`. -/
theorem kepler_sub_mem {e : ℝ} (he0 : 0 ≤ e) {x y : ℝ} (hxy : x ≤ y) :
    (1 - e) * (y - x) ≤ kepler e y - kepler e x ∧ kepler e y - kepler e x ≤ (1 + e) * (y - x) := by
  have h := abs_sin_sub_sin_le y x
  rw [abs_of_nonneg (sub_nonneg.2 hxy)] at h
  have h' := abs_le.1 h
  simp only [kepler]
  constructor
  · nlinarith [mul_le_mul_of_nonneg_left h'.2 he0]
  · nlinarith [mul_le_mul_of_nonneg_left h'.1 he0]

/-- `(1 − e)·|x − y| ≤ |M(x) − M(y)|` pour `e ≥ 0` : la réciproque du résolveur est `1/(1 − e)`-lipschitzienne. -/
theorem kepler_abs_sub_ge {e : ℝ} (he0 : 0 ≤ e) (x y : ℝ) :
    (1 - e) * |x - y| ≤ |kepler e x - kepler e y| := by
  have h1 : kepler e x - kepler e y = (x - y) - e * (sin x - sin y) := by simp only [kepler]; ring
  have h2 := abs_sub_abs_le_abs_sub (x - y) (e * (sin x - sin y))
  have h3 : |e * (sin x - sin y)| ≤ e * |x - y| := by
    rw [abs_mul, abs_of_nonneg he0]
    exact mul_le_mul_of_nonneg_left (abs_sin_sub_sin_le x y) he0
  rw [h1]
  nlinarith

/-- La fonction de Kepler est continue. -/
theorem kepler_continuous (e : ℝ) : Continuous (kepler e) := by
  unfold kepler
  fun_prop

/-- Pour `0 ≤ e < 1`, `E ↦ E − e sin E` est strictement croissante. -/
theorem kepler_strictMono {e : ℝ} (he0 : 0 ≤ e) (he1 : e < 1) : StrictMono (kepler e) := by
  intro x y hxy
  have h := (kepler_sub_mem he0 hxy.le).1
  nlinarith [mul_pos (sub_pos.2 he1) (sub_pos.2 hxy)]

/-- Pour `0 ≤ e ≤ 1`, `E ↦ E − e sin E` est surjective de ℝ sur ℝ (valeurs intermédiaires sur `[M − 1, M + 1]`). -/
theorem kepler_surjective {e : ℝ} (he0 : 0 ≤ e) (he1 : e ≤ 1) : Function.Surjective (kepler e) := by
  intro M
  have h1 : kepler e (M - 1) ≤ M := by
    simp only [kepler]
    nlinarith [mul_le_mul_of_nonneg_left (neg_one_le_sin (M - 1)) he0]
  have h2 : M ≤ kepler e (M + 1) := by
    simp only [kepler]
    nlinarith [mul_le_mul_of_nonneg_left (sin_le_one (M + 1)) he0]
  obtain ⟨E, -, hE⟩ := intermediate_value_Icc (by linarith : M - 1 ≤ M + 1)
    (kepler_continuous e).continuousOn ⟨h1, h2⟩
  exact ⟨E, hE⟩

/-- **Équation de Kepler** : pour `0 ≤ e < 1` et toute anomalie moyenne `M`, il existe une et une seule anomalie
excentrique `E` telle que `E − e sin E = M`. -/
theorem kepler_existsUnique {e : ℝ} (he0 : 0 ≤ e) (he1 : e < 1) (M : ℝ) : ∃! E : ℝ, E - e * sin E = M := by
  obtain ⟨E, hE⟩ := kepler_surjective he0 he1.le M
  exact ⟨E, hE, fun E' hE' => (kepler_strictMono he0 he1).injective (hE'.trans hE.symm)⟩

/-- **Le résolveur est un difféomorphisme croissant de ℝ.** Pour `0 ≤ e < 1`, la solution `g` de l'équation de
Kepler (`g M − e sin (g M) = M`) est l'inverse de `E ↦ E − e sin E` ; elle est strictement croissante,
`1/(1 − e)`-lipschitzienne (donc continue) et dérivable, de dérivée `dE/dM = 1/(1 − e cos E)`. -/
theorem kepler_solution {e : ℝ} (he0 : 0 ≤ e) (he1 : e < 1) :
    ∃ g : ℝ → ℝ, (∀ M, g M - e * sin (g M) = M) ∧ (∀ E, g (E - e * sin E) = E) ∧ StrictMono g ∧
      (∀ M₁ M₂, |g M₁ - g M₂| ≤ |M₁ - M₂| / (1 - e)) ∧ Continuous g ∧
      ∀ M, HasDerivAt g (1 - e * cos (g M))⁻¹ M := by
  have hm := kepler_strictMono he0 he1
  obtain ⟨g, hfg⟩ : ∃ g : ℝ → ℝ, ∀ M, kepler e (g M) = M :=
    ⟨_, Function.surjInv_eq (kepler_surjective he0 he1.le)⟩
  have hgf : ∀ E, g (kepler e E) = E := fun E => hm.injective (hfg _)
  have hlip : ∀ M₁ M₂, |g M₁ - g M₂| ≤ |M₁ - M₂| / (1 - e) := by
    intro M₁ M₂
    rw [le_div_iff₀ (sub_pos.2 he1), mul_comm]
    have := kepler_abs_sub_ge he0 (g M₁) (g M₂)
    rwa [hfg, hfg] at this
  have hcont : Continuous g := by
    refine (LipschitzWith.of_dist_le' (K := (1 - e)⁻¹) fun x y => ?_).continuous
    rw [Real.dist_eq, Real.dist_eq, ← div_eq_inv_mul]
    exact hlip x y
  refine ⟨g, hfg, hgf, fun x y hxy => hm.lt_iff_lt.1 (by rwa [hfg, hfg]), hlip, hcont, fun M => ?_⟩
  exact HasDerivAt.of_local_left_inverse hcont.continuousAt (hasDerivAt_kepler e (g M))
    (kepler_deriv_pos he0 he1 _).ne' (Filter.Eventually.of_forall hfg)

/-- **La boucle du résolveur** (§ 1.2 e). Une manivelle de rayon `R_y` calée sur l'arbre E mène une coulisse
écossaise (course `x = R_y sin E`) ; sa crémaillère roule sans glisser sur un pignon de rayon `ρ_p`, qui tourne de
`δ` avec `ρ_p·δ = x` ; un différentiel impose `M = E − δ`. Avec `R_y/ρ_p = e`, la boucle équivaut à l'équation de
Kepler `E − e sin E = M`. -/
theorem boucle_resolveur {e R_y ρ_p E M : ℝ} (hρ : ρ_p ≠ 0) (hR : R_y / ρ_p = e) :
    (∃ x δ : ℝ, x = R_y * sin E ∧ ρ_p * δ = x ∧ M = E - δ) ↔ E - e * sin E = M := by
  have hRy : R_y = e * ρ_p := by rw [← hR, div_mul_cancel₀ R_y hρ]
  constructor
  · rintro ⟨x, δ, rfl, h1, h2⟩
    have hδ : δ = e * sin E := by
      apply mul_left_cancel₀ hρ
      rw [h1, hRy]
      ring
    linear_combination hδ - h2
  · intro h
    exact ⟨R_y * sin E, e * sin E, rfl, by rw [hRy]; ring, h.symm⟩

/-- Pour `0 ≤ e < 1`, la boucle fermée du résolveur a un et un seul état `E` pour chaque `M`. -/
theorem boucle_resolveur_existsUnique {e R_y ρ_p : ℝ} (he0 : 0 ≤ e) (he1 : e < 1) (hρ : ρ_p ≠ 0)
    (hR : R_y / ρ_p = e) (M : ℝ) :
    ∃! E : ℝ, ∃ x δ : ℝ, x = R_y * sin E ∧ ρ_p * δ = x ∧ M = E - δ := by
  simp only [boucle_resolveur hρ hR]
  exact kepler_existsUnique he0 he1 M

/-- Valeurs d'exemple de Mercure (§ 1.2 e) : `R_y = 3,084 mm` et `ρ_p = 15 mm` donnent `e = 0,2056`, et le
facteur de transmission `1 − e cos E` reste dans `[0,79 ; 1,21]`. -/
theorem resolveur_mercure :
    (3.084 : ℝ) / 15 = 0.2056 ∧ ∀ E : ℝ, 1 - 0.2056 * cos E ∈ Set.Icc (0.79 : ℝ) 1.21 := by
  refine ⟨by norm_num, fun E => ?_⟩
  have h := kepler_deriv_mem (by norm_num : (0 : ℝ) ≤ 0.2056) E
  exact ⟨by linarith [h.1], by linarith [h.2]⟩

/-! ## 4. L'équant bissecté (§ 1.2 b)

La planète parcourt un cercle de centre `C` et de rayon `ρ` ; un bras rainuré pivote au point équant `Q`
(|Q − C| = eρ) et tourne uniformément ; la goupille de la manivelle (pivot `C`, rayon `ρ`) glisse dans la
rainure. La goupille est donc au point où la demi-droite issue de `Q` coupe le cercle. -/

/-- `|w + t·u θ|² = t² + 2t⟨w, u θ⟩ + |w|²`. -/
theorem nsq_add_smul_u (w : ℝ × ℝ) (t θ : ℝ) :
    nsq (w + t • u θ) = t ^ 2 + 2 * t * dot w (u θ) + nsq w := by
  simp only [nsq, dot, u, Prod.fst_add, Prod.snd_add, Prod.smul_fst, Prod.smul_snd, smul_eq_mul]
  linear_combination t ^ 2 * sin_sq_add_cos_sq θ

/-- Le paramètre de la goupille de l'équant, en forme close : sur la demi-droite issue de `Q` dans la direction
`u θ`, le point du cercle (C, ρ) est à la distance `t = −b + √(b² + ρ² − |Q − C|²)` de `Q`, avec
`b = ⟨Q − C, u θ⟩`. -/
def tEquant (C Q : ℝ × ℝ) (ρ θ : ℝ) : ℝ :=
  -dot (Q - C) (u θ) + √(dot (Q - C) (u θ) ^ 2 + (ρ ^ 2 - nsq (Q - C)))

/-- Le paramètre `tEquant` dépend continûment de l'angle `θ` du bras rainuré. -/
theorem tEquant_continuous (C Q : ℝ × ℝ) (ρ : ℝ) : Continuous (tEquant C Q ρ) := by
  unfold tEquant dot u
  fun_prop

/-- La goupille `Q + tEquant(θ)·u θ` se déplace continûment avec l'angle θ du bras rainuré. -/
theorem equant_goupille_continuous (C Q : ℝ × ℝ) (ρ : ℝ) :
    Continuous fun θ => Q + tEquant C Q ρ θ • u θ := by
  have := tEquant_continuous C Q ρ
  unfold u
  fun_prop

/-- **La goupille de l'équant existe** : si `Q` est intérieur au cercle (|Q − C| = eρ, 0 ≤ e < 1, ρ > 0), le
point `Q + t·u θ` avec `t = tEquant C Q ρ θ` est sur le cercle, et `t > 0`. -/
theorem equant_point {C Q : ℝ × ℝ} {ρ e : ℝ} (hρ : 0 < ρ) (he0 : 0 ≤ e) (he1 : e < 1)
    (hQ : deucl Q C = e * ρ) (θ : ℝ) :
    0 < tEquant C Q ρ θ ∧ deucl (Q + tEquant C Q ρ θ • u θ) C = ρ := by
  have hw : nsq (Q - C) = (e * ρ) ^ 2 := (deucl_eq_iff (by positivity)).1 hQ
  have hk : 0 < ρ ^ 2 - nsq (Q - C) := by
    rw [hw]
    have : ρ ^ 2 - (e * ρ) ^ 2 = ρ ^ 2 * ((1 - e) * (1 + e)) := by ring
    rw [this]
    have : 0 < (1 - e) * (1 + e) := mul_pos (by linarith) (by linarith)
    positivity
  set b := dot (Q - C) (u θ)
  have hS : 0 ≤ b ^ 2 + (ρ ^ 2 - nsq (Q - C)) := by positivity
  have hlt : |b| < √(b ^ 2 + (ρ ^ 2 - nsq (Q - C))) := by
    rw [Real.lt_sqrt (abs_nonneg b), sq_abs]
    linarith
  refine ⟨?_, ?_⟩
  · show 0 < -b + √(b ^ 2 + (ρ ^ 2 - nsq (Q - C)))
    linarith [le_abs_self b]
  · rw [deucl_eq_iff hρ.le, add_sub_right_comm, nsq_add_smul_u]
    show (-b + √(b ^ 2 + (ρ ^ 2 - nsq (Q - C)))) ^ 2 + 2 * (-b + √(b ^ 2 + (ρ ^ 2 - nsq (Q - C)))) * b
      + nsq (Q - C) = ρ ^ 2
    linear_combination Real.sq_sqrt hS

/-- **Équant bissecté : la goupille est bien définie.** Pour un cercle de centre `C` et de rayon `ρ > 0` et un
point équant `Q` intérieur (|Q − C| = eρ, 0 ≤ e < 1), toute demi-droite issue de `Q` (le bras rainuré, d'angle
θ) coupe le cercle (où est la goupille de la manivelle) en exactement un point : il existe un unique `t > 0` tel
que `|Q + t·u θ − C| = ρ`. La goupille-rainure de l'équant est donc définie à chaque instant. -/
theorem equant_rayon_unique {C Q : ℝ × ℝ} {ρ e : ℝ} (hρ : 0 < ρ) (he0 : 0 ≤ e) (he1 : e < 1)
    (hQ : deucl Q C = e * ρ) (θ : ℝ) :
    ∃! t : ℝ, 0 < t ∧ deucl (Q + t • u θ) C = ρ := by
  obtain ⟨ht0, hP0⟩ := equant_point hρ he0 he1 hQ θ
  refine ⟨tEquant C Q ρ θ, ⟨ht0, hP0⟩, ?_⟩
  rintro t ⟨ht, hP⟩
  have hw : nsq (Q - C) = (e * ρ) ^ 2 := (deucl_eq_iff (by positivity)).1 hQ
  have hk : 0 < ρ ^ 2 - nsq (Q - C) := by
    rw [hw]
    have : ρ ^ 2 - (e * ρ) ^ 2 = ρ ^ 2 * ((1 - e) * (1 + e)) := by ring
    rw [this]
    have : 0 < (1 - e) * (1 + e) := mul_pos (by linarith) (by linarith)
    positivity
  rw [deucl_eq_iff hρ.le, add_sub_right_comm, nsq_add_smul_u] at hP hP0
  set b := dot (Q - C) (u θ)
  set t₀ := tEquant C Q ρ θ
  have hprod : (t - t₀) * (t + t₀ + 2 * b) = 0 := by linear_combination hP - hP0
  rcases mul_eq_zero.1 hprod with h | h
  · linarith
  · exfalso
    have : t * t₀ = -(ρ ^ 2 - nsq (Q - C)) := by linear_combination -hP + t * h
    nlinarith [mul_pos ht ht0]

/-! ## 5. L'accouplement d'Oldham

Deux arbres parallèles d'axes `O₁`, `O₂` ; un disque intermédiaire porte deux languettes à angle droit, une sur
chaque face. Une rainure (ou une languette) est une droite : sa direction n'est définie qu'à π près. -/

/-- `cross (u α) (u β) = sin (β − α)`. -/
theorem cross_u (α β : ℝ) : cross (u α) (u β) = sin (β - α) := by
  simp only [cross, u, sin_sub]
  ring

/-- Deux directions sont parallèles (`cross = 0`) si et seulement si leurs angles sont égaux modulo π. -/
theorem parallele_iff (α β : ℝ) : cross (u α) (u β) = 0 ↔ ∃ k : ℤ, β = α + k * π := by
  rw [cross_u, sin_eq_zero_iff]
  constructor
  · rintro ⟨n, hn⟩
    exact ⟨n, by linarith⟩
  · rintro ⟨k, hk⟩
    exact ⟨k, by linarith⟩

/-- **Oldham, modulo π.** Disque intermédiaire d'angle β : languette 1 de direction `u β`, languette 2 de
direction `u (β + π/2)` (à angle droit, sur l'autre face). Rainure de l'arbre d'entrée (angle α) : direction
`u α` ; rainure de l'arbre de sortie (angle γ) : direction `u (γ + π/2)`. Si chaque languette est parallèle à
sa rainure, alors γ = α modulo π. -/
theorem oldham_modulo_pi {α β γ : ℝ} (h₁ : cross (u α) (u β) = 0)
    (h₂ : cross (u (γ + π / 2)) (u (β + π / 2)) = 0) : ∃ k : ℤ, γ = α + k * π := by
  obtain ⟨k₁, hk₁⟩ := (parallele_iff _ _).1 h₁
  obtain ⟨k₂, hk₂⟩ := (parallele_iff _ _).1 h₂
  exact ⟨k₁ - k₂, by push_cast; linarith⟩

/-- **Continuité.** Deux angles qui varient continûment, égaux modulo π à chaque instant et égaux à l'instant 0,
sont égaux à tout instant : leur écart, multiple entier de π et continu, ne peut pas sauter (sinon il prendrait
la valeur ±π/2 par le théorème des valeurs intermédiaires). -/
theorem eq_of_modulo_pi_of_continuous {α γ : ℝ → ℝ} (hα : Continuous α) (hγ : Continuous γ)
    (hmod : ∀ t, ∃ k : ℤ, γ t = α t + k * π) (h0 : γ 0 = α 0) (t : ℝ) : γ t = α t := by
  have hdc : Continuous fun s => γ s - α s := hγ.sub hα
  -- l'écart ne vaut jamais ±π/2
  have hhalf : ∀ s, γ s - α s ≠ π / 2 ∧ γ s - α s ≠ -(π / 2) := by
    intro s
    obtain ⟨j, hj⟩ := hmod s
    have hds : γ s - α s = j * π := by linarith
    rw [hds]
    constructor
    · intro h
      have h2 : (2 * (j : ℝ) - 1) * π = 0 := by linear_combination 2 * h
      have h3 : 2 * (j : ℝ) - 1 = 0 := (mul_eq_zero.1 h2).resolve_right pi_ne_zero
      have h4 : 2 * j = 1 := by exact_mod_cast (by linarith : 2 * (j : ℝ) = 1)
      omega
    · intro h
      have h2 : (2 * (j : ℝ) + 1) * π = 0 := by linear_combination 2 * h
      have h3 : 2 * (j : ℝ) + 1 = 0 := (mul_eq_zero.1 h2).resolve_right pi_ne_zero
      have h4 : 2 * j = -1 := by exact_mod_cast (by linarith : 2 * (j : ℝ) = -1)
      omega
  obtain ⟨k, hk⟩ := hmod t
  have hdt : γ t - α t = k * π := by linarith
  have hd0 : γ 0 - α 0 = 0 := by linarith
  by_contra hne
  have hk0 : k ≠ 0 := by
    rintro rfl
    apply hne
    simp only [Int.cast_zero, zero_mul] at hdt
    linarith
  rcases lt_or_gt_of_ne hk0 with hneg | hpos
  · have hk1 : (k : ℝ) ≤ -1 := by exact_mod_cast (show k ≤ -1 by omega)
    have hmem : -(π / 2) ∈ Set.uIcc (γ 0 - α 0) (γ t - α t) := by
      rw [Set.mem_uIcc, hd0, hdt]
      right
      constructor <;> nlinarith [pi_pos]
    obtain ⟨s, -, hs⟩ := intermediate_value_uIcc hdc.continuousOn hmem
    exact (hhalf s).2 hs
  · have hk1 : (1 : ℝ) ≤ k := by exact_mod_cast (show 1 ≤ k by omega)
    have hmem : π / 2 ∈ Set.uIcc (γ 0 - α 0) (γ t - α t) := by
      rw [Set.mem_uIcc, hd0, hdt]
      left
      constructor <;> nlinarith [pi_pos]
    obtain ⟨s, -, hs⟩ := intermediate_value_uIcc hdc.continuousOn hmem
    exact (hhalf s).1 hs

/-- **Oldham : même rotation.** Si les angles α(t) et γ(t) des deux arbres varient continûment (l'angle β(t) du
disque est quelconque), si les languettes restent dans leurs rainures à chaque instant et si les deux arbres
partent du même angle, ils ont le même angle à tout instant : l'accouplement transmet la rotation 1:1 entre
arbres parallèles décalés. -/
theorem oldham_meme_rotation {α β γ : ℝ → ℝ} (hα : Continuous α) (hγ : Continuous γ)
    (h₁ : ∀ t, cross (u (α t)) (u (β t)) = 0)
    (h₂ : ∀ t, cross (u (γ t + π / 2)) (u (β t + π / 2)) = 0) (h0 : γ 0 = α 0) (t : ℝ) :
    γ t = α t :=
  eq_of_modulo_pi_of_continuous hα hγ (fun s => oldham_modulo_pi (h₁ s) (h₂ s)) h0 t

/-- **Le disque d'Oldham décrit un cercle.** Le centre `D` du disque est sur la rainure de l'arbre d'entrée
(droite issue de `O₁`, direction `u α`) et sur celle de l'arbre de sortie (droite issue de `O₂`, direction
`u (γ + π/2)`), avec γ = α modulo π. Alors `D` est sur le cercle de diamètre `O₁O₂` :
`|D − (O₁ + O₂)/2|² = |O₁ − O₂|²/4` (course du disque dans ses rainures : le diamètre |O₁O₂|). -/
theorem oldham_centre_cercle {α γ : ℝ} {O₁ O₂ D : ℝ × ℝ} (hmod : ∃ k : ℤ, γ = α + k * π)
    (h₁ : cross (D - O₁) (u α) = 0) (h₂ : cross (D - O₂) (u (γ + π / 2)) = 0) :
    nsq (D - (1 / 2 : ℝ) • (O₁ + O₂)) = nsq (O₁ - O₂) / 4 := by
  obtain ⟨k, rfl⟩ := hmod
  have hc : cross (D - O₂) (u (α + k * π + π / 2)) = (-1) ^ k * dot (D - O₂) (u α) := by
    simp only [cross, dot, u, cos_add_pi_div_two, sin_add_pi_div_two, cos_add_int_mul_pi,
      sin_add_int_mul_pi]
    ring
  rw [hc] at h₂
  have hB : dot (D - O₂) (u α) = 0 :=
    (mul_eq_zero.1 h₂).resolve_left (zpow_ne_zero _ (by norm_num))
  obtain ⟨d₁, d₂⟩ := D
  obtain ⟨p₁, p₂⟩ := O₁
  obtain ⟨q₁, q₂⟩ := O₂
  simp only [cross, dot, nsq, u, Prod.fst_sub, Prod.snd_sub, Prod.fst_add, Prod.snd_add, Prod.smul_fst,
    Prod.smul_snd, smul_eq_mul] at h₁ hB ⊢
  linear_combination ((d₁ - p₁) * cos α + (d₂ - p₂) * sin α) * hB +
    ((d₁ - q₁) * sin α - (d₂ - q₂) * cos α) * h₁ -
    ((d₁ - p₁) * (d₁ - q₁) + (d₂ - p₂) * (d₂ - q₂)) * sin_sq_add_cos_sq α

/-! ## 6. Le joint de Hooke et la réduction à l'équateur (§ 4.5)

L'arbre d'entrée est l'axe z ; l'arbre de sortie est incliné de ε dans le plan (y, z). Le croisillon a deux
branches perpendiculaires : l'une tenue par la fourche d'entrée (perpendiculaire à l'arbre d'entrée), l'autre par
la fourche de sortie (perpendiculaire à l'arbre de sortie). -/

/-- Produit scalaire de ℝ³. -/
def dot3 (a b : ℝ × ℝ × ℝ) : ℝ := a.1 * b.1 + a.2.1 * b.2.1 + a.2.2 * b.2.2

/-- Axe de l'arbre de sortie du joint, incliné de `ε` sur l'arbre d'entrée (axe z) dans le plan (y, z). -/
def axeSortie (ε : ℝ) : ℝ × ℝ × ℝ := (0, -sin ε, cos ε)

/-- Branche d'entrée du croisillon, tenue par la fourche de l'arbre d'entrée (axe z) tourné de l'angle `l`. -/
def brancheEntree (l : ℝ) : ℝ × ℝ × ℝ := (cos l, sin l, 0)

/-- Branche de sortie du croisillon, tenue par la fourche de l'arbre de sortie tourné de `φ` autour de
`axeSortie ε`, calée à 90° : `φ = 0` met la branche le long de `(0, cos ε, sin ε)`, et
`brancheSortie ε φ = cos (φ + π/2)·(1, 0, 0) + sin (φ + π/2)·(0, cos ε, sin ε)`. -/
def brancheSortie (ε φ : ℝ) : ℝ × ℝ × ℝ := (-sin φ, cos φ * cos ε, cos φ * sin ε)

/-- Géométrie du joint : la branche d'entrée est perpendiculaire à l'arbre d'entrée ; la branche de sortie est un
vecteur unitaire perpendiculaire à l'arbre de sortie ; l'arbre de sortie est unitaire et fait l'angle ε avec
l'arbre d'entrée (`⟨e_z, axe⟩ = cos ε`). -/
theorem hooke_geometrie (ε l φ : ℝ) :
    dot3 (brancheEntree l) (0, 0, 1) = 0 ∧ dot3 (brancheSortie ε φ) (axeSortie ε) = 0 ∧
      dot3 (brancheSortie ε φ) (brancheSortie ε φ) = 1 ∧ dot3 (axeSortie ε) (axeSortie ε) = 1 ∧
      dot3 (0, 0, 1) (axeSortie ε) = cos ε := by
  simp only [dot3, brancheEntree, brancheSortie, axeSortie]
  refine ⟨by ring, by ring, ?_, ?_, by ring⟩
  · linear_combination cos φ ^ 2 * sin_sq_add_cos_sq ε + sin_sq_add_cos_sq φ
  · linear_combination sin_sq_add_cos_sq ε

/-- **Loi du joint de Hooke.** Les deux branches du croisillon sont perpendiculaires si et seulement si
`sin φ cos λ = cos ε cos φ sin λ` : forme sans division de `tan φ = cos ε tan λ`. -/
theorem hooke_croisillon (ε l φ : ℝ) :
    dot3 (brancheEntree l) (brancheSortie ε φ) = 0 ↔ sin φ * cos l = cos ε * (cos φ * sin l) := by
  simp only [dot3, brancheEntree, brancheSortie]
  constructor <;> intro h <;> linear_combination -h

/-- Forme tangente : si `cos φ ≠ 0` et `cos λ ≠ 0`, le joint est en prise si et seulement si
`tan φ = cos ε · tan λ`. -/
theorem hooke_tan {ε l φ : ℝ} (hφ : cos φ ≠ 0) (hl : cos l ≠ 0) :
    dot3 (brancheEntree l) (brancheSortie ε φ) = 0 ↔ tan φ = cos ε * tan l := by
  have hT : sin l = sin l / cos l * cos l := (div_mul_cancel₀ _ hl).symm
  rw [hooke_croisillon, tan_eq_sin_div_cos, tan_eq_sin_div_cos, div_eq_iff hφ]
  constructor
  · intro h
    apply mul_right_cancel₀ hl
    linear_combination h + cos ε * cos φ * hT
  · intro h
    linear_combination cos l * h - cos ε * cos φ * hT

/-- Direction du Soleil de longitude écliptique `l` (latitude nulle) en coordonnées équatoriales : image de
`(cos l, sin l, 0)` par la rotation d'angle ε (obliquité) autour de l'axe x, dirigé vers le point vernal. -/
def soleilEquatorial (ε l : ℝ) : ℝ × ℝ × ℝ := (cos l, cos ε * sin l, sin ε * sin l)

/-- `α` est une ascension droite du Soleil de longitude `l` : la projection de sa direction sur le plan de
l'équateur pointe dans la direction `u α`. -/
def EstAscensionDroite (ε l α : ℝ) : Prop :=
  ∃ r : ℝ, 0 < r ∧ ((soleilEquatorial ε l).1, (soleilEquatorial ε l).2.1) = r • u α

/-- **Réduction à l'équateur** : l'ascension droite α du Soleil de longitude λ vérifie
`sin α cos λ = cos ε cos α sin λ`, c'est-à-dire `tan α = cos ε tan λ` : la même loi que le joint de Hooke. -/
theorem ascensionDroite_relation {ε l α : ℝ} (h : EstAscensionDroite ε l α) :
    sin α * cos l = cos ε * (cos α * sin l) := by
  obtain ⟨r, -, hr⟩ := h
  simp only [soleilEquatorial, u, Prod.smul_mk, Prod.mk.injEq] at hr
  obtain ⟨h1, h2⟩ := hr
  linear_combination sin α * h1 - cos α * h2

/-- Pour `cos ε ≠ 0`, le Soleil a une ascension droite pour toute longitude (sa projection équatoriale n'est
jamais nulle). -/
theorem ascensionDroite_existe {ε : ℝ} (hε : cos ε ≠ 0) (l : ℝ) : ∃ α, EstAscensionDroite ε l α := by
  let z : ℂ := ⟨cos l, cos ε * sin l⟩
  have hz : z ≠ 0 := by
    intro h
    have h1 : cos l = 0 := congrArg Complex.re h
    have h2 : cos ε * sin l = 0 := congrArg Complex.im h
    have h3 : sin l = 0 := (mul_eq_zero.1 h2).resolve_left hε
    have h4 := sin_sq_add_cos_sq l
    rw [h1, h3] at h4
    norm_num at h4
  refine ⟨Complex.arg z, ‖z‖, norm_pos_iff.2 hz, ?_⟩
  simp only [soleilEquatorial, u, Prod.smul_mk, Prod.mk.injEq]
  exact ⟨(Complex.norm_mul_cos_arg z).symm, (Complex.norm_mul_sin_arg z).symm⟩

/-- **Le joint de Hooke donne l'ascension droite, modulo π.** Si le joint plié de ε, mené à l'angle λ, est en
prise à l'angle de sortie φ et si α est l'ascension droite du Soleil de longitude λ, alors φ = α modulo π. -/
theorem hooke_ascensionDroite_modulo_pi {ε l φ α : ℝ}
    (hJ : dot3 (brancheEntree l) (brancheSortie ε φ) = 0) (hA : EstAscensionDroite ε l α) :
    ∃ k : ℤ, φ = α + k * π := by
  rw [hooke_croisillon] at hJ
  obtain ⟨r, hr, hv⟩ := hA
  simp only [soleilEquatorial, u, Prod.smul_mk, Prod.mk.injEq] at hv
  obtain ⟨h1, h2⟩ := hv
  have hc : cross (u α) (u φ) = 0 := by
    rw [cross_u]
    have : r * sin (φ - α) = 0 := by
      rw [sin_sub]
      linear_combination hJ - sin φ * h1 + cos φ * h2
    exact (mul_eq_zero.1 this).resolve_left hr.ne'
  exact (parallele_iff α φ).1 hc

/-- **Le joint de Hooke calcule l'ascension droite.** Si la sortie φ(t) du joint et l'ascension droite α(t) du
Soleil (de longitude λ(t), l'entrée) varient continûment, si le joint est en prise à chaque instant et si
φ = α à l'instant 0 (calage), alors φ(t) = α(t) à tout instant ; un différentiel donne ensuite l'équation du
temps L − α. -/
theorem hooke_egale_ascensionDroite {ε : ℝ} {l φ α : ℝ → ℝ} (hφ : Continuous φ) (hα : Continuous α)
    (hJ : ∀ t, dot3 (brancheEntree (l t)) (brancheSortie ε (φ t)) = 0)
    (hA : ∀ t, EstAscensionDroite ε (l t) (α t)) (h0 : φ 0 = α 0) (t : ℝ) : φ t = α t :=
  eq_of_modulo_pi_of_continuous hα hφ (fun s => hooke_ascensionDroite_modulo_pi (hJ s) (hA s)) h0 t

end

end AnticythereV2.Mechanisms
