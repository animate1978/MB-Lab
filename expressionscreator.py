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
#
# ManuelbastioniLAB - Copyright (C) 2015-2018 Manuel Bastioni
# Teto for this part.

import logging
import json
import os
import bpy
import numpy
from . import algorithms
from . import file_ops
from . import utils

logger = logging.getLogger(__name__)

class ExpressionsCreator():

    def __init__(self):

        self.standard_expressions_list = ["abdomExpansion_min", "abdomExpansion_max",
            "browOutVertL_min", "browOutVertL_max", "browOutVertR_min",
            "browOutVertR_max", "browsMidVert_min", "browsMidVert_max",
            "browSqueezeL_min", "browSqueezeL_max", "browSqueezeR_min",
            "browSqueezeR_max", "cheekSneerL_max", "cheekSneerR_max",
            "chestExpansion_min", "chestExpansion_max", "deglutition_min",
            "deglutition_max", "eyeClosedL_min", "eyeClosedL_max",
            "eyeClosedPressureL_min", "eyeClosedPressureL_max",
            "eyeClosedPressureR_min", "eyeClosedPressureR_max",
            "eyeClosedR_min", "eyeClosedR_max", "eyesHoriz_min",
            "eyesHoriz_max", "eyeSquintL_min", "eyeSquintL_max",
            "eyeSquintR_min", "eyeSquintR_max", "eyesSmile_max",
            "eyesVert_min", "eyesVert_max", "jawHoriz_min", "jawHoriz_max",
            "jawOut_min", "jawOut_max", "mouthBite_min", "mouthBite_max",
            "mouthChew_min", "mouthChew_max", "mouthClosed_min",
            "mouthClosed_max", "mouthHoriz_min", "mouthHoriz_max",
            "mouthInflated_min", "mouthInflated_max", "mouthLowerOut_min",
            "mouthLowerOut_max", "mouthOpen_min", "mouthOpen_max",
            "mouthOpenAggr_min", "mouthOpenAggr_max", "mouthOpenHalf_max",
            "mouthOpenLarge_min", "mouthOpenLarge_max", "mouthOpenO_min",
            "mouthOpenO_max", "mouthOpenTeethClosed_min",
            "mouthOpenTeethClosed_max", "mouthSmile_min", "mouthSmile_max",
            "mouthSmileL_max", "mouthSmileOpen_min", "mouthSmileOpen_max",
            "mouthSmileOpen2_min", "mouthSmileOpen2_max", "mouthSmileR_max",
            "nostrilsExpansion_min", "nostrilsExpansion_max",
            "pupilsDilatation_min", "pupilsDilatation_max", "tongueHoriz_min",
            "tongueHoriz_max", "tongueOut_min", "tongueOut_max",
            "tongueOutPressure_max", "tongueTipUp_max", "tongueVert_min",
            "tongueVert_max"]

        self.standard_expressions = [("AA", "abdomExpansion_min", "abdomen"),
            ("AB", "abdomExpansion_max", "abdomen"),
            ("AC", "browOutVertL_min", "brow"),
            ("AD", "browOutVertL_max", "brow"),
            ("AE", "browOutVertR_min", "brow"),
            ("AF", "browOutVertR_max", "brow"),
            ("AG", "browsMidVert_min", "brow"),
            ("AH", "browsMidVert_max", "brow"),
            ("AI", "browSqueezeL_min", "brow"),
            ("AJ", "browSqueezeL_max", "brow"),
            ("AK", "browSqueezeR_min", "brow"),
            ("AL", "browSqueezeR_max", "brow"),
            ("AM", "cheekSneerL_max", "cheek"),
            ("AN", "cheekSneerR_max", "cheek"),
            ("AO", "chestExpansion_min", "chest"),
            ("AP", "chestExpansion_max", "chest"),
            ("AQ", "deglutition_min", "deglutition"),
            ("AR", "deglutition_max", "deglutition"),
            ("AS", "eyeClosedL_min", "eye"),
            ("AT", "eyeClosedL_max", "eye"),
            ("AU", "eyeClosedPressureL_min", "eye"),
            ("AV", "eyeClosedPressureL_max", "eye"),
            ("AW", "eyeClosedPressureR_min", "eye"),
            ("AX", "eyeClosedPressureR_max", "eye"),
            ("AY", "eyeClosedR_min", "eye"),
            ("AY", "eyeClosedR_max", "eye"),
            ("AZ", "eyesHoriz_min", "eye"),
            ("BA", "eyesHoriz_max", "eye"),
            ("BB", "eyeSquintL_min", "eye"),
            ("BC", "eyeSquintL_max", "eye"),
            ("BD", "eyeSquintR_min", "eye"),
            ("BE", "eyeSquintR_max", "eye"),
            ("BF", "eyesSmile_max", "eye"),
            ("BG", "eyesVert_min", "eye"),
            ("BH", "eyesVert_max", "eye"),
            ("BI", "jawHoriz_min", "jaw"),
            ("BJ", "jawHoriz_max", "jaw"),
            ("BK", "jawOut_min", "jaw"),
            ("BL", "jawOut_max", "jaw"),
            ("BM", "mouthBite_min", "mouth"),
            ("BN", "mouthBite_max", "mouth"),
            ("BO", "mouthChew_min", "mouth"),
            ("BP", "mouthChew_max", "mouth"),
            ("BQ", "mouthClosed_min", "mouth"),
            ("BR", "mouthClosed_max", "mouth"),
            ("BS", "mouthHoriz_min", "mouth"),
            ("BT", "mouthHoriz_max", "mouth"),
            ("BU", "mouthInflated_min", "mouth"),
            ("BV", "mouthInflated_max", "mouth"),
            ("BW", "mouthLowerOut_min", "mouth"),
            ("BX", "mouthLowerOut_max", "mouth"),
            ("BY", "mouthOpen_min", "mouth"),
            ("BZ", "mouthOpen_max", "mouth"),
            ("CA", "mouthOpenAggr_min", "mouth"),
            ("CB", "mouthOpenAggr_max", "mouth"),
            ("CC", "mouthOpenHalf_max", "mouth"),
            ("CD", "mouthOpenLarge_min", "mouth"),
            ("CE", "mouthOpenLarge_max", "mouth"),
            ("CF", "mouthOpenO_min", "mouth"),
            ("CG", "mouthOpenO_max", "mouth"),
            ("CH", "mouthOpenTeethClosed_min", "mouth"),
            ("CI", "mouthOpenTeethClosed_max", "mouth"),
            ("CJ", "mouthSmile_min", "mouth"),
            ("CK", "mouthSmile_max", "mouth"),
            ("CL", "mouthSmileL_max", "mouth"),
            ("CM", "mouthSmileOpen_min", "mouth"),
            ("CN", "mouthSmileOpen_max", "mouth"),
            ("CO", "mouthSmileOpen2_min", "mouth"),
            ("CP", "mouthSmileOpen2_max", "mouth"),
            ("CQ", "mouthSmileR_max", "mouth"),
            ("CR", "nostrilsExpansion_min", "nostrils"),
            ("CS", "nostrilsExpansion_max", "nostrils"),
            ("CT", "pupilsDilatation_min", "pupils"),
            ("CU", "pupilsDilatation_max", "pupils"),
            ("CV", "tongueHoriz_min", "tongue"),
            ("CW", "tongueHoriz_max", "tongue"),
            ("CX", "tongueOut_min", "tongue"),
            ("CY", "tongueOut_max", "tongue"),
            ("CZ", "tongueOutPressure_max", "tongue"),
            ("DA", "tongueTipUp_max", "tongue"),
            ("DB", "tongueVert_min", "tongue"),
            ("DC", "tongueVert_max", "tongue"),
            ("OT", "other", "other")]

        # For enumProperty
        self.body_parts_expr = [
            ("AB", "abdom", ""),
            ("BR", "brow", ""),
            ("BS", "brows", ""),
            ("CH", "cheek", ""),
            ("CE", "chest", ""),
            ("DE", "deglutition", ""),
            ("EY", "eye", ""),
            ("ES", "eyes", ""),
            ("JA", "jaw", ""),
            ("MO", "mouth", ""),
            ("NO", "nostrils", ""),
            ("PU", "pupils", ""),
            ("TO", "tongue", ""),
            ("OT", "other", "")]

        # Simple list
        self.body_parts_expr_list = ["abdom", "brow", "brows",
            "cheek", "chest", "deglutition", "eye", "eyes",
            "jaw", "mouth", "nostrils", "pupils", "tongue"]


        self.min_max_expr = [("MI", "min", "min = 0"),
           ("MA", "max", "max = 1")]

        self.expression_ID_list = [("HU", "Humans", "Standard in MB-Lab"),
           ("AN", "Anime", "Standard in MB-Lab"),
           ("OT", "OTHER", "For another model")]

        self.forbidden_char_list = '-_²&=¨^$£%µ,?;!§+*/'

        self.expression_name = ["", "", 0]
        #the number is for autosaves.

        self.editor_expressions_items = []
        # To have quickly items for enum_property,
        # and create them only when model is changed.
        # Used only AFTER finalization of the model.

        self.expressions_sub_categories = []
        # The sub_categories for expressions (jaw, brows, ...)

        self.expressions_modifiers = {}
        # To have quickly modifiers for enum_property,
        # and create them only when model is changed.
        # Used only BEFORE finalization of the model,
        # in the Combined Expression Editor.

        self.humanoid = None
        # Instance of class Humanoid

    #--------------Play with variables
    def set_lab_version(self, lab_version):
        self.lab_vers = list(lab_version)

    def get_standard_expressions_list(self):
        return self.standard_expressions_list

    def get_standard_base_expr(self, key=None):
        if key == None:
            return self.standard_expressions
        value = None
        for index in range(len(self.standard_expressions)):
            if key in self.standard_expressions[index]:
                value = self.standard_expressions[index]
                return value[1]
        return ""

    def get_body_parts_expr(self, key=None):
        if key == None:
            return self.body_parts_expr
        value = None
        for index in range(len(self.body_parts_expr)):
            if key in self.body_parts_expr[index]:
                value = self.body_parts_expr[index]
                return value[1]
        return ""

    def get_min_max_expr(self, key=None):
        if key == None:
            return self.min_max_expr
        value = None
        for index in range(len(self.min_max_expr)):
            if key in self.min_max_expr[index]:
                value = self.min_max_expr[index]
                return value[1]
        return ""

    def set_expression_name(self, name):
        self.expression_name[0] = name

    def get_expression_name(self):
        return self.expression_name[0]

    def set_expression_ID(self, id):
        self.expression_name[1] = "Expressions_ID" + id + "_max"

    def get_expression_ID(self):
        return self.expression_name[1]

    def get_expression_ID_list(self):
        return self.expression_ID_list

    def get_next_number(self):
        self.expression_name[2] += 1
        return str(self.expression_name[2]).zfill(3)

    #Methods about EnumProperty for combined expressions creation
    #-------------BEFORE finalization of the character
    def reset_expressions_items(self):
        self.editor_expressions_items.clear()
        self.expressions_modifiers.clear()
        self.expressions_sub_categories.clear()

    def set_expressions_modifiers(self, huma):
        self.humanoid = huma
        if len(self.expressions_modifiers) > 0:
            return self.expressions_modifiers
        category = self.humanoid.get_category("Expressions")
        if not category:
            logger.error("Expressions is aren't found in humanoid")
            return
        self.expressions_modifiers = category.get_modifier_tiny_name(self.body_parts_expr_list)

    def get_expressions_modifiers(self):
        return self.expressions_modifiers

    # To know the real name from a key in an enumProp
    def get_modifier_item(self, key):
        return algorithms.get_enum_property_item(key, self.get_expressions_sub_categories())

    # Give items in sub categories,
    # but knows difference between eyes and eyeS in name
    def get_items_in_sub(self, key):
        sub = algorithms.get_enum_property_item(key, self.get_expressions_sub_categories())
        cat = self.humanoid.get_category("Expressions")
        tiny = cat.get_modifier_tiny_name(sub_categories=[sub], exclude_in_others=self.body_parts_expr_list)
        items = tiny[sub]
        return_items = []
        for item in items:
            return_items.append(item[2])
        return return_items

    # Return an enumProperty with all sub-categories.
    def get_expressions_sub_categories(self):
        if len(self.expressions_sub_categories) > 0:
            return self.expressions_sub_categories
        if len(self.expressions_modifiers) < 1 and self.humanoid != None:
            self.set_expressions_modifiers(self.humanoid)
        sorted_list = sorted(list(self.expressions_modifiers.keys()))
        self.expressions_sub_categories = algorithms.create_enum_property_items(sorted_list, tip_length=100)
        return self.expressions_sub_categories

    def is_comb_expression_exists(self, root_model, name):
        if len(root_model) < 1 or len(name) < 1:
            return False
        try:
            path = os.path.join(file_ops.get_data_path(), "expressions_comb", root_model+"_expressions")
            for database_file in os.listdir(path):
                the_item, extension = os.path.splitext(database_file)
                if the_item == name:
                    return True
        except:
            return False
        return False

    #--------------EnumProperty for expressions in UI
    #--------------AFTER finalization of the character

    def set_expressions_items(self, sorted_names):
        if len(self.editor_expressions_items) > 0:
            return
        key = 0
        for s_n in sorted_names:
            self.editor_expressions_items.append((str(key).zfill(3), s_n, "" ))
            key += 1

    def get_expressions_items(self):
        return self.editor_expressions_items

    def get_expressions_item(self, key):
        return algorithms.get_enum_property_item(key, self.editor_expressions_items)

    #--------------Loading data
    def get_all_expression_files(self, data_path, data_type_path, body_type):
        #Get all files in morphs directory, with standard ones.
        #Used when the engine loads expressions librairies.
        dir = os.path.join(data_path, data_type_path)
        found_files = []
        body_type_split = body_type.split('_')[:2]
        list = os.listdir(dir)
        for item in list:
            if item == body_type:
                found_files += [os.path.join(dir, item)]
        for item in list:
            if item.split('_')[:2] == body_type_split and item != body_type:
                found_files += [os.path.join(dir, item)]
        return found_files

    #--------------Saving all changed base expression in a filedef
    def save_face_expression(self, filepath):
        # Save all expression morphs as a new face expression
        # in its dedicated file.
        # If file already exists, it's replaced.
        logger.info("Exporting character to {0}".format(file_ops.simple_path(filepath)))
        obj = self.humanoid.get_object()
        char_data = {"manuellab_vers": self.lab_vers, "structural": dict(), "metaproperties": dict(), "materialproperties": dict()}

        if obj:
            for prop in self.humanoid.character_data.keys():
                if self.humanoid.character_data[prop] != 0.5 and prop.startswith("Expressions_"):
                    char_data["structural"][prop] = round(self.humanoid.character_data[prop], 4)
            with open(filepath, "w") as j_file:
                json.dump(char_data, j_file, indent=2)
            j_file.close()

    # data_source can be a filepath but also the data themselves.
    def load_face_expression(self, data_source, reset_unassigned=True):

        if self.humanoid == None:
            return

        obj = self.humanoid.get_object()
        log_msg_type = "Expression data"

        if isinstance(data_source, str):
            log_msg_type = file_ops.simple_path(data_source)
            charac_data = file_ops.load_json_data(data_source, "Expression data")
        else:
            charac_data = data_source

        logger.info("Loading expression from {0}".format(log_msg_type))

        if "manuellab_vers" in charac_data:
            if not utils.check_version(charac_data["manuellab_vers"]):
                logger.warning("{0} created with vers. {1}. Current vers is {2}".format(log_msg_type, charac_data["manuellab_vers"], self.lab_vers))
        else:
            logger.info("No lab version specified in {0}".format(log_msg_type))

        if "structural" in charac_data:
            char_data = charac_data["structural"]
        else:
            logger.warning("No structural data in  {0}".format(log_msg_type))
            char_data = {}

        # data are loaded, now update the character.
        if char_data is not None:
            for name in self.humanoid.character_data.keys():
                if name in char_data:
                    self.humanoid.character_data[name] = char_data[name]
                else:
                    if reset_unassigned and name.startswith("Expressions_"):
                        self.humanoid.character_data[name] = 0.5
            # Now updating.
            self.humanoid.update_character(mode="update_all")