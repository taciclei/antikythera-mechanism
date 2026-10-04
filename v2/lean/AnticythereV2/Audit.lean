-- GÉNÉRÉ par v2/tools/make_lean_v2.py depuis v2/spec/trains.json et v2/spec/architecture.json.
-- Ne pas éditer à la main : relancer le générateur.

import AnticythereV2.Kinematics
import AnticythereV2.Ratios
import AnticythereV2.Rates
import AnticythereV2.Identities
import AnticythereV2.Architecture
import AnticythereV2.Mechanisms

/-!
# Audit

Fait échouer la compilation si une déclaration de `AnticythereV2` dépend d'un axiome autre que les trois axiomes
standard de Lean et de Mathlib (`propext`, `Classical.choice`, `Quot.sound`), en particulier de `sorryAx`
(preuve inachevée) ou de `Lean.ofReduceBool` (`native_decide`). Avec `warningAsError = true`, un `lake build`
réussi signifie donc que chaque théorème est entièrement prouvé et vérifié par le noyau de Lean.

Les théorèmes générés et les théorèmes écrits à la main portent tous une docstring : l'audit compte ceux-là, hors
projections de la structure `Kinematics` (les lemmes auxiliaires créés automatiquement par Lean n'ont pas de
docstring), et exige au moins 249 théorèmes : 201 produits par `v2/tools/make_lean_v2.py` et
48 écrits à la main (`Mechanisms.lean` : 48). Chaque théorème écrit à la main est en outre vérifié par son nom
(existence, théorème, docstring) ; le générateur en relève la liste ci-dessous.
-/

open Lean Elab Command in
run_cmd do
  let env ← getEnv
  let allowed := [``propext, ``Classical.choice, ``Quot.sound]
  let hand : List Name := [
    ``AnticythereV2.Mechanisms.deucl_eq_dist,
    ``AnticythereV2.Mechanisms.nsq_u,
    ``AnticythereV2.Mechanisms.u_add_pi,
    ``AnticythereV2.Mechanisms.deucl_eq_iff,
    ``AnticythereV2.Mechanisms.nsq_rot,
    ``AnticythereV2.Mechanisms.rot_neg_rot,
    ``AnticythereV2.Mechanisms.rot_sub,
    ``AnticythereV2.Mechanisms.module_exterieur,
    ``AnticythereV2.Mechanisms.module_interieur,
    ``AnticythereV2.Mechanisms.suiveur_geocentrique,
    ``AnticythereV2.Mechanisms.pivot_heliocentrique,
    ``AnticythereV2.Mechanisms.ecart_pivots,
    ``AnticythereV2.Mechanisms.chaine_un_un,
    ``AnticythereV2.Mechanisms.deux_bras,
    ``AnticythereV2.Mechanisms.deux_bras_mem_ellipse,
    ``AnticythereV2.Mechanisms.deux_bras_dist_foyer,
    ``AnticythereV2.Mechanisms.hasDerivAt_kepler,
    ``AnticythereV2.Mechanisms.kepler_deriv_mem,
    ``AnticythereV2.Mechanisms.kepler_deriv_pos,
    ``AnticythereV2.Mechanisms.kepler_inv_deriv_mem,
    ``AnticythereV2.Mechanisms.kepler_sub_mem,
    ``AnticythereV2.Mechanisms.kepler_abs_sub_ge,
    ``AnticythereV2.Mechanisms.kepler_continuous,
    ``AnticythereV2.Mechanisms.kepler_strictMono,
    ``AnticythereV2.Mechanisms.kepler_surjective,
    ``AnticythereV2.Mechanisms.kepler_existsUnique,
    ``AnticythereV2.Mechanisms.kepler_solution,
    ``AnticythereV2.Mechanisms.boucle_resolveur,
    ``AnticythereV2.Mechanisms.boucle_resolveur_existsUnique,
    ``AnticythereV2.Mechanisms.resolveur_mercure,
    ``AnticythereV2.Mechanisms.nsq_add_smul_u,
    ``AnticythereV2.Mechanisms.tEquant_continuous,
    ``AnticythereV2.Mechanisms.equant_goupille_continuous,
    ``AnticythereV2.Mechanisms.equant_point,
    ``AnticythereV2.Mechanisms.equant_rayon_unique,
    ``AnticythereV2.Mechanisms.cross_u,
    ``AnticythereV2.Mechanisms.parallele_iff,
    ``AnticythereV2.Mechanisms.oldham_modulo_pi,
    ``AnticythereV2.Mechanisms.eq_of_modulo_pi_of_continuous,
    ``AnticythereV2.Mechanisms.oldham_meme_rotation,
    ``AnticythereV2.Mechanisms.oldham_centre_cercle,
    ``AnticythereV2.Mechanisms.hooke_geometrie,
    ``AnticythereV2.Mechanisms.hooke_croisillon,
    ``AnticythereV2.Mechanisms.hooke_tan,
    ``AnticythereV2.Mechanisms.ascensionDroite_relation,
    ``AnticythereV2.Mechanisms.ascensionDroite_existe,
    ``AnticythereV2.Mechanisms.hooke_ascensionDroite_modulo_pi,
    ``AnticythereV2.Mechanisms.hooke_egale_ascensionDroite]
  for name in hand do
    let some info := env.find? name | throwError "{name} introuvable"
    unless info matches .thmInfo _ do
      throwError "{name} n'est pas un théorème"
    if (← findDocString? env name).isNone then
      throwError "{name} n'a pas de docstring"
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
  if documented < 249 then
    throwError "audit : seulement {documented} théorèmes documentés sur 249 attendus"
  logInfo m!"audit : {documented} théorèmes documentés (201 générés + {hand.length} écrits à la main ; \
    {thms} avec projections et lemmes auxiliaires), tous prouvés (axiomes ⊆ propext, Classical.choice, Quot.sound)"
