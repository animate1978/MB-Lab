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

import bpy
import mathutils

from . import algorithms, utils, file_ops
from .utils import get_object_parent

logger = logging.getLogger(__name__)


class SkeletonEngine:
    armature_modifier_name = "mbastlab_armature"

    def __init__(self, obj_body, character_config, rigging_type):
        self.has_data = False
        self.data_path = file_ops.get_data_path()
        #characters_config = algorithms.get_configuration()
        #character_config = characters_config[character_identifier]

        if obj_body:

            self.body_name = obj_body.name
            self.joints_filename = character_config["joints_base_file"]
            self.joints_offset_filename = character_config["joints_offset_file"]

            if rigging_type == "base":
                self.skeleton_template_name = "MBLab_skeleton_base_fk"
                self.groups_filename = character_config["vertexgroup_base_file"]
            elif rigging_type == "ik":
                self.skeleton_template_name = "MBLab_skeleton_base_ik"
                self.groups_filename = character_config["vertexgroup_base_file"]
            elif rigging_type == "muscle":
                self.skeleton_template_name = "MBLab_skeleton_muscle_fk"
                self.groups_filename = character_config["vertexgroup_muscle_file"]
            elif rigging_type == "muscle_ik":
                self.skeleton_template_name = "MBLab_skeleton_muscle_ik"
                self.groups_filename = character_config["vertexgroup_muscle_file"]

            skeleton_name = character_config["name"]+"_skeleton"
            joints_data_path = os.path.join(self.data_path, "joints", self.joints_filename)
            joints_offset_data_path = os.path.join(self.data_path, "joints", self.joints_offset_filename)
            vgroup_data_path = os.path.join(self.data_path, "vgroups", self.groups_filename)

            self.lib_filepath = file_ops.get_blendlibrary_path()
            self.joints_database = file_ops.load_json_data(joints_data_path, "Joints data")
            self.joints_offset_database = file_ops.load_json_data(joints_offset_data_path, "Joints offset data")

            if self.check_skeleton(obj_body):
                obj_armat = get_object_parent(obj_body)
            else:
                obj_armat = file_ops.import_object_from_lib(
                    self.lib_filepath, self.skeleton_template_name, skeleton_name)

            if obj_armat is not None:
                self.store_z_axis()
                # TODO doesn't look like armature_visibility is used
                # anywhere
                #self.armature_visibility = [x for x in obj_armat.layers]
                self.armature_name = obj_armat.name
                self.align_bones_z_axis()
                obj_body.parent = obj_armat
                self.has_data = True
            self.load_groups(vgroup_data_path)
            self.add_armature_modifier()

    @staticmethod
    def check_skeleton(obj_body):
        obj_parent = get_object_parent(obj_body)
        return obj_parent and obj_parent.type == 'ARMATURE'

    def add_armature_modifier(self):
        if self.has_data:
            obj = self.get_body()
            armat = self.get_armature()
            parameters = {"object": armat}
            algorithms.new_modifier(obj, self.armature_modifier_name, 'ARMATURE', parameters)

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
            algorithms.select_and_change_mode(armat, 'POSE')
            bpy.ops.pose.armature_apply()
            algorithms.select_and_change_mode(obj, 'OBJECT')

    @staticmethod
    def error_msg(path):
        logger.error("Database file not found: %s", file_ops.simple_path(path))

    def store_z_axis(self):
        logger.info("Importing temporary original skeleton to store z axis")
        native_armature = file_ops.import_object_from_lib(
            self.lib_filepath, self.skeleton_template_name, "temp_armature")

        if native_armature:
            self.armature_z_axis = algorithms.get_all_bones_z_axis(native_armature)
            algorithms.remove_object(native_armature)

    def align_bones_z_axis(self):
        target_armature = self.get_armature()
        if target_armature:
            algorithms.select_and_change_mode(target_armature, 'EDIT')
            edit_bones = algorithms.get_edit_bones(target_armature)
            for e_bone in edit_bones:
                if e_bone.name in self.armature_z_axis:
                    z_axis = self.armature_z_axis[e_bone.name]
                    e_bone.align_roll(z_axis)
            algorithms.select_and_change_mode(target_armature, 'POSE')

    def load_groups(self, filepath, use_weights=True, clear_all=True):
        if self.has_data:
            obj = self.get_body()
            g_data = file_ops.load_json_data(filepath, "Vertgroups data")

            if clear_all:
                algorithms.remove_vertgroups_all(obj)
            if g_data:
                group_names = sorted(g_data.keys())
                for group_name in group_names:
                    new_group = algorithms.new_vertgroup(obj, group_name)
                    for vert_data in g_data[group_name]:
                        if use_weights:
                            if isinstance(vert_data, list):
                                new_group.add([vert_data[0]], vert_data[1], 'REPLACE')
                            else:
                                logger.info("Error: wrong format for vert weight")
                        else:
                            if isinstance(vert_data, int):
                                new_group.add([vert_data], 1.0, 'REPLACE')
                            else:
                                logger.info("Error: wrong format for vert group")

                logger.info("Group loaded from %s", file_ops.simple_path(filepath))
            else:
                logger.warning("Vgroup file problem %s", file_ops.simple_path(filepath))

    def get_body(self):
        if self.has_data:
            return file_ops.get_object_by_name(self.body_name)
        return None

    def get_armature(self):
        if self.has_data:
            return file_ops.get_object_by_name(self.armature_name)
        return None

    def __bool__(self):
        armat = self.get_armature()
        body = self.get_body()
        return body and armat

    @staticmethod
    def calculate_joint_location(obj, vertsindex_list):
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
            logger.debug("Fitting armature %s", armat.name)
            armat.data.use_mirror_x = False
            current_active_obj = algorithms.get_active_object()
            algorithms.select_and_change_mode(armat, "EDIT")
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

            algorithms.select_and_change_mode(armat, "OBJECT")
            self.align_bones_z_axis()
            algorithms.update_bendy_bones(armat)
            algorithms.set_active_object(current_active_obj)
