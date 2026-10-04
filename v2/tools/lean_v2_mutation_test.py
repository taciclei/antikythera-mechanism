"""Test de mutation des preuves Lean v2 : Lean doit REJETER une machine fausse.

Chaque mutant est une copie temporaire de trains.json ou d'architecture.json où UN nombre de dents est changé. Le
générateur (avec --no-check, pour que Python ne bloque pas avant Lean) écrit un paquet Lake complet dans un
dossier temporaire, puis `lake build` y est lancé. Le test réussit si le témoin non muté compile et si TOUS les
mutants échouent avec une erreur Lean dans le fichier attendu. Le mutant « cohérent » recalcule aussi les vitesses
déclarées : il montre que les bornes (`Rates`) rejettent une machine fausse même quand le JSON est cohérent avec
lui-même. Mathlib est prise par chemin dans lean/.lake/packages (déjà compilée) : rien n'est téléchargé.

Usage : python3 v2/tools/lean_v2_mutation_test.py [--jobs 2] [--keep]
"""
import argparse
import copy
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
V2 = HERE.parent
LEAN_V2 = V2 / "lean"
PACKAGES = (V2.parent / "lean" / ".lake" / "packages").resolve()
TRAINS, ARCH = V2 / "spec" / "trains.json", V2 / "spec" / "architecture.json"


def lake_exe():
    for c in (shutil.which("lake"), Path.home() / ".elan" / "bin" / "lake"):
        if c and Path(c).exists():
            return str(c)
    raise SystemExit("lake introuvable (installer elan)")


def mutate_stage(shaft, stage, side, new):
    """trains.json : dent `side` (0 = menante, 1 = menée) du couple `stage` de l'arbre `shaft` → `new`."""
    def f(T, A):
        st = next(s for s in T["shafts"] if s["id"] == shaft)["stages"][stage]
        old = st[side]
        st[side] = new
        return f"trains.json : {shaft} couple {stage}, {'menante' if side == 0 else 'menée'} {old} → {new} dents"
    return f


def mutate_item(item, new):
    """architecture.json : nombre de dents de la roue placée `item` → `new`."""
    def f(T, A):
        it = next(i for i in A["items"] if i["id"] == item)
        old = it["teeth"]
        it["teeth"] = new
        return f"architecture.json : roue {item}, {old} → {new} dents"
    return f


def mutate_coherent(shaft, stage, side, new):
    """trains.json, mutant COHÉRENT : une dent change ET la vitesse déclarée, le rapport et le candidat `ratio` sont
    recalculés. Le fichier reste cohérent avec lui-même (Kinematics et Ratios compilent) : seules les bornes, dont
    les cibles ne dépendent pas des dents, peuvent rejeter cette machine fausse. Réservé à un arbre feuille."""
    def f(T, A):
        what = mutate_stage(shaft, stage, side, new)(T, A)
        S = {s["id"]: s for s in T["shafts"]}
        assert not any(s.get("src") == shaft or any(t["shaft"] == shaft for t in s.get("terms", []))
                       for s in T["shafts"]), f"{shaft} n'est pas un arbre feuille"
        sh = S[shaft]
        N, D = [a for a, _, _ in sh["stages"]], [b for _, b, _ in sh["stages"]]
        ratio = Fraction(int(sh["sign"]))
        for a, b in zip(N, D):
            ratio *= Fraction(a, b)
        rate = ratio * Fraction(S[sh["src"]]["rate_turns_per_day"])
        sh["ratio"], sh["rate_turns_per_day"] = str(ratio), str(rate)
        for c in T["lean_candidates"]:
            if c["kind"] == "ratio" and c["shaft"] == shaft:
                c["statement"] = (f"ω {shaft} = ({'-' if ratio < 0 else ''}{'·'.join(map(str, N))} / "
                                  f"{'·'.join(map(str, D))}) · ω {sh['src']}")
                c["rate_vs_J"] = str(rate)
        return what + " ; vitesse déclarée et candidat ratio recalculés (mutant cohérent)"
    return f


# (nom, mutation, fichier où Lean doit signaler l'erreur)
MUTANTS = [
    ("témoin", None, None),
    ("Y", mutate_stage("Y", 0, 0, 32), "Kinematics.lean"),                   # 31 → 32 : train de l'année
    ("moon_node", mutate_stage("moon_node", 1, 1, 110), "Kinematics.lean"),  # 109 → 110 : nœuds de la Lune
    ("venus_place", mutate_item("venus_L#w4", 68), "Architecture.lean"),     # 67 → 68 : roue placée de Vénus
    ("callisto_coh", mutate_coherent("callisto", 0, 0, 52), "Rates.lean"),   # 51 → 52, vitesses recalculées
]


def package(dirpath: Path):
    """Paquet Lake minimal dans `dirpath`, Mathlib et ses dépendances par chemin (relatif) vers lean/.lake."""
    rel = Path(os.path.relpath(PACKAGES, dirpath.resolve()))
    toml = (LEAN_V2 / "lakefile.toml").read_text(encoding="utf-8").replace('"../../lean/.lake/packages/mathlib"',
                                                           json.dumps(str(rel / "mathlib")))
    assert str(rel / "mathlib") in toml, "chemin de Mathlib introuvable dans lakefile.toml"
    (dirpath / "lakefile.toml").write_text(toml, encoding="utf-8")
    man = json.loads((LEAN_V2 / "lake-manifest.json").read_text(encoding="utf-8"))
    for p in man["packages"]:
        p["dir"] = str(rel / p["name"])
    (dirpath / "lake-manifest.json").write_text(json.dumps(man, indent=1), encoding="utf-8")
    shutil.copy(LEAN_V2 / "lean-toolchain", dirpath / "lean-toolchain")


def run(item, root: Path, lake: str):
    name, mut, expected = item
    d = root / name
    d.mkdir()
    T, A = json.loads(TRAINS.read_text(encoding="utf-8")), json.loads(ARCH.read_text(encoding="utf-8"))
    T2, A2 = copy.deepcopy(T), copy.deepcopy(A)
    what = mut(T2, A2) if mut else "aucune mutation (doit compiler)"
    (d / "trains.json").write_text(json.dumps(T2, ensure_ascii=False), encoding="utf-8")
    (d / "architecture.json").write_text(json.dumps(A2, ensure_ascii=False), encoding="utf-8")
    package(d)
    g = subprocess.run([sys.executable, str(HERE / "make_lean_v2.py"), "--trains", str(d / "trains.json"),
                        "--arch", str(d / "architecture.json"), "--out", str(d), "--no-check"],
                       capture_output=True, text=True)
    if g.returncode:
        return name, what, expected, None, f"générateur en échec : {g.stderr.strip()[-300:]}", 0.0
    t0 = time.time()
    b = subprocess.run([lake, "build"], cwd=d, capture_output=True, text=True)
    out = b.stdout + b.stderr
    errors = [l.strip() for l in out.splitlines() if "error:" in l and ".lean:" in l]
    # première erreur dans le fichier attendu (sinon la première erreur Lean, qui fera échouer le contrôle)
    first = next((l for l in errors if expected and f"{expected}:" in l), errors[0] if errors else "")
    if b.returncode == 0:
        first = next((l.strip() for l in out.splitlines() if "audit :" in l), "")
    return name, what, expected, b.returncode, first, time.time() - t0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--jobs", type=int, default=2)
    ap.add_argument("--keep", action="store_true", help="garder les dossiers temporaires")
    args = ap.parse_args(argv)
    lake = lake_exe()
    os.environ["PATH"] = str(Path(lake).parent) + os.pathsep + os.environ.get("PATH", "")
    root = Path(tempfile.mkdtemp(prefix="lean_v2_mut_")).resolve()   # /var → /private/var sur macOS
    print(f"dossier temporaire : {root}")
    with ThreadPoolExecutor(args.jobs) as ex:
        results = list(ex.map(lambda it: run(it, root, lake), MUTANTS))
    bad = 0
    for name, what, expected, code, first, dt in results:
        control = expected is None
        # un mutant n'est « rejeté » que si Lean signale une erreur dans le fichier .lean attendu (pas un échec
        # d'installation, ni une erreur sans rapport avec la mutation)
        ok = code == 0 if control else (code not in (None, 0) and f"{expected}:" in first)
        bad += not ok
        status = (("compile" if code == 0 else "REJETÉ") if ok else "NE COMPILE PAS" if control else
                  "SURVIT" if code == 0 else "GÉNÉRATEUR KO" if code is None else "ERREUR AILLEURS")
        print(f"{'OK ' if ok else 'BAD'} {status:14} {name:12} {what} ({dt:.0f} s)")
        if first:
            print(f"      {first[:160]}")
    if not args.keep:
        shutil.rmtree(root, ignore_errors=True)
    n = len(MUTANTS) - 1
    print(f"\n{n} mutants sur {n} rejetés par Lean, témoin compilé" if not bad else f"\n{bad} problème(s)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
