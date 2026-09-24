# Antikythera Mechanism - functional reconstruction: verification report

Spec `Antikythera Mechanism — functional reconstruction spec` v1.0.0 (2026-09-24). Generated from `spec/antikythera.json`, `out/verify_all.json`, `out/check.json`, `out/build_report.json` and `out/print/*/print_report.json`.

## Status

**All 10 acceptance criteria are GREEN.** No problem was found in the spec data; no fallback of section 8 was needed.

| # | Criterion (section 9) | State |
|---|---|---|
| 1 | Spec fingerprint identical | GREEN |
| 2 | Exact solver: DOF 1, rates, 22 targets | GREEN |
| 3 | Meshes: centre distances, modules, face overlap, eps, z >= 8, nominal tip land; crowns by BVH (a) | GREEN |
| 4 | 2D interference: 0 penetration (j = 0.03) | GREEN |
| 5 | Pre-filter 0 conflicts, a1 keep-out, follower sectors, cosmos checks | GREEN |
| 6 | Drivers valid/simple/untruncated, readback < 1e-5 rad, cycles closed | GREEN |
| 7 | BVH: 0 overlapping pairs on every sample (dials and case included, FONT excluded) | GREEN |
| 8 | Meshes closed, manifold, contiguous, volume = area x thickness (crowns per shell) | GREEN |
| 9 | Deliverables present; am.blend animates without Python scripts | GREEN |
| 10 | PROGRESS.md / DECISIONS.md up to date; deviations listed | GREEN |

## Trains and periods

Periods in days use the model year = 1 tropical year = 365.2422 days. Deviations are relative to `reference_values_days` (modern values); each train reproduces its ancient period relation exactly.

| Output | Chain | Exact rate (rev/y) | Cycle | Period (d) | Reference (d) | Rel. dev. |
|---|---|---|---|---|---|---|
| Crank a (turns/year) | a1 (crown) ~ b1 | 223/48 | definition 223/48 | - | - | - |
| Mean Sun / date pointer b | b1 (input) | 1 | tropical year | 365.2422 | 365.2422 | +0.00e+00 |
| Moon pointer (mean sidereal) | b2>c1, c2>d1, d2>e2, e5>k1 ~pin~ k2>e6, e1>b3 | 254/19 | 254 sidereal months / 19 y | 27.3213 | 27.3217 | -1.44e-05 |
| Moon phase q1 (synodic) | b0 ~ q1 (crown differential on the Moon pointer) | 235/19 | synodic month | 29.5302 | 29.5306 | -1.25e-05 |
| Lunar anomaly k1 on e3 | e5>k1 relative to the e3 turntable | 56165/4237 | anomalistic month | 27.5533 | 27.5545 | -4.53e-05 |
| Lunar apsidal line e3 | b2>l1, l2>m1, m3>e3 | -477/4237 | 8.88 y | 3244.3002 | 3232.6054 | +3.62e-03 |
| Draconic month (Moon - nodes) | moon - t_nodes | 23717/1767 | draconic month | 27.2118 | 27.2122 | -1.44e-05 |
| Dragon Hand (nodes) | fx49>nd62, nd64>nd48 (spB on b) | -5/93 | 18.6 y retrograde | 6793.5049 | 6793.4800 | +3.67e-06 |
| Metonic pointer (5 turns) | b2>l1, l2>m1, m2>n1 | -5/19 | 19 y = 235 synodic months | 6939.6018 | 6939.6884 | -1.25e-05 |
| Olympiad pointer | ... m2>n1, n3>o1 | 1/4 | 4-year games cycle | 1460.9688 | - | - |
| Callippic pointer | ... m2>n1, n2>p1, p2>cal1 | -1/76 | 76 y = 940 synodic months | 27758.4072 | 27758.7536 | -1.25e-05 |
| Saros pointer (4 turns) | ... l2>m1, m3>e3, e4>f1, f2>g1 | -940/4237 | 223 synodic months | 6585.2392 | 6585.3213 | -1.25e-05 |
| Exeligmos pointer | ... f2>g1, g2>h1, h2>i1 | -235/12711 | 3 Saros | 19755.7175 | 19755.9639 | -1.25e-05 |
| Mercury epicycle (synodic) | fx51>me72, me89>me40>me20 (on b), pin + follower | 1513/480 | 1513 synodic periods / 480 y | 115.8733 | 115.8800 | -5.81e-05 |
| Venus epicycle (synodic) | fx51>vn44, vn34>vn26>r1 (on b), pin + follower | 289/462 | 289 synodic periods / 462 y | 583.8820 | 583.9200 | -6.51e-05 |
| True-Sun epicycle su56 (anomaly) | fx56>cp52>su56 (on CP), eccentric pin + follower | -1 | anomalistic year ~ tropical year | 365.2422 | 365.2422 | +0.00e+00 |
| Mars pin gear (synodic) | fx56>cp64, ma38>ma40>ma71 | 133/284 | 133 syn / 284 y | 779.9157 | 779.9400 | -3.12e-05 |
| Mars output (sidereal) | ... ma71 ~pin~ ma80s>ma80o | 151/284 | 151 sid / 284 y | 686.9456 | 686.9800 | -5.01e-05 |
| Jupiter pin gear (synodic) | fx56>cp64, ju45>ju40>ju43 | 315/344 | 315 syn / 344 y | 398.8677 | 398.8800 | -3.09e-05 |
| Jupiter output (sidereal) | ... ju43 ~pin~ ju65s>ju65o | 29/344 | 29 sid / 344 y | 4332.5282 | 4332.5890 | -1.40e-05 |
| Saturn pin gear (synodic) | fx56>cp52, sa61>sa40>sa68 | 427/442 | 427 syn / 442 y | 378.0727 | 378.0900 | -4.57e-05 |
| Saturn output (sidereal) | ... sa68 ~pin~ sa86s>sa86o | 15/442 | 15 sid / 442 y | 10762.4702 | 10759.2200 | +3.02e-04 |

## Kinematics (exact)

- Unknowns 45 (mobile bodies except frame, a, q); equations 44 = 37 Willis + 4 pin-slot + 3 followers.
- Rank **44**, degrees of freedom **1**, inconsistent constraints 0; rank with input w_b = 1: 45.
- Mean rates equal to `rate_abs_mean` for all bodies: True; targets exact: 22/22.

| Target | Expr | Expected | Solver | OK |
|---|---|---|---|---|
| crank | a | 223/48 | 223/48 | GREEN |
| mean Sun | b | 1 | 1 | GREEN |
| Moon (mean sidereal) | moon | 254/19 | 254/19 | GREEN |
| lunar apsidal line | e_table | -477/4237 | -477/4237 | GREEN |
| lunar anomaly phase (k1 relative to e3) | k@e_table | 56165/4237 | 56165/4237 | GREEN |
| Moon phase (q1 relative to Moon pointer, magnitude) | q@moon | 235/19 | 235/19 | GREEN |
| Metonic pointer | n | -5/19 | -5/19 | GREEN |
| Olympiad pointer | o | 1/4 | 1/4 | GREEN |
| Callippic pointer | cal | -1/76 | -1/76 | GREEN |
| Saros pointer | g | -940/4237 | -940/4237 | GREEN |
| Exeligmos pointer | i | -235/12711 | -235/12711 | GREEN |
| Dragon Hand (nodes) | t_nodes | -5/93 | -5/93 | GREEN |
| draconic month (Moon - nodes) | moon-t_nodes | 23717/1767 | 23717/1767 | GREEN |
| Mercury epicycle relative to b1 | x_me20@b | 1513/480 | 1513/480 | GREEN |
| Venus epicycle relative to b1 | x_r1@b | 289/462 | 289/462 | GREEN |
| true-Sun epicycle absolute | x_su56 | 0 | 0 | GREEN |
| Mars pin gear relative to CP | x_ma71@b | 133/284 | 133/284 | GREEN |
| Jupiter pin gear relative to CP | x_ju43@b | 315/344 | 315/344 | GREEN |
| Saturn pin gear relative to CP | x_sa68@b | 427/442 | 427/442 | GREEN |
| Mars output | t_mars | 151/284 | 151/284 | GREEN |
| Jupiter output | t_jupiter | 29/344 | 29/344 | GREEN |
| Saturn output | t_saturn | 15/442 | 15/442 | GREEN |

## Cosmos checks (section 5.8)

| Check | Values | State |
|---|---|---|
| elongation_mercury | max_abs_elongation_deg = 22.9545, limit_deg = 22.9545, marker_local_deg_is_minus_g0 = True | GREEN |
| elongation_venus | max_abs_elongation_deg = 46.0367, limit_deg = 46.0367, marker_local_deg_is_minus_g0 = True | GREEN |
| elongation_trueSun | max_abs_elongation_deg = 2.3880, limit_deg = 2.3880, marker_local_deg_is_minus_g0 = True | GREEN |
| retrograde_saturn | max_dev_from_180_deg = 8.527e-14, marker_local_deg = 0.0000, marker_is_180_plus_beta = True | GREEN |
| retrograde_jupiter | max_dev_from_180_deg = 0.0000, marker_local_deg = 0.0000, marker_is_180_plus_beta = True | GREEN |
| retrograde_mars | max_dev_from_180_deg = 0.0018, marker_local_deg = 150.0000, marker_is_180_plus_beta = True | GREEN |
| solar_apogee | apogee_longitude_deg = 65.5001 | GREEN |
| lunar_anomaly | amplitude_deg = 6.5796, asin_e_over_r_deg = 6.5796 | GREEN |
| pins_in_slots | max_angle_error_rad = 7.222e-11 | GREEN |

## Modules and centre distances (37 external meshes)

| Mesh | Carrier | Module | Centre distance | Error (mm) | Face overlap | eps | eps spec | 2D min signed | Backlash near | OK |
|---|---|---|---|---|---|---|---|---|---|---|
| b2~c1 | frame | 0.480000 | 24.480000 | 4.4e-11 | 1.30 | 1.391 | 1.391 | 0.0130 | 0.0130 | GREEN |
| c2~d1 | frame | 0.447200 | 16.099200 | 2.2e-11 | 1.30 | 1.361 | 1.361 | 0.0130 | 0.0130 | GREEN |
| d2~e2 | frame | 0.485500 | 38.597250 | 5.6e-11 | 1.00 | 1.398 | 1.398 | 0.0130 | 0.0130 | GREEN |
| b2~l1 | frame | 0.480000 | 24.480000 | 4.6e-11 | 1.50 | 1.391 | 1.391 | 0.0130 | 0.0130 | GREEN |
| l2~m1 | frame | 0.496600 | 36.996700 | 2.6e-11 | 1.50 | 1.413 | 1.413 | 0.0130 | 0.0130 | GREEN |
| m3~e3 | frame | 0.466000 | 58.250000 | 1.2e-11 | 1.40 | 1.397 | 1.397 | 0.0130 | 0.0130 | GREEN |
| e5~k1 | e_table | 0.512000 | 25.600000 | 4.8e-11 | 0.50 | 1.394 | 1.394 | 0.0130 | 0.0130 | GREEN |
| k2~e6 | e_table | 0.534000 | 26.700000 | 3.4e-12 | 0.50 | 1.394 | 1.394 | 0.0130 | 0.0130 | GREEN |
| e1~b3 | frame | 0.559400 | 17.900800 | 2.8e-11 | 1.30 | 1.359 | 1.359 | 0.0130 | 0.0130 | GREEN |
| e4~f1 | frame | 0.520300 | 62.696150 | 3.2e-11 | 1.30 | 1.423 | 1.423 | 0.0130 | 0.0130 | GREEN |
| f2~g1 | frame | 0.516700 | 21.701400 | 2.9e-11 | 1.20 | 1.376 | 1.376 | 0.0130 | 0.0130 | GREEN |
| g2~h1 | frame | 0.447500 | 17.900000 | 1.6e-11 | 1.00 | 1.358 | 1.358 | 0.0130 | 0.0130 | GREEN |
| h2~i1 | frame | 0.434700 | 16.301250 | 4.3e-11 | 1.20 | 1.340 | 1.34 | 0.0130 | 0.0130 | GREEN |
| m2~n1 | frame | 0.514000 | 17.476000 | 0.0e+00 | 1.50 | 1.336 | 1.336 | 0.0130 | 0.0130 | GREEN |
| n3~o1 | frame | 0.417100 | 24.400350 | 3.6e-15 | 1.10 | 1.404 | 1.404 | 0.0130 | 0.0130 | GREEN |
| n2~p1 | frame | 0.500000 | 18.750000 | 1.5e-11 | 1.30 | 1.340 | 1.34 | 0.0130 | 0.0130 | GREEN |
| p2~cal1 | frame | 0.500000 | 18.000000 | 5.7e-11 | 1.30 | 1.324 | 1.324 | 0.0130 | 0.0130 | GREEN |
| fx49~nd62 | b | 0.486486 | 27.000000 | 4.4e-11 | 1.00 | 1.400 | 1.4 | 0.0130 | 0.0130 | GREEN |
| nd64~nd48 | b | 0.482143 | 27.000000 | 9.5e-12 | 1.00 | 1.400 | 1.4 | 0.0130 | 0.0130 | GREEN |
| fx51~vn44 | b | 0.538947 | 25.600000 | 1.8e-11 | 1.00 | 1.390 | 1.39 | 0.0130 | 0.0130 | GREEN |
| vn34~vn26 | b | 0.521000 | 15.630000 | 5.9e-11 | 1.00 | 1.352 | 1.352 | 0.0130 | 0.0130 | GREEN |
| vn26~r1 | b | 0.521000 | 23.184500 | 1.5e-11 | 1.00 | 1.374 | 1.374 | 0.0130 | 0.0130 | GREEN |
| fx51~me72 | b | 0.538947 | 33.145263 | 1.7e-11 | 1.00 | 1.405 | 1.405 | 0.0130 | 0.0130 | GREEN |
| me89~me40 | b | 0.500000 | 32.250000 | 1.9e-11 | 1.00 | 1.401 | 1.401 | 0.0130 | 0.0130 | GREEN |
| me40~me20 | b | 0.500000 | 15.000000 | 3.8e-11 | 1.00 | 1.344 | 1.344 | 0.0130 | 0.0130 | GREEN |
| fx56~cp52 | b | 0.480000 | 25.920000 | 2.7e-11 | 1.00 | 1.399 | 1.399 | 0.0130 | 0.0130 | GREEN |
| cp52~su56 | b | 0.480000 | 25.920000 | 3.6e-11 | 1.00 | 1.399 | 1.399 | 0.0130 | 0.0130 | GREEN |
| fx56~cp64 | b | 0.480000 | 28.800000 | 4.5e-11 | 1.00 | 1.405 | 1.405 | 0.0130 | 0.0130 | GREEN |
| sa61~sa40 | b | 0.480000 | 24.240000 | 2.4e-11 | 1.00 | 1.392 | 1.392 | 0.0130 | 0.0130 | GREEN |
| sa40~sa68 | b | 0.480000 | 25.920000 | 2.4e-11 | 1.00 | 1.395 | 1.395 | 0.0130 | 0.0130 | GREEN |
| sa86s~sa86o | b | 0.480000 | 41.280000 | 1.9e-11 | 1.00 | 1.423 | 1.423 | 0.0130 | 0.0130 | GREEN |
| ju45~ju40 | b | 0.480000 | 20.400000 | 2.1e-12 | 1.00 | 1.382 | 1.382 | 0.0130 | 0.0130 | GREEN |
| ju40~ju43 | b | 0.480000 | 19.920000 | 4.1e-11 | 1.00 | 1.381 | 1.381 | 0.0130 | 0.0130 | GREEN |
| ju65s~ju65o | b | 0.480000 | 31.200000 | 2.2e-11 | 1.00 | 1.410 | 1.41 | 0.0130 | 0.0130 | GREEN |
| ma38~ma40 | b | 0.480000 | 18.720000 | 2.5e-11 | 1.00 | 1.376 | 1.376 | 0.0130 | 0.0130 | GREEN |
| ma40~ma71 | b | 0.480000 | 26.640000 | 1.2e-11 | 1.00 | 1.396 | 1.396 | 0.0130 | 0.0130 | GREEN |
| ma80s~ma80o | b | 0.480000 | 38.400000 | 1.9e-11 | 1.00 | 1.420 | 1.42 | 0.0130 | 0.0130 | GREEN |

Tip lands: minimum nominal tip land 0.228 m (p2); minimum thinned (j = 0.03) tip land 0.0964 mm; root fillet between 0.144 m and 0.200 m (reduced where two fillets would not fit).

## Verification results

- Spec SHA-256 `18934c80264941ed315ced4273d0b16d733132a296d64e25300bea5576ab86b3` (identical); 24/24 section fingerprints: True.
- Phasing: 28 spur components, 65 gears phased (b1, b0 at local 0; crowns pre-phased).
- Pre-filter: 228 parts, 4251 z-overlapping pairs of different bodies, **0 conflicts**, 83 intended contacts (meshes, pin-slots, shafts in plate holes, slider pins in grooves), 168 pairs retained for the BVH.
- a1 keep-out: largest radius carried by b between z 4.6 and 33.73 (b1 excepted): 63.1471 mm (limit 63.6).
- Follower sectors (relative to b): {'mercury_follower': [-48.954, -3.046], 'venus_follower': [108.963, 201.037], 'true_sun_follower': [147.612, 152.388]}; no b-carried object in them except the intended pins.
- Driver expressions: 47 bodies, max length 120, max error 6.719e-13 rad vs the solver over 200 samples in [-50, 50].
- Blender drivers: 51 on objects, all valid True, all simple True, expressions identical True; readback max error 5.999e-07 rad over 50 float32 crank values.
- Cycle closure: metonic after 19.0000 y: 0.0000 rad, olympiad after 4.0000 y: 0.0000 rad, callippic after 76.0000 y: 0.0000 rad, saros after 18.0298 y: 3.020e-07 rad.
- Crank F-curve: {'1': 0.0, '61': 0.5, '481': 4.0, '961': 8.0} (frames 1/61/481/961), extrapolation LINEAR.
- BVH (world coordinates, overlap()): (a) 39 meshes x 50 positions per pitch: 0 overlaps; (b) 7 pin-slots/followers + 2 spiral sliders x 72 positions per relative cycle: 0 overlaps; (c) 168 retained pairs x 240 crank values (120 on [0,1] + 120 random on [0,76], seed 20260924): 0 overlaps. Sanity test: known intersections and a half-pitch mis-phased gear are detected.
- Meshes: 228 mesh objects, all closed/manifold/contiguous: True; extruded volumes = area x (float32(z1) - float32(z0)), max relative error 3.312e-13.
- Spirals: slider pin vs rho(psi): {'metonic': '1.206e-04 mm', 'saros': '1.150e-04 mm'}.
- Units: ['METRIC', 'MILLIMETERS', 0.0010000000474974513]; controller `crank` and `patina` float: True / True.

## FONT texts (excluded from manifold, BVH and print checks)

Built-in font, extrusion 0.025 (0.05 thick), body frame, collection AM_DIALS. Missing glyphs (compared with the notdef box of U+10300): none. The stigma is written ΙΣΤ as in the spec.

| Text | Content | z range | Closest moving part overlapping in xy (dz, part) | OK |
|---|---|---|---|---|
| txt_zodiac_00 | ΚΡΙΟΣ | 41.600..41.650 | 1.000 date_pointer | GREEN |
| txt_zodiac_01 | ΤΑΥΡΟΣ | 41.600..41.650 | 1.000 date_pointer | GREEN |
| txt_zodiac_02 | ΔΙΔΥΜΟΙ | 41.600..41.650 | 1.000 date_pointer | GREEN |
| txt_zodiac_03 | ΚΑΡΚΙΝΟΣ | 41.600..41.650 | 1.000 date_pointer | GREEN |
| txt_zodiac_04 | ΛΕΩΝ | 41.600..41.650 | 1.000 date_pointer | GREEN |
| txt_zodiac_05 | ΠΑΡΘΕΝΟΣ | 41.600..41.650 | 1.000 date_pointer | GREEN |
| txt_zodiac_06 | ΧΗΛΑΙ | 41.600..41.650 | 1.000 date_pointer | GREEN |
| txt_zodiac_07 | ΣΚΟΡΠΙΟΣ | 41.600..41.650 | 1.000 date_pointer | GREEN |
| txt_zodiac_08 | ΤΟΞΟΤΗΣ | 41.600..41.650 | 1.000 date_pointer | GREEN |
| txt_zodiac_09 | ΑΙΓΟΚΕΡΩΣ | 41.600..41.650 | 1.000 date_pointer | GREEN |
| txt_zodiac_10 | ΥΔΡΟΧΟΟΣ | 41.600..41.650 | 1.000 date_pointer | GREEN |
| txt_zodiac_11 | ΙΧΘΥΕΣ | 41.600..41.650 | 1.000 date_pointer | GREEN |
| txt_month_00 | ΘΩΥΘ | 42.450..42.500 | 0.150 date_pointer | GREEN |
| txt_month_01 | ΦΑΩΦΙ | 42.450..42.500 | 0.150 date_pointer | GREEN |
| txt_month_02 | ΑΘΥΡ | 42.450..42.500 | 0.150 date_pointer | GREEN |
| txt_month_03 | ΧΟΙΑΚ | 42.450..42.500 | 0.150 date_pointer | GREEN |
| txt_month_04 | ΤΥΒΙ | 42.450..42.500 | 0.150 date_pointer | GREEN |
| txt_month_05 | ΜΕΧΙΡ | 42.450..42.500 | 0.150 date_pointer | GREEN |
| txt_month_06 | ΦΑΜΕΝΩΘ | 42.450..42.500 | 0.150 date_pointer | GREEN |
| txt_month_07 | ΦΑΡΜΟΥΘΙ | 42.450..42.500 | 0.150 date_pointer | GREEN |
| txt_month_08 | ΠΑΧΩΝ | 42.450..42.500 | 0.150 date_pointer | GREEN |
| txt_month_09 | ΠΑΥΝΙ | 42.450..42.500 | 0.150 date_pointer | GREEN |
| txt_month_10 | ΕΠΙΦΙ | 42.450..42.500 | 0.150 date_pointer | GREEN |
| txt_month_11 | ΜΕΣΟΡΗ | 42.450..42.500 | 0.150 date_pointer | GREEN |
| txt_month_12 | ΕΠΑΓΟΜΕΝΑΙ | 42.450..42.500 | 0.150 date_pointer | GREEN |
| txt_olympiad_0 | ΙΣΘΜΙΑ | -16.550..-16.500 | 0.850 metonic_pointer | GREEN |
| txt_olympiad_1 | ΟΛΥΜΠΙΑ | -16.550..-16.500 | 0.850 metonic_pointer | GREEN |
| txt_olympiad_2 | ΝΕΜΕΑ | -16.550..-16.500 | 0.850 metonic_pointer | GREEN |
| txt_olympiad_3 | ΠΥΘΙΑ | -16.550..-16.500 | 0.850 metonic_pointer | GREEN |
| txt_exeligmos_1 | Η | -16.550..-16.500 | 0.850 saros_pointer | GREEN |
| txt_exeligmos_2 | ΙΣΤ | -16.550..-16.500 | 0.850 saros_pointer | GREEN |

## Parts by status

**SURVIVING** (93): main_plate, stud_c, stud_l, a1, a_shaft, b1, b2, b1_hub, b_hub, short_pillar_1, short_tenon_1, short_pillar_2, short_tenon_2, long_pillar_1, long_tenon_1, long_pillar_2, long_tenon_2, long_pillar_3, long_tenon_3, long_pillar_4, long_tenon_4, d_plate, d_post_1, d_post_2, stud_r1, r1, hub_r1, venus_disk, pin_venus, b3, moon_arbor, q1, q_arbor, c2, c1, d1, d2, e2, e5, e3, e4, e1, e6, k1, k2, l2, l1, m1, m2, f1, f2, g1, g2, h1, h2, i1, o1, shaft_d, shaft_e_inner, pipe_e, shaft_f, shaft_g, shaft_h, shaft_i, shaft_o, hub_c, hub_l, boss_k, stud_kp, e4_spacers, pin_lunar, metonic_pointer, metonic_slider, metonic_slider_pin, saros_pointer, saros_slider, saros_slider_pin, olympiad_pointer, exeligmos_pointer, metonic_cells, metonic_rim, saros_cells, saros_rim, olympiad_dial, exeligmos_dial, zodiac_ring, zodiac_marks, calendar_ring, calendar_marks, parapegma_1, parapegma_lines_1, parapegma_2, parapegma_lines_2

**RECONSTRUCTED** (26): back_plate, front_plate, frame_pillar_1, frame_pillar_2, frame_pillar_3, frame_pillar_4, date_pointer, m3, n1, n3, n2, p1, p2, cal1, shaft_m, shaft_n, shaft_p, shaft_cal, callippic_pointer, callippic_dial, case_left, case_bottom, case_top, case_right, case_cover_front, case_cover_back

**HYPOTHETICAL** (109): crank_bracket, fixed_tube, fx51, fx49, fx56, sub_plate, spacer_ring, standoff_1, standoff_2, standoff_3, crank_arm, crank_knob, b0, t_meanSun, t_date, mean_sun_bar, mean_sun_post, strap, cp, stud_spA, stud_spB, stud_spC, stud_me40, stud_me20, stud_vn26, stud_sa40, stud_ju40, stud_ma40, boss_sa68, stud_sa86s, boss_ju43, stud_ju65s, boss_ma71, stud_ma80s, me72, me89, nd62, nd64, vn44, vn34, me40, me20, vn26, cp52, sa61, cp64, ma38, ju45, su56, sa40, sa68, sa86s, ju40, ju43, ju65s, ma40, ma71, ma80s, hub_spA, hub_spB, hub_spC, hub_me40, hub_me20, hub_vn26, shaft_cp52, shaft_cp64, shaft_su56, crank_disc_su56, hub_sa40, hub_ju40, hub_ma40, mercury_disk, pin_saturn, pin_jupiter, pin_mars, pin_mercury, pin_trueSun, moon_pointer, moon_hanger_1, moon_hanger_2, phase_sphere_dark, phase_sphere_silver, nd48, t_nodes, dragon_hand, t_mercury, mercury_follower, ring_mercury, marker_mercury, t_venus, venus_follower, ring_venus, marker_venus, t_trueSun, true_sun_follower, ring_trueSun, marker_trueSun, t_mars, ma80o, ring_mars, marker_mars, t_jupiter, ju65o, ring_jupiter, marker_jupiter, t_saturn, sa86o, ring_saturn, marker_saturn

Collections: {'AM_CASE': 6, 'AM_DIALS': 72, 'AM_HELPERS': 57, 'AM_HYPOTHETICAL': 42, 'AM_RECONSTRUCTED': 11, 'AM_STRUCTURE': 81, 'AM_SURVIVING': 47}

## Print export

| Profile | Files | 2D check | STL re-import rel. err | Larger than the bed | Fragile tips (tip land mm) | Walls |
|---|---|---|---|---|---|---|
| resin_x1 | 228 STL + 3MF (13.7 MB, 228 objects, closed True) | True (backlash near 0.0217..0.0218 mm) | b1 6.5e-07, a1 1.4e-04, main_plate 0.0e+00, marker_trueSun 2.4e-07 | main_plate, back_plate, front_plate, b1, cp, ring_saturn, metonic_cells, metonic_rim, saros_cells, saros_rim, zodiac_ring, zodiac_marks, calendar_ring, calendar_marks, case_left, case_right, case_cover_front, case_cover_back | h2 0.086, p2 0.085 | 0 below 0.40 mm (min 0.502) |
| resin_x1_5 | 228 STL + 3MF (13.8 MB, 228 objects, closed True) | True (backlash near 0.0346..0.0349 mm) | b1 2.0e-06, a1 9.6e-05, main_plate 0.0e+00, marker_trueSun 6.4e-07 | main_plate, back_plate, front_plate, sub_plate, b1, cp, ring_venus, ring_trueSun, ring_mars, ring_jupiter, ring_saturn, e3, e4, metonic_cells, metonic_rim, saros_cells, saros_rim, zodiac_ring, zodiac_marks, calendar_ring, calendar_marks, parapegma_1, parapegma_2, case_left, case_bottom, case_top, case_right, case_cover_front, case_cover_back | h2 0.126, p2 0.124 | 0 below 0.50 mm (min 0.752) |
| fdm_x2 | 228 STL + 3MF (13.9 MB, 228 objects, closed True) | True (backlash near 0.0866..0.0870 mm) | b1 1.7e-06, a1 3.5e-05, main_plate 0.0e+00, marker_trueSun 2.4e-07 | main_plate, back_plate, front_plate, b1, cp, metonic_cells, metonic_rim, saros_cells, saros_rim, zodiac_ring, zodiac_marks, calendar_ring, calendar_marks, parapegma_1, parapegma_lines_1, parapegma_2, parapegma_lines_2, case_left, case_bottom, case_top, case_right, case_cover_front, case_cover_back | b0 0.188, me20 0.188, d1 0.174, m2 0.156, g2 0.156, h2 0.114, n2 0.149, p2 0.111 | 0 below 0.80 mm (min 1.002) |

## Renders

Files: front34.png present, front.png present, back.png present, exploded.png present, antikythera.mp4 present. Stills rendered with Cycles on Metal (Apple M4 GPU - 8 cores), 1920x1080, 256 samples, OpenImageDenoise on GPU, after a warm-up render (kernel compilation). Animation: EEVEE, 480 frames 1280x720 at 24 fps, crank 0 -> 4 years, PNG frames encoded once through the sequencer to H.264/MP4 (movieclip frame_duration = 480).

## Unresolved defaults applied (spec)

- Axis XY coordinates are derived (not published); residuals against CT distances are within ~0.8 mm.
- Angles of H, I, O, P and the K direction on e3 are unpublished design choices.
- Cosmos ring radii are visual estimates from F21 Fig. 7.
- True-Sun eccentricity d = i/24 (Hipparchus); F21SI Table S9 does not give it. Solar apogee set at longitude 65.5 deg (Hipparchus) through followers[trueSun].pin_phase_deg = 84.5.
- Crown teeth (a1, q1) are envelope-generated against the involute spur (clearance 0.04 per flank) instead of the ancient hand-filed form.
- Lunar pin radius 9.6 mm (alternative 9.9).
- Calendar hole count 354 (alternatives 355, 365).
- Epoch phases are uncalibrated (all 0 at crank 0).
- Rear-layout handedness follows Price 1974 (mirror not excluded).
- Main Plate modelled 2.0 thick (Price: double sheet 2 x 2.0-2.3); turntable raised 3.05 mm instead of 2.7 to keep 0.15 mm axial gaps.

## Decisions

- Spec loaded read-only from `spec/antikythera.json`; every constant read as float64 from it — the spec is the single source of truth.
- Solver angles of linear bodies are reduced modulo 2π exactly with `Fraction(rate)*Fraction(t)` — avoids float drift for large t.
- Target `a` = |w_b|·z_b1/z_a1 and `q@moon` = |w_b − w_moon|·z_b0/z_q1, computed from the two crown meshes — both are outside the linear system (§5.1).
- Root fillet = 0.2·m reduced (down to 0.144·m for z ≥ 100) when two fillets would not fit in the narrow 30° root space — keeps a root arc; the fillet stays below rf + 0.2 m, never reached by the mating tip (rf + 0.25 m).
- Lightening windows only when (rim − hub) ≥ 2 mm; count 4/5/6 for rim radius < 10 / < 15 / ≥ 15 mm; arms along local +x — simplest reading of `tooth.lightening` (fx56 has no window).
- e3: 5 windows between 4 and 40 mm, K arm 9.0 mm wide at −38°, other arms 0.12·r — spec asks ≥ 8 for the K arm.
- b1: rim (inner 53) + hub (9) + 4 spokes 15.5 wide; spoke features (flat, bearing OD, pierced block) not modelled because the studs/post are fused to b — cosmetic.
- b1 hub/rivets modelled as an annulus r 3.2..9.0, z 6.65..7.85 — spec "hub and rivets to 7.85".
- c and l get a hub r 1.25..2.5 joining their two wheels — the two wheels of one body must be connected.
- Pillars: small dimension radial; tenons 2.4×3.0 (short) and 4.0×5.0 (long) through matching Strap/CP holes — spec gives only "tenon_to".
- D-plate posts at 22 mm along the 161° line, ±8 mm across — clear of every other part between z 18.8 and 22.85.
- Mean-Sun bar: collar r 3.4, bar 3 wide, end block r 2.2 at Dblock, post r 1.5 — dimensions not given.
- Mercury/Venus/true-Sun levers: bar 3 mm wide, round end, hubs r 4.5 / 5.2 / 6.0 — slot geometry exactly per spec.
- Mercury pin z 12.65..14.9 (`shafts.pins`) instead of 12.6 (`structure.mercury_disk.pin`) — ends inside the slot instead of flush with the lever face (no coplanar contact).
- Moon pointer: hub r 3, bar 3 wide to 62 with pointed tip, window boss r 5.1 with window r 4.1; hangers 2.4 wide (v) — only length/width/window given.
- Back pointers: hub r 2.5 (spirals) / 2.0 (subsidiary), width 2.0 / 1.5, pointed; spiral sliders: block 3.2×3.0 at z −18.35..−17.4 and pin r 0.5 up to z −15.6 (ends inside the groove).
- Back dial marks (cells, rims r 71.2..71.7, subsidiary rings and sector lines) raised 0.3 mm (z −16.8..−16.5) outside the sweep of the pointers; subsidiary sector lines start 0.3 mm beyond the pointer tip.
- Front dials: zodiac ring 0.1 mm raised at z 41.5, 360 ticks; calendar ring per spec with 365 ticks; front-plate hole circle 354 × Ø0.8; parapegma lines are 0.4 mm raised strips (placeholder text).
- Cosmos rings: annulus from the tube inner radius to the ring outer radius (disc + annulus in one piece).
- Case: 4 walls 5 mm (right wall with the Ø3.1 crank hole) + front/back covers hidden (viewport and render).
- Collections: 69 gears and status-bearing mechanism parts in `AM_<status>`; plates, shafts, tubes, studs, hubs, pins and crank parts in `AM_STRUCTURE`; dials/pointers/markers/texts in `AM_DIALS`; case in `AM_CASE`; body empties, controller, cameras, lights in `AM_HELPERS`. Every object carries `status`.
- Frame-child body empties are top-level objects (only children of b, e_table and moon are parented) — world = local for them.
- Body drivers: default F-curve keys cleared (pass-through driver); non-linear bodies read other empties with SINGLE_PROP on `rotation_euler[i]`; linear sub-terms are inlined with exact integer fractions.
- Volume check: contour area computed on the float32-rounded 2D contour (vertices are float32), exactly like the z range of §5.5.
- Pre-filter follower rule applied to every object carried by b (b itself and its children), except coaxial tubes of b (plain radial test).
- Text z-clearance rule interpreted per xy footprint: a moving part whose swept region overlaps the text footprint must be ≥ 0.1 mm away in z (the subsidiary pointers are only 0.1 mm from the plate, so a global reading is impossible).

## Fallbacks (section 8) and deviations

- None: no crown tightening, no flank densification, no remodelling of a non-toothed part, no intermediate empties; Cycles Metal used for the stills.
