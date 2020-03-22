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

logger = logging.getLogger(__name__)

transfor_categories = {}

def realtime_transfor_update(self, context):
    # Check all changed values.
    global transfor_categories
    changed_values = None
    for tc in transfor_categories.values():
        changed_values = tc.get_changed_values()
        for changed_value in changed_values:
            whatever = None
        # Reinit for the next change
        tc.validate_changed_values()
    
    

class TransforMorph():
    
    def transfor_realtime_update(self, context):
        print(self.full_name)
    
    def __init__(self, cat, name, minmax = "min"):
        self.category = cat
        self.morph_name = name
        self.min_max = minmax
        self.full_name = cat + "_" + name + "_" + minmax
        self.properties = []
        self.float_prop = None
        self.actual_value = 0
        
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
    
    def set_value(self, value):
        setattr(bpy.context.scene, self.full_name, value)
    
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
        if getattr(bpy.context.scene, self.full_name) != self.actual_value:
            print(getattr(bpy.context.scene, self.full_name))
            return True
        return False
    
    def get_value(self):
        return getattr(bpy.context.scene, self.full_name)
        
    def validate_change(self):
        self.actual_value = getattr(bpy.context.scene, self.full_name)
        
    def __contains__(self, prop):
        for propx in self.properties:
            if propx == prop:
                return True
        return False
        
    def __eq__(self, other):
        return other.category == self.category and other.morph_name in self.morph_name

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
    
    def get_changed_values(self):
        changed_values = []
        for ldb in self.local_data_base.values():
            if ldb[0].is_changed() or ldb[1].is_changed():
                print(ldb[0])
                #changed_values.append
                # To do here : What values we put in changed_values
                # in order to do the changes in the character quickly ?
        return []
     
    def validate_changed_values(self):
        for ldb in self.local_data_base.values():
            ldb[0].validate_change()
            ldb[1].validate_change()
    
    # Update transformation values in humanoid.
    def update(self, cat):
        list = []
        transformation_list = self.humanoid.transformations_data[self.transfor_category]
        for h_prop in transformation_list:
            for t_prop in self.transformorphs_in_morph_category:
                print("Todo")
    
    def __repr__(self):
        return "Nb of transfor_morphs = {0}\"".format(len(self.local_data_base.keys()))


class Transfor:
    
    def __init__(self, huma):
        global transfor_categories
        self.humanoid = huma
        self.panel_initialized = False
        self.scn = None
        self.data_base = []
        transfor_categories["Age"] = TransforCategory("Age", self.humanoid)
        transfor_categories["Mass"] = TransforCategory("Mass", self.humanoid)
        transfor_categories["Tone"] = TransforCategory("Tone", self.humanoid)
        
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
        
    def load_transformation(self, filepath):
        return None
    
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
        txt = "transfor_" + title.lower()
        parent_box.prop(self.scn, txt)
        t_cat = getattr(self.scn, txt)
        t_morphs = self.get_data_base(title)
        for t_morph in t_morphs:
            if t_morph[1].morph_name.startswith(t_cat):
                r = parent_box.row()
                r.label(text=t_morph[1].morph_name)
                r.prop(self.scn, t_morph[1].full_name)
                r.prop(self.scn, t_morph[2].full_name)

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