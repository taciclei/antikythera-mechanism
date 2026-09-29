# Dossier du projet (page HTML autonome)

Génère `docs/dossier.html` (publié sur GitHub Pages et comme Artifact claude.ai) à partir de `template.html`
(mise en page et textes), `data.py` (les 69 engrenages), `figs.py` (plans à l'échelle et arbre des trains en SVG),
des chiffres lus dans le projet (`lean/Antikythera/*.lean`, `build/out/explainer/report.json` et `glyphs.json`) et des
images `*.jpg` intégrées en base64.

```sh
~/voxtral-tts/bin/python tools/dossier/prep_images.py      # seulement si les images du film changent
/Applications/Blender.app/Contents/Resources/5.2/python/bin/python3.13 tools/dossier/build.py
```

`build.py` échoue si un nombre annoncé ne correspond plus au projet (théorèmes Lean, glyphes, tableau des éclipses).
