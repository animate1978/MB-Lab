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

import bpy
from . import algorithms
import os, json, time
import mathutils

class ProxyEngine:

    def __init__(self):
        self.has_data = False
        self.data_path = algorithms.get_data_path()
        self.templates_library = algorithms.get_blendlibrary_path()

        self.assets_path = os.path.join(self.data_path,"assets")
        self.assets_models = algorithms.generate_items_list(self.assets_path, "blend")

        self.corrective_modifier_name = "mbastlab_proxy_smooth_modifier"
        #self.mask_modifier_name = "mbastlab_mask_modifier"
        self.proxy_armature_modifier = "mbastlab_proxy_armature"


    def update_assets_models(self):
        scn = bpy.context.scene
        if os.path.isdir(scn.mblab_proxy_library):
            self.assets_path = scn.mblab_proxy_library            
        else:
            self.assets_path = os.path.join(self.data_path,"assets")     
            
        self.assets_models = algorithms.generate_items_list(self.assets_path, "blend")
            

    def load_asset(self, assetname):
        scn = bpy.context.scene
        asset_path = os.path.join(self.assets_path,assetname+".blend")
        algorithms.append_object_from_library(asset_path, [assetname])


    def transfer_weights(self, body, proxy):

        body_kd_tree = algorithms.kdtree_from_mesh_vertices(body.data)

        fit_shapekey = algorithms.get_shapekey(proxy, "mbastlab_proxyfit")
        if fit_shapekey:
            proxy_vertices = fit_shapekey.data
        else:
            proxy_vertices = proxy.data.vertices
            algorithms.print_log_report("WARNING","Weights transfer executed without fitting (No fit shapekey found)")



        body_verts_weights = [[] for v in body.data.vertices]
        for grp in body.vertex_groups:
            for idx, w_data in enumerate(body_verts_weights):
                try:
                    w_data.append([grp.name,grp.weight(idx)])
                except:
                    pass #TODO: idx in grp.weight

        for p_idx, proxy_vert in enumerate(proxy_vertices):

            proxy_vert_weights = {}
            nearest_body_vert = body_kd_tree.find(proxy_vert.co)
            min_dist =  nearest_body_vert[2]

            nearest_body_verts = body_kd_tree.find_range(proxy_vert.co,min_dist*2)


            for nearest_body_vert_data in nearest_body_verts:

                body_vert_idx = nearest_body_vert_data[1]
                body_vert_dist = nearest_body_vert_data[2]

                if body_vert_dist != 0:
                    magnitude = min_dist/body_vert_dist
                else:
                    magnitude = 1


                group_data = body_verts_weights[body_vert_idx]

                for g_data in group_data:
                    if len(g_data) > 0:
                        group_name = g_data[0]
                        vert_weight = g_data[1]

                    if group_name in proxy_vert_weights:
                        proxy_vert_weights[group_name] += vert_weight*magnitude
                    else:
                        proxy_vert_weights[group_name] = vert_weight*magnitude


            #Weights normalize
            weights_sum = 0
            for vert_weight in proxy_vert_weights.values():
                weights_sum += vert_weight

            for group_name,vert_weight in proxy_vert_weights.items():
                proxy_vert_weights[group_name] = vert_weight/weights_sum


            for group_name,vert_weight in proxy_vert_weights.items():

                    if group_name not in proxy.vertex_groups:
                        proxy.vertex_groups.new(name=group_name)

                    g = proxy.vertex_groups[group_name]
                    g.add([p_idx], vert_weight, 'REPLACE')


    def disable_extra_armature_modfr(self, proxy):
        for modfr in proxy.modifiers:
            if modfr.type == 'ARMATURE':
                if modfr.name != self.proxy_armature_modifier:
                    algorithms.disable_modifier(modfr)

    def add_proxy_armature_modfr(self, proxy, armat):
        for modfr in proxy.modifiers:
            if modfr.type == 'ARMATURE':
                if modfr.name == self.proxy_armature_modifier:
                    algorithms.remove_modifier(proxy, self.proxy_armature_modifier)

        parameters = {"object":armat}
        armature_modifier = algorithms.new_modifier(proxy, self.proxy_armature_modifier,'ARMATURE', parameters)
        return armature_modifier

    # def add_mask_modifier(self, body, mask_name):
        # parameters = {"vertex_group":mask_name,"invert_vertex_group":True}
        # algorithms.new_modifier(body, mask_name, 'MASK', parameters)

    def calibrate_proxy_object(self,proxy):
        if proxy != None:
            old_version_sk = algorithms.get_shapekey(proxy,"Fitted")
            if old_version_sk:
                old_version_sk.value = 0
            if not algorithms.get_shapekey(proxy,"mbastlab_proxyfit"):
                algorithms.apply_object_transformation(proxy)
            if not algorithms.get_shapekey_reference(proxy):
                algorithms.new_shapekey(proxy, "Basis")

    def remove_fitting(self):
        status, proxy, body = self.get_proxy_fitting_ingredients()
        mask_name = "mbastlab_mask_" + proxy.name
        if status == "OK":
            algorithms.remove_shapekeys_all(proxy)
            proxy.matrix_world.identity()
            self.remove_body_mask(body, mask_name)


    def get_proxy_template_design(self, proxy_obj):

        g_identifiers1 = ["girl", "woman", "female"]
        g_identifiers2 = ["boy", "man", "male"]

        if "anime" in proxy_obj.name.lower():
            for g_id in g_identifiers1:
                if g_id in proxy_obj.name.lower():
                    return "anime_female"
            for g_id in g_identifiers2:
                if g_id in proxy_obj.name.lower():
                    return "anime_male"
        else:
            for g_id in g_identifiers1:
                if g_id in proxy_obj.name.lower():
                    return "human_female"
            for g_id in g_identifiers2:
                if g_id in proxy_obj.name.lower():
                    return "human_male"

        return None



    def validate_assets_compatibility(self, proxy_obj, reference_obj):

        proxy_template =  self.get_proxy_template_design(proxy_obj)
        id_template = algorithms.get_template_model(reference_obj)

        if proxy_template != None:
            if id_template != None:
                if proxy_template in id_template:
                    return "OK"
                else:
                    return "WARNING"

        return "NO_SPECIFIED"



    def get_proxy_fitting_ingredients(self):
        scn = bpy.context.scene
        status = 'OK'

        if scn.mblab_proxy_name != "NO_PROXY_FOUND":

            if scn.mblab_fitref_name == scn.mblab_proxy_name:
                return ["SAME_OBJECTS", None, None]
            character_obj = algorithms.get_object_by_name(scn.mblab_fitref_name)
            proxy_obj = algorithms.get_object_by_name(scn.mblab_proxy_name)
            if character_obj == None:
                return ["CHARACTER_NOT_FOUND", None, None]
            if proxy_obj == None:
                return ["PROXY_NOT_FOUND", None, None]
            if not algorithms.is_a_lab_character(character_obj):
                return ["NO_REFERENCE", None, None]
            return ["OK", proxy_obj, character_obj]

        return ["PROXY_NOT_FOUND", None, None]



    def reset_proxy_shapekey(self,proxy):
        fit_shapekey = algorithms.get_shapekey(proxy, "mbastlab_proxyfit")
        if fit_shapekey:
            algorithms.remove_shapekey(proxy, "mbastlab_proxyfit")


    def fit_distant_vertices(self, basis_proxy,basis_body,proxy_shapekey,current_body):


        #basis_proxy = proxy in basis shape, without shapekey applied
        #proxy_shapekey = shapekey to modify as final result
        #basis_body = body in basis shape, without morphings and armature
        #current_body = current body shape, with morphing (but not armature) applied

        polygons_file = algorithms.get_template_polygons(current_body)
        polygons_path = os.path.join(self.data_path,"pgroups",polygons_file)
        valid_polygons_indxs = algorithms.load_json_data(polygons_path, "Subset of polygons for proxy fitting")

        basis_proxy_vertices = basis_proxy.data.vertices #In Blender obj.data = basis data
        basis_body_polygons = basis_body.data.polygons
        current_body_polygons = current_body.data.polygons

        involved_body_polygons_idx = []
        involved_basis_body_polygons_coords = []
        involved_current_body_polygons_coords = []

        if len(basis_body_polygons) == len(current_body_polygons):
            basis_body_tree = algorithms.kdtree_from_obj_polygons(basis_body, valid_polygons_indxs)

            for i,basis_proxy_vert in enumerate(basis_proxy_vertices):

                nearest_body_polygons_data = basis_body_tree.find(basis_proxy_vert.co)
                body_polygon_index = nearest_body_polygons_data[1]
                involved_body_polygons_idx.append(body_polygon_index)


            for i in involved_body_polygons_idx:
                basis_body_polygon = basis_body_polygons[i]
                current_body_polygon = current_body_polygons[i]

                #current_body_polygon.select = True

                involved_basis_body_polygons_coords.append(basis_body_polygon.center)
                involved_current_body_polygons_coords.append(current_body_polygon.center)

            basis_body_bbox = algorithms.get_bounding_box(involved_basis_body_polygons_coords)
            current_body_bbox = algorithms.get_bounding_box(involved_current_body_polygons_coords)

            basis_body_center = algorithms.average_center(involved_basis_body_polygons_coords)
            current_body_center = algorithms.average_center(involved_current_body_polygons_coords)

            scaleX = current_body_bbox[0]/basis_body_bbox[0]
            scaleY = current_body_bbox[1]/basis_body_bbox[1]
            scaleZ = current_body_bbox[2]/basis_body_bbox[2]

            scale_bbox = mathutils.Vector((scaleX,scaleY,scaleZ))

            for i,basis_proxy_vert in enumerate(basis_proxy_vertices):
                proxy_shapekey_vert = proxy_shapekey.data[i]
                basis_radial_vector = basis_proxy_vert.co-basis_body_center
                scaled_radial_vector = mathutils.Vector((basis_radial_vector[0]*scale_bbox[0],
                                                        basis_radial_vector[1]*scale_bbox[1],
                                                        basis_radial_vector[2]*scale_bbox[2]))

                proxy_shapekey_vert.co = current_body_center + scaled_radial_vector



    def fit_near_vertices(self, basis_proxy,basis_body,proxy_shapekey,current_body, proxy_threshold = 0.025):

        #basis_proxy = proxy in basis shape, without shapekey applied
        #proxy_shapekey = shapekey to modify as final result
        #basis_body = body in basis shape, without morphings and armature
        #current_body = current body shape, with morphing (but not armature) applied

        polygons_file = algorithms.get_template_polygons(current_body)
        polygons_path = os.path.join(self.data_path,"pgroups",polygons_file)
        valid_polygons_indxs = algorithms.load_json_data(polygons_path, "Subset of polygons for proxy fitting")

        basis_proxy_vertices = basis_proxy.data.vertices #In Blender obj.data = basis data
        basis_body_polygons = basis_body.data.polygons
        current_body_polygons = current_body.data.polygons

        if len(basis_body_polygons) == len(current_body_polygons):
            basis_body_tree = algorithms.kdtree_from_obj_polygons(basis_body, valid_polygons_indxs)

            for i,basis_proxy_vert in enumerate(basis_proxy_vertices):

                nearest_body_polygons_data = basis_body_tree.find_n(basis_proxy_vert.co, 25)
                #basis body vs basis proxy
                for body_polygons_data in nearest_body_polygons_data:
                    body_polygon_index = body_polygons_data[1]
                    body_polygon_dist = body_polygons_data[2] #distance basis_body - basis_proxy
                    body_polygon = basis_body_polygons[body_polygon_index]
                    if basis_proxy_vert.normal.dot(body_polygon.normal) > 0:
                        break

                if proxy_threshold > 0:
                    f_factor = 1 - ((body_polygon_dist - proxy_threshold)/proxy_threshold)
                    f_factor = min(f_factor,1)
                    f_factor = max(f_factor,0)
                else:
                    f_factor = 0

                basis_body_verts_coords = algorithms.get_polygon_vertices_coords(basis_body,body_polygon_index)
                p1 = basis_body_verts_coords[0]
                p2 = basis_body_verts_coords[1]
                p3 = basis_body_verts_coords[2]

                raw_body_verts_coords = algorithms.get_polygon_vertices_coords(current_body,body_polygon_index)
                p4 = raw_body_verts_coords[0]
                p5 = raw_body_verts_coords[1]
                p6 = raw_body_verts_coords[2]

                proxy_shapekey_vert = proxy_shapekey.data[i]
                fitted_vert = mathutils.geometry.barycentric_transform(basis_proxy_vert.co,p1,p2,p3,p4,p5,p6)

                proxy_shapekey_vert.co = proxy_shapekey_vert.co + f_factor*(fitted_vert-proxy_shapekey_vert.co)




    def fit_proxy_object(self,proxy_offset=0.0, proxy_threshold = 0.5, create_proxy_mask = False, transfer_w = True):
        scn = bpy.context.scene
        status, proxy, body = self.get_proxy_fitting_ingredients()
        if status == "OK":
            armat = algorithms.get_linked_armature(body)
            self.calibrate_proxy_object(proxy)
            self.reset_proxy_shapekey(proxy)#Always after calibration!

            proxy.matrix_world = body.matrix_world

            template_name = algorithms.get_template_model(body)
            mask_name = "mbastlab_mask_" + proxy.name

            algorithms.print_log_report("INFO","Fitting proxy {0}".format(proxy.name))
            selected_objs_names = algorithms.get_objects_selected_names()

            body_modfs_status = algorithms.get_object_modifiers_visibility(body)
            proxy_modfs_status = algorithms.get_object_modifiers_visibility(proxy)

            algorithms.disable_object_modifiers(proxy, ['ARMATURE','SUBSURF','MASK'])
            algorithms.disable_object_modifiers(body, ['ARMATURE','SUBSURF','MASK'])


            basis_body = algorithms.import_object_from_lib(self.templates_library, template_name, stop_import = False)

            proxy_shapekey = algorithms.new_shapekey(proxy,"mbastlab_proxyfit")


            self.fit_distant_vertices(proxy,basis_body,proxy_shapekey,body)

            self.fit_near_vertices(proxy,basis_body,proxy_shapekey,body,proxy_threshold)
            self.proxy_offset(proxy,basis_body,proxy_shapekey,body,proxy_offset)
            self.calculate_finishing_morph(proxy, "mbastlab_proxyfit")

            if create_proxy_mask:
                self.add_body_mask(body, proxy_shapekey, mask_name)
            else:
                self.remove_body_mask(body, mask_name)

            #algorithms.remove_mesh(basis_body_mesh, True)
            algorithms.remove_object(basis_body, True, True)

            armature_mod = self.add_proxy_armature_modfr(proxy, armat)

            if transfer_w == True:
                algorithms.remove_vertgroups_all(proxy)
                self.transfer_weights(body, proxy)

            algorithms.set_object_modifiers_visibility(proxy, proxy_modfs_status)
            algorithms.set_object_modifiers_visibility(body, body_modfs_status)
            self.disable_extra_armature_modfr(proxy)

            parameters = {"show_viewport":True}

            correct_smooth_mod = algorithms.new_modifier(proxy, self.corrective_modifier_name, 'CORRECTIVE_SMOOTH', parameters)


            for i in range(10):
                algorithms.move_up_modifier(proxy, correct_smooth_mod)

            for i in range(10):
                algorithms.move_up_modifier(proxy, armature_mod)


            for obj_name in selected_objs_names:
                algorithms.select_object_by_name(obj_name)





    def proxy_offset(self, basis_proxy,basis_body,proxy_shapekey,current_body,offset_factor):

        #basis_proxy = proxy in basis shape, without shapekey applied
        #proxy_shapekey = shapekey of actual, "real" proxy shape to modify as final result
        #basis_body = body in basis shape, without morphings and armature
        #current_body = raw copy of current body shape, with morphing and armature applied

        basis_proxy_vertices = basis_proxy.data.vertices
        basis_body_polygons = basis_body.data.polygons
        current_body_polygons = current_body.data.polygons

        polygons_file = algorithms.get_template_polygons(current_body)
        polygons_path = os.path.join(self.data_path,"pgroups",polygons_file)
        valid_polygons_indxs = algorithms.load_json_data(polygons_path, "Subset of polygons for proxy fitting")

        if len(basis_body_polygons) == len(current_body_polygons):

            #current_body_tree = algorithms.kdtree_from_mesh_polygons(current_body)
            current_body_tree = algorithms.kdtree_from_obj_polygons(current_body, valid_polygons_indxs)

            for i in range(len(basis_proxy_vertices)):
                proxy_shapekey_vert = proxy_shapekey.data[i]
                nearest_body_polygons_data = current_body_tree.find_n(proxy_shapekey_vert.co, 10)
                body_normals = []

                #raw body vs proxy shapekey
                for body_polygons_data in nearest_body_polygons_data:
                    body_polygon_index = body_polygons_data[1]
                    body_polygon_dist = body_polygons_data[2] #distance body-proxy
                    body_polygon = current_body_polygons[body_polygon_index]
                    body_polygon_normal = body_polygon.normal
                    body_polygon_center = body_polygon.center
                    body_normals.append(body_polygon_normal)

                offset_vector = mathutils.Vector((0,0,0))
                for n in body_normals:
                    offset_vector += n

                if len(body_normals) != 0:
                    offset_vector = offset_vector/len(body_normals)
                proxy_shapekey_vert.co = proxy_shapekey_vert.co + offset_vector*offset_factor


    def add_body_mask(self, body, proxy_shapekey, mask_name, proxy_threshold = 0.025):

        #basis_proxy_mesh = proxy in basis shape, without shapekey applied
        #proxy_shapekey = shapekey of actual, "real" proxy shape as it is after the fitting
        #basis_body_mesh = body in basis shape, without morphings and armature
        #body = actual body to modify as final result

        polygons_file = algorithms.get_template_polygons(body)
        polygons_path = os.path.join(self.data_path,"pgroups",polygons_file)
        valid_polygons_indxs = algorithms.load_json_data(polygons_path, "Subset of polygons for proxy fitting")
        body_tree = algorithms.kdtree_from_obj_polygons(body, valid_polygons_indxs)


        algorithms.remove_vertgroup(body, mask_name)

        masked_verts_idx = set()
        mask_group = algorithms.new_vertgroup(body, mask_name)

        for actual_vert in proxy_shapekey.data:

            nearest_body_polygon_data = body_tree.find(actual_vert.co)
            involved_vertices = set()
            dist_proxy_body = nearest_body_polygon_data[2]
            body_polygon_idx = nearest_body_polygon_data[1]
            body_polygon = body.data.polygons[body_polygon_idx]

            #body_polygon.select = True

            if dist_proxy_body < proxy_threshold:
                for v_idx in body_polygon.vertices:
                    masked_verts_idx.add(v_idx)

        algorithms.less_boundary_verts(body, masked_verts_idx, iterations=2)

        for i,vert in enumerate(body.data.vertices):
            if i in masked_verts_idx:
                mask_group.add([vert.index], 1.0, 'REPLACE')

        #self.add_mask_modifier(body, mask_name)
        parameters = {"vertex_group":mask_name,"invert_vertex_group":True}
        algorithms.new_modifier(body, mask_name, 'MASK', parameters)

    def remove_body_mask(self, body, mask_name):
        algorithms.remove_modifier(body, mask_name)
        algorithms.remove_vertgroup(body, mask_name)


    def calculate_finishing_morph(self, obj, shapekey_name = "Fitted", threshold=0.2):

        shape_to_finish = algorithms.get_shapekey(obj, shapekey_name)
        if shape_to_finish:
            boundary_verts = algorithms.get_boundary_verts(obj)

            for polyg in obj.data.polygons:
                polyg_base_verts = []
                polyg_current_verts = []
                for vert_index in polyg.vertices:
                    polyg_base_verts.append(obj.data.vertices[vert_index].co)
                    polyg_current_verts.append(shape_to_finish.data[vert_index].co)
                base_factors = algorithms.polygon_forma(polyg_base_verts)
                current_factors = algorithms.polygon_forma(polyg_current_verts)

                deformations = []
                for idx in range(len(current_factors)):
                    deformations.append(abs(current_factors[idx]-base_factors[idx]))
                max_deform = max(deformations)/2.0

                if max_deform > threshold:
                    for idx in polyg.vertices:
                        b_verts = boundary_verts[str(idx)]
                        average = mathutils.Vector((0, 0, 0))
                        for vidx in b_verts:
                            coords = shape_to_finish.data[vidx].co
                            average += coords
                        average = average/len(b_verts)
                        corrected_position = shape_to_finish.data[idx].co*(1.0 - max_deform) + average*max_deform
                        shape_to_finish.data[idx].co = corrected_position # + fitted_forma.vertices[idx].normal*difference.length
                        #obj.data.vertices[idx].select = True



