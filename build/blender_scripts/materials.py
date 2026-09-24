"""PBR materials: bronze with a patina mix driven by AM_Controller["patina"], wood, accents."""
import bpy


def _principled(mat):
    return next(n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')


def _output(mat):
    return next(n for n in mat.node_tree.nodes if n.type == 'OUTPUT_MATERIAL')


def patina_driver(socket_owner, ctl):
    fc = socket_owner.driver_add('default_value')
    fc.keyframe_points.clear()
    d = fc.driver
    d.type = 'SCRIPTED'
    v = d.variables.new()
    v.name = 'p'
    v.type = 'SINGLE_PROP'
    v.targets[0].id_type = 'OBJECT'
    v.targets[0].id = ctl
    v.targets[0].data_path = '["patina"]'
    d.expression = 'p'
    return fc


def bronze(spec, ctl, name='AM_bronze', tint=(1.0, 1.0, 1.0)):
    mb = spec['materials']['bronze']
    mp = spec['materials']['patina']
    mat = bpy.data.materials.new(name)
    nt = mat.node_tree
    N, Lk = nt.nodes, nt.links
    pb = _principled(mat)
    col = mb['base_color_linear']
    pb.inputs['Base Color'].default_value = (col[0] * tint[0], col[1] * tint[1], col[2] * tint[2], 1.0)
    pb.inputs['Metallic'].default_value = mb['metallic']
    pb.inputs['Roughness'].default_value = mb['roughness']
    pp = N.new('ShaderNodeBsdfPrincipled')
    pp.location = (0, -700)
    pp.inputs['Metallic'].default_value = mp['metallic']
    pp.inputs['Roughness'].default_value = mp['roughness']
    # patina colour: verdigris / cuprite through noise and a colour ramp
    tex = N.new('ShaderNodeTexCoord')
    tex.location = (-1400, -400)
    noise = N.new('ShaderNodeTexNoise')
    noise.location = (-1200, -400)
    noise.inputs['Scale'].default_value = 0.35
    noise.inputs['Detail'].default_value = 6.0
    Lk.new(tex.outputs['Object'], noise.inputs['Vector'])
    ramp = N.new('ShaderNodeValToRGB')
    ramp.location = (-950, -400)
    ramp.color_ramp.elements[0].color = (0.18, 0.42, 0.34, 1.0)
    ramp.color_ramp.elements[1].color = (0.22, 0.10, 0.06, 1.0)
    ramp.color_ramp.elements[0].position = 0.35
    ramp.color_ramp.elements[1].position = 0.7
    Lk.new(noise.outputs['Fac'], ramp.inputs['Fac'])
    Lk.new(ramp.outputs['Color'], pp.inputs['Base Color'])
    # mask = patina * (0.55 + 0.45 * noise) * (1.2 - 0.4 * AO)
    ao = N.new('ShaderNodeAmbientOcclusion')
    ao.location = (-1200, -800)
    ao.inputs['Distance'].default_value = 2.0
    val = N.new('ShaderNodeValue')
    val.name = val.label = 'patina'
    val.location = (-1200, 0)
    patina_driver(val.outputs[0], ctl)
    m1 = N.new('ShaderNodeMath')
    m1.operation = 'MULTIPLY_ADD'
    m1.location = (-950, -100)
    m1.inputs[1].default_value = 0.45
    m1.inputs[2].default_value = 0.55
    Lk.new(noise.outputs['Fac'], m1.inputs[0])
    m2 = N.new('ShaderNodeMath')
    m2.operation = 'MULTIPLY_ADD'
    m2.location = (-950, -800)
    m2.inputs[1].default_value = -0.4
    m2.inputs[2].default_value = 1.2
    Lk.new(ao.outputs['AO'], m2.inputs[0])
    m3 = N.new('ShaderNodeMath')
    m3.operation = 'MULTIPLY'
    m3.location = (-750, -300)
    Lk.new(m1.outputs[0], m3.inputs[0])
    Lk.new(m2.outputs[0], m3.inputs[1])
    m4 = N.new('ShaderNodeMath')
    m4.operation = 'MULTIPLY'
    m4.use_clamp = True
    m4.location = (-550, -200)
    Lk.new(val.outputs[0], m4.inputs[0])
    Lk.new(m3.outputs[0], m4.inputs[1])
    mix = N.new('ShaderNodeMixShader')
    mix.location = (300, -200)
    Lk.new(m4.outputs[0], mix.inputs['Fac'])
    Lk.new(pb.outputs['BSDF'], mix.inputs[1])
    Lk.new(pp.outputs['BSDF'], mix.inputs[2])
    out = _output(mat)
    out.location = (550, -200)
    Lk.new(mix.outputs['Shader'], out.inputs['Surface'])
    return mat


def simple(name, color, metallic=0.0, roughness=0.5):
    mat = bpy.data.materials.new(name)
    pb = _principled(mat)
    pb.inputs['Base Color'].default_value = tuple(color) + (1.0,)
    pb.inputs['Metallic'].default_value = metallic
    pb.inputs['Roughness'].default_value = roughness
    return mat


def wood(spec):
    w = spec['materials']['wood']
    mat = simple('AM_wood', w['base_color_linear'], 0.0, w['roughness'])
    nt = mat.node_tree
    pb = _principled(mat)
    wave = nt.nodes.new('ShaderNodeTexWave')
    wave.location = (-600, 200)
    wave.inputs['Scale'].default_value = 0.08
    wave.inputs['Distortion'].default_value = 6.0
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.location = (-350, 200)
    c = w['base_color_linear']
    ramp.color_ramp.elements[0].color = (c[0] * 0.7, c[1] * 0.7, c[2] * 0.7, 1.0)
    ramp.color_ramp.elements[1].color = (c[0] * 1.2, c[1] * 1.2, c[2] * 1.2, 1.0)
    nt.links.new(wave.outputs['Fac'], ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'], pb.inputs['Base Color'])
    return mat


def make_all(spec, ctl):
    return {
        'bronze': bronze(spec, ctl),
        'wood': wood(spec),
        'dark': simple('AM_phase_dark', (0.02, 0.02, 0.025), 0.0, 0.6),
        'silver': simple('AM_silver', (0.9, 0.9, 0.92), 1.0, 0.2),
        'gold': simple('AM_gold', (1.0, 0.76, 0.33), 1.0, 0.25),
        'stone': simple('AM_stone', (0.35, 0.33, 0.3), 0.0, 0.7),
        'text': simple('AM_engraving', (0.12, 0.08, 0.04), 0.3, 0.6),
    }
