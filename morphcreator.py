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
import numpy
from . import algorithms
from . import file_ops


body_parts = [("AB", "Abdomen", ""),
   ("AR", "Armpit", ""),
   ("AM", "Arms", ""),
   ("BO", "Body", ""),
   ("CH", "Cheeks", ""),
   ("CE", "Chest", ""),
   ("CI", "Chin", ""),
   ("EA", "Ears", ""),
   ("EL", "Elbows", ""),
   ("EX", "Expressions", ""),
   ("EY", "Eyebrows", ""),
   ("EL", "Eyelids", ""),
   ("EE", "Eyes", ""),
   ("FA", "Face", ""),
   ("FT", "Fantasy", ""),
   ("FE", "Feet", ""),
   ("FO", "Forehead", ""),
   ("HA", "Hands", ""),
   ("HE", "Head", ""),
   ("JA", "Jaw", ""),
   ("LE", "Legs", ""),
   ("MO", "Mouth", ""),
   ("NE", "Neck", ""),
   ("NO", "Nose", ""),
   ("PE", "Pelvis", ""),
   ("SH", "Shoulders", ""),
   ("ST", "Stomach", ""),
   ("TO", "Torso", ""),
   ("WA", "Waist", ""),
   ("WR", "Wrists", "")]

spectrum = [("GE", "Gender", "For all males / females"),
   ("ET", "Ethnic group", "For a specific ethnic group")]

min_max = [("MI", "min", "0"), ("MA", "max", "1")]

morphs_names = ["", "", 0]
#0 = get_model_and_gender()
#1 = get_body_type()
#2 = the number for save files

vertices_lists = [[], []]
#0 base vertices.
#1 Sculpted vertices.

modifiers_for_combined = ["", [], []]
# variable for creating combined morphs
# 1st value is the name
# 2nd list of body parts
# 3rd list of corresponding min/max

# Below = Variables for copy/move/delete utilities.
current_cmd_morph_file = ""
gender_cmd_morphs_files = []
body_type_cmd_morphs_files = []
cmd_categories_in_file = []
cmd_morphs_in_category = []
# Below:
# Keys = Name of files.
# Values = dict of morphs files
#   Keys = cmd_morphName (with category)
#   Values = morphName (with category)
properties_for_cmd = {}

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------------
#    All methods to help creating morph names
# ------------------------------------------------------------------------
def get_body_parts(key = None):
    if key == None:
        return body_parts
    return algorithms.get_enum_property_item(key, body_parts)

def get_spectrum(key = None):
    if key == None:
        return spectrum
    return algorithms.get_enum_property_item(key, spectrum)

def get_min_max(key = None):
    if key == None:
        return min_max
    return algorithms.get_enum_property_item(key, min_max)

# ------------------------------------------------------------------------
#    All methods to help creating file names
# ------------------------------------------------------------------------

def init_morph_names_database():
    global morphs_names
    global modifiers_for_combined
    global gender_cmd_morphs_files
    global body_type_cmd_morphs_files
    global properties_for_cmd
    morphs_names[0] = ""
    morphs_names[1] = ""
    morphs_names[2] = 0
    modifiers_for_combined[0] = ""
    modifiers_for_combined[1].clear()
    modifiers_for_combined[2].clear()
    gender_cmd_morphs_files.clear()
    body_type_cmd_morphs_files.clear()
    properties_for_cmd.clear()
    
def get_model_and_gender():
    if len(morphs_names[0]) == 0:
        obj = bpy.context.view_layer.objects.active
        # Dirty, but SOMETIMES for an unknown reason,
        # algorithms.get_template_model(obj) returns None.
        # Tried to reproduce the bug, without success.
        try:
            temp = algorithms.get_template_model(obj).split("_")
        except:
            return "Bug"
        morphs_names[0] = temp[1] + "_" + temp[2] + "_morphs"
    return morphs_names[0]

def get_body_type():
    if len(morphs_names[1]) == 0:
        morphs_names[1] = bpy.context.scene.mblab_character_name
    return morphs_names[1]

def get_next_number():
    morphs_names[2] += 1
    return str(morphs_names[2]).zfill(3)
# ------------------------------------------------------------------------
#    All methods/classes to help creating morphs
# ------------------------------------------------------------------------

#0 base vertices.
#1 Sculpted vertices.
def set_vertices_list(index, list):
    vertices_lists[index] = list

def get_vertices_list(index):
    return vertices_lists[index]

def create_vertices_list(raw_vertices):
    if raw_vertices == []:
        return []
    bpy.ops.object.mode_set(mode='OBJECT')
    #vertices to store in a convenient way.
    vertices_count = len(raw_vertices)
    stored_vertices = numpy.empty(vertices_count * 3)
    raw_vertices.foreach_get('co', stored_vertices)
    stored_vertices.shape = (vertices_count, 3)
    stored_vertices = numpy.around(stored_vertices, decimals=5)
    return stored_vertices

def create_vertices_list_from_list(vertices_list):
    #useless, just for reminder...
    array = numpy.array(vertices_list)
    return array

def are_points_different(point_a, point_b):
    #compare 2 lists ( under form [a, b, c, n...] )
    #NO security...
    for i in range(len(point_a)):
        if point_a[i] != point_b[i]:
            return True
    return False

def insert_number_in_list(list, index=0, start=0):
    #Insert a number from 'start' in each sub-list at index 'index'. No step here.
    #in MB-Lab the index used is the physical index of the list (not sure)
    #NO deep checks...
    #And at the end, the method is useless, except, maybe, for debugging.
    if len(list) == 0:
        return []
    list = list[:]
    for item in list:
        item[index:index] = [start]
        start += 1
    return list

def substract_vertices_lists(list_a, list_b):
    #Substract content of list_b by list_a
    list_a = numpy.around(list_a, decimals=4).tolist()
    list_b = numpy.around(list_b, decimals=4).tolist()
    length = len(list_a)
    if length != len(list_b) or not are_points_different(list_a, list_b):
        return []
    return_list = [0]*3
    for i in range(length):
        return_list[i] = list_b[i] - list_a[i]
    return numpy.around(return_list, decimals=4).tolist()

def substract_with_index(list_a, list_b):
    length = len(list_a)
    if length == 0 or length != len(list_b):
        return []
    return_list = []
    for i in range(length):
        substract = substract_vertices_lists(list_a[i], list_b[i])
        if len(substract) > 0:
            substract[0:0] = [i]
            return_list.append(substract)
    return return_list

def get_all_morph_files(data_path, data_type_path, body_type):
    #Get all files in morphs directory, without standard ones.
    #Used when the engine loads morphs librairies, here the user ones.
    #Can be used for both types of files : gender and specific type.
    dir = os.path.join(data_path, data_type_path)
    found_files = []
    body_type_split = body_type.split('_')[:2]
    for item in os.listdir(dir):
        if item != body_type and item.count("extra") < 1:
            if item.split('_')[:2] == body_type_split:
                found_files += [os.path.join(dir, item)]
    return found_files

# ------------------------------------------------------------------------
#    All methods/classes to help creating combined morphs
# ------------------------------------------------------------------------

def get_combined_morph_name():
    return modifiers_for_combined[0]

# Answer if the morph "name" is already part of a combined morph or not.
def is_modifier_combined_morph(humanoid, name="", category=""):
    if name == "" or category == "":
        return True # Just in case...
    cat = humanoid.get_category(category)
    modif = cat.get_modifier(name)
    if modif == None:
        return True
    return False

# A special and dirty function to help and simplify __init__
def secure_modifier_name(enum_items, items):
    check_name = algorithms.get_enum_property_item(enum_items, items)
    try:
        temp = check_name.split("_")[1]
    except:
        return "###_###"
    return check_name

# Store the combined morph elements for
# updating the model and save the morph
def set_modifiers_for_combined_morphs(final_name="", morphs_name=[], minmax=[]):
    global modifiers_for_combined
    modifiers_for_combined[0] = final_name
    modifiers_for_combined[1] = morphs_name
    for i in range(len(minmax)):
        if len(minmax[i]) > 0:
            if minmax[i] == "min":
                minmax[i] = 0
            else:
                minmax[i] = 1
        else:
            minmax[i] = 0.5
    modifiers_for_combined[2] = minmax

def update_for_combined_morphs(humanoid):
    global modifiers_for_combined
    if len(modifiers_for_combined[0]) < 1 or humanoid == None:
        return
    obj = humanoid.get_object()
    names = modifiers_for_combined[1]
    minmax = modifiers_for_combined[2]
    for i in range(len(names)):
        for prop in humanoid.character_data:
            if str(prop) == names[i]:
                setattr(obj, prop, minmax[i])
    humanoid.sync_character_data_to_obj_props()
    humanoid.update_character()
    
# ------------------------------------------------------------------------
#    All methods/classes to help creating phenotypes
# ------------------------------------------------------------------------

def is_phenotype_exists(body_type, name):
    if len(body_type) < 1 or len(name) < 1:
        return False
    try:
        path = os.path.join(file_ops.get_data_path(), "phenotypes", body_type+"_ptypes")
        for database_file in os.listdir(path):
            the_item, extension = os.path.splitext(database_file)
            if the_item == name:
                return True
    except:
        return False
    return False

def save_phenotype(path, humanoid):
    # Save all expression morphs as a new face expression
    # in its dedicated file.
    # If file already exists, it's replaced.
    logger.info("Exporting character to {0}".format(file_ops.simple_path(path)))
    obj = humanoid.get_object()
    char_data = {"structural": dict()}

    if obj:
        for prop in humanoid.character_data.keys():
            if humanoid.character_data[prop] != 0.5 and not prop.startswith("Expressions_"):
                char_data["structural"][prop] = round(humanoid.character_data[prop], 2)
        
        with open(path, "w") as j_file:
            json.dump(char_data, j_file, indent=2)
        j_file.close()

# ------------------------------------------------------------------------
#    All methods/classes to help creating presets
# ------------------------------------------------------------------------

def is_preset_exists(preset_folder, name):
    if len(preset_folder) < 1 or len(name) < 1:
        return False
    try:
        path = os.path.join(file_ops.get_data_path(), "presets", preset_folder)
        for database_file in os.listdir(path):
            the_item, extension = os.path.splitext(database_file)
            if the_item == name:
                return True
    except:
        return False
    return False

def save_preset(filepath, humanoid, integrate_material=False):
    logger.info("Exporting character to {0}".format(file_ops.simple_path(filepath)))
    obj = humanoid.get_object()
    char_data = {"manuellab_vers": humanoid.lab_vers, "structural": dict(), "metaproperties": dict(), "materialproperties": dict(), "materialproperties": dict()}

    if obj:
        # Structural
        for prop in humanoid.character_data.keys():
            if humanoid.character_data[prop] != 0.5 and not prop.startswith("Expressions_"):
                char_data["structural"][prop] = round(humanoid.character_data[prop], 4)
        # metaproperties
        for meta_data_prop in humanoid.character_metaproperties.keys():
            char_data["metaproperties"][meta_data_prop] = round(humanoid.character_metaproperties[meta_data_prop], 2)
        # materiel properties
        if integrate_material:
            mat_param = humanoid.mat_engine.get_material_parameters()
            for mat_prop in mat_param.keys():
                char_data["materialproperties"][mat_prop] = round(mat_param[mat_prop], 4)
        # File
        with open(filepath, "w") as j_file:
            json.dump(char_data, j_file, indent=2)
        j_file.close()

# ------------------------------------------------------------------------
#    All methods to move/copy/delete morphs
# ------------------------------------------------------------------------

def init_cmd_tools():
    global current_cmd_morph_file
    global gender_cmd_morphs_files
    global body_type_cmd_morphs_files
    global properties_for_cmd
    current_cmd_morph_file = ""
    gender_cmd_morphs_files.clear()
    body_type_cmd_morphs_files.clear()
    properties_for_cmd.clear()
    
# Create tuples for UI.
def get_gender_type_files(humanoid, type, with_new=False):
    gender, body_type = get_all_compatible_files(humanoid)
    return_list = []
    if type == "Gender":
        for file in gender:
            return_list.append((file+".json", file, file))
        if with_new:
            return_list.append(("NEW", "New file", "Add a new file"))
        return return_list
    else:
        for file in body_type:
            return_list.append((file+".json", file, file))
        if with_new:
            return_list.append(("NEW", "New file", "Add a new file"))
        return return_list
        
# return all compatible files
# return : gender, body_type
def get_all_compatible_files(humanoid):
    # humanoid will be useful later,
    # when for each humanoid you will have a dedicated
    # data directory...
    global gender_cmd_morphs_files
    global body_type_cmd_morphs_files
    global properties_for_cmd
    
    if humanoid == None:
        return gender_cmd_morphs_files, body_type_cmd_morphs_files
    if len(gender_cmd_morphs_files) > 0 or len(body_type_cmd_morphs_files) > 0:
        return gender_cmd_morphs_files, body_type_cmd_morphs_files
    properties_for_cmd.clear()
    path = os.path.join(file_ops.get_data_path(), "morphs")
    list_dir = os.listdir(path)
    split_name = []
    for file in list_dir:
        split_name = file.split("_")
        try:
            if split_name[0] == "m" or split_name[0] == "f" or split_name[0] == "u":
                body_type_cmd_morphs_files.append(file.split(".")[0])
            else:
                gender_cmd_morphs_files.append(file.split(".")[0])
            properties_for_cmd[file] = {}
        except:
            logger.info("File {0} not valid for morphs".format(file))
    gender_cmd_morphs_files = sorted(gender_cmd_morphs_files)
    body_type_cmd_morphs_files = sorted(body_type_cmd_morphs_files)
    return gender_cmd_morphs_files, body_type_cmd_morphs_files

def get_cmd_properties(file):
    global properties_for_cmd
    if len(properties_for_cmd[file]) < 1:
        content = get_morph_file_raw_content(file)
        tmp = properties_for_cmd[file] # to clear the code...
        key = ""
        morph_name = ""
        splitted = ""
        for morph in content.keys():
            splitted = morph.split("_")
            morph_name = splitted[0] + "_" + splitted[1]
            key = "cmd_" + morph_name # The key, used later for setattr
            if not key in tmp:
                tmp[key] = morph_name + "_"
    return properties_for_cmd[file]
    
def get_all_cmd_attr_names(humanoid):
    global properties_for_cmd
    if len(properties_for_cmd) < 1:
        get_all_compatible_files(humanoid)
    complete_files = properties_for_cmd.keys()
    return_properties = []
    props = []
    for file in complete_files:
        props = get_cmd_properties(file)
        for prop in props.keys():
            if not prop in return_properties:
                return_properties.append(prop)
    return return_properties
    
# Get all keys, sorted, no doubles, of all categories for morphs in the file.
# User give the content of the file.
def get_morph_file_categories(file_name):
    global cmd_categories_in_file
    
    if len(cmd_categories_in_file) > 0:
        return cmd_categories_in_file
    categories = []
    tmp = ""
    prop_values = get_cmd_properties(file_name)
    for morph in prop_values.values():
        tmp = morph.split("_")[0]
        if tmp not in categories:
            categories.append(tmp)
            cmd_categories_in_file.append((tmp, tmp, tmp))
    cmd_categories_in_file = sorted(cmd_categories_in_file)
    return cmd_categories_in_file

def get_morphs_in_category(file, category):
    global properties_for_cmd
    global cmd_morphs_in_category
    
    if len(cmd_morphs_in_category) > 0:
        return cmd_morphs_in_category
    content = properties_for_cmd[file]
    splitted = ""
    for key, value in content.items():
        splitted = value.split("_")[0]
        if splitted == category and not key in cmd_morphs_in_category:
            cmd_morphs_in_category.append(key)
    cmd_morphs_in_category = sorted(cmd_morphs_in_category)
    return cmd_morphs_in_category


# Trick to avoid the file to be loaded constantly.
# Must be used to open a file for copy/move/delete/rename.
def update_cmd_file(file_name): #OK, checked.
    global current_cmd_morph_file
    global cmd_categories_in_file
    global cmd_morphs_in_category
    
    if file_name == None:
        current_cmd_morph_file = ""
        cmd_categories_in_file.clear()
        cmd_morphs_in_category.clear()
        return
    if current_cmd_morph_file != file_name:
        current_cmd_morph_file = file_name
        cmd_categories_in_file.clear()
        cmd_morphs_in_category.clear()

def update_cmd_morphs():
    global cmd_morphs_in_category
    cmd_morphs_in_category.clear()

# Should not be used directly outside this file.
def get_morph_file_raw_content(file_name):
    path = os.path.join(file_ops.get_data_path(), "morphs", file_name)
    return file_ops.load_json_data(path)

# Should not be used directly outside this file.
def save_morph_file_raw_content(file_name, data):
    path = os.path.join(file_ops.get_data_path(), "morphs", file_name)
    file_ops.save_json_data(path, data)

# return all cmd_morphs that are selected via GUI
# The returned values are under form "Category_morphName"
def get_selected_cmd_morphs(source_file, obj):
    if len(properties_for_cmd[source_file]) < 1:
        get_cmd_properties(source_file)
    selected_morphs_list = []
    for key, value in properties_for_cmd[source_file].items():
        if hasattr(obj, key) and getattr(obj, key):
            selected_morphs_list.append(value)
    return sorted(selected_morphs_list)

# Reset all selected morphs
def reset_cmd_morphs(obj):
    cmd_to_reset = []
    for content in properties_for_cmd.values():
        for key in content.keys():
            if hasattr(obj, key) and getattr(obj, key) and not key in cmd_to_reset:
                cmd_to_reset.append(key)
    for reset in cmd_to_reset:
        setattr(obj, reset, False)
    
# Return all morphs from a file that are selected in the GUI.
# A dict is returned with the morphs and their content.
def get_morphs_list(source_file, obj):
    selected_morphs_list = get_selected_cmd_morphs(source_file, obj)
    output_morphs_list = {}
    if len(selected_morphs_list) < 1:
        return output_morphs_list
    content_file = get_morph_file_raw_content(source_file)
    for key, value in content_file.items():
        for morph_name in selected_morphs_list:
            if key.startswith(morph_name):
                output_morphs_list[key] = value
    return output_morphs_list

# Do the copy/move/delete operations from input_file to output_file.
# copy = False and delete = False ==> rename, indexes must match for old->new name
def cmd_morphs_action(input_name, output_name=None, morphs_names=[], new_name="", copy=True, delete=False):
    if morphs_names == None or len(morphs_names) < 1:
        return
    input_file = get_morph_file_raw_content(input_name)
    if copy:
        if output_name == None:
            return
        output_file = get_morph_file_raw_content(output_name)
        if output_file == None:
            output_file = {}
        for morph in morphs_names:
            output_file[morph] = input_file[morph]
        save_morph_file_raw_content(output_name, output_file)
    if delete:
        for morph in morphs_names:
            del input_file[morph]
        save_morph_file_raw_content(input_name, input_file)
    if not copy and not delete and len(new_name) > 0:
        splitted = []
        final_name = ""
        for name in morphs_names:
            splitted = name.split("_")
            final_name = splitted[0] + "_" + new_name + "_" + splitted[2]
            input_file[final_name] = input_file[name][:]
            del input_file[name]
        save_morph_file_raw_content(input_name, input_file)

def backup_morph_file(extra_name): #OK, checked.
    if len(current_cmd_morph_file) < 1:
        return
    path = os.path.join(file_ops.get_data_path(), "morphs", current_cmd_morph_file + "_" + extra_name + ".json")
    content_for_cmd = get_morph_file_raw_content(current_cmd_morph_file)
    file_ops.save_json_data(path, content_for_cmd)