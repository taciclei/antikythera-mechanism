"""AM_Controller, body drivers (simple expressions only), spiral slider lookup tables, crank action."""
import bpy
from bpy_extras import anim_utils


class DriverError(Exception):
    pass


def controller(coll):
    ctl = bpy.data.objects.new('AM_Controller', None)
    coll.objects.link(ctl)
    ctl.empty_display_type = 'SPHERE'
    ctl.empty_display_size = 5.0
    ctl.location = (0.0, 175.0, 0.0)
    ctl['crank'] = 0.0
    ctl['patina'] = 0.0
    if type(ctl['crank']) is not float or type(ctl['patina']) is not float:
        raise DriverError('crank/patina must be float properties')
    ctl.id_properties_ui('crank').update(description='Crank position in years (1 year = 1 turn of b1)',
                                         soft_min=-100.0, soft_max=100.0)
    ctl.id_properties_ui('patina').update(min=0.0, max=1.0, description='0 = new bronze, 1 = museum')
    return ctl


def add_driver(ob, path, index, expr, variables, keep_keys=False):
    fc = ob.driver_add(path, index)
    if not keep_keys:
        fc.keyframe_points.clear()
    d = fc.driver
    d.type = 'SCRIPTED'
    d.use_self = False
    for name, (objname, dp) in variables.items():
        v = d.variables.new()
        v.name = name
        v.type = 'SINGLE_PROP'
        t = v.targets[0]
        t.id_type = 'OBJECT'
        t.id = bpy.data.objects[objname]
        t.data_path = dp
    d.expression = expr
    if d.expression != expr:
        raise DriverError('expression truncated on %s: %r' % (ob.name, d.expression))
    return fc


def body_drivers(exprs):
    fcs = {}
    for body, e in exprs.items():
        ob = bpy.data.objects['B_' + body]
        fcs[body] = add_driver(ob, 'rotation_euler', e['index'], e['expr'], e['vars'])
    return fcs


def slider_driver(ob, s):
    fc = add_driver(ob, 'location', 1, s['expr'], s['vars'])
    psi, rho = s['psi'], s['rho']
    kp = fc.keyframe_points
    kp.clear()
    kp.add(len(psi))
    co = []
    for x, y in zip(psi, rho):
        co += [x, y]
    kp.foreach_set('co', co)
    for k in kp:
        k.interpolation = 'LINEAR'
    fc.extrapolation = 'CONSTANT'
    fc.update()
    return fc


def crank_action(ctl, scene, years=4.0, frames=480):
    ctl['crank'] = 0.0
    ctl.keyframe_insert('["crank"]', frame=1)
    ctl['crank'] = float(years)
    ctl.keyframe_insert('["crank"]', frame=frames + 1)
    ad = ctl.animation_data
    ad.action.name = 'AM_crank'
    cb = anim_utils.action_get_channelbag_for_slot(ad.action, ad.action_slot)
    for fc in cb.fcurves:
        fc.extrapolation = 'LINEAR'
        for k in fc.keyframe_points:
            k.interpolation = 'LINEAR'
        fc.update()
    ctl['crank'] = 0.0
    scene.frame_start = 1
    scene.frame_end = frames
    scene.render.fps = 24
    scene.frame_set(1)
    return cb
