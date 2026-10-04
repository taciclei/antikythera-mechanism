"""Feuille de style de study/etude.html (bureau d'études : encre bleu-noir sur papier, bronze en accent)."""

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500'
         '&family=IBM+Plex+Sans+Condensed:wght@500;600;700&family=IBM+Plex+Sans:ital,wght@0,400;0,500;0,600;1,400'
         '&display=swap">')

CSS = r"""
:root{
  --paper:#f4f5f1; --sheet:#fbfbf8; --ink:#17212c; --ink-2:#3d4a57; --muted:#66727e; --rule:#cfd5d8; --grid:#e6e9e6;
  --bronze:#9a5a17; --blue:#2a5a86; --warn-bg:#fbefe2; --warn-ink:#6b3a0c;
  --k-time:#2f5d8a; --k-planet:#a8641c; --k-moon:#5f6f86; --k-ecl:#b23a2e; --k-jup:#c27a12; --k-sun:#b8860f; --k-bus:#6b5aa6;
  --sans:"IBM Plex Sans",system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif;
  --cond:"IBM Plex Sans Condensed","IBM Plex Sans",system-ui,Arial,sans-serif;
  --mono:"IBM Plex Mono",ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    color-scheme:dark;
    --paper:#0f151c; --sheet:#141c25; --ink:#e4e9ee; --ink-2:#c3ccd5; --muted:#93a0ad; --rule:#2c3a48; --grid:#1b2531;
    --bronze:#dd9c55; --blue:#86b5e3; --warn-bg:#2b2014; --warn-ink:#f1c89a;
    --k-time:#86b5e3; --k-planet:#dd9c55; --k-moon:#a9b7cc; --k-ecl:#ef7d6f; --k-jup:#f0a948; --k-sun:#e8c15a; --k-bus:#b3a5ef;
  }
}
:root[data-theme="dark"]{
  color-scheme:dark;
  --paper:#0f151c; --sheet:#141c25; --ink:#e4e9ee; --ink-2:#c3ccd5; --muted:#93a0ad; --rule:#2c3a48; --grid:#1b2531;
  --bronze:#dd9c55; --blue:#86b5e3; --warn-bg:#2b2014; --warn-ink:#f1c89a;
  --k-time:#86b5e3; --k-planet:#dd9c55; --k-moon:#a9b7cc; --k-ecl:#ef7d6f; --k-jup:#f0a948; --k-sun:#e8c15a; --k-bus:#b3a5ef;
}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font:16px/1.6 var(--sans);
  background-image:linear-gradient(var(--grid) 1px,transparent 1px),linear-gradient(90deg,var(--grid) 1px,transparent 1px);
  background-size:24px 24px;background-attachment:fixed}
.wrap{max-width:1080px;margin:0 auto;padding-inline:16px;padding-block:28px 64px}
.sheet{background:var(--sheet);border:1px solid var(--rule);padding:clamp(18px,4vw,48px)}
header.title{border-bottom:2px solid var(--ink);padding-bottom:22px;margin-bottom:8px}
.kicker{font:500 13px/1.3 var(--mono);letter-spacing:.08em;text-transform:uppercase;color:var(--bronze);margin:0 0 10px}
h1{font:700 clamp(36px,6vw,60px)/1.02 var(--cond);letter-spacing:-.01em;margin:0 0 14px;text-wrap:balance}
h2{font:700 clamp(24px,3.2vw,32px)/1.15 var(--cond);margin:56px 0 14px;text-wrap:balance;display:flex;gap:14px;align-items:baseline}
h2 .n{font:500 14px var(--mono);color:var(--bronze);min-width:2.2em}
h3{font:600 19px/1.3 var(--cond);margin:28px 0 8px;text-wrap:balance}
p,li{max-width:68ch}
.lede{font-size:19px;line-height:1.5;color:var(--ink-2);max-width:62ch;margin:0}
.warn{background:var(--warn-bg);color:var(--warn-ink);border-left:4px solid var(--bronze);padding:12px 16px;margin:22px 0 0;max-width:72ch}
.warn strong{color:inherit}
a{color:var(--blue);text-underline-offset:2px}
.figs{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:0;border:1px solid var(--rule);margin:26px 0 6px}
.figs div{padding:14px 16px;border-right:1px solid var(--rule);border-bottom:1px solid var(--rule)}
.figs b{display:block;font:600 26px/1.1 var(--cond);font-variant-numeric:tabular-nums}
.figs span{font-size:13px;color:var(--muted)}
figure{margin:22px 0 30px}
figure .art{border:1px solid var(--rule);background:var(--sheet);padding:10px;overflow-x:auto}
figure svg{display:block;width:100%;height:auto;min-width:560px;font-family:var(--sans)}
figure.narrow .art{max-width:600px}
figure.narrow svg{min-width:420px}
figcaption{font-size:14px;color:var(--muted);margin-top:8px;max-width:80ch}
figcaption b{color:var(--ink-2)}
.tbl{overflow-x:auto;margin:14px 0 22px;border:1px solid var(--rule)}
table{border-collapse:collapse;width:100%;font-size:14.5px;font-variant-numeric:tabular-nums}
th,td{padding:8px 12px;border-bottom:1px solid var(--rule);text-align:left;vertical-align:top}
th{font:600 13px/1.3 var(--cond);letter-spacing:.02em;background:color-mix(in srgb,var(--rule) 35%,transparent)}
tr:last-child td{border-bottom:0}
td.num,th.num{text-align:right;white-space:nowrap}
.mech{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:20px 32px;margin-top:10px}
@media (max-width:720px){.mech{grid-template-columns:1fr}}
.mech section{border-top:2px solid var(--ink);padding-top:10px}
.mech h3{margin:0 0 6px}
.mech .acc{font:500 13px/1.4 var(--mono);color:var(--bronze);margin:6px 0 0}
.mech p{margin:6px 0;font-size:15px}
code{font:13.5px var(--mono);background:color-mix(in srgb,var(--rule) 40%,transparent);padding:1px 4px}
ul.tight li{margin:3px 0}
.two{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:8px 32px}
footer{margin-top:48px;padding-top:16px;border-top:1px solid var(--rule);font-size:13.5px;color:var(--muted)}
svg .c-time{stroke:var(--k-time)} svg .c-time:not([fill="none"]){fill:var(--k-time)}
svg .c-planet{stroke:var(--k-planet)} svg .c-planet:not([fill="none"]){fill:var(--k-planet)}
svg .c-moon{stroke:var(--k-moon)} svg .c-moon:not([fill="none"]){fill:var(--k-moon)}
svg .c-ecl{stroke:var(--k-ecl)} svg .c-ecl:not([fill="none"]){fill:var(--k-ecl)}
svg .c-jup{stroke:var(--k-jup)} svg .c-jup:not([fill="none"]){fill:var(--k-jup)}
svg .c-sun{stroke:var(--k-sun)} svg .c-sun:not([fill="none"]){fill:var(--k-sun)}
svg .c-bus{stroke:var(--k-bus)} svg .c-bus:not([fill="none"]){fill:var(--k-bus)}
svg text.c-bus{stroke:none}
@media (max-width:520px){ body{font-size:15.5px} .lede{font-size:17px} .figs b{font-size:22px} }
"""
