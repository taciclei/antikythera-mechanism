# Antikythera Mechanism: a functional, verified 3D reconstruction

**English** · [Français](README.fr.md) · [Español](README.es.md) · [Deutsch](README.de.md) · [Italiano](README.it.md) · [Português](README.pt.md) · [Ελληνικά](README.el.md) · [中文](README.zh.md) · [日本語](README.ja.md)

[![Lean proofs](https://github.com/taciclei/antikythera-mechanism/actions/workflows/lean.yml/badge.svg)](https://github.com/taciclei/antikythera-mechanism/actions/workflows/lean.yml)

![The reconstructed mechanism, front three-quarter view](docs/images/front34.jpg)


https://github.com/user-attachments/assets/c810d3ee-ecfa-46e3-b11d-f919c3ae2cd9



https://github.com/user-attachments/assets/40b1f61b-5fb0-4b54-bd1c-1ba1f423a424


The Antikythera Mechanism is a hand-cranked bronze astronomical calculator built in Greece in the 2nd or 1st century BC and recovered from a shipwreck in 1901. It is the oldest known complex geared machine. This repository contains a complete 3D reconstruction of it in **Blender 5.2**:

- all **69 gears** have their real tooth counts;
- the teeth are conjugate involute teeth, so every pair meshes and actually works;
- every gear train has been **checked in exact fractions** against the astronomical cycle it models;
- the parts have been **checked for collisions** over the whole range of motion.

The whole build was produced in a single pass by Claude Opus 5.5 from one self-contained master prompt ([`PROMPT_OPUS.md`](PROMPT_OPUS.md)), then verified independently.

## Highlights

- **69 gears**, tagged by how certain they are:
  - 30 **surviving**, physically present in the fragments (CT scans);
  - 7 **reconstructed**, from strong evidence;
  - 32 **hypothetical**, from the model of Freeth et al. 2021.

  Each status has its own Blender collection, so each group can be hidden or shown.
- **Exact mathematics.** 1 turn of the main wheel b1 is 1 year. The mechanism has exactly **one degree of freedom** (the crank), and all 22 targets match exactly as fractions (sample below).

  | Output | Exact rate (turns/year) | Cycle |
  |---|---|---|
  | Moon (mean) | 254/19 | 254 sidereal months in 19 years |
  | Metonic dial | −5/19 | 5 turns = 19 years = 235 lunar months |
  | Saros dial | −940/4237 | 4 turns = 223 lunar months |
  | Lunar nodes (Dragon Hand) | −5/93 | 18.6 years, backwards |
  | Venus | 289/462 relative to b1 | 289 synodic periods in 462 years |
- **Formally proved in Lean 4.** [`lean/`](lean/README.md) contains 193 theorems, checked by Lean's kernel with Mathlib, with no `sorry`:
  - the mean-rate kinematics has exactly **one degree of freedom**, and every rate follows from the tooth counts;
  - the 22 targets hold, and so do the Metonic, Saros, Exeligmos, Callippic and Olympiad cycles and the planetary period relations;
  - the 37 centre distances are correct to within 10⁻⁶ mm;
  - the pin-and-slots keep their mean rates, and the lunar anomaly amplitude lies between 6.579° and 6.581°.

  Mutation tests show that Lean rejects a wrong tooth count, a wrong target or a misplaced axis.
- **It works mechanically.**
  - Centre distances are exact to 10⁻⁶ mm, and every contact ratio is ≥ 1.2.
  - There is **0 interpenetration** on thousands of 3D (BVH) samples: every mesh over a tooth pitch, every pin-and-slot cycle, and 168 pairs of parts at 240 crank positions.
- **The Moon speeds up and slows down with round gears**, not oval ones. A pin-and-slot on the rotating e3 turntable reproduces Hipparchus' lunar anomaly (±6.58°).
- **Planets move backwards at the right time.** Mars, Jupiter and Saturn go retrograde at opposition (180° ± 0.03°), and Mercury and Venus stay within their maximum elongations.
- **One crank drives everything.** All motion comes from `AM_Controller["crank"]` in years, through simple-expression drivers, so the file animates without enabling Python scripts.
- **Readable display.** Each of the seven ancient "planets" has its own colour and a label that follows it (Sun, Moon, Mercury, Venus, Mars, Jupiter, Saturn), plus a legend.
- **Museum lighting.** The scene has a dark cyclorama backdrop and warm softboxes, rendered with AgX colour. This setup was chosen from three designs rendered side by side.
- **Exploded view.** Move `AM_Controller["explode"]` from 0 to 1 and every part slides along the stacking axis.
- **3D printing.** One STL per part plus a full 3MF, in three profiles: resin ×1, resin ×1.5 and FDM ×2.

| Front dial | Back dials |
|---|---|
| ![Front dial with coloured, labelled planets](docs/images/front.jpg) | ![Metonic and Saros spirals](docs/images/back.jpg) |

| Exploded view | Inside, opened |
|---|---|
| ![Exploded still](docs/images/exploded.jpg) | ![Frame of the exploded video](docs/images/exploded_video_frame.jpg) |

## Videos

- [`antikythera.mp4`](build/out/renders/antikythera.mp4): 20 s. The crank turns 4 years, and the planets, Moon and back dials all move.
- [`antikythera_eclate.mp4`](build/out/renders/antikythera_eclate.mp4): 15 s exploded view. The mechanism opens layer by layer while the gears keep turning, then closes again.

Planets that sometimes move **backwards** in the videos are not a bug. This is the **retrograde motion** seen from Earth, and the mechanism was built to show it. The Dragon Hand (the lunar nodes) always turns backwards.

## Quick start

1. Install **Blender 5.2** or later.
2. Open [`build/out/am.blend`](build/out/am.blend) and press **Space** to play the animation.
3. Select `AM_Controller` and change its custom properties:
   - `crank`: years; 1 is one turn of b1;
   - `explode`: 0 to 1;
   - `patina`: 0 is new bronze, 1 is museum patina.
4. Use the Outliner to hide collections:
   - `AM_CASE` and `AM_DIALS` to see the gearing;
   - `AM_HYPOTHETICAL` to keep only what is attested;
   - `AM_LABELS` to remove the labels;
   - `AM_STAGE` to remove the lighting set.
5. Click any part to read its custom properties: `status`, `role`, `teeth`, `module` and `sources`.

### Re-run the verification

Use the Python bundled with Blender. The paths below are for macOS; adapt them on other systems.

```sh
PY=/Applications/Blender.app/Contents/Resources/5.2/python/bin/python3.13
BL=/Applications/Blender.app/Contents/MacOS/Blender

$PY tools/validate_spec.py          # exact linear solve (1 DOF, 22 targets), centre distances, collision screening
$PY tools/check_kinematics.py       # pin-and-slot laws, followers, elongations, retrogrades, solar apogee
cd build && $PY -m unittest discover -s tests && $PY -m am.verify --stage all && cd ..
$BL -b build/out/am.blend --python-exit-code 1 -P tools/crosscheck_blend.py   # Blender rotations vs an independent solver
```

[`build/README.md`](build/README.md) lists every build, check, export and render step, with one command per step.

### Check the formal proofs (Lean 4)

Install [elan](https://lean-lang.org/install) once, then:

```sh
cd lean
lake exe cache get    # download the compiled Mathlib (about 5 GB)
lake build            # check every proof; warnings are errors, so success means no sorry
cd ..
python3 tools/lean_mutation_test.py   # Lean must reject 9 deliberately wrong mechanisms
```

[`lean/README.md`](lean/README.md) lists what is proved, module by module, and what is not.

### Rebuild everything from the master prompt

In an **empty** folder, with [Claude Code](https://claude.com/claude-code):

```sh
claude -p --model 'claude-opus-5-5[1m]' --effort xhigh --permission-mode acceptEdits \
  --allowedTools Bash Read Write Edit Glob Grep < PROMPT_OPUS.md
```

- [`prompts/PROMPT_OPUS_v1_validated.md`](prompts/PROMPT_OPUS_v1_validated.md) is the exact version that produced this build in one pass (89 min).
- [`PROMPT_OPUS.md`](PROMPT_OPUS.md) is v1.2. It adds the planet colours and labels, the museum staging, the explode slider and the exploded video. All of these were added to this build afterwards with the scripts in `tools/`, and v1.2 has not yet been rerun from scratch.

## How it was made

1. **Research.** Parallel agents read the primary sources: Freeth et al. 2006, 2008 and 2021 (with the Supplementary Information), Price 1974, Budiselic et al. 2020, Woan & Bayley 2024, Anastasiou et al. 2014, and others. The results were reconciled into one data set, then checked by a sceptic agent.
2. **Specification.** [`spec/antikythera.json`](spec/antikythera.json) is the single source of truth. It gives the teeth, module, axis position, z range and bore of every gear, and every shaft, stud, boss, pin, dial and material. It is generated by `tools/make_spec.py`, which fixes 22 geometric impossibilities in the published data (for example, b2 cannot mesh with both c1 and l1 at the published distances). Every centre distance is solved exactly.
3. **Independent checks.** `tools/validate_spec.py` and `tools/check_kinematics.py` share no code with the generator, and mutation tests confirm they catch injected errors.
4. **Crown teeth by envelope.** `tools/crown_envelope.py` computes the contrate teeth of a1 and q1 as the region the mating teeth never sweep. `tools/test_crowns_blender.py` then checks them with BVH in Blender.
5. **Adversarial reviews.** Two rounds of independent reviewers covered data, the Blender API tested live, executability and geometry, and found 5 blockers and about 60 other issues. All of them are fixed.
6. **One-pass build** by a fresh Opus 5.5 session from the prompt alone: 131 turns, about 5,000 lines of code, and all acceptance criteria green.
7. **Independent verification** of the result: tests, exact checks, the full BVH check, and a cross-check of every body in `am.blend` against the independent solver (7·10⁻⁷ rad).
8. **Formal proofs.** `tools/make_lean.py` translates the spec into Lean 4. The kinematics, targets and centre distances are proved from it. Hand-written modules add the pin-and-slot analysis and the astronomy, and adversarial reviewers and mutation tests checked that each statement says what it claims.

## Repository layout

```
PROMPT_OPUS.md            master prompt (v1.2), self-contained; embeds the full JSON spec + SHA-256
prompts/                  the prompt version validated by the one-pass build (v1)
spec/antikythera.json     single source of truth (gears, axes, shafts, trains, dials, staging, video)
research/                 raw multi-agent research results with source URLs
tools/                    spec generator, validators, crown envelopes, Lean generator, annotation/staging/explode/render scripts
lean/                     Lean 4 + Mathlib proofs: kinematics, targets, centre distances, pin-and-slot, astronomy
build/                    the project generated by the one-pass build (am/, blender_scripts/, tests/, README)
build/out/                am.blend, verification report (report.md/html), checks, print files, renders, videos
docs/                     dossier (HTML) and images
```

## Honest limits

- The planetary trains, the lunar nodes and the true Sun follow the **hypothetical** model of Freeth et al. 2021. A working animation does not prove how the original was built.
- Some quantities are not published. For these the spec uses documented defaults, listed in `spec/antikythera.json` → `unresolved_defaults`:
  - axis angles on the rear plate;
  - cosmos ring radii;
  - starting phases (the epoch is uncalibrated).
- The Lean proofs cover the mean-rate kinematics, the targets, the centre distances and the pin-and-slot and follower laws. Contact ratio, face overlap, undercut and collisions are checked by the Python tools and in Blender, not in Lean.
- The teeth are conjugate involutes (a 30° rack, which is the ancient equilateral-triangle tooth), not the hand-filed triangles of the original.
- Planet colours are for readability only; they are not historical.

## Main sources

- T. Freeth et al., "A Model of the Cosmos in the ancient Greek Antikythera Mechanism", *Scientific Reports* 11, 5821 (2021), with its Supplementary Information.
- T. Freeth et al., "Decoding the ancient Greek astronomical calculator known as the Antikythera Mechanism", *Nature* 444, 587 (2006).
- T. Freeth, A. Jones, J. Steele, Y. Bitsakis, "Calendars with Olympiad display and eclipse prediction on the Antikythera Mechanism", *Nature* 454, 614 (2008).
- T. Freeth & A. Jones, "The Cosmos in the Antikythera Mechanism", ISAW Papers 4 (2012).
- D. de Solla Price, *Gears from the Greeks* (1974).
- C. Budiselic et al. (2020); G. Woan & J. Bayley (2024): calendar ring hole count.
- M. Anastasiou et al. (2014): the back-dial spirals.

The full list with URLs is in `spec/antikythera.json` → `sources`.

## Licence

- **Code**: MIT ([`LICENSE`](LICENSE)).
- **Renders, videos, 3D model, print files and texts**: CC BY 4.0 ([`LICENSE-MEDIA.md`](LICENSE-MEDIA.md)).
- **Scholarly data**: please cite the works above.

---

Built with [Claude Code](https://claude.com/claude-code) (Claude Opus 5 / 5.5) for taciclei.
