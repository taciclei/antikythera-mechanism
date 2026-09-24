import bpy, numpy as np
ctl = bpy.data.objects['AM_Controller']; vl = bpy.context.view_layer
names = ['Soleil', 'Lune', 'Mercure', 'Vénus', 'Mars', 'Jupiter', 'Saturne']
off = {n: [] for n in names}
for c in np.r_[0.0, np.random.default_rng(3).uniform(-30, 30, 19)]:
    ctl['crank'] = float(np.float32(c)); ctl.update_tag(); vl.update()
    for n in names:
        a = bpy.data.objects['ANCHOR_' + n].matrix_world.translation; l = bpy.data.objects['LABEL_' + n].matrix_world
        off[n].append((l.translation.x - a.x, l.translation.y - a.y, l.translation.z))
        assert abs(l.to_euler().z) < 1e-6, n
worst = max(float(np.ptp(np.array(v)[:, k])) for v in off.values() for k in range(3))
print('[labels] upright: yes; max variation of label-anchor offset over 20 cranks:', f'{worst:.2e} mm', 'OK' if worst < 1e-4 else 'FAIL')
print('[labels] autoexec off:', not bpy.context.preferences.filepaths.use_scripts_auto_execute)
