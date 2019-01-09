import json
import os
import bpy
from . import algorithms

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
            populate_modifer(mod, m)

def populate_variable(v, var):
    face_rig = bpy.data.objects['MBLab_skeleton_face_rig']

    v.name = var['name']
    v.type = var['type']
    # we have one target by default
    v.targets[0].id = face_rig
    v.targets[0].transform_space = var['targets'][0]['transform_space']
    v.targets[0].transform_type = var['targets'][0]['transform_type']
    v.targets[0].bone_target = var['targets'][0]['bone_target']

def build_drivers(drivers):
    # Iterate through each driver entry and create driver
    mesh = algorithms.get_active_body()
    mname = mesh.name
    for k, v in drivers.items():
        shape_name = v['data_path'].strip('key_blocks["').strip('"].value')
        idx = bpy.data.objects[mname].data.shape_keys.key_blocks.find(shape_name)
        if idx == -1:
            algorithms.print_log_report("CRITICAL", "{0} shape key not found".format(shape_name))
            continue
        check = bpy.data.objects[mname].data.shape_keys.animation_data and \
                bpy.data.objects[mname].data.shape_keys.animation_data.drivers.\
                    find(v['data_path'])
        if check:
            algorithms.print_log_report("CRITICAL", "{0} shape key already has animation data".format(shape_name))
            continue

        # NOTE: The call to driver_add adds a modifier of type GENERATOR
        # automatically
        driver = bpy.data.objects[mname].data.shape_keys.key_blocks[idx]. \
                    driver_add('value')
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
        algorithms.print_log_report("CRITICAL", "MBLab_skeleton_face_rig is already imported")
        return False

    data_path = algorithms.get_data_path()

    # Load the face rig
    if not data_path:
        algorithms.print_log_report("CRITICAL", "{0} not found. Please check your Blender addons directory. Might need to reinstall ManuelBastioniLab".format(data_path))
        return False

    face_rig_blend = os.path.join(data_path, "humanoid_library.blend")

    if not os.path.exists(face_rig_blend):
        algorithms.print_log_report("CRITICAL", "{0} not found. Might need to reinstall ManuelBastioniLab".format(face_rig_blend))
        return False

    # append the rig
    file_path = face_rig_blend+"\\"+"Collection\Face_Rig"
    directory = face_rig_blend+"\\"+"Collection"
    try:
        bpy.ops.wm.append(filepath=file_path, filename="Face_Rig", directory=directory)
    except RuntimeError as e:
        algorithms.print_log_report("CRITICAL", "{0}".format(str(e)))
        return False

    # Load face rig json file
    json_file = os.path.join(data_path, "face_rig", "expression_drivers.json")

    if not os.path.exists(json_file):
        algorithms.print_log_report("CRITICAL", "{0} not found. Might need to reinstall ManuelBastioniLab".format(json_file))
        return False

    with open(json_file, 'r') as f:
        drivers = json.load(f)
        build_drivers(drivers)

    return True


