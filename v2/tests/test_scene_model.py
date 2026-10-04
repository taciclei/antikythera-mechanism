"""Tests du modèle de scène (v2/tools/scene_model.py → v2/spec/scene.json).

Lancer depuis v2/ : $PY -m unittest discover -s tests -v
"""
import copy
import json
import math
import os
import sys
import unittest
from fractions import Fraction as F

HERE = os.path.dirname(os.path.abspath(__file__))
V2 = os.path.dirname(HERE)
if os.path.join(V2, "tools") not in sys.path:
    sys.path.insert(0, os.path.join(V2, "tools"))

import scene_model as SM  # noqa: E402

TWO_PI = 2.0 * math.pi


def ang_mod(x, p):
    """Écart de x à un multiple de p, dans [−p/2, p/2[."""
    return (x + p / 2) % p - p / 2


class SceneModelTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(SM.ARCH_PATH) as f:
            cls.arch = json.load(f)
        with open(SM.TRAINS_PATH) as f:
            cls.trains = json.load(f)
        cls.S = {s["id"]: s for s in cls.trains["shafts"]}
        cls.scene = SM.build(copy.deepcopy(cls.arch), copy.deepcopy(cls.trains))
        cls.parts = {p["id"]: p for p in cls.scene["parts"]}
        cls.pairs = sorted({tuple(sorted((a, b))) for a, p in cls.parts.items() for b in p["meshes_with"]})

    # ----------------------------------------------------------------------------------------------- structure
    def test_ids_unique_and_items_converted(self):
        ids = [p["id"] for p in self.scene["parts"]]
        self.assertEqual(len(ids), len(set(ids)))
        for it in self.arch["items"]:
            self.assertIn(it["id"], self.parts)
        kinds = {"gear", "crown", "bevel", "arbor", "tube", "rod", "block", "plate", "axis", "misc"}
        for p in self.scene["parts"]:
            self.assertIn(p["kind"], kinds, p["id"])
            for k in ("collection", "label", "links", "meshes_with", "motion", "rate", "phys", "phase", "axis"):
                self.assertIn(k, p, f"{p['id']} : {k}")
            self.assertIn(p["phys"], (1, -1))
            self.assertAlmostEqual(math.hypot(*p["axis"]), 1.0, places=9)

    def test_names_resolve(self):
        for p in self.scene["parts"]:
            for key in ("links", "meshes_with", "engages"):
                for n in p.get(key, []):
                    self.assertIn(n, self.parts, f"{p['id']}.{key} → {n}")

    def test_controller(self):
        c = self.scene["controller"]
        self.assertEqual(c["name"], "V2_Controleur")
        self.assertEqual(c["frames"], 366)
        self.assertEqual(c["start_jd"], 2461041.5)
        self.assertEqual(c["start_jours"], 2461041.5 - 2451545.0)

    # ----------------------------------------------------------------------------------------------- taux
    def shaft(self, sid):
        sh = self.S[sid]
        r = F(sh["rate_turns_per_day"])
        return r, (sh["phys"] if sh["phys"] is not None else (1 if r >= 0 else -1))

    def test_placed_train_rates_equal_trains_json(self):
        rep = self.scene["meta"]["trains"]
        self.assertEqual(set(rep), set(self.arch["trains_places"]))
        for key, r in rep.items():
            out = self.parts[r["output"]]
            rate, phys = self.shaft(key)
            if key == "precession_ring":  # sortie dessinée : arbre de la roue de 131 (anneau × 179/15, même sens)
                zd, zn, kind = self.S[key]["stages"][1]
                self.assertEqual(kind, "internal")
                rate = abs(rate) * F(zn, zd)
            else:
                self.assertEqual(F(out["rate_exact"]), rate, key)
            self.assertEqual(abs(F(out["rate_exact"])), abs(rate), key)
            self.assertLessEqual(abs(abs(out["rate"]) - float(abs(rate))), 1e-12 * max(1.0, float(abs(rate))))
            self.assertEqual(out["phys"], phys, key)
            src_rate, src_phys = self.shaft(r["source"])
            inp = self.parts[r["input"]]
            self.assertEqual(abs(F(inp["rate_exact"])), abs(src_rate), key)
            self.assertEqual(inp["phys"], src_phys, key)

    def test_linear_rate_floats_match_fractions(self):
        for p in self.scene["parts"]:
            if p["motion"] == "linear":
                self.assertEqual(p["rate"], float(F(p["rate_exact"])), p["id"])
                self.assertNotEqual(p["rate"], 0.0, p["id"])

    def test_wheels_turn_with_their_arbor(self):
        for it in self.arch["items"]:
            if it.get("wheel") != "train":
                continue
            arb = it["links"][0]
            if it["role"] == "reprise" and arb.startswith("axe_"):
                arb += "#tubeY"
            w, a = self.parts[it["id"]], self.parts[arb]
            self.assertEqual((w["rate_exact"], w["phys"]), (a["rate_exact"], a["phys"]), it["id"])

    def test_hubs_bus_and_moon_entries(self):
        y, j = self.shaft("Y"), self.shaft("J")
        for hub, h in self.arch["moyeux"].items():
            r, ph = y if h["src"] == "Y" else j
            self.assertEqual((F(self.parts[hub]["rate_exact"]), self.parts[hub]["phys"]), (r, ph), hub)
        for pid, p in self.parts.items():
            if pid.endswith("#bus#rod"):
                cour = self.parts[pid[:-4] + "#cour"]
                self.assertEqual(abs(F(p["rate_exact"])), 4 * abs(F(cour["rate_exact"])), pid)
            if pid.endswith("#tubeY"):
                self.assertEqual((F(p["rate_exact"]), p["phys"]), y, pid)
            if pid.startswith("lune_entree_") and pid.endswith("#w1"):
                w2, fou = self.parts[pid[:-1] + "2"], self.parts[pid[:-3] + "#fou"]
                self.assertEqual((w2["rate_exact"], w2["phys"]), (p["rate_exact"], p["phys"]), pid)
                self.assertEqual(fou["phys"], -p["phys"])

    def test_route_motions(self):
        for pid, p in self.parts.items():
            if pid.startswith("geo_") or pid.startswith("car_") or pid.startswith("tube_"):
                name = pid.split("#")[0].split("_", 1)[1]
                key = {"moon": "lambda_moon", "node": "node"}.get(name, "lambda_geo_" + name)
                self.assertEqual(p["motion"], "ephem:" + key, pid)
            if pid.startswith("orr_") and not pid.startswith("orr_moon"):
                self.assertEqual(p["motion"], "ephem:helio_" + pid.split("#")[0][4:], pid)
            if pid.startswith("vers_edt"):
                self.assertEqual(p["motion"], "ephem:eot")
                self.assertAlmostEqual(abs(p["scale"]), 10 * TWO_PI / 1440, places=15)
            if pid.startswith("gamma"):
                self.assertEqual(p["motion"], "fixed")
            if p["motion"].startswith("ephem:"):
                self.assertEqual(p["scale"], p["phys"] * (SM.EOT_SCALE if p["motion"] == "ephem:eot" else -1.0))
            if pid.startswith("tube_"):  # aiguilles du cadran avant : sens direct = horaire vu de face
                self.assertEqual((p["phys"], p["scale"]), (1, -1.0), pid)

    def test_ephem_keys_shared(self):
        used = {p["motion"][6:] for p in self.scene["parts"] if p["motion"].startswith("ephem:")}
        self.assertTrue(used <= set(SM.EPHEM_KEYS))
        try:
            import ephem
        except Exception:  # noqa: BLE001 — module d'un autre lot, facultatif ici
            self.skipTest("tools/ephem.py indisponible")
        self.assertTrue(used <= set(ephem.KEYS), used - set(ephem.KEYS))

    # ----------------------------------------------------------------------------------------------- roues
    def test_every_wheel_has_teeth_and_module(self):
        n = 0
        for p in self.scene["parts"]:
            if p["kind"] in ("gear", "crown", "bevel"):
                n += 1
                self.assertIsInstance(p["teeth"], int, p["id"])
                self.assertGreaterEqual(p["teeth"], 10, p["id"])
                self.assertGreater(p["m"], 0.0, p["id"])
                self.assertIn(p["mesh"], ("external", "internal", "crown", "bevel"), p["id"])
        self.assertGreater(n, 200)

    def test_meshes_with_symmetric(self):
        for pid, p in self.parts.items():
            for q in p["meshes_with"]:
                self.assertIn(pid, self.parts[q]["meshes_with"], f"{pid} ↔ {q}")
            for q in p.get("engages", []):
                self.assertIn(pid, self.parts[q]["engages"], f"{pid} ↔ {q}")
        for it in self.arch["items"]:  # partenaires des items conservés
            for q in it.get("partners", []):
                self.assertIn(q, self.parts[it["id"]]["meshes_with"])

    def test_centre_distances(self):
        idler = 0
        for a, b in self.pairs:
            A, B = self.parts[a], self.parts[b]
            self.assertEqual((A["kind"], B["kind"]), ("gear", "gear"), (a, b))
            self.assertEqual(A["m"], B["m"], (a, b))
            internal = "internal" in (A["mesh"], B["mesh"])
            za, zb = sorted((A["teeth"], B["teeth"])) if internal else (A["teeth"], B["teeth"])
            cd = A["m"] * ((zb - za) if internal else (za + zb)) / 2
            self.assertLess(abs(math.dist(A["c"], B["c"]) - cd), 1e-6, (a, b))
            idler += any(self.arch_item(x).get("role") in ("fou", "reprise_fou") for x in (a, b))
        self.assertGreaterEqual(idler, 2 * 7 + 2 * 2)  # 7 reprises et 2 fous d'étage, deux couples chacun

    def arch_item(self, pid):
        return next((it for it in self.arch["items"] if it["id"] == pid), {})

    def test_spur_kinematics(self):
        for a, b in self.pairs:
            A, B = self.parts[a], self.parts[b]
            self.assertEqual(A["phys"], -B["phys"], (a, b))
            if A["motion"] == "linear":
                self.assertEqual(abs(F(A["rate_exact"])) * A["teeth"], abs(F(B["rate_exact"])) * B["teeth"], (a, b))
            else:
                self.assertEqual((A["motion"], A["teeth"], A["scale"]), (B["motion"], B["teeth"], -B["scale"]))

    def test_phases_interleave(self):
        for a, b in self.pairs:
            A, B = self.parts[a], self.parts[b]
            beta = math.atan2(B["c"][1] - A["c"][1], B["c"][0] - A["c"][0])
            want = SM.mesh_phase(A["phase"], beta, A["teeth"], B["teeth"])
            self.assertLess(abs(ang_mod(want - B["phase"], TWO_PI / B["teeth"])), 1e-9, (a, b))

    def test_crown_contacts(self):
        n = 0
        for pid, p in self.parts.items():
            if p["kind"] != "crown":
                continue
            self.assertIn(p["face"], (1, -1))
            for q in p["engages"]:
                g = self.parts[q]
                n += 1
                self.assertEqual((g["teeth"], p["teeth"]), (24, 96))
                self.assertAlmostEqual(math.dist(g["c"], p["c"]), SM.HUB_PIN_AT, places=9)
                self.assertEqual(abs(F(g["rate_exact"])), 4 * abs(F(p["rate_exact"])), (pid, q))
                c = (g["c"][0] - p["c"][0], g["c"][1] - p["c"][1])
                self.assertEqual(g["phys"], SM.crown_rule(p["phys"], p["face"], g["axis"], c), (pid, q))
        self.assertEqual(n, 31)

    # ----------------------------------------------------------------------------------------------- platines
    def test_plates(self):
        plates = {p["id"]: p for p in self.scene["parts"] if p["kind"] == "plate"}
        self.assertEqual(set(plates), set(SM.PLATE_IDS.values()))
        for name in ("P1", "P2", "P3", "P4"):
            self.assertTrue(plates["platine_" + name]["holes"], name)
        for pid, pl in plates.items():
            self.assertEqual(pl["size"], [450.0, 340.0])
            z0, z1 = pl["z"]
            for h in pl["holes"]:
                self.assertLess(abs(h["c"][0]) + h["r"], 225.0)
                self.assertLess(abs(h["c"][1]) + h["r"], 170.0)
            for p in self.scene["parts"]:
                if p["kind"] in ("arbor", "tube", "axis") and p["z"][0] < z1 and p["z"][1] > z0:
                    h = [h for h in pl["holes"] if p["id"] in h["ids"]]
                    self.assertEqual(len(h), 1, (pid, p["id"]))
                    self.assertLess(math.dist(h[0]["c"], p["c"]), 1e-9)
                    self.assertGreaterEqual(h[0]["r"], p["r"] + 0.3 - 1e-9)

    # ----------------------------------------------------------------------------------------------- fichier
    def test_json_deterministic_and_up_to_date(self):
        again = SM.dumps(SM.build(copy.deepcopy(self.arch), copy.deepcopy(self.trains)))
        self.assertEqual(again, SM.dumps(self.scene))
        with open(SM.OUT_PATH) as f:
            self.assertEqual(f.read(), again, "spec/scene.json périmé : relancer tools/scene_model.py")

    # ----------------------------------------------------------------------------------------------- échecs
    def test_input_check_fails_loudly(self):
        for sid, field, value in (("venus_L", "rate_turns_per_day", "18260/4102812"),
                                  ("moon_node", "phys", 1), ("Y", "rate_turns_per_day", "589/215135")):
            tr = copy.deepcopy(self.trains)
            next(s for s in tr["shafts"] if s["id"] == sid)[field] = value
            with self.assertRaises(SM.SceneError, msg=f"{sid}.{field}"):
                SM.build(copy.deepcopy(self.arch), tr)

    def test_teeth_mismatch_fails(self):
        ar = copy.deepcopy(self.arch)
        next(it for it in ar["items"] if it["id"] == "venus_L#w3")["teeth"] = 125
        with self.assertRaises(SM.SceneError):
            SM.build(ar, copy.deepcopy(self.trains))


def omega(p):
    """Vecteur vitesse angulaire (à un facteur positif près) : angle = −2π·phys·|rate|·t ou phys·base·valeur, base < 0."""
    import numpy as np
    w = -p["phys"] * (abs(float(F(p["rate_exact"]))) or 1.0)
    return w * np.asarray(p["axis"], float)


class SceneSenseTest(unittest.TestCase):
    """Sens physiques vérifiés par les vitesses au contact (indépendamment des règles de scene_model)."""

    @classmethod
    def setUpClass(cls):
        with open(SM.ARCH_PATH) as f:
            cls.arch = json.load(f)
        with open(SM.TRAINS_PATH) as f:
            cls.trains = json.load(f)
        cls.S = {s["id"]: s for s in cls.trains["shafts"]}
        cls.scene = SM.build(copy.deepcopy(cls.arch), copy.deepcopy(cls.trains))
        cls.parts = {p["id"]: p for p in cls.scene["parts"]}

    def test_crown_contacts_roll(self):
        import numpy as np
        n = 0
        for c in (p for p in self.parts.values() if p["kind"] == "crown"):
            zm = 0.5 * (c["z"][0] + c["z"][1])
            for q in c["engages"]:
                g = self.parts[q]
                C, Pc = np.array([*c["c"], zm]), np.array([*g["c"], zm])
                P = Pc + np.array([0.0, 0.0, -c["face"] * 4.8])  # point de contact : sous le pignon si face = +1
                vc, vp = np.cross(omega(c), P - C), np.cross(omega(g), P - Pc)
                self.assertGreater(float(np.dot(vc, vp)), 0.0, (c["id"], q))           # même sens au contact
                self.assertAlmostEqual(abs(float(F(g["rate_exact"]))), 4 * abs(float(F(c["rate_exact"]))), places=12)
                n += 1
        self.assertEqual(n, 31)

    def test_mitre_bevels_roll(self):
        import numpy as np
        n = 0
        for b in (p for p in self.parts.values() if p["kind"] == "bevel" and "rod" in p):
            A = np.asarray(b["apex_point"], float)
            for q in b["engages"]:
                z = self.parts[q]
                self.assertEqual(z["kind"], "bevel")
                self.assertLess(float(np.linalg.norm(np.asarray(z["apex_point"]) - A)), 1e-9, (b["id"], q))
                d = -b["apex"] * np.asarray(b["axis"], float) - z["apex"] * np.asarray(z["axis"], float)
                self.assertAlmostEqual(float(np.dot(b["axis"], z["axis"])), 0.0, places=12)
                vb, vz = np.cross(omega(b), d), np.cross(omega(z), d)
                self.assertTrue(np.allclose(vb, vz, atol=1e-12), (b["id"], q, vb, vz))
                self.assertEqual((b["motion"], b["rate_exact"]), (z["motion"], z["rate_exact"]))
                n += 1
        self.assertGreaterEqual(n, 34)

    def test_hub_route_arrivals_keep_sense(self):
        """architecture.json « sens » : con → con garde le sens (lune_Y, j_avant, temps_J, temps_Y)."""
        sens = {s["renvoi"]: s for s in self.arch["sens"]}
        n = 0
        for rv in self.arch["renvois"]:
            if rv["id"] not in SM.HUB_ROUTES or rv["id"] == "manivelle":
                continue
            self.assertTrue(sens[rv["id"]]["chaine"].startswith("con → con"))
            src = self.S[rv["shaft"]]
            arb = self.parts[rv["id"] + "#z1"]
            crown = self.parts[rv["id"] + "#m0q"]
            for p in (arb, crown):
                self.assertEqual((F(p["rate_exact"]), p["phys"]), (F(src["rate_turns_per_day"]), src["phys"]), p["id"])
            rod = self.parts[rv["id"] + "#r0"]
            pin = self.parts[rv["id"] + "#m0q~pin"]
            far = max(math.dist(rod["p"], crown["c"]), math.dist(rod["q"], crown["c"]))
            self.assertGreaterEqual(far + 1e-9, math.dist(pin["c"], crown["c"]) + SM.PIN_WIDTH / 2)
            self.assertLessEqual(math.dist(pin["c"], crown["c"]) + SM.PIN_WIDTH / 2, SM.CROWN_R + 1e-9)
            if crown["face"] > 0:  # pignon au-delà du centre : l'arbre s'arrête sous la tringle
                self.assertLess(arb["z"][1], 0.5 * (rod["z"][0] + rod["z"][1]) - rod["r"])
            n += 1
        self.assertEqual(n, 4)

    def test_orrery_rods_turn_like_lid_arms(self):
        """faces_lid : bras de l'orrery = +λ autour de +Y (scale +1) ; les tringles qui les mènent tournent pareil."""
        rods = [p for p in self.parts.values() if p["kind"] == "rod" and p["id"].startswith("orr_")]
        self.assertEqual(len(rods), 9)
        for r in rods:
            self.assertEqual(r["axis"], [0.0, 1.0, 0.0], r["id"])
            self.assertEqual((r["phys"], r["scale"]), (-1, 1.0), r["id"])

    def test_tower_tube_y(self):
        y = (F(self.S["Y"]["rate_turns_per_day"]), self.S["Y"]["phys"])
        for pid, p in self.parts.items():
            if pid.startswith("axe_") and (pid.endswith("#haut") or pid.endswith("#tubeY")):
                self.assertEqual((p["kind"], F(p["rate_exact"]), p["phys"]), ("tube", *y), pid)
            if pid.startswith("axe_") and pid.endswith("#tubeY"):  # vrai tube autour de l'arbre L
                self.assertGreater(p["r_in"], self.parts[pid[:-len("#tubeY")]]["r"], pid)
            if pid.endswith("#bus#cour") and pid.split("#")[0] in ("venus_L", "mercury_L", "mars_L", "jupiter_L",
                                                                      "saturn_L", "uranus_L", "neptune_L"):
                self.assertIn(pid, [x for h in self.parts.values() if h["id"].endswith("#haut")
                                    for x in [pid] if math.dist(h["c"], p["c"]) < 1e-9])
                self.assertEqual(p["arbor_r"], 4.0, pid)

    def test_rate_signs_follow_trains_json(self):
        """Une pièce qui tourne comme un arbre de trains.json en porte le taux signé (ex. J : +1, phys −1)."""
        for pid in ("axe_J", "J5", "moon_L#a0", "j_avant#z1", "temps_J#z1"):
            self.assertEqual((self.parts[pid]["rate_exact"], self.parts[pid]["phys"]), ("1", -1), pid)
        for r in self.scene["meta"]["trains"].values():
            src = self.S[r["source"]]
            self.assertEqual(F(self.parts[r["input"]]["rate_exact"]), F(src["rate_turns_per_day"]), r["input"])

    def test_coaxial_supports_declared_and_cleared(self):
        """Roue d'axe Z : tout arbre/tube/axe coaxial qui traverse son corps est lié et tient dans l'alésage."""
        sup = [p for p in self.parts.values() if p["kind"] in ("arbor", "tube", "axis", "misc") and "c" in p]
        for p in self.parts.values():
            if p["kind"] not in ("gear", "crown", "bevel") or p["axis"] != [0.0, 0.0, 1.0] or p["mesh"] == "internal":
                continue
            z0, z1 = p["z"]
            if p["kind"] == "bevel":
                a = 0.5 * (z0 + z1)
                z0, z1 = (a + 2.0, a + 5.2) if p["apex"] < 0 else (a - 5.2, a - 2.0)
            for s in sup:
                if math.dist(s["c"], p["c"]) < 1e-6 and s["z"][0] < z1 - 1e-9 and s["z"][1] > z0 + 1e-9:
                    self.assertLessEqual(s["r"], p.get("arbor_r", 2.0), (p["id"], s["id"]))
                    self.assertTrue(s["id"] in p["links"] or p["id"] in s["links"], (p["id"], s["id"]))

    def test_tower_parts_linked(self):
        """arch_geom.linked : même groupe, ou lien vers le nom de base axe_x (vaut pour axe_x#haut, #tubeY, #bas)."""
        for it in self.arch["items"]:
            p = self.parts[it["id"]]
            for o in self.arch["items"]:
                if o["id"] != it["id"] and it.get("group") and o.get("group") == it["group"]:
                    self.assertIn(o["id"], p["links"], (it["id"], o["id"]))
            for lk in it.get("links", []):
                if lk.startswith("axe_") and "#" not in lk:
                    for o in self.parts:
                        if o.startswith(lk + "#") and o.split("#")[1] in ("haut", "tubeY", "bas"):
                            self.assertIn(o, p["links"], (it["id"], o))

    def test_moving_route_arbors_have_a_wheel(self):
        """Chaque arbre de renvoi mobile porte au moins une roue à sa vitesse (ex. lunette#z0 : conique « ~z2 »)."""
        for a in self.parts.values():
            if a["kind"] != "arbor" or a["motion"] == "fixed" or not self.arch_route(a["id"]):
                continue
            ok = False
            for w in self.parts.values():
                if w["kind"] in ("gear", "crown", "bevel") and "c" in w and w["axis"] == [0.0, 0.0, 1.0] \
                        and math.dist(w["c"], a["c"]) < 1e-6 and (w["motion"], w["rate_exact"], w["phys"]) == \
                        (a["motion"], a["rate_exact"], a["phys"]):
                    z0, z1 = w["z"]
                    if w["kind"] == "bevel":
                        m = 0.5 * (z0 + z1)
                        z0, z1 = (m + 2.0, m + 5.2) if w["apex"] < 0 else (m - 5.2, m - 2.0)
                    ok = ok or (a["z"][0] < z1 and a["z"][1] > z0)
            self.assertTrue(ok, a["id"])

    def test_every_arbor_at_a_corner_is_engaged(self):
        """Tout arbre vertical qui entre dans la zone d'une conique couchée (au-dessus ou au-dessous du sommet) y
        porte une conique engrenée sur elle (sinon : arbre non mené, ex. lunette#z0 sur geo_jupiter#m1p)."""
        n = 0
        for b in (p for p in self.parts.values() if p["kind"] == "bevel" and "rod" in p):
            x, y, a = b["apex_point"]
            for s in self.parts.values():
                if s["kind"] not in ("arbor", "tube", "axis") or "c" not in s or math.dist(s["c"], (x, y)) > 1e-6:
                    continue
                sides = {apex for lo, hi, apex in ((a + 2.0, a + 5.2, -1), (a - 5.2, a - 2.0, 1))
                         if s["z"][0] <= lo + 1e-6 and s["z"][1] >= hi - 1e-6}
                if not sides:
                    continue
                if len(sides) == 2:  # arbre traversant (ex. prec#a1) : une conique d'un côté ou de l'autre suffit
                    sides = {-1, 1}
                mates = [self.parts[q] for q in b["engages"]]
                self.assertTrue(any(m["apex"] in sides and math.dist(m["c"], s["c"]) < 1e-6 for m in mates),
                                (b["id"], s["id"], sides))
                n += 1
        self.assertGreaterEqual(n, 27)

    def test_engaged_teeth_interleave(self):
        """À jours = 0, au point de contact, la dent la plus proche de l'une tombe sur le creux le plus proche de
        l'autre (positions 3D refaites avec les conventions de parts.py : dent 0 à l'angle `phase`, pièce couchée
        comptée de ẑ × u vers +Z, couronne : dents sur k·2π/96)."""
        import numpy as np
        Zh = np.array([0.0, 0.0, 1.0])

        def ring(O, e1, e2, rho, phase, n, half):
            ang = phase + (np.arange(n) + (0.5 if half else 0.0)) * TWO_PI / n
            return O + rho * (np.cos(ang)[:, None] * e1 + np.sin(ang)[:, None] * e2)

        def lying_frame(p):
            u = np.asarray(p["axis"], float)
            return u, np.cross(Zh, u)

        n = 0
        for a in self.parts.values():
            for bid in a.get("engages", []):
                b = self.parts[bid]
                if a["kind"] == "crown":
                    zm = 0.5 * (a["z"][0] + a["z"][1])
                    u, e1 = lying_frame(b)
                    R = math.dist(a["c"], b["c"])
                    rho = R * b["teeth"] / a["teeth"]
                    Ob = np.array([*b["c"], zm])
                    K = Ob - a["face"] * rho * Zh
                    teeth = ring(Ob, e1, Zh, rho, b["phase"], b["teeth"], False)
                    gaps = ring(np.array([*a["c"], K[2]]), np.array([1.0, 0, 0]), np.array([0, 1.0, 0]), R,
                                a["phase"], a["teeth"], True)
                    pitch = rho * TWO_PI / b["teeth"]
                elif a["kind"] == "bevel" and abs(a["axis"][2]) < 0.5:
                    A = np.asarray(a["apex_point"], float)
                    u, e1 = lying_frame(a)
                    d = -a["apex"] * u - b["apex"] * Zh
                    K = A + 4.8 * d                      # génératrice primitive : rayon 4,8 sur les deux coniques
                    teeth = ring(A + np.dot(K - A, u) * u, e1, Zh, 4.8, a["phase"], a["teeth"], False)
                    gaps = ring(A + np.dot(K - A, Zh) * Zh, np.array([1.0, 0, 0]), np.array([0, 1.0, 0]), 4.8,
                                b["phase"], b["teeth"], True)
                    pitch = 4.8 * TWO_PI / a["teeth"]
                else:
                    continue
                t = teeth[np.argmin(np.linalg.norm(teeth - K, axis=1))]
                g = gaps[np.argmin(np.linalg.norm(gaps - K, axis=1))]
                off = float(np.dot(t - g, e1))           # dentures périodiques : écart compté modulo le pas
                self.assertLess(abs(ang_mod(off, pitch)), 0.05 * pitch, (a["id"], bid, off))
                n += 1
        self.assertEqual(n, 66)

    def arch_route(self, pid):
        return next((it.get("route") for it in self.arch["items"] if it["id"] == pid), None)

    def test_mesh_phase_is_v1(self):
        import importlib.util
        path = os.path.join(os.path.dirname(V2), "build", "am", "involute.py")
        if not os.path.exists(path):
            self.skipTest("v1 absente")
        spec = importlib.util.spec_from_file_location("v1_involute", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        for phi, beta, z1, z2 in ((0.0, 0.3, 24, 96), (1.2, -2.0, 17, 37), (-0.4, 3.0, 189, 166)):
            self.assertEqual(SM.mesh_phase(phi, beta, z1, z2), mod.mesh_phase(phi, beta, z1, z2))


if __name__ == "__main__":
    unittest.main()
