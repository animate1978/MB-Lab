import bpy

from bpy.types import StretchToConstraint, CopyRotationConstraint

align_table = {
  "upperarm_twist_L": "upperarm_L",
  "upperarm_twist_R": "upperarm_R",
  "lowerarm_twist_L": "lowerarm_L",
  "lowerarm_twist_R": "lowerarm_R",
  "thigh_twist_L": "thigh_L",
  "thigh_twist_R": "thigh_R",
  "calf_twist_L": "calf_L",
  "calf_twist_R": "calf_R",
  "rot_helper01_L": "calf_L",
  "rot_helper01_R": "calf_R",
  "rot_helper02_L": "lowerarm_L",
  "rot_helper02_R": "lowerarm_R",
  "rot_helper03_L": "thigh_L",
  "rot_helper03_R": "thigh_R",
  "rot_helper04_L": "foot_L",
  "rot_helper04_R": "foot_R",
  "rot_helper06_L": "thigh_L",
  "rot_helper06_R": "thigh_R",
}

bpy.ops.object.mode_set(mode='OBJECT')

bpy.context.view_layer.layer_collection.children['ARMATURE'].hide_viewport = False

for rig_name in ['MBLab_skeleton_base_fk', 'MBLab_skeleton_base_ik', 'MBLab_skeleton_muscle_fk', 'MBLab_skeleton_muscle_ik']:
    rig = bpy.data.objects[rig_name]

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = rig
    rig.select_set(True)
    bpy.ops.object.mode_set(mode='OBJECT')

    assert bpy.context.active_object == rig

    bpy.ops.object.mode_set(mode='EDIT')
    eb = rig.data.edit_bones

    # Align helper bones
    for name, origin in align_table.items():
        bone = eb.get(name)
        if bone:
            for child in bone.children:
                child.use_connect = False

            matrix = eb[origin].matrix.copy()
            matrix.translation = bone.head
            bone.matrix = matrix

    bpy.ops.object.mode_set(mode='OBJECT')
    pb = rig.pose.bones

    # Reset Stretch To
    for pbone in pb:
        for con in pbone.constraints:
            if isinstance(con, StretchToConstraint):
                con.rest_length = pbone.bone.length

    # Fix muscles
    for pbone in pb:
        bone = pbone.bone
        name = bone.name
        if bone.bbone_segments > 1 and 'muscle' in name:
            # Fix handles
            if '_L' in name or '_R' in name:
                prev_name = name[0:-2] + '_H' + name[-2:]
                next_name = name[0:-2] + '_T' + name[-2:]
            else:
                prev_name = name + '_H'
                next_name = name + '_T'

            bone.bbone_handle_type_start = 'ABSOLUTE'
            bone.bbone_custom_handle_start = pb[prev_name].bone
            bone.bbone_handle_type_end = 'ABSOLUTE'
            bone.bbone_custom_handle_end = pb[next_name].bone

            # Remove unnecessary Copy Rotation
            copyrot = [con for con in pbone.constraints if isinstance(con, CopyRotationConstraint)]
            for con in copyrot:
                pbone.constraints.remove(con)

    # Fix rotation order for the constraint
    for name in ['rot_helper01_L', 'rot_helper01_R', 'rot_helper02_L', 'rot_helper02_R']:
        pbone = pb.get(name)
        if pbone:
            pbone.rotation_mode = 'YZX'
