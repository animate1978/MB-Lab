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

transfor_categories = {}

inhibition = False

def realtime_transfor_update(self, context):
    # Useful during initialization.
    if inhibition:
        return
    # Check all changed values.
    global transfor_categories
    for tc in transfor_categories.values():
        tc.check_changed_values()

class TransforMorph():
    
    def __init__(self, cat, name, minmax = "min"):
        self.category = cat # Means age, mass, tone
        self.morph_name = name
        self.min_max = minmax
        self.full_name = cat + "_" + name + "_" + minmax
        self.properties = [] # Useless, maybe
        self.float_prop = None # The cursor on GUI
        self.current_value = 0 # The actual value shown in the cursor
        self.saved_value = 0 # A state where the user can recover.
        
    def add(self, prop):
        self.properties.append(prop)
    
    def get_property(self, prop):
        """
        Return the property by name.
        """
        for propx in self.properties:
            if propx == prop:
                return propx
        return None

    def get_properties(self):
        """
        Return the properties contained in the
        modifier. Important: keep unsorted!
        """
        return self.properties

    def get_object(self):
        """
        Get the blender object. It can't be stored because
        Blender's undo and redo change the memory locations
        """
        if self.full_name in bpy.data.objects:
            return bpy.data.objects[self.full_name]
        return None
    
    """def set_value(self, value):
        setattr(bpy.context.scene, self.full_name, value)"""
    
    def create_transfor_prop(self):
        self.float_prop = bpy.props.FloatProperty(
            name=self.min_max,
            min=-5.0,
            max=5.0,
            soft_min=-1.0,
            soft_max=1.0,
            precision=3,
            default=0.0,
            subtype='FACTOR',
            update=realtime_transfor_update)
        setattr(
            bpy.types.Scene,
            self.full_name,
            self.float_prop
            )
            
    def is_changed(self):
        if getattr(bpy.context.scene, self.full_name) != self.current_value:
            return True
        return False
    
    def validate_recover_value(self):
        self.saved_value = self.current_value
    
    def recover_value(self):
        self.current_value = self.saved_value
        setattr(bpy.context.scene, self.full_name, self.saved_value)
        # Careful : think to put the value in humanoid data base !
        
    def __contains__(self, prop):
        for propx in self.properties:
            if propx == prop:
                return True
        return False
        
    def __eq__(self, other):
        try:
            return self.current_value == other.current_value
        except:
            return self.current_value == other

    def __repr__(self):
        return "Transfor item \"{0}\" (full name : {1})".format(
            self.morph_name,
            self.full_name)

class TransforCategory:
    
    def __init__(self, ca, huma):
        # The category : Age, Tone, mass
        self.transfor_category = ca
        # The original humanoid
        self.humanoid = huma
        # Key : Name of the morph
        # Value : a [] with full_name, object TransforMorph min, object TransforMorph max
        self.local_data_base = {}
    
    # Don't remember why I was thinking that user could need this method.
    def set_humanoid(self, huma):
        if self.humanoid == None:
            self.humanoid = huma
    
    # Init local data base with properties for update
    def set_local_data_base(self, data_base):
        self.local_data_base.clear()
        for prop in data_base:
            tm_min = TransforMorph(self.transfor_category, prop)
            tm_max = TransforMorph(self.transfor_category, prop, minmax = "max")
            name = self.transfor_category + "_" + prop
            self.local_data_base[name] = [tm_min, tm_max]
            # Create prop for later
            tm_min.create_transfor_prop()
            tm_max.create_transfor_prop()
    
    def get_local_data_base(self):
        return self.local_data_base
    
    # check all objects in the category and if there's a difference
    # between the dedicated property and the value in the object,
    # the new value is saved.
    def check_changed_values(self):
        for ldb_value in self.local_data_base.values():
            val_min = getattr(bpy.context.scene, ldb_value[0].full_name)
            val_max = getattr(bpy.context.scene, ldb_value[1].full_name)
            if ldb_value[0].current_value != val_min or ldb_value[1].current_value != val_max:
                ldb_value[0].current_value = val_min
                ldb_value[1].current_value = val_max
                self.seek_and_change_humanoid_value(ldb_value[0], ldb_value[1])
    
    def seek_and_change_humanoid_value(self, transfor_min, transfor_max):
        # tricks... btw, if new categories are added for a reason,
        # they will have to keep the same name (aka "name_data")
        # to avoid this...
        key_after = ""
        if self.transfor_category == "mass":
            key_after = "fat_data"
        elif self.transfor_category == "tone":
            key_after = "muscle_data"
        else:
            key_after = self.transfor_category + "_data"
        # comeback to normal.
        h_database = self.humanoid.transformations_data[key_after]
        ok = False
        for h_data in h_database:
            if h_data[0] in transfor_min.morph_name:
                #print("Existing : " + h_data[0])
                h_data[1] = transfor_min.current_value
                h_data[2] = transfor_max.current_value
                ok = True
        if not ok:
            #print("Creating : " + h_data[0])
            self.humanoid.transformations_data[key_after].append([transfor_min.morph_name, transfor_min.current_value, transfor_max.current_value])
        
    def validate_recover_values(self):
        for ldb_value in self.local_data_base.values():
            ldb_value[0].validate_recover_value()
            ldb_value[1].validate_recover_value()
    
    def recover_values(self):
        global inhibition
        inhibition = True
        for ldb_value in self.local_data_base.values():
            ldb[0].recover_value()
            ldb[1].recover_value()
        inhibition = False
    
    def get_changed_transformorph(self):
        changed_values = []
        for ldb_name, ldb_value in self.local_data_base.items():
            if ldb_value[0].is_changed() or ldb_value[1].is_changed():
                changed_values.append([ldb_name, ldb_value[0], ldb_value[1]])
        return changed_values
     
    def __repr__(self):
        return "Nb of transfor_morphs = {0}\"".format(len(self.local_data_base.keys()))


class Transfor:
    
    def __init__(self, huma):
        global transfor_categories
        self.humanoid = huma
        self.panel_initialized = False
        self.scn = None
        self.data_base = []
        transfor_categories["age"] = TransforCategory("age", self.humanoid)
        transfor_categories["mass"] = TransforCategory("mass", self.humanoid)
        transfor_categories["tone"] = TransforCategory("tone", self.humanoid)
        
    def init_transfor_props(self):
        global transfor_categories
        if self.panel_initialized:
            return
        for prop in sorted(self.humanoid.character_data.keys()):
            if not prop.startswith("Expressions"):
                self.data_base.append(prop)
        print("... Init transformations data base for Age / Mass / Tone")
        for cat in transfor_categories.values():
            cat.set_local_data_base(self.data_base)
        print("... Done.")
        self.load_transformation_from_model()
        self.panel_initialized = True
    
    def is_initialized(self):
        return self.panel_initialized
    
    def get_transfor_categories(self):
        global transfor_categories
        return transfor_categories
    
    def get_data_base(self, cat):
        global transfor_categories
        adb = []
        tmp = []
        for key, value in transfor_categories[cat].get_local_data_base().items():
            tmp = [key, value[0], value[1]]
            adb.append(tmp)
        return adb
    
    def get_all_data_bases(self):
        global transfor_categories
        adb = []
        for cat in transfor_categories.keys():
            adb.append(self.get_data_base(cat))
        return adb
        
    def set_scene(self, scene):
        self.scn = scene
    
    # Return a box with all stuff inside to change properties.
    def create_box(self, parent_panel):
        global transfor_categories
        self.init_transfor_props()
        if self.scn == None:
            return
        # Construction
        for cat in transfor_categories.keys():
            main_box = parent_panel.box()
            self.create_agemasstone_box(main_box, cat)
    
    def create_agemasstone_box(self, parent_box, title):
        parent_box.label(text=title, icon='SORT_ASC')
        txt = "transfor_" + title
        parent_box.prop(self.scn, txt)
        t_cat = getattr(self.scn, txt)
        t_morphs = self.get_data_base(title)
        for t_morph in t_morphs:
            if t_morph[1].morph_name.startswith(t_cat):
                r = parent_box.row()
                r.label(text=t_morph[1].morph_name)
                r.prop(self.scn, t_morph[1].full_name)
                r.prop(self.scn, t_morph[2].full_name)
    
    def load_transformation_from_model(self):
        global inhibition
        inhibition = True
        # tricks... btw if new categories are added for a reason,
        # they will have to keep the same name (aka "name_data")
        # to avoid this...
        keys_before = self.humanoid.transformations_data.keys()
        keys_after = []
        for i in keys_before:
            if i == "fat_data":
                keys_after.append("mass")
            elif i == "muscle_data":
                keys_after.append("tone")
            else:
                keys_after.append(i.split("_")[0])
        # comeback to normal.
        index = 0
        debug = 0
        for key in keys_before:
            local_db = self.get_data_base(keys_after[index])
            for h_transfor in self.humanoid.transformations_data[key]:
                for l_transfor in local_db:
                    if h_transfor[0] in l_transfor[0]:
                        setattr(bpy.context.scene, l_transfor[1].full_name, h_transfor[1])
                        setattr(bpy.context.scene, l_transfor[2].full_name, h_transfor[2])
                        l_transfor[1].current_value = h_transfor[1]
                        l_transfor[2].current_value = h_transfor[2]
                        debug += 1
            print("Debug : for " + keys_after[index] + ", " + str(debug) + " properties were found.")
            index += 1
            debug = 0
        # The step below is necessary, because values created by setattr are not rounded everytime
        # For example 0.45 can be initialized at 0.4999999999912358
        # So the step below fixes that.
        global transfor_categories
        for cat in transfor_categories.values():
            cat.check_changed_values()
        inhibition = False
    
    def load_transformation_from_file(self, filepath):
        self.humanoid.reset_character()
        self.humanoid.transformations_data = file_ops.load_json_data(filepath, "Transformation file")
        self.load_transformation_from_model()
        return
        
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
    
    def reset_values(self):
        adb = get_all_data_bases()
        for property in adb:
            print("reset")

    def validate_values(self):
        print("validate_values")
        