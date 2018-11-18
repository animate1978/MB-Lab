#ManuelbastioniLAB - Copyright (C) 2015-2018 Manuel Bastioni
#Official site: www.manuelbastioni.com
#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.

#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.

#You should have received a copy of the GNU General Public License
#along with this program.  If not, see <http://www.gnu.org/licenses/>.

import bpy, os, json, time
import mathutils
from . import algorithms

class RetargetEngine:

    def __init__(self):
        self.has_data = False
        self.femaleposes_exist = False
        self.maleposes_exist = False
        self.data_path = algorithms.get_data_path()
        self.maleposes_path = os.path.join(self.data_path,self.data_path,"poses","male_poses")
        self.femaleposes_path = os.path.join(self.data_path,self.data_path,"poses","female_poses")
        if os.path.isdir(self.maleposes_path):
            self.maleposes_exist = True
        if os.path.isdir(self.femaleposes_path):
            self.femaleposes_exist = True

        self.body_name = ""
        self.armature_name = ""
        self.skeleton_mapped = {}
        self.lib_filepath = algorithms.get_blendlibrary_path()
        self.knowledge_path = os.path.join(self.data_path,"retarget_knowledge.json")

        if os.path.isfile(self.lib_filepath) and os.path.isfile(self.knowledge_path):

            self.knowledge_database = algorithms.load_json_data(self.knowledge_path,"Skeleton knowledge data")
            self.local_rotation_bones = self.knowledge_database["local_rotation_bones"]
            self.last_selected_bone_name = None
            self.stored_animations = {}
            self.correction_is_sync = True
            self.is_animated_bone = ""
            self.rot_type =  ""
            self.has_data = True
        else:
            algorithms.print_log_report("CRITICAL","Retarget database not found. Please check your Blender addons directory.")
            return None


    def get_selected_posebone(self):
        if bpy.context.selected_pose_bones:
            if len(bpy.context.selected_pose_bones) > 0:
                return bpy.context.selected_pose_bones[0]
        return None


    def is_editable_bone(self):
        armat = algorithms.get_active_armature()
        if armat:
            if armat.animation_data:
                if armat.animation_data.action:
                    if self.rot_type in ["EULER","QUATERNION"]:
                        self.is_animated_bone = "VALID_BONE"
                    else:
                        self.is_animated_bone = "The bone has not anim. data"
                else:
                    self.is_animated_bone =  "{0} has not action data".format(armat.name)
            else:
                self.is_animated_bone =  "{0} has not animation data".format(armat.name)
        else:
            self.is_animated_bone =  "No armature selected"



    def get_action(self,target_armature):
        if target_armature:
            if target_armature.animation_data:
                return target_armature.animation_data.action
        return None


    def check_correction_sync(self):
        scn = bpy.context.scene
        selected_bone = self.get_selected_posebone()
        if selected_bone:
            if self.last_selected_bone_name != selected_bone.name:

                self.get_bone_rot_type()
                offsets = self.get_offset_values()
                if scn.mblab_rot_offset_0 != offsets[0]:
                    self.correction_is_sync = False
                if scn.mblab_rot_offset_1 != offsets[1]:
                    self.correction_is_sync = False
                if scn.mblab_rot_offset_2 != offsets[2]:
                    self.correction_is_sync = False
                self.is_editable_bone()
                self.last_selected_bone_name = selected_bone.name


    def get_offset_values(self):
        offsets = [0,0,0]
        scn = bpy.context.scene

        for i in [0,1,2]:
            if self.rot_type == "QUATERNION":
                channel = i+1
            else:
                channel = i
            armat_name, animation_curve, animation_data_ID =  self.get_curve_data(channel)

            if armat_name in self.stored_animations.keys():
                if animation_data_ID in self.stored_animations[armat_name].keys():
                    animation_data = self.stored_animations[armat_name][animation_data_ID]
                    if animation_curve:
                        if len(animation_curve.keyframe_points) > 0:
                            offsets[i] = animation_curve.keyframe_points[0].co[1]-animation_data[0]
        return offsets

    def identify_curve_rot(self, bone):
        r_type = "NO_CURVES"
        armat = algorithms.get_active_armature()
        if armat:
            action = self.get_action(armat)
            if action:
                if bone:
                    d_path1 = 'pose.bones["{0}"].rotation_quaternion'.format(bone.name)
                    d_path2 = 'pose.bones["{0}"].rotation_axis_angle'.format(bone.name)
                    d_path3 = 'pose.bones["{0}"].rotation_euler'.format(bone.name)

                    animation_curve1 = action.fcurves.find(d_path1,0)
                    animation_curve2 = action.fcurves.find(d_path2,0)
                    animation_curve3 = action.fcurves.find(d_path3,0)

                    if animation_curve1:
                        r_type = "QUATERNION"
                    if animation_curve2:
                        r_type = "AXIS_ANGLE"
                    if animation_curve3:
                        r_type = "EULER"
        return r_type


    def get_bone_rot_type(self):
        selected_bone = self.get_selected_posebone()
        self.rot_type =  self.identify_curve_rot(selected_bone)


    def get_bone_curve_ID(self,selected_bone):
        if self.rot_type == "QUATERNION":
            return 'pose.bones["{0}"].rotation_quaternion'.format(selected_bone.name)
        if self.rot_type == "EULER":
            return 'pose.bones["{0}"].rotation_euler'.format(selected_bone.name)
        return None

    def get_curve_data(self,channel):
        armat = algorithms.get_active_armature()
        d_path = None
        if armat:
            action = self.get_action(armat)
            if action:
                selected_bone = self.get_selected_posebone()
                if selected_bone:
                    d_path = self.get_bone_curve_ID(selected_bone)
                    if d_path:
                        animation_curve = action.fcurves.find(d_path,channel)
                        animation_data_ID = d_path+str(channel)
                        if animation_curve:
                            return (armat.name, animation_curve, animation_data_ID)
        return (None,None,None)


    def reset_bones_correction(self):
        self.stored_animations = {}


    def correct_bone_angle(self,channel,value):
        scn = bpy.context.scene
        if self.rot_type == "QUATERNION":
            channel += 1

        armat_name, animation_curve, animation_data_ID =  self.get_curve_data(channel)
        if armat_name and animation_curve and animation_data_ID:
            if armat_name not in self.stored_animations.keys():
                self.stored_animations[armat_name] = {}
            if animation_data_ID not in self.stored_animations[armat_name].keys():
                animation_data = []
                for kpoint in animation_curve.keyframe_points:
                    animation_data.append(kpoint.co[1])
                self.stored_animations[armat_name][animation_data_ID]= animation_data
            else:
                animation_data = self.stored_animations[armat_name][animation_data_ID]

            for i,v in enumerate(animation_data):
                animation_curve.keyframe_points[i].co[1] = animation_data[i]+value
            animation_curve.update()
        scn.frame_set(scn.frame_current)

    def align_bones_z_axis(self,target_armature,source_armature):
        armature_z_axis = {}
        if target_armature:
            if source_armature:
                algorithms.print_log_report("INFO","Aligning Z axis of {0} with Z axis of {1}".format(target_armature.name,source_armature.name))
                algorithms.select_and_change_mode(source_armature,'EDIT')

                for x_bone in target_armature.data.bones:
                    b_name = x_bone.name
                    source_bone_name = self.get_mapped_name(b_name)
                    if source_bone_name != None:
                        armature_z_axis[b_name] = source_armature.data.edit_bones[source_bone_name].z_axis.copy()
                    else:
                        algorithms.print_log_report("DEBUG","Bone {0} non mapped".format(b_name))
                algorithms.select_and_change_mode(source_armature,'POSE')

            algorithms.select_and_change_mode(target_armature,'EDIT')
            for armat_bone in target_armature.data.edit_bones:
                if armat_bone.name in armature_z_axis:
                    z_axis = armature_z_axis[armat_bone.name]
                    armat_bone.align_roll(z_axis)
            algorithms.select_and_change_mode(target_armature,'POSE')


    def reset_skeleton_mapped(self):
        self.skeleton_mapped = {}

    def init_skeleton_map(self,source_armat):

        self.reset_skeleton_mapped()
        self.already_mapped_bones = []
        self.spine_bones_names = None
        self.rarm_bones_names = None
        self.larm_bones_names = None
        self.rleg_bones_names = None
        self.lleg_bones_names = None
        self.head_bones_names = None
        self.pelvis_bones_names = None
        self.rtoe1_bones_names = None
        self.rtoe2_bones_names = None
        self.rtoe3_bones_names = None
        self.rtoe4_bones_names = None
        self.rtoe5_bones_names = None
        self.ltoe1_bones_names = None
        self.ltoe2_bones_names = None
        self.ltoe3_bones_names = None
        self.ltoe4_bones_names = None
        self.ltoe5_bones_names = None
        self.rfinger0_bones_names = None
        self.rfinger1_bones_names = None
        self.rfinger2_bones_names = None
        self.rfinger3_bones_names = None
        self.rfinger4_bones_names = None
        self.lfinger0_bones_names = None
        self.lfinger1_bones_names = None
        self.lfinger2_bones_names = None
        self.lfinger3_bones_names = None
        self.lfinger4_bones_names = None

        self.map_main_bones(source_armat)


    def name_combinations(self, bone_identifiers, side):

        combinations = []
        if side == 'RIGHT':
                side_id = ["r","right"]
                junctions = [".","_","-",""]
        elif side == 'LEFT':
            side_id = ["l","left"]
            junctions = [".","_","-",""]
        else:
            side_id = [""]
            junctions = [""]

        for b_id in bone_identifiers:
            for s_id in side_id:
                for junct in junctions:
                    combinations.append(b_id+junct+s_id)
                    combinations.append(s_id+junct+b_id)

        return combinations



    def get_bone_by_exact_ID(self, bones_to_scan, bone_identifiers, side):
        if bones_to_scan:
            name_combinations = self.name_combinations(bone_identifiers, side)
            for b_name in bones_to_scan:
                if b_name.lower() in name_combinations:
                    return b_name
        return None


    


    def get_bone_by_childr(self, armat, bones_to_scan, childr_identifiers, debug = False):

        if len(childr_identifiers) > 0:
            for bone_name in bones_to_scan:
                x_bone = self.get_bone(armat,bone_name)
                if x_bone:
                    for ch_bone in x_bone.children:
                        for ch_ID in childr_identifiers:
                            c1 = algorithms.is_string_in_string(ch_ID,ch_bone.name)
                            c2 = ch_bone.name in bones_to_scan
                            c3 = algorithms.is_too_much_similar(x_bone.name,ch_bone.name)
                            if c1 and c2 and not c3:
                                return x_bone.name
        return None


    def get_bones_by_index(self, bones_chain,index_data):
        index = None
        if bones_chain:
            if len(index_data) == 1:
                if index_data[0] == "LAST":
                    index = len(bones_chain)-1
                else:
                    index = index_data[0]
            if len(index_data) == 3:
                if len(bones_chain) == index_data[0]:
                    index = index_data[1]
                else:
                    index = index_data[2]

            if index == "None":
                index = None

            if index != None:
                try:
                    return bones_chain[index]
                except:
                    algorithms.print_log_report("WARNING","The chain {0} of mocap file has less bones than the chain in the lab".format(bones_chain))

        return None


    def get_bones_by_parent(self, armat, bones_to_scan, parent_IDs):
        found_bones = set()
        for bone_name in bones_to_scan:
            parent_name = self.bone_parent_name(armat,bone_name)
            for pr_ID in parent_IDs:
                if algorithms.is_string_in_string(pr_ID, parent_name):
                    found_bones.add(bone_name)
        return found_bones


    def get_bone_chains(self, armat, bone_names):
        found_chains = []
        for bone_name in bone_names:
            bn = armat.data.bones[bone_name]
            chain_names = [b.name for b in bn.parent_recursive]
            chain = [bone_name]+chain_names
            found_chains.append(chain)
        return found_chains

    def get_all_bone_names(self,armat):
        bone_names = []
        for bn in armat.data.bones:
            bone_names.append(bn.name)
        return bone_names


    def is_in_side(self,bone_names,side):

        bone_IDs = ["forearm","elbow","lowerarm","hand","wrist","finger","thumb","index","ring","pink",\
                    "thigh","upperleg","upper_leg","leg","knee","shin","calf","lowerleg","lower_leg",\
                    "toe","ball","foot"]

        combo_bones_start = []
        combo_bones_end = []

        score_level = 0.0

        if side == "RIGHT":
            ID_side1 = "r"
            ID_side2 = "right"
            ID_side3 = ["r.","r_"]
            ID_side4 = ["_r",".r"]

        if side == "LEFT":
            ID_side1 = "l"
            ID_side2 = "left"
            ID_side3 = ["l.","l_"]
            ID_side4 = ["_l",".l"]

        for b_ID in bone_IDs:
            combo_bones_start.append(ID_side1 + b_ID)
            combo_bones_end.append(b_ID + ID_side1)

        for bone_name in bone_names:
            bone_name = bone_name.lower()

            if len(bone_name) > 3:
                c1 = bone_name[:2] in ID_side3
                c2 = bone_name[-2:] in ID_side4
                c3 = ID_side2 in bone_name
                c4 = algorithms.is_in_list(bone_names,combo_bones_start,"START")
                c5 = algorithms.is_in_list(bone_names,combo_bones_end,"END")
                if  c1 or c2 or c3 or c4 or c5:
                    score_level += 1

        if len(bone_names) != 0:
            final_score = score_level/len(bone_names)
        else:
            return 0
        return final_score

    def order_with_list(self,bones_set,bones_list):
        ordered_bones = []
        for nm in bones_list:
            if nm in bones_set:
                ordered_bones.append(nm)
        return ordered_bones

    def chains_intersection(self,chains):

        chain_sets = []
        chain_inters = None
        result_chain = []

        for chain in chains:
            chain_sets.append(set(chain))

        for i,chain in enumerate(chain_sets):
            if chain_inters == None:
                chain_inters = chain
            else:
                chain_inters = chain_inters.intersection(chain)
            result_chain = self.order_with_list(chain_inters,chains[i])

        return result_chain

    def filter_chains_by_max_length(self,chains):
        longer_chains = []
        max_length = 0

        for chain in chains:
            max_length = max(max_length,len(chain))

        for chain in chains:
            if len(chain) == max_length:
                longer_chains.append(chain)
        return longer_chains

    def chains_difference(self,chain_list,subchain_list):
        subchain_set = set(subchain_list)
        chain_set = set(chain_list)
        d_chain = chain_set.difference(subchain_set)
        return self.order_with_list(d_chain,chain_list)

    def filter_chains_by_side(self,chains):

        left_chains = []
        right_chains = []
        center_chains = []
        for chain in chains:
            score_left = self.is_in_side(chain,"LEFT")
            score_right = self.is_in_side(chain,"RIGHT")

            if score_left > 0:
                left_chains.append(chain)
            elif score_right > 0:
                right_chains.append(chain)
            else:
                center_chains.append(chain)

        if len(center_chains) == 0:
            score_threshold = 0
            for chain in chains:
                score_left = self.is_in_side(chain,"LEFT")
                score_right = self.is_in_side(chain,"RIGHT")
                score_center = 1.0-score_left-score_right
                if score_center > score_threshold:
                    score_threshold = score_center
                    center_chain = chain

            center_chains.append(center_chain)
        return left_chains,center_chains,right_chains


    def filter_chains_by_tail(self,chains,chain_IDs):
        target_chains_lists = []
        if chains:
            for chain in chains:
                chain_tail = chain[0]
                if algorithms.is_in_list(chain_IDs,[chain_tail]):
                    target_chains_lists.append(chain)
        return target_chains_lists

    def clear_chain_by_dot_product(self, chain, armature):
        algorithms.select_and_change_mode(armature,'EDIT')
        if len(chain) > 2:
            edit_bones = algorithms.get_edit_bones(armature)
            bone_name = chain[0]
            if bone_name in edit_bones:
                e_bone = edit_bones[bone_name]
                if e_bone.parent:
                    v1 = e_bone.vector.normalized()
                    v2 = e_bone.parent.vector.normalized()
                    if v1.dot(v2) < 0.5:
                        algorithms.print_log_report("INFO","Retarget: Bone {0} removed BY DOT".format(bone_name))
                        chain.remove(bone_name)
        algorithms.select_and_change_mode(armature,'POSE')#TODO: store the status and restore it
        return chain


    def clear_chain_by_length(self, chain, armature):
        algorithms.select_and_change_mode(armature,'EDIT')
        for bone_name in chain:
            edit_bones = algorithms.get_edit_bones(armature)
            if bone_name in edit_bones:
                e_bone = edit_bones[bone_name]
                if e_bone.parent:
                    if e_bone.length < e_bone.parent.length/8: 
                        algorithms.print_log_report("INFO","Retarget: Bone {0} removed BY LENGTH".format(bone_name))
                        chain.remove(bone_name)
        algorithms.select_and_change_mode(armature,'POSE')#TODO: store the status and restore it
        return chain


    def filter_chains_by_dotprod(self, armature):

        self.spine_bones_names = self.clear_chain_by_dot_product(self.spine_bones_names, armature)
        self.head_bones_names = self.clear_chain_by_dot_product(self.head_bones_names, armature)
        self.rarm_bones_names = self.clear_chain_by_dot_product(self.rarm_bones_names, armature)
        self.larm_bones_names = self.clear_chain_by_dot_product(self.larm_bones_names, armature)
        
        self.pelvis_bones_names = self.clear_chain_by_dot_product(self.pelvis_bones_names, armature)
        self.ltoe_and_leg_names = self.clear_chain_by_dot_product(self.ltoe_and_leg_names, armature)
        self.rtoe_and_leg_names = self.clear_chain_by_dot_product(self.rtoe_and_leg_names, armature)

        self.rfinger0_bones_names = self.clear_chain_by_dot_product(self.rfinger0_bones_names, armature)
        self.rfinger1_bones_names = self.clear_chain_by_dot_product(self.rfinger1_bones_names, armature)
        self.rfinger2_bones_names = self.clear_chain_by_dot_product(self.rfinger2_bones_names, armature)
        self.rfinger3_bones_names = self.clear_chain_by_dot_product(self.rfinger3_bones_names, armature)
        self.rfinger4_bones_names = self.clear_chain_by_dot_product(self.rfinger4_bones_names, armature)
        self.lfinger0_bones_names = self.clear_chain_by_dot_product(self.lfinger0_bones_names, armature)
        self.lfinger1_bones_names = self.clear_chain_by_dot_product(self.lfinger1_bones_names, armature)
        self.lfinger2_bones_names = self.clear_chain_by_dot_product(self.lfinger2_bones_names, armature)
        self.lfinger3_bones_names = self.clear_chain_by_dot_product(self.lfinger3_bones_names, armature)
        self.lfinger4_bones_names = self.clear_chain_by_dot_product(self.lfinger4_bones_names, armature)


    def filter_chains_by_length(self, armature):

        
        self.head_bones_names = self.clear_chain_by_length(self.head_bones_names, armature)
        self.rarm_bones_names = self.clear_chain_by_length(self.rarm_bones_names, armature)
        self.larm_bones_names = self.clear_chain_by_length(self.larm_bones_names, armature)
        self.rleg_bones_names = self.clear_chain_by_length(self.rleg_bones_names, armature)
        self.lleg_bones_names = self.clear_chain_by_length(self.lleg_bones_names, armature)
        
        self.ltoe_and_leg_names = self.clear_chain_by_length(self.ltoe_and_leg_names, armature)
        self.rtoe_and_leg_names = self.clear_chain_by_length(self.rtoe_and_leg_names, armature)

        self.rfinger0_bones_names = self.clear_chain_by_length(self.rfinger0_bones_names, armature)
        self.rfinger1_bones_names = self.clear_chain_by_length(self.rfinger1_bones_names, armature)
        self.rfinger2_bones_names = self.clear_chain_by_length(self.rfinger2_bones_names, armature)
        self.rfinger3_bones_names = self.clear_chain_by_length(self.rfinger3_bones_names, armature)
        self.rfinger4_bones_names = self.clear_chain_by_length(self.rfinger4_bones_names, armature)
        self.lfinger0_bones_names = self.clear_chain_by_length(self.lfinger0_bones_names, armature)
        self.lfinger1_bones_names = self.clear_chain_by_length(self.lfinger1_bones_names, armature)
        self.lfinger2_bones_names = self.clear_chain_by_length(self.lfinger2_bones_names, armature)
        self.lfinger3_bones_names = self.clear_chain_by_length(self.lfinger3_bones_names, armature)
        self.lfinger4_bones_names = self.clear_chain_by_length(self.lfinger4_bones_names, armature)

    def filter_chains_by_ID(self,chains,chain_IDs):
        target_chains_lists = []
        for chain in chains:
            if algorithms.is_in_list(chain_IDs,chain):
                target_chains_lists.append(chain)
        return target_chains_lists

    def filter_chains_by_order(self, chains, n_ord):
        named_fingers = ["thu","ind","mid","ring","pink"]
        identifiers = []
        for chain in chains:
            if len(chain) > 0:
                identifiers.append(chain[0])
        identifiers.sort()
        result_chain = []
        chain_order =None
        chain_ID = None

        if algorithms.is_in_list(named_fingers,identifiers):
            chain_order = "NAMED"
        else:
            chain_order = "NUMBERED"
        if chain_order == "NAMED":
            chain_ID = named_fingers[n_ord]
        if chain_order == "NUMBERED":
            if len(identifiers) > n_ord:
                chain_ID = identifiers[n_ord]
        if chain_ID:
            chain_ID = chain_ID.lower()
            for chain in chains:
                chain_tail = chain[0]
                chain_tail = chain_tail.lower()
                if chain_ID in chain_tail:
                    result_chain = chain
                    return result_chain
        return result_chain


    def identify_bone_chains(self,chains, debug = False):
        arm_chain_IDs = ["arm","elbow","hand","wrist","finger","thumb","index","ring","pink","mid"]
        leg_chain_IDs = ["thigh","upperleg","upper_leg","leg","knee","shin","calf","lowerleg","lower_leg","foot","ankle","toe","ball"]
        head_chain_IDs = ["head","neck","skull","face","spine"]
        finger_chain_IDs = ["finger","thumb","index","ring","pink","mid"]
        foot_chain_IDs = ["foot","ankle","toe","ball"]

        max_right_arm_chain = []
        max_left_arm_chain = []
        max_right_leg_chain = []
        max_left_leg_chain = []
        max_head_chain = []

        max_left_finger_chains = []
        max_right_finger_chains = []

        left_chains,center_chains,right_chains = self.filter_chains_by_side(chains)

        head_tail_chains = self.filter_chains_by_ID(center_chains,head_chain_IDs)
        head_tail_chains = self.filter_chains_by_max_length(head_tail_chains)

        arms_tail_chains = self.filter_chains_by_ID(chains,arm_chain_IDs)
        arms_tail_chains = self.filter_chains_by_max_length(arms_tail_chains)

        right_arm_tail_chains = self.filter_chains_by_tail(right_chains,arm_chain_IDs)
        right_arm_tail_chains = self.filter_chains_by_max_length(right_arm_tail_chains)

        left_arm_tail_chains = self.filter_chains_by_tail(left_chains,arm_chain_IDs)
        left_arm_tail_chains = self.filter_chains_by_max_length(left_arm_tail_chains)

        right_fingers_tail_chains = self.filter_chains_by_tail(right_chains,finger_chain_IDs)
        left_fingers_tail_chains = self.filter_chains_by_tail(left_chains,finger_chain_IDs)

        right_foot_tail_chains = self.filter_chains_by_tail(right_chains,foot_chain_IDs)
        right_foot_tail_chains.sort()
        self.rtoe_and_leg_names = right_foot_tail_chains[0]
        right_foot_tail_chains = self.filter_chains_by_max_length(right_foot_tail_chains)

        left_foot_tail_chains = self.filter_chains_by_tail(left_chains,foot_chain_IDs)
        left_foot_tail_chains.sort()
        self.ltoe_and_leg_names = left_foot_tail_chains[0]
        left_foot_tail_chains = self.filter_chains_by_max_length(left_foot_tail_chains)

        feet_tail_chains = self.filter_chains_by_tail(chains,foot_chain_IDs)

        spine_chain = self.chains_intersection(arms_tail_chains)

        head_and_spine_chains = self.chains_intersection(head_tail_chains)
        head_chain = self.chains_difference(head_and_spine_chains,spine_chain)

        r_finger_arm_spine_chain = self.chains_intersection(right_fingers_tail_chains)
        right_fingers_chain = [self.chains_difference(fingr,r_finger_arm_spine_chain) for fingr in right_fingers_tail_chains]

        l_finger_arm_spine_chain = self.chains_intersection(left_fingers_tail_chains)
        left_fingers_chain = [self.chains_difference(fingr,l_finger_arm_spine_chain) for fingr in left_fingers_tail_chains]

        r_arm_spine_chain = self.chains_intersection(right_arm_tail_chains)
        right_arm_chain = self.chains_difference(r_arm_spine_chain,spine_chain)

        l_arm_spine_chain = self.chains_intersection(left_arm_tail_chains)
        left_arm_chain = self.chains_difference(l_arm_spine_chain,spine_chain)

        r_leg_and_spine_chain = self.chains_intersection(right_foot_tail_chains)
        l_leg_and_spine_chain = self.chains_intersection(left_foot_tail_chains)

        right_leg_chain = self.chains_difference(r_leg_and_spine_chain,spine_chain)
        left_leg_chain = self.chains_difference(l_leg_and_spine_chain,spine_chain)

        right_toes_chain = [self.chains_difference(toe,r_leg_and_spine_chain) for toe in right_foot_tail_chains]
        right_toes_chain = self.filter_chains_by_max_length(right_toes_chain)

        left_toes_chain = [self.chains_difference(toe,l_leg_and_spine_chain) for toe in left_foot_tail_chains]
        left_toes_chain = self.filter_chains_by_max_length(left_toes_chain)

        pelvis_chain = self.chains_intersection(feet_tail_chains)

        r_finger0_chain = self.filter_chains_by_order(right_fingers_chain, 0)
        r_finger1_chain = self.filter_chains_by_order(right_fingers_chain, 1)
        r_finger2_chain = self.filter_chains_by_order(right_fingers_chain, 2)
        r_finger3_chain = self.filter_chains_by_order(right_fingers_chain, 3)
        r_finger4_chain = self.filter_chains_by_order(right_fingers_chain, 4)

        l_finger0_chain = self.filter_chains_by_order(left_fingers_chain, 0)
        l_finger1_chain = self.filter_chains_by_order(left_fingers_chain, 1)
        l_finger2_chain = self.filter_chains_by_order(left_fingers_chain, 2)
        l_finger3_chain = self.filter_chains_by_order(left_fingers_chain, 3)
        l_finger4_chain = self.filter_chains_by_order(left_fingers_chain, 4)

        self.spine_bones_names = spine_chain
        self.head_bones_names = head_chain
        self.rarm_bones_names = right_arm_chain
        self.larm_bones_names = left_arm_chain
        self.rleg_bones_names = right_leg_chain
        self.lleg_bones_names = left_leg_chain
        self.pelvis_bones_names = pelvis_chain

        self.rfinger0_bones_names = r_finger0_chain
        self.rfinger1_bones_names = r_finger1_chain
        self.rfinger2_bones_names = r_finger2_chain
        self.rfinger3_bones_names = r_finger3_chain
        self.rfinger4_bones_names = r_finger4_chain
        self.lfinger0_bones_names = l_finger0_chain
        self.lfinger1_bones_names = l_finger1_chain
        self.lfinger2_bones_names = l_finger2_chain
        self.lfinger3_bones_names = l_finger3_chain
        self.lfinger4_bones_names = l_finger4_chain

    def get_ending_bones(self, armat):
        found_bones = set()
        for bn in armat.data.bones:
            if len(bn.children) == 0:
                found_bones.add(bn.name)
        return found_bones

    def string_similarity(self, main_string, identifiers, side):
        m_string = main_string.lower()
        sub_string_found = False
        substrings = []
        if side == 'LEFT':
            substrings = ["l-","-l","_l","l_",".l","l.","left"]
        if side == 'RIGHT':
            substrings = ["r-","-r","_r","r_",".r","r.","right"]

        for id_string in identifiers:
            if id_string in m_string:
                sub_string_found = True

        if sub_string_found:
            strings_to_subtract = identifiers + substrings
            for s_string in strings_to_subtract:
                s_string = s_string.lower()
                if s_string in m_string:
                    m_string = m_string.replace(s_string,"")
            return len(m_string)
        return 1000


    def get_bone_by_similar_ID(self, bones_to_scan, bone_identifiers, side):
        diff_length = 100
        result = None


        if bones_to_scan:
            for bone_name in bones_to_scan:
                score = self.string_similarity(bone_name, bone_identifiers, side)
                if score < diff_length:
                    diff_length = score
                    result = bone_name
        return result



    def find_bone(self,armat,bone_type,search_method):

        if self.knowledge_database:
            bone_knowledge = self.knowledge_database[bone_type]
            main_IDs = bone_knowledge["main_IDs"]
            children_IDs = bone_knowledge["children_IDs"]
            parent_IDs = bone_knowledge["parent_IDs"]
            side = bone_knowledge["side"]
            chain_ID =  bone_knowledge["chain_ID"]
            position_in_chain = bone_knowledge["position_in_chain"]
            bones_chain = None

            if chain_ID == "spine_bones_names":
                bones_chain = self.spine_bones_names
            elif chain_ID == "rarm_bones_names":
                bones_chain = self.rarm_bones_names
            elif chain_ID == "larm_bones_names":
                bones_chain = self.larm_bones_names
            elif chain_ID == "rleg_bones_names":
                bones_chain = self.rleg_bones_names
            elif chain_ID == "lleg_bones_names":
                bones_chain = self.lleg_bones_names
            elif chain_ID == "head_bones_names":
                bones_chain = self.head_bones_names
            elif chain_ID == "pelvis_bones_names":
                bones_chain = self.pelvis_bones_names
            elif chain_ID == "rtoe_and_leg_names":
                bones_chain = self.rtoe_and_leg_names
            elif chain_ID == "ltoe_and_leg_names":
                bones_chain = self.ltoe_and_leg_names
            elif chain_ID == "rfinger0_bones_names":
                bones_chain = self.rfinger0_bones_names
            elif chain_ID == "rfinger1_bones_names":
                bones_chain = self.rfinger1_bones_names
            elif chain_ID == "rfinger2_bones_names":
                bones_chain = self.rfinger2_bones_names
            elif chain_ID == "rfinger3_bones_names":
                bones_chain = self.rfinger3_bones_names
            elif chain_ID == "rfinger4_bones_names":
                bones_chain = self.rfinger4_bones_names
            elif chain_ID == "lfinger0_bones_names":
                bones_chain = self.lfinger0_bones_names
            elif chain_ID == "lfinger1_bones_names":
                bones_chain = self.lfinger1_bones_names
            elif chain_ID == "lfinger2_bones_names":
                bones_chain = self.lfinger2_bones_names
            elif chain_ID == "lfinger3_bones_names":
                bones_chain = self.lfinger3_bones_names
            elif chain_ID == "lfinger4_bones_names":
                bones_chain = self.lfinger4_bones_names
            elif chain_ID == "all_chains":
                bones_chain = self.get_all_bone_names(armat)

            if bones_chain:

                all_methods = ["by_exact_name", "by_chain_index","by_similar_name","by_children"]
                search_sequence = [search_method] #The first method is the one in knowledge

                for methd in all_methods:
                    if methd not in search_sequence:
                        search_sequence.append(methd)

                for s_method in search_sequence:
                    if s_method == "by_exact_name":
                        result = self.get_bone_by_exact_ID(bones_chain, main_IDs, side)

                        if result:
                            algorithms.print_log_report("INFO","Retarget: Bone {0} found BY EXACT NAME".format(bone_type))
                            if result not in self.already_mapped_bones:
                                self.already_mapped_bones.append(result)
                                algorithms.print_log_report("INFO","Retarget: {0} added to mapped bones".format(result))
                                return result

                    if s_method == "by_similar_name":
                        result = self.get_bone_by_similar_ID(bones_chain, main_IDs, side)

                        if result:
                            algorithms.print_log_report("INFO","Retarget: Bone {0} found BY SIMILAR NAME".format(bone_type))
                            if result not in self.already_mapped_bones:
                                self.already_mapped_bones.append(result)
                                algorithms.print_log_report("INFO","Retarget: {0} added to mapped bones".format(result))
                                return result

                    if s_method == "by_children":
                        result = self.get_bone_by_childr(armat, bones_chain, children_IDs)

                        if result:
                            algorithms.print_log_report("INFO","Retarget: Bone {0} found BY CHILDREN".format(bone_type))
                            if result not in self.already_mapped_bones:
                                self.already_mapped_bones.append(result)
                                algorithms.print_log_report("INFO","Retarget: {0} added to mapped bones".format(result))
                                return result

                    if s_method == "by_chain_index":
                        result = self.get_bones_by_index(bones_chain,position_in_chain)

                        if result:
                            algorithms.print_log_report("INFO","Retarget: Bone {0} found BY CHAIN INDEX".format(bone_type))
                            if result not in self.already_mapped_bones:
                                self.already_mapped_bones.append(result)
                                algorithms.print_log_report("INFO","Retarget: {0} added to mapped bones".format(result))
                                return result

                algorithms.print_log_report("WARNING","All retarget methods failed for {0}.".format(bone_type))
                #algorithms.print_log_report("WARNING","No candidates found in: {0}, or the candidate found is already mapped to another bone".format(bones_chain))
                return None
        else:
            return None


    def bone_parent_name(self,armat,b_name):
        x_bone = self.get_bone(armat,b_name)
        if x_bone:
            if x_bone.parent:
                return x_bone.parent.name
        return None

    def get_bone(self,armat,b_name,b_type = "TARGET"):
        if armat:
            if b_type == "TARGET":
                if b_name:
                    if b_name in armat.pose.bones:
                        return armat.pose.bones[b_name]
            if b_type == "SOURCE":
                b_name = self.get_mapped_name(b_name)
                if b_name:
                    if b_name in armat.pose.bones:
                        return armat.pose.bones[b_name]
        return None

    def get_target_editbone(self,armat,b_name,):
        if bpy.context.object.mode == "EDIT":
            if b_name:
                ebone = algorithms.get_edit_bone(armat, b_name)
                if ebone:
                    return ebone
                else:
                    algorithms.print_log_report("WARNING","{0} not found in edit mode of target armature {1}".format(b_name,armat))
                    return None
        else:
            algorithms.print_log_report("WARNING","Warning: Can't get the edit bone of {0} because the mode is {1}".format(bpy.context.scene.objects.active,bpy.context.object.mode))
        return None

    def get_source_editbone(self,armat,b_name):
        if bpy.context.object.mode == "EDIT":
            b_name = self.get_mapped_name(b_name)
            if b_name:
                ebone = algorithms.get_edit_bone(armat, b_name)
                if ebone:
                    return ebone
                else:
                    algorithms.print_log_report("WARNING","{0} not found in edit mode of source armature {1}".format(b_name,armat))
                    return None
        else:
            algorithms.print_log_report("WARNING","Warning: Can't get the edit bone of {0} because the mode is {1}".format(bpy.context.scene.objects.active,bpy.context.object.mode))
        return None


    def get_mapped_name(self, b_name):
        if b_name in self.skeleton_mapped:
            return self.skeleton_mapped[b_name]
        else:
            return None

    def map_bone(self,armat,b_name,b_type,s_method):
        mapped_name = self.find_bone(armat,b_type,s_method)
        if mapped_name != None:
            self.skeleton_mapped[b_name] = mapped_name

    def map_by_direct_parent(self,armat,childr_name,map_name):
        childr_bone_name = self.get_mapped_name(childr_name)

        if childr_bone_name:
            parent_bone_name = self.bone_parent_name(armat,childr_bone_name)
            if parent_bone_name:
                if parent_bone_name not in self.already_mapped_bones:
                    self.skeleton_mapped[map_name] = parent_bone_name
                    self.already_mapped_bones.append(parent_bone_name)
                return True
        algorithms.print_log_report("WARNING","Error in mapping {1} as direct parent of {0}".format(childr_name,map_name))
        return False

    def map_main_bones(self,armat):

        ending_bones = self.get_ending_bones(armat)
        chains = self.get_bone_chains(armat,ending_bones)
        self.identify_bone_chains(chains,False)
        self.filter_chains_by_length(armat)
        self.filter_chains_by_dotprod(armat)

        self.map_bone(armat,"clavicle_L","LCLAVICLE","by_exact_name")
        self.map_bone(armat,"clavicle_R","RCLAVICLE","by_exact_name")
        self.map_bone(armat,"head","HEAD","by_exact_name")
        self.map_bone(armat,"lowerarm_R","RFOREARM","by_exact_name")
        self.map_bone(armat,"lowerarm_L","LFOREARM","by_exact_name")
        self.map_bone(armat,"upperarm_R","RUPPERARM","by_children")
        self.map_bone(armat,"upperarm_L","LUPPERARM","by_children")
        self.map_bone(armat,"hand_R","RHAND","by_exact_name")
        self.map_bone(armat,"hand_L","LHAND","by_exact_name")
        self.map_bone(armat,"breast_R","RBREAST","by_exact_name")
        self.map_bone(armat,"breast_L","LBREAST","by_exact_name")
        self.map_bone(armat,"calf_R","RCALF","by_exact_name")
        self.map_bone(armat,"calf_L","LCALF","by_exact_name")
        self.map_bone(armat,"foot_R","RFOOT","by_exact_name")
        self.map_bone(armat,"foot_L","LFOOT","by_exact_name")
        self.map_bone(armat,"toes_R","RTOE","by_exact_name")
        self.map_bone(armat,"toes_L","LTOE","by_exact_name")
        self.map_bone(armat,"pelvis","PELVIS","by_exact_name")
        self.map_bone(armat,"spine03","CHEST","by_chain_index")

        if not self.map_by_direct_parent(armat,"head","neck"):
            self.map_bone(armat,"neck","NECK","by_similar_name") #TODO: integrate in find function

        self.map_by_direct_parent(armat,"spine03","spine02")
        self.map_by_direct_parent(armat,"spine02","spine01")
        self.map_by_direct_parent(armat,"calf_R","thigh_R")
        self.map_by_direct_parent(armat,"calf_L","thigh_L")

        self.map_bone(armat,"thumb03_R","RTHUMB03","by_chain_index")
        self.map_bone(armat,"thumb02_R","RTHUMB02","by_chain_index")
        self.map_bone(armat,"thumb01_R","RTHUMB01","by_chain_index")
        self.map_bone(armat,"index03_R","RINDEX03","by_chain_index")
        self.map_bone(armat,"index02_R","RINDEX02","by_chain_index")
        self.map_bone(armat,"index01_R","RINDEX01","by_chain_index")
        self.map_bone(armat,"index00_R","RINDEX00","by_exact_name")
        self.map_bone(armat,"middle03_R","RMIDDLE03","by_chain_index")
        self.map_bone(armat,"middle02_R","RMIDDLE02","by_chain_index")
        self.map_bone(armat,"middle01_R","RMIDDLE01","by_chain_index")
        self.map_bone(armat,"middle00_R","RMIDDLE00","by_exact_name")
        self.map_bone(armat,"ring03_R","RRING03","by_chain_index")
        self.map_bone(armat,"ring02_R","RRING02","by_chain_index")
        self.map_bone(armat,"ring01_R","RRING01","by_chain_index")
        self.map_bone(armat,"ring00_R","RRING00","by_exact_name")
        self.map_bone(armat,"pinky03_R","RPINKY03","by_chain_index")
        self.map_bone(armat,"pinky02_R","RPINKY02","by_chain_index")
        self.map_bone(armat,"pinky01_R","RPINKY01","by_chain_index")
        self.map_bone(armat,"pinky00_R","RPINKY00","by_exact_name")
        self.map_bone(armat,"thumb03_L","LTHUMB03","by_chain_index")
        self.map_bone(armat,"thumb02_L","LTHUMB02","by_chain_index")
        self.map_bone(armat,"thumb01_L","LTHUMB01","by_chain_index")
        self.map_bone(armat,"index03_L","LINDEX03","by_chain_index")
        self.map_bone(armat,"index02_L","LINDEX02","by_chain_index")
        self.map_bone(armat,"index01_L","LINDEX01","by_chain_index")
        self.map_bone(armat,"index00_L","LINDEX00","by_exact_name")
        self.map_bone(armat,"middle03_L","LMIDDLE03","by_chain_index")
        self.map_bone(armat,"middle02_L","LMIDDLE02","by_chain_index")
        self.map_bone(armat,"middle01_L","LMIDDLE01","by_chain_index")
        self.map_bone(armat,"middle00_L","LMIDDLE00","by_exact_name")
        self.map_bone(armat,"ring03_L","LRING03","by_chain_index")
        self.map_bone(armat,"ring02_L","LRING02","by_chain_index")
        self.map_bone(armat,"ring01_L","LRING01","by_chain_index")
        self.map_bone(armat,"ring00_L","LRING00","by_exact_name")
        self.map_bone(armat,"pinky03_L","LPINKY03","by_chain_index")
        self.map_bone(armat,"pinky02_L","LPINKY02","by_chain_index")
        self.map_bone(armat,"pinky01_L","LPINKY01","by_chain_index")
        self.map_bone(armat,"pinky00_L","LPINKY00","by_exact_name")

        self.map_bone(armat,"upperarm_twist_R","RUPPERARM_TWIST","by_exact_name")
        self.map_bone(armat,"upperarm_twist_L","LUPPERARM_TWIST","by_exact_name")
        self.map_bone(armat,"lowerarm_twist_R","RFOREARM_TWIST","by_exact_name")
        self.map_bone(armat,"lowerarm_twist_L","LFOREARM_TWIST","by_exact_name")
        self.map_bone(armat,"thigh_twist_R","RUPPERLEG_TWIST","by_exact_name")
        self.map_bone(armat,"thigh_twist_L","LUPPERLEG_TWIST","by_exact_name")
        self.map_bone(armat,"thigh_calf_R","RCALF_TWIST","by_exact_name")
        self.map_bone(armat,"thigh_calf_L","LCALF_TWIST","by_exact_name")

    def bake_animation(self,target_armat,source_armat):

        f_range = [0,bpy.context.scene.frame_current]
        algorithms.select_and_change_mode(target_armat,'POSE')
        if source_armat.animation_data:
            source_action = source_armat.animation_data.action
            f_range = source_action.frame_range

        bpy.ops.nla.bake(frame_start=f_range[0], frame_end=f_range[1],only_selected=False, visual_keying=True, clear_constraints=False, use_current_action=True, bake_types={'POSE'})
        self.remove_armature_constraints(target_armat)


    def reset_bones_rotations(self,armat):
        reset_val =  mathutils.Quaternion((1.0, 0.0, 0.0, 0.0))
        for p_bone in armat.pose.bones:
            if p_bone.rotation_mode == 'QUATERNION':
                reset_val =  mathutils.Quaternion((1.0, 0.0, 0.0, 0.0))
                p_bone.rotation_quaternion = reset_val
            elif p_bone.rotation_mode == 'AXIS_ANGLE':
                reset_val =  mathutils.Vector((0.0, 0.0, 1.0, 0.0))
                p_bone.rotation_axis_angle = reset_val
            else:
                reset_val =  mathutils.Euler((0.0, 0.0, 0.0))
                p_bone.rotation_euler = reset_val


    #TODO skeleton structure check
    def calculate_skeleton_vectors(self,armat,armat_type,rot_type):

        algorithms.select_and_change_mode(armat,"EDIT")
        if armat_type == 'SOURCE':

            head_bone = self.get_source_editbone(armat,"head")
            pelvis_bone = self.get_source_editbone(armat,"pelvis")
            hand_bone1 = self.get_source_editbone(armat,"hand_R")
            hand_bone2 = self.get_source_editbone(armat,"hand_L")

            if head_bone == None:
                head_bone = self.get_source_editbone(armat,"neck")
            if hand_bone1 == None:
                hand_bone1 = self.get_source_editbone(armat,"lowerarm_R")
            if hand_bone2 == None:
                hand_bone2 = self.get_source_editbone(armat,"lowerarm_L")

        if armat_type == 'TARGET':

            head_bone = self.get_target_editbone(armat,"head")
            pelvis_bone = self.get_target_editbone(armat,"pelvis")
            hand_bone1 = self.get_target_editbone(armat,"hand_R")
            hand_bone2 = self.get_target_editbone(armat,"hand_L")

            if head_bone == None:
                head_bone = self.get_target_editbone(armat,"neck")
            if hand_bone1 == None:
                hand_bone1 = self.get_target_editbone(armat,"lowerarm_R")
            if hand_bone2 == None:
                hand_bone2 = self.get_target_editbone(armat,"lowerarm_L")

        vect1 = None
        vect2 = None

        if head_bone != None:
            if pelvis_bone != None:
                if hand_bone1 != None:
                    if hand_bone2 != None:

                        vect1 = head_bone.head-pelvis_bone.head
                        vect2 = hand_bone2.head-hand_bone1.head

        algorithms.select_and_change_mode(armat,"POSE")

        if vect1 != None and vect2 != None:
            if rot_type == "ALIGN_SPINE":
                return vect1.normalized()
            if rot_type == "ALIGN_SHOULDERS":
                return vect2.normalized()

        return None


    def define_angle_direction(self,vect1,vect2,rot_axis,angle):

        angle1 = mathutils.Quaternion(rot_axis, angle)
        angle2 = mathutils.Quaternion(rot_axis, -angle)

        v_rot1 = vect1.copy()
        v_rot2 = vect1.copy()

        v_rot1.rotate(angle1)
        v_rot2.rotate(angle2)

        v_dot1 = v_rot1.dot(vect2)
        v_dot2 = v_rot2.dot(vect2)

        if v_dot1 >= 0 and v_dot1 >= v_dot2:
            return angle1

        if v_dot2 >= 0 and v_dot2 >= v_dot1:
            return angle2

        return mathutils.Quaternion((0.0, 0.0, 1.0), 0)


    def align_skeleton(self,target_armat,source_armat):
        self.calculate_skeleton_rotations(target_armat,source_armat,"ALIGN_SPINE")
        self.calculate_skeleton_rotations(target_armat,source_armat,"ALIGN_SHOULDERS")


    def calculate_skeleton_rotations(self,target_armat,source_armat,rot_type):

        algorithms.apply_object_transformation(source_armat)
        source_vectors = self.calculate_skeleton_vectors(source_armat,'SOURCE',rot_type)
        if source_vectors:
            target_vectors = self.calculate_skeleton_vectors(target_armat,'TARGET',rot_type)
            if rot_type == "ALIGN_SHOULDERS":
                source_vectors.z = 0.0
            if target_vectors != None:
                angle = source_vectors.angle(target_vectors)
                rot_axis = source_vectors.cross(target_vectors)
                rot = self.define_angle_direction(source_vectors,target_vectors,rot_axis,angle)
                self.rotate_skeleton(source_armat,rot)
                algorithms.apply_object_transformation(source_armat)
            else:
                algorithms.print_log_report("WARNING","Cannot calculate the target vector for armature alignment")
        else:
            algorithms.print_log_report("WARNING","Cannot calculate the source vector for armature alignment")



    def rotate_skeleton(self,armat,rot_quat):
        armat.rotation_mode = 'QUATERNION'
        armat.rotation_quaternion = rot_quat
        bpy.context.scene.update()


    def use_animation_pelvis(self,target_armat,source_armat):

        if target_armat != None:
            if source_armat != None:
                v1 = None
                v2 = None

                armat_prop = self.get_armature_proportion(target_armat,source_armat)
                algorithms.select_and_change_mode(source_armat,'EDIT')
                source_pelvis = self.get_source_editbone(source_armat,"pelvis")
                r_thigh_bone = self.get_source_editbone(source_armat,"thigh_R")
                l_thigh_bone = self.get_source_editbone(source_armat,"thigh_L")

                if source_pelvis != None:
                    if r_thigh_bone != None:
                        if l_thigh_bone != None:

                            p1 =  (r_thigh_bone.head + l_thigh_bone.head)*0.5
                            p2 =  source_pelvis.head
                            p3 =  source_pelvis.tail
                            v1 = armat_prop*(p2-p1)
                            v2 = armat_prop*(p3-p2)

                algorithms.select_and_change_mode(source_armat,'POSE')

                if v1 != None:
                    if v2 != None:
                        algorithms.select_and_change_mode(target_armat,'EDIT')
                        target_pelvis = self.get_target_editbone(target_armat,"pelvis")
                        r_thigh_bone = self.get_target_editbone(target_armat,"thigh_R")
                        l_thigh_bone = self.get_target_editbone(target_armat,"thigh_L")

                        if target_pelvis != None:
                            if r_thigh_bone != None:
                                if l_thigh_bone != None:

                                    p1a =  (r_thigh_bone.head + l_thigh_bone.head)*0.5
                                    target_pelvis.head = p1a+v1
                                    target_pelvis.tail = target_pelvis.head + v2
                        algorithms.select_and_change_mode(target_armat,'POSE')



    def armature_height(self,armat,armat_type):

        if armat:
            algorithms.set_object_visible(armat)
            algorithms.select_and_change_mode(armat,'EDIT')
            upper_point = None
            lower_point = None

            if armat_type == 'SOURCE':
                r_foot_bone = self.get_source_editbone(armat,"foot_R")
                l_foot_bone = self.get_source_editbone(armat,"foot_L")
                r_calf_bone = self.get_source_editbone(armat,"calf_R")
                l_calf_bone = self.get_source_editbone(armat,"calf_L")
                r_clavicle_bone = self.get_source_editbone(armat,"clavicle_R")
                l_clavicle_bone = self.get_source_editbone(armat,"clavicle_L")
                r_upperarm_bone = self.get_source_editbone(armat,"upperarm_R")
                l_upperarm_bone = self.get_source_editbone(armat,"upperarm_L")

            if armat_type == 'TARGET':
                r_foot_bone = self.get_target_editbone(armat,"foot_R")
                l_foot_bone = self.get_target_editbone(armat,"foot_L")
                r_calf_bone = self.get_target_editbone(armat,"calf_R")
                l_calf_bone = self.get_target_editbone(armat,"calf_L")
                r_clavicle_bone = self.get_target_editbone(armat,"clavicle_R")
                l_clavicle_bone = self.get_target_editbone(armat,"clavicle_L")
                r_upperarm_bone = self.get_target_editbone(armat,"upperarm_R")
                l_upperarm_bone = self.get_target_editbone(armat,"upperarm_L")

            if l_clavicle_bone and r_clavicle_bone:
                upper_point = (l_clavicle_bone.head + r_clavicle_bone.head)*0.5
            elif l_upperarm_bone and r_upperarm_bone:
                upper_point = (l_upperarm_bone.tail + r_upperarm_bone.tail)*0.5
            else:
                algorithms.print_log_report("WARNING","Cannot calculate armature height: clavicles not found")

            if l_foot_bone and r_foot_bone:
                lower_point = (l_foot_bone.head + r_foot_bone.head)*0.5
            elif l_calf_bone and r_calf_bone:
                lower_point = (l_calf_bone.head + r_calf_bone.head)*0.5
            else:
                algorithms.print_log_report("WARNING","Cannot calculate armature height: feet not found")

            if upper_point and lower_point:
                height = upper_point-lower_point
                algorithms.select_and_change_mode(armat,'POSE')
                return height.length
            else:
                return 0

        else:
            algorithms.print_log_report("WARNING","Cannot found the source armature for height calculation")

    def remove_armature_constraints(self,target_armature):
        for b in target_armature.pose.bones:
            if len(b.constraints) > 0:
                for cstr in b.constraints:
                    if "mbastlab_" in cstr.name:
                        b.constraints.remove(cstr)

    def add_copy_rotations(self,target_armat,source_armat,bones_to_rotate, space='WORLD'):
        for b in target_armat.pose.bones:
            if b.name in self.skeleton_mapped:
                if b.name in bones_to_rotate:
                    if self.skeleton_mapped[b.name] != None:
                        if "mbastlab_rot" not in b.constraints:
                            cstr = b.constraints.new('COPY_ROTATION')
                            cstr.target = source_armat
                            cstr.subtarget =  self.skeleton_mapped[b.name]
                            cstr.target_space = space
                            cstr.owner_space = space
                            cstr.name = "mbastlab_rot"

    def add_copy_location(self,target_armat,source_armat,bones_to_move):
        for b in target_armat.pose.bones:
            if b.name in self.skeleton_mapped:
                if b.name in bones_to_move:
                    if "mbastlab_loc" not in b.constraints:
                        cstr = b.constraints.new('COPY_LOCATION')
                        cstr.target = source_armat
                        cstr.subtarget =  self.skeleton_mapped[b.name]
                        cstr.target_space = "WORLD"
                        cstr.owner_space = "WORLD"
                        cstr.name = "mbastlab_loc"

    def add_armature_constraints(self,target_armat, source_armat):
        bones_to_rotate = []
        for b in target_armat.pose.bones:
            if b.name not in self.local_rotation_bones:
                bones_to_rotate.append(b.name)

        self.add_copy_rotations(target_armat,source_armat,bones_to_rotate)
        self.add_copy_rotations(target_armat,source_armat,self.local_rotation_bones,'LOCAL')
        self.add_copy_location(target_armat,source_armat,["pelvis"])

    def scale_armat(self,target_armat,source_armat):
        scale = self.get_armature_proportion(target_armat,source_armat)
        source_armat.scale = [scale,scale,scale]

    def clear_animation(self,armat):
        if armat:
            armat.animation_data_clear()

    def get_armature_proportion(self,target_armat,source_armat):
        t_height = self.armature_height(target_armat,'TARGET')
        s_height = self.armature_height(source_armat,'SOURCE')
        if s_height != 0:
            armat_prop = t_height/s_height
        else:
            armat_prop = 1
        return armat_prop

    def reset_pose(self, armat = None, reset_location = True):
        if not armat:
            armat = algorithms.get_active_armature()
        if armat:
            self.clear_animation(armat)
            algorithms.stop_animation()
            for p_bone in armat.pose.bones:
                algorithms.reset_bone_rot(p_bone)                
                if reset_location:
                    if p_bone.name == "pelvis":
                        p_bone.location = [0,0,0]

    def load_bones_quaternions(self, armat, data_path):
        self.reset_pose(armat)

        if armat:
            matrix_data = algorithms.load_json_data(data_path,"Pose data")
            algorithms.set_object_visible(armat)
            algorithms.select_and_change_mode(armat,"POSE")

            pose_bones = algorithms.get_pose_bones(armat)
            for p_bone in pose_bones:
                if p_bone.name in matrix_data:
                    algorithms.set_bone_rotation(p_bone, mathutils.Quaternion(matrix_data[p_bone.name]))
                else:
                    algorithms.reset_bone_rot(p_bone)

    def save_pose(self, armat, filepath):

        if armat:
            algorithms.select_and_change_mode(armat,"POSE")
            matrix_data = {}
            algorithms.set_object_visible(armat)
            pose_bones = algorithms.get_pose_bones(armat)
            for p_bone in pose_bones:
                if "muscle" not in p_bone.name:
                    if "IK_" not in p_bone.name:
                        matrix_data[p_bone.name] = [value for value in algorithms.get_bone_rotation(p_bone)]
            fp = open(filepath, 'w')
            json.dump(matrix_data,fp)
            fp.close()


    def load_pose(self,filepath, target_armature = None, use_retarget = False):

        if not target_armature:
            target_armature = algorithms.get_active_armature()
        if not target_armature:
            return False

        self.reset_bones_correction()
        self.reset_pose(target_armature)

        if use_retarget:
            source_armature = algorithms.import_object_from_lib(self.lib_filepath, "MBLab_skeleton_base_fk", "temporary_armature")
            if source_armature:
                self.load_bones_quaternions(source_armature, filepath)
                self.retarget(target_armature,source_armature, bake_animation = True)
                algorithms.remove_object(source_armature)
                algorithms.stop_animation()
        else:
            self.load_bones_quaternions(target_armature, filepath)
        self.clear_animation(target_armature)
        return True

    def load_animation(self,bvh_path, debug_mode=False):
        time1 = time.time()
        target_armature = algorithms.get_active_armature()
        if not target_armature:
            return
        self.reset_bones_correction()
        if target_armature:
            existing_obj_names = algorithms.collect_existing_objects()
            self.load_bvh(bvh_path)
            source_armature = algorithms.get_newest_object(existing_obj_names)
            if source_armature:
                if debug_mode == False:
                    self.retarget(target_armature,source_armature, True)
                    algorithms.remove_object(source_armature)
                else:
                    self.retarget(target_armature,source_armature, False)
                algorithms.play_animation()
        algorithms.print_log_report("INFO","Animation loaded in {0} sec.".format(time.time()-time1))



    def load_bvh(self,bvh_path):

        bpy.context.scene.frame_end = 0
        try:
            bpy.ops.import_anim.bvh(
                filepath = bvh_path,
                use_fps_scale = True,
                update_scene_duration = True
                )
        except:
            algorithms.print_log_report("WARNING","Standard bvh operator not found: can't import animation.")



    def retarget(self, target_armature, source_armature, bake_animation = True):

        algorithms.print_log_report("INFO","retarget with {0}".format(source_armature.name))
        if source_armature and target_armature:
            self.init_skeleton_map(source_armature)
            self.clear_animation(target_armature)
            self.align_skeleton(target_armature,source_armature)
            self.scale_armat(target_armature,source_armature)
            self.reset_bones_rotations(target_armature)
            self.use_animation_pelvis(target_armature,source_armature)
            self.align_bones_z_axis(target_armature,source_armature)
            self.remove_armature_constraints(target_armature)
            self.add_armature_constraints(target_armature,source_armature)
            if bake_animation:
                scene_modifiers_status = algorithms.get_scene_modifiers_status()
                algorithms.set_scene_modifiers_status(False)
                algorithms.set_scene_modifiers_status_by_type('ARMATURE',True)
                self.bake_animation(target_armature,source_armature)
                algorithms.set_scene_modifiers_status(False,scene_modifiers_status)


class ExpressionEngineShapeK:

    def __init__(self):
        self.has_data = False
        self.data_path = algorithms.get_data_path()
        self.human_expression_path = os.path.join(
                self.data_path,
                "expressions_comb",
                "human_expressions")

        self.anime_expression_path = os.path.join(
                self.data_path,
                "expressions_comb",
                "anime_expressions")


        self.expressions_labels = set()
        self.human_expressions_data = self.load_expression_database(self.human_expression_path)
        self.anime_expressions_data = self.load_expression_database(self.anime_expression_path)
        self.expressions_data = {}
        self.model_type = "NONE"
        self.has_data = True


    def identify_model_type(self):
        self.model_type = "NONE"

        obj = algorithms.get_active_body()
        if obj:
            current_shapekes_names = algorithms.get_shapekeys_names(obj)
            if len(current_shapekes_names) > 0:
                if "Expressions_IDHumans_max" in current_shapekes_names:
                    self.model_type = "HUMAN"
                    return
                if "Expressions_IDAnime_max" in current_shapekes_names:
                    self.model_type = "ANIME"
                    return


    def load_expression(self, filepath):

            charac_data = algorithms.load_json_data(filepath,"Character data")
            expressions_ID = algorithms.simple_path(filepath)
            if "manuellab_vers" in charac_data:
                if not algorithms.check_version(charac_data["manuellab_vers"]):
                    algorithms.print_log_report("INFO","{0} created with vers. {1}.".format(expressions_ID,charac_data["manuellab_vers"]))
            else:
                algorithms.print_log_report("INFO","No lab version specified in {0}".format(expressions_ID))

            if "structural" in charac_data:
                char_data = charac_data["structural"]
            else:
                algorithms.print_log_report("WARNING","No structural data in  {0}".format(expressions_ID))
                char_data = None

            return char_data



    def load_expression_database(self, dirpath):        
        expressions_data = {}
        if algorithms.exists_database(dirpath):
            for expression_filename in os.listdir(dirpath):
                expression_filepath = os.path.join(dirpath,expression_filename)
                e_item, extension = os.path.splitext(expression_filename)
                if "json" in extension:
                    self.expressions_labels.add(e_item)
                    expressions_data[e_item] = self.load_expression(expression_filepath)
        return expressions_data




    def sync_expression_to_GUI(self):
        #Process all expressions: reset all them and then update all them.
        #according the GUI value. TODO: optimize.         

        obj = algorithms.get_active_body()
        for expression_name in self.expressions_data.keys():
            
            # Perhaps these two lines are not required
            if not hasattr(obj, expression_name):              
                setattr(obj, expression_name, 0.0)
            
            if hasattr(obj, expression_name):                
                self.reset_expression(expression_name)

        for expression_name in sorted(self.expressions_data.keys()):
            if hasattr(obj, expression_name):
                express_val = getattr(obj, expression_name)
                if express_val != 0:
                    self.update_expression(expression_name, express_val)        


    def reset_expressions_GUI(self):
        obj = algorithms.get_active_body()
        for expression_name in self.expressions_data.keys():
            if hasattr(obj, expression_name):
                setattr(obj, expression_name, 0.0)
                self.reset_expression(expression_name)


    def update_expressions_data(self):
        self.identify_model_type()
        if self.model_type == "ANIME":
            self.expressions_data = self.anime_expressions_data
        if self.model_type == "HUMAN":
            self.expressions_data = self.human_expressions_data
        if self.model_type == "NONE":
            self.expressions_data = {}



    def update_expression(self, expression_name, express_val):       
        
        obj = algorithms.get_active_body()
        if obj:
            if not obj.data.shape_keys:                
                return None

            if expression_name in self.expressions_data:                
                expr_data = self.expressions_data[expression_name]                
                for name,value in expr_data.items():

                    sk_value = 0
                    if value < 0.5:
                        name = name+"_min"
                        sk_value = (0.5-value)*2
                    else:
                        name = name+"_max"
                        sk_value = (value-0.5)*2

                    sk_value = sk_value*express_val                    

                    if sk_value != 0:
                        if hasattr(obj.data.shape_keys,'key_blocks'):
                            if name in obj.data.shape_keys.key_blocks:
                                current_val = obj.data.shape_keys.key_blocks[name].value
                                obj.data.shape_keys.key_blocks[name].value = min(current_val+sk_value,1.0)
                            else:
                                algorithms.print_log_report("WARNING","Expression {0}: shapekey {1} not found".format(expression_name,name))



    def reset_expression(self, expression_name):
        obj = algorithms.get_active_body()

        if obj:
            if not obj.data.shape_keys:                
                return None
            if expression_name in self.expressions_data:
                expr_data = self.expressions_data[expression_name]

                for name,value in expr_data.items():
                    if value < 0.5:
                        name = name+"_min"
                    else:
                        name = name+"_max"

                    if hasattr(obj.data.shape_keys,'key_blocks'):
                        if name in obj.data.shape_keys.key_blocks:
                            obj.data.shape_keys.key_blocks[name].value = 0


    def keyframe_expression(self):
        obj = algorithms.get_active_body()
        scn = bpy.context.scene

        if obj:
            if not obj.data.shape_keys:                
                return None
            if hasattr(obj.data.shape_keys,'key_blocks'):
                for sk in obj.data.shape_keys.key_blocks:
                    if "Expressions_" in sk.name:
                        sk.keyframe_insert(data_path="value")




