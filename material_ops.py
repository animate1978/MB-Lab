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
import bpy



logger = logging.getLogger(__name__)

# ------------------------------------------------------------------------
#    Material Functions
# ------------------------------------------------------------------------

def set_node_image(mat_node, mat_image):
    if mat_node:
        mat_node.image = mat_image
    else:
        logger.warning("Node assignment failed. Image not found: %s", mat_image)


def get_material(material_name):
    for material in bpy.data.materials:
        if material.name == material_name:
            return material
    logger.warning("Material %s not found", material_name)
    return None


def get_material_nodes(material):
    if material.node_tree:
        return material.node_tree.nodes

    logger.warning("Material %s has not nodes", material.name)
    return None


def get_material_node(material_name, node_name):
    material_node = None
    material = get_material(material_name)
    if material:
        if node_name in material.node_tree.nodes:
            material_node = material.node_tree.nodes[node_name]
    if not material_node:
        logger.warning("Node not found: %s in material %s", node_name, material_name)
    return material_node


def get_node_output_value(node, index):
    if index < len(node.outputs):
        if hasattr(node.outputs[index], "default_value"):
            return node.outputs[index].default_value

        logger.warning("Socket [%s] has not default_value attribute", index)
        return None

    logger.warning("Socket [%s] not in range of node %s outputs", index, node.name)
    return None


def set_node_output_value(node, index, value):
    if index < len(node.outputs):
        if hasattr(node.outputs[index], "default_value"):
            node.outputs[index].default_value = value
        else:
            logger.warning("Socket [%s] has not default_value attribute", index)
    else:
        logger.warning("Socket[%s] not in range of node %s outputs", index, node.name)

def get_object_materials(obj):
    if obj.data.materials:
        return obj.data.materials
    return []
