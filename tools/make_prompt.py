"""Fill tools/prompt_template.md with the spec -> PROMPT_OPUS.md (single self-contained prompt)."""
import json, hashlib, math
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
spec = json.loads((ROOT / 'spec' / 'antikythera.json').read_text())
def canon(x): return json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
sha = hashlib.sha256(canon(spec).encode()).hexdigest()
sec = "\n".join(f"- `{k}` : `{hashlib.sha256(canon(v).encode()).hexdigest()[:16]}`" for k, v in spec.items())

# readable-but-compact JSON: one top-level key per line block, list items one per line
def dump(obj):
    lines = ["{"]
    keys = list(obj)
    for n, k in enumerate(keys):
        v = obj[k]; comma = "," if n < len(keys) - 1 else ""
        if isinstance(v, list) and v and isinstance(v[0], dict):
            lines.append(f' {json.dumps(k)}:[')
            for j, it in enumerate(v):
                lines.append("  " + json.dumps(it, ensure_ascii=False, separators=(',', ':')) + ("," if j < len(v) - 1 else ""))
            lines.append(" ]" + comma)
        elif isinstance(v, dict) and len(json.dumps(v)) > 900:
            lines.append(f' {json.dumps(k)}:{{')
            sk = list(v)
            for j, kk in enumerate(sk):
                lines.append(f"  {json.dumps(kk)}:" + json.dumps(v[kk], ensure_ascii=False, separators=(',', ':')) + ("," if j < len(sk) - 1 else ""))
            lines.append(" }" + comma)
        else:
            lines.append(f" {json.dumps(k)}:" + json.dumps(v, ensure_ascii=False, separators=(',', ':')) + comma)
    lines.append("}")
    return "\n".join(lines)
text = dump(spec)
assert json.loads(text) == spec, "formatted JSON must round-trip exactly"

B = {b['id']: b for b in spec['bodies']}
PS = {p['slot_gear']: p for p in spec['pin_slots']}
FO = {f['body']: f for f in spec['followers']}
def fr(s): return s if s else "—"
def pos(b):
    p = b['axis_xy_in_parent']
    return "—" if p is None else f"({p[0]:.4f}, {p[1]:.4f})"
special = {
 'frame': "fixe",
 'a': "autour de +x : −2π·(223/48)·t",
 'q': "autour de son X local (radial), relatif à `moon` : θ_q = θ_b − θ_moon (NON LINÉAIRE ; moyenne +235/19)",
 'kp': "tenon-rainure : θ = θ_k + atan2(1.1·sin(θ_k − β), 9.6 − 1.1·cos(θ_k − β)), β = −38°",
 'e_inner': "monde : θ = θ_e_table − θ_kp (θ_kp local à e_table)",
 'moon': "monde : θ = −θ_e_inner",
}
for slot_body, pinb, outb in (('x_sa86s', 'x_sa68', 't_saturn'), ('x_ju65s', 'x_ju43', 't_jupiter'), ('x_ma80s', 'x_ma71', 't_mars')):
    p = next(ps for ps in spec['pin_slots'] if ps['slot_gear'] in B[slot_body]['gears'])
    special[slot_body] = f"tenon-rainure : θ = θ_{pinb} + atan2({p['offset']}·sin(θ_{pinb} − β), {p['pin_radius']} − {p['offset']}·cos(θ_{pinb} − β)), β = {p['offset_dir_local_deg']:g}° (local à b)"
    special[outb] = f"monde : θ = θ_b − θ_{slot_body} (θ_{slot_body} local à b)"
for f in spec['followers']:
    g0 = math.degrees(math.atan2(f['epicycle_axis_xy_in_b'][1], f['epicycle_axis_xy_in_b'][0]))
    ph = f" + {f['pin_phase_deg']:g}°" if f['pin_phase_deg'] else ""
    special[f['body']] = f"suiveur : θ = θ_b + γ0 + atan2(d·sin λ, i + d·cos λ), λ = θ_{f['epicycle_body']}{ph} − γ0 ; i = {f['i']:.4f}, d = {f['pin_d']:.4f}, γ0 = {g0:.4f}°"
rows = ["| corps | parent | axe (repère du parent, mm) | roues | taux moyen absolu | angle θ(t) |", "|---|---|---|---|---|---|"]
for b in spec['bodies']:
    ang = special.get(b['id'], f"−2π·({b['rate_rel_parent_mean']})·t" + (" (local)" if b['parent'] not in (None, 'frame') else ""))
    rows.append(f"| `{b['id']}` | {b['parent'] or '—'} | {pos(b)} | {', '.join(b['gears']) or '—'} | {fr(b['rate_abs_mean'])} | {ang} |")
table = "\n".join(rows)
tpl = (ROOT / 'tools' / 'prompt_template.md').read_text()
for k, v in {"{{SHA}}": sha, "{{SECTION_HASHES}}": sec, "{{SPEC_JSON}}": text, "{{BODY_TABLE}}": table}.items():
    assert k in tpl, k
    tpl = tpl.replace(k, v)
(ROOT / 'PROMPT_OPUS.md').write_text(tpl)
print("PROMPT_OPUS.md written:", len(tpl.encode()), "bytes; sha", sha)
