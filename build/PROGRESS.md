# PROGRESS

| Step | State | Notes |
|---|---|---|
| 0 spec | GREEN | `spec/antikythera.json` written in 5 chunks; canonical SHA-256 `18934c80…86b3`, 24/24 section fingerprints OK. |
| 1 kinematics | GREEN | 45 unknowns, 44 equations (37 Willis, 4 pin-slot, 3 followers), rank 44, DOF 1, 0 inconsistent, 45 rates = spec, 22/22 targets exact. |
| 2 geometry 2D | GREEN | 37/37 meshes: centre distances exact (max err 6e-11 mm), eps min 1.324, face overlap min 0.50; 2D interference 0 penetration, backlash near line of centres 0.0130 mm; 28 phasing components; pre-filter 228 parts / 4251 z-overlapping pairs / 0 conflicts / 83 intended contacts / 168 retained pairs; a1 keep-out OK; follower sectors free; cosmos checks OK (apogee 65.500 deg, anomaly 6.5796 deg). |
| 3 expressions | GREEN | 47 body drivers, max 120 chars, max error 6.7e-13 rad over 200 samples in [-50, 50]. |
| 4 Blender build | GREEN | `out/am.blend`: 228 mesh parts, 31 FONT texts, 49 empties; 52 drivers valid/simple/untruncated; all meshes closed, manifold, contiguous, volume = area x thickness (max rel err 3e-13). Build 3 s. |
| 5 3D check | GREEN | readback max 6.0e-7 rad (50 values); cycles Metonic/Olympiad/Callippic/Saros closed (max 3e-7 rad); crank F-curve 0/0.5/4.0; BVH: 39 meshes x 50 positions, 9 pin/follower/slider cycles x 72, 168 pairs x 240 cranks -> 0 overlaps. BVH sanity test detects known intersections and a mis-phased gear. |
| 6 dials & case | GREEN | dials are catalogue parts (rings, marks, spirals, pointers, sliders, markers) + 31 Greek FONT texts (no missing glyph); spirals follow rho(psi) within 1.2e-4 mm (500 values); texts >= 0.15 mm in z from overlapping moving parts. |
| 7 print | GREEN | resin_x1 / resin_x1_5 / fdm_x2: 228 STL each (unparented body-local copies, `global_scale` = scale) + one 3MF (228 closed objects, re-read OK); 2D check with the profile backlash OK (near-centre backlash 0.0217 / 0.0347 / 0.0868 mm); STL re-import sizes within 1e-3; walls >= min_wall everywhere; fragile tips listed (h2, p2; 8 gears at fdm_x2); oversize parts listed (b1 at fdm_x2 is 260 mm). ~11 s per profile. |
| 8 renders | GREEN | Cycles Metal (Apple M4 GPU): warm-up + 4 stills 1920x1080, 256 samples, OIDN on GPU (~1 min each). EEVEE: 480 PNG frames 1280x720 in 4 batches (~0.8 s/frame), encoded once via the sequencer; `movieclips.load(...).frame_duration == 480`. |
| 9 report | GREEN | `out/report.md` + `out/report.html`: 22 trains, cosmos checks, DOF/rank, every check with numbers, modules and centre distances, parts by status, FONT texts, print table, unresolved defaults, decisions, fallbacks (none). All 10 criteria GREEN. |

Final re-run of the full 3D check suite on the final `out/am.blend`: `out/check.json` summary ok = True (0 overlaps on all samples).

## Problems met and fixes
- `layout.gear`: b1/b0 are not in the spur forest -> phase 0 (spec 5.3).
- Pre-filter: slider-pin band vs dial rim reported as overlap because hole-less polygon distance was used -> island distance now honours holes (an island lying in a hole).
- Volume check: thin strips (0.4 mm wide) failed at 1.5e-5 because the contour area was computed on float64 coordinates while vertices are stored in float32 -> area now computed on the float32 contour (same treatment as z in spec 5.5).
- Print profiles: hole radii that were constants (hubs, disks, levers, rings, plate centre holes) now use `Profile.hole(r_inner, r_spec)` so every bore/hole is regenerated with `bore_clearance_mm`; scholarly geometry unchanged (pre-filter re-run: 0 conflicts).
- STL export in an empty factory scene: removed temporaries left `None` entries in the view-layer object list -> deselect via `scene.objects` after `view_layer.update()`.
- Renders: first previews too dark/patinated (metallic bronze reflecting a black world) -> studio-grey world, patina 0.06 for stills, darker engraving material for dial marks, case hidden for the 3/4, dial and exploded views.
- Animation batch loop: zsh does not word-split and aborts on an empty glob -> loops run under `bash -c`.
