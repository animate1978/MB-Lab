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

import logging
import array
import os
import time

import bpy
from . import algorithms


logger = logging.getLogger(__name__)


class MaterialEngine:
    generated_disp_modifier_ID = "mbastlab_displacement"
    generated_disp_texture_name = "mbastlab_displ_texture"
    subdivision_modifier_name = "mbastlab_subdvision"
    parameter_identifiers = ("skin_", "eyes_")

    def __init__(self, obj_name, character_config):

        data_path = algorithms.get_data_path()
        self.obj_name = obj_name

        image_file_names = {
            "displ_data": character_config["texture_displacement"],
            "body_derm": character_config["texture_diffuse"],
            "body_displ": character_config["name"]+"_displ.png",
            "body_spec": character_config["texture_specular"],
            "body_rough": character_config["texture_roughness"],
            "eyes_diffuse": character_config["texture_eyes"],
            "body_bump": character_config["texture_bump"],
            "body_subd": character_config["texture_subdermal"],
        }

        image_file_paths = {}

        for img_id, value in image_file_names.items():
            image_file_paths[img_id] = os.path.join(
                os.path.join(data_path, "textures"),
                value
            )

        self.image_file_paths = image_file_paths
        self.image_file_names = image_file_names
        self.load_data_images()
        self.generate_displacement_image()

    def load_data_images(self):
        for img_path in self.image_file_paths.values():
            algorithms.load_image(img_path)

    def load_texture(self, img_path, shader_target):
        algorithms.load_image(img_path)
        self.image_file_names[shader_target] = os.path.basename(img_path)
        self.update_shaders()

    @property
    def texture_dermal_exist(self):
        return os.path.isfile(self.image_file_paths["body_derm"])

    @property
    def texture_spec_exist(self):
        return os.path.isfile(self.image_file_paths["body_spec"])

    @property
    def texture_rough_exist(self):
        return os.path.isfile(self.image_file_paths["body_rough"])

    @property
    def texture_subd_exist(self):
        return os.path.isfile(self.image_file_paths["body_subd"])

    @property
    def texture_eyes_exist(self):
        return os.path.isfile(self.image_file_paths["eyes_diffuse"])

    @property
    def texture_bump_exist(self):
        return os.path.isfile(self.image_file_paths["body_bump"])

    @property
    def texture_displace_exist(self):
        return os.path.isfile(self.image_file_paths["displ_data"])

    @staticmethod
    def calculate_disp_pixels(blender_image, age_factor, tone_factor, mass_factor):

        img_a = array.array('f', blender_image.pixels[:])
        result_image = array.array('f')

        age_f = age_factor if age_factor > 0 else 0

        tone_f = tone_factor if tone_factor > 0 else 0

        mass_f = (1 - tone_f) * mass_factor if mass_factor > 0 else 0

        for i in range(0, len(img_a), 4):
            # details + age_disp + tone_disp + mass_disp
            add_result = img_a[0] + age_f * (img_a[1] - 0.5) + tone_f * (img_a[2] - 0.5) + mass_f * (img_a[3] - 0.5)
            if add_result > 1.0:
                add_result = 1.0

            for _ in range(3):
                result_image.append(add_result)  # R,G,B
            result_image.append(1.0)  # Alpha is always 1

        return result_image.tolist()

    @staticmethod
    def multiply_images(image1, image2, result_name, blending_factor=0.5):

        if image1 and image2 and algorithms.are_squared_images(image1, image2):
            algorithms.scale_image_to_fit(image1, image2)

            img_1_arr = array.array('f', image1.pixels[:])
            img_2_arr = array.array('f', image2.pixels[:])
            result_array = array.array('f')

            for px1, px2 in zip(img_1_arr, img_2_arr):
                px_result = (px1 * px2 * blending_factor) + (px1 * (1 - blending_factor))
                result_array.append(px_result)

            result_img = algorithms.new_image(result_name, image1.size)
            algorithms.array_to_image(result_array, result_img)

    @staticmethod
    def assign_image_to_node(material_name, node_name, image_name):
        logger.info("Assigning the image %s to node %s", image_name, node_name)
        mat_node = algorithms.get_material_node(material_name, node_name)
        mat_image = algorithms.get_image(image_name)
        if mat_image:
            algorithms.set_node_image(mat_node, mat_image)
        else:
            logger.warning("Node assignment failed. Image not found: %s", image_name)

    def get_material_parameters(self):

        material_parameters = {}

        obj = self.get_object()
        for material in algorithms.get_object_materials(obj):
            if material.node_tree:
                for node in algorithms.get_material_nodes(material):
                    is_parameter = False
                    for param_identifier in self.parameter_identifiers:
                        if param_identifier in node.name:
                            is_parameter = True
                            break
                    if is_parameter:
                        node_output_val = algorithms.get_node_output_value(node, 0)
                        material_parameters[node.name] = node_output_val
        return material_parameters

    def update_shaders(self, material_parameters=[], update_textures_nodes=True):

        obj = self.get_object()
        for material in algorithms.get_object_materials(obj):
            nodes = algorithms.get_material_nodes(material)
            if not nodes:
                continue

            for node in nodes:
                if node.name in material_parameters:
                    value = material_parameters[node.name]
                    algorithms.set_node_output_value(node, 0, value)
                elif update_textures_nodes:
                    if "_skn_diffuse" in node.name:
                        self.assign_image_to_node(material.name, node.name, self.image_file_names["body_derm"])
                    if "_skn_specular" in node.name:
                        self.assign_image_to_node(material.name, node.name, self.image_file_names["body_spec"])
                    if "_skn_roughness" in node.name:
                        self.assign_image_to_node(material.name, node.name,
                                                  self.image_file_names["body_rough"])
                    if "_skn_subdermal" in node.name:
                        self.assign_image_to_node(material.name, node.name, self.image_file_names["body_subd"])
                    if "_eys_diffuse" in node.name:
                        self.assign_image_to_node(material.name, node.name,
                                                  self.image_file_names["eyes_diffuse"])
                    if "_eylsh_diffuse" in node.name:
                        self.assign_image_to_node(material.name, node.name, self.image_file_names["body_derm"])
                    if "_tth_diffuse" in node.name:
                        self.assign_image_to_node(material.name, node.name, self.image_file_names["body_derm"])
                    if "_skn_bump" in node.name:
                        self.assign_image_to_node(material.name, node.name, self.image_file_names["body_bump"])
                    if "_skn_disp" in node.name:
                        self.assign_image_to_node(material.name, node.name,
                                                  self.image_file_names["body_displ"])

    def rename_skin_shaders(self, prefix):
        obj = self.get_object()
        for material in algorithms.get_object_materials(obj):
            if prefix != "":
                material.name = prefix + "_" + material.name
            else:
                material.name = material.name+str(time.time())

    def get_object(self):
        return algorithms.get_object_by_name(self.obj_name)

    def generate_displacement_image(self):
        disp_data_image_name = self.image_file_names["displ_data"]
        if disp_data_image_name != "":
            disp_data_image = algorithms.get_image(disp_data_image_name)
            if disp_data_image:
                disp_size = disp_data_image.size
                logger.info(
                    "Creating the displacement image from data image %s with size %sx%s",
                    disp_data_image.name, disp_size[0], disp_size[1])
                algorithms.new_image(self.image_file_names["body_displ"], disp_size)
            else:
                logger.warning(
                    "Cannot create the displacement modifier: data image not found: %s",
                    algorithms.simple_path(self.image_file_paths["displ_data"]))

    def calculate_displacement_texture(self, age_factor, tone_factor, mass_factor):
        time1 = time.time()
        disp_data_image_name = self.image_file_names["displ_data"]

        if disp_data_image_name != "":
            disp_data_image = algorithms.get_image(disp_data_image_name)

            if disp_data_image:

                if self.image_file_names["body_displ"] in bpy.data.images:
                    disp_img = bpy.data.images[self.image_file_names["body_displ"]]
                else:
                    logger.warning("Displace image not found: %s", self.image_file_names["body_displ"])
                    return

                if self.generated_disp_modifier_ID in bpy.data.textures:
                    disp_tex = bpy.data.textures[self.generated_disp_modifier_ID]
                else:
                    logger.warning("Displace texture not found: %s", self.generated_disp_modifier_ID)
                    return

                if algorithms.are_squared_images(disp_data_image, disp_img):
                    algorithms.scale_image_to_fit(disp_data_image, disp_img)
                    disp_img.pixels = self.calculate_disp_pixels(disp_data_image, age_factor, tone_factor, mass_factor)
                    disp_tex.image = disp_img
                    logger.info("Displacement calculated in %s seconds", time.time()-time1)
            else:
                logger.error("Displace data image not found: %s",
                             algorithms.simple_path(self.image_file_paths["displ_data"]))

    def save_texture(self, filepath, shader_target):
        img_name = self.image_file_names[shader_target]
        logger.info("Saving image %s in %s", img_name, algorithms.simple_path(filepath))
        algorithms.save_image(img_name, filepath)
        algorithms.load_image(filepath)  # Load the just saved image to replace the current one
        self.image_file_names[shader_target] = os.path.basename(filepath)
        self.update_shaders()
