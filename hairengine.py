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

from . import algorithms
from . import object_ops



# ------------------------------------------------------------------------
#    Functions
# ------------------------------------------------------------------------


def get_hair_data(fileName):
    data_dir = algorithms.get_data_path()
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
def add_scalp():
    bpy.ops.object.mode_set(mode='OBJECT')
    gs = object_ops.get_sel()
    viw = object_ops.vg_idx_dict(gs)
    vid = object_ops.vidx_dict()
    object_ops.obj_new('Hair', gs[0], gs[1], "ManuelBastioni_Character")
    try:
        object_ops.copy_wt("Hair", viw, vid)
    except:
        pass
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')
    bpy.ops.object.shade_smooth()

def hair_armature_mod(skeleton):
    a_mod = bpy.data.objects["Hair"].modifiers.new("armature_hair", 'ARMATURE')
    a_mod.object = skeleton
    a_mod.vertex_group = 'head'

#Add particle hair
def add_hair():
    p_sys = bpy.data.objects["Hair"].modifiers.new("hair", 'PARTICLE_SYSTEM').particle_system
    p_sys.settings.type = 'HAIR'
    #p_sys.settings.use_render_emitter = False
    p_sys.settings.hair_length = 0.1
    p_sys.settings.child_type = 'INTERPOLATED'
    bpy.context.object.show_instancer_for_viewport = False
    bpy.ops.particle.connect_hair(all=True)

    
    


# def execute():
#     actv = bpy.context.view_layer.objects.active
#     get_mode = bpy.ops.object.mode_get()

#     skeleton = get_skeleton()
#     skeleton.select_set(state=False)
    
#     body = get_body_mesh()
#     body.select_set(state=True)
#     bpy.context.view_layer.objects.active = body



#    faces = hairengine.get_hair_data(fileName)

#    hairengine.sel_faces(faces)

#     hairengine.add_scalp()
#     hairengine.hair_armature_mod(skeleton)
#     hairengine.add_hair()

#     bpy.ops.object.mode_set(mode='OBJECT')
#     bpy.context.view_layer.objects.active = actv
#     try:
#         bpy.ops.object.mode_set(mode='POSE')
#     except:
#         pass


