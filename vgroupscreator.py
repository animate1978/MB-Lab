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

# create the template for vgroups base file.
def create_base_template_file(filepath):
    file = {}
    for item in skeleton_ops.base_bones:
        file[item] = []
    with open(filepath, "w") as j_file:
        json.dump(file, j_file, indent=2)

# create the template for vgroups muscle file.
def create_muscle_template_file(filepath):
    file = {}
    for item in skeleton_ops.muscle_bones:
        file[item] = []
    with open(filepath, "w") as j_file:
        json.dump(file, j_file, indent=2)

vgroups_base_list = []
vgroups_muscle_list = []
# Name only, because all is done with Blender.
current_vgroups_file = ""
# Key : Name of the file with .json
# Value : a dict with
#   name : The name.
#   object : Object attached to file.
#   file : The file itself.
#   init : If vgroups are created in Blender or not.
vgroups_base_files = {}
vgroups_muscle_files = {}

def get_set_vgroups_file(type, vgroups_name):
    global vgroups_base_files
    global vgroups_muscle_files
    if type == 'BASE' and vgroups_name in vgroups_base_files:
        return vgroups_base_files[vgroups_name]
    elif vgroups_name in vgroups_muscle_files:
        return vgroups_muscle_files[vgroups_name]
    addon_directory = os.path.dirname(os.path.realpath(__file__))
    filepath = os.path.join(
        addon_directory,
        creation_tools_ops.get_data_directory(), "vgroups",
        vgroups_name)
    file = file_ops.load_json_data(filepath)
    if file != None:
        extended_file = {}
        extended_file["name"] = vgroups_name
        extended_file["file"] = file
        extended_file["init"] = False
        # we add the dict in list of file
        if type == 'BASE':
            vgroups_base_files[vgroups_name] = extended_file
        else:
            vgroups_muscle_files[vgroups_name] = extended_file
    return extended_file

def set_current_vgroups_file(type, vgroups_name):
    global current_vgroups_file
    if vgroups_name != current_vgroups_file:
        tmp = get_set_vgroups_file(type, vgroups_name)
        if tmp == None:
            return
        current_vgroups_file = vgroups_name

def set_current_vgroups_type(type, obj):
    global current_vgroups_file
    global vgroups_base_files
    global vgroups_muscle_files
    if obj == None or len(current_vgroups_file) < 1:
        return
    pack = None
    if type == 'BASE':
        pack = vgroups_base_files[current_vgroups_file]
    else:
        pack = vgroups_muscle_files[current_vgroups_file]
    if pack == None or pack["init"]:
        return
    # Check a last time if obj exists, and init.
    if "object" not in pack:
        pack["object"] = obj
    if pack["object"] == None:
        return
    pack["init"] = True
    # Now we create the weight paints    
    for key, value in pack['file'].items():
        txt = ""
        if type == 'BASE':
            txt = "base_" + key
        else:
            txt = "mscl_" + key
        vg = obj.vertex_groups.new(name=txt)
        for i in value:
            vg.add([i[0]], i[1], "REPLACE")

# Return all vgroups from a given type,
# and base_ & mscl_ are removed.
def get_current_vgroups_type(type):
    global current_vgroups_file
    global vgroups_base_files
    global vgroups_muscle_files
    if len(current_vgroups_file) < 1:
        return None, None
    pack = None
    if type == 'BASE':
        pack = vgroups_base_files[current_vgroups_file]
    else:
        pack = vgroups_muscle_files[current_vgroups_file]
    if pack == None:
        return None, None
    # Now we get the vgroups on object.
    obj = pack["object"]
    obj.update_from_editmode() # Just in case.
    dat = obj.data
    vgroup_names = {vgroup.index: vgroup.name for vgroup in obj.vertex_groups}
    index_name_weight = {v.index: [[vgroup_names[g.group], g.weight] for g in v.groups] for v in dat.vertices}
    new_dict = {name: [] for name in vgroup_names.values()}
    for key, double_values in index_name_weight.items():
        for dv in double_values:
            new_dict[dv[0]].append([int(key), dv[1]])
    return_dict = {}
    for key, value in new_dict.items():
        return_dict[key[5:]] = value
    return return_dict
    
def save_current_vgroups_type(type):
    vg = get_current_vgroups_type(type)
    if vg == None:
        return
    addon_directory = os.path.dirname(os.path.realpath(__file__))
    filepath = os.path.join(
        addon_directory,
        creation_tools_ops.get_data_directory(), "vgroups",
        file_name)
    with open(filepath, "w") as j_file:
        json.dump(vg, j_file, indent=2)