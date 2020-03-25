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
# Part made by Teto.

import logging
import bpy
# TODO pathlib might replace the current import os 
# from pathlib import Path

import os
import time
import json
import operator

from . import algorithms
from . import file_ops

logger = logging.getLogger(__name__)

class Transfor:
    
    def __init__(self, huma):
        self.humanoid = huma
        
    def load_transformation_from_file(self, filepath):
        self.humanoid.reset_character()
        self.humanoid.transformations_data = file_ops.load_json_data(filepath, "Transformation file")

    def check_compatibility_with_current_model(self, filepath):
        print("#Todo : check_compatibility_with_current_model")

    def clean_file(self, filepath):
        print("#Todo : clean_file")
        
    def save_transformation(self, filepath):
        print("#Todo : save_transformation")

    def save_current_model(self, filepath):
        transf_data = self.humanoid.transformations_data
        with open(filepath, "w") as j_file:
            json.dump(transf_data, j_file, indent=2)
        j_file.close()