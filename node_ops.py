import bpy
import os
import numpy as np
from numpy import array


def get_filename(filePath, File):
    FP = os.path.join(filePath, File)
    return FP

def get_universal_dict(filename):
    with np.load(filename, 'r+', allow_pickle=True) as data:
        d = dict(data)
    return d

def get_universal_list(filename):
    with np.load(filename, 'r', allow_pickle=True) as data:
        l = list(data.files)
    return l

def get_universal_presets(filename, style):
    with np.load(filename, 'r', allow_pickle=True) as data:
        d = data[style]
    return d

def set_universal_shader(mat_name, filename, style):
    material = get_material(mat_name)
    nodes = material.node_tree.nodes
    ds = get_universal_presets(filename, style)
    args = [tuple(np.array(i).tolist()) for i in ds]
    for arg in args:
        id = nodes[arg[0]].bl_idname
        fd = func_dict(shader_set_dict(), id)
        data = args[args.index(arg)]
        fd(*data)

def save_universal_presets(filename, style, Value):
    with np.load(filename, 'r+', allow_pickle=True) as data:
        d = dict(data)
        td = {style: Value}
        d.update(**td)
        np.savez(filename, **d)

def remove_universal_presets(filename, style, List):
    with np.load(filename, 'r+', allow_pickle=True) as data:
        d = dict(data)
        rs = [style, d[style]]
        List.append(rs)
        d.pop(style)
        np.savez(filename, **d)

def replace_removed_shader(filename, List):
    if not List:
        pass
    with np.load(filename, 'r+', allow_pickle=True) as data:
        d = dict(data)
        rl = List[-1]
        List.remove(rl)
        td = {rl[0]: rl[1]}
        d.update(**td)
        np.savez(filename, **d)

def export_universal_presets(filePath, ext, style, Value): #'UN_Hair_'
    File = ext + style + '.npz'
    fp = get_filename(filePath, File)
    d = {style: Value}
    np.savez(fp, **d)


def import_universal_presets(filename, mport):
    fp = os.path.split(mport)[1]
    if fp.startswith('UN_Hshader_'):
        with np.load(filename, 'r+') as data:
            d = dict(data)
        with np.load(mport, 'r+') as imdata:
            imd = dict(imdata)
            d.update(imd)
        np.savez(filename, **d)
    else:
        pass

#######################################################################

def get_material(mat_name):
    mat = (bpy.data.materials.get(mat_name) or 
       bpy.data.materials.new(mat_name))
    return mat

def clear_material(object):
    object.data.materials.clear()
    
def clear_node(material):
    if material.node_tree:
        material.node_tree.links.clear()
        material.node_tree.nodes.clear()

def add_shader_node(material, node_type, Label, Name, location):
    nodes = material.node_tree.nodes
    new_node = nodes.new(type=node_type)
    new_node.label = Label
    new_node.name = Name
    new_node.location = location
    return new_node

def add_node_link(material, link1, link2):
    links = material.node_tree.links
    link = links.new(link1, link2)
    return link

def shader_prep(material):
    clear_material(bpy.context.object)
    clear_node(material)
    material.use_nodes = True
    clear_node(material)
    
#######################################################################
# Node Ops

def node_info(nodes):
    return [[i.bl_idname, i.bl_label, i.label, i.name, i.location] for i in nodes[:]]


def set_links(material, nlink):
    for i in nlink:
        add_node_link(material, i[0], i[1])


#######################################################################

def shader_get_dict():
    shader_ = { 
                'ShaderNodeMixRGB': get_mix_shader, 
                'ShaderNodeValToRGB': get_colorramp_shader, 
                'ShaderNodeBsdfDiffuse': get_bsdf_diffuse_shader, 
                'ShaderNodeBsdfGlossy': get_bsdf_glossy_shader,
                'ShaderNodeBsdfHairPrincipled': get_hairP_shader,
                'ShaderNodeTexImage': get_image_shader,
            }
    return shader_

def shader_set_dict():
    shader_ = { 
                'ShaderNodeMixRGB': set_mix_shader, 
                'ShaderNodeValToRGB': set_colorramp_shader,
                'ShaderNodeBsdfDiffuse': set_bsdf_diffuse_shader, 
                'ShaderNodeBsdfGlossy': set_bsdf_glossy_shader,
                'ShaderNodeBsdfHairPrincipled': set_hairP_shader,
                'ShaderNodeTexImage': set_image_shader,
            }
    return shader_

#######################################################################

def func_dict(Dict, Key):
    return Dict.get(Key, lambda: 'Invalid')


def get_all_shader_(nodes):
    info = node_info(nodes)
    setting = []
    for i in info:
        if i[0] in shader_get_dict():
            fd = func_dict(shader_get_dict(), i[0])
            setting.append(fd(nodes, i[3]))
    return setting

####################################################################### 
# Add Universal Hair Shaders

def universal_hair_setup():
    return [['ShaderNodeMixRGB', 'Mix', 'Gradient_Color', 'Gradient_Color', (-100, 280)], 
    ['ShaderNodeMixRGB', 'Mix', 'Tip_Color', 'Tip_Color', (150, 280)], 
    ['ShaderNodeMixRGB', 'Mix', 'Main_Color', 'Main_Color', (-325, 280)], 
    ['ShaderNodeHairInfo', 'Hair Info', 'Hair Info', 'Hair Info', (-890, 260)], 
    ['ShaderNodeAddShader', 'Add Shader', 'Highlight_Mix', 'Highlight_Mix', (680, 250)], 
    ['ShaderNodeBsdfDiffuse', 'Diffuse BSDF', 'Main_Diffuse', 'Main_Diffuse', (390, 240)], 
    ['ShaderNodeAddShader', 'Add Shader', 'Highlight_Mix_2', 'Highlight_Mix_2', (890, 260)], 
    ['ShaderNodeValToRGB', 'ColorRamp', 'Gradient_Control', 'Gradient_Control', (-660, 280)], 
    ['ShaderNodeValToRGB', 'ColorRamp', 'Main_Contrast', 'Main_Contrast', (-660, -5)], 
    ['ShaderNodeValToRGB', 'ColorRamp', 'Tip_Control', 'Tip_Control', (-660, 555)], 
    ['ShaderNodeBsdfGlossy', 'Glossy BSDF', 'Main_Highlight', 'Main_Highlight', (440, 80)], 
    ['ShaderNodeBsdfGlossy', 'Glossy BSDF', 'Secondary_Highlight', 'Secondary_Highlight', (680, 80)]]

def universal_hair_links(nodes):
    return [[nodes['Gradient_Color'].outputs[0], nodes['Tip_Color'].inputs[1]], 
            [nodes['Tip_Color'].outputs[0], nodes['Main_Diffuse'].inputs[0]], 
            [nodes['Main_Color'].outputs[0], nodes['Gradient_Color'].inputs[1]], 
            [nodes['Hair Info'].outputs[1], nodes['Gradient_Control'].inputs[0]], 
            [nodes['Hair Info'].outputs[1], nodes['Tip_Control'].inputs[0]], 
            [nodes['Hair Info'].outputs[4], nodes['Main_Contrast'].inputs[0]], 
            [nodes['Highlight_Mix'].outputs[0], nodes['Highlight_Mix_2'].inputs[0]], 
            [nodes['Main_Diffuse'].outputs[0], nodes['Highlight_Mix'].inputs[0]], 
            [nodes['Highlight_Mix_2'].outputs[0], nodes['Material Output'].inputs[0]], 
            [nodes['Gradient_Control'].outputs[0], nodes['Gradient_Color'].inputs[0]],
            [nodes['Main_Contrast'].outputs[0], nodes['Main_Color'].inputs[0]], 
            [nodes['Tip_Control'].outputs[0], nodes['Tip_Color'].inputs[0]], 
            [nodes['Main_Highlight'].outputs[0], nodes['Highlight_Mix'].inputs[1]], 
            [nodes['Secondary_Highlight'].outputs[0], nodes['Highlight_Mix_2'].inputs[1]],
            [nodes['Highlight_Mix_2'].outputs[0], nodes['Material Output'].inputs[0]],
            ]

#######################################################################

def create_shader(material, id, Label, Name, location):
    shader_prep(material)
    clear_node(material)
    add_shader_node(material, id, Label, Name, location)
    bpy.context.object.active_material = material
    
def universal_shader_nodes(mat_name, data, out_loc):
    material = get_material(mat_name)
    shader_prep(material)
    output = add_shader_node(material, 'ShaderNodeOutputMaterial', 'Material Output', 'Material Output', out_loc)
    bpy.context.object.active_material = material
    nodes = material.node_tree.nodes
    for i in data:
        add_shader_node(material, i[0], i[2], i[3], i[4])
    set_links(material, universal_hair_links(nodes))

def hairP_shader_nodes(mat_name):
    material = get_material(mat_name)
    shader_prep(material)
    output = add_shader_node(material, 'ShaderNodeOutputMaterial', 'Material Output', 'Material Output', (400,100))
    hair = add_shader_node(material, 'ShaderNodeBsdfHairPrincipled', 'Hair_Shader', 'Hair_Shader', (100,100))
    link = add_node_link(material, hair.outputs[0], output.inputs[0])
    bpy.context.object.active_material = material
    

#######################################################################
# Hair Principled Shader

def get_hairP_shader(nodes, node_name):
    node = nodes.get(node_name)
    par = node.parametrization
    v5 = node.inputs[5].default_value
    v6 = node.inputs[6].default_value
    v7 = node.inputs[7].default_value
    v8 = node.inputs[8].default_value
    v9 = node.inputs[9].default_value
    v11 = node.inputs[11].default_value
    if par == 'COLOR':
        v0 = node.inputs[0].default_value[:]
        v1 = None
        v2 = None
        v3 = None
        v4 = None
        v10 = None
    elif par == 'MELANIN':
        v0 = None
        v1 = node.inputs[1].default_value
        v2 = node.inputs[2].default_value
        v3 = node.inputs[3].default_value[:]
        v4 = None
        v10 = node.inputs[10].default_value
    elif par == 'ABSORPTION':
        v0 = None
        v1 = None
        v2 = None
        v3 = None
        v4 = node.inputs[4].default_value
        v10 = None
    return np.array([node_name, par, v0, v1, v2, v3, v4, v5, v6, v7, v8, v9, v10, v11], dtype=object)


def set_hairP_shader(node_name, parametrization, v0, v1, v2, v3, v4, v5, v6, v7, v8, v9, v10, v11):
    material = bpy.context.object.active_material
    nodes = material.node_tree.nodes
    node = nodes.get(node_name)
    node.parametrization = parametrization #['ABSORPTION', 'COLOR', 'MELANIN']
    if parametrization is 'COLOR': #Direct Coloring
        node.inputs[0].default_value = v0 #Color
    if parametrization is 'MELANIN': #Melanin Concetration
        node.inputs[1].default_value = v1 #Melanin
        node.inputs[2].default_value = v2 #Melanin Redness
        node.inputs[3].default_value = v3 #Tint
        node.inputs[10].default_value = v10 #Random Color
    if parametrization is 'ABSORPTION': #    
        node.inputs[4].default_value = v4 #Absorbtion Coefficient
    node.inputs[5].default_value = v5 #Roughness
    node.inputs[6].default_value = v6 #Radial Roughness
    node.inputs[7].default_value = v7 #Coat
    node.inputs[8].default_value = v8 #IOR
    node.inputs[9].default_value = v9 #offset
    node.inputs[11].default_value = v11 #Random Roughness

#######################################################################
# Color Ramp Shader

def get_colorramp_shader(nodes, node_name):
    node = nodes.get(node_name)
    pos1 = node.color_ramp.elements[0].position
    col1 = node.color_ramp.elements[0].color[:]
    pos2 = node.color_ramp.elements[1].position
    col2 = node.color_ramp.elements[1].color[:]
    return np.array([node_name, pos1, col1, pos2, col2], dtype=object)

# def get_colorramp_shader(nodes, node_name):
#     node = nodes.get(node_name)
#     elem = node.color_ramp.elements
#     p_c = np.array([[elem[i[0]].position, elem[i[0]].color[:]] for i in enumerate(elem)], dtype=object)
#     return np.array([node_name, p_c], dtype=object)


def set_colorramp_shader(node_name, pos1, col1, pos2, col2):
    material = bpy.context.object.active_material
    nodes = material.node_tree.nodes
    node = nodes.get(node_name)
    node.color_ramp.elements[0].position = pos1
    node.color_ramp.elements[0].color[:] = col1
    node.color_ramp.elements[1].position = pos2
    node.color_ramp.elements[1].color[:] = col2

# def set_colorramp_shader(node_name, p_c):
#     material = bpy.context.object.active_material
#     nodes = material.node_tree.nodes
#     node = nodes.get(node_name)
#     elem = node.color_ramp.elements
#     for i in enumerate(p_c):
#         elem[i[0]].position = i[1][0]
#         elem[i[0]].color[:] = i[1][1]

#######################################################################
# Mix Shader

def get_mix_shader(nodes, node_name):
    node = nodes.get(node_name)
    blend = node.blend_type
    clamp = node.use_clamp
    fac = node.inputs[0].default_value
    col1 = node.inputs[1].default_value[:]
    col2 = node.inputs[2].default_value[:]
    return np.array([node_name, blend, clamp, fac, col1, col2], dtype=object)

def set_mix_shader(node_name, blend, clamp, fac, col1, col2):
    material = bpy.context.object.active_material
    nodes = material.node_tree.nodes
    node = nodes.get(node_name)
    node.blend_type = blend
    node.use_clamp = clamp
    node.inputs[0].default_value = fac
    node.inputs[1].default_value = col1
    node.inputs[2].default_value = col2
    
#######################################################################    
# BSDF Diffuse

def get_bsdf_diffuse_shader(nodes, node_name):
    node = nodes.get(node_name)
    col = node.inputs[0].default_value[:]
    rough = node.inputs[1].default_value
    norm = node.inputs[2].default_value[:]
    return np.array([node_name, col, rough, norm], dtype=object)
    
def set_bsdf_diffuse_shader(node_name, col, rough, norm):
    material = bpy.context.object.active_material
    nodes = material.node_tree.nodes
    node = nodes.get(node_name)
    node.inputs[0].default_value = col
    node.inputs[1].default_value = rough
    node.inputs[2].default_value = norm

#######################################################################    
# BSDF Glossy

def get_bsdf_glossy_shader(nodes, node_name):
    node = nodes.get(node_name)
    distribution = node.distribution
    col = node.inputs[0].default_value[:]
    rough = node.inputs[1].default_value
    norm = node.inputs[2].default_value[:]
    return np.array([node_name, distribution, col, rough, norm], dtype=object)

def set_bsdf_glossy_shader(node_name, distribution, col, rough, norm):
    material = bpy.context.object.active_material
    nodes = material.node_tree.nodes
    node = nodes.get(node_name)
    node.distribution = distribution
    node.inputs[0].default_value = col
    node.inputs[1].default_value = rough
    node.inputs[2].default_value = norm

#######################################################################    
# Add ShaderImage Texture

def get_image_shader(nodes, node_name):
    node = nodes.get(node_name)
    texture = node.image
    col = node.color
    ext = node.extension
    bc = node.color_mapping.blend_color
    bf = node.color_mapping.blend_factor
    bt = node.color_mapping.blend_type
    bright = node.color_mapping.brightness
    contrast = node.color_mapping.contrast
    saturation = node.color_mapping.saturation
    ucr = node.color_mapping.use_color_ramp
    cm1 = node.color_mapping.color_ramp.color_mode
    alpha1 = node.color_mapping.color_ramp.elements[0].alpha
    col1 = node.color_mapping.color_ramp.elements[0].color[:]
    cpos1 = node.color_mapping.color_ramp.elements[0].position
    cm2 = node.color_mapping.color_ramp.color_mode
    alpha2 = node.color_mapping.color_ramp.elements[1].alpha
    col2 = node.color_mapping.color_ramp.elements[1].color[:]
    cpos2 = node.color_mapping.color_ramp.elements[1].position
    h_int = node.color_mapping.color_ramp.hue_interpolation
    intp = node.color_mapping.color_ramp.interpolation
    fs = node.image_user.frame_start
    fc = node.image_user.frame_current
    fd = node.image_user.frame_duration
    fo = node.image_user.frame_offset
    ml = node.image_user.multilayer_layer
    mp = node.image_user.multilayer_pass
    mv = node.image_user.multilayer_view
    uaf = node.image_user.use_auto_refresh
    ucy = node.image_user.use_cyclic
    return np.array([node_name, texture, col, ext, bc, bf, bt, bright, contrast, saturation, ucr, cm1, alpha1, col1, cpos1, cm2, alpha2, col2, cpos2, h_int, intp, fs, fc, fd, fo, ml, mp, mv, uaf, ucy], dtype=object)

def set_image_shader(node_name, texture, col, ext, bc, bf, bt, bright, contrast, saturation, ucr, cm1, alpha1, col1, cpos1, cm2, alpha2, col2, cpos2, h_int, intp, fs, fc, fd, fo, ml, mp, mv, uaf, ucy):
    material = bpy.context.object.active_material
    nodes = material.node_tree.nodes
    node = nodes.get(node_name)
    node.image = texture
    node.extension = ext
    node.color_mapping.blend_color = bc
    node.color_mapping.blend_factor = bf
    node.color_mapping.blend_type = bt
    node.color_mapping.brightness = bright
    node.color_mapping.contrast = contrast
    node.color_mapping.saturation = saturation
    node.color_mapping.use_color_ramp = ucr
    node.color_mapping.color_ramp.color_mode = cm1
    node.color_mapping.color_ramp.elements[0].alpha = alpha1
    node.color_mapping.color_ramp.elements[0].color[:] = col1
    node.color_mapping.color_ramp.elements[0].position = cpos1
    node.color_mapping.color_ramp.color_mode = cm2
    node.color_mapping.color_ramp.elements[1].alpha = alpha2
    node.color_mapping.color_ramp.elements[1].color[:] = col2
    node.color_mapping.color_ramp.elements[1].position = cpos2
    node.color_mapping.color_ramp.hue_interpolation = h_int
    node.color_mapping.color_ramp.interpolation = intp
    node.image_user.frame_start = fs
    node.image_user.frame_current = fc
    node.image_user.frame_duration = fd
    node.image_user.frame_offset = fo
    node.image_user.multilayer_layer = ml
    node.image_user.multilayer_pass = mp
    node.image_user.multilayer_view = mv
    node.image_user.use_auto_refresh = uaf
    node.image_user.use_cyclic = ucy


#######################################################################


