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
        self.scn = None
        
    def load_transformation_from_file(self, filepath):
        self.humanoid.reset_character()
        self.humanoid.transformations_data = file_ops.load_json_data(filepath, "Transformation file")
    
    def set_scene(self, scene):
        self.scn = scene

    def save_transformation(self, filepath, category, minmax):
        export_db = file_ops.load_json_data(filepath, "Create step or finalize transformation file.")
        if export_db == None:
            export_db = {}
        #------------------ Variables for the method
        obj = self.humanoid.get_object()
        exists = False
        #------------------ If the category doesn't exist, it's created.
        if category not in export_db.keys():
            export_db[category] = []
        #------------------ Now, check every property, add to a temp list
        temp_list = {}
        calc = 0.0
        for m_prop in self.humanoid.character_data.keys():
            if not m_prop.startswith("Expressions"):
                calc = (self.humanoid.character_data[m_prop] * 2) - 1
                temp_list[m_prop] = round(calc, 3)
        #------------------ Now, check final list and change values.
        for key, value in temp_list.items():
            exists = False
            for t_prop in export_db[category]:
                if key == t_prop[0]:
                    exists = True
                    if minmax == "MI":
                        t_prop[1] = value
                    else:
                        t_prop[2] = value
            if not exists:
                if minmax == "MI":
                    export_db[category].append([key, value, 0.0])
                else:
                    export_db[category].append([key, 0.0, value])
            exists = False
        #--------Clean data base by deleting all values [name, 0, 0]
        cleaned_db = []
        for t_prop in export_db[category]:
            if t_prop[1] != 0.0 or t_prop[2] != 0.0:
                cleaned_db.append(t_prop)
        export_db[category] = cleaned_db
        if len(export_db[category]) < 1:
            del export_db[category]
        #--------Save file
        with open(filepath, "w") as j_file:
            json.dump(export_db, j_file, indent=2)
        j_file.close()
    
    def load_transformation(self, filepath, category, minmax):
        self.humanoid.reset_character()
        import_db = file_ops.load_json_data(filepath, "import step transformation file.")
        #------------------ Create a temp list with all values to change
        temp_list = {}
        for t_prop in import_db[category]:
            if minmax == "MI":
                temp_list[t_prop[0]] = (t_prop[1] * 0.5) + 0.5
            else:
                temp_list[t_prop[0]] = (t_prop[2] * 0.5) + 0.5
        #------------------ Now we put the values in humanoid database.
        for key, item in temp_list.items():
            # Had to do this because sometimes names in standard files are not
            # complete, example BreastTone instead of Torso_BreastTone.
            for m_key in self.humanoid.character_data.keys():
                if key in m_key:
                    self.humanoid.character_data[m_key] = item
        self.humanoid.update_character()
        
    def check_compatibility_with_current_model(self, filepath):
        data_base = file_ops.load_json_data(filepath, "Read transformation file to check compatibility.")
        txt = {}
        txt["About"] = [
            "Check if some entries in transformation database are not valid.",
            "Could be a wrong name, an unknown name or a name for another model.",
            "For the case of trying to use transformations from one model to another",
            "too many unused morphs may create weird results."]
        txt_key = ""
        obj = bpy.types.Object
        exists = False
        for key in data_base.keys():
            if key == "fat_data":
                txt_key = "About mass"
            elif key == "muscle_data":
                txt_key = "About tone"
            else:
                txt_key = "About " + key.split("_")[0]
            if txt_key not in txt:
                txt[txt_key] = []
            #--------------------
            for t_prop in data_base[key]:
                exists = False
                for m_prop in self.humanoid.character_data.keys():
                    if t_prop[0] in m_prop:
                        exists = True
                        break
                if not exists:
                    txt[txt_key].append(t_prop[0] + " may not be used")
        filepath += ".txt"
        with open(filepath, "w") as j_file:
            json.dump(txt, j_file, indent=2)
        j_file.close()

    def save_current_model(self, filepath):
        transf_data = self.humanoid.transformations_data
        with open(filepath, "w") as j_file:
            json.dump(transf_data, j_file, indent=2)
        j_file.close()