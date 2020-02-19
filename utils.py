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

# MB-Lab version check

def check_version(m_vers, min_version=(1, 5, 0)):

    # m_vers can be a list, tuple, IDfloatarray or str
    # so it must be converted in a list.
    if not isinstance(m_vers, str):
        m_vers = list(m_vers)

    mesh_version = str(m_vers)
    mesh_version = mesh_version.replace(' ', '')
    mesh_version = mesh_version.strip("[]()")
    if len(mesh_version) < 5:
        logger.warning("The current humanoid has wrong format for version")
        return False

    mesh_version = (float(mesh_version[0]), float(mesh_version[2]), float(mesh_version[4]))
    return mesh_version > min_version
