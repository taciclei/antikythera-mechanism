"""Anticythère 2.0 — renvois (arbres en z, tringles, liaisons directes). Version 2.

Segments :
  ("z", (x, y), (étage, sous-étage) de départ, (étage, sous-étage) d'arrivée)  arbre de renvoi
  ("rod", (x, y) | "hub" | "carrousel", (x, y) | "carrousel", (étage, couche))  tringle, coniques 1:1 m 0,4 aux bouts
« chaine » : la suite des engrènements, pour le tableau des sens de rotation :
  "ext" (roues droites extérieures : inverse), "int" (intérieure : garde), "fou" (pignon fou : inverse),
  "con" (renvoi conique ou couronne : le sens se choisit par la face d'engrènement).
« roues » : roues ajoutées par ce renvoi (en plus de trains.json) ; « interne » : roues dans un bloc, non dessinées.
"""
from arch_layout import CENTRE, CRANK_IN, J_DAY, M_MOON, NAME_FR, PLATE, TOWER_ORDER, TOWERS, de

TOP = PLATE["y"][1] - 2

ROUTES = []
for _p in TOWER_ORDER:
    _x, _y = TOWERS[_p]
    ROUTES.append({"id": f"geo_{_p}", "shaft": f"{_p}_geo", "kind": "geo",
                   "role": f"longitude géocentrique {de(NAME_FR[_p])} vers la pile avant",
                   "links": [f"mod_{_p}", f"axe_{_p}"], "car": _p,
                   "chaine": ["con", "con", "ext"], "roues": 6,
                   "segs": [("z", (_x, _y), ("E2", "mod"), ("E1", "T1")), ("rod", (_x, _y), "carrousel", ("E1", "T1"))]})
    ROUTES.append({"id": f"orr_{_p}", "shaft": f"orrery_{_p}", "kind": "orr", "tower": _p,
                   "role": f"longitude héliocentrique {de(NAME_FR[_p])} vers l'orrery (suiveur F)",
                   "links": [f"uak_{_p}", f"axe_{_p}"], "exit": "q",
                   "chaine": ["ext", "con", "con", "ext"], "roues": 2 + 4,
                   "segs": [("rod", "prise", "haut", ("E3", "T1"))]})
ROUTES += [
    {"id": "orr_earth", "shaft": "orrery_earth", "kind": "orr", "tower": "earth",
     "role": "Soleil vrai (Terre) vers l'orrery", "links": ["terre_maitre", "axe_soleil"], "exit": "q",
     "chaine": ["ext", "con", "con", "ext"], "roues": 2 + 4, "segs": [("rod", "prise", "haut", ("E3", "T1"))]},
    {"id": "moon_true", "shaft": "moon_true", "kind": "geo", "car": "moon",
     "role": "Lune vraie vers la pile avant", "links": ["lune"], "interne": 2,
     "chaine": ["ext", "con", "con", "ext"], "roues": 6,
     "segs": [("z", (132.0, 15.0), ("E5", "meca"), ("E1", "T1")), ("rod", (132.0, 15.0), "carrousel", ("E1", "T1"))]},
    {"id": "node", "shaft": "moon_node", "kind": "geo", "car": "node",
     "role": "nœud ascendant (aiguille du Dragon) vers la pile avant", "links": ["lune"], "interne": 2,
     "chaine": ["ext", "con", "con", "ext"], "roues": 6,
     "segs": [("z", (150.0, -5.0), ("E5", "meca"), ("E1", "T1")), ("rod", (150.0, -5.0), "carrousel", ("E1", "T1"))]},
    {"id": "gamma", "shaft": None, "kind": "orr",
     "role": "course de la coulisse d'éclipse (γ) vers l'aiguille d'ombre du globe", "links": ["lune"], "exit": "q",
     "interne": 2, "chaine": ["crémaillère", "con", "con"], "roues": 4 + 2,
     "segs": [("z", (118.0, 40.0), ("E5", "meca"), ("E3", "T1")), ("rod", (118.0, 40.0), (118.0, TOP), ("E3", "T1"))]},
    {"id": "orr_moon", "shaft": "moon_true", "kind": "orr",
     "role": "Lune vraie vers le bras de la Lune du tellurion", "links": ["lune"], "exit": "q", "interne": 2,
     "chaine": ["ext", "con", "con", "ext"], "roues": 4 + 2,
     "segs": [("z", (100.0, 30.0), ("E5", "meca"), ("E3", "T1")), ("rod", (100.0, 30.0), (100.0, TOP), ("E3", "T1"))]},
    {"id": "lune_Y", "shaft": "Y", "kind": "in", "role": "année Y vers le bloc de la Lune (évection, équation annuelle)",
     "links": ["lune", "Y5"], "hub": "Y5", "interne": 2, "chaine": ["con", "con", "ext"], "roues": 3, "interface": "lune",
     "segs": [("rod", "hub", (100.0, 62.0), ("E5", "T1")), ("z", (100.0, 62.0), ("E5", "T1"), ("E5", "meca"))]},
    {"id": "j_avant", "shaft": "J", "kind": "in", "role": "arbre-jour vers la boîte de Laplace",
     "links": ["J5", "laplace"], "hub": "J5", "chaine": ["con", "con"], "roues": 3,
     "segs": [("rod", "hub", (-95.0, -45.0), ("E5", "T2")), ("z", (-95.0, -45.0), ("E5", "T2"), ("E1", "pile"))]},
    {"id": "vers_horloge", "shaft": "gmst", "kind": "out", "role": "temps moyen (J) et temps sidéral, coaxiaux, vers l'horloge 24 h",
     "links": ["temps", "horloge"], "coaxial": 2, "chaine": ["con", "con"], "roues": 8,
     "segs": [("z", (-21.0, -58.0), ("E5", "meca"), ("E1", "T2")), ("rod", (-21.0, -58.0), (-188.0, 118.0), ("E1", "T2"))]},
    {"id": "vers_edt", "shaft": "eot_dial", "kind": "out", "role": "équation du temps (×10) vers son cadran",
     "links": ["temps", "edt"], "chaine": ["con", "con"], "roues": 4,
     "segs": [("z", (15.0, -58.0), ("E5", "meca"), ("E1", "T2")), ("rod", (15.0, -58.0), (188.0, -118.0), ("E1", "T2"))]},
    {"id": "prec_avant", "shaft": "precession_ring", "kind": "out",
     "role": "arbre de la roue de 131 (précession × 179/15) : il monte droit jusqu'au pignon de l'anneau tropique",
     "links": ["temps", "prec_pignon", "prec_bas#m0q", "prec_bas#r0"], "chaine": ["int"], "roues": 0,
     "segs": [("z", (0.0, -65.6), ("E5", "meca"), ("E1", "pile"))]},
    {"id": "tellurion", "shaft": "tellurion", "kind": "orr", "role": "temps sidéral vers la rotation du globe de l'orrery",
     "links": ["temps"], "exit": "q", "chaine": ["ext", "con", "con"], "roues": 2 + 4,
     "segs": [("z", (-30.0, -92.0), ("E5", "meca"), ("E3", "T1")), ("rod", (-30.0, -92.0), (-30.0, TOP), ("E3", "T1"))]},
    {"id": "lunette", "shaft": "jupiter_geo", "kind": "out", "role": "longitude géocentrique de Jupiter vers la lunette",
     "links": ["geo_jupiter#z0", "geo_jupiter#r1", "geo_jupiter#m1p", "laplace"], "chaine": ["con", "con"], "roues": 4,
     "segs": [("z", TOWERS["jupiter"], ("E1", "T1"), ("E1", "T2")), ("rod", TOWERS["jupiter"], (-188.0, -118.0), ("E1", "T2"))]},
    {"id": "manivelle", "shaft": "J", "kind": "in", "role": "manivelle (paroi gauche) vers l'arbre-jour", "links": ["J5"],
     "hub": "J5", "exit": "p", "chaine": ["con"], "roues": 1, "segs": [("rod", CRANK_IN, "hub", ("E5", "T2"))]},
]

# Entrées du bloc du temps : tringles de moyeu (J5 en couche T2, Y5 en couche T1), puis arbre vers le bloc.
ROUTES += [
    {"id": "temps_J", "shaft": "J", "kind": "in", "role": "arbre-jour vers le bloc du temps (temps sidéral, horloge)",
     "links": ["temps", "J5"], "hub": "J5", "chaine": ["con", "con"], "roues": 3,
     "segs": [("rod", "hub", (-42.0, -70.0), ("E5", "T2")), ("z", (-42.0, -70.0), ("E5", "T2"), ("E5", "meca"))]},
    {"id": "temps_Y", "shaft": "Y", "kind": "in", "role": "année Y vers le bloc du temps (Soleil moyen, précession)",
     "links": ["temps", "Y5"], "hub": "Y5", "chaine": ["con", "con"], "roues": 3,
     "segs": [("rod", "hub", (30.0, -88.0), ("E5", "T1")), ("z", (30.0, -88.0), ("E5", "T1"), ("E5", "meca"))]},
]
DIRECT_LINKS = []

# Roues internes aux blocs, non dessinées mais comptées (revue I9) : estimation de trains.py hors aiguilles,
# plus les couples d'interface du bloc lune et le couple 15:179 du bloc du temps.
INTERNAL_WHEELS = [
    ("modules vectoriels : 7 × (bras planète 2 + bras Terre 2 + chaîne 1:1 3)", 49),
    ("cascade lunaire : 6 couples relatifs", 12),
    ("couronne de phase de la Lune (48:48)", 2),
    ("cadran jovien : 4 couples", 8),
    ("demi-roues anti-jeu (ciseaux) des 9 couples 64:64 du carrousel", 9),
    ("bloc du temps : couple 15:179 de la précession + pignon fou", 3),
    ("bloc du temps : copie de l'UAK Terre (couple d'entrée)", 2),
    ("prises du suiveur F vers l'orrery : comptées avec chaque renvoi", 0),
]
