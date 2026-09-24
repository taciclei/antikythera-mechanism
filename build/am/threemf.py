"""Minimal 3MF writer/reader (zipfile + XML, unit millimeter) and closed-mesh check."""
import io
import xml.etree.ElementTree as ET
import zipfile

import numpy as np

NS = 'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'
CT = ('<?xml version="1.0" encoding="UTF-8"?>\n'
      '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
      '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
      '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>'
      '</Types>')
RELS = ('<?xml version="1.0" encoding="UTF-8"?>\n'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Target="/3D/3dmodel.model" Id="rel0" '
        'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')


def _esc(s):
    return (s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;'))


def write(path, objects, spacing=5.0, row_width=400.0):
    """objects: list of (name, V (N,3) mm, T (M,3) int). Items are laid out on a grid (build
    transforms); vertices stay in each part's local frame."""
    buf = io.StringIO()
    buf.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    buf.write('<model unit="millimeter" xml:lang="en-US" xmlns="%s">\n<resources>\n' % NS)
    items = []
    x = y = row_h = 0.0
    for k, (name, V, T) in enumerate(objects):
        oid = k + 1
        buf.write('<object id="%d" type="model" name="%s"><mesh><vertices>\n' % (oid, _esc(name)))
        buf.write(''.join('<vertex x="%.6f" y="%.6f" z="%.6f"/>\n' % tuple(v) for v in V))
        buf.write('</vertices><triangles>\n')
        buf.write(''.join('<triangle v1="%d" v2="%d" v3="%d"/>\n' % tuple(t) for t in T))
        buf.write('</triangles></mesh></object>\n')
        lo, hi = V.min(0), V.max(0)
        w, h = hi[0] - lo[0], hi[1] - lo[1]
        if x + w > row_width and x > 0:
            x, y, row_h = 0.0, y + row_h + spacing, 0.0
        tx, ty, tz = x - lo[0], y - lo[1], -lo[2]
        items.append('<item objectid="%d" transform="1 0 0 0 1 0 0 0 1 %.6f %.6f %.6f"/>' % (oid, tx, ty, tz))
        x += w + spacing
        row_h = max(row_h, h)
    buf.write('</resources>\n<build>\n%s\n</build>\n</model>\n' % '\n'.join(items))
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml', CT)
        z.writestr('_rels/.rels', RELS)
        z.writestr('3D/3dmodel.model', buf.getvalue())


def read(path):
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        assert '[Content_Types].xml' in names and '_rels/.rels' in names
        ET.fromstring(z.read('[Content_Types].xml'))
        ET.fromstring(z.read('_rels/.rels'))
        root = ET.fromstring(z.read('3D/3dmodel.model'))
    assert root.get('unit') == 'millimeter'
    out = []
    for ob in root.iter('{%s}object' % NS):
        vs = ob.find('{%s}mesh/{%s}vertices' % (NS, NS))
        ts = ob.find('{%s}mesh/{%s}triangles' % (NS, NS))
        V = np.array([[float(v.get('x')), float(v.get('y')), float(v.get('z'))] for v in vs])
        T = np.array([[int(t.get('v1')), int(t.get('v2')), int(t.get('v3'))] for t in ts], np.int64)
        out.append((ob.get('name'), V, T))
    return out, len(list(root.iter('{%s}item' % NS)))


def closed(T):
    """Every directed edge appears once and its reverse once (closed, consistently oriented)."""
    e = np.concatenate([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]])
    key = e[:, 0].astype(np.int64) * (int(T.max()) + 1) + e[:, 1]
    rkey = e[:, 1].astype(np.int64) * (int(T.max()) + 1) + e[:, 0]
    u, c = np.unique(key, return_counts=True)
    if c.max() > 1:
        return False
    return bool(np.isin(rkey, u).all())
