# MB-Lab

# MB-Lab fork website : https://github.com/animate1978/MB-Lab

# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
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

import logging

import bpy


logger = logging.getLogger(__name__)


def get_object_parent(obj):
    if not obj:
        return None
    return getattr(obj, "parent", None)


def get_deforming_armature(obj):
    if obj.type == 'MESH':
        for modf in obj.modifiers:
            if modf.type == 'ARMATURE':
                return modf.object
    return None


def get_active_armature():
    active_obj = bpy.context.view_layer.objects.active
    parent_object = get_object_parent(active_obj)
    if active_obj:
        if active_obj.type == 'ARMATURE':
            return active_obj
        if active_obj.type == 'MESH':
            if parent_object:
                if parent_object.type == 'ARMATURE':
                    return parent_object
            else:
                deforming_armature = get_deforming_armature(active_obj)
                if deforming_armature:
                    return deforming_armature
    return None


def is_ik_armature(armature=None):
    if not armature:
        armature = get_active_armature()
        if armature and armature.type == 'ARMATURE':
            for b in armature.data.bones:
                if 'IK' in b.name:
                    return True
        elif armature and armature.type != 'ARMATURE':
            logger.warning("Cannot get the bones because the obj is not an armature")
            return False
    return False
