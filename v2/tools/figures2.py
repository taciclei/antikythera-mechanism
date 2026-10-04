"""Figures à l'échelle : faces avant/arrière, couvercle (orrery), plans d'étages, coupe en z."""
import json
import math
import os

import arch_faces as FA
import arch_layout as L
from figures import COL, V2, esc, svg

SUBCOL = ["#b23a2e", "#2f5d8a", "#2e8b57", "#6b5aa6", "#c27a12", "#5f6f86"]


def _load():
    with open(os.path.join(V2, "spec", "architecture.json")) as f:
        return json.load(f)


def _face(ox, oy, s, dials, title, mirror, extra):
    X = (lambda x: ox + (225 - x) * s) if mirror else (lambda x: ox + (x + 225) * s)
    Y = lambda y: oy + (170 - y) * s  # noqa: E731
    b = [f'<rect x="{ox}" y="{oy}" width="{450 * s}" height="{340 * s}" rx="6" fill="none" stroke="currentColor" stroke-width="1.6"/>',
         f'<text x="{ox}" y="{oy - 10}" font-weight="600" font-size="13">{esc(title)}</text>']
    for key, d in dials.items():
        (x, y), R = d["c"], d["R"]
        b.append(f'<circle cx="{X(x):.1f}" cy="{Y(y):.1f}" r="{R * s:.1f}" fill="none" stroke="currentColor" stroke-width="1.2"/>')
        b += extra(key, X(x), Y(y), R * s, s)
        t = esc(d["titre"].split(" (")[0])
        if R >= 60:
            dy = -0.40 if key == "calendrier" else 0.62
            b.append(f'<text x="{X(x):.1f}" y="{Y(y) + R * s * dy:.1f}" text-anchor="middle" font-size="11" font-weight="600">{t}</text>')
        else:  # petits cadrans : titre côté intérieur de la face, au-dessus ou au-dessous
            side = 1 if X(x) < ox + 225 * s else -1
            anchor = "start" if side > 0 else "end"
            tx = X(x) - side * R * s
            ty = Y(y) + R * s + 14 if Y(y) < oy + 170 * s else Y(y) - R * s - 6
            b.append(f'<text x="{tx:.1f}" y="{ty:.1f}" text-anchor="{anchor}" font-size="10.5">{t}</text>')
    return b


def _ring(cx, cy, r0, r1, kind, ticks=0):
    c = COL[kind]
    out = [f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{(r0 + r1) / 2:.1f}" fill="none" stroke="{c}" class="c-{kind}" '
           f'stroke-opacity="0.35" stroke-width="{r1 - r0:.1f}"/>']
    for k in range(ticks):
        a = 2 * math.pi * k / ticks
        out.append(f'<line x1="{cx + r0 * math.cos(a):.1f}" y1="{cy + r0 * math.sin(a):.1f}" x2="{cx + r1 * math.cos(a):.1f}" '
                   f'y2="{cy + r1 * math.sin(a):.1f}" stroke="currentColor" stroke-width="0.6" opacity="0.6"/>')
    return out


def fig_faces():
    s = 0.92
    def front_extra(key, cx, cy, R, s):
        if key == "principal":
            o = _ring(cx, cy, 136 * s, 150 * s, "time", 36) + _ring(cx, cy, 112 * s, 134 * s, "sun", 12)
            for i, ang in enumerate([20, 65, 100, 150, 200, 235, 280, 315, 340, 5]):
                a = math.radians(ang)
                rr = (60 + 5 * i) * s
                o.append(f'<line x1="{cx:.1f}" y1="{cy:.1f}" x2="{cx + rr * math.cos(a):.1f}" y2="{cy - rr * math.sin(a):.1f}" '
                         f'stroke="currentColor" stroke-width="1" opacity="0.45"/>')
            o.append(f'<text x="{cx:.1f}" y="{cy + 40 * s:.1f}" text-anchor="middle" font-size="10" opacity="0.8">dix aiguilles coaxiales</text>')
            o.append(f'<text x="{cx:.1f}" y="{cy - 100 * s:.1f}" text-anchor="middle" font-size="9.5" opacity="0.8">zodiaque tropique</text>')
            o.append(f'<text x="{cx:.1f}" y="{cy - 140 * s:.1f}" text-anchor="middle" font-size="9.5" opacity="0.8">constellations J2000</text>')
            return o
        return [f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="2" fill="currentColor"/>']

    def back_extra(key, cx, cy, R, s):
        if key == "calendrier":
            o = _ring(cx, cy, 90 * s, 105 * s, "time", 12)
            o.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{84 * s:.1f}" fill="none" stroke="currentColor" stroke-dasharray="3 3" stroke-width="0.8"/>')
            for bid, lab in (("semaine", "jours"), ("annees", "années")):
                bx, by = L.BLOCKS[bid]["c"]
                dx, dy = -(bx - L.K_CAL[0]) * s, -(by - L.K_CAL[1]) * s
                o.append(f'<circle cx="{cx + dx:.1f}" cy="{cy + dy:.1f}" r="{L.BLOCKS[bid]["r"] * s:.1f}" fill="none" stroke="currentColor" stroke-width="0.9"/>')
                o.append(f'<text x="{cx + dx:.1f}" y="{cy + dy + 3:.1f}" text-anchor="middle" font-size="9">{lab}</text>')
            o.append(f'<text x="{cx:.1f}" y="{cy - 92 * s:.1f}" text-anchor="middle" font-size="9" opacity="0.8">366 dates</text>')
            return o
        if key == "eclipses":
            o = [f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{80 * s:.1f}" fill="{COL["ecl"]}" class="c-ecl" fill-opacity="0.08" stroke="{COL["ecl"]}" stroke-width="1"/>']
            a = math.radians(25)
            o.append(f'<line x1="{cx - 78 * s * math.cos(a):.1f}" y1="{cy + 78 * s * math.sin(a):.1f}" x2="{cx + 78 * s * math.cos(a):.1f}" '
                     f'y2="{cy - 78 * s * math.sin(a):.1f}" stroke="{COL["ecl"]}" class="c-ecl" stroke-width="1.6"/>')
            o.append(f'<text x="{cx:.1f}" y="{cy + 50 * s:.1f}" text-anchor="middle" font-size="9.5">ligne des nœuds, échelle γ</text>')
            return o
        if key == "saros":
            o = _ring(cx, cy, 30 * s, 40 * s, "ecl", 0)
            o.append(f'<circle cx="{cx:.1f}" cy="{cy + 12 * s:.1f}" r="{11 * s:.1f}" fill="none" stroke="currentColor" stroke-width="0.8"/>')
            return o
        return [f'<text x="{cx:.1f}" y="{cy + 3:.1f}" text-anchor="middle" font-size="9" opacity="0.8">gravure</text>']

    b = _face(14, 30, s, FA.FRONT, "Face avant (vue de face)", False, front_extra)
    b += _face(14 + 450 * s + 40, 30, s, FA.BACK, "Face arrière (vue de dos)", True, back_extra)
    w = 14 + 2 * 450 * s + 40 + 14
    return svg(round(w), round(30 + 340 * s + 20), b,
               "Les deux faces à l'échelle : devant, le grand cadran du ciel et quatre petits cadrans ; derrière, le calendrier, "
               "les éclipses et le Saros.")


def fig_couvercle():
    s = 1.55
    z0, z1 = L.BACK_DOOR_Z[0], L.FRONT_COVER_Z[1]
    W = 470 * s
    X = lambda x: 20 + (x + 235) * s  # noqa: E731
    Z = lambda z: 34 + (z - z0 + 6) * s  # noqa: E731  (le dos en haut, l'avant en bas)
    b = [f'<rect x="20" y="34" width="{W:.0f}" height="{(z1 - z0 + 12) * s:.0f}" rx="6" fill="none" stroke="currentColor" stroke-width="1.6"/>',
         f'<text x="20" y="22" font-weight="600" font-size="13">Couvercle vu d\'en haut (le dos en haut, la face avant en bas)</text>']
    cx, cz = X(0), Z((z0 + z1) / 2)
    b.append(f'<circle cx="{cx:.1f}" cy="{cz:.1f}" r="7" fill="{COL["sun"]}" class="c-sun"/>')
    ecc = {"mercury": (0.2056, 77.46), "mars": (0.0934, 336.04)}
    for p, r in FA.ORRERY["rayons"].items():
        if p in ecc:
            e, w = ecc[p]
            a, bb = r * s, r * s * math.sqrt(1 - e * e)
            c = a * e
            ang = math.radians(w)
            ex, ey = cx - c * math.cos(ang), cz + c * math.sin(ang)
            b.append(f'<ellipse cx="{ex:.1f}" cy="{ey:.1f}" rx="{a:.1f}" ry="{bb:.1f}" transform="rotate({-w:.1f} {ex:.1f} {ey:.1f})" '
                     f'fill="none" stroke="{COL["planet"]}" class="c-planet" stroke-width="1.3"/>')
            if p == "mercury":  # cercle de référence centré sur le Soleil : l'écart montre l'excentricité
                b.append(f'<circle cx="{cx:.1f}" cy="{cz:.1f}" r="{a:.1f}" fill="none" stroke="currentColor" '
                         f'stroke-dasharray="2 3" stroke-width="0.8" opacity="0.7"/>')
        else:
            k = "sun" if p == "earth" else "planet"
            b.append(f'<circle cx="{cx:.1f}" cy="{cz:.1f}" r="{r * s:.1f}" fill="none" stroke="{COL[k]}" class="c-{k}" stroke-width="1"/>')
        b.append(f'<text x="{cx:.1f}" y="{cz - r * s - 3:.1f}" text-anchor="middle" font-size="10">{esc(L.NAME_FR[p])}</text>')
    ea = math.radians(200)
    ex, ez = cx + 52 * s * math.cos(ea), cz - 52 * s * math.sin(ea)
    gr = FA.ORRERY["tellurion"]["globe_r"] * s
    b.append(f'<circle cx="{ex:.1f}" cy="{ez:.1f}" r="{gr:.1f}" fill="{COL["time"]}" class="c-time" fill-opacity="0.35" stroke="currentColor"/>')
    b.append(f'<line x1="{cx:.1f}" y1="{cz:.1f}" x2="{ex:.1f}" y2="{ez:.1f}" stroke="{COL["ecl"]}" class="c-ecl" stroke-dasharray="4 3" stroke-width="1.2"/>')
    b.append(f'<text x="{ex - 6:.1f}" y="{ez + gr + 13:.1f}" text-anchor="middle" font-size="10">tellurion et aiguille d\'ombre</text>')
    zr = (L.FLOORS["E3"]["sub"]["T1"][0] + L.FLOORS["E3"]["sub"]["T1"][1]) / 2
    exits = [it for it in _load()["items"] if it["kind"] == "rod" and it["q"][1] >= L.PLATE["y"][1] - 3]
    for it in exits:
        x = it["q"][0]
        b.append(f'<circle cx="{X(x):.1f}" cy="{Z(zr):.1f}" r="3" fill="none" stroke="{COL["bus"]}" class="c-bus" stroke-width="1.4"/>')
    b.append(f'<text x="{X(-230):.1f}" y="{Z(zr) - 8:.1f}" font-size="10" opacity="0.85">{len(exits)} tringles montantes</text>')
    return svg(round(W + 40), round(34 + (z1 - z0 + 12) * s + 14), b,
               "L'orrery du couvercle à l'échelle : huit orbites comprimées autour du Soleil, l'ellipse de Mercure et celle "
               "de Mars visibles, la Terre en tellurion avec son aiguille d'ombre.")


def fig_etages():
    out = _load()
    items = out["items"]
    s, pw, ph, gx, gy = 0.6, 450 * 0.6, 340 * 0.6, 28, 58
    b, k = [], 0
    for fid, f in L.FLOORS.items():
        col, row = k % 2, k // 2
        ox, oy = 14 + col * (pw + gx), 30 + row * (ph + gy)
        b.append(f'<rect x="{ox}" y="{oy}" width="{pw}" height="{ph}" fill="none" stroke="currentColor" stroke-width="1"/>')
        b.append(f'<text x="{ox}" y="{oy - 8}" font-weight="600" font-size="11.5">{fid} : {esc(f["nom"])}</text>')
        subs = list(f["sub"].items())
        for it in items:
            z = it["z"]
            if min(z[1], f["z"][1]) - max(z[0], f["z"][0]) <= 1e-9:
                continue
            si = next(i for i, (_, (a, bb)) in enumerate(subs) if min(z[1], bb) - max(z[0], a) > 1e-9)
            c = SUBCOL[si % len(SUBCOL)]
            if it["kind"] == "cyl":
                x, y = it["c"]
                X, Y = ox + (x + 225) * s, oy + (170 - y) * s
                thin = it["r"] <= 4.5
                b.append(f'<circle cx="{X:.1f}" cy="{Y:.1f}" r="{max(it["r"] * s, 1.2):.1f}" fill="{c}" fill-opacity="{0.7 if thin else 0.10}" '
                         f'stroke="{c}" stroke-width="0.7"/>')
            else:
                (px, py), (qx, qy) = it["p"], it["q"]
                b.append(f'<line x1="{ox + (px + 225) * s:.1f}" y1="{oy + (170 - py) * s:.1f}" x2="{ox + (qx + 225) * s:.1f}" '
                         f'y2="{oy + (170 - qy) * s:.1f}" stroke="{c}" stroke-width="1.6" stroke-opacity="0.85"/>')
        for i, (sid, (a, bb)) in enumerate(subs):
            per = 3 if len(subs) > 4 else len(subs)
            step = pw / max(per, 3)
            b.append(f'<text x="{ox + 4 + (i % per) * step:.0f}" y="{oy + ph + 13 + 12 * (i // per)}" font-size="9" '
                     f'fill="{SUBCOL[i % len(SUBCOL)]}">{sid} {a:.0f}–{bb:.0f}</text>')
        k += 1
    ox, oy = 14 + (pw + gx), 30 + 2 * (ph + gy)
    legend = ["Cercles pâles : roues, blocs, couronnes.", "Points pleins : arbres qui traversent l'étage.",
              "Traits : tringles (renvois 1:1).", "Couleur : sous-étage (z en mm).",
              f"{len(out['verifications']['collisions'])} collision sur {out['verifications']['objets']} pièces."]
    for i, t in enumerate(legend):
        b.append(f'<text x="{ox + 6}" y="{oy + 18 + i * 18}" font-size="11">{esc(t)}</text>')
    return svg(round(14 + 2 * pw + gx + 14), round(30 + 3 * (ph + gy)), b,
               "Les cinq étages vus de face, à l'échelle, avec chaque roue, bloc, arbre et tringle placés par le vérificateur.")


def fig_coupe():
    s = 1.15
    z0, z1 = L.BACK_DOOR_Z[0], L.FRONT_COVER_Z[1]
    Zx = lambda z: 40 + (z - z0) * s  # noqa: E731
    Yy = lambda y: 70 + (240 - y) * s  # noqa: E731
    b = [f'<text x="40" y="22" font-size="11" opacity="0.85">arrière ←</text>',
         f'<text x="{Zx(z1):.1f}" y="22" text-anchor="end" font-size="11" opacity="0.85">→ avant</text>']
    for fid, f in L.FLOORS.items():
        a, bb = f["z"]
        b.append(f'<rect x="{Zx(a):.1f}" y="{Yy(170):.1f}" width="{(bb - a) * s:.1f}" height="{340 * s:.1f}" fill="{COL["time"]}" '
                 f'class="c-time" fill-opacity="0.06"/>')
        b.append(f'<text x="{Zx((a + bb) / 2):.1f}" y="{Yy(-140):.1f}" text-anchor="middle" font-weight="600" font-size="12">{fid}</text>')
        stag = -156 if list(L.FLOORS).index(fid) % 2 == 0 else -166
        b.append(f'<text x="{Zx((a + bb) / 2):.1f}" y="{Yy(stag):.1f}" text-anchor="middle" font-size="8.5">{a:.0f}–{bb:.0f}</text>')
    for name, (a, bb) in L.PLATES_Z.items():
        b.append(f'<rect x="{Zx(a):.1f}" y="{Yy(170):.1f}" width="{max((bb - a) * s, 2):.1f}" height="{340 * s:.1f}" fill="currentColor" opacity="0.75"/>')
        b.append(f'<text x="{Zx((a + bb) / 2):.1f}" y="{Yy(-170) + 13:.1f}" text-anchor="middle" font-size="9">{esc(name.replace("cadran ", ""))}</text>')
    def zbar(z0_, z1_, y0_, y1_, kind, lab=None):
        o = [f'<rect x="{Zx(z0_):.1f}" y="{Yy(y1_):.1f}" width="{(z1_ - z0_) * s:.1f}" height="{(y1_ - y0_) * s:.1f}" '
             f'fill="{COL[kind]}" class="c-{kind}" fill-opacity="0.22" stroke="{COL[kind]}" stroke-width="0.8"/>']
        if lab:
            o.append(f'<text x="{Zx((z0_ + z1_) / 2):.1f}" y="{Yy((y0_ + y1_) / 2) + 3:.1f}" text-anchor="middle" font-size="9">{esc(lab)}</text>')
        return o
    F = L.FLOORS
    b += zbar(F["E4"]["sub"]["A"][0], F["E4"]["sub"]["A"][1], 92 - 30, 92 + 30, "planet", "train")
    b += zbar(*F["E3"]["sub"]["uak"], 92 - 28, 92 + 28, "planet", "UAK")
    b += zbar(*F["E2"]["sub"]["mod"], 92 - 70, 92 + 70, "planet", "module")
    b.append(f'<text x="{Zx(F["E4"]["z"][0]) + 2:.1f}" y="{Yy(92 - 40):.1f}" font-size="9.5">tour de Mars (y = 92)</text>')
    b += zbar(*F["E3"]["sub"]["uak"], -28, 28, "sun", "Terre")
    b += zbar(*F["E1"]["sub"]["pile"], -49, 49, "time", "pile")
    b += zbar(L.sub("E5", "meca")[0], L.sub("E5", "meca")[1], -78 - 46, -78 + 46, "time", "temps")
    b.append(f'<line x1="{Zx(L.sub("E5", "meca")[0]):.1f}" y1="{Yy(0):.1f}" x2="{Zx(F["E3"]["sub"]["uak"][0]):.1f}" y2="{Yy(0):.1f}" '
             f'stroke="{COL["sun"]}" class="c-sun" stroke-width="3"/>')
    b.append(f'<line x1="{Zx(F["E3"]["sub"]["uak"][1]):.1f}" y1="{Yy(0):.1f}" x2="{Zx(L.Z_FRONT + 18):.1f}" y2="{Yy(0):.1f}" '
             f'stroke="currentColor" stroke-width="2"/>')
    b.append(f'<text x="{Zx(L.Z_FRONT + 4):.1f}" y="{Yy(0) - 6:.1f}" font-size="9.5">Soleil</text>')
    b.append(f'<text x="{Zx(F["E4"]["z"][0]) + 2:.1f}" y="{Yy(0) - 6:.1f}" font-size="9.5">arbre Y</text>')
    b.append(f'<rect x="{Zx(L.Z_FRONT):.1f}" y="{Yy(150):.1f}" width="{20 * s:.1f}" height="{300 * s:.1f}" fill="none" '
             f'stroke="currentColor" stroke-dasharray="3 3" stroke-width="0.8"/>')
    b.append(f'<text x="{Zx(L.Z_FRONT + 22):.1f}" y="{Yy(150) + 10:.1f}" font-size="9.5">aiguilles</text>')
    oy = Yy(225)
    oc = (z0 + z1) / 2
    b += zbar(oc - 40, oc + 40, 172, 205, "planet", "socle")
    b.append(f'<line x1="{Zx(oc - 111):.1f}" y1="{oy:.1f}" x2="{Zx(oc + 111):.1f}" y2="{oy:.1f}" stroke="{COL["planet"]}" class="c-planet" stroke-width="2"/>')
    b.append(f'<line x1="{Zx(oc):.1f}" y1="{Yy(178):.1f}" x2="{Zx(oc):.1f}" y2="{oy:.1f}" stroke="currentColor" stroke-width="1.4"/>')
    b.append(f'<text x="{Zx(oc):.1f}" y="{oy - 10:.1f}" text-anchor="middle" font-size="10.5">orrery du couvercle</text>')
    b.append(f'<text x="{Zx(z0):.1f}" y="{Yy(-178) + 26:.1f}" font-size="10">porte arrière</text>')
    b.append(f'<text x="{Zx(z1):.1f}" y="{Yy(-178) + 26:.1f}" text-anchor="end" font-size="10">verre avant</text>')
    return svg(round(Zx(z1) + 40), round(Yy(-178) + 40), b,
               "Coupe de la caisse : cinq étages entre le cadran arrière et le cadran avant, quatre platines, l'orrery sur le couvercle.")


def main(write):
    write("fig_faces.svg", fig_faces())
    write("fig_couvercle.svg", fig_couvercle())
    write("fig_etages.svg", fig_etages())
    write("fig_coupe.svg", fig_coupe())
