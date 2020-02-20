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

from . import algorithms, utils, file_ops

logger = logging.getLogger(__name__)

class ExpressionEngineShapeK:

    def __init__(self):
        self.has_data = False
        self.data_path = file_ops.get_data_path()
        self.human_expression_path = os.path.join(
            self.data_path,
            "expressions_comb",
            "human_expressions")

        self.anime_expression_path = os.path.join(
            self.data_path,
            "expressions_comb",
            "anime_expressions")

        self.expressions_labels = set()
        #Teto
        #self.human_expressions_data = self.load_expression_database(self.human_expression_path)
        #self.anime_expressions_data = self.load_expression_database(self.anime_expression_path)
        self.model_expressions_data = {}
        self.model_expressions_data['HUMANS'] = self.load_expression_database(self.human_expression_path)
        self.model_expressions_data['ANIME'] = self.load_expression_database(self.anime_expression_path)
        self.model_expressions_data['NONE'] = {}
        #End Teto
        self.expressions_data = {}
        self.model_type = "NONE"
        self.has_data = True

    def identify_model_type(self):
        #self.model_type = "NONE"
        obj = algorithms.get_active_body()
        if obj:
            current_shapekes_names = algorithms.get_shapekeys_names(obj)
            if current_shapekes_names:
                #Teto
                """if "Expressions_IDHumans_max" in current_shapekes_names:
                    self.model_type = "HUMAN"
                    return
                if "Expressions_IDAnime_max" in current_shapekes_names:
                    self.model_type = "ANIME"
                    return"""
                for id in current_shapekes_names:
                    if id.startswith('Expressions_ID') and id.endswith('_max'):
                        length = len(id)-4
                        self.model_type = id[14:length].upper()
                        return
        self.model_type = "NONE"
        #End Teto

    @staticmethod
    def load_expression(filepath):

        charac_data = file_ops.load_json_data(filepath, "Character data")
        expressions_id = file_ops.simple_path(filepath)
        if "manuellab_vers" in charac_data:
            if not utils.check_version(charac_data["manuellab_vers"]):
                logger.info("%s created with vers. %s.",
                            expressions_id, charac_data["manuellab_vers"])
        else:
            logger.info("No lab version specified in %s", expressions_id)

        if "structural" in charac_data:
            char_data = charac_data["structural"]
        else:
            logger.warning("No structural data in  %s", expressions_id)
            char_data = None

        return char_data

    def load_expression_database(self, dirpath):
        expressions_data = {}
        if file_ops.exists_database(dirpath):
            for expression_filename in os.listdir(dirpath):
                expression_filepath = os.path.join(dirpath, expression_filename)
                e_item, extension = os.path.splitext(expression_filename)
                if "json" in extension:
                    self.expressions_labels.add(e_item)
                    expressions_data[e_item] = self.load_expression(expression_filepath)
        return expressions_data
    
    #Teto
    
    #Will be useful with new models.
    def add_expression_model_type(self, name="", dirpath=""):
        ed = self.load_expression_database(self, dirpath)
        if len(ed) < 1 or len(name) < 1:
            return
        self.model_expressions_data[name] = ed
        self.model_type = name #Useless ?
    
    def get_loaded_expression_database(self, name):
        if name in self.model_expressions_data:
            return self.model_expressions_data[name]
        return {}
        
    #End Teto

    def sync_expression_to_gui(self):
        # Process all expressions: reset all them and then update all them.
        # according the GUI value. TODO: optimize.

        obj = algorithms.get_active_body()
        for expression_name in self.expressions_data:

            # Perhaps these two lines are not required
            if not hasattr(obj, expression_name):
                setattr(obj, expression_name, 0.0)

            if hasattr(obj, expression_name):
                self.reset_expression(expression_name)

        for expression_name in sorted(self.expressions_data.keys()):
            if hasattr(obj, expression_name):
                express_val = getattr(obj, expression_name)
                if express_val != 0:
                    self.update_expression(expression_name, express_val)

    def reset_expressions_gui(self):
        obj = algorithms.get_active_body()
        for expression_name in self.expressions_data:
            if hasattr(obj, expression_name):
                setattr(obj, expression_name, 0.0)
                self.reset_expression(expression_name)

    def update_expressions_data(self):
        self.identify_model_type()
        #Teto
        """if self.model_type == "ANIME":
            self.expressions_data = self.anime_expressions_data
        if self.model_type == "HUMAN":
            self.expressions_data = self.human_expressions_data
        if self.model_type == "NONE":
            self.expressions_data = {}"""
        self.expressions_data = self.model_expressions_data[self.model_type]
        #End Teto

    def update_expression(self, expression_name, express_val):

        obj = algorithms.get_active_body()
        if not obj:
            return

        if not obj.data.shape_keys:
            return

        if expression_name in self.expressions_data:
            expr_data = self.expressions_data[expression_name]
            for name, value in expr_data.items():

                sk_value = 0
                if value < 0.5:
                    name = f"{name}_min"
                    sk_value = (0.5 - value) * 2
                else:
                    name = f"{name}_max"
                    sk_value = (value - 0.5) * 2

                sk_value = sk_value*express_val

                if sk_value != 0 and hasattr(obj.data.shape_keys, 'key_blocks'):
                    if name in obj.data.shape_keys.key_blocks:
                        current_val = obj.data.shape_keys.key_blocks[name].value
                        obj.data.shape_keys.key_blocks[name].value = min(current_val + sk_value, 1.0)
                    else:
                        logger.warning("Expression %s: shapekey %s not found", expression_name, name)

    def reset_expression(self, expression_name):
        obj = algorithms.get_active_body()
        if not obj:
            return
        if not obj.data.shape_keys:
            return

        if expression_name in self.expressions_data:
            expr_data = self.expressions_data[expression_name]

            for name, value in expr_data.items():
                name = f"{name}_min" if value < 0.5 else f"{name}_max"

                if hasattr(obj.data.shape_keys, 'key_blocks'):
                    if name in obj.data.shape_keys.key_blocks:
                        obj.data.shape_keys.key_blocks[name].value = 0

    @staticmethod
    def keyframe_expression():
        obj = algorithms.get_active_body()
        if not obj:
            return
        if not obj.data.shape_keys:
            return

        if hasattr(obj.data.shape_keys, 'key_blocks'):
            for sk in obj.data.shape_keys.key_blocks:
                if "Expressions_" in sk.name:
                    sk.keyframe_insert(data_path="value")
