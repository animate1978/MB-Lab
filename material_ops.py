import logging
import bpy



logger = logging.getLogger(__name__)

#TODO Send to material_ops
def set_node_image(mat_node, mat_image):
    if mat_node:
        mat_node.image = mat_image
    else:
        logger.warning("Node assignment failed. Image not found: %s", mat_image)

#
def get_material(material_name):
    for material in bpy.data.materials:
        if material.name == material_name:
            return material
    logger.warning("Material %s not found", material_name)
    return None

#
def get_material_nodes(material):
    if material.node_tree:
        return material.node_tree.nodes

    logger.warning("Material %s has not nodes", material.name)
    return None

#
def get_material_node(material_name, node_name):
    material_node = None
    material = get_material(material_name)
    if material:
        if node_name in material.node_tree.nodes:
            material_node = material.node_tree.nodes[node_name]
    if not material_node:
        logger.warning("Node not found: %s in material %s", node_name, material_name)
    return material_node

#
def get_node_output_value(node, index):
    if index < len(node.outputs):
        if hasattr(node.outputs[index], "default_value"):
            return node.outputs[index].default_value

        logger.warning("Socket [%s] has not default_value attribute", index)
        return None

    logger.warning("Socket [%s] not in range of node %s outputs", index, node.name)
    return None

#
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
