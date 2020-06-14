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

# MB-Lab Imports

import logging

import time, ntpath
import datetime
import json
import os
import numpy
#from pathlib import Path
from math import radians, degrees

import bpy
from bpy.app.handlers import persistent
from bpy_extras.io_utils import ExportHelper, ImportHelper

from . import addon_updater_ops
from . import algorithms
from . import animationengine
from . import creation_tools_ops
from . import expressionengine
from . import expressionscreator
from . import facerig
from . import file_ops
from . import hairengine
from . import humanoid
from . import humanoid_rotations
from . import morphcreator
from . import node_ops
from . import numpy_ops
from . import object_ops
from . import proxyengine
from . import transfor
from . import utils
from . import preferences


logger = logging.getLogger(__name__)

# MB-Lab Blender Info
# 3/22 added new version number to MB-Lab, internal dev purposes

bl_info = {
    "name": "MB-Lab",
    "author": "Manuel Bastioni, MB-Lab Community",
    "version": (1, 7, 8, 42),
    "blender": (2, 81, 16),
    "location": "View3D > Tools > MB-Lab",
    "description": "A complete lab for character creation",
    "warning": "",
    'wiki_url': "https://mb-lab-docs.readthedocs.io/en/latest/index.html",
    'tracker_url': 'https://github.com/animate1978/MB-Lab/issues',
    "category": "Characters"
}

mblab_humanoid = humanoid.Humanoid(bl_info["version"])
mblab_retarget = animationengine.RetargetEngine()
mblab_shapekeys = expressionengine.ExpressionEngineShapeK()
mblab_proxy = proxyengine.ProxyEngine()
mbcrea_expressionscreator = expressionscreator.ExpressionsCreator()
mbcrea_transfor = transfor.Transfor(mblab_humanoid)

gui_status = "NEW_SESSION"
gui_err_msg = ""

# GUI panels for MB-Lab
gui_active_panel = None
gui_active_panel_middle = None
gui_active_panel_display = None
gui_active_panel_fin = None

# GUI panels for MB-Dev
gui_active_panel_first = None
gui_active_panel_second = None
gui_active_panel_third = None

#Delete List
CY_Hshader_remove = []
UN_shader_remove = []

# BEGIN
def start_lab_session():
    global mblab_humanoid
    global gui_status, gui_err_msg

    logger.info("Start_the lab session...")
    scn = bpy.context.scene
    character_identifier = scn.mblab_character_name
    rigging_type = "base"
    if scn.mblab_use_ik:
        rigging_type = "ik"
    if scn.mblab_use_muscle:
        rigging_type = "muscle"
    if scn.mblab_use_muscle and scn.mblab_use_ik:
        rigging_type = "muscle_ik"

    lib_filepath = file_ops.get_blendlibrary_path()

    obj = None
    is_existing = False
    is_obj = algorithms.looking_for_humanoid_obj()

    if is_obj[0] == "ERROR":
        gui_status = "ERROR_SESSION"
        gui_err_msg = is_obj[1]
        return

    if is_obj[0] == "NO_OBJ":
        base_model_name = mblab_humanoid.characters_config[character_identifier]["template_model"]
        obj = file_ops.import_object_from_lib(lib_filepath, base_model_name, character_identifier)
        obj["manuellab_vers"] = bl_info["version"]
        obj["manuellab_id"] = character_identifier
        obj["manuellab_rig"] = rigging_type

    if is_obj[0] == "FOUND":
        obj = file_ops.get_object_by_name(is_obj[1])
        character_identifier = obj["manuellab_id"]
        rigging_type = obj["manuellab_rig"]
        is_existing = True

    if not obj:
        logger.critical("Init failed...")
        gui_status = "ERROR_SESSION"
        gui_err_msg = "Init failed. Check the log file"
    else:
        mblab_humanoid.init_database(obj, character_identifier, rigging_type)
        if mblab_humanoid.has_data:
            gui_status = "ACTIVE_SESSION"

            if scn.mblab_use_cycles or scn.mblab_use_eevee:
                if scn.mblab_use_cycles:
                    scn.render.engine = 'CYCLES'
                else:
                    scn.render.engine = 'BLENDER_EEVEE'
                if scn.mblab_use_lamps:

                    object_ops.add_lighting()

            else:
                scn.render.engine = 'BLENDER_WORKBENCH'

            logger.info("Rendering engine now is %s", scn.render.engine)
            init_morphing_props(mblab_humanoid)
            init_categories_props(mblab_humanoid)
            init_measures_props(mblab_humanoid)
            init_restposes_props(mblab_humanoid)
            init_presets_props(mblab_humanoid)
            init_ethnic_props(mblab_humanoid)
            init_metaparameters_props(mblab_humanoid)
            init_material_parameters_props(mblab_humanoid)
            mblab_humanoid.update_materials()

            if is_existing:
                logger.info("Re-init the character %s", obj.name)
                mblab_humanoid.store_mesh_in_cache()
                mblab_humanoid.reset_mesh()
                mblab_humanoid.recover_prop_values_from_obj_attr()
                mblab_humanoid.restore_mesh_from_cache()
            else:
                mblab_humanoid.reset_mesh()
                mblab_humanoid.update_character(mode="update_all")
            
            # All inits for creation tools.
            morphcreator.init_morph_names_database()
            mbcrea_expressionscreator.reset_expressions_items()
            mbcrea_transfor.set_scene(scn)
            init_cmd_props(mblab_humanoid)
            # End for that.
            algorithms.deselect_all_objects()
    algorithms.remove_censors()


@persistent
def check_manuelbastionilab_session(dummy):
    global mblab_humanoid
    global gui_status, gui_err_msg
    scn = bpy.context.scene
    if mblab_humanoid:
        # init_femaleposes_props()
        # init_maleposes_props()
        gui_status = "NEW_SESSION"
        is_obj = algorithms.looking_for_humanoid_obj()
        if is_obj[0] == "FOUND":
            # gui_status = "RECOVERY_SESSION"
            # if scn.do_not_ask_again:
            start_lab_session()
        if is_obj[0] == "ERROR":
            gui_status = "ERROR_SESSION"
            gui_err_msg = is_obj[1]
            return


bpy.app.handlers.load_post.append(check_manuelbastionilab_session)


def sync_character_to_props():
    # It's important to avoid problems with Blender undo system
    global mblab_humanoid
    mblab_humanoid.sync_character_data_to_obj_props()
    mblab_humanoid.update_character()


def realtime_update(self, context):
    """
    Update the character while the prop slider moves.
    """
    global mblab_humanoid
    if mblab_humanoid.bodydata_realtime_activated:
        # time1 = time.time()
        scn = bpy.context.scene
        mblab_humanoid.update_character(category_name=scn.morphingCategory, mode="update_realtime")
        #Teto
        # Dirty, but I didn't want to touch the code too much.
        # I tried things, but I am pretty sure that they would
        # bring inconsistencies when changing model without
        # quitting Blender.
        # So we always update expressions category, because same
        # prop are used in "facial expression creator".
        if scn.morphingCategory != "Expressions":
            mblab_humanoid.update_character(category_name="Expressions", mode="update_realtime")
        #End Teto
        mblab_humanoid.sync_gui_according_measures()
        # print("realtime_update: {0}".format(time.time()-time1))

def age_update(self, context):
    global mblab_humanoid
    time1 = time.time()
    if mblab_humanoid.metadata_realtime_activated:
        time1 = time.time()
        mblab_humanoid.calculate_transformation("AGE")


def mass_update(self, context):
    global mblab_humanoid
    if mblab_humanoid.metadata_realtime_activated:
        mblab_humanoid.calculate_transformation("FAT")


def tone_update(self, context):
    global mblab_humanoid
    if mblab_humanoid.metadata_realtime_activated:
        mblab_humanoid.calculate_transformation("MUSCLE")


def modifiers_update(self, context):
    sync_character_to_props()


def set_cycles_render_engine(self, context):
    if context.scene.mblab_use_cycles:
        context.scene.mblab_use_eevee = False


def set_eevee_render_engine(self, context):
    if context.scene.mblab_use_eevee:
        context.scene.mblab_use_cycles = False


def preset_update(self, context):
    """
    Update the character while prop slider moves
    """
    scn = bpy.context.scene
    global mblab_humanoid
    obj = mblab_humanoid.get_object()
    filepath = os.path.join(
        mblab_humanoid.presets_path,
        "".join([obj.preset, ".json"]))
    mblab_humanoid.load_character(filepath, mix=scn.mblab_mix_characters)


def ethnic_update(self, context):
    scn = bpy.context.scene
    global mblab_humanoid
    obj = mblab_humanoid.get_object()
    filepath = os.path.join(
        mblab_humanoid.phenotypes_path,
        "".join([obj.ethnic, ".json"]))
    mblab_humanoid.load_character(filepath, mix=scn.mblab_mix_characters)


def material_update(self, context):
    global mblab_humanoid
    if mblab_humanoid.material_realtime_activated:
        mblab_humanoid.update_materials(update_textures_nodes=False)


def measure_units_update(self, context):
    global mblab_humanoid
    mblab_humanoid.sync_gui_according_measures()


def human_expression_update(self, context):
    global mblab_shapekeys
    scn = bpy.context.scene
    mblab_shapekeys.sync_expression_to_gui()


def restpose_update(self, context):
    global mblab_humanoid
    armature = mblab_humanoid.get_armature()
    filepath = os.path.join(
        mblab_humanoid.restposes_path,
        "".join([armature.rest_pose, ".json"]))
    mblab_retarget.load_pose(filepath, armature)


def malepose_update(self, context):
    global mblab_retarget
    armature = utils.get_active_armature()
    filepath = os.path.join(
        mblab_retarget.maleposes_path,
        "".join([armature.male_pose, ".json"]))
    mblab_retarget.load_pose(filepath, use_retarget=True)


def femalepose_update(self, context):
    global mblab_retarget
    armature = utils.get_active_armature()
    filepath = os.path.join(
        mblab_retarget.femaleposes_path,
        "".join([armature.female_pose, ".json"]))
    mblab_retarget.load_pose(filepath, use_retarget=True)


def init_morphing_props(humanoid_instance):
    for prop in humanoid_instance.character_data:
        setattr(
            bpy.types.Object,
            prop,
            bpy.props.FloatProperty(
                name=prop.split("_")[1],
                min=-5.0,
                max=5.0,
                soft_min=0.0,
                soft_max=1.0,
                precision=3,
                default=0.5,
                subtype='FACTOR',
                update=realtime_update))

def init_cmd_props(humanoid_instance):
    for prop in morphcreator.get_all_cmd_attr_names(humanoid_instance):
        setattr(
            bpy.types.Object,
            prop,
            bpy.props.BoolProperty(
                name=prop.split("_")[2],
                default=False))

def init_measures_props(humanoid_instance):
    for measure_name, measure_val in humanoid_instance.morph_engine.measures.items():
        setattr(
            bpy.types.Object,
            measure_name,
            bpy.props.FloatProperty(
                name=measure_name, min=0.0, max=500.0,
                subtype='FACTOR',
                default=measure_val))
    humanoid_instance.sync_gui_according_measures()

#Teto
def get_categories_enum(exclude=[]):
    categories_enum = []
    # All categories for "Body Measures"
    for category in mblab_humanoid.get_categories(exclude):
        categories_enum.append(
            (category.name, category.name, category.name))
    return categories_enum

def init_categories_props(humanoid_instance):
    bpy.types.Scene.morphingCategory = bpy.props.EnumProperty(
        items=get_categories_enum(),
        update=modifiers_update,
        name="Morphing categories")
    
    # Sub-categories for "Facial expressions"
    mbcrea_expressionscreator.set_expressions_modifiers(mblab_humanoid)
    sub_categories_enum = mbcrea_expressionscreator.get_expressions_sub_categories()
    
    bpy.types.Scene.expressionsSubCategory = bpy.props.EnumProperty(
        items=sub_categories_enum,
        update=modifiers_update,
        name="Expressions sub-categories")

    # Special properties used by transfor.Transfor
    bpy.types.Scene.transforMorphingCategory = bpy.props.EnumProperty(
        items=get_categories_enum(["Expressions"]),
        update=modifiers_update,
        name="Morphing categories")

#End Teto

def init_restposes_props(humanoid_instance):
    if humanoid_instance.exists_rest_poses_database():
        restpose_items = file_ops.generate_items_list(humanoid_instance.restposes_path)
        bpy.types.Object.rest_pose = bpy.props.EnumProperty(
            items=restpose_items,
            name="Rest pose",
            default=restpose_items[0][0],
            update=restpose_update)


def init_maleposes_props():
    global mblab_retarget
    if mblab_retarget.maleposes_exist:
        if not hasattr(bpy.types.Object, 'male_pose'):
            malepose_items = file_ops.generate_items_list(mblab_retarget.maleposes_path)
            bpy.types.Object.male_pose = bpy.props.EnumProperty(
                items=malepose_items,
                name="Male pose",
                default=malepose_items[0][0],
                update=malepose_update)


def init_femaleposes_props():
    global mblab_retarget
    if mblab_retarget.femaleposes_exist:
        if not hasattr(bpy.types.Object, 'female_pose'):
            femalepose_items = file_ops.generate_items_list(mblab_retarget.femaleposes_path)
            bpy.types.Object.female_pose = bpy.props.EnumProperty(
                items=femalepose_items,
                name="Female pose",
                default=femalepose_items[0][0],
                update=femalepose_update)


def init_expression_props():
    for expression_name in mblab_shapekeys.expressions_labels:
        if not hasattr(bpy.types.Object, expression_name):
            setattr(
                bpy.types.Object,
                expression_name,
                bpy.props.FloatProperty(
                    name=expression_name,
                    min=0.0,
                    max=1.0,
                    precision=3,
                    default=0.0,
                    subtype='FACTOR',
                    update=human_expression_update))


def init_presets_props(humanoid_instance):
    if humanoid_instance.exists_preset_database():
        preset_items = file_ops.generate_items_list(humanoid_instance.presets_path)
        bpy.types.Object.preset = bpy.props.EnumProperty(
            items=preset_items,
            name="Types",
            update=preset_update)


def init_ethnic_props(humanoid_instance):
    if humanoid_instance.exists_phenotype_database():
        ethnic_items = file_ops.generate_items_list(humanoid_instance.phenotypes_path)
        bpy.types.Object.ethnic = bpy.props.EnumProperty(
            items=ethnic_items,
            name="Phenotype",
            update=ethnic_update)


def init_metaparameters_props(humanoid_instance):
    for meta_data_prop in humanoid_instance.character_metaproperties.keys():
        upd_function = None

        if "age" in meta_data_prop:
            upd_function = age_update
        if "mass" in meta_data_prop:
            upd_function = mass_update
        if "tone" in meta_data_prop:
            upd_function = tone_update
        if "last" in meta_data_prop:
            upd_function = None

        if "last_" not in meta_data_prop:
            setattr(
                bpy.types.Object,
                meta_data_prop,
                bpy.props.FloatProperty(
                    name=meta_data_prop, min=-1.0, max=1.0,
                    precision=3,
                    default=0.0,
                    subtype='FACTOR',
                    update=upd_function))


def init_material_parameters_props(humanoid_instance):
    for material_data_prop, value in humanoid_instance.character_material_properties.items():
        setattr(
            bpy.types.Object,
            material_data_prop,
            bpy.props.FloatProperty(
                name=material_data_prop,
                min=0.0,
                max=1.0,
                precision=2,
                subtype='FACTOR',
                update=material_update,
                default=value))

def angle_update_0(self, context):
    global mblab_retarget
    scn = bpy.context.scene
    value = scn.mblab_rot_offset_0
    mblab_retarget.correct_bone_angle(0, value)


def angle_update_1(self, context):
    global mblab_retarget
    scn = bpy.context.scene
    value = scn.mblab_rot_offset_1
    mblab_retarget.correct_bone_angle(1, value)


def angle_update_2(self, context):
    global mblab_retarget
    scn = bpy.context.scene
    value = scn.mblab_rot_offset_2
    mblab_retarget.correct_bone_angle(2, value)


def get_character_items(self, context):
    items = []
    for obj in bpy.data.objects:
        if obj.type == 'MESH':
            if algorithms.get_template_model(obj) is not None:
                items.append((obj.name, obj.name, obj.name))
    return items


def get_proxy_items(self, context):
    items = []
    for obj in bpy.data.objects:
        if obj.type == 'MESH':
            if algorithms.get_template_model(obj) is None:
                items.append((obj.name, obj.name, obj.name))
    if len(items) == 0:
        items = [("NO_PROXY_FOUND", "No proxy found", "No proxy found")]
    return items


def get_proxy_items_from_library(self, context):
    items = mblab_proxy.assets_models
    return items


def update_proxy_library(self, context):
    mblab_proxy.update_assets_models()


def load_proxy_item(self, context):
    scn = bpy.context.scene
    mblab_proxy.load_asset(scn.mblab_assets_models)

#Choose Hair Colors
def hair_style_list(self, context):
    scn = bpy.context.scene
    if scn.mblab_use_cycles: #and context.scene.mblab_use_pHair:
        fileName = hairengine.get_hair_npz('CY_shader_presets.npz')
        data = node_ops.get_universal_dict(fileName)
        dat = data['arr_0'].tolist()
        items = dat
    else:
        fileName = hairengine.get_hair_npz('universal_hair_shader.npz')
        items = node_ops.get_universal_list(fileName)
    #[(identifier, name, description, icon, number)
    return [(i, i, i) for i in items]

# MB-Lab Properties

bpy.types.Scene.mblab_proxy_library = bpy.props.StringProperty(
    name="Library folder",
    description="Folder with assets blend files",
    default="",
    maxlen=1024,
    update=update_proxy_library,
    subtype='DIR_PATH')

bpy.types.Scene.mblab_fitref_name = bpy.props.EnumProperty(
    items=get_character_items,
    name="Character")

bpy.types.Scene.mblab_proxy_name = bpy.props.EnumProperty(
    items=get_proxy_items,
    name="Proxy")

bpy.types.Scene.mblab_final_prefix = bpy.props.StringProperty(
    name="Prefix",
    description="The prefix of names for finalized model, skeleton and materials. If none, it will be generated automatically",
    default="")

bpy.types.Scene.mblab_rot_offset_0 = bpy.props.FloatProperty(
    name="Tweak rot X",
    min=-1,
    max=1,
    precision=2,
    subtype='FACTOR',
    update=angle_update_0,
    default=0.0)

bpy.types.Scene.mblab_rot_offset_1 = bpy.props.FloatProperty(
    name="Tweak rot Y",
    min=-1,
    max=1,
    precision=2,
    subtype='FACTOR',
    update=angle_update_1,
    default=0.0)

bpy.types.Scene.mblab_rot_offset_2 = bpy.props.FloatProperty(
    name="Tweak rot Z",
    min=-1,
    max=1,
    precision=2,
    subtype='FACTOR',
    update=angle_update_2,
    default=0.0)

bpy.types.Scene.mblab_proxy_offset = bpy.props.FloatProperty(
    name="Offset",
    min=0,
    max=100,
    subtype='FACTOR',
    default=0)

bpy.types.Scene.mblab_proxy_threshold = bpy.props.FloatProperty(
    name="Influence",
    min=0,
    max=1000,
    default=20,
    subtype='FACTOR',
    description="Maximum distance threshold for proxy vertices to closely follow the body surface")

bpy.types.Scene.mblab_proxy_use_advanced = bpy.props.BoolProperty(
    name="Advanced",
    default=False,
    description="Use advanced options")

bpy.types.Scene.mblab_proxy_reverse_fit = bpy.props.BoolProperty(
    name="Reversed fitting",
    default=False,
    description="Refit the mesh from the character to the base mesh, as a step in converting a character-specific item to a generic proxy")

bpy.types.Scene.mblab_proxy_use_all_faces = bpy.props.BoolProperty(
    name="Use all faces",
    default=False,
    description="Use all base mesh faces for close fitting, including insides of the mouth etc")

bpy.types.Scene.mblab_proxy_no_smoothing = bpy.props.BoolProperty(
    name="Disable smoothing",
    default=False,
    description="Disable additional smoothing applied to the fitting results")

bpy.types.Scene.mblab_use_ik = bpy.props.BoolProperty(
    name="Use Inverse Kinematic",
    default=False,
    description="Use inverse kinematic armature")

bpy.types.Scene.mblab_use_muscle = bpy.props.BoolProperty(
    name="Use basic muscles",
    default=False,
    description="Use basic muscle armature")

bpy.types.Scene.mblab_remove_all_modifiers = bpy.props.BoolProperty(
    name="Remove modifiers",
    default=False,
    description="If checked, all the modifiers will be removed, except the armature (displacement, subdivision, corrective smooth, etc)")

bpy.types.Scene.mblab_use_cycles = bpy.props.BoolProperty(
    name="Use Cycles engine",
    default=True,
    update=set_cycles_render_engine,
    description="This is needed in order to use the skin editor and shaders (highly recommended)")

bpy.types.Scene.mblab_use_eevee = bpy.props.BoolProperty(
    name="Use EEVEE engine",
    default=False,
    update=set_eevee_render_engine,
    description="This is needed in order to use the skin editor and shaders")

bpy.types.Scene.mblab_use_lamps = bpy.props.BoolProperty(
    name="Use portrait studio lights",
    default=False,
    description="Add a set of lights optimized for portrait. Useful during the design of skin (recommended)")

bpy.types.Scene.mblab_show_measures = bpy.props.BoolProperty(
    name="Measurements",
    description="Show measures controls",
    update=modifiers_update)

bpy.types.Scene.mblab_measure_filter = bpy.props.StringProperty(
    name="Filter",
    default="",
    description="Filter the measures to show")

bpy.types.Scene.mblab_expression_filter = bpy.props.StringProperty(
    name="Filter",
    default="",
    description="Filter the expressions to show")

#Teto
def mbcrea_enum_expressions_items_update(self, context):
    return mbcrea_expressionscreator.get_expressions_items()
   

bpy.types.Scene.mbcrea_enum_expressions_items = bpy.props.EnumProperty(
    items=mbcrea_enum_expressions_items_update,
    name="",
    default=None,
    options={'ANIMATABLE'},
    )
#End Teto

bpy.types.Scene.mblab_mix_characters = bpy.props.BoolProperty(
    name="Mix with current",
    description="Mix templates")

bpy.types.Scene.mblab_template_name = bpy.props.EnumProperty(
    items=mblab_humanoid.template_types,
    name="Select",
    default="human_female_base")

bpy.types.Scene.mblab_character_name = bpy.props.EnumProperty(
    items=mblab_humanoid.humanoid_types,
    name="Select",
    default="f_af01")

bpy.types.Scene.mblab_assets_models = bpy.props.EnumProperty(
    items=get_proxy_items_from_library,
    update=load_proxy_item,
    name="Assets model")

bpy.types.Scene.mblab_transfer_proxy_weights = bpy.props.BoolProperty(
    name="Transfer weights from body to proxy (replace existing)",
    description="If the proxy has already rigging weights, they will be replaced with the weights projected from the character body",
    default=True)

bpy.types.Scene.mblab_save_images_and_backup = bpy.props.BoolProperty(
    name="Save images and backup character",
    description="Save all images from the skin shader and backup the character in json format",
    default=True)

bpy.types.Object.mblab_use_inch = bpy.props.BoolProperty(
    name="Inch",
    update=measure_units_update,
    description="Use inch instead of cm")

bpy.types.Scene.mblab_export_proportions = bpy.props.BoolProperty(
    name="Include proportions",
    description="Include proportions in the exported character file")

bpy.types.Scene.mblab_export_materials = bpy.props.BoolProperty(
    name="Include materials",
    default=True,
    description="Include materials in the exported character file")

bpy.types.Scene.mblab_show_texture_load_save = bpy.props.BoolProperty(
    name="Import-export images",
    description="Show controls to import and export texture images")

bpy.types.Scene.mblab_add_mask_group = bpy.props.BoolProperty(
    name="Add mask vertgroup",
    description="Create a new vertgroup and use it as mask the body under proxy.",
    default=False)

bpy.types.Scene.mblab_preserve_mass = bpy.props.BoolProperty(
    name="Mass",
    description="Preserve the current relative mass percentage")

bpy.types.Scene.mblab_preserve_height = bpy.props.BoolProperty(
    name="Height",
    description="Preserve the current character height")

bpy.types.Scene.mblab_preserve_tone = bpy.props.BoolProperty(
    name="Tone",
    description="Preserve the current relative tone percentage")

bpy.types.Scene.mblab_preserve_fantasy = bpy.props.BoolProperty(
    name="Fantasy",
    description="Preserve the current amount of fantasy morphs")

bpy.types.Scene.mblab_preserve_body = bpy.props.BoolProperty(
    name="Body",
    description="Preserve the body features")

bpy.types.Scene.mblab_preserve_face = bpy.props.BoolProperty(
    name="Face",
    description="Preserve the face features, but not the head shape")

bpy.types.Scene.mblab_preserve_phenotype = bpy.props.BoolProperty(
    name="Phenotype",
    description="Preserve characteristic traits, like people that are members of the same family")

bpy.types.Scene.mblab_set_tone_and_mass = bpy.props.BoolProperty(
    name="Use fixed tone and mass values",
    description="Enable the setting of fixed values for mass and tone using a slider UI")

bpy.types.Scene.mblab_body_mass = bpy.props.FloatProperty(
    name="Body mass",
    min=0.0,
    max=1.0,
    default=0.5,
    subtype='FACTOR',
    description="Preserve the current character body mass")

bpy.types.Scene.mblab_body_tone = bpy.props.FloatProperty(
    name="Body tone",
    min=0.0,
    max=1.0,
    default=0.5,
    subtype='FACTOR',
    description="Preserve the current character body tone")

bpy.types.Scene.mblab_morphing_spectrum = bpy.props.EnumProperty(
    items=morphcreator.get_spectrum(),
    name="Spectrum",
    default="GE")

bpy.types.Scene.mblab_morph_min_max = bpy.props.EnumProperty(
    items=morphcreator.get_min_max(),
    name="min/max",
    default="MA")

bpy.types.Scene.mblab_morphing_body_type = bpy.props.StringProperty(
    name="Ethnic group",
    description="Overide the ethnic group.\n4 letters, without f_ or m_.\nExample : af01\nLet empty to not overide",
    #default="",
    maxlen=4,
    subtype='FILE_NAME')

bpy.types.Scene.mblab_morphing_file_extra_name = bpy.props.StringProperty(
    name="Extra name",
    description="Typically it's the name of the author",
    default="pseudo",
    maxlen=1024,
    subtype='FILE_NAME')

bpy.types.Scene.mblab_incremental_saves = bpy.props.BoolProperty(
    name="Autosaves",
    description="Does an incremental save each time\n  the final save button is pressed.\nFrom 001 to 999\nCaution : returns to 001 between sessions")

bpy.types.Scene.mblab_morph_name = bpy.props.StringProperty(
    name="Name",
    description="Format : ExplicitPartMorphed\n(Without body part category)",
    default="",
    maxlen=1024,
    subtype='FILE_NAME')

bpy.types.Scene.mblab_body_part_name = bpy.props.EnumProperty(
    items=morphcreator.get_body_parts(),
    name="Body part",
    default="BO")


bpy.types.Scene.mblab_body_tone = bpy.props.FloatProperty(
    name="Body tone",
    min=0.0,
    max=1.0,
    default=0.5,
    subtype='FACTOR',
    description="Preserve the current character body mass")

bpy.types.Scene.mblab_random_engine = bpy.props.EnumProperty(
    items=[("LI", "Light", "Little variations from the standard"),
           ("RE", "Realistic", "Realistic characters"),
           ("NO", "Noticeable", "Very characterized people"),
           ("CA", "Caricature", "Engine for caricatures"),
           ("EX", "Extreme", "Extreme characters")],
    name="Engine",
    default="LI")

bpy.types.Scene.mblab_facs_rig = bpy.props.BoolProperty(
    name="Import FACS Rig")

bpy.types.Scene.mblab_copy_to_all_phenotype = bpy.props.BoolProperty(
    name="Apply to all Phenotype")
bpy.types.Scene.mblab_override_expressions = bpy.props.BoolProperty(
    name="Override Existing Expressions")

#Hair color Drop Down List
bpy.types.Scene.mblab_hair_color = bpy.props.EnumProperty(
    items=hair_style_list,
    name="Color Select",
    update=hair_style_list)

#Hair new color name
bpy.types.Scene.mblab_new_hair_color = bpy.props.StringProperty(
    name="Save Hair Color",
    default="",
    description="Enter name for new hair color")

# MB-Lab Operations

class ButtonParametersOff(bpy.types.Operator):
    bl_label = 'Body Measures'
    bl_idname = 'mbast.button_parameters_off'
    bl_description = 'Close details panel'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global gui_active_panel_middle
        gui_active_panel_middle = None
        return {'FINISHED'}


class ButtonParametersOn(bpy.types.Operator):
    bl_label = 'Body Measures'
    bl_idname = 'mbast.button_parameters_on'
    bl_description = 'Open details panel'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global gui_active_panel_middle
        gui_active_panel_middle = "parameters"
        sync_character_to_props()
        return {'FINISHED'}


class ButtonUtilitiesOff(bpy.types.Operator):
    bl_label = 'UTILITIES'
    bl_idname = 'mbast.button_utilities_off'
    bl_description = 'Close utilities panel'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global gui_active_panel_fin
        gui_active_panel_fin = None
        return {'FINISHED'}


class ButtonUtilitiesOn(bpy.types.Operator):
    bl_label = 'UTILITIES'
    bl_idname = 'mbast.button_utilities_on'
    bl_description = 'Open utilities panel'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global gui_active_panel_fin
        gui_active_panel_fin = "utilities"
        return {'FINISHED'}


class ButtonFaceRigOff(bpy.types.Operator):
    bl_label = 'FACE RIG'
    bl_idname = 'mbast.button_facerig_off'
    bl_description = 'Close face rig panel'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global gui_active_panel_fin
        gui_active_panel_fin = None
        return {'FINISHED'}


class ButtonFaceRigOn(bpy.types.Operator):
    bl_label = 'FACE RIG'
    bl_idname = 'mbast.button_facerig_on'
    bl_description = 'Open face rig panel'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global gui_active_panel_fin
        gui_active_panel_fin = "face_rig"
        return {'FINISHED'}


class ButtonExpressionsOff(bpy.types.Operator):
    bl_label = 'FACE EXPRESSIONS'
    bl_idname = 'mbast.button_expressions_off'
    bl_description = 'Close expressions panel'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global gui_active_panel_fin
        gui_active_panel_fin = None
        return {'FINISHED'}


class ButtonExpressionOn(bpy.types.Operator):
    bl_label = 'FACE EXPRESSIONS'
    bl_idname = 'mbast.button_expressions_on'
    bl_description = 'Open expressions panel'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global gui_active_panel_fin
        gui_active_panel_fin = "expressions"
        # sync_character_to_props()
        init_expression_props()
        return {'FINISHED'}


class ButtonRandomOff(bpy.types.Operator):
    bl_label = 'Random Generator'
    bl_idname = 'mbast.button_random_off'
    bl_description = 'Close random generator panel'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global gui_active_panel
        gui_active_panel = None
        return {'FINISHED'}


class ButtonRandomOn(bpy.types.Operator):
    bl_label = 'Random Generator'
    bl_idname = 'mbast.button_random_on'
    bl_description = 'Open random generator panel'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global gui_active_panel
        gui_active_panel = 'random'
        sync_character_to_props()
        return {'FINISHED'}

class ButtonStoreBaseBodyVertices(bpy.types.Operator):
    bl_label = 'Store base body vertices'
    bl_idname = 'mbast.button_store_base_vertices'
    bl_description = '!WARNING! UNDO UNAVAILABLE!!!'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        mode = bpy.context.active_object.mode
        vt = bpy.context.object.data.vertices
        bpy.ops.object.mode_set(mode='OBJECT')
        #vertices
        morphcreator.set_vertices_list(0, morphcreator.create_vertices_list(vt))
        return {'FINISHED'}
    #Teto
    #@classmethod
    #def get_stored_base_vertices(self):
    #    return morphcreator.set_vertices_list(0)
    #End Teto -> I think that this method is useless, because unused.

class ButtonSaveWorkInProgress(bpy.types.Operator):
    bl_label = 'Quick save wip'
    bl_idname = 'mbast.button_store_work_in_progress'
    bl_description = 'Name and location are automatic'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        mode = bpy.context.active_object.mode
        vt = bpy.context.object.data.vertices
        bpy.ops.object.mode_set(mode='OBJECT')
        #vertices
        morphcreator.set_vertices_list(1, morphcreator.create_vertices_list(vt))
        return {'FINISHED'}

    #Teto
    #@classmethod
    #def get_stored_actual_vertices(self):
    #    return morphcreator.set_vertices_list(1)
    #End Teto -> I think that this method is useless, because unused.

class FinalizeMorph(bpy.types.Operator):
    """
        NOW we're talking:
        - Checking that the base body exists.
        - Checking that the sculpted body exists.
        - Doing the substract between the two.
        - Creating the file name.
        - Creating the morph name.
        - Opening or creating the named file.
        - Adding or replacing the morph.
        - Close the file.
        - Profit.
    """
    bl_label = 'Finalize the morph'
    bl_idname = 'mbast.button_save_final_morph'
    filename_ext = ".json"
    bl_description = 'Finalize the morph, create or open the morphs file, replace or append new morph'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        scn = bpy.context.scene
        base = []
        sculpted = []

        if len(scn.mblab_morph_name) < 1:
            self.ShowMessageBox("Please choose a name for the morph ! No file saved", "Warning", 'ERROR')
            return {'FINISHED'}
        try:
            base = morphcreator.get_vertices_list(0)
        except:
            self.ShowMessageBox("Base vertices are not stored !", "Warning", 'ERROR')
            return {'FINISHED'}
        try:
            sculpted = morphcreator.get_vertices_list(1)
        except:
            self.ShowMessageBox("Changed vertices are not stored !", "Warning", 'ERROR')
            return {'FINISHED'}
        indexed_vertices = morphcreator.substract_with_index(base, sculpted)
        if len(indexed_vertices) < 1:
            self.ShowMessageBox("Models base / sculpted are equals ! No file saved", "Warning", 'INFO')
            return {'FINISHED'}
        #-------File name----------
        file_name = ""
        if scn.mblab_morphing_spectrum == "GE":
            #File name for whole gender, like human_female or anime_male.
            file_name = morphcreator.get_model_and_gender()
        else:
            splitted = algorithms.split_name(scn.mblab_morphing_body_type)
            if len(splitted) < 1:
                file_name = morphcreator.get_body_type() + "_morphs"
            else:
                file_name = morphcreator.get_body_type()[0:2] + splitted + "_morphs"
            if len(scn.mblab_morphing_file_extra_name) > 0:
                file_name = file_name + "_" + scn.mblab_morphing_file_extra_name
        if scn.mblab_incremental_saves:
            file_name = file_name + "_" + morphcreator.get_next_number()
        #-------Morph name----------
        morph_name = morphcreator.get_body_parts(scn.mblab_body_part_name) + "_" + scn.mblab_morph_name + "_" + morphcreator.get_min_max(scn.mblab_morph_min_max)
        #-------Morphs path----------
        file_path_name = os.path.join(file_ops.get_data_path(), "morphs", file_name + ".json")
        file = file_ops.load_json_data(file_path_name, "Try to load a morph file")
        if file == None:
            file = {}
        #---Creating new morph-------
        file[morph_name] = indexed_vertices
        file_ops.save_json_data(file_path_name, file)
        #----------------------------
        return {'FINISHED'}

    def ShowMessageBox(self, message = "", title = "Message Box", icon = 'INFO'):

        def draw(self, context):
            self.layout.label(text=message)
        bpy.context.window_manager.popup_menu(draw, title = title, icon = icon)

class SaveBodyAsIs(bpy.types.Operator, ExportHelper):
    """
        Save the model shown on screen.
    """
    bl_label = 'Save in a file all vertices of the actual model'
    bl_idname = 'mbast.button_save_body_as_is'
    filename_ext = ".json"
    filter_glob: bpy.props.StringProperty(default="*.json", options={'HIDDEN'},)
    bl_description = 'Save all vertices of the actual body shown on screen in a file.'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        mode = bpy.context.active_object.mode
        vt = bpy.context.object.data.vertices
        bpy.ops.object.mode_set(mode='OBJECT')
        vertices_to_save = morphcreator.create_vertices_list(vt)
        vertices_to_save = numpy.around(vertices_to_save, decimals=5).tolist()
        #--------------------
        file_ops.save_json_data(self.filepath, vertices_to_save)
        return {'FINISHED'}

class LoadBaseBody(bpy.types.Operator, ImportHelper):
    """
        Load the model as a base model.
    """
    bl_label = 'Load all vertices as a base model'
    bl_idname = 'mbast.button_load_base_body'
    filename_ext = ".json"
    filter_glob: bpy.props.StringProperty(default="*.json", options={'HIDDEN'},)
    bl_description = 'Load all vertices as a base body model.'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        mode = bpy.context.active_object.mode
        bpy.ops.object.mode_set(mode='OBJECT')
        file = file_ops.load_json_data(self.filepath, "Base model vertices")
        #--------------------
        morphcreator.set_vertices_list(0, numpy.array(file))
        return {'FINISHED'}

class LoadSculptedBody(bpy.types.Operator, ImportHelper):
    """
        Load the model as a sculpted model.
    """
    bl_label = 'Load all vertices as a sculpted model'
    bl_idname = 'mbast.button_load_sculpted_body'
    filename_ext = ".json"
    filter_glob: bpy.props.StringProperty(default="*.json", options={'HIDDEN'},)
    bl_description = 'Load all vertices as a sculpted body model.'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        mode = bpy.context.active_object.mode
        bpy.ops.object.mode_set(mode='OBJECT')
        file = file_ops.load_json_data(self.filepath, "Sculpted model vertices")
        #--------------------
        morphcreator.set_vertices_list(1, numpy.array(file))#.tolist())
        return {'FINISHED'}
#End Teto
class ButtonAutomodellingOff(bpy.types.Operator):
    bl_label = 'Automodelling Tools'
    bl_idname = 'mbast.button_automodelling_off'
    bl_description = 'Close automodelling panel'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global gui_active_panel
        gui_active_panel = None
        return {'FINISHED'}


class ButtonAutomodellingOn(bpy.types.Operator):
    bl_label = 'Automodelling Tools'
    bl_idname = 'mbast.button_automodelling_on'
    bl_description = 'Open automodelling panel'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global gui_active_panel
        gui_active_panel = 'automodelling'
        return {'FINISHED'}


class ButtonRestPoseOff(bpy.types.Operator):
    bl_label = 'Rest Pose'
    bl_idname = 'mbast.button_rest_pose_off'
    bl_description = 'Close rest pose panel'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global gui_active_panel_middle
        gui_active_panel_middle = None
        return {'FINISHED'}


class ButtonRestPoseOn(bpy.types.Operator):
    bl_label = 'Rest Pose'
    bl_idname = 'mbast.button_rest_pose_on'
    bl_description = 'Open rest pose panel'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global gui_active_panel_middle
        gui_active_panel_middle = 'rest_pose'
        return {'FINISHED'}


class ButtonAssetsOn(bpy.types.Operator):
    bl_label = 'ASSETS AND HAIR'
    bl_idname = 'mbast.button_assets_on'
    bl_description = 'Open assets and hair panel'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global gui_active_panel_fin
        gui_active_panel_fin = 'assets'
        return {'FINISHED'}


class ButtonAssetsOff(bpy.types.Operator):
    bl_label = 'ASSETS AND HAIR'
    bl_idname = 'mbast.button_assets_off'
    bl_description = 'Close assets and hair panel'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global gui_active_panel_fin
        gui_active_panel_fin = None
        return {'FINISHED'}


class ButtonPoseOff(bpy.types.Operator):
    bl_label = 'POSE AND ANIMATION'
    bl_idname = 'mbast.button_pose_off'
    bl_description = 'Close pose panel'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global gui_active_panel_fin
        gui_active_panel_fin = None
        return {'FINISHED'}

class ButtonPoseOn(bpy.types.Operator):
    bl_label = 'POSE AND ANIMATION'
    bl_idname = 'mbast.button_pose_on'
    bl_description = 'Open pose panel'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global gui_active_panel_fin
        init_femaleposes_props()
        init_maleposes_props()
        gui_active_panel_fin = 'pose'
        return {'FINISHED'}


class ButtonSkinOff(bpy.types.Operator):
    bl_label = 'Skin Editor'
    bl_idname = 'mbast.button_skin_off'
    bl_description = 'Close skin editor panel'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global gui_active_panel_middle
        gui_active_panel_middle = None
        return {'FINISHED'}


class ButtonSkinOn(bpy.types.Operator):
    bl_label = 'Skin Editor'
    bl_idname = 'mbast.button_skin_on'
    bl_description = 'Open skin editor panel'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global gui_active_panel_middle
        gui_active_panel_middle = 'skin'
        return {'FINISHED'}


class ButtonViewOptOff(bpy.types.Operator):
    bl_label = 'Display Options'
    bl_idname = 'mbast.button_display_off'
    bl_description = 'Close skin editor panel'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global gui_active_panel_display
        gui_active_panel_display = None
        return {'FINISHED'}


class ButtonViewOptOn(bpy.types.Operator):
    bl_label = 'Display Options'
    bl_idname = 'mbast.button_display_on'
    bl_description = 'Open skin editor panel'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global gui_active_panel_display
        gui_active_panel_display = 'display_opt'
        return {'FINISHED'}


class ButtonProxyFitOff(bpy.types.Operator):
    bl_label = 'PROXY FITTING'
    bl_idname = 'mbast.button_proxy_fit_off'
    bl_description = 'Close proxy panel'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global gui_active_panel_fin
        gui_active_panel_fin = None
        return {'FINISHED'}


class ButtonProxyFitOn(bpy.types.Operator):
    bl_label = 'PROXY FITTING'
    bl_idname = 'mbast.button_proxy_fit_on'
    bl_description = 'Open proxy panel'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global gui_active_panel_fin
        gui_active_panel_fin = 'proxy_fit'
        return {'FINISHED'}


class ButtonFilesOff(bpy.types.Operator):
    bl_label = 'File Tools'
    bl_idname = 'mbast.button_file_off'
    bl_description = 'Close file panel'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global gui_active_panel_display
        gui_active_panel_display = None
        return {'FINISHED'}


class ButtonFilesOn(bpy.types.Operator):
    bl_label = 'File Tools'
    bl_idname = 'mbast.button_file_on'
    bl_description = 'Open file panel'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global gui_active_panel_display
        gui_active_panel_display = 'file'
        return {'FINISHED'}


class ButtonFinalizeOff(bpy.types.Operator):
    bl_label = 'Finalize Tools'
    bl_idname = 'mbast.button_finalize_off'
    bl_description = 'Close finalize panel'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global gui_active_panel_display
        gui_active_panel_display = None
        return {'FINISHED'}


class ButtonFinalizeOn(bpy.types.Operator):
    bl_label = 'Finalize Tools'
    bl_idname = 'mbast.button_finalize_on'
    bl_description = 'Open finalize panel'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global gui_active_panel_display
        gui_active_panel_display = 'finalize'
        return {'FINISHED'}


class ButtonLibraryOff(bpy.types.Operator):
    bl_label = 'Character Library'
    bl_idname = 'mbast.button_library_off'
    bl_description = 'Close character library panel'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global gui_active_panel
        gui_active_panel = None
        return {'FINISHED'}


class ButtonLibraryOn(bpy.types.Operator):
    bl_label = 'Character Library'
    bl_idname = 'mbast.button_library_on'
    bl_description = 'Open character library panel'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global gui_active_panel
        gui_active_panel = 'library'
        return {'FINISHED'}


class ButtonFinalizedCorrectRot(bpy.types.Operator):
    bl_label = 'Adjust the Selected Bone'
    bl_idname = 'mbast.button_adjustrotation'
    bl_description = 'Correct the animation with an offset to the bone angle'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        scn = bpy.context.scene
        mblab_retarget.get_bone_rot_type()

        if mblab_retarget.rot_type in ["EULER", "QUATERNION"]:
            offsets = mblab_retarget.get_offset_values()
            scn.mblab_rot_offset_0 = offsets[0]
            scn.mblab_rot_offset_1 = offsets[1]
            scn.mblab_rot_offset_2 = offsets[2]
            mblab_retarget.correction_is_sync = True
        return {'FINISHED'}


class UpdateSkinDisplacement(bpy.types.Operator):
    """
    Calculate and apply the skin displacement
    """
    bl_label = 'Update displacement'
    bl_idname = 'mbast.skindisplace_calculate'
    bl_description = 'Calculate and apply the skin details using displace modifier'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        """
        Calculate and apply the skin displacement
        """
        global mblab_humanoid
        scn = bpy.context.scene
        mblab_humanoid.update_displacement()
        mblab_humanoid.update_materials()
        return {'FINISHED'}


class DisableSubdivision(bpy.types.Operator):
    """
    Disable subdivision surface
    """
    bl_label = 'Disable subdivision preview'
    bl_idname = 'mbast.subdivision_disable'
    bl_description = 'Disable subdivision modifier'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global mblab_humanoid
        scn = bpy.context.scene

        if mblab_humanoid.get_subd_visibility() is True:
            mblab_humanoid.set_subd_visibility(False)
        return {'FINISHED'}


class EnableSubdivision(bpy.types.Operator):
    """
    Enable subdivision surface
    """
    bl_label = 'Enable subdivision preview'
    bl_idname = 'mbast.subdivision_enable'
    bl_description = 'Enable subdivision preview (Warning: it will slow down the morphing)'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global mblab_humanoid
        scn = bpy.context.scene

        if mblab_humanoid.get_subd_visibility() is False:
            mblab_humanoid.set_subd_visibility(True)
        return {'FINISHED'}


class DisableSmooth(bpy.types.Operator):
    bl_label = 'Disable corrective smooth'
    bl_idname = 'mbast.corrective_disable'
    bl_description = 'Disable corrective smooth modifier in viewport'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global mblab_humanoid
        scn = bpy.context.scene

        if mblab_humanoid.get_smooth_visibility() is True:
            mblab_humanoid.set_smooth_visibility(False)
        return {'FINISHED'}


class EnableSmooth(bpy.types.Operator):
    bl_label = 'Enable corrective smooth'
    bl_idname = 'mbast.corrective_enable'
    bl_description = 'Enable corrective smooth modifier in viewport'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global mblab_humanoid
        scn = bpy.context.scene

        if mblab_humanoid.get_smooth_visibility() is False:
            mblab_humanoid.set_smooth_visibility(True)
        return {'FINISHED'}


class DisableDisplacement(bpy.types.Operator):
    """
    Disable displacement modifier
    """
    bl_label = 'Disable displacement preview'
    bl_idname = 'mbast.displacement_disable'
    bl_description = 'Disable displacement modifier'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global mblab_humanoid
        scn = bpy.context.scene

        if mblab_humanoid.get_disp_visibility() is True:
            mblab_humanoid.set_disp_visibility(False)
        return {'FINISHED'}


class EnableDisplacement(bpy.types.Operator):
    """
    Enable displacement modifier
    """
    bl_label = 'Enable displacement preview'
    bl_idname = 'mbast.displacement_enable'
    bl_description = 'Enable displacement preview (Warning: it will slow down the morphing)'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global mblab_humanoid
        scn = bpy.context.scene

        if mblab_humanoid.get_disp_visibility() is False:
            mblab_humanoid.set_disp_visibility(True)
        return {'FINISHED'}


class ButtonAddParticleHair(bpy.types.Operator):
    bl_label = 'UTILITIES'
    bl_idname = 'mbast.button_utilities_on'
    bl_description = 'Open utilities panel'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global gui_active_panel_fin
        gui_active_panel_fin = "utilities"
        return {'FINISHED'}


class FinalizeCharacterAndImages(bpy.types.Operator, ExportHelper):
    """
        Convert the character in a standard Blender model
    """
    bl_label = 'Finalize with textures and backup'
    bl_idname = 'mbast.finalize_character_and_images'
    filename_ext = ".png"
    filter_glob: bpy.props.StringProperty(default="*.png", options={'HIDDEN'},)
    bl_description = 'Finalize, saving all the textures and converting the parameters in shapekeys. Warning: after the conversion the character will be no longer modifiable using MB-Lab tools'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):

        global mblab_humanoid
        global gui_status
        # TODO unique function in humanoid class
        scn = bpy.context.scene
        armature = mblab_humanoid.get_armature()

        mblab_humanoid.correct_expressions(correct_all=True)

        if not utils.is_ik_armature(armature):
            mblab_humanoid.set_rest_pose()
        if scn.mblab_remove_all_modifiers:
            mblab_humanoid.remove_modifiers()

        mblab_humanoid.sync_internal_data_with_mesh()
        mblab_humanoid.update_displacement()
        mblab_humanoid.update_materials()
        mblab_humanoid.save_backup_character(self.filepath)
        mblab_humanoid.save_all_textures(self.filepath)

        mblab_humanoid.morph_engine.convert_all_to_blshapekeys()
        mblab_humanoid.delete_all_properties()
        mblab_humanoid.rename_materials(scn.mblab_final_prefix)
        mblab_humanoid.update_bendy_muscles()
        mblab_humanoid.rename_obj(scn.mblab_final_prefix)
        mblab_humanoid.rename_armature(scn.mblab_final_prefix)
        gui_status = "NEW_SESSION"
        return {'FINISHED'}


class FinalizeCharacter(bpy.types.Operator):
    """
    Convert the character in a standard Blender model
    """
    bl_label = 'Finalize'
    bl_idname = 'mbast.finalize_character'
    bl_description = 'Finalize converting the parameters in shapekeys. Warning: after the conversion the character will be no longer modifiable using MB-Lab Tools'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):

        global mblab_humanoid
        global gui_status
        scn = bpy.context.scene
        armature = mblab_humanoid.get_armature()

        mblab_humanoid.correct_expressions(correct_all=True)

        if not utils.is_ik_armature(armature):
            mblab_humanoid.set_rest_pose()
        if scn.mblab_remove_all_modifiers:
            mblab_humanoid.remove_modifiers()

        mblab_humanoid.sync_internal_data_with_mesh()

        mblab_humanoid.morph_engine.convert_all_to_blshapekeys()
        mblab_humanoid.update_displacement()
        mblab_humanoid.update_materials()

        mblab_humanoid.delete_all_properties()
        mblab_humanoid.rename_materials(scn.mblab_final_prefix)
        mblab_humanoid.update_bendy_muscles()
        mblab_humanoid.rename_obj(scn.mblab_final_prefix)
        mblab_humanoid.rename_armature(scn.mblab_final_prefix)

        gui_status = "NEW_SESSION"
        return {'FINISHED'}


class ResetParameters(bpy.types.Operator):
    """Reset all morphings."""
    bl_label = 'Reset character'
    bl_idname = 'mbast.reset_allproperties'
    bl_description = 'Reset all character parameters'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL', 'UNDO'}

    def execute(self, context):
        global mblab_humanoid
        mblab_humanoid.reset_character()
        return {'FINISHED'}


class ResetExpressions(bpy.types.Operator):
    """Reset all morphings."""
    bl_label = 'Reset Expression'
    bl_idname = 'mbast.reset_expression'
    bl_description = 'Reset the expression'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL', 'UNDO'}

    def execute(self, context):
        global mblab_shapekeys
        mblab_shapekeys.reset_expressions_gui()
        return {'FINISHED'}


class InsertExpressionKeyframe(bpy.types.Operator):
    """Reset all morphings."""
    bl_label = 'Insert Keyframe'
    bl_idname = 'mbast.keyframe_expression'
    bl_description = 'Insert a keyframe expression at the current time'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL', 'UNDO'}

    def execute(self, context):
        global mblab_shapekeys
        mblab_shapekeys.keyframe_expression()
        return {'FINISHED'}


class Reset_category(bpy.types.Operator):
    """Reset the parameters for the currently selected category"""
    bl_label = 'Reset category'
    bl_idname = 'mbast.reset_categoryonly'
    bl_description = 'Reset the parameters for the current category'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL', 'UNDO'}

    def execute(self, context):
        global mblab_humanoid
        scn = bpy.context.scene
        mblab_humanoid.reset_category(scn.morphingCategory)
        return {'FINISHED'}


class CharacterGenerator(bpy.types.Operator):
    """Generate a new character using the specified parameters"""
    bl_label = 'Generate'
    bl_idname = 'mbast.character_generator'
    bl_description = 'Generate a new character according the parameters.'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL', 'UNDO'}

    def execute(self, context):
        global mblab_humanoid
        scn = bpy.context.scene
        rnd_values = {"LI": 0.05, "RE": 0.1, "NO": 0.2, "CA": 0.3, "EX": 0.5}
        rnd_val = rnd_values[scn.mblab_random_engine]
        p_face = scn.mblab_preserve_face
        p_body = scn.mblab_preserve_body
        p_mass = scn.mblab_preserve_mass
        p_tone = scn.mblab_preserve_tone
        p_height = scn.mblab_preserve_height
        p_phenotype = scn.mblab_preserve_phenotype
        set_tone_mass = scn.mblab_set_tone_and_mass
        b_tone = scn.mblab_body_tone
        b_mass = scn.mblab_body_mass
        p_fantasy = scn.mblab_preserve_fantasy

        mblab_humanoid.generate_character(rnd_val, p_face, p_body, p_mass, p_tone, p_height, p_phenotype, set_tone_mass, b_mass, b_tone, p_fantasy)
        return {'FINISHED'}


class ExpDisplacementImage(bpy.types.Operator, ExportHelper):
    """Export texture maps for the character"""
    bl_idname = "mbast.export_dispimage"
    bl_label = "Save displacement map"
    filename_ext = ".png"
    filter_glob: bpy.props.StringProperty(
        default="*.png",
        options={'HIDDEN'},
    )
    bl_context = 'objectmode'

    def execute(self, context):
        global mblab_humanoid
        mblab_humanoid.save_body_displacement_texture(self.filepath)
        return {'FINISHED'}


class ExpDermalImage(bpy.types.Operator, ExportHelper):
    """Export texture maps for the character"""
    bl_idname = "mbast.export_dermimage"
    bl_label = "Save dermal map"
    filename_ext = ".png"
    filter_glob: bpy.props.StringProperty(
        default="*.png",
        options={'HIDDEN'},
    )
    bl_context = 'objectmode'

    def execute(self, context):
        global mblab_humanoid
        mblab_humanoid.save_body_dermal_texture(self.filepath)
        return {'FINISHED'}


class ExpAllImages(bpy.types.Operator, ExportHelper):
    """Export all texture maps for the character"""
    bl_idname = "mbast.export_allimages"
    bl_label = "Export all maps"
    filename_ext = ".png"
    filter_glob: bpy.props.StringProperty(
        default="*.png",
        options={'HIDDEN'},
    )
    bl_context = 'objectmode'

    def execute(self, context):
        global mblab_humanoid
        mblab_humanoid.save_all_textures(self.filepath)
        return {'FINISHED'}


class ExpCharacter(bpy.types.Operator, ExportHelper):
    """Export parameters for the character"""
    bl_idname = "mbast.export_character"
    bl_label = "Export character"
    filename_ext = ".json"
    filter_glob: bpy.props.StringProperty(
        default="*.json",
        options={'HIDDEN'},
    )
    bl_context = 'objectmode'

    def execute(self, context):
        global mblab_humanoid
        scn = bpy.context.scene
        mblab_humanoid.save_character(self.filepath, scn.mblab_export_proportions, scn.mblab_export_materials)
        return {'FINISHED'}


class ExpMeasures(bpy.types.Operator, ExportHelper):
    """Export parameters for the character"""
    bl_idname = "mbast.export_measures"
    bl_label = "Export measures"
    filename_ext = ".json"
    filter_glob: bpy.props.StringProperty(
        default="*.json",
        options={'HIDDEN'},
    )
    bl_context = 'objectmode'

    def execute(self, context):
        global mblab_humanoid
        mblab_humanoid.export_measures(self.filepath)
        return {'FINISHED'}


class ImpCharacter(bpy.types.Operator, ImportHelper):
    """Import parameters for the character"""
    bl_idname = "mbast.import_character"
    bl_label = "Import character"
    filename_ext = ".json"
    filter_glob: bpy.props.StringProperty(
        default="*.json",
        options={'HIDDEN'},
    )
    bl_context = 'objectmode'

    def execute(self, context):
        global mblab_humanoid

        char_data = mblab_humanoid.load_character(self.filepath)
        return {'FINISHED'}


class ImpMeasures(bpy.types.Operator, ImportHelper):
    """Import parameters for the character"""
    bl_idname = "mbast.import_measures"
    bl_label = "Import measures"
    filename_ext = ".json"
    filter_glob: bpy.props.StringProperty(
        default="*.json",
        options={'HIDDEN'},
    )
    bl_context = 'objectmode'

    def execute(self, context):
        global mblab_humanoid
        mblab_humanoid.import_measures(self.filepath)
        return {'FINISHED'}


class LoadDermImage(bpy.types.Operator, ImportHelper):
    """Import texture maps for the character"""
    bl_idname = "mbast.import_dermal"
    bl_label = "Load dermal map"
    filename_ext = ".png"
    filter_glob: bpy.props.StringProperty(
        default="*.png",
        options={'HIDDEN'},
    )
    bl_context = 'objectmode'

    def execute(self, context):
        global mblab_humanoid
        mblab_humanoid.load_body_dermal_texture(self.filepath)
        return {'FINISHED'}


class LoadDispImage(bpy.types.Operator, ImportHelper):
    """Import texture maps for the character"""
    bl_idname = "mbast.import_displacement"
    bl_label = "Load displacement map"
    filename_ext = ".png"
    filter_glob: bpy.props.StringProperty(
        default="*.png",
        options={'HIDDEN'},
    )
    bl_context = 'objectmode'

    def execute(self, context):
        global mblab_humanoid
        mblab_humanoid.load_body_displacement_texture(self.filepath)
        return {'FINISHED'}


class FitProxy(bpy.types.Operator):
    bl_label = 'Fit Proxy'
    bl_idname = 'mbast.proxy_fit'
    bl_description = 'Fit the selected proxy to the character'
    bl_context = 'objectmode'
    bl_options = {'UNDO', 'INTERNAL'}

    def execute(self, context):
        scn = bpy.context.scene
        offset = scn.mblab_proxy_offset / 1000
        threshold = scn.mblab_proxy_threshold / 1000
        advanced = scn.mblab_proxy_use_advanced
        mblab_proxy.fit_proxy_object(
            offset, threshold,
            create_proxy_mask = scn.mblab_add_mask_group,
            transfer_w = scn.mblab_transfer_proxy_weights,
            reverse = advanced and scn.mblab_proxy_reverse_fit,
            all_faces = advanced and scn.mblab_proxy_use_all_faces,
            smoothing = not (advanced and scn.mblab_proxy_no_smoothing),
        )
        return {'FINISHED'}


class RemoveProxy(bpy.types.Operator):
    bl_label = 'Remove fitting'
    bl_idname = 'mbast.proxy_removefit'
    bl_description = 'Remove fitting, so the proxy can be modified and then fitted again'
    bl_context = 'objectmode'
    bl_options = {'UNDO', 'INTERNAL'}

    def execute(self, context):
        scn = bpy.context.scene
        mblab_proxy.remove_fitting()
        return {'FINISHED'}
        

class ApplyMeasures(bpy.types.Operator):
    """Fit the character to the measures"""

    bl_label = 'Update character'
    bl_idname = 'mbast.measures_apply'
    bl_description = 'Fit the character to the measures'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global mblab_humanoid
        mblab_humanoid.automodelling(use_measures_from_GUI=True)
        return {'FINISHED'}


class AutoModelling(bpy.types.Operator):
    """Fit the character to the measures"""

    bl_label = 'Auto modelling'
    bl_idname = 'mbast.auto_modelling'
    bl_description = 'Analyze the mesh form and return a verisimilar human'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL', 'UNDO'}

    def execute(self, context):
        global mblab_humanoid
        mblab_humanoid.automodelling(use_measures_from_current_obj=True)
        return {'FINISHED'}


class AutoModellingMix(bpy.types.Operator):
    """Fit the character to the measures"""

    bl_label = 'Averaged auto modelling'
    bl_idname = 'mbast.auto_modelling_mix'
    bl_description = 'Return a verisimilar human with multiple interpolations that make it nearest to average'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL', 'UNDO'}

    def execute(self, context):
        global mblab_humanoid
        mblab_humanoid.automodelling(use_measures_from_current_obj=True, mix=True)
        return {'FINISHED'}


class SaveRestPose(bpy.types.Operator, ExportHelper):
    """Export pose"""
    bl_idname = "mbast.restpose_save"
    bl_label = "Save custom rest pose"
    filename_ext = ".json"
    filter_glob: bpy.props.StringProperty(
        default="*.json",
        options={'HIDDEN'},
    )
    bl_context = 'objectmode'

    def execute(self, context):
        global mblab_humanoid
        armature = mblab_humanoid.get_armature()
        mblab_retarget.save_pose(armature, self.filepath)
        return {'FINISHED'}


class LoadRestPose(bpy.types.Operator, ImportHelper):
    """Import parameters for the character"""
    bl_idname = "mbast.restpose_load"
    bl_label = "Load custom rest pose"
    filename_ext = ".json"
    filter_glob: bpy.props.StringProperty(
        default="*.json",
        options={'HIDDEN'},
    )
    bl_context = 'objectmode'

    def execute(self, context):
        global mblab_humanoid, mblab_retarget
        armature = mblab_humanoid.get_armature()
        mblab_retarget.load_pose(self.filepath, armature, use_retarget=False)
        return {'FINISHED'}


class SavePose(bpy.types.Operator, ExportHelper):
    """Export pose"""
    bl_idname = "mbast.pose_save"
    bl_label = "Save pose"
    filename_ext = ".json"
    filter_glob: bpy.props.StringProperty(
        default="*.json",
        options={'HIDDEN'},
    )
    bl_context = 'objectmode'

    def execute(self, context):
        global mblab_humanoid
        armature = utils.get_active_armature()
        mblab_retarget.save_pose(armature, self.filepath)
        return {'FINISHED'}

class ButtonLoadBvhAdjusments(bpy.types.Operator, ImportHelper):
    """Import bvh settings for the character"""
    bl_idname = "mbast.button_load_bvh_adjustments"
    bl_label = "Load BVH Bone Config"
    filename_ext = ".json"
    bl_description = 'Import the json file containing bvh animation adjustments'
    filter_glob: bpy.props.StringProperty(
        default="*.json",
        options={'HIDDEN'},
    )
    bl_context = 'objectmode'

    def execute(self, context):
        global mblab_humanoid
        global mblab_retarget
        scn = bpy.context.scene
        armature = utils.get_active_armature()
        matrix_data = file_ops.load_json_data(self.filepath, "BVH config")
        # Loop Through Config Adjustments and Apply Changes
        for bone in matrix_data:
            armature.data.bones[bone].select = True
            rot_x = matrix_data[bone][0]
            rot_y = matrix_data[bone][1]
            rot_z = matrix_data[bone][2]
            mblab_retarget.correct_bone_angle(0, rot_x)
            mblab_retarget.correct_bone_angle(1, rot_y)
            mblab_retarget.correct_bone_angle(2, rot_z)
            armature.data.bones[bone].select = False
        return {'FINISHED'}

class ButtonSaveBvhAdjustments(bpy.types.Operator, ExportHelper):
    bl_idname = 'mbast.button_save_bvh_adjustments'
    bl_label = 'Save BVH Bone Config'
    bl_description = 'Save bone corrections into a local json file'
    filename_ext = ".json"
    filter_glob: bpy.props.StringProperty(
        default="*.json",
        options={'HIDDEN'},
    )
    bl_context = 'objectmode'

    def execute(self, context):
        scn = bpy.context.scene
        selected_bone = mblab_retarget.get_selected_posebone().name

        if mblab_retarget.rot_type in ["EULER", "QUATERNION"]:
            offsets = mblab_retarget.get_offset_values()
            saveBone = []
            saveBone.append(offsets[0])
            saveBone.append(offsets[1])
            saveBone.append(offsets[2])
            dict = {selected_bone: saveBone}

            if os.path.exists(self.filepath):
                with open(self.filepath, 'r+') as f:
                    bones = json.load(f)
                    # Update Json
                    bones[selected_bone] = saveBone
                    f.seek(0)
                    f.truncate()
                    json.dump(bones, f)
            else:
                data = json.dumps(dict, indent=1, ensure_ascii=True)
                with open(self.filepath, 'w') as outfile:
                    outfile.write(data + '\n')

        return {'FINISHED'}


class LoadPose(bpy.types.Operator, ImportHelper):
    """Import parameters for the character"""
    bl_idname = "mbast.pose_load"
    bl_label = "Load pose"
    filename_ext = ".json"
    filter_glob: bpy.props.StringProperty(
        default="*.json",
        options={'HIDDEN'},
    )
    bl_context = 'objectmode'

    def execute(self, context):
        global mblab_retarget
        mblab_retarget.load_pose(self.filepath, use_retarget=True)
        return {'FINISHED'}


class ResetPose(bpy.types.Operator):
    """Import parameters for the character"""
    bl_idname = "mbast.pose_reset"
    bl_label = "Reset pose"
    bl_context = 'objectmode'
    bl_description = 'Reset the angles of the armature bones'
    bl_options = {'REGISTER', 'INTERNAL', 'UNDO'}

    def execute(self, context):
        global mblab_retarget
        mblab_retarget.reset_pose()
        return {'FINISHED'}


class LoadBvh(bpy.types.Operator, ImportHelper):
    """Import parameters for the character"""
    bl_idname = "mbast.load_animation"
    bl_label = "Load animation (bvh)"
    filename_ext = ".bvh"
    bl_description = 'Import the animation from a bvh motion capture file'
    filter_glob: bpy.props.StringProperty(
        default="*.bvh",
        options={'HIDDEN'},
    )
    bl_context = 'objectmode'

    def execute(self, context):
        global mblab_retarget
        mblab_retarget.load_animation(self.filepath)
        return {'FINISHED'}


class CreateFaceRig(bpy.types.Operator):
    bl_idname = "mbast.create_face_rig"
    bl_label = "Create Face Rig"
    bl_description = "Create the character's face Rig"
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL', 'UNDO'}

    def execute(self, context):
        mblab_shapekeys.update_expressions_data()
        if mblab_shapekeys.model_type != "NONE":
            obj = algorithms.get_active_body()
            rc = facerig.setup_face_rig(obj)
            if not rc:
                self.report({'ERROR'},
                            "Face Rig creation process failed")
                return {'FINISHED'}
            elif bpy.context.scene.mblab_facs_rig:
                rc = facerig.setup_facs_rig(obj)
                if not rc:
                    self.report({'ERROR'},
                                "FACS Rig creation process failed")
                    return {'FINISHED'}
        else:
            self.report({'ERROR'},
                        "Select finalized MB-Lab character to create face rig")
        return {'FINISHED'}


class DeleteFaceRig(bpy.types.Operator):
    bl_idname = "mbast.delete_face_rig"
    bl_label = "Delete Face Rig"
    bl_description = "Delete the character's face Rig"
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL', 'UNDO'}

    def execute(self, context):
        mblab_shapekeys.update_expressions_data()
        obj = algorithms.get_active_object()
        if not obj:
            self.report({'ERROR'}, "Select Face Rig to delete")
            return {'FINISHED'}

        if not facerig.delete_face_rig(obj):
            self.report({'ERROR'}, "failed to delete face rig")
        return {'FINISHED'}

# Add Limit Rotations Constraint
class OBJECT_OT_humanoid_rot_limits(bpy.types.Operator):
    """Add Humanoid Rotation Limits to Character"""
    bl_idname = "mbast.humanoid_rot_limits"
    bl_label = "Humanoid Rotations"
    bl_options = {'REGISTER', 'INTERNAL', 'UNDO'}

    def execute(self, context):
        armature = humanoid_rotations.get_skeleton()
        pb = armature.pose.bones
        humanoid_rotations.limit_bone_rotation(humanoid_rotations.rotation_limits_dict, pb)
        humanoid_rotations.limit_bone_rotation(humanoid_rotations.fd, pb)
        return {'FINISHED'}

# Delete Limit Rotations Constraint
class OBJECT_OT_delete_rotations(bpy.types.Operator):
    """Delete Humanoid Rotation Limits for Character"""
    bl_idname = "mbast.delete_rotations"
    bl_label = "Delete Humanoid Rotations"
    bl_options = {'REGISTER', 'INTERNAL', 'UNDO'}

    def execute(self, context):
        armature = humanoid_rotations.get_skeleton()
        pb = armature.pose.bones
        humanoid_rotations.remove_bone_constraints('LIMIT_ROTATION', pb)
        return {'FINISHED'}

#Add Hair Op
class OBJECT_OT_particle_hair(bpy.types.Operator):
    """Add Hair to Character"""
    bl_idname = "mbast.particle_hair"
    bl_label = "Particle Hair"
    bl_options = {'REGISTER', 'INTERNAL', 'UNDO'}

    def execute(self, context):
        self.hair_Name = "Head_Hair"
        scn = bpy.context.scene
        style = scn.mblab_hair_color
        character_id = scn.mblab_character_name
        skeleton = object_ops.get_skeleton()
        bpy.ops.object.mode_set(mode='OBJECT')
        skeleton.select_set(state=False)
        body = object_ops.get_body_mesh()
        body.select_set(state=True)
        bpy.context.view_layer.objects.active = body
        faces = hairengine.get_hair_data(character_id)
        hairengine.sel_faces(faces)
        hairengine.add_scalp(self.hair_Name)
        hair = bpy.data.objects[self.hair_Name]
        hairengine.hair_armature_mod(skeleton, hair)
        if context.scene.mblab_use_cycles:
            hairengine.add_hair(hair, self.hair_Name, style)
        else:
            hairengine.add_pHair(hair)
            node_ops.universal_shader_nodes(self.hair_Name, node_ops.universal_hair_setup(), (1130, 280))
            node_ops.set_universal_shader(self.hair_Name, hairengine.get_hair_npz('universal_hair_shader.npz'), style)
        bpy.ops.object.mode_set(mode='OBJECT')
        object_ops.add_parent(skeleton.name, [self.hair_Name])
        # object_ops.active_ob(skeleton.name, None)
        # try:
        #     bpy.ops.object.mode_set(mode='POSE')
        # except:
        #     pass       
        return {'FINISHED'}

class OBJECT_OT_manual_hair(bpy.types.Operator):
    """Add Hair to Character from Selected Polygons"""
    bl_idname = "mbast.manual_hair"
    bl_label = "Hair from Selected"
    bl_options = {'REGISTER', 'INTERNAL', 'UNDO'}

    def execute(self, context):
        self.hair_Name = "Hairs"
        scn = bpy.context.scene
        style = scn.mblab_hair_color
        character_id = scn.mblab_character_name
        get_mode = bpy.context.object.mode
        skeleton = object_ops.get_skeleton()
        hairengine.add_scalp(self.hair_Name)
        hair = bpy.data.objects[self.hair_Name]
        hairengine.hair_armature_mod(skeleton, hair)
        if scn.mblab_use_cycles:
            hairengine.add_hair(hair, self.hair_Name, style)
        else:
            hairengine.add_pHair(hair)
            node_ops.universal_shader_nodes(self.hair_Name, node_ops.universal_hair_setup(), (1130, 280))
            node_ops.set_universal_shader(self.hair_Name, hairengine.get_hair_npz('universal_hair_shader.npz'), style)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.object.mode_set(mode='OBJECT')
        object_ops.add_parent(skeleton.name, [self.hair_Name])
        # object_ops.active_ob(skeleton.name, None)
        # try:
        #     bpy.ops.object.mode_set(mode='POSE')
        # except:
        #     pass       
        return {'FINISHED'}

class OBJECT_OT_change_hair_color(bpy.types.Operator):
    """Change Selected Hair Color"""
    bl_idname = "mbast.change_hair"
    bl_label = "Change Color"
    bl_options = {'REGISTER', 'INTERNAL', 'UNDO'}

    def execute(self, context):
        self.hair_Name = "Hairs"
        scn = bpy.context.scene
        style = scn.mblab_hair_color
        character_id = scn.mblab_character_name
        get_mode = bpy.context.object.mode
        skeleton = object_ops.get_skeleton()
        material = bpy.context.object.active_material
        nodes = material.node_tree.nodes
        if scn.mblab_use_cycles:
            hairengine.change_hair_shader(style)
        else:
            node_ops.universal_shader_nodes(material.name, node_ops.universal_hair_setup(), (1130, 280))
            node_ops.set_universal_shader(bpy.context.object.name, hairengine.get_hair_npz('universal_hair_shader.npz'), style)
        return {'FINISHED'}

class OBJECT_OT_add_color_preset(bpy.types.Operator):
    """Add Hair Color to Presets"""
    bl_idname = "mbast.add_hair_preset"
    bl_label = "Add Preset"
    bl_options = {'REGISTER', 'INTERNAL', 'UNDO'}

    def execute(self, context):
        #self.hair_Name = "Head_Hair"
        scn = bpy.context.scene
        #style = scn.mblab_hair_color
        character_id = scn.mblab_character_name
        skeleton = object_ops.get_skeleton()
        newColor = scn.mblab_new_hair_color
        material = bpy.context.object.active_material
        nodes = material.node_tree.nodes
        if scn.mblab_use_cycles:
            fileName = hairengine.get_hair_npz('CY_shader_presets.npz')
            hairengine.add_hair_data(context.object, newColor, fileName)
        else:
            fileName = hairengine.get_hair_npz('universal_hair_shader.npz')
            node_ops.save_universal_presets(fileName, newColor, node_ops.get_all_shader_(nodes))
        return {'FINISHED'}

class OBJECT_OT_remove_color_preset(bpy.types.Operator):
    """Remove Hair Color from Presets"""
    bl_idname = "mbast.del_hair_preset"
    bl_label = "Delete Preset"
    bl_options = {'REGISTER', 'INTERNAL', 'UNDO'}

    def execute(self, context):
        scn = bpy.context.scene
        style = scn.mblab_hair_color
        newColor = scn.mblab_new_hair_color
        if scn.mblab_use_cycles:
            global CY_Hshader_remove
            fileName = hairengine.get_hair_npz("CY_shader_presets.npz")
            hairengine.delete_hair_data(style, fileName, CY_Hshader_remove)
        else:
            global UN_shader_remove
            fileName = hairengine.get_hair_npz('universal_hair_shader.npz')
            node_ops.remove_universal_presets(fileName, style, UN_shader_remove)
        return {'FINISHED'}

#Undo Delete Preset
class OBJECT_OT_undo_remove_color(bpy.types.Operator):
    """Replace Removed Hair Color"""
    bl_idname = "mbast.rep_hair_preset"
    bl_label = "Undo Delete Preset"
    bl_options = {'REGISTER', 'INTERNAL', 'UNDO'}

    def execute(self, context):
        scn = bpy.context.scene
        style = scn.mblab_hair_color
        newColor = scn.mblab_new_hair_color
        if scn.mblab_use_cycles:
            global CY_Hshader_remove
            fileName = hairengine.get_hair_npz("CY_shader_presets.npz")
            hairengine.replace_hair_data(fileName, CY_Hshader_remove)
        else:
            global UN_shader_remove
            fileName = hairengine.get_hair_npz('universal_hair_shader.npz')
            node_ops.replace_removed_shader(fileName, UN_shader_remove)
        return {'FINISHED'}

class StartSession(bpy.types.Operator):
    bl_idname = "mbast.init_character"
    bl_label = "Create character"
    bl_description = 'Create the character selected above'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL', 'UNDO'}

    def execute(self, context):
        start_lab_session()
        return {'FINISHED'}


class LoadTemplate(bpy.types.Operator):
    bl_idname = "mbast.load_base_template"
    bl_label = "Import template"
    bl_description = 'Import the humanoid template for proxies reference'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL', 'UNDO'}

    def execute(self, context):
        global mblab_humanoid
        scn = bpy.context.scene
        lib_filepath = file_ops.get_blendlibrary_path()
        base_model_name = mblab_humanoid.characters_config[scn.mblab_template_name]["template_model"]
        obj = file_ops.import_object_from_lib(lib_filepath, base_model_name, scn.mblab_template_name)
        if obj:
            obj["manuellab_proxy_reference"] = mblab_humanoid.characters_config[scn.mblab_template_name][
                "template_model"]
        return {'FINISHED'}

# MB-Lab Main GUI

class VIEW3D_PT_tools_MBLAB(bpy.types.Panel):
    bl_label = "MB-Lab {0}.{1}.{2}".format(bl_info["version"][0], bl_info["version"][1], bl_info["version"][2], bl_info["version"][3])
    bl_idname = "OBJECT_PT_characters01"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    # bl_context = 'objectmode'
    bl_category = "MB-Lab"

    @classmethod
    def poll(cls, context):
        return context.mode in {'OBJECT', 'POSE'}

    def draw(self, context):

        global mblab_humanoid, gui_status, gui_err_msg #gui_active_panel
        global gui_active_panel, gui_active_panel_middle, gui_active_panel_display
        scn = bpy.context.scene
        icon_expand = "DISCLOSURE_TRI_RIGHT"
        icon_collapse = "DISCLOSURE_TRI_DOWN"

        box_info = self.layout.box()
        box_info.label(text="https://www.mblab.dev")

        if gui_status == "ERROR_SESSION":
            box_err = self.layout.box()
            box_err.label(text=gui_err_msg, icon="INFO")

        if gui_status == "NEW_SESSION":

            self.layout.label(text="CREATION OPTIONS", icon='RNA_ADD')
            box_new_opt = self.layout.box()
            box_new_opt.prop(scn, 'mblab_character_name')

            if mblab_humanoid.is_ik_rig_available(scn.mblab_character_name):
                box_new_opt.prop(scn, 'mblab_use_ik', icon='BONE_DATA')
            if mblab_humanoid.is_muscle_rig_available(scn.mblab_character_name):
                box_new_opt.prop(scn, 'mblab_use_muscle', icon='BONE_DATA')

            box_new_opt.prop(scn, 'mblab_use_cycles', icon='SHADING_RENDERED')
            box_new_opt.prop(scn, 'mblab_use_eevee', icon='SHADING_RENDERED')
            if scn.mblab_use_cycles or scn.mblab_use_eevee:
                box_new_opt.prop(scn, 'mblab_use_lamps', icon='LIGHT_DATA')
            box_new_opt.operator('mbast.init_character', icon='ARMATURE_DATA')

        if gui_status != "ACTIVE_SESSION":
            self.layout.separator(factor=0.5)
            self.layout.label(text="AFTER-CREATION TOOLS", icon='MODIFIER_ON')

            box_post_opt = self.layout.box()
            if gui_active_panel_fin != "face_rig":
                box_post_opt.operator('mbast.button_facerig_on', icon=icon_expand)
            else:
                box_post_opt.operator('mbast.button_facerig_off', icon=icon_collapse)

            # Face Rig
            
                box_face_rig = box_post_opt.box()
                #box_face_rig.label(text="Face Rig")
                box_face_rig.operator('mbast.create_face_rig', icon='USER')
                box_face_rig.operator('mbast.delete_face_rig', icon='CANCEL')
                box_face_rig.prop(scn, "mblab_facs_rig")

            # Expressions
            
            if gui_active_panel_fin != "expressions":
                box_post_opt.operator('mbast.button_expressions_on', icon=icon_expand)
            else:
                box_post_opt.operator('mbast.button_expressions_off', icon=icon_collapse)
                box_exp = box_post_opt.box()
                mblab_shapekeys.update_expressions_data()
                if mblab_shapekeys.model_type != "NONE":
                    box_exp.enabled = True
                    box_exp.prop(scn, 'mblab_expression_filter')
                    box_exp.operator("mbast.keyframe_expression", icon="ACTION")
                    #Teto
                    if mblab_shapekeys.expressions_data:
                        sorted_expressions = sorted(mblab_shapekeys.expressions_data.keys())
                        obj = algorithms.get_active_body()
                        if len(str(scn.mblab_expression_filter)) > 0:
                            for expr_name in sorted_expressions:
                                if hasattr(obj, expr_name) and scn.mblab_expression_filter in expr_name:
                                    box_exp.prop(obj, expr_name)
                        else:
                            mbcrea_expressionscreator.set_expressions_items(sorted_expressions)
                            box_exp.prop(scn, 'mbcrea_enum_expressions_items')
                            result = mbcrea_expressionscreator.get_expressions_item(scn.mbcrea_enum_expressions_items)
                            box_exp.prop(obj, result)
                    #End Teto
                    box_exp.operator("mbast.reset_expression", icon="RECOVER_LAST")
                else:
                    box_exp.enabled = False
                    box_exp.label(text="No express. shapekeys", icon='INFO')
            
            # Assets, Fitting and Particle Hair

            if gui_active_panel_fin != "assets":
                box_post_opt.operator('mbast.button_assets_on', icon=icon_expand)
            else:
                box_post_opt.operator('mbast.button_assets_off', icon=icon_collapse)
                # assets_status = mblab_proxy.validate_assets_fitting()
                box_asts = box_post_opt.box()
                box_asts.label(text="Mesh Assets")
                box_asts.prop(scn, 'mblab_proxy_library')
                box_asts.prop(scn, 'mblab_assets_models')
                # box.operator('mbast.load_assets_element')
                box_asts.label(text="To adapt the asset, use the proxy fitting tool", icon='INFO')
                # Add Particle Hair
                box_asts = box_post_opt.box()
                box_asts.label(text="Hair")
                box_asts.prop(scn, 'mblab_hair_color')
                box_asts.operator("mbast.particle_hair", icon='USER')
                box_asts.operator("mbast.manual_hair", icon='USER')
                box_asts.operator("mbast.change_hair", icon='USER')
                box_asts.prop(scn, 'mblab_new_hair_color')
                box_asts.operator("mbast.add_hair_preset", icon='USER')
                box_asts.operator("mbast.del_hair_preset", icon='USER')
                box_asts.operator("mbast.rep_hair_preset", icon='USER')

            # Proxy Fitting

            if gui_active_panel_fin != "proxy_fit":
                box_post_opt.operator('mbast.button_proxy_fit_on', icon=icon_expand)
            else:
                box_post_opt.operator('mbast.button_proxy_fit_off', icon=icon_collapse)
                fitting_status, proxy_obj, reference_obj = mblab_proxy.get_proxy_fitting_ingredients()

                box_prox = box_post_opt.box()
                box_prox.label(text="PROXY FITTING")
                box_prox.label(text="Please select character and proxy:")
                box_prox.prop(scn, 'mblab_fitref_name')
                box_prox.prop(scn, 'mblab_proxy_name')
                if fitting_status == "NO_REFERENCE":
                    # box_prox.enabled = False
                    box_prox.label(text="Character not valid.", icon="ERROR")
                    box_prox.label(text="Possible reasons:")
                    box_prox.label(text="- Character created with a different lab version")
                    box_prox.label(text="- Character topology altered by custom modelling")
                    box_prox.label(text="- Character topology altered by modifiers (decimator,subsurf, etc..)")
                if fitting_status == "SAME_OBJECTS":
                    box_prox.label(text="Proxy and character cannot be the same object", icon="ERROR")
                if fitting_status == "CHARACTER_NOT_FOUND":
                    box_prox.label(text="Character not found", icon="ERROR")
                if fitting_status == "PROXY_NOT_FOUND":
                    box_prox.label(text="Proxy not found", icon="ERROR")
                if fitting_status == 'OK':
                    box_prox.label(text="The proxy is ready for fitting.", icon="INFO")
                    proxy_compatib = mblab_proxy.validate_assets_compatibility(proxy_obj, reference_obj)

                    if proxy_compatib == "WARNING":
                        box_prox.label(text="The proxy seems not designed for the selected character.", icon="ERROR")

                    box_prox.prop(scn, 'mblab_proxy_offset')
                    box_prox.prop(scn, 'mblab_proxy_threshold')
                    box_prox.prop(scn, 'mblab_proxy_use_advanced', icon="PLUS")
                    if scn.mblab_proxy_use_advanced:
                        col = box_prox.column()
                        col.prop(scn, 'mblab_proxy_use_all_faces', icon="FACESEL")
                        col.prop(scn, 'mblab_proxy_no_smoothing', icon="MOD_SMOOTH")
                        col.prop(scn, 'mblab_proxy_reverse_fit', icon="COMMUNITY")
                    col = box_prox.column()
                    col.active = not (scn.mblab_proxy_use_advanced and scn.mblab_proxy_reverse_fit)
                    col.prop(scn, 'mblab_add_mask_group', icon="XRAY")
                    col.prop(scn, 'mblab_transfer_proxy_weights',icon="UV_SYNC_SELECT")
                    box_prox.operator("mbast.proxy_fit", icon="MOD_CLOTH")
                    box_prox.operator("mbast.proxy_removefit", icon="MOD_CLOTH")
                if fitting_status == 'WRONG_SELECTION':
                    box_prox.enabled = False
                    box_prox.label(text="Please select only two objects: humanoid and proxy", icon="INFO")
                if fitting_status == 'NO_REFERENCE_SELECTED':
                    box_prox.enabled = False
                    box_prox.label(text="No valid humanoid template selected", icon="INFO")
                if fitting_status == 'NO_MESH_SELECTED':
                    box_prox.enabled = False
                    box_prox.label(text="Selected proxy is not a mesh", icon="INFO")

            # Pose

            if gui_active_panel_fin != "pose":
                box_post_opt.operator('mbast.button_pose_on', icon=icon_expand)
            else:
                box_post_opt.operator('mbast.button_pose_off', icon=icon_collapse)
                box_pose = box_post_opt.box()

                armature = utils.get_active_armature()
                if armature is not None and not utils.is_ik_armature(armature):
                    box_pose.enabled = True
                    sel_gender = algorithms.get_selected_gender()
                    if sel_gender == "FEMALE":
                        if mblab_retarget.femaleposes_exist:
                            box_pose.prop(armature, "female_pose")
                    if sel_gender == "MALE":
                        if mblab_retarget.maleposes_exist:
                            box_pose.prop(armature, "male_pose")
                    box_pose.operator("mbast.pose_load", icon='IMPORT')
                    box_pose.operator("mbast.pose_save", icon='EXPORT')
                    box_pose.operator("mbast.pose_reset", icon='ARMATURE_DATA')
                    box_pose.operator("mbast.load_animation", icon='IMPORT')
                    # Humanoid Rotations
                    box_pose.operator("mbast.humanoid_rot_limits", icon='USER')
                    box_pose.operator('mbast.delete_rotations', icon='CANCEL')
                else:
                    box_pose.enabled = False
                    box_pose.label(text="Please select the lab character (IK not supported)", icon='INFO')

            # Utilities

            if gui_active_panel_fin != "utilities":
                box_post_opt.operator('mbast.button_utilities_on', icon=icon_expand)
            else:
                box_post_opt.operator('mbast.button_utilities_off', icon=icon_collapse)

                box_util_prox = box_post_opt.box()
                box_util_prox.label(text="Choose a proxy reference")
                box_util_prox.prop(scn, 'mblab_template_name')
                box_util_prox.operator('mbast.load_base_template')

                box_util_bvh = box_post_opt.box()
                box_util_bvh.label(text="Bones rot. offset")
                box_util_bvh.operator('mbast.button_adjustrotation', icon='BONE_DATA')
                box_util_bvh.operator('mbast.button_save_bvh_adjustments', icon='EXPORT')
                box_util_bvh.operator('mbast.button_load_bvh_adjustments', icon='IMPORT')
                mblab_retarget.check_correction_sync()
                if mblab_retarget.is_animated_bone == "VALID_BONE":
                    if mblab_retarget.correction_is_sync:
                        box_util_bvh.prop(scn, 'mblab_rot_offset_0')
                        box_util_bvh.prop(scn, 'mblab_rot_offset_1')
                        box_util_bvh.prop(scn, 'mblab_rot_offset_2')
                else:
                    box_util_bvh.label(text=mblab_retarget.is_animated_bone)

        # Pre-Finalized State

        if gui_status == "ACTIVE_SESSION":
            obj = mblab_humanoid.get_object()
            armature = mblab_humanoid.get_armature()
            if obj and armature:
                self.layout.label(text="CHARACTER SHAPE", icon="RNA")
                box_act_opt = self.layout.box()
                box_act_opt_sub = box_act_opt.box()

                if mblab_humanoid.exists_transform_database():
                    x_age = getattr(obj, 'character_age', 0)
                    x_mass = getattr(obj, 'character_mass', 0)
                    x_tone = getattr(obj, 'character_tone', 0)
                    age_lbl = round((15.5 * x_age ** 2) + 31 * x_age + 33)
                    mass_lbl = round(50 * (x_mass + 1))
                    tone_lbl = round(50 * (x_tone + 1))
                    lbl_text = "Age : {0} yr.  Mass : {1}%  Tone : {2}% ".format(age_lbl, mass_lbl, tone_lbl)
                    box_act_opt_sub.label(text=lbl_text)

                    for meta_data_prop in sorted(mblab_humanoid.character_metaproperties.keys()):
                        if "last" not in meta_data_prop:
                            box_act_opt_sub.prop(obj, meta_data_prop)
                    box_act_opt_sub.operator("mbast.reset_allproperties", icon="RECOVER_LAST")
                    box_act_opt_sub.separator(factor=0.2)
                    #if mblab_humanoid.get_subd_visibility() is True:
                        #self.layout.label(text="Tip: for slow PC, disable the subdivision in Display Options below", icon='INFO')
                # Sub-panel for all tools below
                box_act_tools_sub = self.layout.box()
                
                # Character library
                
                box_act_tools_sub.label(text="CHARACTER SET-UP", icon="RNA")
                if gui_active_panel != "library":
                    box_act_tools_sub.operator('mbast.button_library_on', icon=icon_expand)
                else:
                    box_act_tools_sub.operator('mbast.button_library_off', icon=icon_collapse)
                    box_lib = self.layout.box()

                    #box_lib.label(text="Characters library", icon='ARMATURE_DATA')
                    if mblab_humanoid.exists_preset_database():
                        box_lib.prop(obj, "preset")
                    if mblab_humanoid.exists_phenotype_database():
                        box_lib.prop(obj, "ethnic")
                    box_lib.prop(scn, 'mblab_mix_characters', icon='FORCE_CHARGE')
                
                # Randomize character
                
                if gui_active_panel != "random":
                    box_act_tools_sub.operator('mbast.button_random_on', icon=icon_expand)
                else:
                    box_act_tools_sub.operator('mbast.button_random_off', icon=icon_collapse)

                    box_rand = self.layout.box()
                    box_rand.prop(scn, "mblab_random_engine")
                    box_rand.prop(scn, "mblab_set_tone_and_mass")
                    if scn.mblab_set_tone_and_mass:
                        box_rand.prop(scn, "mblab_body_mass")
                        box_rand.prop(scn, "mblab_body_tone")

                    box_rand.label(text="Preserve:")
                    box_rand.prop(scn, "mblab_preserve_mass")
                    box_rand.prop(scn, "mblab_preserve_height")
                    box_rand.prop(scn, "mblab_preserve_tone")
                    box_rand.prop(scn, "mblab_preserve_body")
                    box_rand.prop(scn, "mblab_preserve_face")
                    box_rand.prop(scn, "mblab_preserve_phenotype")
                    box_rand.prop(scn, "mblab_preserve_fantasy")

                    box_rand.operator('mbast.character_generator', icon="FILE_REFRESH")
                
                # Automodelling tools
                
                if mblab_humanoid.exists_measure_database():
                    if gui_active_panel != "automodelling":
                        box_act_tools_sub.operator('mbast.button_automodelling_on', icon=icon_expand)
                    else:
                        box_act_tools_sub.operator('mbast.button_automodelling_off', icon=icon_collapse)
                        box_auto = self.layout.box()
                        box_auto.operator("mbast.auto_modelling", icon='OUTLINER_DATA_MESH')
                        box_auto.operator("mbast.auto_modelling_mix", icon='OUTLINER_OB_MESH')
                else:
                    box_auto = self.layout.box()
                    box_auto.enabled = False
                    box_auto.label(text="Automodelling not available for this character", icon='INFO')
                
                # Body measures
                
                box_act_tools_sub.label(text="CHARACTER DESIGN", icon="RNA")
                if gui_active_panel_middle != "parameters":
                    box_act_tools_sub.operator('mbast.button_parameters_on', icon=icon_expand)
                else:
                    box_act_tools_sub.operator('mbast.button_parameters_off', icon=icon_collapse)

                    box_param = self.layout.box()
                    mblab_humanoid.bodydata_realtime_activated = True
                    if mblab_humanoid.exists_measure_database():
                        box_param.prop(scn, 'mblab_show_measures', icon='SNAP_INCREMENT')
                    split = box_param.split()

                    col = split.column()
                    col.label(text="PARAMETERS")
                    col.prop(scn, "morphingCategory")

                    for prop in mblab_humanoid.get_properties_in_category(scn.morphingCategory):
                        if hasattr(obj, prop) and not prop.startswith("Expressions_ID"):
                            col.prop(obj, prop)

                    if mblab_humanoid.exists_measure_database() and scn.mblab_show_measures:
                        col = split.column()
                        col.label(text="DIMENSIONS")
                        #col.label(text="Experimental feature", icon='ERROR')
                        col.prop(obj, 'mblab_use_inch')
                        col.prop(scn, 'mblab_measure_filter')
                        col.operator("mbast.measures_apply", icon='FILE_REFRESH')

                        if obj.mblab_use_inch:
                            a_inch = getattr(obj, "body_height_Z", 0)
                            m_feet = int(a_inch / 12)
                            m_inch = int(a_inch % 12)
                            col.label(text="Height: {0}ft {1}in ({2}in)".format(m_feet, m_inch, round(a_inch, 3)))
                        else:
                            col.label(text="Height: {0} cm".format(round(getattr(obj, "body_height_Z", 0), 3)))
                        for measure in sorted(mblab_humanoid.measures.keys()):
                            if measure != "body_height_Z":
                                if hasattr(obj, measure):
                                    if scn.mblab_measure_filter in measure:
                                        col.prop(obj, measure)

                        col.operator("mbast.export_measures", icon='EXPORT')
                        col.operator("mbast.import_measures", icon='IMPORT')

                    sub = box_param.box()
                    sub.label(text="RESET")
                    sub.operator("mbast.reset_categoryonly", icon="RECOVER_LAST")
                
                # Poses
                
                if mblab_humanoid.exists_rest_poses_database():
                    if gui_active_panel_middle != "rest_pose":
                        box_act_tools_sub.operator('mbast.button_rest_pose_on', icon=icon_expand)
                    else:
                        box_act_tools_sub.operator('mbast.button_rest_pose_off', icon=icon_collapse)
                        box_act_pose = self.layout.box()

                        if utils.is_ik_armature(armature):
                            box_act_pose.enabled = False
                            box_act_pose.label(text="Rest poses are not available for IK armatures", icon='INFO')
                        else:
                            box_act_pose.enabled = True
                            box_act_pose.prop(armature, "rest_pose")

                            box_act_pose.operator("mbast.restpose_load", icon='IMPORT')
                            box_act_pose.operator("mbast.restpose_save", icon='EXPORT')
                
                # Skin editor
                
                if gui_active_panel_middle != "skin":
                    box_act_tools_sub.operator('mbast.button_skin_on', icon=icon_expand)
                else:
                    box_act_tools_sub.operator('mbast.button_skin_off', icon=icon_collapse)

                    box_skin = self.layout.box()
                    box_skin.enabled = True
                    if scn.render.engine != 'CYCLES' and scn.render.engine != 'BLENDER_EEVEE':
                        box_skin.enabled = False
                        box_skin.label(text="Skin editor requires Cycles or EEVEE", icon='INFO')

                    if mblab_humanoid.exists_displace_texture():
                        box_skin.operator("mbast.skindisplace_calculate", icon='MOD_DISPLACE')
                        box_skin.label(text="Enable Displacement Preview to view updates", icon='INFO')

                    for material_data_prop in sorted(mblab_humanoid.character_material_properties.keys()):
                        box_skin.prop(obj, material_data_prop)
                
                # Finalize character
                box_act_tools_sub.label(text="OTHERS", icon="RNA")
                if gui_active_panel_display != "finalize":
                    box_act_tools_sub.operator('mbast.button_finalize_on', icon=icon_expand)
                else:
                    box_act_tools_sub.operator('mbast.button_finalize_off', icon=icon_collapse)
                    box_fin = self.layout.box()
                    box_fin.prop(scn, 'mblab_save_images_and_backup', icon='EXPORT')
                    box_fin.prop(scn, 'mblab_remove_all_modifiers', icon='CANCEL')
                    box_fin.prop(scn, 'mblab_final_prefix')
                    if scn.mblab_save_images_and_backup:
                        box_fin.operator("mbast.finalize_character_and_images", icon='FREEZE')
                    else:
                        box_fin.operator("mbast.finalize_character", icon='FREEZE')
                
                # File tools
                
                if gui_active_panel_display != "file":
                    box_act_tools_sub.operator('mbast.button_file_on', icon=icon_expand)
                else:
                    box_act_tools_sub.operator('mbast.button_file_off', icon=icon_collapse)
                    box_file = self.layout.box()
                    box_file.prop(scn, 'mblab_show_texture_load_save', icon='TEXTURE')
                    if scn.mblab_show_texture_load_save:

                        if mblab_humanoid.exists_dermal_texture():
                            box_file_drtx = box_file.box()
                            box_file_drtx.label(text="Dermal texture")
                            box_file_drtx.operator("mbast.export_dermimage", icon='EXPORT')
                            box_file_drtx.operator("mbast.import_dermal", icon='IMPORT')

                        if mblab_humanoid.exists_displace_texture():
                            box_file_dstx = box_file.box()
                            box_file_dstx.label(text="Displacement texture")
                            box_file_dstx.operator("mbast.export_dispimage", icon='EXPORT')
                            box_file_dstx.operator("mbast.import_displacement", icon='IMPORT')

                        box_file_exp = box_file.box()
                        box_file_exp.label(text="Export all images used in skin shader")
                        box_file_exp.operator("mbast.export_allimages", icon='EXPORT')
                    box_file.prop(scn, 'mblab_export_proportions', icon='PRESET')
                    box_file.prop(scn, 'mblab_export_materials', icon='MATERIAL')
                    box_file.operator("mbast.export_character", icon='EXPORT')
                    box_file.operator("mbast.import_character", icon='IMPORT')
                
                # Display character
                
                if gui_active_panel_display != "display_opt":
                    box_act_tools_sub.operator('mbast.button_display_on', icon=icon_expand)
                else:
                    box_act_tools_sub.operator('mbast.button_display_off', icon=icon_collapse)
                    box_disp = self.layout.box()

                    if mblab_humanoid.exists_displace_texture():
                        if mblab_humanoid.get_disp_visibility() is False:
                            box_disp.operator("mbast.displacement_enable", icon='MOD_DISPLACE')
                        else:
                            box_disp.operator("mbast.displacement_disable", icon='X')
                    if mblab_humanoid.get_subd_visibility() is False:
                        box_disp.operator("mbast.subdivision_enable", icon='MOD_SUBSURF')
                        box_disp.label(text="Subd. preview is very CPU intensive", icon='INFO')
                    else:
                        box_disp.operator("mbast.subdivision_disable", icon='X')
                        box_disp.label(text="Disable subdivision to increase performance", icon='ERROR')
                    if mblab_humanoid.get_smooth_visibility() is False:
                        box_disp.operator("mbast.corrective_enable", icon='MOD_SMOOTH')
                    else:
                        box_disp.operator("mbast.corrective_disable", icon='X')

                self.layout.separator(factor=0.5)
                self.layout.label(text="AFTER-CREATION TOOLS", icon="MODIFIER_ON")
                layout_sub=self.layout.box()
                layout_sub.label(text="FINALIZED characters ONLY", icon="INFO")

            else:
                gui_status = "NEW_SESSION"

# MB-Lab Secondary GUI
class VIEW3D_PT_tools_MBCrea(bpy.types.Panel):
    bl_label = "MB-Dev {0}.{1}.{2}".format(bl_info["version"][0], bl_info["version"][1], bl_info["version"][2])
    bl_idname = "OBJECT_PT_characters02"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = 'objectmode'
    bl_category = "MB-Lab"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.mode in {'OBJECT', 'POSE'}

    def draw(self, context):
        scn = bpy.context.scene
        is_objet, name = algorithms.looking_for_humanoid_obj()
        icon_expand = "DISCLOSURE_TRI_RIGHT"
        icon_collapse = "DISCLOSURE_TRI_DOWN"
        
        box_general = self.layout.box()
        box_general.label(text="https://www.mblab.dev")
        #box_general.operator('mbcrea.button_for_tests', icon='BLENDER')

        box_tools = self.layout.box()
        box_tools.label(text="TOOLS CATEGORIES", icon="RNA")
        box_tools.operator('mbcrea.button_import_shape_keys', icon='EXPORT')
        box_tools.prop(scn, "mblab_copy_to_all_phenotype")
        box_tools.prop(scn, "mblab_override_expressions")
        if gui_active_panel_first != "adaptation_tools":
            box_tools.operator('mbcrea.button_adaptation_tools_on', icon=icon_expand)
        else:
            box_tools.operator('mbcrea.button_adaptation_tools_off', icon=icon_collapse)
            box_adaptation_tools = self.layout.box()
            box_adaptation_tools.label(text="Before finalization", icon='MODIFIER_ON')
            box_adaptation_tools.prop(scn, "mbcrea_before_edition_tools")
            #------------Morph creator------------
            if scn.mbcrea_before_edition_tools == "Morphcreator":
                box_morphcreator = self.layout.box()
                if is_objet == "FOUND":
                    box_morphcreator.operator("mbast.reset_allproperties", icon="RECOVER_LAST") # Reset character.
                    box_morphcreator.operator('mbast.button_store_base_vertices', icon="SPHERE") #Store all vertices of the actual body.
                    box_morphcreator.label(text="Morph wording - Body parts", icon='SORT_ASC')
                    box_morphcreator.prop(scn, "mblab_body_part_name") #first part of the morph's name : jaws, legs, ...
                    box_morphcreator.prop(scn, 'mblab_morph_name') #name for the morph
                    box_morphcreator.prop(scn, "mblab_morph_min_max") #The morph is for min proportions or max proportions.
                    if len(scn.mblab_morph_name) > 0:
                        morph_label = "Morph name : " + morphcreator.get_body_parts(scn.mblab_body_part_name)
                        morph_label += "_" + scn.mblab_morph_name
                        morph_label += "_" + morphcreator.get_min_max(scn.mblab_morph_min_max)                    
                        box_morphcreator.label(text=morph_label, icon='INFO')
                    else:
                        box_morphcreator.label(text="Name needed !", icon='ERROR')
                    box_morphcreator.label(text="Morph wording - File", icon='SORT_ASC')
                    box_morphcreator.prop(scn, "mblab_morphing_spectrum") #Ask if the new morph is global or just for a specific body
                    spectrum = morphcreator.get_spectrum(scn.mblab_morphing_spectrum)
                    box_morphcreator.prop(scn, 'mblab_morphing_body_type') #The name of the type (4 letters)
                    splitted = algorithms.split_name(scn.mblab_morphing_body_type)
                    if len(splitted) > 3:
                        box_morphcreator.label(text="(Delete to reset the name)", icon='BLANK1')
                    elif len(splitted) > 0:
                        box_morphcreator.label(text="4 letters please (but that'll do)", icon='BLANK1')
                    box_morphcreator.prop(scn, 'mblab_morphing_file_extra_name') #The extra name for the file (basically the name of the author)
                    txt = "File name : "
                    if spectrum == "Gender":
                        txt += morphcreator.get_model_and_gender()
                        if len(scn.mblab_morphing_file_extra_name) > 0:
                            txt += "_" + scn.mblab_morphing_file_extra_name
                        box_morphcreator.label(text=txt, icon='INFO')
                    else:
                        if len(splitted) > 0:
                            txt +=  morphcreator.get_body_type().split('_')[0] + "_" + splitted + "_morphs"
                        else:
                            txt += morphcreator.get_body_type() + "_morphs"
                        if len(scn.mblab_morphing_file_extra_name) > 0:
                            txt += "_" + scn.mblab_morphing_file_extra_name
                        box_morphcreator.label(text=txt, icon='INFO')
                    box_morphcreator.prop(scn, 'mblab_incremental_saves') #If user wants to overide morph in final file or not.
                    box_morphcreator.operator('mbast.button_store_work_in_progress', icon="MONKEY") #Store all vertices of the modified body in a work-in-progress file.
                    box_morphcreator.operator('mbast.button_save_final_morph', icon="FREEZE") #Save the final morph.
                    box_morphcreator.label(text="Tools", icon='SORT_ASC')
                    box_morphcreator.operator('mbast.button_save_body_as_is', icon='EXPORT')
                    box_morphcreator.operator('mbast.button_load_base_body', icon='IMPORT')
                    box_morphcreator.operator('mbast.button_load_sculpted_body', icon='IMPORT')
                else:
                    box_morphcreator.label(text="!NO COMPATIBLE MODEL!", icon='ERROR')
                    box_morphcreator.enabled = False
            #----------Combined Morph creator-----------
            elif scn.mbcrea_before_edition_tools == "Comb_morphcreator":
                box_comb_morphcreator = self.layout.box()
                if is_objet == "FOUND":
                    box_comb_morphcreator.operator("mbast.reset_allproperties", icon="RECOVER_LAST")
                    box_comb_morphcreator.operator('mbast.button_store_base_vertices', icon="SPHERE")
                    #box_comb_morphcreator.separator(factor=0.5)
                    box_comb_morphcreator.label(text="Morph wording - Mix bases", icon='SORT_ASC')
                    box_comb_morphcreator.prop(scn, "mbcrea_mixing_morphs_number")
                    nb = int(scn.mbcrea_mixing_morphs_number)
                    # If 2 combined morphs or more
                    box_comb_morphcreator.prop(scn, "morphingCategory")
                    cat = algorithms.get_enum_property_item(scn.morphingCategory, get_categories_enum())
                    items_1, minmax_1 = morphs_items_minmax(box_comb_morphcreator, "mbcrea_morphs_items_1", "mbcrea_morphs_minmax_1")
                    check_name_1 = algorithms.get_enum_property_item(scn.mbcrea_morphs_items_1, items_1)
                    check_minmax_1 = algorithms.get_enum_property_item(scn.mbcrea_morphs_minmax_1, minmax_1)
                    combined_name = check_name_1
                    combined_minmax = check_minmax_1
                    check_fail_1 = morphcreator.is_modifier_combined_morph(mblab_humanoid, combined_name, cat)
                    #
                    items_2, minmax_2 = morphs_items_minmax(box_comb_morphcreator, "mbcrea_morphs_items_2", "mbcrea_morphs_minmax_2")
                    check_name_2 = morphcreator.secure_modifier_name(scn.mbcrea_morphs_items_2, items_2)
                    check_minmax_2 = algorithms.get_enum_property_item(scn.mbcrea_morphs_minmax_2, minmax_2)
                    combined_name += "-" + check_name_2.split("_")[1]
                    combined_minmax += "-" + check_minmax_2
                    check_fail_2 = morphcreator.is_modifier_combined_morph(mblab_humanoid, check_name_2, cat)
                    # If 3 combined morphs or more
                    check_name_3 = ""
                    check_minmax_3 = ""
                    check_fail_3 = False
                    if nb > 2:
                        items_3, minmax_3 = morphs_items_minmax(box_comb_morphcreator, "mbcrea_morphs_items_3", "mbcrea_morphs_minmax_3")
                        check_name_3 = morphcreator.secure_modifier_name(scn.mbcrea_morphs_items_3, items_3)
                        check_minmax_3 = algorithms.get_enum_property_item(scn.mbcrea_morphs_minmax_3, minmax_3)
                        combined_name += "-" + check_name_3.split("_")[1]
                        combined_minmax += "-" + check_minmax_3
                        check_fail_3 = morphcreator.is_modifier_combined_morph(mblab_humanoid, check_name_3, cat)
                    # If 4 combined morphs
                    check_name_4 = ""
                    check_minmax_4 = ""
                    check_fail_4 = False
                    if nb > 3:
                        items_4, minmax_4 = morphs_items_minmax(box_comb_morphcreator, "mbcrea_morphs_items_4", "mbcrea_morphs_minmax_4")
                        check_name_4 = morphcreator.secure_modifier_name(scn.mbcrea_morphs_items_4, items_4)
                        check_minmax_4 = algorithms.get_enum_property_item(scn.mbcrea_morphs_minmax_4, minmax_4)
                        combined_name += "-" + check_name_4.split("_")[1]
                        combined_minmax += "-" + check_minmax_4
                        check_fail_4 = morphcreator.is_modifier_combined_morph(mblab_humanoid, check_name_4, cat)
                    # Checks validity and prepare save file.
                    fail = False # If user chooses a morph that is already in combined morph.
                    if check_fail_1:
                        fail = True
                        box_comb_morphcreator.label(text="1st invalid ! ", icon='ERROR')
                    if check_fail_2:
                        fail = True
                        box_comb_morphcreator.label(text="2nd invalid ! ", icon='ERROR')
                    if check_fail_3:
                        fail = True
                        box_comb_morphcreator.label(text="3rd invalid ! ", icon='ERROR')
                    if check_fail_4:
                        fail = True
                        box_comb_morphcreator.label(text="4th invalid ! ", icon='ERROR')
                    final_morph_name = combined_name + "_" + combined_minmax
                    #
                    if not fail:
                        box_comb_morphcreator.label(text="Combined name : " + final_morph_name, icon='INFO')
                        box_comb_morphcreator.label(text="(Reminder : Keep alphabetical order)", icon='FORWARD')
                        # Now we update the model + new button for that.
                        morphcreator.set_modifiers_for_combined_morphs(final_morph_name, [check_name_1, check_name_2, check_name_3, check_name_4], [check_minmax_1, check_minmax_2, check_minmax_3, check_minmax_4])
                        box_comb_morphcreator.operator("mbcrea.update_comb_morphs", icon="MONKEY")
                        # Same elements that come from regular morphs
                        box_comb_morphcreator.label(text="Morph wording - File", icon='SORT_ASC')
                        box_comb_morphcreator.prop(scn, "mblab_morphing_spectrum") #Ask if the new morph is global or just for a specific body
                        spectrum = morphcreator.get_spectrum(scn.mblab_morphing_spectrum)
                        txt = "File name : "
                        if spectrum == "Gender":
                            txt += morphcreator.get_model_and_gender()
                        else:
                            box_comb_morphcreator.prop(scn, 'mblab_morphing_body_type') #The name of the type (4 letters)
                            if len(scn.mblab_morphing_body_type) > 3:
                                box_comb_morphcreator.label(text="(delete to reset the name)", icon='BLANK1')
                            elif len(scn.mblab_morphing_body_type) > 0:
                                box_comb_morphcreator.label(text="4 letters please (but that'll do)", icon='BLANK1')
                            if len(scn.mblab_morphing_body_type) > 0:
                                txt +=  morphcreator.get_body_type().split('_')[0] + "_" + scn.mblab_morphing_body_type + "_morphs"
                            else:
                                txt += morphcreator.get_body_type() + "_morphs"
                        box_comb_morphcreator.prop(scn, 'mblab_morphing_file_extra_name') #The extra name for the file (basically the name of the author)
                        if len(scn.mblab_morphing_file_extra_name) > 0:
                            txt += "_" + scn.mblab_morphing_file_extra_name
                        box_comb_morphcreator.label(text=txt, icon='INFO')
                        box_comb_morphcreator.prop(scn, 'mblab_incremental_saves') #If user wants to overide morph in final file or not.
                        box_comb_morphcreator.operator('mbast.button_store_work_in_progress', icon="MONKEY") #Store all vertices of the modified body in a work-in-progress file.
                        box_comb_morphcreator.operator('mbcrea.button_save_final_comb_morph', icon="FREEZE") #Save the final morph.
                    else:
                        box_comb_morphcreator.label(text="You cannot save while there are warnings ! ", icon='ERROR')
                    box_comb_morphcreator.label(text="Tools", icon='SORT_ASC')
                    box_comb_morphcreator.operator('mbast.button_save_body_as_is', icon='EXPORT')
                    box_comb_morphcreator.operator('mbast.button_load_base_body', icon='IMPORT')
                    box_comb_morphcreator.operator('mbast.button_load_sculpted_body', icon='IMPORT')
                else:
                    box_comb_morphcreator.label(text="!NO COMPATIBLE MODEL!", icon='ERROR')
                    box_comb_morphcreator.enabled = False
            #------Age/Fat/Muscle Creator------
            elif scn.mbcrea_before_edition_tools == "agemasstone_creator":
                box_agemasstone = self.layout.box()
                if is_objet == "FOUND":
                    mblab_humanoid.bodydata_realtime_activated = True
                    obj = mblab_humanoid.get_object()
                    box_agemasstone.operator("mbast.reset_allproperties", icon="RECOVER_LAST")
                    #---------- Now the tool itself
                    box_agemasstone.label(text="Selection", icon='SORT_ASC')
                    box_agemasstone_sub = box_agemasstone.box()
                    box_agemasstone_sub.prop(scn, "transforMorphingCategory")
                    for prop in mblab_humanoid.get_properties_in_category(scn.transforMorphingCategory):
                        if hasattr(obj, prop):
                            box_agemasstone_sub.prop(obj, prop)
                    #---------- The name
                    box_agemasstone.label(text="Tool wording - Content", icon='SORT_ASC')
                    box_agemasstone.prop(scn, "mbcrea_transfor_category")
                    box_agemasstone.prop(scn, "mbcrea_transfor_minmax")
                    #---------- The name and file
                    box_agemasstone.label(text="Tool wording - File", icon='SORT_ASC')
                    box_agemasstone.prop(scn, 'mbcrea_agemasstone_name')
                    box_agemasstone.label(text="File saved under " + os.path.join("data", "transformations"), icon='INFO')
                    if len(scn.mbcrea_agemasstone_name) > 0:
                        tmp = morphcreator.get_model_and_gender().split("_")
                        agemasstone_name = tmp[0] + "_" + tmp[1] + "_" + algorithms.split_name(scn.mbcrea_agemasstone_name.lower()) + "_transf"
                        box_agemasstone.label(text="File name : " + agemasstone_name, icon="INFO")
                        #---------- Saving file
                        box_agemasstone.label(text="Load / Save", icon='SORT_ASC')
                        box_agemasstone.operator('mbcrea.button_transfor_load', icon='MONKEY')
                        box_agemasstone.operator('mbcrea.button_transfor_save', icon='FREEZE')
                    else:
                        box_agemasstone.label(text="Name needed ! ", icon="ERROR")
                    #---------- Tools
                    box_agemasstone.label(text="Tools", icon='SORT_ASC')
                    box_agemasstone.operator('mbcrea.button_check_transf', icon='IMPORT')
                    if len(scn.mbcrea_agemasstone_name) > 0:
                        box_agemasstone.operator('mbcrea.button_transfor_save_current', icon='FREEZE')
                    box_agemasstone.operator('mbcrea.button_load_transf', icon='IMPORT')
                else:
                    box_agemasstone.label(text="! NO COMPATIBLE MODEL !", icon='ERROR')
                    box_agemasstone.enabled = False
            #----------Fast creators-----------
            elif scn.mbcrea_before_edition_tools == "fast_creators":
                box_fast_creators = self.layout.box()
                if is_objet == "FOUND":
                    mblab_humanoid.bodydata_realtime_activated = True
                    obj = mblab_humanoid.get_object()
                    box_fast_creators.operator("mbast.reset_allproperties", icon="RECOVER_LAST")
                    #----------
                    box_fast_creators_sub = box_fast_creators.box()
                    if mblab_humanoid.exists_transform_database():
                        x_age = getattr(obj, 'character_age', 0)
                        x_mass = getattr(obj, 'character_mass', 0)
                        x_tone = getattr(obj, 'character_tone', 0)
                        age_lbl = round((15.5 * x_age ** 2) + 31 * x_age + 33)
                        mass_lbl = round(50 * (x_mass + 1))
                        tone_lbl = round(50 * (x_tone + 1))
                        lbl_text = "Age : {0} yr.  Mass : {1}%  Tone : {2}% ".format(age_lbl, mass_lbl, tone_lbl)
                        box_fast_creators_sub.label(text=lbl_text)

                        for meta_data_prop in sorted(mblab_humanoid.character_metaproperties.keys()):
                            if "last" not in meta_data_prop:
                                box_fast_creators_sub.prop(obj, meta_data_prop)
                    else:
                        box_fast_creators_sub.label(text="No transform database !", icon="ERROR")
                    #----------
                    box_fast_creators_sub.prop(scn, "morphingCategory")
                    for prop in mblab_humanoid.get_properties_in_category(scn.morphingCategory):
                        if hasattr(obj, prop) and not prop.startswith("Expressions_"):
                            box_fast_creators_sub.prop(obj, prop)
                    box_fast_creators_sub.operator("mbast.reset_categoryonly", icon="RECOVER_LAST")
                    #----------
                    box_fast_creators.separator(factor=0.2)
                    box_fast_creators.label(text="Phenotype Creator", icon='SORT_ASC')
                    body_type = morphcreator.get_body_type()
                    path = os.path.join("data", "phenotypes", body_type + "_ptypes")
                    box_fast_creators.label(text="File saved under " + path, icon='INFO')
                    box_fast_creators.label(text="(age, mass & tone useless here)", icon='FORWARD')
                    box_fast_creators.prop(scn, 'mbcrea_phenotype_name_filter')
                    if len(scn.mbcrea_phenotype_name_filter) > 0:
                        pheno_name = algorithms.split_name(scn.mbcrea_phenotype_name_filter, '-²&=¨^$£%µ,?;!§+*/').lower()
                        box_fast_creators.label(text="Name : " + pheno_name, icon='INFO')
                        if morphcreator.is_phenotype_exists(body_type, pheno_name):
                            box_fast_creators.label(text="File already exists !", icon='ERROR')
                        box_fast_creators.operator('mbcrea.button_save_phenotype', icon="FREEZE")
                    #----------
                    box_fast_creators.separator(factor=0.5)
                    box_fast_creators.label(text="Preset Creator", icon='SORT_ASC')
                    preset_folder = mblab_humanoid.presets_data_folder
                    path = os.path.join("data", "presets", preset_folder)
                    box_fast_creators.label(text="File saved under " + path, icon='INFO')
                    box_fast_creators.label(text="(age, mass & tone are used here)", icon='FORWARD')
                    box_fast_creators.prop(scn, 'mbcrea_preset_name_filter')
                    if len(scn.mbcrea_preset_name_filter) > 0:
                        box_fast_creators.prop(scn, 'mbcrea_integrate_material')
                        if scn.mbcrea_integrate_material:
                            box_skin = box_fast_creators.box()
                            box_skin.enabled = True
                            if scn.render.engine != 'CYCLES' and scn.render.engine != 'BLENDER_EEVEE':
                                box_skin.enabled = False
                                box_skin.label(text="Skin editor requires Cycles or EEVEE", icon='INFO')
                            if mblab_humanoid.exists_displace_texture():
                                box_skin.operator("mbast.skindisplace_calculate", icon='MOD_DISPLACE')
                                box_skin.label(text="Enable Displacement Preview to view updates", icon='INFO')
                            for material_data_prop in sorted(mblab_humanoid.character_material_properties.keys()):
                                box_skin.prop(obj, material_data_prop)
                        box_fast_creators.prop(scn, 'mbcrea_special_preset') # Common or Special ?
                        preset_name = ""
                        if scn.mbcrea_special_preset:
                            preset_name = "special"
                        tmp = algorithms.split_name(scn.mbcrea_preset_name_filter, '-²&=¨^$£%µ,?;!§+*/').lower()
                        if not tmp.startswith("type_"):
                            preset_name += "type_"
                        preset_name += tmp
                        box_fast_creators.label(text="Name : " + preset_name, icon='INFO')
                        if morphcreator.is_preset_exists(preset_folder, preset_name):
                            box_fast_creators.label(text="File already exists !", icon='ERROR')
                        box_fast_creators.operator('mbcrea.button_save_preset', icon="FREEZE")
                else:
                    box_fast_creators.label(text="! NO COMPATIBLE MODEL !", icon='ERROR')
                    box_fast_creators.enabled = False
            #------------Expressions creator------------
            elif scn.mbcrea_before_edition_tools == "morphs_for_expressions":
                box_morphexpression = self.layout.box()
                if is_objet == "FOUND":
                    box_morphexpression.operator('mbast.button_store_base_vertices', icon="SPHERE") #Store all vertices of the actual body.
                    box_morphexpression.label(text="Expr. wording - Name", icon='SORT_ASC')
                    box_morphexpression.prop(scn, "mbcrea_standard_base_expr")
                    final_name = "Expressions_" + mbcrea_expressionscreator.get_standard_base_expr(scn.mbcrea_standard_base_expr)
                    if scn.mbcrea_standard_base_expr == 'OT':
                        box_morphexpression.prop(scn, "mbcrea_body_part_expr")
                        final_name = "Expressions_" + mbcrea_expressionscreator.get_body_parts_expr(scn.mbcrea_body_part_expr)
                        if scn.mbcrea_body_part_expr == 'OT':
                            box_morphexpression.prop(scn, "mbcrea_new_base_expr_name")
                            final_name = "Expressions_" + scn.mbcrea_new_base_expr_name.lower()
                        box_morphexpression.prop(scn, "mbcrea_expr_name")
                        final_name += scn.mbcrea_expr_name.capitalize()
                        box_morphexpression.prop(scn, "mbcrea_min_max_expr")
                        if scn.mbcrea_min_max_expr == 'MI':
                            box_morphexpression.label(text="Reminder, min only not allowed.", icon='INFO')
                        final_name += "_" + mbcrea_expressionscreator.get_min_max_expr(scn.mbcrea_min_max_expr)
                    if final_name in mbcrea_expressionscreator.get_standard_expressions_list():
                        box_morphexpression.label(text="!WARNING! may overwrite standard expression!", icon='ERROR')
                    mbcrea_expressionscreator.set_expression_name(final_name)
                    box_morphexpression.label(text="Complete name : " + final_name, icon='INFO')
                    #------------------------------
                    box_morphexpression.label(text="Expr. wording - File", icon='SORT_ASC')
                    box_morphexpression.prop(scn, "mbcrea_expr_pseudo")
                    box_morphexpression.prop(scn, 'mbcrea_incremental_saves_expr')
                    box_morphexpression.prop(scn, 'mbcrea_standard_ID_expr')
                    mbcrea_expressionscreator.set_expression_ID(scn.mbcrea_standard_ID_expr)
                    if scn.mbcrea_standard_ID_expr == 'OT':
                        box_morphexpression.prop(scn, "mbcrea_other_ID_expr")
                        mbcrea_expressionscreator.set_expression_ID(scn.mbcrea_other_ID_expr)
                    else:
                        mbcrea_expressionscreator.set_expression_ID(str(scn.mbcrea_standard_ID_expr).capitalize())
                    box_morphexpression.operator('mbast.button_store_work_in_progress', icon="MONKEY") #Store all vertices of the modified expression in a wip.
                    box_morphexpression.operator('mbcrea.button_save_final_base_expression', icon="FREEZE") #Save the final expression.
                    box_morphexpression.label(text="Tools", icon='SORT_ASC')
                    box_morphexpression.operator('mbast.button_save_body_as_is', icon='EXPORT')
                    box_morphexpression.operator('mbast.button_load_base_body', icon='IMPORT')
                    box_morphexpression.operator('mbast.button_load_sculpted_body', icon='IMPORT')
                else:
                    box_morphexpression.label(text="!NO COMPATIBLE MODEL!", icon='ERROR')
                    box_morphexpression.enabled = False
            #------------Combine expressions creator------------
            elif scn.mbcrea_before_edition_tools == "combine_expressions":
                box_combinexpression = self.layout.box()
                if is_objet == "FOUND":
                    obj = algorithms.get_active_body() #to be sure...
                    mblab_humanoid.bodydata_realtime_activated = True
                    #-------------------------------------
                    box_combinexpression.operator("mbcrea.reset_expressionscategory", icon="RECOVER_LAST")
                    box_combinexpression.operator("mbcrea.import_expression", icon='IMPORT')
                    box_combinexpression.label(text="Base expressions", icon='SORT_ASC')
                    #--------- Expression filter ---------
                    box_combinexpression.prop(scn, 'mbcrea_base_expression_filter')
                    sorted_expressions = sorted(mblab_humanoid.get_properties_in_category("Expressions"))
                    if len(str(scn.mbcrea_base_expression_filter)) > 0:
                        for expr_name in sorted_expressions:
                            if hasattr(obj, expr_name) and scn.mbcrea_base_expression_filter in expr_name and not expr_name.startswith("Expressions_ID"):
                                    box_combinexpression.prop(obj, expr_name)
                    #-------- Expression enumProp --------
                    else:
                        box_combinexpression.prop(scn, 'expressionsSubCategory')
                        props = sorted(mbcrea_expressionscreator.get_items_in_sub(scn.expressionsSubCategory), reverse = True)
                        for prop in props:
                            if hasattr(obj, prop):
                                box_combinexpression.prop(obj, prop)
                    #-------- New expression name --------
                    box_combinexpression.label(text="Expr. wording - Name", icon='SORT_ASC')
                    box_combinexpression.prop(scn, 'mbcrea_comb_expression_filter')
                    comb_name = str(scn.mbcrea_comb_expression_filter).lower()
                    comb_name = algorithms.split_name(comb_name, splitting_char=mbcrea_expressionscreator.forbidden_char_list)
                    box_combinexpression.label(text="File name : " + comb_name, icon='INFO')
                    check_root = mblab_humanoid.get_root_model_name()
                    if mbcrea_expressionscreator.is_comb_expression_exists(check_root, comb_name):
                        box_combinexpression.label(text="File already exists !", icon='ERROR')
                    #-------- New expression file --------
                    box_combinexpression.label(text="Expr. wording - File", icon='SORT_ASC')
                    if len(comb_name) < 1:
                        box_combinexpression.label(text="Choose a name !", icon='ERROR')
                    else:
                        box_combinexpression.label(text="Save in : " + mblab_humanoid.get_root_model_name(), icon='INFO')
                        box_combinexpression.operator('mbcrea.button_save_final_comb_expression', icon="FREEZE") #Save the final expression.
                else:
                    box_combinexpression.label(text="!NO COMPATIBLE MODEL!", icon='ERROR')
                    box_combinexpression.enabled = False
                
            # Copy / Move / Delete utilities.
            elif scn.mbcrea_before_edition_tools == "cmd_utilities":
                box_cmd_morphs = self.layout.box()
                if is_objet == "FOUND":
                    box_cmd_morphs.operator("mbcrea.rescan_morph_files", icon="RECOVER_LAST")
                    # -------------------
                    box_cmd_morphs.label(text="Morph file source", icon='SORT_ASC')
                    box_cmd_morphs.prop(scn, "mbcrea_cmd_spectrum") #Ask if the new morph is global or just for a specific body
                    spectrum = morphcreator.get_spectrum(scn.mbcrea_cmd_spectrum)
                    if spectrum == "Gender":
                        box_cmd_morphs.prop(scn, "mbcrea_gender_files_in")
                    else:
                        box_cmd_morphs.prop(scn, "mbcrea_body_type_files_in")
                    # -------------------
                    box_cmd_morphs.label(text="File content", icon='SORT_ASC')
                    obj = mblab_humanoid.get_object()
                    box_cmd_morphs.prop(scn, "mbcrea_file_categories_content")
                    box_cmd_morphs_sub = box_cmd_morphs.box()
                    props = []
                    if spectrum == "Gender":
                        props = morphcreator.get_morphs_in_category(scn.mbcrea_gender_files_in, scn.mbcrea_file_categories_content)
                    else:
                        props = morphcreator.get_morphs_in_category(scn.mbcrea_body_type_files_in, scn.mbcrea_file_categories_content)
                    for prop in props:
                        if hasattr(obj, prop):
                            # In case of rescaning, if there are new props,
                            # they can't be displayed, so that's why there's hasattr
                            box_cmd_morphs_sub.prop(obj, prop)
                    # -------------------
                    box_cmd_morphs.label(text="Destination file", icon='SORT_ASC')
                    if spectrum == "Gender":
                        box_cmd_morphs.prop(scn, "mbcrea_gender_files_out")
                        box_cmd_morphs.label(text="New file not allowed", icon='INFO')
                    else:
                        box_cmd_morphs.prop(scn, "mbcrea_body_type_files_out")
                        if scn.mbcrea_body_type_files_out == "NEW":
                            box_cmd_morphs.prop(scn, 'mblab_morphing_body_type') #The name of the type (4 letters)
                            splitted = algorithms.split_name(scn.mblab_morphing_body_type)
                            if len(splitted) < 1:
                                box_cmd_morphs.label(text="Nothing allowed while empty!", icon='ERROR')
                            elif len(splitted) < 4:
                                box_cmd_morphs.label(text="4 letters please (but that'll do)", icon='BLANK1')
                        box_cmd_morphs.prop(scn, 'mblab_morphing_file_extra_name') #The extra name for the file (basically the name of the author)
                    # ------ File name
                    file_name = get_cmd_output_file_name()
                    if len(file_name) > 0:
                        box_cmd_morphs.label(text="File name : " + file_name, icon='INFO')
                    # ---- Counting and preparing content for cmd
                    # -------------------
                    box_cmd_morphs.label(text="Tools", icon='SORT_ASC')
                    box_cmd_morphs.operator('mbcrea.button_backup_morph')
                    if len(file_name) > 0:
                        box_cmd_morphs.label(text="Reminder : No undo !", icon='ERROR')
                        box_cmd_morphs.operator('mbcrea.button_copy_morph')
                        box_cmd_morphs.operator('mbcrea.button_move_morph')
                        box_cmd_morphs.operator('mbcrea.button_delete_morph')
                        # Below : only if ONE simple morph is selected...
                        box_cmd_rename = box_cmd_morphs.box()
                        box_cmd_rename.prop(scn, 'mbcrea_morphing_rename')
                        selected = morphcreator.get_selected_cmd_morphs(get_cmd_input_file_name(), obj)
                        if len(selected) > 0:
                            cat = selected[0].split("_")[0]
                            new_name = algorithms.split_name(scn.mbcrea_morphing_rename, ' _²&=¨^$£%µ,?;!§+*/')
                            box_cmd_rename.label(text="Morph name : " + cat + "_" + new_name + "_min(max)", icon='INFO')
                        box_cmd_rename.operator('mbcrea.button_rename_morph')
                        if len(selected) == 1:
                            box_cmd_rename.enabled = True
                        else:
                            box_cmd_rename.enabled = False
                        # Here
                else:
                    box_cmd_morphs.label(text="!NO COMPATIBLE MODEL!", icon='ERROR')
                    box_cmd_morphs.enabled = False
            #------------Rigify------------
            box_adaptation_tools.label(text="After finalization", icon='MODIFIER_ON')
            box_adaptation_tools.prop(scn, "mbcrea_after_edition_tools")
            if scn.mbcrea_after_edition_tools == "Rigify":
                box_rigify = self.layout.box()
                box_rigify.label(text="#TODO Rigify...")
            #------------Blenrig------------
            elif scn.mbcrea_after_edition_tools == "Blenrig":
                box_blenrig = self.layout.box()
                box_blenrig.label(text="#TODO Blenrig...")
            box_adaptation_tools.separator(factor=0.5)

        #Create/edit tools...
        if gui_active_panel_first != "compat_tools":
            box_tools.operator('mbcrea.button_compat_tools_on', icon=icon_expand)
        else:
            box_tools.operator('mbcrea.button_compat_tools_off', icon=icon_collapse)
            box_compat_tools = self.layout.box()
            #-------------
            if gui_active_panel_second != "Init_compat":
                box_compat_tools.operator('mbcrea.button_init_compat_on', icon=icon_expand)
            else:
                box_compat_tools.operator('mbcrea.button_init_compat_off', icon=icon_collapse)
                box_init = box_compat_tools.box()
                box_init.operator('mbcrea.button_init_compat', icon="ERROR")
            box_compat_tools_sub = box_compat_tools.box()
            if creation_tools_ops.is_project_loaded():
                box_compat_tools_sub.label(text="/data/ directory : " + creation_tools_ops.get_created_name('project_name'), icon='INFO')
                box_compat_tools_sub.label(text="Body full name : " + creation_tools_ops.get_created_name('body'), icon='INFO')
                box_compat_tools_sub.label(text="Body short name : " + creation_tools_ops.get_created_name('body_short'), icon='INFO')
                box_compat_tools_sub.label(text="Gender short name : " + creation_tools_ops.get_created_name('gender'), icon='INFO')
                box_compat_tools_sub.label(text="Gender short name : " + creation_tools_ops.get_created_name('gender_short'), icon='INFO')
                box_compat_tools_sub.label(text="Body type : " + creation_tools_ops.get_created_name('type'), icon='INFO')
            else:
                box_compat_tools_sub.prop(scn, 'mbcrea_project_name')
                box_compat_tools_sub.label(text="New model names", icon='QUESTION')
                box_compat_tools_sub.prop(scn, 'mbcrea_body_name')
                box_compat_tools_sub.prop(scn, 'mbcrea_body_gender')
                box_compat_tools_sub.prop(scn, 'mbcrea_body_type')
                if len(scn.mbcrea_body_name) > 0:
                    body_name = algorithms.split_name(scn.mbcrea_body_name)
                    if body_name not in creation_tools_ops.get_forbidden_names():
                        creation_tools_ops.set_created_name('body', body_name)
                        creation_tools_ops.set_created_name('body_short', body_name[0:2])
                        box_compat_tools_sub.label(text="Body full name : " + body_name, icon='INFO')
                        box_compat_tools_sub.label(text="Body short name : " + creation_tools_ops.get_created_name('body_short'), icon='INFO')
                    else:
                        creation_tools_ops.set_created_name('body', "")
                        creation_tools_ops.set_created_name('body_short', "")
                        box_compat_tools_sub.label(text="Body name not allowed !", icon='ERROR')
                gender_name = creation_tools_ops.get_static_genders(scn.mbcrea_body_gender)
                creation_tools_ops.set_created_name('gender', gender_name)
                creation_tools_ops.set_created_name('gender_short', gender_name[0:1] + "_")
                box_compat_tools_sub.label(text="Gender short name : " + creation_tools_ops.get_created_name('gender_short'), icon='INFO')
                if len(scn.mbcrea_body_type) > 0:
                    body_type = algorithms.split_name(scn.mbcrea_body_type)
                    creation_tools_ops.set_created_name('type', body_type)
                    box_compat_tools_sub.label(text="Body type : " + body_type, icon='INFO')
                else:
                    creation_tools_ops.set_created_name('type', '')
                #-------------
                project_creation_buttons=box_compat_tools_sub.box()
                if len(str(scn.mbcrea_project_name)) > 0:
                    creation_tools_ops.set_created_name("project_name", str(scn.mbcrea_project_name))
                    project_creation_buttons.operator('mbcrea.button_create_directories', icon='FREEZE')
                    project_creation_buttons.operator('mbcrea.button_save_compat_project', icon='FREEZE')
                else:
                    creation_tools_ops.set_created_name("project_name", "")
                    project_creation_buttons.label(text="Choose a project name !", icon='ERROR')
            box_compat_tools_sub.operator('mbcrea.button_load_compat_project', icon='IMPORT')
            
            # Tools about vertex creation
            if gui_active_panel_second != "Vertex_creation":
                box_compat_tools.operator('mbcrea.button_vertex_creation_on', icon=icon_expand)
            else:
                box_compat_tools.operator('mbcrea.button_vertex_creation_off', icon=icon_collapse)
                box_body_tools = self.layout.box()
                box_body_tools.operator('mbast.button_store_base_vertices', icon="SPHERE")
            if gui_active_panel_second != "Bboxes_tools":
                box_compat_tools.operator('mbcrea.button_bboxes_tools_on', icon=icon_expand)
            else:
                box_compat_tools.operator('mbcrea.button_bboxes_tools_off', icon=icon_collapse)
                box_bboxes_tools = self.layout.box()
                box_bboxes_tools.label(text="#TODO bboxes tools...")
            if gui_active_panel_second != "Weight_painting":
                box_compat_tools.operator('mbcrea.button_weight_painting_tools_on', icon=icon_expand)
            else:
                box_compat_tools.operator('mbcrea.button_weight_painting_tools_off', icon=icon_collapse)
                box_weight_painting_tools = self.layout.box()
                box_weight_painting_tools.label(text="#TODO weight painting tools...")
            if gui_active_panel_second != "Vertices_groups":
                box_compat_tools.operator('mbcrea.button_vertices_groups_tools_on', icon=icon_expand)
            else:
                box_compat_tools.operator('mbcrea.button_vertices_groups_tools_off', icon=icon_collapse)
                box_vertices_groups_tools = self.layout.box()
                box_vertices_groups_tools.label(text="#TODO vertices groups tools...")
            if gui_active_panel_second != "Muscles":
                box_compat_tools.operator('mbcrea.button_muscles_tools_on', icon=icon_expand)
            else:
                box_compat_tools.operator('mbcrea.button_muscles_tools_off', icon=icon_collapse)
                box_muscles_tools = self.layout.box()
                box_muscles_tools.label(text="#TODO muscles tools...")
            if gui_active_panel_second != "Config":
                box_compat_tools.operator('mbcrea.button_config_tools_on', icon=icon_expand)
            else:
                box_compat_tools.operator('mbcrea.button_config_tools_off', icon=icon_collapse)
                box_config_tools = self.layout.box()
                box_config_tools.label(text="#TODO config files tools...")
            if gui_active_panel_second != "Files_management":
                box_compat_tools.operator('mbcrea.button_management_tools_on', icon=icon_expand)
            else:
                box_compat_tools.operator('mbcrea.button_management_tools_off', icon=icon_collapse)
                box_management_tools = self.layout.box()
                box_management_tools.label(text="#TODO files management tools...")
        box_tools.separator(factor=0.5)

bpy.types.Scene.mbcrea_project_name = bpy.props.StringProperty(
    name="Project's name",
    description="Like MyProject",
    default=creation_tools_ops.get_created_name('project_name'),
    maxlen=1024,
    subtype='FILE_NAME')

bpy.types.Scene.mbcrea_body_name = bpy.props.StringProperty(
    name="New body's name",
    description="Like MyHuman, NewHorse01",
    default=creation_tools_ops.get_created_name('body'),
    maxlen=1024,
    subtype='FILE_NAME')

bpy.types.Scene.mbcrea_body_gender = bpy.props.EnumProperty(
    items=creation_tools_ops.get_static_genders(),
    name="Gender",
    default="UN")

bpy.types.Scene.mbcrea_body_type = bpy.props.StringProperty(
    name="Body Type",
    description="in 4 letters, like nm01 (North Martian 01)\nNo gender here",
    default=creation_tools_ops.get_created_name('type'),
    maxlen=4,
    subtype='FILE_NAME')

bpy.types.Scene.mbcrea_standard_base_expr = bpy.props.EnumProperty(
    items=mbcrea_expressionscreator.get_standard_base_expr(),
    name="",
    default="CK")

bpy.types.Scene.mbcrea_body_part_expr = bpy.props.EnumProperty(
    items=mbcrea_expressionscreator.get_body_parts_expr(),
    name="Body part",
    default="MO")

bpy.types.Scene.mbcrea_new_base_expr_name = bpy.props.StringProperty(
    name="Part name",
    description="New body part for expression,\nlike ears",
    default="",
    maxlen=1024,
    subtype='FILE_NAME')

bpy.types.Scene.mbcrea_expr_name = bpy.props.StringProperty(
    name="Expression name",
    description="New name for the expression,\nlike Downward",
    default="",
    maxlen=1024,
    subtype='FILE_NAME')

bpy.types.Scene.mbcrea_min_max_expr = bpy.props.EnumProperty(
    items=mbcrea_expressionscreator.get_min_max_expr(),
    name="min/max:",
    default="MA")

bpy.types.Scene.mbcrea_expr_pseudo = bpy.props.StringProperty(
    name="Extra name",
    description="To avoid overwriting existing files\nBasically it's the name of the author",
    default="",
    maxlen=1024,
    subtype='FILE_NAME')

bpy.types.Scene.mbcrea_incremental_saves_expr = bpy.props.BoolProperty(
    name="Autosaves",
    description="Does an incremental save each time\n  the final save button is pressed.\nFrom 001 to 999\nCaution : returns to 001 between sessions")

bpy.types.Scene.mbcrea_standard_ID_expr = bpy.props.EnumProperty(
    items=mbcrea_expressionscreator.get_expression_ID_list(),
    name="Model ID",
    default="HU")

bpy.types.Scene.mbcrea_other_ID_expr = bpy.props.StringProperty(
    name="Other ID",
    description="Another model for the base expression",
    default="CantBeEmpty",
    maxlen=1024,
    subtype='FILE_NAME')

bpy.types.Scene.mbcrea_base_expression_filter = bpy.props.StringProperty(
    name="Filter",
    description="Filter the base expressions available.\nCase sensitive !",
    default="",
    maxlen=1024,
    subtype='FILE_NAME')

bpy.types.Scene.mbcrea_comb_expression_filter = bpy.props.StringProperty(
    name="Name",
    description="Name the new face expression",
    default="",
    maxlen=1024,
    subtype='FILE_NAME')

bpy.types.Scene.mbcrea_mixing_morphs_number = bpy.props.EnumProperty(
    items=[("2", "2", "Means 4 combined to create"),
        ("3", "3", "Means 8 combined to create"),
        ("4", "4", "Means 16 combined to create")],
    name="Base morphs number",
    default="2")

def mbcrea_enum_morph_items_update(self, context):
    obj = mblab_humanoid.get_object()
    props = []
    for prop in mblab_humanoid.get_properties_in_category(bpy.context.scene.morphingCategory):
        if hasattr(obj, prop) and not prop.startswith("Expressions_ID"):
            props.append(prop)
    global mbcrea_combined_morph_list
    mbcrea_combined_morph_list = algorithms.create_enum_property_items(props)
    return mbcrea_combined_morph_list
   
bpy.types.Scene.mbcrea_morphs_items_1 = bpy.props.EnumProperty(
    items=mbcrea_enum_morph_items_update,
    name="",
    default=None,
    options={'ANIMATABLE'},
    )

bpy.types.Scene.mbcrea_morphs_items_2 = bpy.props.EnumProperty(
    items=mbcrea_enum_morph_items_update,
    name="",
    default=None,
    options={'ANIMATABLE'},
    )

bpy.types.Scene.mbcrea_morphs_items_3 = bpy.props.EnumProperty(
    items=mbcrea_enum_morph_items_update,
    name="",
    default=None,
    options={'ANIMATABLE'},
    )

bpy.types.Scene.mbcrea_morphs_items_4 = bpy.props.EnumProperty(
    items=mbcrea_enum_morph_items_update,
    name="",
    default=None,
    options={'ANIMATABLE'},
    )

bpy.types.Scene.mbcrea_morphs_minmax_1 = bpy.props.EnumProperty(
    items=morphcreator.get_min_max(),
    name="",
    default=None,
    )

bpy.types.Scene.mbcrea_morphs_minmax_2 = bpy.props.EnumProperty(
    items=morphcreator.get_min_max(),
    name="",
    default=None,
    )

bpy.types.Scene.mbcrea_morphs_minmax_3 = bpy.props.EnumProperty(
    items=morphcreator.get_min_max(),
    name="",
    default=None,
    )

bpy.types.Scene.mbcrea_morphs_minmax_4 = bpy.props.EnumProperty(
    items=morphcreator.get_min_max(),
    name="",
    default=None,
    )

def morphs_items_minmax(box, items_str, minmax_str):
    sub = box.row(align=True)
    sub.prop(bpy.context.scene, items_str)
    sub.prop(bpy.context.scene, minmax_str)
    return mbcrea_enum_morph_items_update(bpy.context.scene, None), morphcreator.get_min_max()

bpy.types.Scene.mbcrea_phenotype_name_filter = bpy.props.StringProperty(
    name="Name",
    description="The name for the file.",
    default="",
    maxlen=1024,
    subtype='FILE_NAME')

bpy.types.Scene.mbcrea_preset_name_filter = bpy.props.StringProperty(
    name="Name",
    description="The name for the file.\nStarting with type_ is automatic",
    default="",
    maxlen=1024,
    subtype='FILE_NAME')

bpy.types.Scene.mbcrea_integrate_material = bpy.props.BoolProperty(
    name="Integrate material",
    description="You can integrate the material or not.")
    
bpy.types.Scene.mbcrea_special_preset = bpy.props.BoolProperty(
    name="Special",
    description="If the preset is special or common")

bpy.types.Scene.mbcrea_agemasstone_name = bpy.props.StringProperty(
    name="Name",
    description="The name for the file.\nBeginning and ending are automatic",
    default="",
    maxlen=1024,
    subtype='FILE_NAME')

def mbcrea_enum_transfor_category(self, context):
    cat = mblab_humanoid.transformations_data.keys()
    mbcrea_transfor_category_list = []
    for key in cat:
        name = key.split("_")[0]
        if name == "fat":
            name = "Mass"
        elif name == "muscle":
            name = "Tone"
        mbcrea_transfor_category_list.append((key, name, name))
    return mbcrea_transfor_category_list
   

bpy.types.Scene.mbcrea_transfor_category = bpy.props.EnumProperty(
    items=mbcrea_enum_transfor_category,
    name="Save for",
    default=None,
    options={'ANIMATABLE'},
    )

bpy.types.Scene.mbcrea_transfor_minmax = bpy.props.EnumProperty(
    items=morphcreator.min_max,
    name="-1 to +1",
    default=None,
    )

bpy.types.Scene.mbcrea_gender_files_out = bpy.props.EnumProperty(
    items=morphcreator.get_gender_type_files(mblab_humanoid, "Gender"),
    name="Write to",
    default=None)

bpy.types.Scene.mbcrea_body_type_files_out = bpy.props.EnumProperty(
    items=morphcreator.get_gender_type_files(mblab_humanoid, "Type", True),
    name="Write to",
    default=None)

def update_cmd_file(self, context):
    scn = bpy.context.scene
    spectrum = morphcreator.get_spectrum(scn.mbcrea_cmd_spectrum)
    if spectrum == "Gender":
        morphcreator.update_cmd_file(scn.mbcrea_gender_files_in)
    else:
        morphcreator.update_cmd_file(scn.mbcrea_body_type_files_in)
    morphcreator.reset_cmd_morphs(mblab_humanoid.get_object())

bpy.types.Scene.mbcrea_cmd_spectrum = bpy.props.EnumProperty(
    items=morphcreator.get_spectrum(),
    name="Spectrum",
    update=update_cmd_file,
    default="GE")
    
bpy.types.Scene.mbcrea_gender_files_in = bpy.props.EnumProperty(
    items=morphcreator.get_gender_type_files(mblab_humanoid, "Gender"),
    name="Gender",
    update=update_cmd_file,
    default=None)

bpy.types.Scene.mbcrea_body_type_files_in = bpy.props.EnumProperty(
    items=morphcreator.get_gender_type_files(mblab_humanoid, "Type"),
    name="Type",
    update=update_cmd_file,
    default=None)

def get_morph_file_categories(self, context):
    scn = bpy.context.scene
    spectrum = morphcreator.get_spectrum(scn.mbcrea_cmd_spectrum)
    if spectrum == "Gender":
        return morphcreator.get_morph_file_categories(scn.mbcrea_gender_files_in)
    return morphcreator.get_morph_file_categories(scn.mbcrea_body_type_files_in)

def update_cmd_categories(self, context):
    morphcreator.update_cmd_morphs()
    
bpy.types.Scene.mbcrea_file_categories_content = bpy.props.EnumProperty(
    items=get_morph_file_categories,
    name="Category",
    default=None,
    update=update_cmd_categories,
    options={'ANIMATABLE'},
    )

bpy.types.Scene.mbcrea_morphing_rename = bpy.props.StringProperty(
    name="Rename",
    description="New name for the morph without category.\nExample : NewMorph01",
    default="NewName",
    maxlen=1024,
    subtype='FILE_NAME')

bpy.types.Scene.mbcrea_after_edition_tools = bpy.props.EnumProperty(
    items=[
        ("None", "Choose ...", "Tools available after finalization"),
        ("Rigify", "Add Rigify to model", "All tools to add Rigify to the model"),
        ("Blenrig", "Add Blenrig to model", "All tools to add Blenrig to the model")
        ],
    name="",
    default="None",
    )

bpy.types.Scene.mbcrea_before_edition_tools = bpy.props.EnumProperty(
    items=[
        ("None", "Choose ...", "Tools available before finalization"),
        ("Morphcreator", "Simple Morph Creation", "Simple morph creation panel"),
        ("Comb_morphcreator", "Combined Morph Creation", "Combined morph creation panel"),
        ("agemasstone_creator", "Age/Mass/Tone Creation", "Quick tool to create interpolation between\nage, mass (or fat), tone (or muscle)\nand the character."),
        ("fast_creators", "Character Library Creation", "Quick tools to create :\n- Phenotypes\n- Presets\nfor Character Library"),
        ("morphs_for_expressions", "Base Expressions Creation", "Tool for morphing base expressions"),
        ("combine_expressions", "Facial Expressions Creation", "Tool for combining base expressions"),
        ("cmd_utilities", "Copy / Move / Delete morphs", "Utilities to move/copy/delete morphs\nfrom one file to another")
        ],
    name="",
    default="None",
    )

class FinalizeExpression(bpy.types.Operator):
    """
        Working like FinalizeMorph
    """
    bl_label = 'Finalize the base expression'
    bl_idname = 'mbcrea.button_save_final_base_expression'
    filename_ext = ".json"
    bl_description = 'Finalize the expression,\nask for min and max files,\ncreate or open the expression file,\nreplace or append new expression'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        scn = bpy.context.scene
        base = []
        sculpted = []

        try:
            base = morphcreator.get_vertices_list(0)
        except:
            self.ShowMessageBox("Base vertices are not stored !", "Warning", 'ERROR')
            return {'FINISHED'}
        try:
            sculpted = morphcreator.get_vertices_list(1)
        except:
            self.ShowMessageBox("Changed vertices are not stored !", "Warning", 'ERROR')
            return {'FINISHED'}
        indexed_vertices = morphcreator.substract_with_index(base, sculpted)
        if len(indexed_vertices) < 1:
            self.ShowMessageBox("Models base / sculpted are equals !\nNo file saved", "Warning", 'INFO')
            return {'FINISHED'}
        #-------File name----------
        file_name = morphcreator.get_body_type() + "_exprs"
        if len(scn.mbcrea_expr_pseudo) > 0:
            file_name += "_" + scn.mbcrea_expr_pseudo
        if scn.mbcrea_incremental_saves_expr:
            file_name += "_" + mbcrea_expressionscreator.get_next_number()
        #-------Expression name----------
        expression_name = mbcrea_expressionscreator.get_expression_name()
        #-------Expression path----------
        file_path_name = os.path.join(file_ops.get_data_path(), "expressions_morphs", file_name + ".json")
        file = file_ops.load_json_data(file_path_name, "Try to load an expression file")
        if file == None:
            file = {}
        #---Creating new expression-------
        file[mbcrea_expressionscreator.get_expression_name()] = indexed_vertices
        file[mbcrea_expressionscreator.get_expression_ID()] = []
        file_ops.save_json_data(file_path_name, file)
        #----------------------------
        return {'FINISHED'}

    def ShowMessageBox(self, message = "", title = "Message Box", icon = 'INFO'):

        def draw(self, context):
            self.layout.label(text=message)
        bpy.context.window_manager.popup_menu(draw, title = title, icon = icon)

class FinalizeCombExpression(bpy.types.Operator):
    """
        Working like Save character
    """
    bl_label = 'Finalize the face expression'
    bl_idname = 'mbcrea.button_save_final_comb_expression'
    filename_ext = ".json"
    bl_description = 'Finalize the face expression,\ncreate or open the face expression file,\nreplace or create new face expression'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        scn = bpy.context.scene
        mbcrea_expressionscreator.set_lab_version(bl_info["version"])
        #-------File name----------
        comb_name = str(scn.mbcrea_comb_expression_filter).lower()
        comb_name = algorithms.split_name(comb_name, splitting_char=mbcrea_expressionscreator.forbidden_char_list)
        #--expression path + name--
        path = os.path.join(file_ops.get_data_path(), "expressions_comb", mblab_humanoid.get_root_model_name() + "_expressions", comb_name+".json")
        #--------Saving file-------
        mbcrea_expressionscreator.save_face_expression(path)
        return {'FINISHED'}

    def ShowMessageBox(self, message = "", title = "Message Box", icon = 'INFO'):

        def draw(self, context):
            self.layout.label(text=message)
        bpy.context.window_manager.popup_menu(draw, title = title, icon = icon)

class FinalizePhenotype(bpy.types.Operator):
    """
        Working like Save character
    """
    bl_label = 'Finalize the phenotype'
    bl_idname = 'mbcrea.button_save_phenotype'
    filename_ext = ".json"
    bl_description = 'Finalize the phenotype'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        scn = bpy.context.scene
        #-------File name----------
        pheno_name = algorithms.split_name(scn.mbcrea_phenotype_name_filter, '-²&=¨^$£%µ,?;!§+*/').lower()
        #---phenotype path + name--
        path = os.path.join(file_ops.get_data_path(), "phenotypes", morphcreator.get_body_type() + "_ptypes", pheno_name+".json")
        #--------Saving file-------
        morphcreator.save_phenotype(path, mblab_humanoid)
        return {'FINISHED'}

class FinalizePreset(bpy.types.Operator):
    """
        Working like Save character
    """
    bl_label = 'Finalize the preset'
    bl_idname = 'mbcrea.button_save_preset'
    filename_ext = ".json"
    bl_description = 'Finalize the preset'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        scn = bpy.context.scene
        #-------File name----------
        preset_name = algorithms.split_name(scn.mbcrea_preset_name_filter, '-²&=¨^$£%µ,?;!§+*/').lower()
        if not preset_name.startswith("type_"):
            preset_name = "type_" + preset_name
        #----preset path + name----
        path = os.path.join(file_ops.get_data_path(), "presets", mblab_humanoid.presets_data_folder, preset_name+".json")
        #--------Saving file-------
        morphcreator.save_preset(path, mblab_humanoid, scn.mbcrea_integrate_material)
        return {'FINISHED'}

def get_transfor_filepath():
    scn = bpy.context.scene
    if len(scn.mbcrea_agemasstone_name) < 1:
        return None
    tmp = morphcreator.get_model_and_gender().split("_")
    name = tmp[0] + "_" + tmp[1] + "_" + algorithms.split_name(scn.mbcrea_agemasstone_name.lower()) + "_transf.json"
    filepath = os.path.join(file_ops.get_data_path(), "transformations", name)
    return filepath
    
class ButtonTransforSave(bpy.types.Operator):
    bl_label = 'Save step / Finalize'
    bl_idname = 'mbcrea.button_transfor_save'
    bl_description = 'Button for saving content in selected category and morph.\nSame button for a simple step or a finalization'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        mode = bpy.context.active_object.mode
        bpy.ops.object.mode_set(mode='OBJECT')
        scn = bpy.context.scene
        #--------------------
        filepath = get_transfor_filepath()
        if filepath == None:
            return {'FINISHED'}
        mbcrea_transfor.save_transformation(filepath, scn.mbcrea_transfor_category, scn.mbcrea_transfor_minmax)
        return {'FINISHED'}

class ButtonTransforLoad(bpy.types.Operator):
    bl_label = 'Load step'
    bl_idname = 'mbcrea.button_transfor_load'
    bl_description = 'Button for loading content in selected category and morph'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        mode = bpy.context.active_object.mode
        bpy.ops.object.mode_set(mode='OBJECT')
        scn = bpy.context.scene
        #--------------------
        filepath = get_transfor_filepath()
        if filepath == None:
            return {'FINISHED'}
        mbcrea_transfor.load_transformation(filepath, scn.mbcrea_transfor_category, scn.mbcrea_transfor_minmax)
        return {'FINISHED'}

class ButtonCurrentModelTransforSave(bpy.types.Operator):
    """
        Save the transformation database of current model.
    """
    bl_label = 'Export current model'
    bl_idname = 'mbcrea.button_transfor_save_current'
    filename_ext = ".json"
    filter_glob: bpy.props.StringProperty(default="*.json", options={'HIDDEN'},)
    bl_description = 'Export the data base of the current model.\ni.e its data base, not the changes from user.'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        mode = bpy.context.active_object.mode
        bpy.ops.object.mode_set(mode='OBJECT')
        #--------------------
        filepath = get_transfor_filepath()
        if filepath == None:
            return {'FINISHED'}
        mbcrea_transfor.save_current_model(filepath)
        return {'FINISHED'}

class CheckTransformationFile(bpy.types.Operator, ImportHelper):
    """
        Load the file as a transformation.
    """
    bl_label = 'Check compatibility'
    bl_idname = 'mbcrea.button_check_transf'
    filename_ext = ".json"
    filter_glob: bpy.props.StringProperty(default="*.json", options={'HIDDEN'},)
    bl_description = 'Check the compatibility of a file to current model.\nThe result is stored under same directory, same name+.txt'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        mode = bpy.context.active_object.mode
        bpy.ops.object.mode_set(mode='OBJECT')
        if not self.filepath.endswith("_transf.json"):
            self.ShowMessageBox(message = "May not a valid file !")
            return {'FINISHED'}
        #--------------------
        mbcrea_transfor.check_compatibility_with_current_model(self.filepath)
        return {'FINISHED'}
    
    def ShowMessageBox(self, message = "", title = "Error !", icon = 'ERROR'):

        def draw(self, context):
            self.layout.label(text=message)
        bpy.context.window_manager.popup_menu(draw, title = title, icon = icon)
    


class LoadTransformationFile(bpy.types.Operator, ImportHelper):
    """
        Load the file as a transformation.
    """
    bl_label = 'Import for current model'
    bl_idname = 'mbcrea.button_load_transf'
    filename_ext = ".json"
    filter_glob: bpy.props.StringProperty(default="*.json", options={'HIDDEN'},)
    bl_description = 'Load a transformation file for the current model.'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        mode = bpy.context.active_object.mode
        bpy.ops.object.mode_set(mode='OBJECT')
        if not self.filepath.endswith("_transf.json"):
            self.ShowMessageBox(message = "May not a valid file !")
            return {'FINISHED'}
        #--------------------
        mbcrea_transfor.load_transformation_from_file(self.filepath)
        return {'FINISHED'}
    
    def ShowMessageBox(self, message = "", title = "Error !", icon = 'ERROR'):

        def draw(self, context):
            self.layout.label(text=message)
        bpy.context.window_manager.popup_menu(draw, title = title, icon = icon)

class ButtonRescanMorphFiles(bpy.types.Operator):
    bl_label = 'Reset morphs and rescan'
    bl_idname = 'mbcrea.rescan_morph_files'
    bl_description = 'reset all selected morphs and rescan directory + input file'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        morphcreator.reset_cmd_morphs(mblab_humanoid.get_object())
        morphcreator.init_cmd_tools()
        morphcreator.get_all_compatible_files(mblab_humanoid)
        return {'FINISHED'}

class ButtonBackupMorphFile(bpy.types.Operator):
    bl_label = 'Backup morph input file'
    bl_idname = 'mbcrea.button_backup_morph'
    bl_description = 'Create a backup of source file\nName : same_name_aaaa-mm-dd-hh-mn-se'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        date = datetime.datetime.now()
        str_date = str(date.year) + "-" + str(date.month).zfill(2) + "-" + str(date.day).zfill(2) + "_" + str(date.hour).zfill(2) + "-" + str(date.minute).zfill(2) + "-" + str(date.second).zfill(2)
        morphcreator.backup_morph_file(str_date)
        return {'FINISHED'}

def get_cmd_output_file_name():
    scn = bpy.context.scene
    spectrum = morphcreator.get_spectrum(scn.mbcrea_cmd_spectrum)
    file_name = ""
    splitted_type = algorithms.split_name(scn.mblab_morphing_body_type)
    splitted_extra_name = algorithms.split_name(scn.mblab_morphing_file_extra_name)
    if spectrum == "Gender":
        file_name = scn.mbcrea_gender_files_out
    elif scn.mbcrea_body_type_files_out != "NEW":
        file_name = scn.mbcrea_body_type_files_out.split(".")[0]
        if len(splitted_extra_name) > 0:
            file_name += "_" + splitted_extra_name
        file_name += ".json"
    elif len(splitted_type) > 0:
        file_name = scn.mbcrea_body_type_files_in.split("_")[0] + "_" + splitted_type + "_morphs"
        if len(splitted_extra_name) > 0:
            file_name += "_" + splitted_extra_name
        file_name += ".json"
    return file_name

def get_cmd_input_file_name():
    scn = bpy.context.scene
    if morphcreator.get_spectrum(scn.mbcrea_cmd_spectrum) == "Gender":
        return scn.mbcrea_gender_files_in
    return scn.mbcrea_body_type_files_in
        
class ButtonCopyMorphs(bpy.types.Operator):
    bl_label = 'Copy to output file'
    bl_idname = 'mbcrea.button_copy_morph'
    bl_description = 'Copy selected morphs to file'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        input_file_name = get_cmd_input_file_name()
        output_file_name = get_cmd_output_file_name()
        if len(output_file_name) < 1:
            return {'FINISHED'}
        morphs_list = morphcreator.get_morphs_list(input_file_name, mblab_humanoid.get_object())
        if len(morphs_list) < 1:
            return {'FINISHED'}
        morphcreator.cmd_morphs_action(input_file_name, output_file_name, morphs_names=morphs_list, new_names=[], copy=True, delete=False)
        return {'FINISHED'}

class ButtonMoveMorphs(bpy.types.Operator):
    bl_label = 'Move to output file'
    bl_idname = 'mbcrea.button_move_morph'
    bl_description = 'Move selected morphs to file'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        input_file_name = get_cmd_input_file_name()
        output_file_name = get_cmd_output_file_name()
        if len(output_file_name) < 1:
            return {'FINISHED'}
        morphs_list = morphcreator.get_morphs_list(input_file_name, mblab_humanoid.get_object())
        if len(morphs_list) < 1:
            return {'FINISHED'}
        morphcreator.cmd_morphs_action(input_file_name, output_file_name, morphs_names=morphs_list, new_names=[], copy=True, delete=True)
        return {'FINISHED'}

class ButtonDeleteMorphs(bpy.types.Operator):
    bl_label = 'Delete selected'
    bl_idname = 'mbcrea.button_delete_morph'
    bl_description = '! NO UNDO ! Delete selected morphs'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        input_file_name = get_cmd_input_file_name()
        morphs_list = morphcreator.get_morphs_list(input_file_name, mblab_humanoid.get_object())
        if len(morphs_list) < 1:
            return {'FINISHED'}
        morphcreator.cmd_morphs_action(input_file_name, None, morphs_names=morphs_list, new_names=[], copy=False, delete=True)
        return {'FINISHED'}

class ButtonRenameMorphs(bpy.types.Operator):
    bl_label = 'Rename selected'
    bl_idname = 'mbcrea.button_rename_morph'
    bl_description = 'Rename selected morph'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        input_file_name = get_cmd_input_file_name()
        morphs_list = morphcreator.get_morphs_list(input_file_name, mblab_humanoid.get_object())
        if len(morphs_list) < 1:
            return {'FINISHED'}
        n_name = algorithms.split_name(bpy.context.scene.mbcrea_morphing_rename, ' _²&=¨^$£%µ,?;!§+*/')
        morphcreator.cmd_morphs_action(input_file_name, None, morphs_names=morphs_list, new_name=n_name, copy=False, delete=False)
        return {'FINISHED'}

class ButtonCompatToolsDir(bpy.types.Operator):
    #just for quick tests
    bl_label = 'Create project directories'
    bl_idname = 'mbcrea.button_create_directories'
    bl_description = 'Button for create all needed\ndirectories for the projet'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        pn = creation_tools_ops.get_created_name("project_name")
        creation_tools_ops.create_needed_directories(pn)
        return {'FINISHED'}

class ButtonSaveCompatProject(bpy.types.Operator):
    #just for quick tests
    bl_label = 'Save current project'
    bl_idname = 'mbcrea.button_save_compat_project'
    bl_description = 'Save current on-going project\nto create a new model.'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        creation_tools_ops.save_project()
        return {'FINISHED'}

class ButtonLoadCompatProject(bpy.types.Operator, ImportHelper):
    """
        Load the model as a base model.
    """
    bl_label = 'Load project'
    bl_idname = 'mbcrea.button_load_compat_project'
    filename_ext = ".json"
    filter_glob: bpy.props.StringProperty(default="*.json", options={'HIDDEN'},)
    bl_description = 'Load a compatibility project'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        #--------------------
        creation_tools_ops.load_project(self.filepath)
        return {'FINISHED'}

class ButtonForTest(bpy.types.Operator):
    #just for quick tests
    bl_label = 'Button for degug tests'
    bl_idname = 'mbcrea.button_for_tests'
    bl_description = 'Test things'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global mblab_humanoid
        print(copie)
        return {'FINISHED'}

class ButtonExportShapeKeys(bpy.types.Operator):
    bl_label = 'Import Expression Shape Keys'
    bl_idname = 'mbcrea.button_import_shape_keys'
    bl_description = 'PRE-FINALIZATION Tool: Import character shape keys to character morphs.\n\
Morphs will be available next time you create same character type'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        # iterate through all shape keys on the mesh data and generate
        # The delta between given shape key and the basis shape key.
        # If no basis shape key operation will fail.
        # If any of the shape keys override existing shape keys, operation
        # will fail. This operation is meant to amend to current Lab keys
        # and not to override them.
        mesh = algorithms.get_active_body()
        mname = mesh.name
        if not mesh:
            self.report({'ERROR'}, "No active mesh. Please select an MB-Lab Character")
        # do a first pass over existing
        basis_found = False
        key_blocks = None
        try:
            key_blocks = bpy.data.objects[mname].data.shape_keys.key_blocks
        except:
            self.ShowMessageBox("Mesh has no shape keys", "Error", 'ERROR')
            return {'FINISHED'}

        expression_keys = self.getExpressionKeys()
        for key in bpy.data.objects[mname].data.shape_keys.key_blocks:
            if key.name == 'Basis':
                if basis_found:
                    self.ShowMessageBox("More than one instance of the Basis Shape Key. Invalid",
                                        "Error", 'ERROR')
                    return {'FINISHED'}
                basis_found = True
                continue
            if key.name in expression_keys and not mblab_override_expressions:
                self.ShowMessageBox("Shape key %s already exists. Aborting operation" % key.name, "Error", 'ERROR')
                return {'FINISHED'}
        if not basis_found:
            self.ShowMessageBox("Basis shape key not found. Invalid setup", "Error", 'ERROR')
            return {'FINISHED'}

        # keys are good lets calculate each one relative to the basis
        basis_vertices = []
        new_expressions = {}
        for key in bpy.data.objects[mname].data.shape_keys.key_blocks:
            if key.name == 'Basis':
                basis_vertices = self.getVertexList(key.data)
                continue
            key_vertices = self.getVertexList(key.data)
            indexed_vertices = morphcreator.substract_with_index(basis_vertices, key_vertices)
            if len(indexed_vertices) < 1:
                continue
            # append and write to the expressions file
            new_expressions[key.name] = indexed_vertices
        self.writeShapeKeyData(new_expressions)
        return {'FINISHED'}

    def writeData(self, path, new_data):
        data = file_ops.load_json_data(path)
        data = dict(data, **new_data)
        file_ops.save_json_data(path, data)

    def writeShapeKeyData(self, new_data):
        phenotype_path = mblab_humanoid.morph_engine.get_expressions_file()
        id1 = ntpath.basename(phenotype_path).split('_')[0]
        id2 = ntpath.basename(phenotype_path).split('_')[1]
        if bpy.context.scene.mblab_copy_to_all_phenotype:
            # we have to check all files
            for path in mblab_humanoid.morph_engine.get_all_expressions_files():
                fname = ntpath.basename(path)
                cur_id1 = fname.split('_')[0]
                cur_id2 = fname.split('_')[1]
                # Apply if this is the same phenotype
                if cur_id1 == id1 and (cur_id2 == id2 or not 'an' in cur_id2):
                    self.writeData(path, new_data)
        else:
            path = mblab_humanoid.morph_engine.get_expressions_file()
            self.writeData(path, new_data)

    def getExpressionKeys(self):
        keys = []
        if bpy.context.scene.mblab_copy_to_all_phenotype:
            # we have to check all files
            for path in mblab_humanoid.morph_engine.get_all_expressions_files():
                data = file_ops.load_json_data(path)
                keys += list(data.keys())
        else:
            path = mblab_humanoid.morph_engine.get_expressions_file()
            data = file_ops.load_json_data(path)
            keys += list(data.keys())
        return keys

    def getVertexList(self, key_data):
        kl_v = key_data.values()
        result = []
        for l in kl_v:
            result.append(l.co)
        return result

    def ShowMessageBox(self, message = "", title = "Error !", icon = 'ERROR'):

        def draw(self, context):
            self.layout.label(text=message)
        bpy.context.window_manager.popup_menu(draw, title = title, icon = icon)


class ButtonAdaptationToolsON(bpy.types.Operator):
    bl_label = 'Model edition'
    bl_idname = 'mbcrea.button_adaptation_tools_on'
    bl_description = 'All tools to change / adapt from an existing model'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global gui_active_panel_first
        gui_active_panel_first = "adaptation_tools"
        #Other things to do...
        return {'FINISHED'}

class ButtonAdaptationToolsOFF(bpy.types.Operator):
    bl_label = 'Model edition'
    bl_idname = 'mbcrea.button_adaptation_tools_off'
    bl_description = 'All tools to change / adapt from an existing model'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global gui_active_panel_first
        gui_active_panel_first = None
        #Other things to do...
        return {'FINISHED'}

class ButtonCompatToolsON(bpy.types.Operator):
    bl_label = 'Model creation'
    bl_idname = 'mbcrea.button_compat_tools_on'
    bl_description = 'All tools to make a model compatible with MB-Lab'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global gui_active_panel_first
        gui_active_panel_first = "compat_tools"
        #Other things to do...
        return {'FINISHED'}

class ButtonCompatToolsOFF(bpy.types.Operator):
    bl_label = 'Model creation'
    bl_idname = 'mbcrea.button_compat_tools_off'
    bl_description = 'All tools to make a model compatible with MB-Lab'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global gui_active_panel_first
        gui_active_panel_first = None
        #Other things to do...
        return {'FINISHED'}

class ButtonUpdateCombMorphs(bpy.types.Operator):
    """Reset all morphings."""
    bl_label = 'Update character'
    bl_idname = 'mbcrea.update_comb_morphs'
    bl_description = 'Update character with actual parameters'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL', 'UNDO'}

    def execute(self, context):
        global mblab_humanoid
        morphcreator.update_for_combined_morphs(mblab_humanoid)
        return {'FINISHED'}

class FinalizeCombMorph(bpy.types.Operator):
    """
        Works like FinalizeMorph
    """
    bl_label = 'Finalize the combined morph'
    bl_idname = 'mbcrea.button_save_final_comb_morph'
    filename_ext = ".json"
    bl_description = 'Finalize the combined morph,\ncreate or open the morphs file,\nreplace or append new morph'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        scn = bpy.context.scene
        base = []
        sculpted = []
        
        try:
            base = morphcreator.get_vertices_list(0)
        except:
            self.ShowMessageBox("Base vertices are not stored !", "Warning", 'ERROR')
            return {'FINISHED'}
        try:
            sculpted = morphcreator.get_vertices_list(1)
        except:
            self.ShowMessageBox("Changed vertices are not stored !", "Warning", 'ERROR')
            return {'FINISHED'}
        indexed_vertices = morphcreator.substract_with_index(base, sculpted)
        if len(indexed_vertices) < 1:
            self.ShowMessageBox("Models base / sculpted are equals !\nNo file saved", "Warning", 'INFO')
            return {'FINISHED'}
        #-------File name----------
        file_name = ""
        if scn.mblab_morphing_spectrum == "GE":
            #File name for whole gender, like human_female or anime_male.
            file_name = morphcreator.get_model_and_gender()
        else:
            if len(scn.mblab_morphing_body_type) < 1:
                file_name = morphcreator.get_body_type() + "_morphs"
            else:
                file_name = morphcreator.get_body_type()[0:2] + scn.mblab_morphing_body_type + "_morphs"
            if len(scn.mblab_morphing_file_extra_name) > 0:
                file_name = file_name + "_" + scn.mblab_morphing_file_extra_name
        if scn.mblab_incremental_saves:
            file_name = file_name + "_" + morphcreator.get_next_number()
        #-------Morph name-----------
        morph_name = morphcreator.get_combined_morph_name()
        #-------Morphs path----------
        file_path_name = os.path.join(file_ops.get_data_path(), "morphs", file_name + ".json")
        file = file_ops.load_json_data(file_path_name, "Try to save a morph file")
        if file == None:
            file = {}
        #---Creating new morph-------
        file[morph_name] = indexed_vertices
        file_ops.save_json_data(file_path_name, file)
        #----------------------------
        return {'FINISHED'}

    def ShowMessageBox(self, message = "", title = "Message Box", icon = 'INFO'):

        def draw(self, context):
            self.layout.label(text=message)
        bpy.context.window_manager.popup_menu(draw, title = title, icon = icon)

class ButtonVertexCreationON(bpy.types.Operator):
    bl_label = 'Vertex creation tools'
    bl_idname = 'mbcrea.button_vertex_creation_on'
    bl_description = 'All tools to create vertex for the body.\nFrom scratch or from an existing model'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global gui_active_panel_second
        gui_active_panel_second = "Vertex_creation"
        #Other things to do...
        return {'FINISHED'}

class ButtonVertexCreationOFF(bpy.types.Operator):
    bl_label = 'Vertex creation tools'
    bl_idname = 'mbcrea.button_vertex_creation_off'
    bl_description = 'All tools to create vertex for the body.\nFrom scratch or from an existing model'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global gui_active_panel_second
        gui_active_panel_second = None
        #Other things to do...
        return {'FINISHED'}

class ButtonBboxesToolsON(bpy.types.Operator):
    bl_label = 'Bboxes tools'
    bl_idname = 'mbcrea.button_bboxes_tools_on'
    bl_description = 'All tools to create bboxes for a model'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global gui_active_panel_second
        gui_active_panel_second = "Bboxes_tools"
        #Other things to do...
        return {'FINISHED'}

class ButtonBboxesToolsOFF(bpy.types.Operator):
    bl_label = 'Bboxes tools'
    bl_idname = 'mbcrea.button_bboxes_tools_off'
    bl_description = 'All tools to create bboxes for a model'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global gui_active_panel_second
        gui_active_panel_second = None
        #Other things to do...
        return {'FINISHED'}

class ButtonWeightToolsON(bpy.types.Operator):
    bl_label = 'Weight painting tools'
    bl_idname = 'mbcrea.button_weight_painting_tools_on'
    bl_description = 'All tools related to weight painting'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global gui_active_panel_second
        gui_active_panel_second = "Weight_painting"
        #Other things to do...
        return {'FINISHED'}

class ButtonWeightToolsOFF(bpy.types.Operator):
    bl_label = 'Weight painting tools'
    bl_idname = 'mbcrea.button_weight_painting_tools_off'
    bl_description = 'All tools related to weight painting'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global gui_active_panel_second
        gui_active_panel_second = None
        #Other things to do...
        return {'FINISHED'}

class ButtonVerticesGroupsToolsON(bpy.types.Operator):
    bl_label = 'Vertices groups tools'
    bl_idname = 'mbcrea.button_vertices_groups_tools_on'
    bl_description = 'All tools related to vertices groups'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global gui_active_panel_second
        gui_active_panel_second = "Vertices_groups"
        #Other things to do...
        return {'FINISHED'}

class ButtonVerticesGroupsToolsOFF(bpy.types.Operator):
    bl_label = 'Vertices groups tools'
    bl_idname = 'mbcrea.button_vertices_groups_tools_off'
    bl_description = 'All tools related to vertices groups'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global gui_active_panel_second
        gui_active_panel_second = None
        #Other things to do...
        return {'FINISHED'}

class ButtonMusclesToolsON(bpy.types.Operator):
    bl_label = 'Muscles tools'
    bl_idname = 'mbcrea.button_muscles_tools_on'
    bl_description = 'All tools related to muscles system'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global gui_active_panel_second
        gui_active_panel_second = "Muscles"
        #Other things to do...
        return {'FINISHED'}

class ButtonMusclesToolsOFF(bpy.types.Operator):
    bl_label = 'Muscles tools'
    bl_idname = 'mbcrea.button_muscles_tools_off'
    bl_description = 'All tools related to muscles system'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global gui_active_panel_second
        gui_active_panel_second = None
        #Other things to do...
        return {'FINISHED'}

class ButtonConfigToolsON(bpy.types.Operator):
    bl_label = 'Configs tools'
    bl_idname = 'mbcrea.button_config_tools_on'
    bl_description = 'All tools for managing configuration files'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global gui_active_panel_second
        gui_active_panel_second = "Config"
        #Other things to do...
        return {'FINISHED'}

class ButtonConfigToolsOFF(bpy.types.Operator):
    bl_label = 'Configs tools'
    bl_idname = 'mbcrea.button_config_tools_off'
    bl_description = 'All tools for managing configuration files'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global gui_active_panel_second
        gui_active_panel_second = None
        #Other things to do...
        return {'FINISHED'}

class ButtonFilesManagementON(bpy.types.Operator):
    bl_label = 'Files management'
    bl_idname = 'mbcrea.button_management_tools_on'
    bl_description = 'All tools for addon files management'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global gui_active_panel_second
        gui_active_panel_second = "Files_management"
        #Other things to do...
        return {'FINISHED'}

class ButtonFilesManagementOFF(bpy.types.Operator):
    bl_label = 'Files management'
    bl_idname = 'mbcrea.button_management_tools_off'
    bl_description = 'All tools for addon files management'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global gui_active_panel_second
        gui_active_panel_second = None
        #Other things to do...
        return {'FINISHED'}

class ButtonInitCompatON(bpy.types.Operator):
    bl_label = 'Init all compatibilty tools'
    bl_idname = 'mbcrea.button_init_compat_on'
    bl_description = 'Init all names and tools for\ncreating a new compatible model'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global gui_active_panel_second
        gui_active_panel_second = "Init_compat"
        #Other things to do...
        return {'FINISHED'}

class ButtonInitCompatOFF(bpy.types.Operator):
    bl_label = 'Init all compatibilty tools'
    bl_idname = 'mbcrea.button_init_compat_off'
    bl_description = 'Init all names and tools for\ncreating a new compatible model'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global gui_active_panel_second
        gui_active_panel_second = None
        #Other things to do...
        return {'FINISHED'}

class ButtonInitCompat(bpy.types.Operator):
    bl_label = 'Go'
    bl_idname = 'mbcrea.button_init_compat'
    bl_description = 'Are you sure ?\nNo undo possible !'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        #init of all tools. No turning back.
        creation_tools_ops.init_project()
        return {'FINISHED'}

class Reset_expression_category(bpy.types.Operator):
    """Reset the parameters for the currently selected category"""
    bl_label = 'Reset expressions'
    bl_idname = 'mbcrea.reset_expressionscategory'
    bl_description = 'Reset the parameters for expressions'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL', 'UNDO'}

    def execute(self, context):
        global mblab_humanoid
        scn = bpy.context.scene
        mblab_humanoid.reset_category("Expressions")
        return {'FINISHED'}

class ImpExpression(bpy.types.Operator, ImportHelper):
    """Import parameters for the character"""
    bl_idname = "mbcrea.import_expression"
    bl_label = "Import facial expression"
    filename_ext = ".json"
    filter_glob: bpy.props.StringProperty(
        default="*.json",
        options={'HIDDEN'},
        )
    bl_context = 'objectmode'

    def execute(self, context):
        global mbcrea_expressionscreator

        char_data = mbcrea_expressionscreator.load_face_expression(self.filepath)
        return {'FINISHED'}


classes = (
    ButtonParametersOff,
    ButtonParametersOn,
    ButtonFaceRigOff,
    ButtonFaceRigOn,
    ButtonUtilitiesOff,
    ButtonUtilitiesOn,
    ButtonExpressionsOff,
    ButtonExpressionOn,
    ButtonRandomOff,
    ButtonRandomOn,
    ButtonAutomodellingOff,
    ButtonAutomodellingOn,
    ButtonRestPoseOff,
    ButtonRestPoseOn,
    ButtonPoseOff,
    ButtonStoreBaseBodyVertices,
    ButtonSaveWorkInProgress,
    FinalizeMorph,
    SaveBodyAsIs,
    LoadBaseBody,
    LoadSculptedBody,
    ButtonAssetsOn,
    ButtonAssetsOff,
    ButtonPoseOn,
    ButtonSkinOff,
    ButtonSkinOn,
    ButtonViewOptOff,
    ButtonViewOptOn,
    ButtonProxyFitOff,
    ButtonProxyFitOn,
    ButtonFilesOff,
    ButtonFilesOn,
    ButtonFinalizeOff,
    ButtonFinalizeOn,
    ButtonLibraryOff,
    ButtonLibraryOn,
    ButtonFinalizedCorrectRot,
    ButtonSaveBvhAdjustments,
    ButtonLoadBvhAdjusments,
    UpdateSkinDisplacement,
    DisableSubdivision,
    EnableSubdivision,
    DisableSmooth,
    EnableSmooth,
    DisableDisplacement,
    EnableDisplacement,
    FinalizeCharacterAndImages,
    FinalizeCharacter,
    ResetParameters,
    ResetExpressions,
    InsertExpressionKeyframe,
    Reset_category,
    CharacterGenerator,
    ExpDisplacementImage,
    ExpDermalImage,
    ExpAllImages,
    ExpCharacter,
    ExpMeasures,
    ImpCharacter,
    ImpMeasures,
    LoadDermImage,
    LoadDispImage,
    FitProxy,
    RemoveProxy,
    ApplyMeasures,
    AutoModelling,
    AutoModellingMix,
    SaveRestPose,
    LoadRestPose,
    SavePose,
    LoadPose,
    ResetPose,
    LoadBvh,
    StartSession,
    CreateFaceRig,
    DeleteFaceRig,
    LoadTemplate,
    preferences.MBPreferences,
    VIEW3D_PT_tools_MBLAB,
    OBJECT_OT_humanoid_rot_limits,
    OBJECT_OT_delete_rotations,
    OBJECT_OT_particle_hair,
    OBJECT_OT_manual_hair,
    OBJECT_OT_change_hair_color,
    OBJECT_OT_add_color_preset,
    OBJECT_OT_remove_color_preset,
    OBJECT_OT_undo_remove_color,
    ButtonForTest,
    ButtonExportShapeKeys,
    ButtonAdaptationToolsON,
    ButtonAdaptationToolsOFF,
    ButtonCompatToolsON,
    ButtonCompatToolsOFF,
    ButtonVertexCreationON,
    ButtonVertexCreationOFF,
    ButtonBboxesToolsON,
    ButtonBboxesToolsOFF,
    ButtonWeightToolsON,
    ButtonWeightToolsOFF,
    ButtonVerticesGroupsToolsON,
    ButtonVerticesGroupsToolsOFF,
    ButtonMusclesToolsON,
    ButtonMusclesToolsOFF,
    ButtonConfigToolsON,
    ButtonConfigToolsOFF,
    ButtonFilesManagementON,
    ButtonFilesManagementOFF,
    ButtonInitCompatON,
    ButtonInitCompatOFF,
    ButtonInitCompat,
    ButtonCompatToolsDir,
    ButtonSaveCompatProject,
    ButtonLoadCompatProject,
    FinalizeExpression,
    FinalizeCombExpression,
    FinalizePhenotype,
    FinalizePreset,
    ButtonUpdateCombMorphs,
    FinalizeCombMorph,
    ButtonTransforSave,
    ButtonTransforLoad,
    ButtonCurrentModelTransforSave,
    CheckTransformationFile,
    LoadTransformationFile,
    ButtonRescanMorphFiles,
    ButtonBackupMorphFile,
    ButtonCopyMorphs,
    ButtonMoveMorphs,
    ButtonDeleteMorphs,
    ButtonRenameMorphs,
    Reset_expression_category,
    ImpExpression,
    VIEW3D_PT_tools_MBCrea,
)

def register():
    # addon updater code and configurations
    # in case of broken version, try to register the updater first
    # so that users can revert back to a working version
    addon_updater_ops.register(bl_info)

    # register the example panel, to show updater buttons
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    # addon updater unregister
    addon_updater_ops.unregister()

    # register the example panel, to show updater buttons
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()

# <pep8 compliant>
