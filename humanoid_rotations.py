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


import bpy
from math import radians, degrees


# ------------------------------------------------------------------------
#    Initializations
# ------------------------------------------------------------------------

MB_list = [
        "root",        #0
        "head",        #1
        "neck",        #2
        "clavicle_L",  #3
        "clavicle_R",  #4
        "breast_L",    #5
        "breast_R",    #6
        "spine03",     #7
        "spine02",     #8
        "spine01",     #9
        "pelvis",      #10
        "thigh_L",     #11
        "calf_L",      #12
        "foot_L",      #13
        "thigh_R",     #14
        "calf_R",      #15
        "foot_R",      #16
        "upperarm_L",  #17
        "lowerarm_L",  #18
        "hand_L",      #19
        "upperarm_R",  #20
        "lowerarm_R",  #21
        "hand_R"       #22
        ]

#left hand
thumb_l = ["thumb01_L", "thumb02_L", "thumb03_L"]
index_l = ["index00_L", "index01_L", "index02_L", "index03_L"]
middle_l = ["middle00_L", "middle01_L", "middle02_L", "middle03_L"]
ring_l = ["ring00_L", "ring01_L", "ring02_L", "ring03_L"]
pinky_l = ["pinky00_L", "pinky01_L", "pinky02_L", "pinky03_L"]
#right hand
thumb_r = ["thumb01_R", "thumb02_R", "thumb03_R"]
index_r = ["index00_R", "index01_R", "index02_R", "index03_R"]
middle_r = ["middle00_R", "middle01_R", "middle02_R", "middle03_R"]
ring_r = ["ring00_R", "ring01_R", "ring02_R", "ring03_R"]
pinky_r = ["pinky00_R", "pinky01_R", "pinky02_R", "pinky03_R"]

fingers = thumb_l + index_l + middle_l + ring_l + pinky_l + thumb_r + index_r + middle_r + ring_r + pinky_r

rotation_limits_dict = {
        MB_list[1]: [-22, 37, -45, 45, -30, 30],    #"head"
        MB_list[2]: [-22, 37, -45, 45, -30, 30],    #"neck"
        MB_list[3]: [-30, 30, 0, 0, -30, 10],       #"clavicle_L"
        MB_list[4]: [-30, 30, 0, 0, -10, 30],       #"clavicle_R"
        #MB_list[10]: [-22, 45, -45, 45, -15, 15],   #"pelvis"
        MB_list[9]: [-45, 68, -45, 45, -30, 30],    #"spine01"
        MB_list[8]: [-45, 68, -45, 45, -30, 30],    #"spine02"
        MB_list[7]: [-45, 22, -45, 45, -30, 30],    #"spine03"
        MB_list[17]: [-58, 95, -15, 30, -60, 105],  #"upperarm_L"
        MB_list[20]: [-58, 95, -30, 15, -105, 60],  #"upperarm_R"
        MB_list[18]: [0, 146, 0, 15, 0, 0],        #"lowerarm_L"
        MB_list[21]: [0, 146, -15, 0, 0, 0],       #"lowerarm_R"
        MB_list[19]: [-45, 45, -90, 86, -25, 36],   #"hand_L"
        MB_list[22]: [-45, 45, -86, 90, -36, 25],   #"hand_R"
        MB_list[11]: [-90, 45, -15, 15, -22, 17],   #"thigh_L"
        MB_list[14]: [-90, 45, -15, 15, -22, 17],   #"thigh_R"
        MB_list[12]: [-150, 0, 0, 0, 0, 0],         #"calf_L"
        MB_list[15]: [-150, 0, 0, 0, 0, 0],         #"calf_R"
        MB_list[13]: [-44, 45, -26, 26, -15, 74],   #"foot_L"
        MB_list[16]: [-45, 44, -26, 26, -74, 15],   #"foot_R"
        }

#Dictionary for fingers
def finger_dict(fingers):
    fd = {}
    for finger in fingers:
        if "00_" in finger:
            fd.update({finger: [0,0,0,0,-5,5]})
        else:
            fd.update({finger: [-90,0,0,0,-5,5]})
    return fd

fd = finger_dict(fingers)


###############################################################################################################################
#CONSTRAINT OPS

#************************************************************ADD LIMIT ROTATION

def limit_bone_rotation(Dict, pb):
    for bone in pb:
        if bone.name in Dict:
            bc = bone.constraints.new(type='LIMIT_ROTATION')
            bc.owner_space = 'LOCAL'
            bc.use_limit_x = True
            bc.use_limit_y = True
            bc.use_limit_z = True
            bc.min_x = radians(Dict[bone.name][0])
            bc.max_x = radians(Dict[bone.name][1])
            bc.min_y = radians(Dict[bone.name][2])
            bc.max_y = radians(Dict[bone.name][3])
            bc.min_z = radians(Dict[bone.name][4])
            bc.max_z = radians(Dict[bone.name][5])


#************************************************************REMOVE BONE CONSTRAINT

def remove_bone_constraints(constraint, pb):
    for bone in pb:
        rbc = [r for r in bone.constraints if r.type == constraint]
        for r in rbc:
            bone.constraints.remove(r)


###############################################################################################################################
#MAIN

def get_skeleton():
    if bpy.context.object.type == 'ARMATURE':
        return bpy.context.object
    else:
        return bpy.context.object.parent

# def humanoid_rot_limits():
#     armature = get_skeleton()
#     pb = armature.pose.bones
#     limit_bone_rotation(ragdoll_dict, pb)
#     limit_finger_rotation(fd, pb)
