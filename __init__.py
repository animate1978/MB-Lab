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

import time
import json
import os
import numpy
#from pathlib import Path
from math import radians, degrees

import bpy
from bpy.app.handlers import persistent
from bpy_extras.io_utils import ExportHelper, ImportHelper

from . import humanoid
from . import algorithms
from . import animationengine
from . import proxyengine
from . import expressionengine
from . import file_ops
from . import object_ops
from . import hairengine
from . import numpy_ops
from . import node_ops
from . import utils
from . import humanoid_rotations
from . import preferences
from . import addon_updater_ops
from . import facerig
from . import morphcreator
from . import creation_tools_ops


logger = logging.getLogger(__name__)

# MB-Lab Blender Info

bl_info = {
    "name": "MB-Lab",
    "author": "Manuel Bastioni, MB-Lab Community",
    "version": (1, 7, 8),
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

gui_status = "NEW_SESSION"
gui_err_msg = ""
gui_active_panel = None
gui_active_panel_fin = None
#Teto
gui_active_panel_first = None
gui_active_panel_second = None
gui_active_panel_third = None
#End Teto

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

                    file_ops.import_object_from_lib(lib_filepath, "Light_Key")
                    file_ops.import_object_from_lib(lib_filepath, "Light_Fill")
                    file_ops.import_object_from_lib(lib_filepath, "Light_Backlight")

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
                name=prop,
                min=-5.0,
                max=5.0,
                soft_min=0.0,
                soft_max=1.0,
                precision=3,
                default=0.5,
                update=realtime_update))


def init_measures_props(humanoid_instance):
    for measure_name, measure_val in humanoid_instance.morph_engine.measures.items():
        setattr(
            bpy.types.Object,
            measure_name,
            bpy.props.FloatProperty(
                name=measure_name, min=0.0, max=500.0,
                default=measure_val))
    humanoid_instance.sync_gui_according_measures()


def init_categories_props(humanoid_instance):
    categories_enum = []
    for category in mblab_humanoid.get_categories():
        categories_enum.append(
            (category.name, category.name, category.name))

    bpy.types.Scene.morphingCategory = bpy.props.EnumProperty(
        items=categories_enum,
        update=modifiers_update,
        name="Morphing categories")


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
    update=angle_update_0,
    default=0.0)

bpy.types.Scene.mblab_rot_offset_1 = bpy.props.FloatProperty(
    name="Tweak rot Y",
    min=-1,
    max=1,
    precision=2,
    update=angle_update_1,
    default=0.0)

bpy.types.Scene.mblab_rot_offset_2 = bpy.props.FloatProperty(
    name="Tweak rot Z",
    min=-1,
    max=1,
    precision=2,
    update=angle_update_2,
    default=0.0)

bpy.types.Scene.mblab_proxy_offset = bpy.props.FloatProperty(
    name="Offset",
    min=0,
    max=100,
    default=0)

bpy.types.Scene.mblab_proxy_threshold = bpy.props.FloatProperty(
    name="Influence",
    min=0,
    max=1000,
    default=20,
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
    description="Preserve the current character body mass")

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
    description="ExplicitBodyPartMorphed",
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
        global gui_active_panel
        gui_active_panel = None
        return {'FINISHED'}


class ButtonParametersOn(bpy.types.Operator):
    bl_label = 'Body Measures'
    bl_idname = 'mbast.button_parameters_on'
    bl_description = 'Open details panel'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global gui_active_panel
        gui_active_panel = "parameters"
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
    bl_description = 'Finalize the morph, ask for min and max files, create or open the morphs file, replace or append new morph'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        scn = bpy.context.scene
        base = []
        sculpted = []

        if len(scn.mblab_morph_name) < 1:
            self.ShowMessageBox("Please choose a name for the morph !\nNo file saved", "Warning", 'ERROR')
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
        #-------Morph name----------
        morph_name = morphcreator.get_body_parts(scn.mblab_body_part_name) + "_" + scn.mblab_morph_name + "_" + morphcreator.get_min_max(scn.mblab_morph_min_max)
        #-------Morphs path----------
        #Teto
        file_path_name = os.path.join(file_ops.get_data_path(), "morphs", file_name + ".json")
        file = file_ops.load_json_data(file_path_name, "Try to load a morph file")
        if file == None:
            file = {}
        #End Teto
        #---Creating new morph-------
        file[morph_name] = indexed_vertices
        file_ops.save_json_data(file_path_name, file)
        #----------------------------
        return {'FINISHED'}

    def ShowMessageBox(self, message = "", title = "Message Box", icon = 'INFO'):

        def draw(self, context):
            self.layout.label(text=message)
        bpy.context.window_manager.popup_menu(draw, title = title, icon = icon)
#Teto
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
        global gui_active_panel
        gui_active_panel = None
        return {'FINISHED'}


class ButtonRestPoseOn(bpy.types.Operator):
    bl_label = 'Rest Pose'
    bl_idname = 'mbast.button_rest_pose_on'
    bl_description = 'Open rest pose panel'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global gui_active_panel
        gui_active_panel = 'rest_pose'
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
        global gui_active_panel
        gui_active_panel = None
        return {'FINISHED'}


class ButtonSkinOn(bpy.types.Operator):
    bl_label = 'Skin Editor'
    bl_idname = 'mbast.button_skin_on'
    bl_description = 'Open skin editor panel'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global gui_active_panel
        gui_active_panel = 'skin'
        return {'FINISHED'}


class ButtonViewOptOff(bpy.types.Operator):
    bl_label = 'Display Options'
    bl_idname = 'mbast.button_display_off'
    bl_description = 'Close skin editor panel'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global gui_active_panel
        gui_active_panel = None
        return {'FINISHED'}


class ButtonViewOptOn(bpy.types.Operator):
    bl_label = 'Display Options'
    bl_idname = 'mbast.button_display_on'
    bl_description = 'Open skin editor panel'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global gui_active_panel
        gui_active_panel = 'display_opt'
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
        global gui_active_panel
        gui_active_panel = None
        return {'FINISHED'}


class ButtonFilesOn(bpy.types.Operator):
    bl_label = 'File Tools'
    bl_idname = 'mbast.button_file_on'
    bl_description = 'Open file panel'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global gui_active_panel
        gui_active_panel = 'file'
        return {'FINISHED'}


class ButtonFinalizeOff(bpy.types.Operator):
    bl_label = 'Finalize Tools'
    bl_idname = 'mbast.button_finalize_off'
    bl_description = 'Close finalize panel'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global gui_active_panel
        gui_active_panel = None
        return {'FINISHED'}


class ButtonFinalizeOn(bpy.types.Operator):
    bl_label = 'Finalize Tools'
    bl_idname = 'mbast.button_finalize_on'
    bl_description = 'Open finalize panel'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global gui_active_panel
        gui_active_panel = 'finalize'
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


# class LoadAssets(bpy.types.Operator):
# """
# Load assets from library
# """
# bl_label = 'Load model from assets library'
# bl_idname = 'mbast.load_assets_element'
# bl_description = 'Load the element selected from the assets library'
# bl_context = 'objectmode'
# bl_options = {'REGISTER', 'INTERNAL','UNDO'}

# def execute(self, context):
# scn = bpy.context.scene
# mblab_proxy.load_asset(scn.mblab_assets_models)
# return {'FINISHED'}


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
    bl_label = "MB-Lab {0}.{1}.{2}".format(bl_info["version"][0], bl_info["version"][1], bl_info["version"][2])
    bl_idname = "OBJECT_PT_characters01"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    # bl_context = 'objectmode'
    bl_category = "MB-Lab"

    @classmethod
    def poll(cls, context):
        return context.mode in {'OBJECT', 'POSE'}

    def draw(self, context):

        global mblab_humanoid, gui_status, gui_err_msg, gui_active_panel
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
            morphcreator.init_morph_names_database()

        if gui_status != "ACTIVE_SESSION":
            self.layout.label(text=" ")
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
                    if mblab_shapekeys.expressions_data:
                        obj = algorithms.get_active_body()
                        for expr_name in sorted(mblab_shapekeys.expressions_data.keys()):
                            if hasattr(obj, expr_name):
                                if scn.mblab_expression_filter in expr_name:
                                    box_exp.prop(obj, expr_name)
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
                self.layout.label(text="CREATION TOOLS", icon="RNA")
                box_act_opt = self.layout.box()

                if mblab_humanoid.exists_transform_database():
                    x_age = getattr(obj, 'character_age', 0)
                    x_mass = getattr(obj, 'character_mass', 0)
                    x_tone = getattr(obj, 'character_tone', 0)
                    age_lbl = round((15.5 * x_age ** 2) + 31 * x_age + 33)
                    mass_lbl = round(50 * (x_mass + 1))
                    tone_lbl = round(50 * (x_tone + 1))
                    lbl_text = "Age : {0} yr.  Mass : {1}%  Tone : {2}% ".format(age_lbl, mass_lbl, tone_lbl)
                    box_act_opt.label(text=lbl_text)

                    for meta_data_prop in sorted(mblab_humanoid.character_metaproperties.keys()):
                        if "last" not in meta_data_prop:
                            box_act_opt.prop(obj, meta_data_prop)
                    box_act_opt.operator("mbast.reset_allproperties", icon="RECOVER_LAST")

                    #if mblab_humanoid.get_subd_visibility() is True:
                        #self.layout.label(text="Tip: for slow PC, disable the subdivision in Display Options below", icon='INFO')

                if gui_active_panel != "library":
                    box_act_opt.operator('mbast.button_library_on', icon=icon_expand)
                else:
                    box_act_opt.operator('mbast.button_library_off', icon=icon_collapse)
                    box_lib = box_act_opt.box()

                    box_lib.label(text="Characters library", icon='ARMATURE_DATA')
                    if mblab_humanoid.exists_preset_database():
                        box_lib.prop(obj, "preset")
                    if mblab_humanoid.exists_phenotype_database():
                        box_lib.prop(obj, "ethnic")
                    box_lib.prop(scn, 'mblab_mix_characters', icon='FORCE_CHARGE')

                if gui_active_panel != "random":
                    box_act_opt.operator('mbast.button_random_on', icon=icon_expand)
                else:
                    box_act_opt.operator('mbast.button_random_off', icon=icon_collapse)

                    box_rand = box_act_opt.box()
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

                if gui_active_panel != "parameters":
                    box_act_opt.operator('mbast.button_parameters_on', icon=icon_expand)
                else:
                    box_act_opt.operator('mbast.button_parameters_off', icon=icon_collapse)

                    box_param = box_act_opt.box()
                    mblab_humanoid.bodydata_realtime_activated = True
                    if mblab_humanoid.exists_measure_database():
                        box_param.prop(scn, 'mblab_show_measures', icon='SNAP_INCREMENT')
                    split = box_param.split()

                    col = split.column()
                    col.label(text="PARAMETERS")
                    col.prop(scn, "morphingCategory")

                    for prop in mblab_humanoid.get_properties_in_category(scn.morphingCategory):
                        if hasattr(obj, prop):
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

                if mblab_humanoid.exists_measure_database():
                    if gui_active_panel != "automodelling":
                        box_act_opt.operator('mbast.button_automodelling_on', icon=icon_expand)
                    else:
                        box_act_opt.operator('mbast.button_automodelling_off', icon=icon_collapse)
                        box_auto = box_act_opt.box()
                        box_auto.operator("mbast.auto_modelling", icon='OUTLINER_DATA_MESH')
                        box_auto.operator("mbast.auto_modelling_mix", icon='OUTLINER_OB_MESH')
                else:
                    box_auto = box_act_opt.box()
                    box_auto.enabled = False
                    box_auto.label(text="Automodelling not available for this character", icon='INFO')

                if mblab_humanoid.exists_rest_poses_database():
                    if gui_active_panel != "rest_pose":
                        box_act_opt.operator('mbast.button_rest_pose_on', icon=icon_expand)
                    else:
                        box_act_opt.operator('mbast.button_rest_pose_off', icon=icon_collapse)
                        box_act_pose = box_act_opt.box()

                        if utils.is_ik_armature(armature):
                            box_act_pose.enabled = False
                            box_act_pose.label(text="Rest poses are not available for IK armatures", icon='INFO')
                        else:
                            box_act_pose.enabled = True
                            box_act_pose.prop(armature, "rest_pose")

                            box_act_pose.operator("mbast.restpose_load", icon='IMPORT')
                            box_act_pose.operator("mbast.restpose_save", icon='EXPORT')

                if gui_active_panel != "skin":
                    box_act_opt.operator('mbast.button_skin_on', icon=icon_expand)
                else:
                    box_act_opt.operator('mbast.button_skin_off', icon=icon_collapse)

                    box_skin = box_act_opt.box()
                    box_skin.enabled = True
                    if scn.render.engine != 'CYCLES' and scn.render.engine != 'BLENDER_EEVEE':
                        box_skin.enabled = False
                        box_skin.label(text="Skin editor requires Cycles or EEVEE", icon='INFO')

                    if mblab_humanoid.exists_displace_texture():
                        box_skin.operator("mbast.skindisplace_calculate", icon='MOD_DISPLACE')
                        box_skin.label(text="Enable Displacement Preview to view updates", icon='INFO')

                    for material_data_prop in sorted(mblab_humanoid.character_material_properties.keys()):
                        box_skin.prop(obj, material_data_prop)

                if gui_active_panel != "finalize":
                    box_act_opt.operator('mbast.button_finalize_on', icon=icon_expand)
                else:
                    box_act_opt.operator('mbast.button_finalize_off', icon=icon_collapse)
                    box_fin = box_act_opt.box()
                    box_fin.prop(scn, 'mblab_save_images_and_backup', icon='EXPORT')
                    box_fin.prop(scn, 'mblab_remove_all_modifiers', icon='CANCEL')
                    box_fin.prop(scn, 'mblab_final_prefix')
                    if scn.mblab_save_images_and_backup:
                        box_fin.operator("mbast.finalize_character_and_images", icon='FREEZE')
                    else:
                        box_fin.operator("mbast.finalize_character", icon='FREEZE')

                if gui_active_panel != "file":
                    box_act_opt.operator('mbast.button_file_on', icon=icon_expand)
                else:
                    box_act_opt.operator('mbast.button_file_off', icon=icon_collapse)
                    box_file = box_act_opt.box()
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

                if gui_active_panel != "display_opt":
                    box_act_opt.operator('mbast.button_display_on', icon=icon_expand)
                else:
                    box_act_opt.operator('mbast.button_display_off', icon=icon_collapse)
                    box_disp = box_act_opt.box()

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

                self.layout.label(text=" ")
                self.layout.label(text="AFTER-CREATION TOOLS", icon="MODIFIER_ON")
                self.layout.label(
                    text="FINALIZED characters ONLY", icon="INFO")

            else:
                gui_status = "NEW_SESSION"

#Teto

# MB-Lab Secondary GUI

class VIEW3D_PT_tools_MBCrea(bpy.types.Panel):
    bl_label = "MB-Crea {0}.{1}.{2}".format(bl_info["version"][0], bl_info["version"][1], bl_info["version"][2])
    bl_idname = "OBJECT_PT_characters02"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = 'objectmode'
    bl_category = "MB-Crea"

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
        box_general.operator('mbcrea.button_for_tests', icon='BLENDER')

        box_tools = self.layout.box()
        box_tools.label(text="Tools categories")
        if gui_active_panel_first != "adaptation_tools":
            box_tools.operator('mbcrea.button_adaptation_tools_on', icon=icon_expand)
        else:
            box_tools.operator('mbcrea.button_adaptation_tools_off', icon=icon_collapse)
            box_adaptation_tools = self.layout.box()
            if gui_active_panel_second != "Rigify":
                box_adaptation_tools.operator('mbcrea.button_rigify_on', icon=icon_expand)
            else:
                box_adaptation_tools.operator('mbcrea.button_rigify_off', icon=icon_collapse)
                box_rigify = box_adaptation_tools.box()
                box_rigify.label(text="#TODO Rigify...")
            if gui_active_panel_second != "Blenrig":
                box_adaptation_tools.operator('mbcrea.button_blenrig_on', icon=icon_expand)
            else:
                box_adaptation_tools.operator('mbcrea.button_blenrig_off', icon=icon_collapse)
                box_blenrig = box_adaptation_tools.box()
                box_blenrig.label(text="#TODO Blenrig...")
            if gui_active_panel_second != "Morphcreator":
                box_adaptation_tools.operator('mbcrea.button_morphcreator_on', icon=icon_expand)
            else:
                box_adaptation_tools.operator('mbcrea.button_morphcreator_off', icon=icon_collapse)
                box_morphcreator = box_adaptation_tools.box()
                if is_objet == "FOUND":
                    box_morphcreator.operator('mbast.button_store_base_vertices', icon="SPHERE") #Store all vertices of the actual body.
                    box_morphcreator.label(text="Morph wording - Body parts", icon='SORT_ASC')
                    box_morphcreator.prop(scn, "mblab_body_part_name") #first part of the morph's name : jaws, legs, ...
                    box_morphcreator.prop(scn, 'mblab_morph_name') #name for the morph
                    box_morphcreator.prop(scn, "mblab_morph_min_max") #The morph is for min proportions or max proportions.
                    box_morphcreator.label(text="Morph wording - File", icon='SORT_ASC')
                    box_morphcreator.prop(scn, "mblab_morphing_spectrum") #Ask if the new morph is global or just for a specific body
                    box_morphcreator.label(text=morphcreator.get_model_and_gender() + "_" + scn.mblab_morphing_file_extra_name, icon='INFO')
                    tp = morphcreator.get_body_type() + " (overide below)"
                    if len(scn.mblab_morphing_body_type) > 3:
                        tp = scn.mblab_morphing_body_type + " (delete below for reset)"
                    elif len(scn.mblab_morphing_body_type) > 0:
                        tp = "4 letters please (but that will work)"
                    box_morphcreator.label(text=tp, icon='INFO')
                    box_morphcreator.prop(scn, 'mblab_morphing_body_type') #The name of the type (4 letters)
                    box_morphcreator.prop(scn, 'mblab_morphing_file_extra_name') #The extra name for the file (basically the name of the author)
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
            if gui_active_panel_second != "morphs_for_expressions":
                box_adaptation_tools.operator('mbcrea.button_morphexpression_on', icon=icon_expand)
            else:
                box_adaptation_tools.operator('mbcrea.button_morphexpression_off', icon=icon_collapse)
                box_morphexpression = box_adaptation_tools.box()
                box_morphexpression.label(text="#TODO Morphs for expressions...")
                box_morphexpression.label(text="but very close to morphs creator.")
            if gui_active_panel_second != "combine_expressions":
                box_adaptation_tools.operator('mbcrea.button_combinexpression_on', icon=icon_expand)
            else:
                box_adaptation_tools.operator('mbcrea.button_combinexpression_off', icon=icon_collapse)
                box_combinexpression = box_adaptation_tools.box()
                box_combinexpression.label(text="#TODO Combine expressions")
                box_combinexpression.label(text="to have plain expressions...")
        
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
            if not creation_tools_ops.is_project_loaded():
                box_compat_tools.prop(scn, 'mbcrea_project_name')
                box_compat_tools.label(text="New model names", icon='QUESTION')
                box_compat_tools.prop(scn, 'mbcrea_body_name')
                box_compat_tools.prop(scn, 'mbcrea_body_gender')
                box_compat_tools.prop(scn, 'mbcrea_body_type')
                if len(scn.mbcrea_body_name) > 0:
                    body_name = str(scn.mbcrea_body_name).lower().split("_")[0]
                    if body_name not in creation_tools_ops.get_forbidden_names():
                        creation_tools_ops.set_created_name('body', body_name)
                        creation_tools_ops.set_created_name('body_short', body_name[0:2])
                        box_compat_tools.label(text="Body full name : " + body_name, icon='INFO')
                        box_compat_tools.label(text="Body short name : " + creation_tools_ops.get_created_name('body_short'), icon='INFO')
                    else:
                        creation_tools_ops.set_created_name('body', "")
                        creation_tools_ops.set_created_name('body_short', "")
                        box_compat_tools.label(text="Body name not allowed !", icon='ERROR')
                gender_name = creation_tools_ops.get_static_genders(scn.mbcrea_body_gender)
                creation_tools_ops.set_created_name('gender', gender_name)
                creation_tools_ops.set_created_name('gender_short', gender_name[0:1] + "_")
                box_compat_tools.label(text="Gender short name : " + creation_tools_ops.get_created_name('gender_short'), icon='INFO')
                if len(scn.mbcrea_body_type) > 0:
                    body_type = str(scn.mbcrea_body_type).lower().split("_")[0]
                    creation_tools_ops.set_created_name('type', body_type)
                    box_compat_tools.label(text="Body type : " + body_type, icon='INFO')
                else:
                    creation_tools_ops.set_created_name('type', '')
                #-------------
                project_creation_buttons=box_compat_tools.box()
                if len(str(scn.mbcrea_project_name)) > 0:
                    creation_tools_ops.set_created_name("project_name", str(scn.mbcrea_project_name))
                    project_creation_buttons.operator('mbcrea.button_create_directories', icon='FREEZE')
                    project_creation_buttons.operator('mbcrea.button_save_compat_project', icon='FREEZE')
                else:
                    creation_tools_ops.set_created_name("project_name", "")
                    project_creation_buttons.label(text="Choose a project name !", icon='ERROR')
            box_compat_tools.operator('mbcrea.button_load_compat_project', icon='IMPORT')
            #-------------
            if gui_active_panel_second != "Body_tools":
                box_compat_tools.operator('mbcrea.button_body_tools_on', icon=icon_expand)
            else:
                box_compat_tools.operator('mbcrea.button_body_tools_off', icon=icon_collapse)
                box_body_tools = box_compat_tools.box()
                box_body_tools.label(text="#TODO Body tools...")
            if gui_active_panel_second != "Bboxes_tools":
                box_compat_tools.operator('mbcrea.button_bboxes_tools_on', icon=icon_expand)
            else:
                box_compat_tools.operator('mbcrea.button_bboxes_tools_off', icon=icon_collapse)
                box_bboxes_tools = box_compat_tools.box()
                box_bboxes_tools.label(text="#TODO bboxes tools...")
            if gui_active_panel_second != "Weight_painting":
                box_compat_tools.operator('mbcrea.button_weight_painting_tools_on', icon=icon_expand)
            else:
                box_compat_tools.operator('mbcrea.button_weight_painting_tools_off', icon=icon_collapse)
                box_weight_painting_tools = box_compat_tools.box()
                box_weight_painting_tools.label(text="#TODO weight painting tools...")
            if gui_active_panel_second != "Vertices_groups":
                box_compat_tools.operator('mbcrea.button_vertices_groups_tools_on', icon=icon_expand)
            else:
                box_compat_tools.operator('mbcrea.button_vertices_groups_tools_off', icon=icon_collapse)
                box_vertices_groups_tools = box_compat_tools.box()
                box_vertices_groups_tools.label(text="#TODO vertices groups tools...")
            if gui_active_panel_second != "Muscles":
                box_compat_tools.operator('mbcrea.button_muscles_tools_on', icon=icon_expand)
            else:
                box_compat_tools.operator('mbcrea.button_muscles_tools_off', icon=icon_collapse)
                box_muscles_tools = box_compat_tools.box()
                box_muscles_tools.label(text="#TODO muscles tools...")
            if gui_active_panel_second != "Config":
                box_compat_tools.operator('mbcrea.button_config_tools_on', icon=icon_expand)
            else:
                box_compat_tools.operator('mbcrea.button_config_tools_off', icon=icon_collapse)
                box_config_tools = box_compat_tools.box()
                box_config_tools.label(text="#TODO config files tools...")
            if gui_active_panel_second != "Files_management":
                box_compat_tools.operator('mbcrea.button_management_tools_on', icon=icon_expand)
            else:
                box_compat_tools.operator('mbcrea.button_management_tools_off', icon=icon_collapse)
                box_management_tools = box_compat_tools.box()
                box_management_tools.label(text="#TODO files management tools...")

"""
bpy.types.Scene.mblab_incremental_saves = bpy.props.BoolProperty(
    name="Autosaves",
    description="Does an incremental save each time\n  the final save button is pressed.\nFrom 001 to 999\nCaution : returns to 001 between sessions")

bpy.types.Scene.mblab_morph_name = bpy.props.StringProperty(
    name="Name",
    description="ExplicitBodyPartMorphed",
    default="",
    maxlen=1024,
    subtype='FILE_NAME')

bpy.types.Scene.mblab_body_part_name = bpy.props.EnumProperty(
    items=morphcreator.get_body_parts(),
    name="Body part",
    default="BO")
"""
bpy.types.Scene.mbcrea_project_name = bpy.props.StringProperty(
    name="Project's name",
    description="Like MyProject.",
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
        creation_tools_ops.create_necessary_directories("user-try")
        return {'FINISHED'}

class ButtonAdaptationToolsON(bpy.types.Operator):
    bl_label = 'Adaptation tools'
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
    bl_label = 'Adaptation tools'
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
    bl_label = 'Compatibility tools'
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
    bl_label = 'Compatibility tools'
    bl_idname = 'mbcrea.button_compat_tools_off'
    bl_description = 'All tools to make a model compatible with MB-Lab'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global gui_active_panel_first
        gui_active_panel_first = None
        #Other things to do...
        return {'FINISHED'}

class ButtonRigifyON(bpy.types.Operator):
    bl_label = 'Add Rigify to model'
    bl_idname = 'mbcrea.button_rigify_on'
    bl_description = 'All tools to add Rigify to the model'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global gui_active_panel_second
        gui_active_panel_second = "Rigify"
        #Other things to do...
        return {'FINISHED'}

class ButtonRigifyOFF(bpy.types.Operator):
    bl_label = 'Add Rigify to model'
    bl_idname = 'mbcrea.button_rigify_off'
    bl_description = 'All tools to add Rigify to the model'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global gui_active_panel_second
        gui_active_panel_second = None
        #Other things to do...
        return {'FINISHED'}

class ButtonBlenrigON(bpy.types.Operator):
    bl_label = 'Add Blenrig to model'
    bl_idname = 'mbcrea.button_blenrig_on'
    bl_description = 'All tools to add Blenrig to the model'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global gui_active_panel_second
        gui_active_panel_second = "Blenrig"
        #Other things to do...
        return {'FINISHED'}

class ButtonBlenrigOFF(bpy.types.Operator):
    bl_label = 'Add Blenrig to model'
    bl_idname = 'mbcrea.button_blenrig_off'
    bl_description = 'All tools to add Blenrig to the model'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global gui_active_panel_second
        gui_active_panel_second = None
        #Other things to do...
        return {'FINISHED'}

class ButtonMorphingON(bpy.types.Operator):
    bl_label = 'Morph Creation'
    bl_idname = 'mbcrea.button_morphcreator_on'
    bl_description = 'Morph creation panel'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global gui_active_panel_second
        gui_active_panel_second = 'Morphcreator'
        return {'FINISHED'}

class ButtonMorphingOFF(bpy.types.Operator):
    bl_label = 'Morph Creation'
    bl_idname = 'mbcrea.button_morphcreator_off'
    bl_description = 'Morph creation panel'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global gui_active_panel_second
        gui_active_panel_second = None
        return {'FINISHED'}

class ButtonMorphExpressionON(bpy.types.Operator):
    bl_label = 'Base expressions'
    bl_idname = 'mbcrea.button_morphexpression_on'
    bl_description = 'Tool for morphing base expressions'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global gui_active_panel_second
        gui_active_panel_second = "morphs_for_expressions"
        #Other things to do...
        return {'FINISHED'}

class ButtonMorphExpressionOFF(bpy.types.Operator):
    bl_label = 'Base expressions'
    bl_idname = 'mbcrea.button_morphexpression_off'
    bl_description = 'Tool for morphing base expressions'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global gui_active_panel_second
        gui_active_panel_second = None
        #Other things to do...
        return {'FINISHED'}

class ButtonCombineExpressionON(bpy.types.Operator):
    bl_label = 'Final expressions'
    bl_idname = 'mbcrea.button_combinexpression_on'
    bl_description = 'Tool for combining base expressions'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global gui_active_panel_second
        gui_active_panel_second = "combine_expressions"
        #Other things to do...
        return {'FINISHED'}

class ButtonCombineExpressionOFF(bpy.types.Operator):
    bl_label = 'Final expressions'
    bl_idname = 'mbcrea.button_combinexpression_off'
    bl_description = 'Tool for combining base expressions'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global gui_active_panel_second
        gui_active_panel_second = None
        #Other things to do...
        return {'FINISHED'}

class ButtonBodyToolsON(bpy.types.Operator):
    bl_label = 'Body tools'
    bl_idname = 'mbcrea.button_body_tools_on'
    bl_description = 'All tools to create a compatible body'
    bl_context = 'objectmode'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        global gui_active_panel_second
        gui_active_panel_second = "Body_tools"
        #Other things to do...
        return {'FINISHED'}

class ButtonBodyToolsOFF(bpy.types.Operator):
    bl_label = 'Body tools'
    bl_idname = 'mbcrea.button_body_tools_off'
    bl_description = 'All tools to create a compatible body'
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
    ButtonAdaptationToolsON,
    ButtonAdaptationToolsOFF,
    ButtonCompatToolsON,
    ButtonCompatToolsOFF,
    ButtonRigifyON,
    ButtonRigifyOFF,
    ButtonBlenrigON,
    ButtonBlenrigOFF,
    ButtonMorphingON,
    ButtonMorphingOFF,
    ButtonMorphExpressionON,
    ButtonMorphExpressionOFF,
    ButtonCombineExpressionON,
    ButtonCombineExpressionOFF,
    ButtonBodyToolsON,
    ButtonBodyToolsOFF,
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
