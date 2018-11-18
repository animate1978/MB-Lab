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

import os
import bpy
import mathutils
from . import algorithms, proxyengine
import time, json
import operator

class MorphingEngine:

    def __init__(self, obj_name, character_config):
        time1 = time.time()
        data_path = algorithms.get_data_path()
        self.final_form = []
        self.cache_form = []
        self.obj_name = obj_name        

        self.vertices_filename = character_config["name"]+"_verts.json"
        self.expressions_filename = character_config["name"]+"_exprs.json"
        self.morphs_filename = character_config["name"]+"_morphs.json"
        self.morphs_filename_extra = character_config["morphs_extra_file"]
        self.shared_morphs_filename = character_config["shared_morphs_file"]
        self.shared_morphs_filename_extra = character_config["shared_morphs_extra_file"]
        self.shared_anthropometric_path = character_config["proportions_folder"]
        self.shared_measures_filename = character_config["measures_file"]
        self.shared_bbox_filename = character_config["bounding_boxes_file"]
        self.measures_database_exist = False
        
        if self.shared_morphs_filename_extra != "":    
            self.shared_morph_extra_data_path = os.path.join(
                data_path,
                "morphs",
                self.shared_morphs_filename_extra)
        else:
            self.shared_morph_extra_data_path = None

        self.measures_data_path = os.path.join(
            data_path,
            "measures",
            self.shared_measures_filename)
        self.bodies_data_path = os.path.join(
            data_path,
            "anthropometry",
            self.shared_anthropometric_path)
        self.shared_morph_data_path = os.path.join(
            data_path,
            "morphs",
            self.shared_morphs_filename)        
        self.morph_data_path = os.path.join(
            data_path,
            "morphs",
            self.morphs_filename)
        self.extra_morph_data_path = os.path.join(
            data_path,
            "morphs",
            self.morphs_filename_extra)
        self.bounding_box_path = os.path.join(
            data_path,
            "bboxes",
            self.shared_bbox_filename)
        self.expressions_path = os.path.join(
            data_path,
            "expressions_morphs",
            self.expressions_filename)
        self.vertices_path = os.path.join(
            data_path,
            "vertices",
            self.vertices_filename)


        if os.path.isdir(self.bodies_data_path):
            if os.path.isfile(self.measures_data_path):
                self.measures_database_exist = True

        self.verts_to_update = set()
        self.morph_data = {}
        self.morph_data_cache = {}
        self.forma_data = None
        self.bbox_data = {}
        self.morph_values = {}
        self.morph_modified_verts = {}
        self.boundary_verts = None
        self.measures_data = {}
        self.measures_relat_data = []
        self.measures_score_weights = {}
        self.body_height_Z_parts = {}

        self.proportions = {}
        self.proportion_index = None

        self.init_final_form()
        self.base_form = algorithms.load_vertices_database(self.vertices_path)

        self.load_morphs_database(self.shared_morph_data_path)
        self.load_morphs_database(self.morph_data_path)
        self.load_morphs_database(self.extra_morph_data_path) #Call this after the loading of shared morph is important for overwrite data.
        if self.shared_morph_extra_data_path:
            self.load_morphs_database(self.shared_morph_extra_data_path)
        self.load_morphs_database(self.expressions_path)
        self.load_bboxes_database(self.bounding_box_path)
        self.load_measures_database(self.measures_data_path)

        self.measures = self.calculate_measures()

        #Checks:
        if len(self.final_form) != len(self.base_form):
            algorithms.print_log_report("CRITICAL","Vertices database not coherent with the vertices in the obj {0}".format(self.obj_name))
        #TODO: add more checks

        algorithms.print_log_report("INFO","Databases loaded in {0} secs".format(time.time()-time1))

    def init_final_form(self):
        obj = self.get_object()
        self.final_form = []
        for vert in obj.data.vertices:
                self.final_form.append(vert.co.copy())

    def __repr__(self):
        return "MorphEngine {0} with {1} morphings".format(self.obj_name, len(self.morph_data))

    def get_object(self):
        if self.obj_name in bpy.data.objects:
            return bpy.data.objects[self.obj_name]
        return None

    def error_msg(self, path):
        algorithms.print_log_report("WARNING","Database file not found: {0}".format(algorithms.simple_path(path)))

    def reset(self, update=True):
        for i in range(len(self.base_form)):
            self.final_form[i] = self.base_form[i]
        for morph_name in self.morph_values.keys():
            self.morph_values[morph_name] = 0.0
        if update:
            self.update(update_all_verts=True)

    def load_measures_database(self, measures_path):
        m_database = algorithms.load_json_data(measures_path,"Measures data")
        if m_database:
            self.measures_data = m_database["measures"]
            self.measures_relat_data = m_database["relations"]
            self.measures_score_weights = m_database["score_weights"]
            self.body_height_Z_parts = m_database["body_height_Z_parts"]

    def load_bboxes_database(self, bounding_box_path):
        self.bbox_data = algorithms.load_json_data(bounding_box_path,"Bounding box data")


    def load_morphs_database(self, morph_data_path):
        time1 = time.time()
        m_data = algorithms.load_json_data(morph_data_path,"Morph data")
        if m_data:
            for morph_name, deltas in m_data.items():
                morph_deltas = []
                modified_verts = set()
                for d_data in deltas:
                    t_delta = mathutils.Vector(d_data[1:])
                    morph_deltas.append([d_data[0], t_delta])
                    modified_verts.add(d_data[0])
                if morph_name in self.morph_data:
                    algorithms.print_log_report("WARNING","Morph {0} duplicated while loading morphs from file".format(morph_name))

                self.morph_data[morph_name] = morph_deltas
                self.morph_values[morph_name] = 0.0
                self.morph_modified_verts[morph_name] = modified_verts
            algorithms.print_log_report("INFO","Morph database {0} loaded in {1} secs".format(algorithms.simple_path(morph_data_path),time.time()-time1))
            algorithms.print_log_report("INFO","Now local morph data contains {0} elements".format(len(self.morph_data)))


    #def apply_finishing_morph(self):
        #"""
        #Modify the Blender object in order to finish the surface.
        #"""
        #time1 = time.time()
        #obj = self.get_object()
        #if not self.boundary_verts:
            #self.boundary_verts = proxyengine.get_boundary_verts(obj)
        #if not self.forma_data:
            #self.forma_data = proxyengine.load_forma_database(self.morph_forma_path)
        #proxyengine.calculate_finishing_morph(obj, self.boundary_verts, self.forma_data, threshold=0.25)
        #algorithms.print_log_report("INFO","Finishing applied in {0} secs".format(time.time()-time1))

    def calculate_measures(self,measure_name = None,vert_coords=None):

        if not vert_coords:
            vert_coords = self.final_form
        measures = {}
        time1 = time.time()
        if measure_name:
            if measure_name in self.measures_data:
                indices =  self.measures_data[measure_name]
                axis = measure_name[-1]
                return algorithms.length_of_strip(vert_coords, indices, axis)
        else:
            for measure_name in self.measures_data.keys():
                measures[measure_name] = self.calculate_measures(measure_name, vert_coords)
            algorithms.print_log_report("DEBUG","Measures calculated in {0} secs".format(time.time()-time1))
            return measures

    def calculate_proportions(self, measures):

        if measures == None:
            measures = self.measures
        if "body_height_Z" in measures:
            if "buttock_girth" in measures:
                if "chest_girth" in measures:
                    p1 = round(measures["buttock_girth"]/measures["body_height_Z"],4)
                    p2 = round(measures["chest_girth"]/measures["body_height_Z"],4)
                    p3 = round(measures["waist_girth"]/measures["body_height_Z"],4)
                    p4 = round(measures["upperarm_axillary_girth"]/measures["body_height_Z"],4)
                    p5 = round(measures["upperleg_top_girth"]/measures["body_height_Z"],4)
                    self.proportion_index = [p1,p2,p3,p4,p5]
                else:
                    algorithms.print_log_report("ERROR","The 'chest_girth' measure not present in the analyzed database")
            else:
                algorithms.print_log_report("ERROR","The 'buttock_girth' measure not present in the analyzed database")
        else:
            algorithms.print_log_report("ERROR","The 'body_height_Z' measure not present in the analyzed database")


    def compare_file_proportions(self,filepath):
        char_data = algorithms.load_json_data(filepath,"Proportions data")
        if "proportion_index" in char_data:
            v1 = mathutils.Vector(self.proportion_index)
            v2 = mathutils.Vector(char_data["proportion_index"])
            delta_v = v2-v1

            return (delta_v.length,filepath)
        else:
            algorithms.print_log_report("INFO","File {0} does not contain proportions".format(algorithms.simple_path(filepath)))


    def compare_data_proportions(self):
        scores = []
        time1 = time.time()
        if os.path.isdir(self.bodies_data_path):
            for database_file in os.listdir(self.bodies_data_path):
                body_data, extension = os.path.splitext(database_file)
                if "json" in extension:
                    scores.append(self.compare_file_proportions(os.path.join(self.bodies_data_path,database_file)))
            scores.sort(key=operator.itemgetter(0), reverse=False)
            algorithms.print_log_report("INFO","Measures compared with database in {0} seconds".format(time.time()-time1))
        else:
            algorithms.print_log_report("WARNING","Bodies database not found")
        return scores




    def correct_morphs(self, names):
        morph_values_cache = {}
        for morph_name in self.morph_data.keys():
            for name in names:
                if name in morph_name:
                    morph_values_cache[morph_name] = self.morph_values[morph_name]#Store the values before the correction
                    self.calculate_morph(morph_name, 0.0) #Reset the morphs to correct

        for morph_name, morph_deltas in self.morph_data.items():
            for name in names:
                if name in morph_name: #If the morph is in the list of morph to correct
                    if morph_name in self.morph_data_cache:
                        morph_deltas_to_recalculate = self.morph_data_cache[morph_name]
                    else:
                        self.morph_data_cache[morph_name] = morph_deltas
                        morph_deltas_to_recalculate = self.morph_data_cache[morph_name]

                    self.morph_data[morph_name] = algorithms.correct_morph(
                        self.base_form,
                        self.final_form,
                        morph_deltas_to_recalculate,
                        self.bbox_data)
        for morph_name in self.morph_data.keys():
            for name in names:
                if name in morph_name:
                    self.calculate_morph(
                        morph_name,
                        morph_values_cache[morph_name])
        self.update()



    def convert_all_to_blshapekeys(self):

        #TODO: re-enable the finishing (finish = True) after some improvements

        obj = self.get_object()
        #Reset all values (for expressions only) and create the basis key
        for morph_name in self.morph_data.keys():
            if "Expression" in morph_name:
                self.calculate_morph(morph_name, 0.0)
                self.update()
        algorithms.new_shapekey(obj, "basis")         
     

        #Store the character in neutral expression
        obj = self.get_object()
        stored_vertices = []
        for vert in obj.data.vertices:
            stored_vertices.append(mathutils.Vector(vert.co))

        algorithms.print_log_report("INFO","Storing neutral character...OK")
        counter = 0
        for morph_name in sorted(self.morph_data.keys()):
            if "Expression" in morph_name:
                counter += 1
                self.calculate_morph(morph_name, 1.0)
                algorithms.print_log_report("INFO","Converting {} to shapekey".format(morph_name))
                self.update(update_all_verts=True)
                new_sk = algorithms.new_shapekey_from_current_vertices(obj, morph_name)
                new_sk.value = 0               

                #Restore the neutral expression
                for i in range(len(self.final_form)):
                    self.final_form[i] = stored_vertices[i]
                self.update(update_all_verts=True)
        algorithms.print_log_report("INFO","Successfully converted {0} morphs in shapekeys".format(counter))




    def update(self, update_all_verts=False):
        obj = self.get_object()
        vertices = obj.data.vertices
        if update_all_verts == True:
            for i in range(len(self.final_form)):
                vertices[i].co = self.final_form[i]
        else:
            for i in self.verts_to_update:
                vertices[i].co = self.final_form[i]

    def copy_in_cache(self):
        obj = self.get_object()
        self.clean_the_cache()
        vertices = obj.data.vertices
        for i in range(len(self.final_form)):
            self.cache_form.append(vertices[i].co.copy())
        algorithms.print_log_report("INFO","Mesh cached")

    def copy_from_cache(self):
        if len(self.final_form) == len(self.cache_form):
            for i in range(len(self.final_form)):
                self.final_form[i] = self.cache_form[i]
            algorithms.print_log_report("INFO","Mesh copied from cache")
        else:
            algorithms.print_log_report("WARNING","Cached mesh not found")

    def clean_the_cache(self):
        self.cache_form = []


    def calculate_morph(self, morph_name, val, add_vertices_to_update=True):

        if morph_name in self.morph_data:
            real_val = val - self.morph_values[morph_name]
            if real_val != 0.0:
                morph = self.morph_data[morph_name]
                for d_data in morph:
                    i = d_data[0]
                    delta = d_data[1]
                    self.final_form[i] = self.final_form[i] + delta*real_val
                if add_vertices_to_update:
                    self.verts_to_update = self.verts_to_update.union(self.morph_modified_verts[morph_name])
                self.morph_values[morph_name] = val
        else:
            algorithms.print_log_report("DEBUG","Morph data {0} not found".format(morph_name))









