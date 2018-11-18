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

import bpy, os, json
import mathutils
from . import algorithms


class SkeletonEngine:

    def __init__(self, obj_body,character_config,rigging_type):
        self.has_data = False
        self.data_path = algorithms.get_data_path()
        #characters_config = algorithms.get_configuration()
        #character_config = characters_config[character_identifier]

        if obj_body:

            self.body_name = obj_body.name
            self.joints_indices = {}
            self.armature_modifier_name = "mbastlab_armature"
            self.joints_filename = character_config["joints_base_file"]
            self.joints_offset_filename = character_config["joints_offset_file"]

            if rigging_type == "base":
                self.skeleton_template_name = "MBLab_skeleton_base_fk"
                self.groups_filename = character_config["vertexgroup_base_file"]
            if rigging_type == "ik":
                self.skeleton_template_name = "MBLab_skeleton_base_ik"
                self.groups_filename = character_config["vertexgroup_base_file"]

            if rigging_type == "muscle":
                self.skeleton_template_name = "MBLab_skeleton_muscle_fk"
                self.groups_filename = character_config["vertexgroup_muscle_file"]
            if rigging_type == "muscle_ik":
                self.skeleton_template_name = "MBLab_skeleton_muscle_ik"
                self.groups_filename = character_config["vertexgroup_muscle_file"]


            self.skeleton_name = character_config["name"]+"_skeleton"
            self.lib_filepath = algorithms.get_blendlibrary_path()
            self.joints_data_path = os.path.join(self.data_path,"joints",self.joints_filename)
            self.joints_offset_data_path = os.path.join(self.data_path,"joints",self.joints_offset_filename)
            self.vgroup_data_path = os.path.join(self.data_path,"vgroups",self.groups_filename)
            self.joints_database = algorithms.load_json_data(self.joints_data_path,"Joints data")
            self.joints_offset_database = algorithms.load_json_data(self.joints_offset_data_path,"Joints offset data")

            if self.check_skeleton(obj_body):
                obj_armat = algorithms.get_object_parent(obj_body)
            else:
                obj_armat = algorithms.import_object_from_lib(self.lib_filepath, self.skeleton_template_name, self.skeleton_name)


            if obj_armat != None:
                self.store_z_axis()
                self.armature_visibility = [x for x in obj_armat.layers]
                self.armature_name = obj_armat.name                
                self.align_bones_z_axis()
                obj_body.parent = obj_armat
                self.has_data = True
            self.load_groups(self.vgroup_data_path)
            self.add_armature_modifier()

    def check_skeleton(self, obj_body):
        obj_parent = algorithms.get_object_parent(obj_body)
        if obj_parent:
            if obj_parent.type == 'ARMATURE':
                return True
        return False

    def add_armature_modifier(self):
        if self.has_data:
            obj = self.get_body()
            armat = self.get_armature()
            parameters = {"object":armat}
            armature_modifier = algorithms.new_modifier(obj, self.armature_modifier_name,'ARMATURE', parameters)

    def move_up_armature_modifier(self):
        if self.has_data:
            obj = self.get_body()
            armature_modifier = algorithms.get_modifier(obj, self.armature_modifier_name)
            if armature_modifier:
                algorithms.move_up_modifier(obj, armature_modifier)

    def apply_armature_modifier(self):
        if self.has_data:
            obj = self.get_body()
            armature_modifier = algorithms.get_modifier(obj, self.armature_modifier_name)
            if armature_modifier:
                algorithms.apply_modifier(obj, armature_modifier)

    def apply_pose_as_rest_pose(self):
        if self.has_data:
            armat = self.get_armature()
            obj = self.get_body()
            algorithms.select_and_change_mode(armat,'POSE')
            bpy.ops.pose.armature_apply()
            algorithms.select_and_change_mode(obj,'OBJECT')

    def error_msg(self, path):
        algorithms.print_log_report("ERROR","Database file not found: {0}".format(algorithms.simple_path(path)))

    def store_z_axis(self):
        algorithms.print_log_report("INFO","Importing temporary original skeleton to store z axis")
        native_armature = algorithms.import_object_from_lib(self.lib_filepath, self.skeleton_template_name, "temp_armature")

        if native_armature:
            self.armature_z_axis = algorithms.get_all_bones_z_axis(native_armature)
            algorithms.remove_object(native_armature)

    def align_bones_z_axis(self):
        target_armature = self.get_armature()
        if target_armature:
            algorithms.select_and_change_mode(target_armature,'EDIT')
            edit_bones = algorithms.get_edit_bones(target_armature)
            for e_bone in edit_bones:                
                if e_bone.name in self.armature_z_axis:
                    z_axis = self.armature_z_axis[e_bone.name]
                    e_bone.align_roll(z_axis)
            algorithms.select_and_change_mode(target_armature,'POSE')

    def load_groups(self,filepath,use_weights = True,clear_all=True):
        if self.has_data:
            obj = self.get_body()
            g_data = algorithms.load_json_data(filepath,"Vertgroups data")

            if clear_all:
                algorithms.remove_vertgroups_all(obj)
            if g_data:
                group_names = sorted(g_data.keys())
                for group_name in group_names:
                    new_group = algorithms.new_vertgroup(obj, group_name)
                    for vert_data in g_data[group_name]:
                        if use_weights:
                            if type(vert_data) == list:                                
                                new_group.add([vert_data[0]], vert_data[1], 'REPLACE')
                            else:
                                algorithms.print_log_report("INFO","Error: wrong format for vert weight")
                        else:
                            if type(vert_data) == int:                                
                                new_group.add([vert_data], 1.0, 'REPLACE')
                            else:
                                algorithms.print_log_report("INFO","Error: wrong format for vert group")

                algorithms.print_log_report("INFO","Group loaded from {0}".format(algorithms.simple_path(filepath)))
            else:
                algorithms.print_log_report("WARNING","Vgroup file problem {0}".format(algorithms.simple_path(filepath)))


    def get_body(self):
        if self.has_data:
            return algorithms.get_object_by_name(self.body_name)

    def get_armature(self):
        if self.has_data:
            return algorithms.get_object_by_name(self.armature_name)

    def __bool__(self):
        armat = self.get_armature()
        body = self.get_body()
        if body and armat:
            return True
        else:
            return False

    def calculate_joint_location(self,obj,vertsindex_list):
        joint_verts_coords = []
        for v_idx in vertsindex_list:
            vert = obj.data.vertices[v_idx]
            joint_verts_coords.append(vert.co)
        return algorithms.average_center(joint_verts_coords)

    def fit_joints(self):

        armat = self.get_armature()
        body = self.get_body()

        if armat and body:
            algorithms.set_object_visible(armat)
            algorithms.print_log_report("DEBUG","Fitting armature {0}".format(armat.name))
            armat.data.use_mirror_x = False
            current_active_obj = algorithms.get_active_object()
            algorithms.select_and_change_mode(armat,"EDIT")
            edit_bones = algorithms.get_edit_bones(armat)
            for e_bone in edit_bones:
                tail_name = "".join((e_bone.name, "_tail"))
                head_name = "".join((e_bone.name, "_head"))

                if tail_name in self.joints_database:
                    tail_location = self.calculate_joint_location(body, self.joints_database[tail_name])

                    if self.joints_offset_database:
                        if tail_name in self.joints_offset_database:
                            tail_delta = mathutils.Vector(self.joints_offset_database[tail_name])
                            tail_location += tail_delta
                    e_bone.tail = tail_location

                if head_name in self.joints_database:
                    head_location = self.calculate_joint_location(body, self.joints_database[head_name])

                    if self.joints_offset_database:
                        if head_name in self.joints_offset_database:
                            head_delta = mathutils.Vector(self.joints_offset_database[head_name])
                            head_location += head_delta
                    e_bone.head = head_location

            algorithms.select_and_change_mode(armat,"OBJECT")
            self.align_bones_z_axis()
            algorithms.update_bendy_bones(armat)
            algorithms.set_active_object(current_active_obj)






