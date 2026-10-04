"""Anticythère 2.0 — faces, couvercle et options (données de conception)."""
from arch_layout import K_CAL, M_MOON, SAROS_AX

# ---------------------------------------------------------------- faces et couvercle
# Coordonnées machine (x vers la droite VU DE FACE). Vue de dos, la gauche et la droite s'échangent.
FRONT = {
    "principal": {"c": (0.0, 0.0), "R": 150.0, "titre": "Le ciel vu de la Terre",
                  "anneaux": [("constellations J2000 et degrés de longitude (fixe, repère des étoiles)", 136, 150),
                              ("zodiaque tropique et mois grégoriens (tourne : précession, 1 tour en 25 772 ans)", 112, 134)],
                  "aiguilles": ["Soleil vrai (arbre central)", "Lune vraie et boule de phase", "Mercure", "Vénus", "Mars",
                                "Jupiter", "Saturne", "Uranus", "Neptune", "Dragon (nœuds de la Lune)"]},
    "horloge": {"c": (-188.0, 118.0), "R": 34.0, "titre": "Horloge 24 h",
                "aiguilles": ["temps solaire moyen (arbre-jour J)", "temps sidéral (gmst)"]},
    "jupiter": {"c": (-188.0, -118.0), "R": 34.0, "titre": "Jupiter et ses lunes",
                "aiguilles": ["Io", "Europe", "Ganymède", "Callisto", "ligne des conjonctions ν", "lunette (barre à λ_J,géo + 90°)"]},
    "edt": {"c": (188.0, -118.0), "R": 34.0, "titre": "Équation du temps (±16,5 min, ×10)",
            "aiguilles": ["équation du temps"]},
    "epoque": {"c": (188.0, 118.0), "R": 34.0, "titre": "Plaque d'époque (fixe)",
               "aiguilles": ["gravé : orbites figées en 2050, valable 2000–2100, date de mise à l'heure"]},
}
BACK = {
    "calendrier": {"c": K_CAL, "R": 105.0, "titre": "Calendrier grégorien",
                   "aiguilles": ["anneau des 366 dates (lu à l'index du haut)", "guichet du jour de la semaine",
                                 "cadran des années 00-99 et guichet des 400 ans", "voyant « bissextile »"]},
    "eclipses": {"c": M_MOON, "R": 105.0, "titre": "Éclipses",
                 "aiguilles": ["Soleil vrai", "Lune vraie", "disque des nœuds gravé en γ et en magnitudes",
                               "index de la coulisse (γ, amplifié)", "secteur total / annulaire"]},
    "saros": {"c": SAROS_AX, "R": 40.0, "titre": "Saros (223 lunaisons) et Exeligmos",
              "aiguilles": ["aiguille du Saros sur 223 cases", "petit cadran de l'Exeligmos (+0 h, +8 h, +16 h)"]},
    "mode_emploi": {"c": (-120.0, -135.0), "R": 30.0, "titre": "Plaque « mode d'emploi » (fixe)",
                    "aiguilles": ["gravé : comment lire chaque cadran, comme les inscriptions de la v1"]},
}
# Orrery du couvercle : rayons affichés (mm), comprimés ; les angles restent exacts.
ORRERY = {"centre_xz": (0.0, None), "rayons": {"mercury": 24, "venus": 38, "earth": 52, "mars": 66,
                                                 "jupiter": 80, "saturn": 92, "uranus": 102, "neptune": 111},
          "tellurion": {"globe_r": 7.0, "bras_lune": 12.0, "inclinaison_deg": 23.44}}
OPTIONS_PLACE = {"gmst_direct": "option : bloc temps", "synodic": "option : bloc lune",
                 "saros_223": "option : roue de 223 dents du Saros (face arrière)",
                 "mars_apsides": "option : tour de Mars", "moon_phase": "aiguille de la Lune (couronne 48:48 menée par le tube du Soleil)",
                 "exeligmos": "cadran du Saros (face arrière)", "tellurion": "route tellurion"}
