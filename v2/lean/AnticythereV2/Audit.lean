-- GÉNÉRÉ par v2/tools/make_lean_v2.py depuis v2/spec/trains.json et v2/spec/architecture.json.
-- Ne pas éditer à la main : relancer le générateur.

import AnticythereV2.Kinematics
import AnticythereV2.Ratios
import AnticythereV2.Rates
import AnticythereV2.Identities
import AnticythereV2.Architecture

/-!
# Audit

Fait échouer la compilation si une déclaration de `AnticythereV2` dépend d'un axiome autre que les trois axiomes
standard de Lean et de Mathlib (`propext`, `Classical.choice`, `Quot.sound`), en particulier de `sorryAx`
(preuve inachevée) ou de `Lean.ofReduceBool` (`native_decide`). Avec `warningAsError = true`, un `lake build`
réussi signifie donc que chaque théorème est entièrement prouvé et vérifié par le noyau de Lean.

Les théorèmes générés portent tous une docstring : l'audit compte ceux-là, hors projections de la structure
`Kinematics` (les lemmes auxiliaires créés automatiquement par Lean n'ont pas de docstring), et exige au moins
201 théorèmes, le nombre produit par `v2/tools/make_lean_v2.py`.
-/

open Lean Elab Command in
run_cmd do
  let env ← getEnv
  let allowed := [``propext, ``Classical.choice, ``Quot.sound]
  let mut thms := 0
  let mut documented := 0
  for (name, info) in env.constants.map₁.toList do
    if (`AnticythereV2).isPrefixOf name && !name.isInternal then
      let axioms ← liftCoreM <| Lean.collectAxioms name
      for ax in axioms do
        unless allowed.contains ax do
          throwError "{name} dépend de l'axiome {ax}"
      if info matches .thmInfo _ then
        thms := thms + 1
        if !env.isProjectionFn name && (← findDocString? env name).isSome then
          documented := documented + 1
  if documented < 201 then
    throwError "audit : seulement {documented} théorèmes documentés sur 201 attendus"
  logInfo m!"audit : {documented} théorèmes générés ({thms} avec projections et lemmes auxiliaires), \
    tous prouvés (axiomes ⊆ propext, Classical.choice, Quot.sound)"
