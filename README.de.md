# Mechanismus von Antikythera: eine funktionsfähige, verifizierte 3D-Rekonstruktion

[English](README.md) · [Français](README.fr.md) · [Español](README.es.md) · **Deutsch** · [Italiano](README.it.md) · [Português](README.pt.md) · [Ελληνικά](README.el.md) · [中文](README.zh.md) · [日本語](README.ja.md)

[![Lean proofs](https://github.com/taciclei/antikythera-mechanism/actions/workflows/lean.yml/badge.svg)](https://github.com/taciclei/antikythera-mechanism/actions/workflows/lean.yml)

![Der rekonstruierte Mechanismus, Dreiviertelansicht von vorn](docs/images/front34.jpg)

https://github.com/user-attachments/assets/c810d3ee-ecfa-46e3-b11d-f919c3ae2cd9

https://github.com/user-attachments/assets/40b1f61b-5fb0-4b54-bd1c-1ba1f423a424


Der Mechanismus von Antikythera ist ein von Hand gekurbelter astronomischer Rechner aus Bronze, der im 2. oder 1. Jahrhundert v. Chr. in Griechenland gebaut und 1901 aus einem Schiffswrack geborgen wurde. Er ist die älteste bekannte komplexe Maschine mit Zahnradgetriebe. Dieses Repository enthält eine vollständige 3D-Rekonstruktion in **Blender 5.2**:

- alle **69 Zahnräder** haben ihre tatsächlichen Zähnezahlen;
- die Zähne sind konjugierte Evolventenzähne, sodass jedes Radpaar sauber kämmt und tatsächlich funktioniert;
- jeder Räderzug wurde anhand des astronomischen Zyklus, den er nachbildet, **in exakten Brüchen geprüft**;
- die Teile wurden über den gesamten Bewegungsbereich **auf Kollisionen geprüft**.

Der gesamte Aufbau wurde von Claude Opus 5.5 in einem einzigen Durchlauf aus einem einzigen, in sich geschlossenen Master-Prompt ([`PROMPT_OPUS.md`](PROMPT_OPUS.md)) erzeugt und anschließend unabhängig verifiziert.

## Besonderheiten

- **69 Zahnräder**, gekennzeichnet nach dem Grad ihrer Gewissheit:
  - 30 **erhalten**, physisch in den Fragmenten vorhanden (CT-Scans);
  - 7 **rekonstruiert**, auf Grundlage starker Belege;
  - 32 **hypothetisch**, nach dem Modell von Freeth et al. 2021.

  Jeder Status hat eine eigene Blender-Collection, sodass sich jede Gruppe aus- und einblenden lässt.
- **Exakte Mathematik.** 1 Umdrehung des Hauptrads b1 entspricht 1 Jahr. Der Mechanismus hat genau **einen Freiheitsgrad** (die Kurbel), und alle 22 Zielwerte stimmen als Brüche exakt überein (Auswahl unten).

  | Abtrieb | Exakte Rate (Umdrehungen/Jahr) | Zyklus |
  |---|---|---|
  | Mond (mittlerer) | 254/19 | 254 siderische Monate in 19 Jahren |
  | Meton-Zifferblatt | −5/19 | 5 Umdrehungen = 19 Jahre = 235 Mondmonate |
  | Saros-Zifferblatt | −940/4237 | 4 Umdrehungen = 223 Mondmonate |
  | Mondknoten (Drachenzeiger) | −5/93 | 18.6 Jahre, rückwärts |
  | Venus | 289/462 relativ zu b1 | 289 synodische Perioden in 462 Jahren |
- **Formal bewiesen in Lean 4.** [`lean/`](lean/README.md) enthält 193 Theoreme, die vom Kernel von Lean mit Mathlib geprüft werden, ohne ein einziges `sorry`:
  - die Kinematik der mittleren Raten hat genau **einen Freiheitsgrad**, und jede Rate ergibt sich aus den Zähnezahlen;
  - die 22 Zielwerte gelten, ebenso die Meton-, Saros-, Exeligmos-, Kallippos- und Olympiadenzyklen sowie die Periodenbeziehungen der Planeten;
  - die 37 Achsabstände stimmen auf 10⁻⁶ mm genau;
  - die Stift-Schlitz-Mechanismen behalten ihre mittleren Raten bei, und die Amplitude der Mondanomalie liegt zwischen 6.579° und 6.581°.

  Mutationstests zeigen, dass Lean eine falsche Zähnezahl, einen falschen Zielwert oder eine falsch platzierte Achse zurückweist.
- **Er funktioniert mechanisch.**
  - Die Achsabstände sind auf 10⁻⁶ mm genau, und jeder Überdeckungsgrad ist ≥ 1.2.
  - Es gibt **0 Durchdringungen** in Tausenden von 3D-Stichproben (BVH): jeder Zahneingriff über eine volle Zahnteilung, jeder Zyklus der Stift-Schlitz-Mechanismen und 168 Teilepaare in 240 Kurbelstellungen.
- **Der Mond wird mit runden Zahnrädern schneller und langsamer**, nicht mit ovalen. Ein Stift-Schlitz-Mechanismus auf der rotierenden Drehscheibe e3 bildet die Mondanomalie des Hipparchos nach (±6.58°).
- **Die Planeten laufen zur richtigen Zeit rückwärts.** Mars, Jupiter und Saturn werden in der Opposition rückläufig (180° ± 0.03°), und Merkur und Venus bleiben innerhalb ihrer größten Elongationen.
- **Eine Kurbel treibt alles an.** Jede Bewegung geht von `AM_Controller["crank"]` (in Jahren) aus und wird über Treiber mit einfachen Ausdrücken (Simple Expressions) weitergegeben, sodass die Datei animiert wird, ohne dass Python-Skripte aktiviert werden müssen.
- **Gut lesbare Anzeige.** Jeder der sieben antiken „Planeten“ hat eine eigene Farbe und eine Beschriftung, die ihm folgt (Sonne, Mond, Merkur, Venus, Mars, Jupiter, Saturn), dazu kommt eine Legende.
- **Museumsbeleuchtung.** Die Szene hat eine dunkle Hohlkehle (Cyclorama) als Hintergrund und warme Softboxen und wird mit der AgX-Farbtransformation gerendert. Dieses Setup wurde aus drei nebeneinander gerenderten Entwürfen ausgewählt.
- **Explosionsansicht.** Stellt man `AM_Controller["explode"]` von 0 auf 1, gleitet jedes Teil entlang der Stapelachse auseinander.
- **3D-Druck.** Eine STL-Datei pro Teil plus eine vollständige 3MF-Datei, in drei Profilen: Harz ×1, Harz ×1.5 und FDM ×2.

| Vorderes Zifferblatt | Hintere Zifferblätter |
|---|---|
| ![Vorderes Zifferblatt mit farbigen, beschrifteten Planeten](docs/images/front.jpg) | ![Meton- und Saros-Spiralen](docs/images/back.jpg) |

| Explosionsansicht | Innenansicht, geöffnet |
|---|---|
| ![Standbild der Explosionsansicht](docs/images/exploded.jpg) | ![Einzelbild aus dem Explosionsvideo](docs/images/exploded_video_frame.jpg) |

## Videos

- [`antikythera.mp4`](build/out/renders/antikythera.mp4): 20 s. Die Kurbel dreht 4 Jahre weiter, und Planeten, Mond und hintere Zifferblätter bewegen sich alle mit.
- [`antikythera_eclate.mp4`](build/out/renders/antikythera_eclate.mp4): 15 s Explosionsansicht. Der Mechanismus öffnet sich Schicht für Schicht, während sich die Zahnräder weiterdrehen, und schließt sich dann wieder.

Dass sich Planeten in den Videos zeitweise **rückwärts** bewegen, ist kein Fehler. Es handelt sich um die von der Erde aus beobachtete **rückläufige Bewegung** (Retrogradation), und der Mechanismus wurde gebaut, um sie darzustellen. Der Drachenzeiger (die Mondknoten) dreht sich stets rückwärts.

## Schnellstart

1. Installieren Sie **Blender 5.2** oder neuer.
2. Öffnen Sie [`build/out/am.blend`](build/out/am.blend) und drücken Sie die **Leertaste**, um die Animation abzuspielen.
3. Wählen Sie `AM_Controller` aus und ändern Sie seine benutzerdefinierten Eigenschaften (Custom Properties):
   - `crank`: Jahre; 1 entspricht einer Umdrehung von b1;
   - `explode`: 0 bis 1;
   - `patina`: 0 ist neue Bronze, 1 ist Museumspatina.
4. Blenden Sie im Outliner Collections aus:
   - `AM_CASE` und `AM_DIALS`, um das Räderwerk zu sehen;
   - `AM_HYPOTHETICAL`, um nur das Belegte zu behalten;
   - `AM_LABELS`, um die Beschriftungen zu entfernen;
   - `AM_STAGE`, um das Beleuchtungs-Set zu entfernen.
5. Klicken Sie auf ein beliebiges Teil, um seine benutzerdefinierten Eigenschaften zu lesen: `status`, `role`, `teeth`, `module` und `sources`.

### Verifikation erneut ausführen

Verwenden Sie das mit Blender mitgelieferte Python. Die folgenden Pfade gelten für macOS; passen Sie sie auf anderen Systemen entsprechend an.

```sh
PY=/Applications/Blender.app/Contents/Resources/5.2/python/bin/python3.13
BL=/Applications/Blender.app/Contents/MacOS/Blender

$PY tools/validate_spec.py          # exact linear solve (1 DOF, 22 targets), centre distances, collision screening
$PY tools/check_kinematics.py       # pin-and-slot laws, followers, elongations, retrogrades, solar apogee
cd build && $PY -m unittest discover -s tests && $PY -m am.verify --stage all && cd ..
$BL -b build/out/am.blend --python-exit-code 1 -P tools/crosscheck_blend.py   # Blender rotations vs an independent solver
```

[`build/README.md`](build/README.md) führt jeden Build-, Prüf-, Export- und Render-Schritt auf, mit einem Befehl pro Schritt.

### Formale Beweise prüfen (Lean 4)

Installieren Sie einmalig [elan](https://lean-lang.org/install) und führen Sie dann Folgendes aus:

```sh
cd lean
lake exe cache get    # download the compiled Mathlib (about 5 GB)
lake build            # check every proof; warnings are errors, so success means no sorry
cd ..
python3 tools/lean_mutation_test.py   # Lean must reject 9 deliberately wrong mechanisms
```

[`lean/README.md`](lean/README.md) führt Modul für Modul auf, was bewiesen ist und was nicht.

### Alles aus dem Master-Prompt neu bauen

In einem **leeren** Ordner, mit [Claude Code](https://claude.com/claude-code):

```sh
claude -p --model 'claude-opus-5-5[1m]' --effort xhigh --permission-mode acceptEdits \
  --allowedTools Bash Read Write Edit Glob Grep < PROMPT_OPUS.md
```

- [`prompts/PROMPT_OPUS_v1_validated.md`](prompts/PROMPT_OPUS_v1_validated.md) ist genau die Version, die diesen Build in einem Durchlauf erzeugt hat (89 min).
- [`PROMPT_OPUS.md`](PROMPT_OPUS.md) ist v1.2. Diese Version ergänzt die Planetenfarben und -beschriftungen, die Museumsinszenierung, den Explosions-Schieberegler und das Explosionsvideo. All dies wurde diesem Build nachträglich mit den Skripten in `tools/` hinzugefügt, und v1.2 wurde noch nicht von Grund auf neu durchlaufen.

## Entstehung

1. **Recherche.** Parallel arbeitende Agenten werteten die Primärquellen aus: Freeth et al. 2006, 2008 und 2021 (einschließlich der Supplementary Information), Price 1974, Budiselic et al. 2020, Woan & Bayley 2024, Anastasiou et al. 2014 und weitere. Die Ergebnisse wurden zu einem einheitlichen Datensatz abgeglichen und anschließend von einem skeptischen Agenten geprüft.
2. **Spezifikation.** [`spec/antikythera.json`](spec/antikythera.json) ist die einzige maßgebliche Datenquelle (Single Source of Truth). Sie enthält Zähnezahl, Modul, Achsposition, z-Bereich und Bohrung jedes Zahnrads sowie jede Welle, jeden Zapfen, jede Nabe, jeden Stift, jedes Zifferblatt und jedes Material. Erzeugt wird sie von `tools/make_spec.py`, das 22 geometrische Unmöglichkeiten in den veröffentlichten Daten behebt (zum Beispiel kann b2 bei den veröffentlichten Abständen nicht zugleich mit c1 und l1 kämmen). Jeder Achsabstand wird exakt berechnet.
3. **Unabhängige Prüfungen.** `tools/validate_spec.py` und `tools/check_kinematics.py` teilen keinen Code mit dem Generator, und Mutationstests bestätigen, dass sie absichtlich eingeschleuste Fehler erkennen.
4. **Kronradzähne über die Hüllkurve.** `tools/crown_envelope.py` berechnet die Zähne der Kronräder a1 und q1 als den Bereich, den die Gegenzähne nie überstreichen. `tools/test_crowns_blender.py` prüft sie anschließend mit BVH in Blender.
5. **Kritische Gegenprüfungen.** Zwei Runden unabhängiger Prüfer nahmen sich die Daten, die live getestete Blender-API, die Ausführbarkeit und die Geometrie vor und fanden 5 blockierende Fehler und etwa 60 weitere Probleme. Alle wurden behoben.
6. **Build in einem Durchlauf** durch eine neue Opus-5.5-Sitzung allein anhand des Prompts: 131 Dialogrunden, rund 5000 Codezeilen, und alle Abnahmekriterien erfüllt.
7. **Unabhängige Verifikation** des Ergebnisses: Tests, exakte Prüfungen, die vollständige BVH-Kollisionsprüfung und ein Abgleich jedes Körpers in `am.blend` mit dem unabhängigen Löser (7·10⁻⁷ rad).
8. **Formale Beweise.** `tools/make_lean.py` übersetzt die Spezifikation in Lean 4. Die Kinematik, die Zielwerte und die Achsabstände werden auf dieser Grundlage bewiesen. Handgeschriebene Module ergänzen die Analyse der Stift-Schlitz-Mechanismen und die Astronomie, und kritische Prüfer sowie Mutationstests stellten sicher, dass jede Aussage tatsächlich das besagt, was sie behauptet.

## Aufbau des Repositorys

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

## Grenzen und Vorbehalte

- Die Planetengetriebe, die Mondknoten und die wahre Sonne folgen dem **hypothetischen** Modell von Freeth et al. 2021. Eine funktionierende Animation beweist nicht, wie das Original gebaut war.
- Einige Größen sind nicht veröffentlicht. Für sie verwendet die Spezifikation dokumentierte Standardwerte, die in `spec/antikythera.json` → `unresolved_defaults` aufgeführt sind:
  - Achswinkel auf der hinteren Platte;
  - Radien der Kosmos-Ringe;
  - Startphasen (die Epoche ist nicht kalibriert).
- Die Lean-Beweise decken die Kinematik der mittleren Raten, die Zielwerte, die Achsabstände sowie die Gesetze der Stift-Schlitz-Mechanismen und der Folgehebel ab. Überdeckungsgrad, Überlappung der Zahnbreiten, Unterschnitt und Kollisionen werden von den Python-Werkzeugen und in Blender geprüft, nicht in Lean.
- Die Zähne sind konjugierte Evolventen (Bezugsprofil einer 30°-Zahnstange, was dem antiken gleichseitigen Dreieckszahn entspricht), nicht die von Hand gefeilten Dreiecke des Originals.
- Die Planetenfarben dienen nur der Lesbarkeit; sie sind nicht historisch.

## Wichtigste Quellen

- T. Freeth et al., "A Model of the Cosmos in the ancient Greek Antikythera Mechanism", *Scientific Reports* 11, 5821 (2021), mit den zugehörigen Supplementary Information.
- T. Freeth et al., "Decoding the ancient Greek astronomical calculator known as the Antikythera Mechanism", *Nature* 444, 587 (2006).
- T. Freeth, A. Jones, J. Steele, Y. Bitsakis, "Calendars with Olympiad display and eclipse prediction on the Antikythera Mechanism", *Nature* 454, 614 (2008).
- T. Freeth & A. Jones, "The Cosmos in the Antikythera Mechanism", ISAW Papers 4 (2012).
- D. de Solla Price, *Gears from the Greeks* (1974).
- C. Budiselic et al. (2020); G. Woan & J. Bayley (2024): Anzahl der Löcher im Kalenderring.
- M. Anastasiou et al. (2014): die Spiralen der hinteren Zifferblätter.

Die vollständige Liste mit URLs steht in `spec/antikythera.json` → `sources`.

## Lizenz

- **Code**: MIT ([`LICENSE`](LICENSE)).
- **Renderings, Videos, 3D-Modell, Druckdateien und Texte**: CC BY 4.0 ([`LICENSE-MEDIA.md`](LICENSE-MEDIA.md)).
- **Wissenschaftliche Daten**: Bitte zitieren Sie die oben genannten Arbeiten.

---

Erstellt mit [Claude Code](https://claude.com/claude-code) (Claude Opus 5 / 5.5) für taciclei.
