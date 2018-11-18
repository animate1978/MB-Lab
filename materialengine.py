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

import math
import array
import bpy
import os
import time
import json
from . import algorithms

class MaterialEngine:

    def __init__(self, obj_name, character_config):

        data_path = algorithms.get_data_path()
        self.obj_name = obj_name
        self.displacement_data_file = character_config["texture_displacement"]
        self.image_diffuse_file = character_config["texture_diffuse"]
        self.image_displacement_file = character_config["name"]+"_displ.png"
        

        self.texture_data_path = os.path.join(data_path,"textures")
        self.texture_dermal_exist = False
        self.texture_displace_exist = False


        self.generated_disp_modifier_ID = "mbastlab_displacement"
        self.generated_disp_texture_name = "mbastlab_displ_texture"
        self.subdivision_modifier_name = "mbastlab_subdvision"

        self.image_file_names = {}
        self.image_file_names["body_displ"] = self.image_displacement_file
        self.image_file_names["displ_data"] = self.displacement_data_file
        self.image_file_names["body_derm"] = self.image_diffuse_file

        self.image_file_paths = {}
        for img_id in self.image_file_names.keys():
            self.image_file_paths[img_id] = os.path.join(
                self.texture_data_path,
                self.image_file_names[img_id])

        self.parameter_identifiers = ["skin_", "eyes_"]

        if os.path.isfile(self.image_file_paths["body_derm"]):
            self.texture_dermal_exist = True

        if os.path.isfile(self.image_file_paths["displ_data"]):
            self.texture_displace_exist = True

        self.load_data_images()
        self.generate_displacement_image()



    def load_data_images(self):
        for img_path in self.image_file_paths.values():
            algorithms.load_image(img_path)

    def load_texture(self, img_path, shader_target):
        algorithms.load_image(img_path)
        self.image_file_names[shader_target] = os.path.basename(img_path)
        self.update_shaders()

    def calculate_disp_pixels(self, blender_image, age_factor,tone_factor,mass_factor):

        source_data_image = algorithms.image_to_array(blender_image)
        result_image= array.array('f')

        if age_factor > 0:
            age_f = age_factor
        else:
            age_f = 0

        if tone_factor > 0:
            tone_f = tone_factor
        else:
            tone_f = 0

        if mass_factor > 0:
            mass_f = (1-tone_f)*mass_factor
        else:
            mass_f = 0

        for i in range(0,len(source_data_image),4):
            r = source_data_image[i]
            g = source_data_image[i+1]
            b = source_data_image[i+2]
            a = source_data_image[i+3]

            details = r
            age_disp = age_f*(g-0.5)
            tone_disp = tone_f*(b-0.5)
            mass_disp = mass_f*(a-0.5)

            add_result = details+age_disp+tone_disp+mass_disp
            if add_result > 1.0:
                add_result = 1.0

            for i2 in range(3):
                result_image.append(add_result) #R,G,B
            result_image.append(1.0)#Alpha is always 1

        return result_image.tolist()

    def multiply_images(self, image1, image2, result_name, blending_factor = 0.5, ):

        if image1 and image2:
            if algorithms.are_squared_images(image1, image2):
                algorithms.scale_image_to_fit(image1, image2)
                image1 = algorithms.image_to_array(image1)
                image2 = algorithms.image_to_array(image2)
                result_array= array.array('f')

                for i in range(len(image1)):
                    px1 = image1[i]
                    px2 = image2[i]
                    px_result = (px1 * px2 * blending_factor) + (px1 * (1 - blending_factor))
                    result_array.append(px_result)

                result_img = algorithms.new_image(result_name, size1)
                algorithms.array_to_image(result_array, result_img)


    def assign_image_to_node(self, material_name, node_name, image_name):
        algorithms.print_log_report("INFO","Assigning the image {0} to node {1}".format(image_name,node_name))
        mat_node = algorithms.get_material_node(material_name, node_name)
        mat_image = algorithms.get_image(image_name)
        if mat_image:
            algorithms.set_node_image(mat_node,mat_image)
        else:
            algorithms.print_log_report("WARNING","Node assignment failed. Image not found: {0}".format(image_name))


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
                    if is_parameter == True:
                        node_output_val = algorithms.get_node_output_value(node, 0)
                        material_parameters[node.name] = node_output_val
        return material_parameters

    def update_shaders(self, material_parameters = [], update_textures_nodes = True):

        obj = self.get_object()
        for material in algorithms.get_object_materials(obj):
            material_name = material.name
            nodes = algorithms.get_material_nodes(material)
            if nodes:
                for node in nodes:                    
                    if node.name in  material_parameters:
                        value = material_parameters[node.name]
                        algorithms.set_node_output_value(node, 0, value)
                    else:
                        if update_textures_nodes == True:

                            if "_skn_diffuse" in node.name:
                                self.assign_image_to_node(material.name, node.name, self.image_file_names["body_derm"])
                            if "_eys_diffuse" in node.name:
                                self.assign_image_to_node(material.name, node.name, self.image_file_names["body_derm"])
                            if "_eylsh_diffuse" in node.name:
                                self.assign_image_to_node(material.name, node.name, self.image_file_names["body_derm"])
                            if "_tth_diffuse" in node.name:
                                self.assign_image_to_node(material.name, node.name, self.image_file_names["body_derm"])
                            if "_skn_disp" in node.name:
                                self.assign_image_to_node(material.name, node.name, self.image_file_names["body_displ"])


    def rename_skin_shaders(self, prefix):
        obj = self.get_object()
        for material in algorithms.get_object_materials(obj):
            if prefix != "":
                material.name = prefix +"_"+ material.name
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
                algorithms.print_log_report("INFO","Creating the displacement image from data image {0} with size {1}x{2}".format(disp_data_image.name, disp_size[0], disp_size[1]))
                disp_img = algorithms.new_image(self.image_file_names["body_displ"], disp_size)
            else:
                algorithms.print_log_report("WARNING","Cannot create the displacement modifier: data image not found: {0}".format(algorithms.simple_path(self.image_file_paths["displ_data"])))


    def calculate_displacement_texture(self,age_factor,tone_factor,mass_factor):
        time1 = time.time()        
        disp_data_image_name = self.image_file_names["displ_data"]
        
        if disp_data_image_name != "":            
            disp_data_image = algorithms.get_image(disp_data_image_name)
            
            if disp_data_image:

                if self.image_file_names["body_displ"] in bpy.data.images:
                    disp_img = bpy.data.images[self.image_file_names["body_displ"]]
                else:
                    algorithms.print_log_report("WARNING","Displace image not found: {0}".format(self.image_file_names["body_displ"]))
                    return

                if self.generated_disp_modifier_ID in bpy.data.textures:
                    disp_tex  = bpy.data.textures[self.generated_disp_modifier_ID]
                else:
                    algorithms.print_log_report("WARNING","Displace texture not found: {0}".format(self.generated_disp_modifier))
                    return            
            
                if algorithms.are_squared_images(disp_data_image, disp_img):
                    algorithms.scale_image_to_fit(disp_data_image, disp_img)
                    disp_img.pixels =  self.calculate_disp_pixels(disp_data_image,age_factor,tone_factor,mass_factor)
                    disp_tex.image = disp_img
                    algorithms.print_log_report("INFO","Displacement calculated in {0} seconds".format(time.time()-time1))
            else:
                algorithms.print_log_report("ERROR","Displace data image not found: {0}".format(algorithms.simple_path(self.image_file_paths["displ_data"])))


    def save_texture(self, filepath, shader_target):
        img_name = self.image_file_names[shader_target]
        algorithms.print_log_report("INFO","Saving image {0} in {1}".format(img_name,algorithms.simple_path(filepath)))
        algorithms.save_image(img_name, filepath)
        algorithms.load_image(filepath) #Load the just saved image to replace the current one
        self.image_file_names[shader_target] = os.path.basename(filepath)
        self.update_shaders()





