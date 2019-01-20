import logging
import json
import os

import bpy

from . import algorithms

logger = logging.getLogger(__name__)


def populate_modifier(mod, m):
    mod.active = m['active']
    mod.blend_in = m['blend_in']
    mod.blend_out = m['blend_out']
    mod.influence = m['influence']
    mod.mode = m['mode']
    mod.mute = m['mute']
    mod.poly_order = m['poly_order']
    # type should be created when the modifier is created
    #mod.type = m['type']
    mod.use_additive = m['use_additive']
    mod.use_influence = m['use_influence']
    mod.coefficients[0] = m['coefficients'][0]
    mod.coefficients[1] = m['coefficients'][1]

def populate_modifiers(modifiers, mlist):
    i = 0
    mod = modifiers[0]
    for m in mlist:
        if i == 0:
            populate_modifier(mod, m)
            i = i + 1
        else:
            mod = modifiers.new(m['type'])
            populate_modifier(mod, m)

def populate_variable(v, var):
    face_rig = bpy.data.objects[var['targets'][0]['id_name']]

    v.name = var['name']
    v.type = var['type']
    # we have one target by default
    v.targets[0].id = face_rig
    v.targets[0].transform_space = var['targets'][0]['transform_space']
    v.targets[0].transform_type = var['targets'][0]['transform_type']
    v.targets[0].bone_target = var['targets'][0]['bone_target']

def add_rm_drivers(drivers, add=True):
    # Iterate through each driver entry and create driver
    mesh = algorithms.get_active_body()
    mname = mesh.name
    for k, v in drivers.items():
        shape_name = v['data_path'].strip('key_blocks["').strip('"].value')
        idx = bpy.data.objects[mname].data.shape_keys.key_blocks.find(shape_name)
        if idx == -1:
            logger.critical("%s shape key not found", shape_name)
            continue
        check = bpy.data.objects[mname].data.shape_keys.animation_data and \
                bpy.data.objects[mname].data.shape_keys.animation_data.drivers.\
                    find(v['data_path'])
        if check and add:
            logger.critical("%s shape key already has animation data", shape_name)
            continue

        # NOTE: The call to driver_add adds a modifier of type GENERATOR
        # automatically
        if add:
            driver = bpy.data.objects[mname].data.shape_keys.key_blocks[idx]. \
                        driver_add('value')
        else:
            rc = bpy.data.objects[mname].data.shape_keys.key_blocks[idx].\
                    driver_remove('value')
            if not rc:
                print("failed to removed: ", shape_name, "idx=", idx)
            continue

        # Populate the driver
        driver.hide = v['hide']
        driver.lock = v['lock']
        driver.mute = v['mute']
        driver.select = v['select']
        populate_modifiers(driver.modifiers, v['modifiers'])
        driver.driver.expression = v['driver']['expression']
        driver.driver.is_valid = v['driver']['is_valid']
        driver.driver.type = v['driver']['type']
        driver.driver.use_self = v['driver']['use_self']
        variables = v['driver']['variables']
        for var in variables:
            v = driver.driver.variables.new()
            populate_variable(v, var)

def setup_face_rig():
    # check if the face rig is already imported
    if bpy.data.objects.find('MBLab_skeleton_face_rig') != -1:
        logger.critical("MBLab_skeleton_face_rig is already imported")
        return False

    data_path = algorithms.get_data_path()

    # Load the face rig
    if not data_path:
        logger.critical(
            "%s not found. Please check your Blender addons directory. Might need to reinstall ManuelBastioniLab",
            data_path)
        return False

    face_rig_blend = os.path.join(data_path, "humanoid_library.blend")

    if not os.path.exists(face_rig_blend):
        logger.critical("%s not found. Might need to reinstall ManuelBastioniLab", face_rig_blend)
        return False

    # append the rig
    file_path = face_rig_blend+"\\"+"Collection\Face_Rig"
    directory = face_rig_blend+"\\"+"Collection"
    try:
        bpy.ops.wm.append(filepath=file_path, filename="Face_Rig", directory=directory)
    except RuntimeError as e:
        logger.critical("%s", str(e))
        return False

    # Load face rig json file
    json_file = os.path.join(data_path, "face_rig", "expression_drivers.json")

    if not os.path.exists(json_file):
        logger.critical("%s not found. Might need to reinstall ManuelBastioniLab", json_file)
        return False

    with open(json_file, 'r') as f:
        drivers = json.load(f)
        add_rm_drivers(drivers)

    return True

def recursive_collection_delete(head):
    for c in head.children:
        recursive_collection_delete(c)

    head.hide_select = False
    head.hide_render = False
    head.hide_viewport = False

    for obj in head.all_objects:
        obj.hide_select = False
        obj.select_set(True)
    bpy.ops.object.delete()

    bpy.data.collections.remove(head)

def delete_face_rig():
    # check if the face rig is already imported
    facerig = bpy.data.objects.get('MBLab_skeleton_face_rig')
    if not facerig:
        logger.critical("face rig is not added")
        return False

    # check if the face rig is already imported
    phoneme = bpy.data.objects.get('MBLab_skeleton_phoneme_rig')
    if not phoneme:
        algorithms.print_log_report("CRITICAL", "face rig is not added")
        return False

    data_path = algorithms.get_data_path()

    # load face rig json file
    json_file = os.path.join(data_path, "face_rig", "expression_drivers.json")

    if not os.path.exists(json_file):
        logger.critical("%s not found. Might need to reinstall ManuelBastioniLab", json_file)
        return False

    with open(json_file, 'r') as f:
        drivers = json.load(f)
        add_rm_drivers(drivers, add=False)

    # store the original selection
    orig_selection = {}
    for ob in bpy.context.scene.objects:
        orig_selection[ob.name] = ob.select_get()
        ob.select_set(False)

    # delete the face rig
    facerig.select_set(True)
    phoneme.select_set(True)
    bpy.ops.object.delete()
    c = bpy.data.collections.get('Face_Rig')
    if c:
       recursive_collection_delete(c)

    # restore the original selection
    for ob in bpy.context.scene.objects:
        ob.select_set(orig_selection[ob.name])

    return True

