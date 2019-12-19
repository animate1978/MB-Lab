# MB-Lab

# MB-Lab fork website : https://github.com/animate1978/MB-Lab

# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 3
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####



import bpy
import numpy as np
import os
import json as js
from copy import deepcopy as dc
from math import radians, degrees

from . import algorithms
from . import object_ops
from . import node_ops
from . import numpy_ops
from . import file_ops


# ------------------------------------------------------------------------
#    Functions
# ------------------------------------------------------------------------

def get_hair_data(fileName):
    data_dir = file_ops.get_data_path()
    hair_dir = os.path.join(data_dir, "Particle_Hair")
    fn = fileName + '_hair.json'
    fpath = os.path.join(hair_dir, fn)
    with open(fpath, 'r') as f:
        data = js.load(f)
    return data 

def js_face_sel(faces):
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    for i in faces:
        bpy.context.object.data.polygons[i].select = True

# ------------------------------------------------------------------------

def sel_faces(faces):
    bpy.ops.object.mode_set(mode='OBJECT')
    gbm = object_ops.get_body_mesh()
    gbm.select_set(state=True)
    js_face_sel(faces)
    bpy.ops.object.mode_set(mode='EDIT')

#Create the Copy Face Object
def add_scalp(Name):
    bpy.ops.object.mode_set(mode='OBJECT')
    gs = object_ops.get_sel()
    viw = object_ops.vg_idx_dict(gs)
    vid = object_ops.vidx_dict()
    hairObj = object_ops.obj_new(Name, gs[0], gs[1], "MB_LAB_Character")
    try:
        object_ops.copy_wt(Name, viw, vid)
    except:
        pass
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')
    bpy.ops.object.shade_smooth()

def hair_armature_mod(skeleton, hair_object):
    a_mod = hair_object.modifiers.new("armature_hair", 'ARMATURE')
    a_mod.object = skeleton
    a_mod.vertex_group = 'head'

#Add particle hair
def add_hair(hair_object, mat_name, style):
    scn = bpy.context.scene
    p_sys = hair_object.modifiers.new("hair", 'PARTICLE_SYSTEM').particle_system
    p_sys.settings.type = 'HAIR'
    p_sys.settings.child_type = 'INTERPOLATED'
    p_sys.settings.hair_length = 0.2
    p_sys.settings.root_radius = 0.03
    p_sys.settings.count = 1000
    p_sys.settings.hair_step = 5
    p_sys.settings.child_nbr = 20
    p_sys.settings.rendered_child_count = 20
    p_sys.settings.child_length = 0.895
    bpy.context.object.show_instancer_for_viewport = False
    bpy.context.object.show_instancer_for_render = False
    bpy.ops.particle.connect_hair(all=True)
    try:
        material = node_ops.get_material(mat_name)
        node_ops.clear_material(hair_object)
        node_ops.clear_node(material)
        material.use_nodes = True
        nodes = material.node_tree.nodes
        node_ops.clear_node(material)
    except:
        pass
    if scn.mblab_use_cycles:
        fileName = get_hair_npz("CY_shader_presets.npz")
        data = numpy_ops.get_data_value(style, fileName)
        output = add_HPshader_node(material, 'ShaderNodeOutputMaterial', (400,100))
        hair = add_HPshader_node(material, 'ShaderNodeBsdfHairPrincipled', (100,100))
        parametrization = data[0]
        hair.parametrization = parametrization #parametrization #['ABSORPTION', 'COLOR', 'MELANIN']
        if parametrization == 'COLOR': #Direct Coloring
            hair.inputs[0].default_value = data[1] #Color
        if parametrization == 'MELANIN': #Melanin Concetration
            hair.inputs[1].default_value = data[2] #Melanin
            hair.inputs[2].default_value = data[3] #Melanin Redness
            hair.inputs[3].default_value = data[4] #Tint
            hair.inputs[10].default_value = data[11] #Random Color
        if parametrization == 'ABSORPTION': #Absorbtion Coefficient    
            hair.inputs[4].default_value = data[5] #Absorbtion Coefficient
        hair.inputs[5].default_value = data[6] #Roughness
        hair.inputs[6].default_value = data[7] #Radial Roughness
        hair.inputs[7].default_value = data[8] #Coat
        hair.inputs[8].default_value = data[9] #IOR
        hair.inputs[9].default_value = data[10] #offset
        hair.inputs[11].default_value = data[12] #Random Roughness
        link = node_ops.add_node_link(material, hair.outputs[0], output.inputs[0])
        hair_object.active_material = material
        hair_object.scale = (0.95, 0.95, 0.95)

#Add Melanin Hair Principled Shader #CYCLES
def add_hairP_shader(mat_name, parametrization, v0, v1, v2, v3, v4, v5, v6, v7, v8, v9, v10, v11):
    material = node_ops.get_material(mat_name)
    node_ops.clear_material(bpy.context.object)
    node_ops.clear_node(material)
    material.use_nodes = True
    output = add_HPshader_node(material, 'ShaderNodeOutputMaterial', (400,100))
    hair = add_HPshader_node(material, 'ShaderNodeBsdfHairPrincipled', (100,100))
    hair.parametrization = parametrization #['ABSORPTION', 'COLOR', 'MELANIN']
    if parametrization == 'COLOR': #Direct Coloring
        hair.inputs[0].default_value = v0 #Color
    if parametrization == 'MELANIN': #Melanin Concetration
        hair.inputs[1].default_value = v1 #Melanin
        hair.inputs[2].default_value = v2 #Melanin Redness
        hair.inputs[3].default_value = v3 #Tint
        hair.inputs[10].default_value = v10 #Random Color
    if parametrization == 'ABSORPTION': #    
        hair.inputs[4].default_value = v4 #Absorbtion Coefficient
    hair.inputs[5].default_value = v5 #Roughness
    hair.inputs[6].default_value = v6 #Radial Roughness
    hair.inputs[7].default_value = v7 #Coat
    hair.inputs[8].default_value = v8 #IOR
    hair.inputs[9].default_value = v9 #offset
    hair.inputs[11].default_value = v11 #Random Roughness
    link = node_ops.add_node_link(material, hair.outputs[0], output.inputs[0])
    bpy.context.object.active_material = material

def change_hair_shader(style):
    context = bpy.context
    fileName = get_hair_npz("CY_shader_presets.npz")
    if context.scene.mblab_use_cycles:
        mat_name = context.object.name
        data = numpy_ops.get_data_value(style, fileName)
        add_hairP_shader(mat_name, data[0], data[1], data[2], data[3], data[4], data[5], data[6], data[7], data[8], data[9], data[10], data[11], data[12])
    if context.scene.mblab_use_eevee:
        pass

# Get Principled Hair shader settings
def get_p_hair_settings(object):
    material = object.active_material
    nodes = material.node_tree.nodes
    hair = nodes.get("Principled Hair BSDF")
    par = hair.parametrization
    v6 = hair.inputs[5].default_value
    v7 = hair.inputs[6].default_value
    v8 = hair.inputs[7].default_value
    v9 = hair.inputs[8].default_value
    v10 = hair.inputs[9].default_value
    v12 = hair.inputs[11].default_value
    if par == 'COLOR':
        v1 = hair.inputs[0].default_value[:]
        v2 = None
        v3 = None
        v4 = None
        v5 = None
        v11 = None
    elif par == 'MELANIN':
        v1 = None
        v2 = hair.inputs[1].default_value
        v3 = hair.inputs[2].default_value
        v4 = hair.inputs[3].default_value[:]
        v5 = None
        v11 = hair.inputs[10].default_value
    elif par == 'ABSORPTION':
        v1 = None
        v2 = None
        v3 = None
        v4 = None
        v5 = hair.inputs[4].default_value
        v11 = None
    return[par, v1, v2, v3, v4, v5, v6, v7, v8, v9, v10, v11, v12]

def add_pHair(hair_object):
    scn = bpy.context.scene
    p_sys = hair_object.modifiers.new("hair", 'PARTICLE_SYSTEM').particle_system
    p_sys.settings.type = 'HAIR'
    p_sys.settings.child_type = 'INTERPOLATED'
    p_sys.settings.hair_length = 0.2
    p_sys.settings.root_radius = 0.03
    p_sys.settings.count = 1000
    p_sys.settings.hair_step = 5
    p_sys.settings.child_nbr = 20
    p_sys.settings.rendered_child_count = 20
    p_sys.settings.child_length = 0.895
    bpy.context.scene.render.hair_type = 'STRIP'
    bpy.context.object.show_instancer_for_viewport = False
    bpy.context.object.show_instancer_for_render = False
    bpy.ops.particle.connect_hair(all=True)

# ------------------------------------------------------------------------

def add_HPshader_node(material, node_type, location):
    nodes = material.node_tree.nodes
    new_node = nodes.new(type=node_type)
    new_node.location = location
    return new_node

# ------------------------------------------------------------------------

#Get Partile Coodinates
def get_hair_particle(object):
    # Dependancy Graph
    dp = bpy.context.evaluated_depsgraph_get()
    # Particle System
    ps = object.evaluated_get(dp).particle_systems
    # Particles
    p = ps[0].particles
    # Count
    count_p = len(p)
    # Cooordinates
    p_dict = {}
    for i, c in [c for c in enumerate(p)]:
        h_keys = []
        hk = p[i].hair_keys
        count_hk = len(hk)
        for pt in hk:
            h_keys.append(pt.co)
        p_dict.update({i: h_keys})
    return p_dict

# ------------------------------------------------------------------------

def get_hair_dir():
    data_dir = file_ops.get_data_path()
    hair_dir = os.path.join(data_dir, "Hair_Data")
    return hair_dir

def get_hair_npz(fileName):
    hair_dir = get_hair_dir()
    return os.path.join(hair_dir, fileName)
    
# def get_hair_data(Name):
#     File = get_hair_npz("scalps.npz")
#     with np.load(File) as data:
#         return data[Name].tolist()

# ------------------------------------------------------------------------

def add_hair_data(object, style, fileName):
    fileName = get_hair_npz("CY_shader_presets.npz")
    Value = get_p_hair_settings(object)
    numpy_ops.add_array(style, Value, fileName)

def delete_hair_data(style, fileName, List):
    fileName = get_hair_npz("CY_shader_presets.npz")
    numpy_ops.remove_array(style, fileName, List)

def replace_hair_data(fileName, List):
    fileName = get_hair_npz("CY_shader_presets.npz")
    rl = List[-1]
    style, Value = rl
    List.remove(rl)
    numpy_ops.add_array(style, Value, fileName)

# def export_hair_data(filePath, style):
#     File = ext + style + '.npz'
#     fp = node_ops.get_filename(filePath, File)
#     fileName = get_hair_npz("CY_shader_presets.npz")
#     with np.load(fileName) as data:
#     Value = get_p_hair_settings(bpy.context.object)
#     data = [style, Value]
#     np.savez(fp, *data)

# def import_hair_data(mport):
#     fileName = get_hair_npz("CY_shader_presets.npz")
#     fp = os.path.split(mport)[1]
#     if fp.startswith("CY_Hshader_"):
#         with np.load(mport, 'r+') as imdata:
#             style, Value = imdata
#     numpy_ops.add_array(style, Value, fileName)

