"""Audit.lean : axiomes ⊆ {propext, Classical.choice, Quot.sound} et nombre minimal de théorèmes.

L'audit importe les modules générés ET les modules écrits à la main (`hand.MODULES`, p. ex. Mechanisms) ; il vérifie
chaque théorème écrit à la main par son nom complet (un nom disparu fait échouer l'élaboration) et exige au moins
(générés + écrits à la main) théorèmes documentés.
"""
from .common import HEADER, NS

MODULES = ["Kinematics", "Ratios", "Rates", "Identities", "Architecture"]


def generate(n_theorems: int, hand_files=()) -> str:
    """`n_theorems` : théorèmes générés ; `hand_files` : modules écrits à la main (`hand.HandFile`)."""
    hand_mods = [h.module for h in hand_files]
    imports = "\n".join(f"import {NS}.{m}" for m in MODULES + hand_mods)
    names = [n for h in hand_files for n in h.names]
    n_hand = len(names)
    total = n_theorems + n_hand
    hand_desc = ", ".join(f"`{h.module}.lean` : {len(h.names)}" for h in hand_files) or "aucun"
    hand_list = ",\n    ".join(f"``{n}" for n in names)
    return f"""{HEADER}
{imports}

/-!
# Audit

Fait échouer la compilation si une déclaration de `{NS}` dépend d'un axiome autre que les trois axiomes
standard de Lean et de Mathlib (`propext`, `Classical.choice`, `Quot.sound`), en particulier de `sorryAx`
(preuve inachevée) ou de `Lean.ofReduceBool` (`native_decide`). Avec `warningAsError = true`, un `lake build`
réussi signifie donc que chaque théorème est entièrement prouvé et vérifié par le noyau de Lean.

Les théorèmes générés et les théorèmes écrits à la main portent tous une docstring : l'audit compte ceux-là, hors
projections de la structure `Kinematics` (les lemmes auxiliaires créés automatiquement par Lean n'ont pas de
docstring), et exige au moins {total} théorèmes : {n_theorems} produits par `v2/tools/make_lean_v2.py` et
{n_hand} écrits à la main ({hand_desc}). Chaque théorème écrit à la main est en outre vérifié par son nom
(existence, théorème, docstring) ; le générateur en relève la liste ci-dessous.
-/

open Lean Elab Command in
run_cmd do
  let env ← getEnv
  let allowed := [``propext, ``Classical.choice, ``Quot.sound]
  let hand : List Name := [
    {hand_list}]
  for name in hand do
    let some info := env.find? name | throwError "{{name}} introuvable"
    unless info matches .thmInfo _ do
      throwError "{{name}} n'est pas un théorème"
    if (← findDocString? env name).isNone then
      throwError "{{name}} n'a pas de docstring"
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
  if documented < {total} then
    throwError "audit : seulement {{documented}} théorèmes documentés sur {total} attendus"
  logInfo m!"audit : {{documented}} théorèmes documentés ({n_theorems} générés + {{hand.length}} écrits à la main ; \\
    {{thms}} avec projections et lemmes auxiliaires), tous prouvés (axiomes ⊆ propext, Classical.choice, Quot.sound)"
"""
