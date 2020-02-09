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
#
# Written by Noizirom


import bpy
import numpy as np
import os
import json as js
from copy import deepcopy as dc
from mathutils import Matrix, Vector, kdtree
import logging

from . import file_ops
from . import object_ops
from . import node_ops
from . import numpy_ops

logger = logging.getLogger(__name__)

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
    object_ops.obj_new(Name, gs[0], gs[1], "MB_LAB_Character")
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
def add_hair(hair_object):
    p_sys = hair_object.modifiers.new("hair", 'PARTICLE_SYSTEM').particle_system
    p_sys.settings.type = 'HAIR'
    p_sys.settings.hair_length = 0.1
    p_sys.settings.child_type = 'INTERPOLATED'
    bpy.context.object.show_instancer_for_viewport = False
    bpy.ops.particle.connect_hair(all=True)

# ------------------------------------------------------------------------
#    Hair Engine
# ------------------------------------------------------------------------
class HairEngine:
    '''
    '''
    def __init__(self, object):
        self.object = object
        self.armature = self.object.parent
        self.hair = "Hair"
        self.hair_card = "Hair_Card"
        self.hair_mesh = "Hair_Object"
        self.view_hide = self.object.hide_viewport
        self.render_hide = self.object.hide_render
        self.material = node_ops.get_material(self.hair)
        self.hc_mat = node_ops.get_material(self.hair_card)
        self.def_image = lambda hair_dir: bpy.data.images.load(os.path.join(hair_dir, "Sample_01.png"), check_existing=True)
        self.def_disp = lambda hair_dir: bpy.data.images.load(os.path.join(hair_dir, "DisplacementMap_01.png"), check_existing=True)
        self.universal_hair_setup = [['ShaderNodeOutputMaterial', 'Material Output', 'Material Output', 'Material Output', (1150, 250)],
            ['ShaderNodeMixRGB', 'Mix', 'Gradient_Color', 'Gradient_Color', (-100, 280)], 
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
        self.universal_hair_links = [['nodes["Gradient_Color"].outputs[0]', 'nodes["Tip_Color"].inputs[1]'], 
            ['nodes["Tip_Color"].outputs[0]', 'nodes["Main_Diffuse"].inputs[0]'], 
            ['nodes["Main_Color"].outputs[0]', 'nodes["Gradient_Color"].inputs[1]'], 
            ['nodes["Hair Info"].outputs[1]', 'nodes["Gradient_Control"].inputs[0]'], 
            ['nodes["Hair Info"].outputs[1]', 'nodes["Tip_Control"].inputs[0]'], 
            ['nodes["Hair Info"].outputs[4]', 'nodes["Main_Contrast"].inputs[0]'], 
            ['nodes["Highlight_Mix"].outputs[0]', 'nodes["Highlight_Mix_2"].inputs[0]'], 
            ['nodes["Main_Diffuse"].outputs[0]', 'nodes["Highlight_Mix"].inputs[0]'], 
            ['nodes["Highlight_Mix_2"].outputs[0]', 'nodes["Material Output"].inputs[0]'], 
            ['nodes["Gradient_Control"].outputs[0]', 'nodes["Gradient_Color"].inputs[0]'],
            ['nodes["Main_Contrast"].outputs[0]', 'nodes["Main_Color"].inputs[0]'], 
            ['nodes["Tip_Control"].outputs[0]', 'nodes["Tip_Color"].inputs[0]'], 
            ['nodes["Main_Highlight"].outputs[0]', 'nodes["Highlight_Mix"].inputs[1]'], 
            ['nodes["Secondary_Highlight"].outputs[0]', 'nodes["Highlight_Mix_2"].inputs[1]'],
            ['nodes["Highlight_Mix_2"].outputs[0]', 'nodes["Material Output"].inputs[0]']]
        self.universal_hair_default =  [
            ['Gradient_Color', 'MULTIPLY', True, 0.5, (0.466727614402771, 0.3782432973384857, 0.19663149118423462, 1.0), (0.2325773388147354, 0.15663157403469086, 0.07910887151956558, 1.0)],
            ['Tip_Color', 'SCREEN', True, 0.5, (0.466727614402771, 0.3782432973384857, 0.19663149118423462, 1.0), (0.38887712359428406, 0.28217148780822754, 0.10125808417797089, 1.0)],
            ['Main_Color', 'MIX', True, 0.5, (0.466727614402771, 0.3782432973384857, 0.19663149118423462, 1.0), (0.1809358447790146, 0.11345928907394409, 0.04037227854132652, 1.0)],
            ['Main_Diffuse', (0.800000011920929, 0.800000011920929, 0.800000011920929, 1.0), 0.0, (0.0, 0.0, 0.0)], 
            ['Gradient_Control', [[0.045454543083906174, (1.0, 1.0, 1.0, 1.0)], [0.8909090161323547, (0.0, 0.0, 0.0, 1.0)]]], 
            ['Main_Contrast', [[0.08181827515363693, (0.0, 0.0, 0.0, 1.0)], [0.863636314868927, (1.0, 1.0, 1.0, 1.0)]]], 
            ['Tip_Control', [[0.5045454502105713, (0.0, 0.0, 0.0, 1.0)], [1.0, (1.0, 1.0, 1.0, 1.0)]]], 
            ['Main_Highlight', 'GGX', (0.08054633438587189, 0.0542692169547081, 0.030534733086824417, 1.0), 0.25, (0.0, 0.0, 0.0)], 
            ['Secondary_Highlight', 'GGX', (0.023630360141396523, 0.02180372178554535, 0.018096407875418663, 1.0), 0.15000000596046448, (0.0, 0.0, 0.0)]]
        self.principled_hair_setup = [['ShaderNodeOutputMaterial', 'Material Output', 'Material Output', 'Material Output', (400,100)],
            ['ShaderNodeBsdfHairPrincipled', 'Principled Hair BSDF', 'Hair_Shader', 'Hair_Shader', (100,100)]]
        self.principled_hair_links = [['nodes["Hair_Shader"].outputs[0]', 'nodes["Material Output"].inputs[0]']]
        self.principled_hair_default = [['Hair_Shader', 'MELANIN', None, 0.11400000005960464, 0.3, (1.0, 0.52252197265625, 0.52252197265625, 1.0), None, 0.5, 0.0, 0.0, 1.4500000476837158, 0.03490658476948738, 0.0, 0.0]]
        self.hair_card_setup = [['ShaderNodeMixRGB', 'Mix', 'Gradient_Color', 'Gradient_Color', (-100.0, 280.0)], 
            ['ShaderNodeMixRGB', 'Mix', 'Tip_Color', 'Tip_Color', (150.0, 280.0)], 
            ['ShaderNodeMixRGB', 'Mix', 'Main_Color', 'Main_Color', (-325.0, 280.0)], 
            ['ShaderNodeHairInfo', 'Hair Info', 'Hair Info', 'Hair Info', (-890.0, 260.0)], 
            ['ShaderNodeAddShader', 'Add Shader', 'Highlight_Mix', 'Highlight_Mix', (680.0, 250.0)], 
            ['ShaderNodeBsdfDiffuse', 'Diffuse BSDF', 'Main_Diffuse', 'Main_Diffuse', (390.0, 240.0)], 
            ['ShaderNodeValToRGB', 'ColorRamp', 'Gradient_Control', 'Gradient_Control', (-660.0, 280.0)], 
            ['ShaderNodeValToRGB', 'ColorRamp', 'Main_Contrast', 'Main_Contrast', (-660.0, -5.0)], 
            ['ShaderNodeValToRGB', 'ColorRamp', 'Tip_Control', 'Tip_Control', (-660.0, 555.0)], 
            ['ShaderNodeBsdfGlossy', 'Glossy BSDF', 'Main_Highlight', 'Main_Highlight', (440.0, 80.0)], 
            ['ShaderNodeBsdfGlossy', 'Glossy BSDF', 'Secondary_Highlight', 'Secondary_Highlight', (680.0, 80.0)], 
            ['ShaderNodeAddShader', 'Add Shader', 'Highlight_Mix_2', 'Highlight_Mix_2', (890.0, 260.0)], 
            ['ShaderNodeTexImage', 'Image Texture', 'Hair_Alpha', 'Hair_Alpha', (165.0, 635.0)], 
            ['ShaderNodeBsdfDiffuse', 'Diffuse BSDF', 'Hair_Diffuse', 'Hair_Diffuse', (515.0, 400.0)], 
            ['ShaderNodeBsdfTransparent', 'Transparent BSDF', 'Hair_Transparency', 'Hair_Transparency', (510.0, 500.0338439941406)], 
            ['ShaderNodeMixShader', 'Mix Shader', 'Diffuse_Mix', 'Diffuse_Mix', (750.0, 550.0)], 
            ['ShaderNodeMixShader', 'Mix Shader', 'Color_Mix', 'Color_Mix', (1030.0, 615.0)], 
            ['ShaderNodeOutputMaterial', 'Material Output', 'Material Output', 'Material Output', (1175.0, 280.0)],
            ['ShaderNodeTexImage', 'Image Texture', 'Hair_Displacement', 'Hair_Displacement', (902.8016967773438, 90.0456771850586)]]
        self.hair_card_links = [['nodes["Gradient_Color"].outputs[0]', 'nodes["Tip_Color"].inputs[1]'], 
            ['nodes["Tip_Color"].outputs[0]', 'nodes["Main_Diffuse"].inputs[0]'], 
            ['nodes["Main_Color"].outputs[0]', 'nodes["Gradient_Color"].inputs[1]'], 
            ['nodes["Hair Info"].outputs[1]', 'nodes["Gradient_Control"].inputs[0]'], 
            ['nodes["Hair Info"].outputs[1]', 'nodes["Tip_Control"].inputs[0]'], 
            ['nodes["Hair Info"].outputs[4]', 'nodes["Main_Contrast"].inputs[0]'], 
            ['nodes["Highlight_Mix"].outputs[0]', 'nodes["Highlight_Mix_2"].inputs[0]'], 
            ['nodes["Main_Diffuse"].outputs[0]', 'nodes["Highlight_Mix"].inputs[0]'], 
            ['nodes["Gradient_Control"].outputs[0]', 'nodes["Gradient_Color"].inputs[0]'], 
            ['nodes["Main_Contrast"].outputs[0]', 'nodes["Main_Color"].inputs[0]'], 
            ['nodes["Tip_Control"].outputs[0]', 'nodes["Tip_Color"].inputs[0]'], 
            ['nodes["Main_Highlight"].outputs[0]', 'nodes["Highlight_Mix"].inputs[1]'], 
            ['nodes["Secondary_Highlight"].outputs[0]', 'nodes["Highlight_Mix_2"].inputs[1]'], 
            ['nodes["Highlight_Mix_2"].outputs[0]', 'nodes["Color_Mix"].inputs[2]'], 
            ['nodes["Hair_Alpha"].outputs[0]', 'nodes["Hair_Diffuse"].inputs[0]'], 
            ['nodes["Hair_Alpha"].outputs[1]', 'nodes["Diffuse_Mix"].inputs[0]'], 
            ['nodes["Hair_Alpha"].outputs[1]', 'nodes["Color_Mix"].inputs[0]'], 
            ['nodes["Hair_Diffuse"].outputs[0]', 'nodes["Diffuse_Mix"].inputs[2]'], 
            ['nodes["Hair_Transparency"].outputs[0]', 'nodes["Diffuse_Mix"].inputs[1]'], 
            ['nodes["Diffuse_Mix"].outputs[0]', 'nodes["Color_Mix"].inputs[1]'], 
            ['nodes["Color_Mix"].outputs[0]', 'nodes["Material Output"].inputs[0]'],
            ['nodes["Hair_Displacement"].outputs[0]', 'nodes["Material Output"].inputs[2]']]
        self.options = ['CLIP', 'OPAQUE']
        self.hair_card_default = lambda hair_dir: [['Hair_Alpha', self.def_image(hair_dir), (0.6079999804496765, 0.6079999804496765, 0.6079999804496765), 'REPEAT', (0.800000011920929, 0.800000011920929, 0.800000011920929), 0.0, 'MIX', 1.0, 1.0, 1.0, False, 'RGB', 1.0, (0.0, 0.0, 0.0, 1.0), 0.0, 'RGB', 1.0, (1.0, 1.0, 1.0, 1.0), 1.0, 'NEAR', 'LINEAR', 1, 1, 1, 0, False, False],
            ['Hair_Displacement', self.def_disp(hair_dir), (0.6079999804496765, 0.6079999804496765, 0.6079999804496765), 'REPEAT', (0.800000011920929, 0.800000011920929, 0.800000011920929), 0.0, 'MIX', 1.0, 1.0, 1.0, False, 'RGB', 1.0, (0.0, 0.0, 0.0, 1.0), 0.0, 'RGB', 1.0, (1.0, 1.0, 1.0, 1.0), 1.0, 'NEAR', 'LINEAR', 1, 0, 1, -1, False, False]]
    '''
    '''
    def set_universal_nodes(self):
        node_ops.new_material(self.hair, self.universal_hair_setup, self.universal_hair_links)
        bpy.context.object.active_material = self.material
    '''
    '''
    def set_principled_nodes(self):
        node_ops.new_material(self.hair, self.principled_hair_setup, self.principled_hair_links)
        bpy.context.object.active_material = self.material
    '''
    '''
    def set_hair_card_nodes(self):
        node_ops.new_material(self.hair_card, self.hair_card_setup, self.hair_card_links)
        bpy.context.object.active_material = self.hc_mat
    '''
    '''
    def set_material_nodes(self, style):
        material = self.material
        bpy.context.object.active_material = material
        nodes = material.node_tree.nodes
        node_ops.set_material(material, style)
    '''
    '''
    #Add particle hair
    def add_hair(self):
        p_sys = bpy.context.object.modifiers.new(self.hair, 'PARTICLE_SYSTEM').particle_system
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
    '''
    '''
    def hair_armature_mod(self, hair, vertgroup):
        new = "ARM_{}".format(hair)
        a_mod = bpy.context.object.modifiers.new(new, 'ARMATURE')
        a_mod.object = self.armature
        a_mod.vertex_group = vertgroup #'head'
    '''
    '''
    def convert_to_curve(self):
        self.view_hide = False
        bpy.ops.object.modifier_convert(modifier=self.hair)
        bpy.ops.object.convert(target='CURVE')
        bpy.context.object.data.extrude = 0.01
        bpy.ops.object.editmode_toggle()
        bpy.ops.curve.select_all(action='SELECT')
        bpy.ops.transform.tilt(value=-1.5708, mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)
        bpy.context.object.data.use_uv_as_generated = True
        bpy.ops.curve.match_texture_space()
        bpy.ops.curve.handle_type_set(type='ALIGNED')
        self.view_hide = True
        bpy.ops.object.editmode_toggle()
        bpy.context.object.name = self.hair_card
        bpy.context.object.data.name = self.hair_card
        self.set_hair_card_nodes()
        bpy.context.object.active_material = self.hc_mat
        bpy.data.objects[self.hair].hide_set(state=True)
        self.hair_armature_mod(self.hair_card, '')
    '''
    '''
    def convert_to_mesh(self):
        bpy.ops.object.convert(target='MESH', keep_original=True)
        bpy.ops.object.editmode_toggle()
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.follow_active_quads(mode='LENGTH')
        bpy.ops.object.editmode_toggle()
        bpy.context.object.name = self.hair_mesh
        bpy.context.object.data.name = self.hair_mesh
        self.hair_armature_mod(self.hair_mesh, '')
        bpy.data.objects[self.hair_card].hide_set(state=True)
    '''
    '''
    def get_mat_options(self):
        blend = self.material.blend_method
        shadow = self.material.shadow_method
        return [blend, shadow]
    '''
    '''
    def set_mat_options(self, object):
        object.active_material.blend_method = 'CLIP'
        object.active_material.shadow_method = 'OPAQUE'
        object.active_material.cycles.displacement_method = 'BOTH'
        object.active_material.pass_index = 32
    '''
    '''
    def make_hair(self, target):
        hair = object_ops.CopyObject(bpy.context.object, self.hair).new_object_full()
        self.add_hair()
        self.hair_armature_mod(self.hair, target)

