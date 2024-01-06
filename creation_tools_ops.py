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
import numpy
from . import algorithms
from . import file_ops
from . import numpy_ops
from . import utils
#from . import 

logger = logging.getLogger(__name__)

forbidden_directories = ["__pycache__", "data", "mb-lab_updater", "animations", "anthropometry",
    "bboxes", "expressions_comb", "expressions_morphs", "face_rig", "Hair_Data", "joints",
    "measures", "morphs", "Particle_Hair", "pgroups", "phenotypes", "poses", "presets",
    "textures", "transformations", "vertices", "vgroups", "hu_f_anthropometry",
    "hu_m_anthropometry", "anime_expressions", "human_expressions", "female_poses",
    "male_poses", "rest_poses"]

forbidden_names = ["human", "humans", "anime", "male", "female", "anthropometry", "bbox", "expressions",
    "exprs", "Expression", "morphs", "hair", "joints", "offset", "measures", "extra", "polygs", "ptypes",
    "poses", "rest", "specialtype", "anyme", "style", "type", "base", "transf", "verts",
    "vgroups", "muscles", "none"]

needed_directories = ["animations", "anthropometry", "bboxes", "expressions_comb",
    "expressions_morphs", "face_rig", "Hair_Data", "joints", "measures", "morphs",
    "Particle_Hair", "pgroups", "phenotypes", "poses", "presets", "textures", "transformations",
    "vertices", "vgroups"]

static_names = {
    "human": ["human", "hu"],
    "anime": ["anime", "an"],
    "male": ["male", "m_"],
    "female": ["female", "f_"],
    #"": [],
    }
#with complete name, short name.

static_genders = [("male", "male", "m_"),
   ("female", "female", "f_"),
   ("undefined", "undefined", "u_")]

# The content of the config file
config_content = {"templates_list": [], "character_list": [], "data_directory": ""}

# The content of blend file associated to project.
blend_file_content = None
blend_file_content_loaded = False

loaded_project = False
#--------------------------------------

def get_forbidden_directories():
    return forbidden_directories

def is_forbidden_directory(dir):
    return dir.lower() in forbidden_directories

def get_forbidden_names():
    return forbidden_names

def is_forbidden_name(name):
    return name.lower() in forbidden_names

def get_static_names():
    return static_names

def get_static_genders():
    return static_genders

#--------------------------------------

def create_needed_directories(name=""):
    if name == None or name == "":
        logger.critical("!WARNING! Name doesn't exist.")
        return
    elif is_forbidden_name(name):
        logger.critical("!WARNING! Name is forbidden.")
        return
    path = os.path.join(os.path.dirname(os.path.realpath(__file__)), name)
    if os.path.exists(path):
        logger.critical("!WARNING! Directory already exists.")
    for sub_dir in needed_directories:
        try:
            os.makedirs(os.path.join(path, sub_dir), mode=0o777)
        except FileExistsError:
            logger.warning("Directory " + sub_dir + " already exists. Skipped.")

def set_data_directory(dir):
    global config_content
    config_content["data_directory"] = dir

def get_data_directory():
    global config_content
    return config_content["data_directory"]

def get_project_directory():
    global config_content
    addon_directory = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(addon_directory, config_content["data_directory"])
    
def save_config():
    global config_content
    if config_content["data_directory"] == "" or config_content["data_directory"] == "data":
        return
    addon_directory = os.path.dirname(os.path.realpath(__file__))
    file_name = os.path.join(addon_directory, config_content["data_directory"], config_content["data_directory"] + "_config.json")
    # Save of the content, except data directory
    temp = config_content.copy()
    del temp["data_directory"]
    with open(file_name, "w") as j_file:
        json.dump(temp, j_file, indent=2)

def load_config(config_name):
    global loaded_project
    global config_content
    path = os.path.join(os.path.dirname(os.path.realpath(__file__)), config_name)
    if os.path.exists(path):
        file_name = os.path.join(path, config_name + "_config.json")
        config_content = file_ops.load_json_data(file_name, "Load config file")
        config_content["data_directory"] = config_name
        loaded_project = True

# User never add a complete content. He always add a single value led
# by a key.
# Important : Before adding content in a base (like "human_female_base")
# or an body type (like "f_ca01"), the key must be added in
# "templates_list" or "character_list" before.
def add_content(key, key_in, content):
    global config_content
    if key == "":
        return
    # Now we figure out what we're talking about.
    if key == "data_directory":
        pass
    elif key == "templates_list" or key == "character_list":
        if not content in config_content[key]:
            config_content[key].append(content)
    elif key in config_content["templates_list"]:
        if not key in config_content:
            config_content[key] = {
                "description": "", "template_model": "",
                "template_polygons": "", "name": key,
                "vertices": 0, "faces": 0, "label": ""}
        if key_in != None:
            config_content[key][key_in] = content
    elif key in config_content["character_list"]:
        if not key in config_content:
            config_content[key] = {
                "description": "", "template_model": "", "name": key,
                "label": "", "texture_albedo": "", "texture_bump": "",
                "texture_displacement": "", "texture_eyes": "",
                "texture_tongue_albedo": "", "texture_teeth_albedo": "",
                "texture_nails_albedo": "", "texture_eyelash_albedo": "",
                "texture_frecklemask": "", "texture_blush": "", 
                "texture_sebum": "", "texture_lipmap": "", 
                "texture_roughness": "", "texture_iris_color": "",
                "texture_iris_bump": "", "texture_sclera_color": "",
                "texture_translucent_mask": "", "texture_sclera_mask": "",
                "morphs_extra_file": "", "shared_morphs_file": "",
                "shared_morphs_extra_file": "", "bounding_boxes_file": "",
                "proportions_folder": "", "joints_base_file": "",
                "joints_offset_file": "", "measures_file": "",
                "presets_folder": "", "transformations_file": "",
                "vertexgroup_base_file": "", "vertexgroup_muscle_file": ""}
        if not key_in in config_content[key]:
            config_content[key][key_in] = content
        elif key_in != None:
            config_content[key][key_in] = content

def set_content(key, content):
    global config_content
    if key == None or key == "":
        return
    config_content[key] = content

def delete_content(key):
    global config_content
    if key == None or key == "":
        return
    del config_content[key]

def get_content(key, key_in):
    global config_content
    if key == None:
        return ""
    if key in config_content["templates_list"] or key in config_content["character_list"]:
        if not key in config_content:
            add_content(key, None, "")
    if key in config_content:
        content = config_content[key]
        if type(content) is dict and key_in != None:
            return content[key_in]
        else:
            return content
    return ""
    
def init_config():
    global config_content
    global loaded_project
    global blend_file_content_loaded
    # init collection
    c = bpy.data.collections.get('MB_LAB_Character')
    if c is not None and blend_file_content != None:
        for name in blend_file_content[1]:
            obj = algorithms.get_object_by_name(name)
            bpy.data.objects.remove(obj)
        bpy.data.collections.remove(c)
    # Init variables
    config_content = {"templates_list": [], "character_list": [], "data_directory": ""}
    loaded_project = False
    blend_file_content_loaded = False
    
def is_project_loaded():
    global loaded_project
    return loaded_project

def is_directories_created():
    global config_content
    addon_directory = os.path.dirname(os.path.realpath(__file__))
    dirpath = os.path.join(addon_directory, config_content["data_directory"])
    if os.path.isdir(dirpath):
        return True
    return False

def is_config_created():
    global config_content
    dirpath = os.path.join(get_project_directory(), config_content["data_directory"] + "_config.json")
    if os.path.isfile(dirpath):
        return True
    return False

def delete_template(name):
    global config_content
    if name in config_content:
        del config_content[name]
    if name in config_content["templates_list"]:
        config_content["templates_list"].remove(name)

def delete_character(name):
    global config_content
    if name in config_content:
        del config_content[name]
    if name in config_content["character_list"]:
        config_content["character_list"].remove(name)

def get_file_list(dir, file_type="json"):
    path = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        get_data_directory(), dir)
    return [('NONE', 'Unknown', 'Unknown file for the moment')] + file_ops.get_items_list(path, file_type, with_type=True)

def get_presets_folder_list():
    dir_list = get_content("templates_list", None)
    if len(dir_list) < 1:
        dir_list["Please create templates"]
    return [('NONE', 'Unknown', 'Unknown folder for the moment')] + algorithms.create_enum_property_items(dir_list, tip_length=20)
    
# ------------------------------------------------------------------------
#    All methods dedicated to the content of blend file
# ------------------------------------------------------------------------

def is_blend_file_exist():
    global config_content
    if len(config_content["data_directory"]) < 1:
        return False
    dirpath = os.path.join(get_project_directory(), "humanoid_library.blend")
    if os.path.isfile(dirpath):
        return True
    return False

def get_blend_file_pathname():
    return os.path.join(get_project_directory(), "humanoid_library.blend")

def get_blend_file_name():
    return "humanoid_library.blend"

def load_blend_file():
    global blend_file_content
    global blend_file_content_loaded
    
    if blend_file_content_loaded:
        return blend_file_content
    
    if is_blend_file_exist():
        lib_filepath = get_blend_file_pathname()
    else:
        logger.critical("Blend file does not exist or is not under /" + get_project_directory() + "/")
        return []
    # Import objects name from library
    with bpy.data.libraries.load(lib_filepath) as (data_from, data_to):
        blend_file_content = [data_from, data_from.objects, data_from.meshes]
    # Import objects name from library
    file_ops.append_object_from_library(lib_filepath, data_from.objects)
    blend_file_content_loaded = True
    return blend_file_content
    
def blend_is_loaded():
    global blend_file_content_loaded
    return blend_file_content_loaded
    
def get_meshes_names():
    global blend_file_content
    global blend_file_content_loaded
    if blend_file_content_loaded:
        return blend_file_content[2]
    return []

def get_objects_names():
    global blend_file_content
    global blend_file_content_loaded
    if blend_file_content_loaded:
        return blend_file_content[1]
    return []

def get_vertices_faces_count(model_name):
    global blend_file_content
    global blend_file_content_loaded
    if not blend_file_content_loaded:
        return 0, 0
    obj = bpy.data.meshes[model_name]
    return len(obj.vertices.values()), len(obj.polygons.values())
# ------------------------------------------------------------------------
#    All methods to return tuples for drop-down lists
# ------------------------------------------------------------------------

def get_templates_list():
    global config_content
    return_list = [("NEW", "New template...", "Create a new template")]
    if len(config_content["templates_list"]) < 1:
        return return_list
    for tl in config_content["templates_list"]:
        return_list.append((tl, tl, tl))
    return return_list

def get_character_list(with_new=True):
    global config_content
    return_list = []
    if with_new:
        return_list = [("NEW", "New character...", "Create a new character")]
    elif len(config_content["character_list"]) < 1:
        return [('NONE', "No character", "No character created")]
    for cl in config_content["character_list"]:
        return_list.append((cl, cl, cl))
    return return_list

def get_meshes_list():
    global blend_file_content
    global blend_file_content_loaded
    if not blend_file_content_loaded:
        return [("NONE", "No blend file", "Must load a blend file to work")]
    return_list = []
    for mesh in blend_file_content[2]:
        return_list.append((mesh, mesh, "mesh : " + mesh))
    return return_list

def is_mesh_compatible(mesh, chara_name="", model_name=""):
    if mesh == None:
        return False
    length = len(mesh.data.vertices)
    final_name = model_name
    if len(chara_name) > 0:
        content = get_content(chara_name, "template_model")
        for temp in get_content("templates_list", None):
            sub_content = get_content(temp, "template_model")
            if sub_content == content:
                final_name = temp
                break
    if len(final_name) > 0:
        content = get_content(final_name, "vertices")
        if content == length:
            return True
        return False
    return False