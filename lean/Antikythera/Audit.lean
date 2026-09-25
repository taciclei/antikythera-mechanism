import Antikythera.Kinematics
import Antikythera.Targets
import Antikythera.Geometry
import Antikythera.PinSlot
import Antikythera.Astronomy

/-!
# Audit

Fails the build if any declaration of the project depends on an axiom other than the three standard
axioms of Lean and Mathlib (`propext`, `Classical.choice`, `Quot.sound`), in particular on `sorryAx`
(an unfinished proof). Together with `warningAsError = true` in the lakefile, a successful `lake build`
therefore means that every theorem in `Antikythera` is fully proved and checked by Lean's kernel.
-/

open Lean Elab Command in
run_cmd do
  let env ← getEnv
  let allowed := [``propext, ``Classical.choice, ``Quot.sound]
  let mut decls := 0
  for (name, info) in env.constants.map₁.toList do
    if (`Antikythera).isPrefixOf name && !name.isInternal then
      let axioms ← liftCoreM <| Lean.collectAxioms name
      for ax in axioms do
        unless allowed.contains ax do
          throwError "{name} depends on the axiom {ax}"
      if info matches .thmInfo _ then
        decls := decls + 1
  if decls < 100 then
    throwError "audit found only {decls} theorems: the library is incomplete"
  logInfo m!"audit: {decls} theorems (including auto-generated lemmas), all fully proved \
    (axioms ⊆ propext, Classical.choice, Quot.sound)"
