# Antikythera Mechanism: functional reconstruction in Blender 5.2

This project builds the mechanism from `spec/antikythera.json`, the single source of truth. It works in five stages:

- it proves the kinematics with exact fractions: rank 44, one degree of freedom, and every target exact;
- it generates conjugate 30° involute gearing, the plates, dials and case;
- it assembles an animated Blender scene driven by a single crank;
- it checks that no part penetrates another over the whole range of motion;
- it exports print files, renders images and an animation, and writes a report.

## Environment

```sh
PY=/Applications/Blender.app/Contents/Resources/5.2/python/bin/python3.13   # numpy 2.3.4
BL=/Applications/Blender.app/Contents/MacOS/Blender                         # Blender 5.2.2 LTS
cd <this folder>
```

The `am/` package never imports `bpy`, so it can be tested outside Blender. Only `blender_scripts/` uses Blender.

## Re-run everything (one command per step)

| Step | Command | Output |
|---|---|---|
| 0 spec fingerprint | `"$PY" -m am.verify --stage spec` | `out/verify_spec.json` |
| 1 exact kinematics | `"$PY" -m unittest discover -s tests -v && "$PY" -m am.verify --stage kinematics` | DOF, rates, targets |
| 2 2D geometry | `"$PY" -m am.verify --stage geometry` | meshes, 2D interference, pre-filter, cosmos; writes `out/prefilter_pairs.json` |
| 3 driver expressions | `"$PY" -m am.verify --stage expr` | expression errors < 1e-9 rad |
| 1-3 together | `"$PY" -m am.verify --stage all` | `out/verify_all.json` |
| 4 Blender build | `"$BL" -b --factory-startup --python-exit-code 1 -P blender_scripts/build.py` | `out/am.blend`, `out/build_report.json` |
| 5 3D checks | `for m in static meshes pins spiral texts sanity; do "$BL" -b --factory-startup --python-exit-code 1 -P blender_scripts/check.py -- $m; done` | `out/check_<mode>.json` |
| 5 BVH pairs (8 batches) | `for i in 0 1 2 3 4 5 6 7; do "$BL" -b --factory-startup --python-exit-code 1 -P blender_scripts/check.py -- pairs $i 8; done` | `out/check_pairs_<i>.json` |
| 5 merge | `"$BL" -b --factory-startup --python-exit-code 1 -P blender_scripts/check.py -- merge` | `out/check.json` |
| 7 print | `"$BL" -b --factory-startup --python-exit-code 1 -P blender_scripts/export_print.py` | `out/print/<profile>/*.stl`, `antikythera.3mf`, `print_report.json` |
| 8 stills (Cycles Metal) | `"$BL" -b --factory-startup --python-exit-code 1 -P blender_scripts/render.py -- stills warmup cycles && "$BL" -b --factory-startup --python-exit-code 1 -P blender_scripts/render.py -- stills all cycles` | `out/renders/{front34,front,back,exploded}.png` |
| 8 animation frames | `"$BL" -b --factory-startup --python-exit-code 1 -P blender_scripts/render.py -- frames 1 120` (then 121-240, 241-360, 361-480) | `out/renders/frames/f_####.png` |
| 8 encode + verify | `"$BL" -b --factory-startup --python-exit-code 1 -P blender_scripts/render.py -- encode && "$BL" -b --factory-startup --python-exit-code 1 -P blender_scripts/render.py -- verify` | `out/renders/antikythera.mp4` (480 frames) |
| 9 report | `"$PY" -m am.report` | `out/report.md`, `out/report.html` |

Blender logs go to `out/logs/`.

## Using `out/am.blend`

- `AM_Controller["crank"]` is the crank position in years; 1 year = 1 turn of b1. A linear action moves it from 0 to 4 years over frames 1–481, with linear extrapolation.
- `AM_Controller["patina"]` blends from new bronze (0) to museum patina (1).
- Every body is an Empty `B_<id>` whose rotation is a **simple-expression driver**. The file therefore animates without allowing Python scripts.
- Every part is a child of its body Empty, modelled in that body's local frame. Parts carry these custom properties: `status`, `role`, `teeth`, `module`, `body` and `sources`.
- `obj.color` shows the status colour; use Solid/Object colour mode to see it.
- Collections: `AM_SURVIVING`, `AM_RECONSTRUCTED`, `AM_HYPOTHETICAL`, `AM_STRUCTURE`, `AM_DIALS`, `AM_CASE` and `AM_HELPERS`. The case covers are hidden.

## Layout

```
spec/antikythera.json    spec (fingerprint 18934c80…86b3)
am/spec.py               loading, fingerprint, structural validation
am/kinematics.py         Fraction solver (Willis), DOF, targets, angle laws theta(t)
am/expr.py               driver expressions + restricted evaluator
am/involute.py           30° involute teeth, backlash, contact ratio, phasing forest
am/outline.py            circles (clearance side counts), slots, arms, windows, gear loops
am/crown.py              a1 / q1 crown teeth from the envelope grids
am/spiral.py             two-centre spirals, grooves, cells, psi->rho table
am/layout.py             catalogue of all 228 parts (islands extruded along z or x), print profiles
am/regions.py            conservative swept-region collision pre-filter
am/interference2d.py     2D tooth interference over one pitch
am/geomcheck.py          'geometry' stage (+ cosmos checks)
am/threemf.py            minimal 3MF writer/reader
am/report.py             Markdown + HTML report
am/verify.py             CLI
blender_scripts/         bootstrap, build, animate, materials, meshing, dials, check, export_print, render
tests/                   unittest suites (Blender's Python)
```

`PROGRESS.md` records what happened at each step. `DECISIONS.md` lists the choices made where the spec is silent.
