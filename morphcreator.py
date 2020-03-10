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
    morphs_names[0] = ""
    morphs_names[1] = ""
    morphs_names[2] = 0
    modifiers_for_combined[0] = ""
    modifiers_for_combined[1] = []
    modifiers_for_combined[2] = []
    
def get_model_and_gender():
    if len(morphs_names[0]) == 0:
        obj = bpy.context.view_layer.objects.active
        temp = algorithms.get_template_model(obj).split("_")
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
    
