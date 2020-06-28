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
# Teto, for MB-Lab

import logging
import json
import os
import bpy

from . import file_ops
from . import creation_tools_ops
from . import mesh_ops


logger = logging.getLogger(__name__)

body_height_Z_parts = sorted([
    "head_height_Z", "neck_height_Z", "torso_height_Z",
    "buttock_height_Z", "upperleg_length", "lowerleg_length",
    "feet_height_Z"])

measures_parts_points = sorted([
    "upperleg_length", "buttock_depth_Y", "buttock_width_X",
    "lowerleg_length", "head_height_Z", "feet_length",
    "feet_heel_width", "torso_height_Z","shoulders_width",
    "feet_height_Z", "head_width_X", "chest_depth_Y",
    "forearm_length", "buttock_height_Z", "hands_width",
    "hands_length", "upperarm_length", "feet_width",
    "body_height_Z", "neck_height_Z", "head_length",
    "chest_width_X"])
    
measures_parts_girths = sorted([
    "wrist_girth", "upperarm_axillary_girth", "neck_girth",
    "lowerleg_bottom_girth", "lowerleg_calf_girth",
    "upperleg_top_girth", "waist_girth", "elbow_girth",
    "upperleg_bottom_girth", "chest_girth", "buttock_girth"])

score_weights = sorted([
    "upperleg_length", "buttock_depth_Y", "buttock_width_X",
    "wrist_girth", "upperarm_axillary_girth", "lowerleg_length",
    "lowerleg_bottom_girth", "head_height_Z", "feet_length",
    "lowerleg_calf_girth", "feet_heel_width", "torso_height_Z",
    "upperleg_top_girth", "shoulders_width", "feet_height_Z",
    "waist_girth", "elbow_girth", "head_width_X",
    "chest_depth_Y", "neck_girth", "forearm_length",
    "head_length", "buttock_height_Z", "hands_length",
    "hands_width", "chest_girth", "upperarm_length",
    "feet_width", "body_height_Z", "neck_height_Z",
    "upperleg_bottom_girth", "buttock_girth", "chest_width_X"])

def create_measures_file(filepath):
    file = {}
    file["body_height_Z_parts"] = ["head_height_Z",
        "neck_height_Z", "torso_height_Z", "buttock_height_Z",
        "upperleg_length", "lowerleg_length", "feet_height_Z"]
    file["measures"] = {
        "upperleg_length": [],
        "buttock_depth_Y": [],
        "buttock_width_X": [],
        "wrist_girth": [],
        "upperarm_axillary_girth": [],
        "neck_girth": [],
        "lowerleg_length": [],
        "lowerleg_bottom_girth": [],
        "head_height_Z": [],
        "feet_length": [],
        "lowerleg_calf_girth": [],
        "feet_heel_width": [],
        "torso_height_Z": [],
        "upperleg_top_girth": [],
        "shoulders_width": [],
        "feet_height_Z": [],
        "waist_girth": [],
        "elbow_girth": [],
        "head_width_X": [],
        "chest_depth_Y": [],
        "upperleg_bottom_girth": [],
        "forearm_length": [],
        "buttock_height_Z": [],
        "hands_width": [],
        "hands_length": [],
        "chest_girth": [],
        "upperarm_length": [],
        "feet_width": [],
        "body_height_Z": [],
        "neck_height_Z": [],
        "head_length": [],
        "buttock_girth": [],
        "chest_width_X": []}
    file["relations"] = [
        ["body_height_Z", "Body_Size"],
        ["torso_height_Z", "Torso_Length"],
        ["chest_width_X", "Chest_SizeX"],
        ["chest_depth_Y", "Chest_SizeY"],
        ["chest_girth", "Chest_Girth"],
        ["neck_girth", "Neck_Size"],
        ["neck_girth", "Neck_Back"],
        ["head_width_X", "Head_SizeX"],
        ["head_length", "Head_SizeY"],
        ["head_height_Z", "Head_SizeZ"],
        ["neck_height_Z", "Neck_Length"],
        ["shoulders_width", "Shoulders_SizeX"],
        ["buttock_height_Z", "Pelvis_Length"],
        ["buttock_depth_Y", "Pelvis_SizeY"],
        ["buttock_width_X", "Pelvis_SizeX"],
        ["buttock_girth", "Pelvis_Girth"],
        ["waist_girth", "Stomach_LocalFat"],
        ["waist_girth", "Stomach_Volume"],
        ["upperleg_length", "Legs_UpperlegLength"],
        ["lowerleg_length", "Legs_LowerlegLength"],
        ["upperleg_top_girth", "Legs_UpperlegSize"],
        ["upperleg_top_girth", "Legs_UpperThighGirth"],
        ["upperleg_bottom_girth", "Legs_LowerThighGirth"],
        ["lowerleg_calf_girth", "Legs_CalfGirth"],
        ["lowerleg_bottom_girth", "Legs_AnkleSize"],
        ["upperarm_axillary_girth", "Arms_UpperarmGirth"],
        ["upperarm_axillary_girth", "Shoulders_Size"],
        ["upperarm_length", "Arms_UpperarmLength"],
        ["forearm_length", "Arms_ForearmLength"],
        ["elbow_girth", "Elbows_Size"],
        ["wrist_girth", "Wrists_Size"],
        ["feet_width", "Feet_SizeX"],
        ["feet_length", "Feet_SizeY"],
        ["feet_height_Z", "Feet_SizeZ"],
        ["hands_length", "Hands_Length"],
        ["hands_width", "Hands_FingersInterDist"],
        ["feet_heel_width", "Feet_HeelWidth"]]
    file["score_weights"] = {
        "upperleg_length": 1,
        "buttock_depth_Y": 1,
        "buttock_width_X": 1,
        "wrist_girth": 1,
        "upperarm_axillary_girth": 3,
        "lowerleg_length": 1,
        "lowerleg_bottom_girth": 3,
        "head_height_Z": 1,
        "feet_length": 0.5,
        "lowerleg_calf_girth": 3,
        "feet_heel_width": 0.5,
        "torso_height_Z": 1,
        "upperleg_top_girth": 3,
        "shoulders_width": 2,
        "feet_height_Z": 0.5,
        "waist_girth": 3,
        "elbow_girth": 3,
        "head_width_X": 1,
        "chest_depth_Y": 1,
        "neck_girth": 0.5,
        "forearm_length": 1,
        "head_length": 1,
        "buttock_height_Z": 1,
        "hands_length": 0.5,
        "hands_width": 0.5,
        "chest_girth": 3,
        "upperarm_length": 1,
        "feet_width": 0.5,
        "body_height_Z": 1,
        "neck_height_Z": 1,
        "upperleg_bottom_girth": 3,
        "buttock_girth": 3,
        "chest_width_X": 1}
    with open(filepath, "w") as j_file:
        json.dump(file, j_file, indent=2)

# Method that can be used when a config file is active
def check_inconsistancies(key):
    if not creation_tools_ops.is_project_loaded():
        return
    measures_name = creation_tools_ops.get_content(key, "measures_file")
    if measures_name == '':
        return # Just in case...
    # we create the txt file content.
    txt_content = []
    txt_content.append(str("Header : Check inconstancies in file " + measures_name))
    # We open the measures file and if it exists, we load it.
    measures_file = get_set_measures_file(measures_name)
    if measures_file == None:
        txt_content.append(str("Measures file : " + measures_name + " doesn't exist"))
        txt_content.append(str("Stop checking."))
    else:
        txt_content.append(str("Measures file : " + measures_name))
    # We check if morph file exist and if yes, we load it.
    morph_name = creation_tools_ops.get_content(key, "shared_morphs_file")
    if morph_name == "":
        txt_content.append(str("Morph file is unknown, stop checking."))
    elif measures_file != None:
        addon_directory = os.path.dirname(os.path.realpath(__file__))
        filepath = os.path.join(
            addon_directory,
            creation_tools_ops.get_data_directory(),
            "morphs", morph_name)
        morph_file = file_ops.load_json_data(filepath, "")
        txt_content.append("Morph file : " + morph_name)
        txt_content.append("---------------")
        txt_content.append("Check morph file content :")
        # Now we check "relations" key and check if any morphs are missing.
        keys = morph_file.keys()
        is_in = False
        perfect = True
        splitted = []
        for couple in measures_file["relations"]:
            splitted = couple[1].split("_")
            splitted[0] += "_"
            splitted[1] += "_"
            for k in keys:
                if splitted[0] in k and splitted[1] in k:
                    is_in = True
                    break
            if not is_in:
                perfect = False
                txt_content.append(str("Not in morph file : " + couple[1]))
        if perfect:
            txt_content.append("All measures correspond to a valid morph.")
            txt_content.append("---------------")
    # At the end we save the file.
    final_name = get_inconsistancies_file_name(key)
    with open(final_name, "w") as j_file:
        json.dump(txt_content, j_file, indent=2)

def get_inconsistancies_file_name(key):
    if not creation_tools_ops.is_project_loaded():
        return
    addon_directory = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(
        addon_directory,
        creation_tools_ops.get_data_directory(),
        "measures", creation_tools_ops.get_content(key, "measures_file")+".txt")

measures_files = {}
current_measures_file = {}

def init_all():
    global measures_files
    global current_measures_file
    global two_points_index
    global girth_index
    global mesh_handling_dict
    global recover_weights_first
    measures_files.clear()
    current_measures_file.clear()
    two_points_index = 0
    girth_index = 0
    mesh_handling_dict.clear()
    recover_weights_first = True
    
def get_set_measures_file(measures_name):
    global measures_files
    if measures_name in measures_files:
        return measures_files[measures_name]
    addon_directory = os.path.dirname(os.path.realpath(__file__))
    filepath = os.path.join(
        addon_directory,
        creation_tools_ops.get_data_directory(), "measures",
        measures_name)
    file = file_ops.load_json_data(filepath)
    # Below : This way, each time the file
    # is None it's not put in database.
    if file != None:
        measures_files[measures_name] = file
    return file

def set_current_measures_file(measures_name):
    global current_measures_file
    global two_points_index
    global girth_index
    global recover_weights_first
    tmp = get_set_measures_file(measures_name)
    if len(current_measures_file) < 1:
        if tmp == None:
            return
        two_points_index = 0
        girth_index = 0
        current_measures_file[measures_name] = tmp
        recover_weights_first = True
        return
    for key in current_measures_file.keys():
        if key != measures_name:
            two_points_index = 0
            girth_index = 0
            current_measures_file.clear()
            current_measures_file[measures_name] = tmp
            recover_weights_first = True

def extract_points(measures_name, points_name):
    global measures_files
    if not measures_name in measures_files:
        return []
    measures = measures_files[measures_name]["measures"]
    if not points_name in measures:
        return []
    return measures[points_name]

def extract_score_weights(measures_name, weight_name):
    global measures_files
    if not measures_name in measures_files:
        return []
    score_weights = measures_files[measures_name]["score_weights"]
    if not weight_name in score_weights:
        return []
    return score_weights[weight_name]
    
def save_measures_file():
    global current_measures_file
    global measures_parts_points
    global measures_parts_girths
    if len(current_measures_file) < 1:
        return
    file_name = ""
    file_content = None
    for key, item in current_measures_file.items():
        file_name = key
        file_content = item
    mesh_handling = get_mesh_handling(file_name, None)
    # In the file, we save nothing for "body_height_Z_parts"
    # In the file, we save things about "measures"
    topic = file_content["measures"]
    # For key "measures", we start with the "2 points"
    for points in measures_parts_points:
        hist = mesh_handling.get_mesh_history(points)
        if hist != None:
            topic[points] = hist.get_measures_file_form()
            hist.clear_recover()
    # For key "measures", we continue with the "girths"
    for girth in measures_parts_girths:
        hist = mesh_handling.get_mesh_history(girth)
        if hist != None:
            tmp = hist.get_measures_file_form()
            last_index = len(tmp)-1
            if last_index > 1 and tmp[0] != tmp[last_index]:
                tmp.append(tmp[0])
            topic[girth] = tmp
            hist.clear_recover()
    # In the file, we save nothing for "relations".
    # In the file, we save things about "score_weights"
    save_weights()
    # Now we save the file
    addon_directory = os.path.dirname(os.path.realpath(__file__))
    filepath = os.path.join(
        addon_directory,
        creation_tools_ops.get_data_directory(), "measures",
        file_name)
    with open(filepath, "w") as j_file:
        json.dump(file_content, j_file, indent=2)
    
# ------------------------------------------------------------------------
#    All methods dedicated to the use of mesh_ops
# ------------------------------------------------------------------------

two_points_index = 0
girth_index = 0
mesh_handling_dict = {}

# direction : +1 -> next / -1 -> previous / 0 -> current
# This method returns the name of selected 2 points
# Select the points in a mesh if the selected points have changed
# if obj == None and the Handling has to be created, nothing happens
def get_two_points(direction=0):
    global current_measures_file
    global two_points_index
    global measures_parts_points
    obj = bpy.context.object
    if obj == None or len(current_measures_file) < 1:
        return None
    tmp = list(current_measures_file.keys())
    file_name = tmp[0]
    # Now we get the new name of the measures
    measure_name = ""
    if direction < 0:
        two_points_index -= 1
        if two_points_index < 0:
            two_points_index = len(measures_parts_points)-1
    elif direction > 0:
        two_points_index += 1
        if two_points_index >= len(measures_parts_points):
            two_points_index = 0
    if two_points_index >= measures_parts_points: # It happens
        two_points_index = len(measures_parts_points)-1
    measure_name = measures_parts_points[two_points_index]
    # Now we seek and keep the values in the MeshHandling.
    mh = get_mesh_handling(file_name, obj)
    """if mh == None: # Because obj == None
        return None"""
    hist = mh.get_mesh_history(measure_name)
    if hist == None:
        hist = mh.create_mesh_history(measure_name)
        # The history is created, so we copy values from file
        file_points_value = current_measures_file[file_name]["measures"][measure_name]
        hist.set('VERTEX', file_points_value)
    # return the History
    return hist

def get_girth(direction=0):
    global current_measures_file
    global girth_index
    global measures_parts_girths
    obj = bpy.context.object
    if obj == None or len(current_measures_file) < 1:
        return None
    tmp = list(current_measures_file.keys())
    file_name = tmp[0]
    # Now we get the new name of the measures
    measure_name = ""
    if direction < 0:
        girth_index -= 1
        if girth_index < 0:
            girth_index = len(measures_parts_girths)-1
    elif direction > 0:
        girth_index += 1
        if girth_index >= len(measures_parts_girths):
            girth_index = 0
    if girth_index >= measures_parts_girths: # It happens
        girth_index = len(measures_parts_girths)-1
    measure_name = measures_parts_girths[girth_index]
    # Now we seek and keep the values in the MeshHandling.
    mh = get_mesh_handling(file_name, obj)
    """if mh == None: # Because obj == None
        return None"""
    hist = mh.get_mesh_history(measure_name)
    if hist == None:
        hist = mh.create_mesh_history(measure_name)
        # The history is created, so we copy values from file
        file_girth_value = current_measures_file[file_name]["measures"][measure_name]
        hist.set('VERTEX', file_girth_value)
    # return the History
    return hist

# POINTS or GIRTH
def get(type, direction=0):
    if type == 'POINTS':
        return get_two_points(direction)
    elif type == 'GIRTH':
        return get_girth(direction)
    return None

def get_mesh_handling(file_name, obj=None):
    global mesh_handling_dict
    if not file_name in mesh_handling_dict:
        if obj == None:
            return None
        mesh_handling_dict[file_name] = mesh_ops.MeshHandling(file_name, obj)
    return mesh_handling_dict[file_name]

def recover():
    hist = get_two_points()
    if hist == None:
        hist = get_girth()
        if hist == None:
            return
    hist.recover('VERTEX')

# -------------------------------------
#            Properties
# -------------------------------------
recover_weights_first = True

def set_weights_layout(layout):
    global score_weights
    global recover_weights_first
    scn = bpy.context.scene
    if not recover_weights_first:
        txt = "mbcrea_"
        for name in score_weights:
            name = txt + name
            layout.prop(scn, name)
        layout.separator()
    layout.prop(scn, "mbcrea_recover_measures_weights", icon='RECOVER_LAST', toggle=1)

def save_weights():
    global current_measures_file
    global recover_weights_first
    if len(current_measures_file) < 1 or recover_weights_first:
        return
    keys = list(current_measures_file.keys())
    file = current_measures_file[keys[0]]
    score_weights = file["score_weights"]
    scn = bpy.context.scene
    # Now we do all stuff...
    score_weights["upperleg_length"] = round(scn.mbcrea_upperleg_length, 1)
    score_weights["buttock_depth_Y"] = round(scn.mbcrea_buttock_depth_Y, 1)
    score_weights["buttock_width_X"] = round(scn.mbcrea_buttock_width_X, 1)
    score_weights["wrist_girth"] = round(scn.mbcrea_wrist_girth, 1)
    score_weights["upperarm_axillary_girth"] = round(scn.mbcrea_upperarm_axillary_girth, 1)
    score_weights["lowerleg_length"] = round(scn.mbcrea_lowerleg_length, 1)
    score_weights["lowerleg_bottom_girth"] = round(scn.mbcrea_lowerleg_bottom_girth, 1)
    score_weights["head_height_Z"] = round(scn.mbcrea_head_height_Z, 1)
    score_weights["feet_length"] = round(scn.mbcrea_feet_length, 1)
    score_weights["lowerleg_calf_girth"] = round(scn.mbcrea_lowerleg_calf_girth, 1)
    score_weights["feet_heel_width"] = round(scn.mbcrea_feet_heel_width, 1)
    score_weights["torso_height_Z"] = round(scn.mbcrea_torso_height_Z, 1)
    score_weights["upperleg_top_girth"] = round(scn.mbcrea_upperleg_top_girth, 1)
    score_weights["shoulders_width"] = round(scn.mbcrea_shoulders_width, 1)
    score_weights["feet_height_Z"] = round(scn.mbcrea_feet_height_Z, 1)
    score_weights["waist_girth"] = round(scn.mbcrea_waist_girth, 1)
    score_weights["elbow_girth"] = round(scn.mbcrea_elbow_girth, 1)
    score_weights["head_width_X"] = round(scn.mbcrea_head_width_X, 1)
    score_weights["chest_depth_Y"] = round(scn.mbcrea_chest_depth_Y, 1)
    score_weights["neck_girth"] = round(scn.mbcrea_neck_girth, 1)
    score_weights["forearm_length"] = round(scn.mbcrea_forearm_length, 1)
    score_weights["head_length"] = round(scn.mbcrea_head_length, 1)
    score_weights["buttock_height_Z"] = round(scn.mbcrea_buttock_height_Z, 1)
    score_weights["hands_length"] = round(scn.mbcrea_hands_length, 1)
    score_weights["hands_width"] = round(scn.mbcrea_hands_width, 1)
    score_weights["chest_girth"] = round(scn.mbcrea_chest_girth, 1)
    score_weights["upperarm_length"] = round(scn.mbcrea_upperarm_length, 1)
    score_weights["feet_width"] = round(scn.mbcrea_feet_width, 1)
    score_weights["body_height_Z"] = round(scn.mbcrea_body_height_Z, 1)
    score_weights["neck_height_Z"] = round(scn.mbcrea_neck_height_Z, 1)
    score_weights["upperleg_bottom_girth"] = round(scn.mbcrea_upperleg_bottom_girth, 1)
    score_weights["buttock_girth"] = round(scn.mbcrea_buttock_girth, 1)
    score_weights["chest_width_X"] = round(scn.mbcrea_chest_width_X, 1)

def weights_update(self, context):
    scn = context.scene
    if not scn.mbcrea_recover_measures_weights:
        return
    global current_measures_file
    global recover_weights_first
    recover_weights_first = False
    scn.mbcrea_recover_measures_weights = False
    if len(current_measures_file) < 1:
        return
    keys = list(current_measures_file.keys())
    file = current_measures_file[keys[0]]
    score_weights = file["score_weights"]
    # Now we do all stuff...
    scn.mbcrea_upperleg_length = score_weights["upperleg_length"]
    scn.mbcrea_buttock_depth_Y = score_weights["buttock_depth_Y"]
    scn.mbcrea_buttock_width_X = score_weights["buttock_width_X"]
    scn.mbcrea_wrist_girth = score_weights["wrist_girth"]
    scn.mbcrea_upperarm_axillary_girth = score_weights["upperarm_axillary_girth"]
    scn.mbcrea_lowerleg_length = score_weights["lowerleg_length"]
    scn.mbcrea_lowerleg_bottom_girth = score_weights["lowerleg_bottom_girth"]
    scn.mbcrea_head_height_Z = score_weights["head_height_Z"]
    scn.mbcrea_feet_length = score_weights["feet_length"]
    scn.mbcrea_lowerleg_calf_girth = score_weights["lowerleg_calf_girth"]
    scn.mbcrea_feet_heel_width = score_weights["feet_heel_width"]
    scn.mbcrea_torso_height_Z = score_weights["torso_height_Z"]
    scn.mbcrea_upperleg_top_girth = score_weights["upperleg_top_girth"]
    scn.mbcrea_shoulders_width = score_weights["shoulders_width"]
    scn.mbcrea_feet_height_Z = score_weights["feet_height_Z"]
    scn.mbcrea_waist_girth = score_weights["waist_girth"]
    scn.mbcrea_elbow_girth = score_weights["elbow_girth"]
    scn.mbcrea_head_width_X = score_weights["head_width_X"]
    scn.mbcrea_chest_depth_Y = score_weights["chest_depth_Y"]
    scn.mbcrea_neck_girth = score_weights["neck_girth"]
    scn.mbcrea_forearm_length = score_weights["forearm_length"]
    scn.mbcrea_head_length = score_weights["head_length"]
    scn.mbcrea_buttock_height_Z = score_weights["buttock_height_Z"]
    scn.mbcrea_hands_length = score_weights["hands_length"]
    scn.mbcrea_hands_width = score_weights["hands_width"]
    scn.mbcrea_chest_girth = score_weights["chest_girth"]
    scn.mbcrea_upperarm_length = score_weights["upperarm_length"]
    scn.mbcrea_feet_width = score_weights["feet_width"]
    scn.mbcrea_body_height_Z = score_weights["body_height_Z"]
    scn.mbcrea_neck_height_Z = score_weights["neck_height_Z"]
    scn.mbcrea_upperleg_bottom_girth = score_weights["upperleg_bottom_girth"]
    scn.mbcrea_buttock_girth = score_weights["buttock_girth"]
    scn.mbcrea_chest_width_X = score_weights["chest_width_X"]

bpy.types.Scene.mbcrea_upperleg_length = bpy.props.FloatProperty(
    name="upperleg_length", min=0.0, max=3.0, soft_min=0.0,
    soft_max=3.0, precision=1, step=500, default=1.0,
    subtype='FACTOR')

bpy.types.Scene.mbcrea_buttock_depth_Y = bpy.props.FloatProperty(
    name="buttock_depth_Y", min=0.0, max=3.0, soft_min=0.0,
    soft_max=3.0, precision=1, step=500, default=1.0,
    subtype='FACTOR')

bpy.types.Scene.mbcrea_buttock_width_X = bpy.props.FloatProperty(
    name="buttock_width_X", min=0.0, max=3.0, soft_min=0.0,
    soft_max=3.0, precision=1, step=500, default=1.0,
    subtype='FACTOR')

bpy.types.Scene.mbcrea_wrist_girth = bpy.props.FloatProperty(
    name="wrist_girth", min=0.0, max=3.0, soft_min=0.0,
    soft_max=3.0, precision=1, step=500, default=1.0,
    subtype='FACTOR')

bpy.types.Scene.mbcrea_upperarm_axillary_girth = bpy.props.FloatProperty(
    name="upperarm_axillary_girth", min=0.0, max=3.0, soft_min=0.0,
    soft_max=3.0, precision=1, step=500, default=3.0,
    subtype='FACTOR')

bpy.types.Scene.mbcrea_lowerleg_length = bpy.props.FloatProperty(
    name="lowerleg_length", min=0.0, max=3.0, soft_min=0.0,
    soft_max=3.0, precision=1, step=500, default=1.0,
    subtype='FACTOR')

bpy.types.Scene.mbcrea_lowerleg_bottom_girth = bpy.props.FloatProperty(
    name="lowerleg_bottom_girth", min=0.0, max=3.0, soft_min=0.0,
    soft_max=3.0, precision=1, step=500, default=3.0,
    subtype='FACTOR')

bpy.types.Scene.mbcrea_head_height_Z = bpy.props.FloatProperty(
    name="head_height_Z", min=0.0, max=3.0, soft_min=0.0,
    soft_max=3.0, precision=1, step=500, default=1.0,
    subtype='FACTOR')

bpy.types.Scene.mbcrea_feet_length = bpy.props.FloatProperty(
    name="feet_length", min=0.0, max=3.0, soft_min=0.0,
    soft_max=3.0, precision=1, step=500, default=0.5,
    subtype='FACTOR')

bpy.types.Scene.mbcrea_lowerleg_calf_girth = bpy.props.FloatProperty(
    name="lowerleg_calf_girth", min=0.0, max=3.0, soft_min=0.0,
    soft_max=3.0, precision=1, step=500, default=3.0,
    subtype='FACTOR')

bpy.types.Scene.mbcrea_feet_heel_width = bpy.props.FloatProperty(
    name="feet_heel_width", min=0.0, max=3.0, soft_min=0.0,
    soft_max=3.0, precision=1, step=500, default=0.5,
    subtype='FACTOR')

bpy.types.Scene.mbcrea_torso_height_Z = bpy.props.FloatProperty(
    name="torso_height_Z", min=0.0, max=3.0, soft_min=0.0,
    soft_max=3.0, precision=1, step=500, default=1.0,
    subtype='FACTOR')

bpy.types.Scene.mbcrea_upperleg_top_girth = bpy.props.FloatProperty(
    name="upperleg_top_girth", min=0.0, max=3.0, soft_min=0.0,
    soft_max=3.0, precision=1, step=500, default=3.0,
    subtype='FACTOR')

bpy.types.Scene.mbcrea_shoulders_width = bpy.props.FloatProperty(
    name="shoulders_width", min=0.0, max=3.0, soft_min=0.0,
    soft_max=3.0, precision=1, step=500, default=2.0,
    subtype='FACTOR')

bpy.types.Scene.mbcrea_feet_height_Z = bpy.props.FloatProperty(
    name="feet_height_Z", min=0.0, max=3.0, soft_min=0.0,
    soft_max=3.0, precision=1, step=500, default=0.5,
    subtype='FACTOR')

bpy.types.Scene.mbcrea_waist_girth = bpy.props.FloatProperty(
    name="waist_girth", min=0.0, max=3.0, soft_min=0.0,
    soft_max=3.0, precision=1, step=500, default=3.0,
    subtype='FACTOR')

bpy.types.Scene.mbcrea_elbow_girth = bpy.props.FloatProperty(
    name="elbow_girth", min=0.0, max=3.0, soft_min=0.0,
    soft_max=3.0, precision=1, step=500, default=3.0,
    subtype='FACTOR')

bpy.types.Scene.mbcrea_head_width_X = bpy.props.FloatProperty(
    name="head_width_X", min=0.0, max=3.0, soft_min=0.0,
    soft_max=3.0, precision=1, step=500, default=1.0,
    subtype='FACTOR')

bpy.types.Scene.mbcrea_chest_depth_Y = bpy.props.FloatProperty(
    name="chest_depth_Y", min=0.0, max=3.0, soft_min=0.0,
    soft_max=3.0, precision=1, step=500, default=1.0,
    subtype='FACTOR')

bpy.types.Scene.mbcrea_neck_girth = bpy.props.FloatProperty(
    name="neck_girth", min=0.0, max=3.0, soft_min=0.0,
    soft_max=3.0, precision=1, step=500, default=0.5,
    subtype='FACTOR')

bpy.types.Scene.mbcrea_forearm_length = bpy.props.FloatProperty(
    name="forearm_length", min=0.0, max=3.0, soft_min=0.0,
    soft_max=3.0, precision=1, step=500, default=1.0,
    subtype='FACTOR')

bpy.types.Scene.mbcrea_head_length = bpy.props.FloatProperty(
    name="head_length", min=0.0, max=3.0, soft_min=0.0,
    soft_max=3.0, precision=1, step=500, default=1.0,
    subtype='FACTOR')

bpy.types.Scene.mbcrea_buttock_height_Z = bpy.props.FloatProperty(
    name="buttock_height_Z", min=0.0, max=3.0, soft_min=0.0,
    soft_max=3.0, precision=1, step=500, default=1.0,
    subtype='FACTOR')

bpy.types.Scene.mbcrea_hands_length = bpy.props.FloatProperty(
    name="hands_length", min=0.0, max=3.0, soft_min=0.0,
    soft_max=3.0, precision=1, step=500, default=0.5,
    subtype='FACTOR')

bpy.types.Scene.mbcrea_hands_width = bpy.props.FloatProperty(
    name="hands_width", min=0.0, max=3.0, soft_min=0.0,
    soft_max=3.0, precision=1, step=500, default=0.5,
    subtype='FACTOR')

bpy.types.Scene.mbcrea_chest_girth = bpy.props.FloatProperty(
    name="chest_girth", min=0.0, max=3.0, soft_min=0.0,
    soft_max=3.0, precision=1, step=500, default=3.0,
    subtype='FACTOR')

bpy.types.Scene.mbcrea_upperarm_length = bpy.props.FloatProperty(
    name="upperarm_length", min=0.0, max=3.0, soft_min=0.0,
    soft_max=3.0, precision=1, step=500, default=1.0,
    subtype='FACTOR')

bpy.types.Scene.mbcrea_feet_width = bpy.props.FloatProperty(
    name="feet_width", min=0.0, max=3.0, soft_min=0.0,
    soft_max=3.0, precision=1, step=500, default=0.5,
    subtype='FACTOR')

bpy.types.Scene.mbcrea_body_height_Z = bpy.props.FloatProperty(
    name="body_height_Z", min=0.0, max=3.0, soft_min=0.0,
    soft_max=3.0, precision=1, step=500, default=1.0,
    subtype='FACTOR')

bpy.types.Scene.mbcrea_neck_height_Z = bpy.props.FloatProperty(
    name="neck_height_Z", min=0.0, max=3.0, soft_min=0.0,
    soft_max=3.0, precision=1, step=500, default=1.0,
    subtype='FACTOR')

bpy.types.Scene.mbcrea_upperleg_bottom_girth = bpy.props.FloatProperty(
    name="upperleg_bottom_girth", min=0.0, max=3.0, soft_min=0.0,
    soft_max=3.0, precision=1, step=500, default=3.0,
    subtype='FACTOR')

bpy.types.Scene.mbcrea_buttock_girth = bpy.props.FloatProperty(
    name="buttock_girth", min=0.0, max=3.0, soft_min=0.0,
    soft_max=3.0, precision=1, step=500, default=3.0,
    subtype='FACTOR')

bpy.types.Scene.mbcrea_chest_width_X = bpy.props.FloatProperty(
    name="chest_width_X", min=0.0, max=3.0, soft_min=0.0,
    soft_max=3.0, precision=1, step=500, default=1.0,
    subtype='FACTOR')

bpy.types.Scene.mbcrea_recover_measures_weights = bpy.props.BoolProperty(
    name="Recover last save",
    default=False,
    update=weights_update)