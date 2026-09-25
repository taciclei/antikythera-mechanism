# Formal proofs in Lean 4

This folder is a [Lean 4](https://lean-lang.org) project, built on [Mathlib](https://github.com/leanprover-community/mathlib4). Its theorems about the reconstructed Antikythera Mechanism are checked by Lean's kernel. A successful `lake build` means all of the following:

- every theorem is fully proved: warnings are errors, so no `sorry` gets through;
- no theorem uses an axiom beyond Lean's three standard ones (`propext`, `Classical.choice`, `Quot.sound`), which `Antikythera/Audit.lean` checks for every declaration;
- the files generated from the spec are exactly what `tools/make_lean.py` produces. The GitHub workflow regenerates them and compares.

## What is proved

| Module | Content | Theorems |
|---|---|---|
| `Kinematics.lean` (generated) | One equation per gear contact, taken from the tooth counts: 37 Willis equations, 2 crown pairs, 4 pin-and-slots and 3 followers. See the list below the table. | 5 |
| `Targets.lean` (generated) | The spec's 22 astronomical targets, derived from the tooth counts alone. `target_b` is the normalisation, 1 turn of b1 per year. | 22 |
| `Geometry.lean` (generated) | For all 37 external meshes: equal modules, and a centre distance equal to m(z₁ + z₂)/2 within 10⁻⁶ mm. | 37 |
| `PinSlot.lean` | The nonlinear couplings. See the list below the table. | 71 |
| `Astronomy.lean` | The cycles and the precision. See the list below the table. | 58 |
| `Audit.lean` | Fails the build if any declaration depends on `sorryAx` or on a non-standard axiom. | — |

**`Kinematics.lean`** proves four results:
- `determined` and `determined_by_crank`: the crank fixes every mean rate;
- `consistent`: the equations have a solution for every crank speed;
- `moves`: the mechanism can turn;
- `one_dof`: the admissible mean-rate vectors form exactly one line, so the mechanism has **one degree of freedom**.

**`PinSlot.lean`** covers the nonlinear couplings:
- the spec's `atan2` laws for the four pin-and-slots and the three followers;
- the exact maximal deviation `arcsin(e/r)`;
- the smooth, strictly monotone slot motion;
- mean rates unchanged by a bounded lag, which formally justifies the linear fields of `Kinematics`;
- the lunar anomaly amplitude: `6.579° < arcsin(1.1/9.6) < 6.581°`;
- the amplitudes for Saturn, Jupiter, Mars, Mercury, Venus and the true Sun.

**`Astronomy.lean`** covers the cycles and the precision:
- sidereal month 254/19 and Metonic cycle (19 years = 235 synodic months);
- the Saros (223 months = 4 turns), Exeligmos, Callippic (940 months = 76 years) and Olympiad dials;
- lunar anomaly and apsides, and the nodes (Dragon Hand);
- the planetary period relations, where sidereal = solar − synodic;
- the precision in days against modern values, with 1 year = 365.2422 days. For example, the gear-implied sidereal month is within 0.0005 days of 27.321661.

Total: **193 theorems** in about 2,300 lines.

## Scope and limits

- The kinematic theorems are about **mean rates**. The instantaneous nonlinear motion of the pin-and-slots and followers is treated in `PinSlot.lean`.
- The **planetary gearing, the Dragon Hand and the true Sun** follow the hypothetical model of Freeth et al. (2021). Lean proves what that model computes, not that the ancient mechanism was built that way.
- **Not covered by Lean**: contact ratio, face overlap, undercut, crown-gear geometry and collisions. These are checked by `tools/validate_spec.py`, `tools/check_kinematics.py` and the BVH tests in Blender.

## Check it yourself

```sh
# once: install elan (the Lean toolchain manager), see https://lean-lang.org/install
cd lean
lake exe cache get    # download the compiled Mathlib (about 5 GB)
lake build            # check every proof (about 2 minutes)
cd ..
python3 tools/make_lean.py            # regenerate Kinematics / Targets / Geometry from the spec
python3 tools/lean_mutation_test.py   # Lean must reject 9 deliberately wrong mechanisms
```

The mutation test does two kinds of change:
- **In the Lean files**: a tooth count, the sign of a Willis equation, a carrier, a rate, a target value, or an axis moved by 10⁻⁵ mm.
- **In the spec, end to end**: one tooth count on the Metonic train and one on the Olympiad train.

Every mutant must fail to compile. The unmutated control must compile.
