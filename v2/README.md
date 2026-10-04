# Anticythère 2.0 : la machine refaite avec la science de 2026

> ⚠️ **Ce n'est pas une reconstruction historique.** Ce dossier contient une **évolution moderne** de la machine
> d'Anticythère. Elle garde l'esprit antique : une boîte de bronze, une manivelle, des cadrans. Mais tout ce qu'elle
> calcule repose sur l'astronomie d'aujourd'hui.
>
> La reconstruction historique (la « v1 ») est à la racine du dépôt, figée par le repère
> [`v1-historique`](https://github.com/taciclei/antikythera-mechanism/releases/tag/v1-historique).

**État : étude de conception terminée.** [Lire l'étude](https://taciclei.github.io/antikythera-mechanism/v2/) (page
illustrée), ou le dossier [`study/`](study/). L'architecture (version 4) est vérifiée pièce par pièce, sans collision, et
a été relue par trois revues adversariales. **La maquette 3D** (Blender, 415 pièces, contrôle d'interférence sans
recouvrement) et **201 preuves Lean 4** sont faites : voir [`blender/README.md`](blender/README.md). Prochaine étape :
dessiner l'intérieur des blocs pièce par pièce.

## Ce qui change par rapport à l'original

| | Machine antique (v1) | Anticythère 2.0 |
|---|---|---|
| Planètes | 5 (Mercure à Saturne), sur des cercles (Hipparque) | **8** : Uranus et Neptune en plus, orbites **képlériennes** |
| Lune | anomalie d'Hipparque (±6,6°) | anomalie, **évection** et **variation** : 0,26° d'erreur au plus |
| Rapports d'engrenages | relations babyloniennes | **périodes modernes** : moins de 0,01° de dérive par siècle |
| Calendrier | égyptien de 365 jours, cycle de Méton | **grégorien** (bissextiles 4/100/400), jour de la semaine |
| Temps | — | **heure sidérale**, **équation du temps**, **précession** des équinoxes |
| Éclipses | spirale du Saros, signes Σ / Η | Saros, plus distance au nœud : **magnitude** et indication de l'hémisphère |
| Affichage | ciel vu depuis la Terre | ciel vu depuis la Terre (face avant) **et** système solaire vu d'en haut (planétaire sur le dessus) |
| En plus | — | les **lunes galiléennes** de Jupiter (résonance 1:2:4) |

## Organisation

```
v2/
  research/   constantes modernes, mécanismes, précédents historiques (horloges de Strasbourg, de Jens Olsen…)
  spec/       trains d'engrenages (trains.json) et architecture vérifiée (architecture.json)
  tools/      scripts qui calculent, placent, vérifient et dessinent tout
  study/      trains.md, architecture.md, les revues, la page etude.html, ses figures et ses rendus
  blender/    la maquette 3D (construction, contrôles, rendus) et son contrat
  lean/       les preuves Lean 4 de la v2
```

Les principes de la v1 restent valables :
- une source de vérité unique ;
- des rapports vérifiés en fractions exactes, puis prouvés en Lean 4 ;
- des limites dites clairement.

---

# Anticythère 2.0 (English)

> ⚠️ **Not a historical reconstruction.** This folder is a **modern evolution** of the Antikythera Mechanism. It keeps
> the ancient spirit (a bronze box, a crank, dials) but computes with 2026 astronomy:
> - 8 planets on Kepler orbits;
> - a modern Moon with evection and variation;
> - the Gregorian calendar, sidereal time, the equation of time and precession;
> - eclipse magnitude;
> - Jupiter's Galilean moons;
> - a geocentric front dial plus a heliocentric orrery on top.
>
> The historical reconstruction (v1) is the rest of this repository, frozen at the
> [`v1-historique`](https://github.com/taciclei/antikythera-mechanism/releases/tag/v1-historique) tag.

**Status:** the design study is complete. [Read it](https://taciclei.github.io/antikythera-mechanism/v2/) (illustrated
page, in French) or browse [`study/`](study/). The architecture (version 4) is checked part by part with no collision
and was reviewed by three adversarial reviews. **The 3D model** (Blender, 415 parts, interference check with no
overlap) and **201 Lean 4 proofs** are done: see [`blender/README.md`](blender/README.md). Next: design the inside of
the blocks part by part.
