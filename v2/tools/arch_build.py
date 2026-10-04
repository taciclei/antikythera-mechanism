"""Assemble les résultats de l'architecture (version 2) et écrit spec/architecture.json."""
import json
import os

import arch_faces as F
import arch_geom as G
import arch_layout as L
import arch_report as RP
import arch_routes as R
import architecture as A


def _calc(name):
    with open(os.path.join(A.V2, "research", "calc", name)) as f:
        return json.load(f)


def error_budget(mods):
    geo, moon, cal, ecl = (_calc(n) for n in ("geocentric_results.json", "moon_results.json",
                                              "calendar_time_results.json", "eclipses_results.json"))
    mech = {"mercury": "kes", "venus": "eq", "mars": "eqe", "jupiter": "eq", "saturn": "eq", "uranus": "eq", "neptune": "eq"}
    jpl = geo["jpl_table1_lon_err_arcsec_1800_2050"]
    rows = []
    for p in L.TOWER_ORDER:
        b = geo["budget"][mech[p]][p]
        rows.append({"sortie": L.NAME_FR[p], "geometrie_deg": round(b["geo_total"], 2),
                     "physique_hors_kepler": f'{jpl[p]}″' if jpl[p] < 300 else f'{jpl[p] / 3600:.2f}°',
                     "tolerance_0_02mm_deg": mods[p]["follower_err_deg_for_0.02mm"],
                     "module_R_mm": mods[p]["module_radius_mm"]})
    mo = moon["moon_errors"]["RECOMMENDED cascade(red,ann,ev,anEQ,va)"]
    return {"planetes": rows, "lune_deg": {"max": mo["max_deg"], "rms": mo["rms_deg"]},
            "calendrier": f'exact de {cal["gregorian"]["years_checked"].replace("-", " à ")} (0 erreur)',
            "sideral_s_par_siecle": round(cal["sidereal"]["diff_seconds_per_century"], 3),
            "equation_du_temps_s": round(cal["equation_of_time"]["hooke_with_precession_input_max_err_s"], 1),
            "copies_uak_terre_deg": 0.05, "copies_uak_terre_edt_s": 12,
            "eclipses": {"detectees": ecl["detection"]["new"]["hits"] + ecl["detection"]["full"]["hits"],
                         "total": ecl["new"]["n"] + ecl["full"]["n"],
                         "gamma_err_max": round(max(ecl["new"]["gamma_err_max"], ecl["full"]["gamma_err_max"]), 3)}}


def build(write=True):
    trains, S, mods = A.load()
    items, report = A.assemble(S, mods)
    coll = G.collisions(items, L.CLEAR)
    outside = [it["id"] for it in items if it["z"][0] >= 3 and not G.inside_plate(it, L.PLATE)
               and not (it["kind"] == "rod" and it["id"].split("#")[0] in A.EXITS)]
    cov = RP.coverage(trains, report)
    faces = RP.faces_check()
    lid = RP.lid_check(items)
    wc = RP.wheel_count(trains, report)
    checks = {"objets": len(items), "trains_places": len(report["placed"]), "echecs_placement": report["failed"],
              "collisions": [list(c) for c in coll], "hors_platine": outside, "interfaces": RP.interfaces(items),
              "couverture": cov, "faces": faces, "couvercle": lid,
              "budgets_blocs": RP.block_budgets(items),
              "liens": "par identifiant exact : roue–arbre, roues qui engrènent, jonctions d'un renvoi ; "
                       "blocs et parties d'axe d'une même tour"}
    checks["ok"] = (not coll and not outside and not report["failed"] and not cov["missing"] and faces["ok"]
                    and lid["ok_spacing"] and lid["ok_fit"] and all(x["ok"] for x in checks["budgets_blocs"]))
    _, lap_r, lap_rads = A.laplace_block(S)
    out = {
        "meta": {"title": "Anticythère 2.0 — architecture de la machine (version 2, après revue)",
                 "generated_by": "v2/tools/architecture.py", "historique": False,
                 "inputs": ["v2/spec/trains.json", "v2/research/calc/*_results.json", "v2/tools/arch_layout.py",
                            "v2/tools/arch_routes.py", "v2/tools/arch_faces.py"],
                 "repere": "x à droite vu de face, y vers le haut, z vers l'observateur de la face avant ; mm ; "
                           "z = 0 sur la face extérieure du cadran arrière"},
        "etages": L.FLOORS, "platines_z": L.PLATES_Z, "z_cadran_avant": L.Z_FRONT,
        "faces": {"avant": F.FRONT, "arriere": F.BACK, "couvercle": F.ORRERY},
        "tours": {p: {"axe": L.TOWERS[p], "module_R_mm": mods[p]["module_radius_mm"], "uak": mods[p]["kepler_unit"],
                      "moyeu": L.TOWER_HUB[p]} for p in L.TOWER_ORDER},
        "blocs": L.BLOCKS, "laplace_rayons_trains_mm": {k: round(v, 1) for k, v in lap_rads.items()},
        "moyeux": L.HUBS, "carrousel_deg": report.get("carousel_deg"), "modules_changes": L.MODULE_OVERRIDE,
        "renvois": R.ROUTES, "trains_places": report["placed"], "verifications": checks,
        "roues": wc, "masse": RP.mass(trains, wc["total"]), "jeu": RP.backlash(), "sens": RP.signs(),
        "budget_erreur": error_budget(mods), "items": items,
    }
    out["masse"]["box_mm"] = out["masse"]["box_mm"]
    if write:
        with open(os.path.join(A.V2, "spec", "architecture.json"), "w") as f:
            json.dump(out, f, ensure_ascii=False, indent=1, default=list)
    return out
