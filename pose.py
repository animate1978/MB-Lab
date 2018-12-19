# ManuelbastioniLAB - Copyright (C) 2015-2018 Manuel Bastioni
# Official site: www.manuelbastioni.com
# MB-Lab fork website : https://github.com/animate1978/MB-Lab
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
import bpy
import os
import json
from bpy_extras.io_utils import ExportHelper, ImportHelper
from bpy.app.handlers import persistent
from . import humanoid, animationengine, proxyengine, algorithms, settings

def restpose_update(self, context):
    # global mblab_humanoid
    armature = self.mblab_humanoid.get_armature()
    filepath = os.path.join(
        settings.mblab_humanoid.restposes_path,
        "".join([armature.rest_pose, ".json"]))
    settings.mblab_retarget.load_pose(filepath, armature)


def malepose_update(self, context):
    # global mblab_retarget
    armature = algorithms.get_active_armature()
    filepath = os.path.join(
        settings.mblab_retarget.maleposes_path,
        "".join([armature.male_pose, ".json"]))
    settings.mblab_retarget.load_pose(filepath, use_retarget=True)


def femalepose_update(self, context):
    # global mblab_retarget
    armature = algorithms.get_active_armature()
    filepath = os.path.join(
        settings.mblab_retarget.femaleposes_path,
        "".join([armature.female_pose, ".json"]))
    settings.mblab_retarget.load_pose(filepath, use_retarget=True)


class SaveRestPose(bpy.types.Operator, ExportHelper):
    """Export pose"""
    bl_idname = "mbast.restpose_save"
    bl_label = "Save custom rest pose"
    filename_ext = ".json"
    filter_glob = bpy.props.StringProperty(
        default="*.json",
        options={'HIDDEN'},
    )
    bl_context = 'objectmode'

    def execute(self, context):
        # global mblab_humanoid
        armature = settings.mblab_humanoid.get_armature()
        settings.mblab_retarget.save_pose(armature, self.filepath)
        return {'FINISHED'}


class LoadRestPose(bpy.types.Operator, ImportHelper):
    """
    Import parameters for the character
    """
    bl_idname = "mbast.restpose_load"
    bl_label = "Load custom rest pose"
    filename_ext = ".json"
    filter_glob = bpy.props.StringProperty(
        default="*.json",
        options={'HIDDEN'},
    )
    bl_context = 'objectmode'

    def execute(self, context):
        # global mblab_humanoid, mblab_retarget
        armature = settings.mblab_humanoid.get_armature()
        settings.mblab_retarget.load_pose(self.filepath, armature, use_retarget=False)
        return {'FINISHED'}


class SavePose(bpy.types.Operator, ExportHelper):
    """Export pose"""
    bl_idname = "mbast.pose_save"
    bl_label = "Save pose"
    filename_ext = ".json"
    filter_glob = bpy.props.StringProperty(
        default="*.json",
        options={'HIDDEN'},
    )
    bl_context = 'objectmode'

    def execute(self, context):
        # global mblab_humanoid
        armature = algorithms.get_active_armature()
        settings.mblab_retarget.save_pose(armature, self.filepath)
        return {'FINISHED'}


class LoadPose(bpy.types.Operator, ImportHelper):
    """
    Import parameters for the character
    """
    bl_idname = "mbast.pose_load"
    bl_label = "Load pose"
    filename_ext = ".json"
    filter_glob = bpy.props.StringProperty(
        default="*.json",
        options={'HIDDEN'},
    )
    bl_context = 'objectmode'

    def execute(self, context):
        # global mblab_retarget
        settings.mblab_retarget.load_pose(self.filepath, use_retarget=True)
        return {'FINISHED'}


class ResetPose(bpy.types.Operator):
    """
    Import parameters for the character
    """
    bl_idname = "mbast.pose_reset"
    bl_label = "Reset pose"
    bl_context = 'objectmode'
    bl_description = 'Reset the angles of the armature bones'
    bl_options = {'REGISTER', 'INTERNAL', 'UNDO'}

    def execute(self, context):
        # global mblab_retarget
        settings.mblab_retarget.reset_pose()
        return {'FINISHED'}


class LoadBvh(bpy.types.Operator, ImportHelper):
    """
    Import parameters for the character
    """
    bl_idname = "mbast.load_animation"
    bl_label = "Load animation (bvh)"
    filename_ext = ".bvh"
    bl_description = 'Import the animation from a bvh motion capture file'
    filter_glob = bpy.props.StringProperty(
        default="*.bvh",
        options={'HIDDEN'},
    )
    bl_context = 'objectmode'

    def execute(self, context):
        # global mblab_retarget
        settings.mblab_retarget.load_animation(self.filepath)
        return {'FINISHED'}