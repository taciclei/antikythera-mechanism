"""Génère les preuves Lean 4 d'Anticythère 2.0 depuis les spécifications (lit SEULEMENT les deux JSON).

Écrit v2/lean/AnticythereV2.lean et v2/lean/AnticythereV2/{Kinematics,Ratios,Rates,Identities,Architecture,
Audit}.lean (CONTRACT.md § 6). Le noyau de Lean vérifie ensuite :
  * Kinematics : une loi de transmission moyenne par arbre (dents de `shafts[].stages`, différentiels, unités,
    pas à pas) ; la table des vitesses déclarées (`rate_turns_per_day`) en découle exactement (`determined`),
    elle les vérifie toutes (`consistent`), et il y a un seul degré de liberté (`one_dof`) ;
  * Ratios : les 36 candidats `ratio` (produit des couples = rapport exact) et le sens physique `phys` ;
  * Rates : les 20 `mean_rate` et les 26 `bound` (dérive < borne, en degrés par siècle, et erreur relative
    majorée, en ℚ) ;
  * Identities : les 14 `identity` et les 2 `decide` (calendrier grégorien pour tout n, semaine de 400 ans),
    avec les prémisses du modèle des cames prouvées depuis Kinematics (`calendar_gearing`, `skip_rate`) ;
  * Architecture : trains placés (même produit, sens ; bus SUPPOSÉ de même sens), reprises, bus, entrées Lune,
    précession, modules changés, entraxes de tous les couples placés ;
  * Audit : axiomes standard seulement et nombre minimal de théorèmes.

Usage : python3 v2/tools/make_lean_v2.py [--trains T] [--arch A] [--out DIR] [--no-check]
--no-check désactive les contrôles de cohérence côté Python : le test de mutation laisse ainsi Lean seul juge.
"""
import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from lean_v2 import archi, audit, identities, kinematics, rates, ratios  # noqa: E402
from lean_v2.common import NS, Ctx  # noqa: E402

V2 = HERE.parent


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--trains", type=Path, default=V2 / "spec" / "trains.json")
    ap.add_argument("--arch", type=Path, default=V2 / "spec" / "architecture.json")
    ap.add_argument("--out", type=Path, default=V2 / "lean", help="dossier du paquet Lake (défaut : v2/lean)")
    ap.add_argument("--no-check", action="store_true", help="ne pas arrêter sur une incohérence (test de mutation)")
    args = ap.parse_args(argv)
    ctx = Ctx(args.trains, args.arch, check=not args.no_check)
    files = {}
    counts = {}
    for mod, gen in (("Kinematics", kinematics), ("Ratios", ratios), ("Rates", rates),
                     ("Identities", identities), ("Architecture", archi)):
        before = ctx.n_theorems
        files[f"{NS}/{mod}.lean"] = gen.generate(ctx)
        counts[mod] = ctx.n_theorems - before
    files[f"{NS}/Audit.lean"] = audit.generate(ctx.n_theorems)
    files[f"{NS}.lean"] = ("-- GÉNÉRÉ par v2/tools/make_lean_v2.py. Ne pas éditer à la main.\n\n"
                           + "".join(f"import {NS}.{m}\n" for m in audit.MODULES + ["Audit"]))
    (args.out / NS).mkdir(parents=True, exist_ok=True)
    for rel, text in files.items():
        (args.out / rel).write_text(text, encoding="utf-8")
    lines = sum(t.count("\n") for t in files.values())
    print(f"{ctx.n_theorems} théorèmes ({', '.join(f'{k} {v}' for k, v in counts.items())}), "
          f"{lines} lignes → {args.out}")
    if ctx.problems:
        print(f"{len(ctx.problems)} incohérence(s) ignorée(s) (--no-check) :")
        for p in ctx.problems:
            print("  -", p)
    return 0


if __name__ == "__main__":
    sys.exit(main())
