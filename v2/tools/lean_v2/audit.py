"""Audit.lean : axiomes ⊆ {propext, Classical.choice, Quot.sound} et nombre minimal de théorèmes."""
from .common import HEADER, NS

MODULES = ["Kinematics", "Ratios", "Rates", "Identities", "Architecture"]


def generate(n_theorems: int) -> str:
    imports = "\n".join(f"import {NS}.{m}" for m in MODULES)
    return f"""{HEADER}
{imports}

/-!
# Audit

Fait échouer la compilation si une déclaration de `{NS}` dépend d'un axiome autre que les trois axiomes
standard de Lean et de Mathlib (`propext`, `Classical.choice`, `Quot.sound`), en particulier de `sorryAx`
(preuve inachevée) ou de `Lean.ofReduceBool` (`native_decide`). Avec `warningAsError = true`, un `lake build`
réussi signifie donc que chaque théorème est entièrement prouvé et vérifié par le noyau de Lean.

Les théorèmes générés portent tous une docstring : l'audit compte ceux-là, hors projections de la structure
`Kinematics` (les lemmes auxiliaires créés automatiquement par Lean n'ont pas de docstring), et exige au moins
{n_theorems} théorèmes, le nombre produit par `v2/tools/make_lean_v2.py`.
-/

open Lean Elab Command in
run_cmd do
  let env ← getEnv
  let allowed := [``propext, ``Classical.choice, ``Quot.sound]
  let mut thms := 0
  let mut documented := 0
  for (name, info) in env.constants.map₁.toList do
    if (`{NS}).isPrefixOf name && !name.isInternal then
      let axioms ← liftCoreM <| Lean.collectAxioms name
      for ax in axioms do
        unless allowed.contains ax do
          throwError "{{name}} dépend de l'axiome {{ax}}"
      if info matches .thmInfo _ then
        thms := thms + 1
        if !env.isProjectionFn name && (← findDocString? env name).isSome then
          documented := documented + 1
  if documented < {n_theorems} then
    throwError "audit : seulement {{documented}} théorèmes documentés sur {n_theorems} attendus"
  logInfo m!"audit : {{documented}} théorèmes générés ({{thms}} avec projections et lemmes auxiliaires), \\
    tous prouvés (axiomes ⊆ propext, Classical.choice, Quot.sound)"
"""
