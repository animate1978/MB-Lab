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
# ManuelbastioniLAB - Copyright (C) 2015-2018 Manuel Bastioni
# Teto for this part.

import logging
import json
import os
import bpy
import bmesh

from . import algorithms
from . import creation_tools_ops
from . import file_ops
from . import mesh_ops
from . import skeleton_ops
from . import utils

# create the template for joints base file.
def create_base_template_file(filepath):
    file = {}
    for item in skeleton_ops.ik_joints_head:
        file[item] = []
    for item in skeleton_ops.ik_joints_tail:
        file[item] = []
    for item in skeleton_ops.normal_joints_head:
        file[item] = []
    for item in skeleton_ops.normal_joints_tail:
        file[item] = []
    with open(filepath, "w") as j_file:
        json.dump(file, j_file, indent=2)

current_filters = []
joints_base_list = []
points_index = 0
current_joints_base_file = {}
joints_base_files = {}
mesh_handling_dict = {}

def get_set_joints_base_file(joints_base_name):
    global joints_base_files
    if joints_base_name in joints_base_files:
        return joints_base_files[joints_base_name]
    addon_directory = os.path.dirname(os.path.realpath(__file__))
    filepath = os.path.join(
        addon_directory,
        creation_tools_ops.get_data_directory(), "joints",
        joints_base_name)
    file = file_ops.load_json_data(filepath)
    # Below : This way, each time the file
    # is None it's not added to database.
    if file != None:
        joints_base_files[joints_base_name] = file
    return file

def set_current_joints_base_file(joints_base_name):
    global current_joints_base_file
    global points_index
    tmp = get_set_joints_base_file(joints_base_name)
    if len(current_joints_base_file) < 1:
        if tmp == None:
            return
        points_index = 0
        current_joints_base_file[joints_base_name] = tmp
        return
    for key in current_joints_base_file.keys():
        if key != joints_base_name:
            points_index = 0
            current_joints_base_file.clear()
            current_joints_base_file[joints_base_name] = tmp

def create_joints_base_layout(layout):
    global current_filters
    global joints_base_list
    scn = bpy.context.scene
    layout_a = layout.column(align=True)
    layout_a.label(text="Name's filters", icon='SORT_ASC')
    layout_b = layout_a.row(align=True)
    layout_b.prop(scn, "mbcrea_joints_filter_head", toggle=1)
    layout_b.prop(scn, "mbcrea_joints_filter_tail", toggle=1)
    layout_a.prop(scn, "mbcrea_joints_filter_ik", toggle=1)
    layout_d = layout_a.row(align=True)
    layout_d.prop(scn, "mbcrea_joints_filter_h", toggle=1)
    layout_d.prop(scn, "mbcrea_joints_filter_t", toggle=1)
    layout_e = layout_a.row(align=True)
    layout_e.prop(scn, "mbcrea_joints_filter_l", toggle=1)
    layout_e.prop(scn, "mbcrea_joints_filter_r", toggle=1)
    layout_a.separator()
    layout_a.prop(scn, "mbcrea_joints_filter", icon='FILTER')
    # Now we check content and sort the result.
    filters = []
    if scn.mbcrea_joints_filter_head:
        filters.append("_head")
    if scn.mbcrea_joints_filter_tail:
        filters.append("_tail")
    if scn.mbcrea_joints_filter_ik:
        filters.append("IK_")
    if scn.mbcrea_joints_filter_h:
        filters.append("_H_")
    if scn.mbcrea_joints_filter_t:
        filters.append("_T_")
    if scn.mbcrea_joints_filter_r:
        filters.append("_R_")
    if scn.mbcrea_joints_filter_l:
        filters.append("_L_")
    tmp = algorithms.split(scn.mbcrea_joints_filter)
    filters += tmp
    # Now we check if filters have changed.
    same = True
    if len(filters) != len(current_filters):
        same = False
    else:
        for item in filters:
            if not item in current_filters:
                same = False
                break
    if same and len(joints_base_list) > 0:
        return
    current_filters = filters[:]
    # If filters have changed, we update the list of joints.
    joints_base_list = utils.sort_str_content(skeleton_ops.ik_joints_head, current_filters, True)
    joints_base_list += utils.sort_str_content(skeleton_ops.ik_joints_tail, current_filters, True)
    joints_base_list += utils.sort_str_content(skeleton_ops.normal_joints_head, current_filters, True)
    joints_base_list += utils.sort_str_content(skeleton_ops.normal_joints_tail, current_filters, True)
    # That's all.

# direction : +1 -> next / -1 -> previous / 0 -> current
# This method returns the name of selected joints
# Select the points in a mesh if the selected points have changed
# if obj == None and the Handling has to be created, nothing happens
def get_points(direction=0):
    global current_joints_base_file
    global points_index
    global joints_base_list
    obj = bpy.context.object
    if obj == None or len(current_joints_base_file) < 1 or len(joints_base_list) < 1:
        return None
    tmp = list(current_joints_base_file.keys())
    file_name = tmp[0]
    # Now we get the new name of the joints
    joints_name = ""
    if direction < 0:
        points_index -= 1
        if points_index < 0:
            points_index = len(joints_base_list)-1
    elif direction > 0:
        points_index += 1
        if points_index >= len(joints_base_list):
            points_index = 0
    if points_index >= len(joints_base_list): # It happens
        points_index = len(joints_base_list)-1
    joints_name = joints_base_list[points_index]
    # Now we seek and keep the values in the MeshHandling.
    mh = get_mesh_handling(file_name, obj)
    """if mh == None: # Because obj == None
        return None"""
    hist = mh.get_mesh_history(joints_name)
    if hist == None:
        hist = mh.create_mesh_history(joints_name)
        # The history is created, so we copy values from file
        file_points_value = current_joints_base_file[file_name][joints_name]
        hist.set('VERTEX', file_points_value)
    # return the History
    return hist

def get_mesh_handling(file_name, obj=None):
    global mesh_handling_dict
    if not file_name in mesh_handling_dict:
        if obj == None:
            return None
        mesh_handling_dict[file_name] = mesh_ops.MeshHandling(file_name, obj)
    return mesh_handling_dict[file_name]

def save_joints_base_file():
    global current_joints_base_file
    global mesh_handling_dict
    if len(current_joints_base_file) < 1:
        return
    file_name = ""
    file_content = None
    for key, item in current_joints_base_file.items():
        file_name = key
        file_content = item
    # Now we check all dict in mesh hanling,
    # and replace new values in the file.
    mh = mesh_handling_dict[file_name]
    hist = mh.get_histories()
    if len(hist) < 1:
        return # No change in points, so useless to save.
    for key, item in hist.items():
        file_content[key] = sorted(item.get_history('VERTEX'))
        item.clear_recover()
    # Now we save the file.
    addon_directory = os.path.dirname(os.path.realpath(__file__))
    filepath = os.path.join(
        addon_directory,
        creation_tools_ops.get_data_directory(), "joints",
        file_name)
    with open(filepath, "w") as j_file:
        json.dump(file_content, j_file, indent=2)

# --------------------------------------------------
#            Central point of joints
# --------------------------------------------------
current_joint_central_point = None

def show_central_point(hist):
    global current_joints_base_file
    global current_joint_central_point
    if hist == None or not hist.has_elements():
        return
    indices = hist.get_history()
    # We check all points in the obj of hist
    vertices = []
    obj = hist.object
    bm = bmesh.from_edit_mesh(obj.data)
    for vert in bm.verts:
        if vert.index in indices:
            vertices.append(vert.co)
    # Now we have all vertices, we compute the average center
    central_point = algorithms.average_center(vertices)
    if current_joint_central_point == None:
        mesh = bpy.data.meshes.new('Basic_Sphere')
        current_joint_central_point = bpy.data.objects.new("Joint center", mesh)
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=4, v_segments=4, diameter=0.004)
        bm.to_mesh(mesh)
        bm.free()
        file_ops.link_to_collection(current_joint_central_point)
        current_joint_central_point.hide_select = True
    current_joint_central_point.location = (central_point.x, central_point.y, central_point.z)

# --------------------------------------------------
#            Offset point of joints
# --------------------------------------------------
current_joints_offset_file = {}
joints_offset_files = {}
current_offset_point = None
recover_the_offset_point = []

# create the template for joints base file.
def create_offset_template_file(filepath):
    file = {}
    for item in skeleton_ops.ik_joints_head:
        file[item] = [0, 0, 0]
    for item in skeleton_ops.ik_joints_tail:
        file[item] = [0, 0, 0]
    with open(filepath, "w") as j_file:
        json.dump(file, j_file, indent=2)

def set_current_joints_offset_file(joints_offset_name):
    global current_joints_offset_file
    tmp = get_set_joints_offset_file(joints_offset_name)
    if len(current_joints_offset_file) < 1:
        if tmp == None:
            return
        current_joints_offset_file[joints_offset_name] = tmp
        return
    for key in current_joints_offset_file.keys():
        if key != joints_offset_name:
            current_joints_offset_file.clear()
            current_joints_offset_file[joints_offset_name] = tmp

def get_set_joints_offset_file(joints_offset_name):
    global joints_offset_files
    if joints_offset_name in joints_offset_files:
        return joints_offset_files[joints_offset_name]
    addon_directory = os.path.dirname(os.path.realpath(__file__))
    filepath = os.path.join(
        addon_directory,
        creation_tools_ops.get_data_directory(), "joints",
        joints_offset_name)
    file = file_ops.load_json_data(filepath)
    # Below : This way, each time the file
    # is None it's not added to database.
    if file != None:
        joints_offset_files[joints_offset_name] = file
    return file

def create_offset_point():
    global current_offset_point
    global recover_the_offset_point
    if current_offset_point != None:
        file_ops.unlink_to_collection(current_offset_point)
        current_offset_point = None
        recover_the_offset_point = []
    mesh = bpy.data.meshes.new('Basic_IcoSphere')
    current_offset_point = bpy.data.objects.new("Joint offset", mesh)
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=1, diameter=0.002)
    bm.to_mesh(mesh)
    bm.free()
    file_ops.link_to_collection(current_offset_point)

def create_offset_and_set_to_center():
    global current_offset_point
    global current_joint_central_point
    global current_joints_offset_file
    hist = get_points()
    if hist == None or current_joint_central_point == None:
        return
    if current_offset_point == None:
        create_offset_point()
    vect = current_joint_central_point.location
    current_offset_point.location = (vect.x, vect.y, vect.z)
    recover_the_offset_point = [0, 0, 0]
    current_offset_point.hide_viewport = False    
    file = None
    # We put the new entry in file
    for key, item in current_joints_offset_file.items():
        file = item
    file[hist.name] = [0, 0, 0]
    
def show_offset_point(hist):
    global current_offset_point
    global current_joints_offset_file
    global current_joint_central_point
    global recover_the_offset_point
    if hist == None or len(current_joints_offset_file) < 1:
        return
    # Now we search in the offset file.
    file = None
    for key, item in current_joints_offset_file.items():
        file = item
    if hist.name in file:
        if current_offset_point == None:
            create_offset_point()
        co = file[hist.name]
        vect = current_joint_central_point.location
        current_offset_point.location = (
            vect.x + co[0],
            vect.y + co[1],
            vect.z + co[2])
        recover_the_offset_point = [co[0], co[1], co[2]]
        current_offset_point.hide_viewport = False
    elif current_offset_point != None:
        current_offset_point.hide_viewport = True
    
def hide_offset_point():
    global current_offset_point
    if current_offset_point != None:
        current_offset_point.hide_viewport = True

def delete_offset_point():
    global current_offset_point
    global current_joints_offset_file
    hist = get_points()
    if hist == None or len(current_joints_offset_file) < 1:
        return
    # Now we search in the offset file.
    file = None
    for key, item in current_joints_offset_file.items():
        file = item
    if hist.name in file:
        del file[hist.name]
    current_offset_point.hide_viewport = True
    
def recover_offset_point():
    global current_offset_point
    global current_joints_offset_file
    global recover_the_offset_point
    if current_offset_point == None:
        return
    hist = get_points()
    if hist == None or len(current_joints_offset_file) < 1:
        return
    # Now we search in the offset file.
    file = None
    for key, item in current_joints_offset_file.items():
        file = item
    # Now we recover the offset
    file[hist.name] = [
        recover_the_offset_point[0],
        recover_the_offset_point[1],
        recover_the_offset_point[2]]
    show_offset_point(hist)

def set_offset_point():
    global current_offset_point
    global current_joints_offset_file
    global current_joint_central_point
    hist = get_points()
    if hist == None or len(current_joints_offset_file) < 1:
        return
    # Now we search in the offset file.
    file = None
    for key, item in current_joints_offset_file.items():
        file = item
    # Now we calculate de relative location of the offset
    center_point = current_joint_central_point.location
    offset_point = current_offset_point.location
    file[hist.name] = [
        offset_point[0] - center_point[0],
        offset_point[1] - center_point[1],
        offset_point[2] - center_point[2]]

def save_joints_offset_file():
    global current_joints_offset_file
    if len(current_joints_offset_file) < 1:
        return
    file_name = ""
    file_content = None
    for key, item in current_joints_offset_file.items():
        file_name = key
        file_content = item
    # Now we save the file.
    addon_directory = os.path.dirname(os.path.realpath(__file__))
    filepath = os.path.join(
        addon_directory,
        creation_tools_ops.get_data_directory(), "joints",
        file_name)
    with open(filepath, "w") as j_file:
        json.dump(file_content, j_file, indent=2)
    
# --------------------------------------------------
#    All layout elements for joints manipulation
# --------------------------------------------------

bpy.types.Scene.mbcrea_joints_filter_head = bpy.props.BoolProperty(
    name="Head",
    description="Show only head joints when on")

bpy.types.Scene.mbcrea_joints_filter_tail = bpy.props.BoolProperty(
    name="Tail",
    description="Show only tail joints when on")
    
bpy.types.Scene.mbcrea_joints_filter_ik = bpy.props.BoolProperty(
    name="IK",
    description="Show only joints for Inverted Kinematics when on")

bpy.types.Scene.mbcrea_joints_filter_h = bpy.props.BoolProperty(
    name="_H_",
    description="If selected, shows all _H_ in name")

bpy.types.Scene.mbcrea_joints_filter_t = bpy.props.BoolProperty(
    name="_T_",
    description="If selected, shows all _T_ in name")

bpy.types.Scene.mbcrea_joints_filter_r = bpy.props.BoolProperty(
    name="Right",
    description="If selected, shows all _R_ (Right) in name")

bpy.types.Scene.mbcrea_joints_filter_l = bpy.props.BoolProperty(
    name="Left",
    description="If selected, shows all _L_ (Left) in name")

bpy.types.Scene.mbcrea_joints_filter = bpy.props.StringProperty(
    name="",
    description="Other filters (more than one is possible)",
    default="",
    maxlen=1024,
    subtype='FILE_NAME')
