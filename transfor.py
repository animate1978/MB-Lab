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

logger = logging.getLogger(__name__)

class Transfor:
    
    def __init__(self, huma):
        self.humanoid = huma
    
    def load_transformation(self, filepath):
        return None
    
    # Return a box with all stuff inside to change properties.
    def get_box(self, parent_panel):
        # Construction
        main_box = parent_panel.box()
        main_box.label(text="#Todo...", icon='INFO')
    
    def save_transformation(self, filepath):
        # transf_data = humanoid.transformations_data.keys()
        # dict_keys(['age_data', 'fat_data', 'muscle_data'])
        transf_data = self.humanoid.transformations_data
        with open(filepath, "w") as j_file:
            json.dump(transf_data, j_file, indent=2)
        j_file.close()
    
    def reset_properties(self):
        # All elements are recreated from humanoid object.
        self.panel_initialized = False
        return None