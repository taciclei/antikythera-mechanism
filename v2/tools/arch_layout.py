"""Anticythère 2.0 — données d'architecture (positions, étages, blocs, trains). Version 2.

Repère (le même que la v1, Freeth) : x vers la droite vu de face, y vers le haut,
z vers l'observateur de la face avant. Origine : centre de la face arrière, z = 0 sur
la face extérieure de la platine-cadran arrière. Unités : mm.

Ce fichier ne contient que des choix de conception. Les tailles des engrenages viennent de
spec/trains.json, celles des modules de research/calc/modules_results.json. Les renvois sont dans
arch_routes.py, les faces dans arch_faces.py. architecture.py place les trains roue par roue et vérifie.
Version 2 : corrections de la revue adversariale (study/review.md).
"""

PLATE = {"x": (-225.0, 225.0), "y": (-170.0, 170.0), "margin": 2.0}
WALL = 6.0           # paroi de la caisse (bois, comme l'original)
PLATE_T = 2.0        # épaisseur des platines intérieures
DIAL_T = 3.0         # épaisseur des platines-cadrans
PLANE_T = 3.0        # un plan d'engrènement : roue de 2 mm + 1 mm de jeu

# Étages de l'arrière vers l'avant. « ponts » : les arbres des trains vont de la platine (ou du cadran)
# jusqu'à un pont de 3 mm ; ils traversent donc TOUS les plans de leur étage. Couches de tringles : 15 mm
# (pignon conique m 0,4 de 24 dents, Ø 10,4 mm, au-dessus de la couronne du moyeu).
FLOOR_STACK = [
    ("E5", "étage du temps, du calendrier et de la Lune",
     [("anneau", 6), ("m1", 39), ("m2", 39), ("ponts", 3), ("T1", 15), ("T2", 18)]),
    ("E4", "étage des trains moyens (bus de l'année)",
     [("A", 9), ("B", 9), ("C", 9), ("ponts", 3), ("T1", 15), ("T2", 15)]),
    ("E3", "étage de Kepler (unités d'anomalie)", [("uak", 17), ("T1", 15)]),
    ("E2", "étage des modules géocentriques", [("mod", 28)]),
    ("E1", "étage des renvois avant", [("T1", 15), ("T2", 15), ("pile", 54)]),
]
PLATE_NAMES = ["P4", "P3", "P2", "P1"]  # entre E5|E4, E4|E3, E3|E2, E2|E1


def build_z():
    floors, plates = {}, {"cadran arrière": (0.0, DIAL_T)}
    z = DIAL_T
    for i, (fid, nom, subs) in enumerate(FLOOR_STACK):
        z0, sub_ = z, {}
        for sid, t in subs:
            sub_[sid] = (z, z + t)
            z += t
        floors[fid] = {"z": (z0, z), "nom": nom, "sub": sub_}
        if i < len(PLATE_NAMES):
            plates[PLATE_NAMES[i]] = (z, z + PLATE_T)
            z += PLATE_T
    plates["cadran avant"] = (z, z + DIAL_T)
    return floors, plates, z + DIAL_T


FLOORS, PLATES_Z, Z_FRONT = build_z()
FRONT_POINTERS_Z = (Z_FRONT, Z_FRONT + 20)
FRONT_COVER_Z = (Z_FRONT + 20, Z_FRONT + 27)
BACK_POINTERS_Z = (-20.0, 0.0)
BACK_DOOR_Z = (-26.0, -20.0)
ALIASES = {("E5", "meca"): ("m1", "m2"), ("E4", "AB"): ("A", "B"), ("E4", "BC"): ("B", "C")}


def sub(fid, sid):
    if (fid, sid) in ALIASES:
        a, b = ALIASES[(fid, sid)]
        return (FLOORS[fid]["sub"][a][0], FLOORS[fid]["sub"][b][1])
    return FLOORS[fid]["sub"][sid]


def arbor_span(fid):
    """Un arbre de train va du bas de l'étage (en E5 : d'un pont bas au-dessus de l'anneau des dates)
    jusqu'au haut des ponts."""
    lo = FLOORS[fid]["sub"]["m1"][0] if fid == "E5" else FLOORS[fid]["z"][0]
    return (lo, FLOORS[fid]["sub"]["ponts"][1])


def mid(fid, sid):
    a, b = sub(fid, sid)
    return (a + b) / 2


# Tours planétaires : un axe commun aux étages 4 (train moyen), 3 (UAK planète + copie de l'UAK Terre)
# et 2 (module vectoriel). Sur l'axe : l'arbre de la longitude moyenne L (dedans) et le tube Y (dehors).
TOWERS = {
    "venus": (-147.0, 92.0), "mars": (5.0, 92.0), "mercury": (157.0, 102.0),
    "jupiter": (-168.0, -112.0), "saturn": (-56.0, -112.0), "neptune": (56.0, -112.0),
    "uranus": (168.0, -112.0),
}
TOWER_ORDER = ["mercury", "venus", "mars", "jupiter", "saturn", "uranus", "neptune"]


def de(name):
    """« de Mars », « d'Uranus »."""
    return ("d'" if name[0] in "AEIOUÉ" else "de ") + name


NAME_FR = {"mercury": "Mercure", "venus": "Vénus", "earth": "Terre", "mars": "Mars", "jupiter": "Jupiter",
           "saturn": "Saturne", "uranus": "Uranus", "neptune": "Neptune", "moon": "Lune"}

CENTRE = (0.0, 0.0)
K_CAL = (-112.0, 15.0)       # axe du calendrier (face arrière, à gauche vue de face)
M_MOON = (112.0, 15.0)       # axe de la Lune et des éclipses
J_DAY = (-50.0, -20.0)       # arbre-jour J
TIME_BLOCK = (0.0, -78.0)    # bloc du temps
SAROS_AX = (170.0, -128.0)   # cadran du Saros
CRANK_IN = (-225.0, 25.0)   # entrée de la manivelle (paroi gauche vue de face)

# Pièces (rayons d'encombrement, tête de dent comprise)
UAK_R = 28.0
RK_MERCURY_R = 42.0
MODULE_FRAME = 5.0
AXIS_R = 4.0          # axe de tour : arbre L + tube Y
SHAFT_R = 2.0         # arbre de train
ARBOR_R = 2.0         # arbre de renvoi
ROD_R = 1.5           # tringle
BEVEL_M = 0.4         # module des coniques et couronnes de renvoi
MITRE_R = BEVEL_M * 24 / 2 + 2 * BEVEL_M          # conique de 24 dents : 5,6
HUB_R = BEVEL_M * 96 / 2 + 2 * BEVEL_M            # couronne de 96 dents : 20,0
HUB_PIN_AT = BEVEL_M * 96 / 2 - 2.0               # centre du pignon couché sur la couronne
CAROUSEL_R = 32.0
CAROUSEL_WHEEL_R = 16.5                           # 64 dents m 0,5
CAROUSEL_STEP = 40.0
TRANSFER_CD = [float(c) for c in range(16, 65, 4)]  # couple 1:1 tube Y → entrée du train (m 0,5, z = 2·cd ≤ 128)
# Prise du suiveur F vers l'orrery : la roue de F (46 dents, r 12) tourne sur une bague excentrique de Ø 18 autour de
# l'axe ; sa partenaire est à 23 mm, du côté indiqué (+1 : +x, −1 : −x). La Terre (UAK maîtresse) prend à 12 mm.
TAKEOFF = {"mercury": (23.0, -1), "venus": (23.0, 1), "mars": (23.0, 1), "jupiter": (23.0, -1), "saturn": (23.0, -1),
           "uranus": (23.0, 1), "neptune": (23.0, 1), "earth": (16.0, -1)}
CLEAR = 1.0

BLOCKS = {
    "cal_anneau": {"c": K_CAL, "r": 96.0, "r_in": 84.0, "floor": "E5", "subs": ["anneau"], "contenu": ["cal_sum"],
                   "role": "anneau des dates : 200 dents intérieures (m 0,9), 366 crans à sautoir"},
    "cal_meca": {"c": K_CAL, "r": 46.0, "floor": "E5", "subs": ["m1", "m2"],
                 "contenu": ["cal_cross_main", "cal_cross_skip", "cal_prog4", "cal_prog100", "cal_prog400"],
                 "role": "croix de Malte (principale et de saut), différentiel, roues-programmes 4/100/400, cames"},
    "semaine": {"c": (-64.0, -10.0), "r": 20.0, "floor": "E5", "subs": ["anneau"], "contenu": [],
                "role": "disque des 7 jours, vu par un guichet du cadran du calendrier"},
    "annees": {"c": (-125.0, -40.0), "r": 24.0, "floor": "E5", "subs": ["anneau"], "contenu": [],
               "role": "disque du siècle (00-99) et guichet des 400 ans"},
    "lune": {"c": M_MOON, "r": 50.0, "floor": "E5", "subs": ["m1", "m2"],
             "contenu": ["moon_true", "annual_eq", "evection_carrier"],
             "role": "cascade lunaire à 5 étages sur l'axe M, coulisse d'éclipse sur le porte-nœuds coaxial, copie de "
                     "l'UAK Terre ; 3 couples d'entrée ramènent L, ϖ, Ω sur l'axe, 4 couples de prise en sortent"},
    "croix": {"c": (-65.7, -11.1), "r": 12.0, "floor": "E5", "subs": ["m1", "m2"], "contenu": [],
              "links": ["jour", "cal_meca"], "interface": True,
              "role": "croix de Malte du calendrier, menée par la goupille de J (interface J → calendrier)"},
    "jour": {"c": J_DAY, "r": 17.0, "floor": "E5", "subs": ["m1", "m2"], "contenu": ["J", "W"],
             "role": "arbre-jour J ; sa goupille mène la croix de Malte du calendrier (6 fentes) et une croix "
                     "de semaine à 7 positions (même rapport 1:7 que 10:70)"},
    "temps": {"c": TIME_BLOCK, "r": 46.0, "floor": "E5", "subs": ["m1", "m2"],
              "contenu": ["sun_trop", "stellar", "gmst", "lambda_trop", "alpha_sun", "eot", "eot_dial", "earth_true"],
              "role": "différentiels du temps sidéral, joint de Hooke (ε = 23,44°), équation du temps ×10, "
                      "couple 15:179 (m 0,4) qui ramène l'arbre de précession au rapport de l'anneau, "
                      "copie de l'UAK Terre menée par Y (Soleil vrai λ)"},
    "terre_maitre": {"c": CENTRE, "r": UAK_R, "floor": "E3", "subs": ["uak"], "contenu": ["earth_true", "sun_geo"],
                     "role": "UAK maîtresse de la Terre : Soleil vrai (aiguille, orrery, temps)"},
    "pile": {"c": CENTRE, "r": 9.2, "floor": "E1", "subs": ["pile"], "contenu": [],
             "role": "pile centrale : arbre du Soleil et 9 tubes coaxiaux (Ø 18,4 mm)"},
    "laplace": {"c": None, "r": None, "floor": "E1", "subs": ["pile"],
                "contenu": ["ganymede", "nu", "callisto", "europa", "io"],
                "role": "boîte de Laplace : trains G, ν, C empilés (10 mm chacun), deux doubleurs, deux différentiels"},
    "horloge": {"c": (-188.0, 118.0), "r": 20.0, "floor": "E1", "subs": ["pile"], "contenu": [],
                "role": "renvoi des aiguilles 24 h : temps moyen (J) et temps sidéral"},
    "edt": {"c": (188.0, -118.0), "r": 14.0, "floor": "E1", "subs": ["pile"], "contenu": [],
            "role": "renvoi de l'aiguille de l'équation du temps"},
    "prec_pignon": {"c": (0.0, -65.6), "r": 8.0, "floor": "E1", "subs": ["pile"], "contenu": ["precession_ring"],
                    "role": "pignon de 15 dents (m 0,8) qui mène l'anneau tropique (179 dents intérieures)"},
}
for _p, _c in TOWERS.items():
    BLOCKS[f"uak_{_p}"] = {
        "c": _c, "r": RK_MERCURY_R if _p == "mercury" else UAK_R, "floor": "E3", "subs": ["uak"], "tower": _p,
        "contenu": [f"{_p}_true"] + (["mercury_E", "mercury_counter_arm"] if _p == "mercury" else [])
        + (["mars_epicyclet"] if _p == "mars" else []),
        "role": ("résolveur de Kepler et ellipse à deux bras" if _p == "mercury" else
                 "équant et épicyclet" if _p == "mars" else "équant bissecté") + ", plus la copie de l'UAK Terre"}
    BLOCKS[f"mod_{_p}"] = {"c": _c, "r": None, "floor": "E2", "subs": ["mod"], "tower": _p, "contenu": [f"{_p}_geo"],
                           "role": "module vectoriel à deux bras (suiveur en O vers l'avant, en F vers l'arrière)"}

# Moyeux : couronne de 96 (m 0,4) sur l'arbre source ; chaque tringle part d'un pignon de 24.
HUBS = {"Y4a": {"c": CENTRE, "floor": "E4", "layer": "T1", "src": "Y"},
        "Y4b": {"c": CENTRE, "floor": "E4", "layer": "T2", "src": "Y"},
        "Y5": {"c": CENTRE, "floor": "E5", "layer": "T1", "src": "Y"},
        "J5": {"c": J_DAY, "floor": "E5", "layer": "T2", "src": "J"}}
TOWER_HUB = {"mercury": "Y4a", "venus": "Y4a", "jupiter": "Y4a", "neptune": "Y4a",
             "mars": "Y4b", "saturn": "Y4b", "uranus": "Y4b"}

# Trains placés roue par roue. mode "tower" : sortie sur l'axe, entrée reprise du tube Y de l'axe par un
# couple 1:1 ; mode "rod" : sortie imposée, entrée menée par une tringle depuis un moyeu.
PLACED_TRAINS = (
    [{"shaft": f"{p}_L", "mode": "tower", "floor": "E4", "anchor": TOWERS[p], "hub": TOWER_HUB[p],
      "subs": ["AB"] if p == "mercury" else (["B"] if p == "neptune" else ["A", "B", "C"]), "tower": p}
     for p in TOWER_ORDER]
    + [{"shaft": "saros", "mode": "rod", "floor": "E5", "anchor": SAROS_AX, "hub": "Y5", "subs": ["m1", "m2"],
        "out_back": True},
       {"shaft": "moon_perigee", "mode": "rod", "floor": "E4", "anchor": (80.0, 35.0), "hub": "Y4b",
        "subs": ["A", "B", "C"], "interface": "lune", "out_down": "lune",
        "arc": (M_MOON, 36.0, list(range(0, 360, 15)))},
       {"shaft": "moon_node", "mode": "rod", "floor": "E5", "anchor": (63.7, 2.1), "hub": "Y5",
        "subs": ["m1", "m2"], "interface": "lune", "arc": (M_MOON, 50.0, list(range(0, 360, 10)))},
       {"shaft": "moon_L", "mode": "rod", "floor": "E5", "anchor": (90.9, -30.3), "hub": "J5",
        "subs": ["m1", "m2"], "interface": "lune", "arc": (M_MOON, 50.0, list(range(100, 300, 10)))}]
)
PLACE_ORDER = ["venus_L", "neptune_L", "mercury_L", "mars_L", "uranus_L", "saturn_L", "jupiter_L",
               "moon_perigee", "saros", "moon_node", "moon_L"]
# Modules changés pour la géométrie seule (rapport inchangé), comme les modules par composante de la v1 :
# Neptune, couple 11:147 en m 0,55 pour que la roue de 148 dégage l'axe de la tour.
# Jupiter, couple 10:26 en m 0,7 (entraxe 12,6 mm) pour que la roue de reprise dégage l'arbre voisin.
MODULE_OVERRIDE = {"neptune_L": ["1/2", "11/20"], "jupiter_L": ["7/10", "1/2"]}
# Train J → Y : ordre des couples inversé (10:83, 19:144, 31:180), même rapport ; la roue de 180 est sur Y.
Y_TRAIN_STAGES = [[10, 83, "external"], [19, 144, "external"], [31, 180, "external"]]
Y_TRAIN_OPTIONS = [("E4", "A"), ("E4", "B"), ("E4", "C")]

# Budget en hauteur des blocs-mécanismes (plans de 3 mm), revue N5. Estimations : composants côte à côte quand le
# rayon du bloc le permet ; différentiels plats (planétaires, 3 plans).
BLOCK_PLANES = {
    "lune": (26, "4 entrées sur l'axe M (L, ϖ, Ω, Y), copie de l'UAK Terre (4), cascade (13 : réduction 2, équation "
                 "annuelle = différentiel plat 3 + couple 30:155, évection = différentiel plat 3, anomalie 2, variation 2), "
                 "prises (3), coulisse d'éclipse et porte-nœuds (2)"),
    "temps": (20, "5 différentiels plats (2 par plan de 3), joint de Hooke (5 plans), 120:12, 15:179 et son fou, "
                  "copie de l'UAK Terre (4 plans), entrées et sorties"),
    "laplace": (18, "3 trains de 3 couples (9), 2 doubleurs, 2 différentiels plats côte à côte (3), "
                    "4 couples vers le cadran jovien (4)"),
    "cal_meca": (8, "2 croix de Malte, différentiel, 20:61, roues-programmes 4/100/400 et cames"),
}
# Les différentiels sont réalisés à plat (engrenages droits, satellites par paires) : même relation que les
# différentiels coniques de trains.json, mais 3 plans de haut au lieu d'une vingtaine de millimètres.
