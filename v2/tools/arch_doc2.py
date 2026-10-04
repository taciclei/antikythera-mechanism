"""Seconde moitié de study/architecture.md (version 2)."""
import json
import os

import arch_layout as L
import arch_routes as R
from arch_doc import UAK_FR, V2, f0, f1, stages_txt, table, xy


def _deg(x, nd=2):
    return f"{x:.{nd}f}°".replace(".", ",").replace("-", "−")


def part2(out, S):
    c, w, m, j, b = out["verifications"], out["roues"], out["masse"], out["jeu"], out["budget_erreur"]
    with open(os.path.join(V2, "spec", "trains.json")) as f:
        ev = json.load(f)["evaluation"]
    pl = out["trains_places"]
    P = ["\n## 4. L'intérieur : cinq étages\n"]
    rows = []
    for fid, f in out["etages"].items():
        z0, z1 = f["z"]
        subs = ", ".join(f"{k} {f0(a)}–{f0(bb)}" for k, (a, bb) in f["sub"].items())
        blocs = [k for k, v in L.BLOCKS.items() if v["floor"] == fid and not k.startswith(("uak_", "mod_"))]
        trains = [t for t, v in pl.items() if v["floor"] == fid]
        rows.append([f"**{fid}**", f["nom"], f"{f0(z0)}–{f0(z1)}", subs,
                     ", ".join((["7 tours"] if fid in ("E3", "E2") else []) + blocs + trains)])
    P.append(table(["Étage", "Rôle", "z (mm)", "Sous-étages (z)", "Contenu"], rows))
    P.append("""
**Règles de construction :**
- **Platines.** Des platines de 2 mm séparent les étages.
- **Arbres.** Un arbre de train va de la platine (en E5, d'un pont bas) jusqu'à un **pont** de 3 mm. Il traverse donc
  tous les plans de son étage.
- **Plans.** Chaque couple occupe un plan de 3 mm.
- **Tringles.** Leurs couches font 15 mm. Deux tringles d'une même couche ne se croisent jamais.
""")
    P.append("**Budget en hauteur des blocs** (plans de 3 mm, revue N5) :\n")
    P.append(table(["Bloc", "Plans", "Besoin (mm)", "Hauteur (mm)", "Contenu estimé"],
                   [[x["bloc"], x["plans"], f0(x["besoin_mm"]), f0(x["hauteur_mm"]), x["detail"]]
                    for x in c["budgets_blocs"]]))
    P.append("")
    P.append("**Blocs-mécanismes** (enveloppes estimées ; leur intérieur sera dessiné en 3D) :\n")
    P.append(table(["Bloc", "Étage", "Centre", "Rayon (mm)", "Rôle"],
                   [[k, v["floor"], xy(v["c"]), f1(v["r"]) if v["r"] else "R + 5", v["role"]]
                    for k, v in L.BLOCKS.items() if not k.startswith(("uak_", "mod_"))]))
    P.append("\n## 5. Les tours et les trains, roue par roue\n")
    rows = []
    for p in L.TOWER_ORDER:
        t, q = out["tours"][p], pl.get(f"{p}_L", {})
        rep = q.get("reprise")
        rep_txt = (f"couple 1:1 à {f0(rep[1])} mm" if rep and rep[0] == "direct" else
                   f"24 → fou {rep[1]} (tenon) → 24" if rep else "—")
        rows.append([L.NAME_FR[p], xy(t["axe"]), f0(t["module_R_mm"]), UAK_FR[t["uak"]],
                     stages_txt(q.get("ordre_couples", [])), q.get("sub", "—"), rep_txt, t["moyeu"]])
    P.append(table(["Planète", "Axe (mm)", "Module R", "Unité de Kepler", "Couples (ordre retenu)", "Sous-étage",
                    "Reprise de Y", "Moyeu"], rows))
    P.append("""
**La recherche.** Pour chaque train, le script essaie toutes les combinaisons suivantes :
- les ordres des couples (le produit ne change pas) ;
- les places du pignon fou ;
- les reprises de Y par pignon fou sur tenon, de 16 à 112 dents (le sens est gardé) ;
- les sous-étages ;
- les angles, de 10° en 10°, avec un élagage dès qu'un arbre viole une règle.

**Les règles :**
- une roue ne touche aucun arbre, sauf le sien et celui de la roue qu'elle mène ;
- deux roues d'un même plan ne se touchent que si elles engrènent ;
- un petit pignon est taillé dans son arbre : sa partenaire peut donc en approcher l'arbre jusqu'au fond de dent.
""")
    rows = [[f"`{k}`", f"{v['floor']} / {v['sub']}", v.get("hub", "—"),
             " → ".join(xy(a) for a in v["arbors"])] for k, v in pl.items()]
    P.append(table(["Train", "Étage / sous-étage", "Moyeu", "Arbres (entrée → sortie)"], rows))
    P.append("\n## 6. Renvois et interfaces\n")
    rows = []
    for r in R.ROUTES:
        segs = []
        for s in r["segs"]:
            if s[0] == "z":
                segs.append(f"arbre à {xy(s[1])}, {s[2][0]} {s[2][1]} → {s[3][0]} {s[3][1]}")
            else:
                pq = [p if isinstance(p, str) else xy(p) for p in (s[1], s[2])]
                segs.append(f"tringle {pq[0]} → {pq[1]} ({s[3][0]} {s[3][1]})")
        rows.append([f"`{r['id']}`", r["role"], " ; ".join(segs)])
    P.append(table(["Renvoi", "Rôle", "Parcours"], rows))
    car = out.get("carrousel_deg") or {}
    P.append("\n**Carrousel** (angle de chaque arbre intermédiaire) : " +
             ", ".join(f"{L.NAME_FR.get(k, 'Dragon' if k == 'node' else k)} {f0(v)}°" for k, v in car.items()) + ".\n")
    P.append("**Interfaces déclarées** (une pièce qui entre volontairement dans l'enveloppe d'un bloc) :\n")
    P.append(table(["Pièce", "Bloc", "Entre de (mm)"],
                   [[f"`{x['piece']}`", x["bloc"], f1(x["entre_de_mm"])] for x in c["interfaces"]]))
    P.append("""
Ce sont :
- la croix de Malte, entre l'arbre-jour et le calendrier ;
- les arbres d'arrivée des trains de la Lune et leurs couples d'entrée (40 → pignon fou → 40), qui ramènent L, ϖ et Ω
  sur l'axe M du bloc ;
- l'arrivée de Y au bloc Lune.

L'intérieur des blocs devra les accueillir.

**Contrôle strict (revue N9).** Le recontrôle compte comme liées les seules pièces citées par leur identifiant exact.
Il trouve 37 recouvrements de plus, tous voulus : une pièce montée sur son propre axe de tour (UAK, tube Y, roue de
prise, couronne du bus, roue finale) ou le pignon de 10 taillé dans l'arbre de Neptune. Aucun recouvrement réel caché.
""")
    P.append("\n## 7. Les roues\n")
    P.append(table(["Poste", "Roues"], [[a, n] for a, n in w["rows"]] + [["**Total**", f"**{w['total']}**"]]))
    P.append("""
**Règles de compte :**
- une tringle 1:1 a deux couples coniques, soit 4 roues ;
- une tringle de moyeu a 3 roues : un pignon au départ, un pignon et une couronne à l'arrivée ;
- chaque tube de la pile ajoute un couple 64:64 ;
- une tringle vers le couvercle compte sa prise, son renvoi d'angle en haut et son couple vers le tube de l'orrery,
  moins le couple conique déjà compté dans `trains.json`.
""")
    P.append("## 8. Le sens de rotation\n")
    P.append("""**Les règles d'inversion :**
- un couple extérieur inverse le sens, un couple intérieur le garde ;
- un pignon fou inverse ;
- un renvoi conique (ou une couronne) peut faire l'un ou l'autre : cela dépend de la face où engrène le pignon.

Chaque chaîne de renvoi contient au moins un renvoi conique ou un pignon fou. Le sens de chaque arbre peut donc
toujours être réglé pour retrouver le sens `phys` de `trains.json`. Le contrôle sur pièces réelles se fera en 3D.
""")
    P.append(table(["Renvoi", "Chaîne", "Sens sans réglage", "Réglage"],
                   [[f"`{s['renvoi']}`", s["chaine"], s["sens_fixe"], s["reglage"]] for s in out["sens"]]))
    P.append(f"""
## 9. Le jeu des engrenages

**Le problème.** Avec un jeu de {str(j['jn_mm']).replace('.', ',')} mm par paire de dents, les renvois en aval d'un
suiveur laissent **{_deg(j['aval_suiveur_deg'])}** de flottement à l'aiguille. Ces renvois sont deux couples coniques
m 0,4 et le couple 64:64.

**Quand ce jeu apparaît.** Il apparaît **chaque fois que la sortie change de sens**, même si la manivelle tourne
toujours dans le même sens. C'est le cas :
""")
    P += [f"- {x} ;" for x in j["sorties_non_monotones"]]
    P.append("""
C'est plus que l'erreur géométrique, au moment le plus intéressant : la boucle de rétrogradation.

**Le remède retenu** : {j['remede']}.

Un frein à friction ne convient pas : il retiendrait l'aiguille pendant que le jeu se rattrape. Les embrayages à
friction ne servent qu'à la mise à l'heure initiale.
""".replace("{j['remede']}", j["remede"]))
    P.append(f"""## 10. Bilans

### 10.1 Masse
""")
    P.append(table(["Poste", "Masse (g)"], [[k, f0(v)] for k, v in m["parts_g"].items()]
                   + [["**Total**", f"**{f1(m['total_kg'])} kg**"]]))
    P.append(f"""
Avec des platines intérieures en aluminium, la masse descend à **{f1(m['total_kg_alu_inner'])} kg**. Les options
(`gmst_direct`, `synodic`, `saros_223`, `mars_apsides`) ne sont pas comptées.

### 10.2 Manivelle

**Mode normal.** Un pignon de 24 dents engrène la couronne de 96 de l'arbre-jour : **1 tour de manivelle = 6 heures**.

**Mode rapide.** Une boîte 1:30 sur la paroi donne **1 tour = 7,5 jours**. La manivelle « de la semaine » de
`trains.md` n'est plus possible : une croix de Malte ne se mène pas à l'envers.

**Effort.** L'effort de manivelle se mesurera sur prototype.

### 10.3 Fabrication

- **Modules.**
  - Trains : m 0,5, avec deux couples en m 0,55 et m 0,7.
  - Couronnes intérieures : m 0,8 et m 0,9.
  - Renvois coniques : m 0,4. Les coniques 40:40 de `trains.json` vers l'orrery deviennent un couple de prise et une
    conique m 0,4, au même rapport.
- **Tolérance de position :** 0,02 mm.
- **Le suiveur F des planètes extérieures** pivote à 0,4–3,7 mm de l'axe de la tour, à l'intérieur de son rayon. Il
  tourne donc sur une **bague excentrique de Ø 18 mm** fixée à la platine P2, autour de l'axe.
  - Sa roue de prise (46 dents, r 12) est enfilée sur la bague.
  - Elle engrène, à 23 mm, l'arbre décalé qui porte la conique.
  - Mercure, Jupiter et Saturne prennent du côté −x, les autres du côté +x.
  - Le modèle centre cette roue sur l'axe ; en réalité, elle tourne autour de F, jusqu'à 3,7 mm plus loin. Les jeux
    restent d'au moins 3,8 mm.
- **Différentiels** : à engrenages droits (satellites par paires), même relation que les différentiels coniques de
  `trains.json`, mais 3 plans de haut.
- **Les excentriques les plus fins :**
  - l'épicyclet de Mars (0,087 mm) ;
  - le bras Soleil de Neptune (1,6 mm).

  Ils se font par bague excentrique réglable ou par électroérosion.

## 11. Budget d'erreur attendu (2000–2100)
""")
    rows = []
    for r in b["planetes"]:
        key = [p for p in L.TOWER_ORDER if L.NAME_FR[p] == r["sortie"]][0]
        rows.append([r["sortie"], _deg(r["geometrie_deg"]), r["physique_hors_kepler"].replace(".", ","),
                     _deg(r["tolerance_0_02mm_deg"]), _deg(ev[f"{key}_L"]["deg_per_century"], 4)])
    P.append(table(["Aiguille", "Géométrie", "Physique hors Kepler", "Tolérance 0,02 mm", "Rapport (°/siècle)"], rows))
    lu, ec = b["lune_deg"], b["eclipses"]
    P.append(f"""
- **Copies de l'UAK Terre** (tours, bloc Lune, bloc du temps) : une tolérance de 0,02 mm donne environ
  {_deg(b['copies_uak_terre_deg'])} d'écart entre le Soleil de l'aiguille et celui de chaque copie. Cet écart s'ajoute
  aux colonnes ci-dessus. Pour l'équation du temps, il fait au plus {b['copies_uak_terre_edt_s']} s d'écart avec
  l'aiguille du Soleil.
- **Lune** : {_deg(lu['max'])} au maximum, {_deg(lu['rms'])} rms.
- **Calendrier** : {b['calendrier']}.
- **Temps sidéral** : {str(b['sideral_s_par_siecle']).replace('.', ',').replace('-', '−')} s par siècle.
- **Équation du temps** : {str(b['equation_du_temps_s']).replace('.', ',')} s au plus pour le modèle. Le bloc du temps
  calcule λ avec sa propre copie de l'UAK Terre : sa tolérance ajoute jusqu'à {b['copies_uak_terre_edt_s']} s, soit
  environ 15 s au pire.
- **Éclipses** : {ec['detectees']} sur {ec['total']}, erreur sur γ d'au plus {str(ec['gamma_err_max']).replace('.', ',')}.
- **Jeu** : environ 0 avec les roues à ciseaux ; sinon {_deg(j['aval_suiveur_deg'])} à chaque changement de sens.

## 12. Ce que cette architecture ne prouve pas encore

- **Les blocs restent des enveloppes estimées**, pas des pièces : cascade lunaire, calendrier, temps, Laplace, UAK,
  modules. Leur intérieur, y compris les interfaces du § 6, sera dessiné et vérifié en 3D.
- **Le socle de l'orrery** n'est vérifié que pour l'espacement des tringles qui y arrivent.
- **La dynamique n'est pas calculée :** efforts, frottements, flexion.
- **Le modèle est fait de disques.** Une roue est un disque plein (tête de dent) ; une conique couchée est un disque
  dans sa couche. Les profils de dents et l'interférence fine viendront avec la 3D (BVH, comme la v1).

## 13. Suite

1. Construction 3D dans Blender à partir de `spec/architecture.json`, avec contrôle d'interférence pièce par pièce.
2. Preuves Lean 4 des rapports de `trains.json` et des identités exactes : Laplace, Hooke, calendrier.
""")
    return P
