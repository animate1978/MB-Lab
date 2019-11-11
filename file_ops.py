# MB-Lab
#
# MB-Lab fork website : https://github.com/animate1978/MB-Lab
#
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

import logging

import os
import json
import array
import time

import mathutils
import bpy

from . import utils
from .utils import get_object_parent


logger = logging.getLogger(__name__)


def is_writeable(filepath):
    try:
        with open(filepath, 'w'):
            return True
    except IOError:
        logger.warning("Writing permission denied for %s", filepath)
    return False


def get_data_path():
    addon_directory = os.path.dirname(os.path.realpath(__file__))
    data_dir = os.path.join(addon_directory, "data")
    logger.info("Looking for the retarget data in the folder %s...", simple_path(data_dir))

    if not os.path.isdir(data_dir):
        logger.critical("Tools data not found. Please check your Blender addons directory.")
        return None

    return data_dir


def get_configuration():
    data_path = get_data_path()

    if data_path:
        configuration_path = os.path.join(data_path, "characters_config.json")
        if os.path.isfile(configuration_path):
            return load_json_data(configuration_path, "Characters definition")

    logger.critical("Configuration database not found. Please check your Blender addons directory.")
    return None


def get_blendlibrary_path():
    data_path = get_data_path()
    if data_path:
        return os.path.join(data_path, "humanoid_library.blend")

    logger.critical("Models library not found. Please check your Blender addons directory.")
    return None


def simple_path(input_path, use_basename=True, max_len=50):
    """
    Return the last part of long paths
    """
    if use_basename:
        return os.path.basename(input_path)

    if len(input_path) > max_len:
        return f"[Trunked]..{input_path[len(input_path)-max_len:]}"

    return input_path

def exists_database(lib_path):
    result = False
    if simple_path(lib_path) != "":
        if os.path.isdir(lib_path):
            if os.listdir(lib_path):
                for database_file in os.listdir(lib_path):
                    _, extension = os.path.splitext(database_file)
                    if "json" in extension or "bvh" in extension:
                        result = True
                    else:
                        logger.warning("Unknow file extension in %s", simple_path(lib_path))

        else:
            logger.warning("data path %s not found", simple_path(lib_path))
    return result

def load_json_data(json_path, description=None):
    try:
        time1 = time.time()
        with open(json_path, "r") as j_file:
            j_database = json.load(j_file)
            if not description:
                logger.info("Json database %s loaded in %s secs",
                            simple_path(json_path), time.time()-time1)
            else:
                logger.info("%s loaded from %s in %s secs",
                            description, simple_path(json_path), time.time()-time1)
            return j_database
    except IOError:
        if simple_path(json_path) != "":
            logger.warning("File not found: %s", simple_path(json_path))
    except json.JSONDecodeError:
        logger.warning("Errors in json file: %s", simple_path(json_path))
    return None

def load_vertices_database(vertices_path):
    vertices = []
    verts = load_json_data(vertices_path, "Vertices data")
    if verts:
        for vert_co in verts:
            vertices.append(mathutils.Vector(vert_co))
    return vertices


def set_verts_coords_from_file(obj, vertices_path):
    new_vertices = load_vertices_database(vertices_path)
    if obj:
        if len(new_vertices) == len(obj.data.vertices):
            for i, vert in enumerate(obj.data.vertices):
                vert.co = new_vertices[i]


def generate_items_list(folderpath, file_type="json"):
    items_list = []
    if os.path.isdir(folderpath):
        for database_file in os.listdir(folderpath):
            the_item, extension = os.path.splitext(database_file)
            if file_type in extension:
                if the_item not in items_list:
                    the_descr = "Load and apply {0} from lab library".format(the_item)
                    items_list.append((the_item, the_item, the_descr))
        items_list.sort()
    return items_list







# Append humanoid objects

def import_object_from_lib(lib_filepath, name, final_name=None, stop_import=True):
    if name != "":
        if stop_import:
            logger.info("Appending object %s from %s", name, simple_path(lib_filepath))
            if name in bpy.data.objects:
                logger.warning("Object %s already in the scene. Import stopped", name)
                return None

            if final_name:
                if final_name in bpy.data.objects:
                    logger.warning("Object %s already in the scene. Import stopped", final_name)
                    return None

        append_object_from_library(lib_filepath, [name])
        obj = get_object_by_name(name)
        if obj:
            logger.info("Object '%s' imported", name)
            if final_name:
                obj.name = final_name
                logger.info("Object '%s' renamed as '%s'", name, final_name)
            return obj

        logger.warning("Object %s not found in library %s", name, simple_path(lib_filepath))
    return None


def append_object_from_library(lib_filepath, obj_names, suffix=None):

    try:
        with bpy.data.libraries.load(lib_filepath) as (data_from, data_to):
            if suffix:
                names_to_append = [name for name in data_from.objects if suffix in name]
                data_to.objects = names_to_append
            else:
                names_to_append = obj_names
                data_to.objects = [name for name in names_to_append if name in data_from.objects]
    except OSError:
        logger.critical("lib %s not found", lib_filepath)

    for obj in data_to.objects:
        link_to_collection(obj)
        obj_parent = utils.get_object_parent(obj)
        if obj_parent:
            link_to_collection(obj_parent)


def append_mesh_from_library(lib_filepath, mesh_names, suffix=None):

    try:
        with bpy.data.libraries.load(lib_filepath) as (data_from, data_to):
            if suffix:
                names_to_append = [name for name in data_from.meshes if suffix in name]
                data_to.meshes = names_to_append
            else:
                names_to_append = mesh_names
                data_to.meshes = [name for name in names_to_append if name in data_from.meshes]
    except OSError:
        logger.critical("lib %s not found", lib_filepath)

def read_object_names_from_library(lib_filepath):
    try:
        with bpy.data.libraries.load(lib_filepath) as (data_from, data_to):
            for name in data_from.objects:
                print("OBJ_LIB: ", name)
    except OSError:
        logger.critical("lib %s not found", lib_filepath)

def link_to_collection(obj):
    # sanity check
    if obj.name not in bpy.data.objects:
        logger.error("Cannot link obj %s because it's not in bpy.data.objects", obj.name)
        return

    collection_name = 'MB_LAB_Character'
    c = bpy.data.collections.get(collection_name)
    scene = bpy.context.scene
    # collection is already created
    if c is not None:
        if obj.name not in c.objects:
            c.objects.link(obj)
        else:
            logger.warning("The object %s is already linked to the scene", obj.name)
    else:
        # create the collection, link collection to scene and link obj to collection
        c = bpy.data.collections.new(collection_name)
        scene.collection.children.link(c)
        c.objects.link(obj)

def is_armature_linked(obj, armat):
    if obj.type == 'MESH':
        for modfr in obj.modifiers:
            if modfr.type == 'ARMATURE' and modfr.object == armat:
                return True
    return False

def get_object_by_name(name):
    return bpy.data.objects.get(name)


def select_object_by_name(name):
    obj = get_object_by_name(name)
    if obj:
        obj.select_set(True)

def get_newest_object(existing_obj_names):
    for obj in bpy.data.objects:
        name = obj.name
        if name not in existing_obj_names:
            return get_object_by_name(name)
    return None





def json_booleans_to_python(value):
    return value == 0


def load_image(filepath):
    if os.path.isfile(filepath):
        logger.info("Loading image %s", os.path.basename(filepath))
        img = bpy.data.images.load(filepath, check_existing=True)
        img.reload()
    else:
        logger.info("Image %s not found", os.path.basename(filepath))

def get_image(name):
    if name:
        if name in bpy.data.images:
            # Some check for log
            if bpy.data.images[name].source == "FILE":
                if os.path.basename(bpy.data.images[name].filepath) != name:
                    logger.warning("Image named %s is from file: %s",
                                   name, os.path.basename(bpy.data.images[name].filepath))
            return bpy.data.images[name]
        logger.warning("Getting image failed. Image %s not found in bpy.data.images", name)
        return None

    logger.warning("Getting image failed. Image name is %s", name)
    return None

def save_image(name, filepath, fileformat='PNG'):
    img = get_image(name)
    scn = bpy.context.scene
    if img:
        current_format = scn.render.image_settings.file_format
        scn.render.image_settings.file_format = fileformat
        img.save_render(filepath)
        scn.render.image_settings.file_format = current_format
    else:
        logger.warning(
            "The image %s cannot be saved because it's not present in bpy.data.images.", name)


def new_texture(name, image=None):
    if name not in bpy.data.textures:
        _new_texture = bpy.data.textures.new(name, type='IMAGE')
    else:
        _new_texture = bpy.data.textures[name]
    if image:
        _new_texture.image = image
    return _new_texture