#!/usr/bin/env python3
"""Construit study/etude.html (page d'étude autonome) à partir des fichiers vérifiés de v2.

Entrées : spec/architecture.json, spec/trains.json, research/calc/*_results.json, study/fig_*.svg.
Les chiffres sont lus dans ces fichiers ; aucun n'est saisi à la main, sauf les rappels de méthode.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
V2 = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import etude_css  # noqa: E402
import etude_text  # noqa: E402

REPO = "https://github.com/taciclei/antikythera-mechanism"


def jl(*p):
    with open(os.path.join(V2, *p)) as f:
        return json.load(f)


def svg_inline(name):
    with open(os.path.join(V2, "study", name)) as f:
        s = f.read()
    return re.sub(r"^<\?xml[^>]*>\s*", "", s).strip()


def fr(x, nd=2):
    return f"{x:.{nd}f}".replace(".", ",").replace("-", "−")


def table(head, rows, num=()):
    th = "".join(f'<th class="{"num" if i in num else ""}">{h}</th>' for i, h in enumerate(head))
    trs = "".join("<tr>" + "".join(f'<td class="{"num" if i in num else ""}">{c}</td>' for i, c in enumerate(r)) + "</tr>"
                  for r in rows)
    return f'<div class="tbl"><table><thead><tr>{th}</tr></thead><tbody>{trs}</tbody></table></div>'


def figure(name, caption, cls=""):
    return f'<figure class="{cls}"><div class="art">{svg_inline(name)}</div><figcaption>{caption}</figcaption></figure>'


def data():
    A = jl("spec", "architecture.json")
    T = jl("spec", "trains.json")
    calc = {k: jl("research", "calc", f"{k}_results.json") for k in ("calendar_time", "eclipses", "moon", "geocentric")}
    return A, T, calc


def main():
    A, T, C = data()
    review = None
    rp = os.path.join(V2, "study", "review.md")
    if os.path.exists(rp):
        with open(rp) as f:
            review = f.read()
    body = "\n".join(etude_text.body(A, T, C, review, figure=figure, table=table, fr=fr, repo=REPO))
    html = f"""<title>Anticythère 2.0</title>
<meta name="description" content="Étude de conception d'une évolution moderne de la machine d'Anticythère : 8 planètes képlériennes, Lune moderne, calendrier grégorien, éclipses, lunes de Jupiter. Pas une reconstruction historique.">
{etude_css.FONTS}
<style>{etude_css.CSS}</style>
<div class="wrap"><article class="sheet">
{body}
</article></div>
"""
    out = os.path.join(V2, "study", "etude.html")
    with open(out, "w") as f:
        f.write(html)
    print("écrit", os.path.relpath(out, V2), f"({len(html) // 1024} Ko)")
    # Version GitHub Pages : document complet (l'Artifact ajoute lui-même ce squelette)
    pages = os.path.join(os.path.dirname(V2), "docs", "v2", "index.html")
    os.makedirs(os.path.dirname(pages), exist_ok=True)
    with open(pages, "w") as f:
        f.write('<!doctype html>\n<html lang="fr">\n<head>\n<meta charset="utf-8">\n'
                '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
                + html.replace("<div class=\"wrap\">", "</head>\n<body>\n<div class=\"wrap\">", 1)
                + "</body>\n</html>\n")
    print("écrit", os.path.relpath(pages, os.path.dirname(V2)))
    import shutil
    src = os.path.join(V2, "study", "img")
    if os.path.isdir(src):
        dst = os.path.join(os.path.dirname(pages), "img")
        os.makedirs(dst, exist_ok=True)
        for f in sorted(os.listdir(src)):
            shutil.copy2(os.path.join(src, f), os.path.join(dst, f))
        print("copié", len(os.listdir(src)), "images vers", os.path.relpath(dst, os.path.dirname(V2)))


if __name__ == "__main__":
    main()
