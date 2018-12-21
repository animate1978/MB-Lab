# ManuelbastioniLAB - Copyright (C) 2015-2018 Manuel Bastioni
# Official site: www.manuelbastioni.com
# MB-Lab fork website : https://github.com/animate1978/MB-Lab
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import mathutils
import itertools
import random
import time
import os
import bpy
import json
import array
from . import settings


def print_log_report(level_in = -1, text_to_write = "An Error occur"):
    levels = ["INFO", "DEBUG", "WARNING", "ERROR", "CRITICAL"]
    if type(level_in) is str:
        log_level = levels.index(level_in)
        level_mess = level_in
    # Rewritten to allow use of int control. What's the point of a print log function if you're
    # just going to rewrite the control code all the time?!
    if type(level_in) is int and -1 <= level_in <= levels.__len__():
        if level_in == -1:
            level_in = 3;
        log_level = level_in
        level_mess = levels[level_in]

    if log_level >= settings.debug_level:
        print(level_mess + ": " + text_to_write)

    # log_level = 0
    # levels = {"INFO": 0, "DEBUG": 1, "WARNING": 2, "ERROR": 3, "CRITICAL": 4, }
    # if level in levels:
    #     log_level = levels[level]
    # if log_level >= settings.debug_level:
    #     print(level + ": " + text_to_write)


def is_writeable(filepath, set_write=True):
    writeable = False
    try:
        test_writing = open(filepath, 'w')
        test_writing.close()
        if set_write:
            writeable = True
    except:
        print("WARNING: Writing permission denied for {0}".format(filepath))
    return writeable

# TODO Make
def get_data_path():
    print_log_report("INFO", "Looking for the retarget data in the folder {0}...".format(settings.data_path))
    if os.path.isdir(settings.data_path):
        return settings.data_path
    else:
        print_log_report("CRITICAL", "Tools data not found. Please check your Blender addons directory.")
        return None
    # global data_path
    # if data_path:
    #     print_log_report("INFO", "Looking for the retarget data in the folder {0}...".format(simple_path(data_path)))
    #     return data_path
    # else:
    #     addon_directory = os.path.dirname(os.path.realpath(__file__))
    #     data_dir = os.path.join(addon_directory, "data")
    #     print_log_report("INFO", "Looking for the retarget data in the folder {0}...".format(simple_path(data_dir)))
    #     if os.path.isdir(data_dir):
    #         data_path = data_dir
    #         return data_dir
    #     else:
    #         print_log_report("CRITICAL", "Tools data not found. Please check your Blender addons directory.")
    #         return None

# def get_data_path():
#     addon_directory = os.path.dirname(os.path.realpath(__file__))
#     data_dir = os.path.join(addon_directory, "data")
#     print_log_report("INFO", "Looking for the retarget data in the folder {0}...".format(simple_path(data_dir)))
#     if os.path.isdir(data_dir):
#         return data_dir
#     else:
#         print_log_report("CRITICAL", "Tools data not found. Please check your Blender addons directory.")
#         return None


def get_configuration():
    data_path = get_data_path()
    if data_path:
        configuration_path = os.path.join(data_path, "characters_config.json")
        if os.path.isfile(configuration_path):
            return load_json_data(configuration_path, "Characters definition")
        else:
            print_log_report("CRITICAL",
                             "Configuration database not found. Please check your Blender addons directory.")
            return None


def get_blendlibrary_path():
    data_path = get_data_path()
    if data_path:
        return os.path.join(data_path, "humanoid_library.blend")
    else:
        print_log_report("CRITICAL", "Models library not found. Please check your Blender addons directory.")
        return None


def simple_path(input_path, use_basename=False, max_len=5000):
    """
    Return the last part of long paths
    """
    if use_basename:
        return os.path.basename(input_path)
    else:
        if len(input_path) > max_len:
            return "[Trunked].." + input_path[len(input_path) - max_len:]
        else:
            return os.path.relpath(input_path, os.path.dirname(os.path.realpath(__file__)))


def json_booleans_to_python(value):
    if value == 0:
        return True
    return False


def quick_dist(p_1, p_2):
    return ((p_1[0] - p_2[0]) ** 2) + ((p_1[1] - p_2[1]) ** 2) + ((p_1[2] - p_2[2]) ** 2)


def full_dist(vert1, vert2, axis="ALL"):
    v1 = mathutils.Vector(vert1)
    v2 = mathutils.Vector(vert2)

    if axis not in ["X", "Y", "Z"]:
        v3 = v1 - v2
        return v3.length
    if axis == "X":
        return abs(v1[0] - v2[0])
    if axis == "Y":
        return abs(v1[1] - v2[1])
    if axis == "Z":
        return abs(v1[2] - v2[2])


def exists_database(lib_path):
    result = False
    if simple_path(lib_path) != "":
        if os.path.isdir(lib_path):
            if len(os.listdir(lib_path)) > 0:
                for database_file in os.listdir(lib_path):
                    p_item, extension = os.path.splitext(database_file)
                    if "json" in extension or "bvh" in extension:
                        result = True
                    else:
                        print_log_report("WARNING", "Unknown file extension in {0}".format(simple_path(lib_path)))

        else:
            print_log_report("WARNING", "data path {0} not found".format(simple_path(lib_path)))
    return result


def length_of_strip(vertices_coords, indices, axis="ALL"):
    strip_length = 0
    for x in range(len(indices) - 1):
        v1 = vertices_coords[indices[x]]
        v2 = vertices_coords[indices[x + 1]]
        strip_length += full_dist(v1, v2, axis)
    return (strip_length)


def function_modifier_a(val_x):
    val_y = 0.0
    if val_x > 0.5:
        val_y = 2 * val_x - 1
    return val_y


def function_modifier_b(val_x):
    val_y = 0.0
    if val_x < 0.5:
        val_y = 1 - 2 * val_x
    return val_y


def bounding_box(verts_coo, indices, roundness=4):
    val_x, val_y, val_z = [], [], []
    for idx in indices:
        if len(verts_coo) > idx:
            val_x.append(verts_coo[idx][0])
            val_y.append(verts_coo[idx][1])
            val_z.append(verts_coo[idx][2])
        else:
            print_log_report("WARNING",
                             "Error in calculating bounding box: index {0} not in verts_coo (len(verts_coo) = {1})".format(
                                 idx, len(verts_coo)))
            return None

    box_x = round(max(val_x) - min(val_x), roundness)
    box_y = round(max(val_y) - min(val_y), roundness)
    box_z = round(max(val_z) - min(val_z), roundness)

    return (box_x, box_y, box_z)


def get_bounding_box(v_coords):
    if len(v_coords) > 0:

        val_x, val_y, val_z = [], [], []
        for coord in v_coords:
            val_x.append(coord[0])
            val_y.append(coord[1])
            val_z.append(coord[2])

        box_x = max(val_x) - min(val_x)
        box_y = max(val_y) - min(val_y)
        box_z = max(val_z) - min(val_z)

        return (box_x, box_y, box_z)

    return None


def load_bbox_data(filepath):
    bboxes = []
    database_file = open(filepath, "r")
    for line in database_file:
        bboxes.append(line.split())
    database_file.close()

    bbox_data_dict = {}
    for x_data in bboxes:
        idx = x_data[0]
        idx_x_max = int(x_data[1])
        idx_y_max = int(x_data[2])
        idx_z_max = int(x_data[3])
        idx_x_min = int(x_data[4])
        idx_y_min = int(x_data[5])
        idx_z_min = int(x_data[6])

        bbox_data_dict[idx] = [
            idx_x_max, idx_y_max,
            idx_z_max, idx_x_min,
            idx_y_min, idx_z_min]
    return bbox_data_dict


def smart_combo(prefix, morph_values):
    debug1 = False
    debug2 = False
    tags = []
    names = []
    weights = []
    max_morph_values = []

    # Compute the combinations and get the max values
    for v_data in morph_values:
        tags.append(["max", "min"])
        max_morph_values.append(max(v_data))
    for n_data in itertools.product(*tags):
        names.append(prefix + "_" + '-'.join(n_data))

    # Compute the weight of each combination
    for n_data in itertools.product(*morph_values):
        weights.append(sum(n_data))

    factor = max(max_morph_values)
    best_val = max(weights)
    toll = 1.5

    # Filter on bestval and calculate the normalize factor
    summ = 0.0
    for i in range(len(weights)):
        weights[i] = max(0, weights[i] - best_val / toll)
        summ += weights[i]

    # Normalize using summ
    if summ != 0:
        for i in range(len(weights)):
            weights[i] = factor * (weights[i] / summ)

    if debug1:
        print("BESTVAL = {0}".format(best_val))
        print("SUM = {0}".format(summ))
        print("AVERAGE = {0}".format(factor))
    if debug2:
        print("MORPHINGS:")
        for i in range(len(names)):
            if weights[i] != 0:
                print(names[i], weights[i])
    return (names, weights)


def is_excluded(property_name, excluded_properties):
    for excluded_property in excluded_properties:
        if excluded_property in property_name:
            return True
    return False


def generate_parameter(val, random_value, preserve_phenotype=False):
    if preserve_phenotype:
        if val > 0.5:
            if val > 0.8:
                new_value = 0.8 + 0.2 * random.random()
            else:
                new_value = 0.5 + random.random() * random_value
        else:
            if val < 0.2:
                new_value = 0.2 * random.random()
            else:
                new_value = 0.5 - random.random() * random_value
    else:
        if random.random() > 0.5:
            new_value = min(1.0, 0.5 + random.random() * random_value)
        else:
            new_value = max(0.0, 0.5 - random.random() * random_value)
    return new_value


def polygon_forma(list_of_verts):
    form_factors = []
    for idx in range(len(list_of_verts)):
        index_a = idx
        index_b = idx - 1
        index_c = idx + 1
        if index_c > len(list_of_verts) - 1:
            index_c = 0

        p_a = list_of_verts[index_a]
        p_b = list_of_verts[index_b]
        p_c = list_of_verts[index_c]

        v_1 = p_b - p_a
        v_2 = p_c - p_a

        v_1.normalize()
        v_2.normalize()

        factor = v_1.dot(v_2)
        form_factors.append(factor)
    return form_factors


def average_center(verts_coords):
    n_verts = len(verts_coords)
    bcenter = mathutils.Vector((0.0, 0.0, 0.0))
    if n_verts != 0:
        for v_coord in verts_coords:
            bcenter += v_coord
        bcenter = bcenter / n_verts
    return bcenter


def linear_interpolation_y(xa, xb, ya, yb, y):
    return (((xa - xb) * y) + (xb * ya) - (xa * yb)) / (ya - yb)


def correct_morph(base_form, current_form, morph_deltas, bboxes):
    time1 = time.time()
    new_morph_deltas = []
    for d_data in morph_deltas:

        idx = d_data[0]

        if str(idx) in bboxes:
            indices = bboxes[str(idx)]
            current_bounding_box = bounding_box(current_form, indices)
            if current_bounding_box:
                base_bounding_box = bounding_box(base_form, indices)
                if base_bounding_box:

                    if base_bounding_box[0] != 0:
                        scale_x = current_bounding_box[0] / base_bounding_box[0]
                    else:
                        scale_x = 1

                    if base_bounding_box[1] != 0:
                        scale_y = current_bounding_box[1] / base_bounding_box[1]
                    else:
                        scale_y = 1

                    if base_bounding_box[2] != 0:
                        scale_z = current_bounding_box[2] / base_bounding_box[2]
                    else:
                        scale_z = 1

                    delta_x = d_data[1][0] * scale_x
                    delta_y = d_data[1][1] * scale_y
                    delta_z = d_data[1][2] * scale_z

                    newd = mathutils.Vector((delta_x, delta_y, delta_z))
                    new_morph_deltas.append([idx, newd])
        else:
            new_morph_deltas.append(d_data)
            print_log_report("WARNING", "Index {0} not in bounding box database".format(idx))
    print_log_report("INFO", "Morphing corrected in {0} secs".format(time.time() - time1))
    return new_morph_deltas


def check_version(m_vers, min_version=(1, 5, 0)):
    version_check = False

    # m_vers can be a list, tuple, IDfloatarray or str
    # so it must be converted in a list.
    if type(m_vers) is not str:
        m_vers = list(m_vers)

    mesh_version = str(m_vers)
    mesh_version = mesh_version.replace(' ', '')
    mesh_version = mesh_version.strip("[]()")
    if len(mesh_version) < 5:
        print_log_report("WARNING", "The current humanoid has wrong format for version")
        return False

    mesh_version = (float(mesh_version[0]), float(mesh_version[2]), float(mesh_version[4]))
    if mesh_version > min_version:
        return True
    else:
        return False

    return version_check


def looking_for_humanoid_obj():
    """
        Looking for a mesh that is OK for the lab
        """
    print_log_report("INFO", "Looking for an humanoid object...")
    if bpy.app.version < (2, 78, 0):
        msg = "Sorry, the lab requires official Blender 2.78 or 2.79."
        print_log_report("WARNING", msg)
        return ("ERROR", msg)

    if bpy.app.version >= (2, 80, 0):
        msg = "Sorry, this version of lab does no work with Blender 2.8"
        print_log_report("WARNING", msg)
        return ("ERROR", msg)

    if bpy.app.version > (2, 79, 0):
        msg = "The lab is not designed to work with unstable Blender build {0}".format(str(bpy.app.version))
        print_log_report("WARNING", msg)
        # return("ERROR",msg)

    human_obj = None
    name = ""
    for obj in bpy.data.objects:
        if obj.type == "MESH":
            if "manuellab_vers" in get_object_keys(obj):
                if check_version(obj["manuellab_vers"]):
                    human_obj = obj
                    name = human_obj.name
                    break

    if not human_obj:
        msg = "No lab humanoids in the scene"
        print_log_report("INFO", msg)
        return ("NO_OBJ", msg)

    if not ("manuellab_id" in get_object_keys(obj)):
        msg = "Character created with old lab version"
        print_log_report("INFO", "Character type not found in obj properties")
        return ("ERROR", msg)

    if not ("manuellab_rig" in get_object_keys(obj)):
        msg = "Character created with old lab version"
        print_log_report("INFO", "Rig type not found in obj properties")
        return ("ERROR", msg)

    if has_shapekeys(obj):
        msg = "The lab cannot edit a character with shapekeys"
        print_log_report("WARNING", msg)
        return ("ERROR", msg)

    return ("FOUND", name)


def is_string_in_string(b_string, b_name):
    if b_string and b_name:
        if b_string.lower() in b_name.lower():
            return True
    return False


def is_too_much_similar(string1, string2, val=2):
    s1 = set(string1)
    s2 = set(string2)

    if len(s1) > len(s2):
        threshold = len(s1) - val
    else:
        threshold = len(s2) - val

    if len(s1.intersection(s2)) > threshold:
        return True
    return False


def is_in_list(list1, list2, position="ANY"):
    for element1 in list1:
        for element2 in list2:
            if position == "ANY":
                if element1.lower() in element2.lower():
                    return True
            if position == "START":
                if element1.lower() in element2[:len(element1)].lower():
                    return True
            if position == "END":
                if element1.lower() in element2[len(element1):].lower():
                    return True
    return False


def load_json_data(json_path, description=None):
    if os.path.isfile(json_path):
        time1 = time.time()
        j_file = open(json_path, "r")
        j_database = None
        try:
            j_database = json.load(j_file)
        except:
            print_log_report("WARNING", "Errors in json file: {0}".format(simple_path(json_path)))
        j_file.close()
        if not description:
            print_log_report("INFO",
                             "Json database {0} loaded in {1} secs".format(simple_path(json_path), time.time() - time1))
        else:
            print_log_report("INFO", "{0} loaded from {1} in {2} secs".format(description, simple_path(json_path),
                                                                              time.time() - time1))
        return j_database
    else:
        if simple_path(json_path) != "":
            print_log_report("WARNING", "File not found: {0}".format(simple_path(json_path)))
        return None


def less_boundary_verts(obj, verts_idx, iterations=1):
    polygons = obj.data.polygons
    vertices = obj.data.vertices

    while iterations != 0:
        verts_to_remove = set()
        for poly in polygons:
            poly_verts_idx = poly.vertices
            for v_idx in poly_verts_idx:
                if v_idx not in verts_idx:
                    for v_idx in poly_verts_idx:
                        verts_to_remove.add(v_idx)
                    break
        verts_idx.difference_update(verts_to_remove)
        iterations -= 1


def kdtree_from_mesh_polygons(mesh):
    polygons = mesh.polygons
    research_tree = mathutils.kdtree.KDTree(len(polygons))
    for polyg in polygons:
        research_tree.insert(polyg.center, polyg.index)
    research_tree.balance()
    return research_tree


def kdtree_from_obj_polygons(obj, indices_of_polygons_subset=None):
    polygons = []
    if indices_of_polygons_subset != None:
        for idx in indices_of_polygons_subset:
            polygons.append(obj.data.polygons[idx])
    else:
        polygons = obj.data.polygons
    research_tree = mathutils.kdtree.KDTree(len(polygons))
    for polyg in polygons:
        research_tree.insert(polyg.center, polyg.index)
    research_tree.balance()
    return research_tree


def kdtree_from_mesh_vertices(mesh):
    vertices = mesh.vertices
    research_tree = mathutils.kdtree.KDTree(len(vertices))
    for idx, vert in enumerate(vertices):
        research_tree.insert(vert.co, idx)
    research_tree.balance()
    return research_tree


def import_mesh_from_lib(lib_filepath, name):
    existing_mesh_names = collect_existing_meshes()
    append_mesh_from_library(lib_filepath, [name])
    new_mesh = get_newest_mesh(existing_mesh_names)
    return new_mesh


def get_scene_modifiers_status():
    scene_viewport_status = {}
    for obj in bpy.data.objects:
        obj_name = obj.name
        scene_viewport_status[obj_name] = get_object_modifiers_visibility(obj)
    return scene_viewport_status


def get_polygon_vertices_coords(obj_data, index):
    if is_object(obj_data):
        polygon = obj_data.data.polygons[index]
    elif is_mesh(obj_data):
        polygon = obj_data.polygons[index]

    polygon_vindex = polygon.vertices
    verts_coords = []

    for i in polygon_vindex:
        if is_object(obj_data):
            v = obj_data.data.vertices[i]
        elif is_mesh(obj_data):
            v = obj_data.vertices[i]
        verts_coords.append(v.co)

    return verts_coords


def remove_mesh(mesh, remove_materials=False):
    if remove_materials:
        for material in mesh.materials:
            if material:
                bpy.data.materials.remove(material, do_unlink=True)
    bpy.data.meshes.remove(mesh, do_unlink=True)


def remove_object(obj, delete_mesh=False, delete_materials=False):
    if obj:
        mesh_to_remove = None
        if obj.type == 'MESH':
            mesh_to_remove = obj.data

        bpy.data.objects.remove(obj, do_unlink=True)
        if delete_mesh:
            if mesh_to_remove != None:
                remove_mesh(mesh_to_remove, delete_materials)


def set_object_layer(obj, n):
    if obj:
        if hasattr(obj, 'layers'):
            n_layer = len(obj.layers)
            for i in range(n_layer):
                obj.layers[i] = False
            if n in range(n_layer):
                obj.layers[n] = True


def normal_from_points(points):
    if len(points) == 4:
        plane_norm = mathutils.geometry.normal(points[0], points[1], points[2], points[3])
    else:
        plane_norm = mathutils.geometry.normal(points[0], points[1], points[2])
    return plane_norm


def apply_object_matrix(obj):
    negative_matrix = False
    for val in obj.scale:
        if val < 0:
            negative_matrix = True

    m = obj.matrix_world
    obj.data.transform(m)
    if negative_matrix and obj.type == 'MESH':
        obj.data.flip_normals()
    obj.matrix_world = mathutils.Matrix()


def set_scene_modifiers_status_by_type(modfr_type, visib):
    for obj in bpy.data.objects:
        for modfr in obj.modifiers:
            if modfr.type == modfr_type:
                set_modifier_viewport(modfr, visib)


def set_scene_modifiers_status(visib, status_data=None):
    if not status_data:
        for obj in bpy.data.objects:
            for modfr in obj.modifiers:
                set_modifier_viewport(modfr, visib)
    else:
        for obj in bpy.data.objects:
            obj_name = obj.name
            if obj_name in status_data:
                modifier_status = status_data[obj_name]
                set_object_modifiers_visibility(obj, modifier_status)


def disable_object_modifiers(obj, types_to_disable=[]):
    for modfr in obj.modifiers:
        modifier_type = modfr.type
        if modifier_type in types_to_disable:
            set_modifier_viewport(modfr, False)
            print_log_report("INFO",
                             "Modifier {0} of {1} can create unpredictable fitting results. The lab disabled it".format(
                                 modifier_type, obj.name))
        elif types_to_disable == []:
            set_modifier_viewport(modfr, False)
            print_log_report("INFO",
                             "Modifier {0} of {1} can create unpredictable fitting results. The lab disabled it".format(
                                 modifier_type, obj.name))


def get_object_modifiers_visibility(obj):
    # Store the viewport visibility for all modifiers of the obj
    obj_modifiers_status = {}
    for modfr in obj.modifiers:
        modfr_name = get_modifier_name(modfr)
        modfr_status = get_modifier_viewport(modfr)
        if modfr_name:
            obj_modifiers_status[modfr_name] = modfr_status
    return obj_modifiers_status


def set_object_modifiers_visibility(obj, modifier_status):
    # Store the viewport visibility for all modifiers of the obj
    for modfr in obj.modifiers:
        modfr_name = get_modifier_name(modfr)
        if modfr_name in modifier_status:
            set_modifier_viewport(modfr, modifier_status[modfr_name])


def get_modifier(obj, modifier_name):
    if modifier_name in obj.modifiers:
        return obj.modifiers[modifier_name]


def get_modifier_name(modfr):
    if hasattr(modfr, 'name'):
        return modfr.name
    return None


def apply_modifier(obj, modifier):
    modifier_name = get_modifier_name(modifier)
    if modifier_name in obj.modifiers:
        set_active_object(obj)
        try:
            bpy.ops.object.modifier_apply(apply_as='DATA', modifier=modifier_name)
        except:
            print_log_report("WARNING", "Problems in applying {0}. Is the modifier disabled?".format(modifier_name))


def move_up_modifier(obj, modifier):
    modifier_name = get_modifier_name(modifier)
    set_active_object(obj)
    for n in range(len(obj.modifiers)):
        bpy.ops.object.modifier_move_up(modifier=modifier_name)


def move_down_modifier(obj, modifier):
    modifier_name = get_modifier_name(modifier)
    set_active_object(obj)
    for n in range(len(obj.modifiers)):
        bpy.ops.object.modifier_move_down(modifier=modifier_name)


def remove_modifier(obj, modifier_name):
    print("Removing ", modifier_name)
    if modifier_name in obj.modifiers:
        obj.modifiers.remove(obj.modifiers[modifier_name])


def disable_modifier(modfr):
    print("Disable ", modfr.name)
    if hasattr(modfr, 'show_viewport'):
        modfr.show_viewport = False
    if hasattr(modfr, 'show_render'):
        modfr.show_render = False
    if hasattr(modfr, 'show_in_editmode'):
        modfr.show_in_editmode = False
    if hasattr(modfr, 'show_on_cage'):
        modfr.show_on_cage = False


def get_modifier_viewport(modfr):
    if hasattr(modfr, 'show_viewport'):
        return modfr.show_viewport
    return None


def set_modifier_viewport(modfr, value):
    if hasattr(modfr, 'show_viewport'):
        modfr.show_viewport = value


def new_modifier(obj, name, modifier_type, parameters):
    if name in obj.modifiers:
        print_log_report("INFO", "Modifier {0} already present in {1}".format(modifier_type, obj.name))
        return obj.modifiers[name]
    new_modifier = obj.modifiers.new(name, modifier_type)
    for parameter, value in parameters.items():
        if hasattr(new_modifier, parameter):
            try:
                setattr(new_modifier, parameter, value)
            except AttributeError:
                print_log_report("INFO", "Setattr failed for attribute '{0}' of modifier {1}".format(parameter, name))
    return new_modifier


# def set_modifier_parameter(modifier, parameter, value):  # UNUSED
#     if hasattr(modifier, parameter):
#         try:
#             setattr(modifier, parameter, value)
#         except AttributeError:
#             print_log_report("INFO",
#                              "Setattr failed for attribute '{0}' of modifier {1}".format(parameter, modifier_name))


def get_object_materials(obj):
    if obj.data.materials:
        return obj.data.materials
    return []


def select_and_change_mode(obj, obj_mode):
    deselect_all_objects()
    if obj:
        obj.select = True
        set_active_object(obj)
        set_object_visible(obj)
        try:
            bpy.ops.object.mode_set(mode=obj_mode)
            print_log_report("DEBUG", "Select and change mode of {0} = {1}".format(obj.name, obj_mode))
        except:
            print_log_report("WARNING", "Can't change the mode of {0} to {1}.".format(obj.name, obj_mode))


def get_selected_objs_names():
    return [obj.name for obj in bpy.context.selected_objects]


def select_object_by_name(name):
    obj = get_object_by_name(name)
    if obj:
        obj.select = True


def set_selected_objs_by_name(names):
    for name in names:
        if name in bpy.data.objects:
            bpy.data.objects[name].select = True


def get_active_object():
    return bpy.context.scene.objects.active


def deselect_all_objects():
    for obj in bpy.data.objects:
        obj.select = False


def set_active_object(obj):
    if obj:
        bpy.context.scene.objects.active = obj


def get_object_by_name(name):
    if name in bpy.data.objects:
        return bpy.data.objects[name]
    return None


def is_object(obj):
    if type(obj) == bpy.types.Object:
        return True
    return False


def is_mesh(obj):
    if type(obj) == bpy.types.Mesh:
        return True
    return False


def get_objects_selected_names():
    selected_objects = []
    for obj in bpy.context.selected_objects:
        if hasattr(obj, 'name'):
            selected_objects.append(obj.name)
    return selected_objects


def get_deforming_armature(obj):
    if obj:
        if obj.type == 'MESH':
            for modf in obj.modifiers:
                if modf.type == 'ARMATURE':
                    return modf.object


def apply_object_transformation(obj):
    if obj:
        selected_objs = get_selected_objs_names()
        active_obj = get_active_object()
        if active_obj:
            active_mode = active_obj.mode
        obj_mode = obj.mode

        select_and_change_mode(obj, 'OBJECT')
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        select_and_change_mode(obj, obj_mode)

        deselect_all_objects()
        set_selected_objs_by_name(selected_objs)
        if active_obj:
            set_active_object(active_obj)
            bpy.ops.object.mode_set(mode=active_mode)


def collect_existing_objects():
    existing_obj_names = []
    for obj in bpy.data.objects:
        name = obj.name
        if name:
            existing_obj_names.append(name)
    return existing_obj_names


def get_newest_object(existing_obj_names):
    for obj in bpy.data.objects:
        name = obj.name
        if name not in existing_obj_names:
            return get_object_by_name(name)
    return None


def get_selected_gender():
    obj = get_active_body()
    template = get_template_model(obj)
    if template != None:
        if "_female" in template:
            return "FEMALE"
        if "_male" in template:
            return "MALE"
    return "NONE"


def identify_template(obj):
    if obj:
        if obj.type == 'MESH':
            verts = obj.data.vertices
            polygons = obj.data.polygons
            config_data = get_configuration()
            # TODO error messages
            if verts != None:
                if polygons != None:
                    n_verts = len(verts)
                    n_polygons = len(polygons)
                    for template in config_data["templates_list"]:
                        n_verts2 = config_data[template]["vertices"]
                        n_polygons2 = config_data[template]["faces"]
                        if n_verts2 == n_verts:
                            if n_polygons2 == n_polygons:
                                return template
    return None


def get_template_model(obj):
    template = identify_template(obj)
    config_data = get_configuration()
    if template != None:
        return config_data[template]["template_model"]
    return None


def get_template_polygons(obj):
    template = identify_template(obj)
    config_data = get_configuration()
    if template != None:
        return config_data[template]["template_polygons"]
    return None


def is_a_lab_character(obj):
    if get_template_model(obj) != None:
        return True
    return False


def get_active_body():
    config_data = get_configuration()
    obj = get_active_object()
    if obj:
        if obj.type == 'MESH':
            return obj
        if obj.type == 'ARMATURE':
            if obj.children:
                for c_obj in obj.children:
                    obj_id = get_template_model(c_obj)
                    if obj_id != None:
                        return c_obj
    return None


def is_IK_armature(self, armature=None):
    if not armature:
        armature = get_active_armature()
        if armature:
            bones = get_bones(armature)
            for b in bones:
                if 'IK' in b.name:
                    return True
    return False


def get_object_parent(obj):
    if obj:
        if hasattr(obj, "parent"):
            return obj.parent
    return None


def get_active_armature():
    active_obj = get_active_object()
    parent_object = get_object_parent(active_obj)
    if active_obj:
        if active_obj.type == 'ARMATURE':
            return active_obj
        if active_obj.type == 'MESH':
            if parent_object:
                if parent_object.type == 'ARMATURE':
                    return parent_object
            else:
                deforming_armature = get_deforming_armature(active_obj)
                if deforming_armature:
                    return deforming_armature
    return None


def get_linked_armature(obj):
    if obj.type == 'MESH':
        for modfr in obj.modifiers:
            if modfr.type == 'ARMATURE':
                return modfr.object
    return None


def raw_mesh_from_object(obj, apply_modifiers=False):
    if obj.type == 'MESH':
        return obj.to_mesh(bpy.context.scene, apply_modifiers, 'PREVIEW')
    return None


def get_all_bones_z_axis(armature):
    armature_z_axis = {}
    select_and_change_mode(armature, 'EDIT')
    source_edit_bones = get_edit_bones(armature)
    if source_edit_bones:
        for e_bone in source_edit_bones:
            armature_z_axis[e_bone.name] = e_bone.z_axis.copy()
    select_and_change_mode(armature, 'OBJECT')
    return armature_z_axis


def reset_bone_rot(p_bone):
    # TODO: check pose mode
    if p_bone.rotation_mode == 'QUATERNION':
        p_bone.rotation_quaternion = [1.0, 0.0, 0.0, 0.0]
    elif p_bone.rotation_mode == 'AXIS_ANGLE':
        p_bone.rotation_axis_angle = [0.0, 0.0, 1.0, 0.0]
    else:
        p_bone.rotation_euler = [0.0, 0.0, 0.0]


def collect_existing_meshes():
    existing_mesh_names = []
    for mesh in bpy.data.meshes:
        existing_mesh_names.append(mesh.name)
    return existing_mesh_names


def get_mesh(name):
    if name in bpy.data.meshes:
        return bpy.data.meshes[name]
    else:
        return None


def get_newest_mesh(existing_mesh_names):
    for mesh in bpy.data.meshes:
        if mesh.name not in existing_mesh_names:
            return get_mesh(mesh.name)
    return None


def new_shapekey(obj, shapekey_name, slider_min=0, slider_max=1.0, value=1.0):
    # TODO a new shapekey should overwrite the existing one
    if shapekey_name in get_shapekeys_names(obj):
        shapekey = get_shapekey(obj, shapekey_name)
    else:
        shapekey = obj.shape_key_add(name=shapekey_name, from_mix=False)
    shapekey.slider_min = slider_min
    shapekey.slider_max = slider_max
    shapekey.value = value
    obj.use_shape_key_edit_mode = True
    return shapekey


def new_shapekey_from_current_vertices(obj, shapekey_name):
    shapekey = new_shapekey(obj, shapekey_name)
    for i in range(len(obj.data.vertices)):
        shapekey.data[i].co = obj.data.vertices[i].co
    return shapekey


def reset_shapekeys(obj):
    if has_shapekeys(obj):
        for sk in obj.data.shape_keys.key_blocks:
            sk.value = 0.0


def get_object_keys(obj):
    if obj:
        return obj.keys()
    return None


def get_vertgroup_verts(obj, vgroup_name):
    g = get_vertgroup_by_name(obj, vgroup_name)
    verts_idxs = []
    if g != None:
        for i in range(len(obj.data.vertices)):
            try:
                if g.weight(i) > 0:
                    verts_idxs.append(i)
            except:
                pass
                # Blender return an error if the vert is not in group
    return verts_idxs


def set_object_visible(obj):
    if obj:
        print_log_report("DEBUG", "Turn the visibility of {0} ON".format(obj.name))
        obj.hide = False

        # bpy.context.scene.layers = obj.layers in some cases this return DAG zero error (with old depsgraph)!
        n = bpy.context.scene.active_layer
        set_object_layer(obj, n)  # TODO not perfect because it changes the layer


def load_vertices_database(vertices_path):
    vertices = []
    verts = load_json_data(vertices_path, "Vertices data")
    if verts:
        for vert_co in verts:
            vertices.append(mathutils.Vector(vert_co))
    return vertices


def set_verts_coords_from_file(obj, vertices_path):
    new_vertices = load_vertices_database(vertices_path)
    if obj:
        if len(new_vertices) == len(obj.data.vertices):
            for i, vert in enumerate(obj.data.vertices):
                vert.co = new_vertices[i]


def generate_items_list(folderpath, file_type="json"):
    items_list = []
    if os.path.isdir(folderpath):
        for database_file in os.listdir(folderpath):
            the_item, extension = os.path.splitext(database_file)
            if file_type in extension:
                if the_item not in items_list:
                    the_descr = "Load and apply {0} from lab library".format(the_item)
                    items_list.append((the_item, the_item, the_descr))
        items_list.sort()
    return items_list


def load_image(filepath):
    if os.path.isfile(filepath):
        print_log_report("INFO", "Loading image {0}".format(os.path.basename(filepath)))
        img = bpy.data.images.load(filepath, check_existing=True)
        img.reload()
    else:
        print_log_report("INFO", "Image {0} not found".format(os.path.basename(filepath)))


def new_image(name, img_size, color=(0.5, 0.5, 0.5, 1)):
    print_log_report("INFO", "Creating new image {0} with size {1}x{2}".format(name, img_size[0], img_size[1]))
    if name in bpy.data.images:
        bpy.data.images.remove(bpy.data.images[name], do_unlink=True)
        print_log_report("INFO", "Previous existing image {0} replaced with the new one".format(name))
    new_img = bpy.data.images.new(name, img_size[0], img_size[1])
    new_img.generated_color = color
    return new_img


def get_image(name):
    if name:
        if name in bpy.data.images:
            # Some check for log
            if bpy.data.images[name].source == "FILE":
                if os.path.basename(bpy.data.images[name].filepath) != name:
                    print_log_report("WARNING", "Image named {0} is from file: {1}".format(name, os.path.basename(
                        bpy.data.images[name].filepath)))
            return bpy.data.images[name]
        else:
            print_log_report("WARNING", "Getting image failed. Image {0} not found in bpy.data.images".format(name))
    else:
        print_log_report("WARNING", "Getting image failed. Image name is {0}".format(name))
    return None


def are_squared_images(image1, image2):
    size1 = image1.size
    size2 = image2.size

    if size1[0] != size1[1]:
        print_log_report("WARNING", "The image {0} cannot be used: not squared".format(image1.name))
        return False

    if size2[0] != size2[1]:
        print_log_report("WARNING", "The image {0} cannot be used: not squared".format(image2.name))
        return False

    return True


def scale_image_to_fit(image1, image2):
    if are_squared_images(image1, image2):
        size1 = image1.size
        size2 = image2.size
        if size1[0] != size2[0]:
            if size1[0] * size1[1] > size2[0] * size2[1]:
                image2.scale(size1[0], size1[1])

            if size1[0] * size1[1] < size2[0] * size2[1]:
                image1.scale(size2[0], size2[1])


def save_image(name, filepath, fileformat='PNG'):
    img = get_image(name)
    scn = bpy.context.scene
    if img:
        current_format = scn.render.image_settings.file_format
        scn.render.image_settings.file_format = fileformat
        img.save_render(filepath)
        scn.render.image_settings.file_format = current_format
    else:
        print_log_report("WARNING",
                         "The image {0} cannot be saved because it's not present in bpy.data.images.".format(name))


def new_texture(name, image=None):
    if name not in bpy.data.textures:
        new_texture = bpy.data.textures.new(name, type='IMAGE')
    else:
        new_texture = bpy.data.textures[name]
    if image:
        new_texture.image = image
    return new_texture


def image_to_array(blender_image):
    return array.array('f', blender_image.pixels[:])


def array_to_image(pixel_array, blender_image):
    blender_image.pixels = pixel_array.tolist()


def set_node_image(mat_node, mat_image):
    if mat_node:
        mat_node.image = mat_image
    else:
        print_log_report("WARNING", "Node assignment failed. Image not found: {0}".format(mat_image.filepath_raw))


def get_material(material_name):
    for material in bpy.data.materials:
        if material.name == material_name:
            return material
    print_log_report("WARNING", "Material {0} not found".format(material_name))
    return None


def get_material_nodes(material):
    if material.node_tree:
        return material.node_tree.nodes
    else:
        return None
        print_log_report("WARNING", "Material {0} has not nodes".format(material.node))


def get_material_node(material_name, node_name):
    material_node = None
    material = get_material(material_name)
    if material:
        if node_name in material.node_tree.nodes:
            material_node = material.node_tree.nodes[node_name]
    if not material_node:
        print_log_report("WARNING", "Node not found: {0} in material {1}".format(node_name, material_name))
    return material_node


def get_node_output_value(node, index):
    if index in range(len(node.outputs)):
        if hasattr(node.outputs[index], "default_value"):
            return node.outputs[index].default_value
        else:
            print_log_report("WARNING", "Socket [{0}] has not default_value attribute".format(index))
    else:
        print_log_report("WARNING", "Socket [{0}] not in range of node {1} outputs".format(index, node.name))


def set_node_output_value(node, index, value):
    if index in range(len(node.outputs)):
        if hasattr(node.outputs[index], "default_value"):
            node.outputs[index].default_value = value
        else:
            print_log_report("WARNING", "Socket [{0}] has not default_value attribute".format(index))
    else:
        print_log_report("WARNING", "Socket[{0}] not in range of node {1} outputs".format(index, node.name))


def get_edit_bones(armature):
    if bpy.context.mode != 'EDIT_ARMATURE':
        print_log_report("WARNING", "Cannot get the edit bones because the obj is not in edit mode")
        return None
    else:
        return armature.data.edit_bones


def get_bones(armature):
    if armature.type == 'ARMATURE':
        return armature.data.bones
    else:
        print_log_report("WARNING", "Cannot get the bones because the obj is not an armature")
        return None


def get_pose_bones(armature):
    if bpy.context.mode != 'POSE':
        print_log_report("WARNING", "Cannot get the pose bones because the obj is not in pose mode")
        return None
    else:
        return armature.pose.bones


def get_edit_bone(armature, name):
    edit_bones = get_edit_bones(armature)
    if edit_bones != None:
        if name in edit_bones:
            return edit_bones[name]
    return None


def set_bone_rotation(bone, value, mode='QUATERNION'):
    if mode == 'QUATERNION':
        bone.rotation_quaternion = value


def get_bone_rotation(bone, mode='QUATERNION'):
    if mode == 'QUATERNION':
        return bone.rotation_quaternion


def has_anime_shapekeys(obj):
    anime_specific_sks = ["Expressions_brow01L_max", "Expressions_brow01L_min",
                          "Expressions_brow01R_max", "Expressions_brow01R_min",
                          "Expressions_brow02L_min", "Expressions_brow02R_min",
                          "Expressions_brow03_max", "Expressions_brow03_min",
                          "Expressions_eyes01_max", "Expressions_eyes01_min",
                          "Expressions_eyes02_max", "Expressions_eyes02_min",
                          "Expressions_eyes03_max", "Expressions_eyes03_min",
                          "Expressions_eyes04_max", "Expressions_eyes04_min",
                          "Expressions_eyes05_max", "Expressions_eyes05_min",
                          "Expressions_eyes06_max"]
    current_sks = set()
    if has_shapekeys(obj):
        current_sks = set(get_shapekeys_names())
        anime_sk_in_current_sk = current_sks.intersection(anime_specific_sks)
        if len(anime_sk_in_current_sk) >= (len(anime_specific_sks) / 2):
            return True
        else:
            return False
    else:
        return False


def get_rest_lengths(armat):
    armature_rest_lengths = {}
    if armat:
        select_and_change_mode(armat, 'EDIT')
        edit_bones = get_edit_bones(armat)
        for e_bone in edit_bones:
            armature_rest_lengths[e_bone.name] = e_bone.length
        select_and_change_mode(armat, 'POSE')
    return armature_rest_lengths


def get_bone_constraint_by_type(bone, constraint_type):
    for constraint in bone.constraints:
        if constraint.type == constraint_type:
            return constraint
    return None


def set_bone_constraint_parameter(constraint, parameter, value):
    if hasattr(constraint, parameter):
        try:
            setattr(constraint, parameter, value)
        except AttributeError:
            print_log_report("INFO",
                             "Setattr failed for attribute '{0}' of constraint {1}".format(parameter, constraint.name))


def get_vertgroup_by_name(obj, group_name):
    if obj:
        if obj.type == 'MESH':
            if group_name in obj.vertex_groups:
                return obj.vertex_groups[group_name]
    return None


def remove_vertgroups_all(obj):
    obj.vertex_groups.clear()


def remove_vertgroup(obj, group_name):
    vertgroup = get_vertgroup_by_name(obj, group_name)
    if vertgroup:
        obj.vertex_groups.remove(vertgroup)


def new_vertgroup(obj, group_name):
    return obj.vertex_groups.new(name=group_name)


def play_animation():
    if not bpy.context.screen.is_animation_playing:
        bpy.ops.screen.animation_play()


def stop_animation():
    if bpy.context.screen.is_animation_playing:
        bpy.ops.screen.animation_play()


def get_shapekey_reference(obj):
    if has_shapekeys(obj):
        return obj.data.shape_keys.reference_key
    return None


def get_shapekey(obj, shapekey_name):
    shapekey_data = None
    if has_shapekeys(obj):
        if shapekey_name in get_shapekeys_names(obj):
            shapekey_data = obj.data.shape_keys.key_blocks[shapekey_name]
    return shapekey_data


def remove_shapekey(obj, shapekey_name):
    shapekey_to_remove = get_shapekey(obj, shapekey_name)
    if shapekey_to_remove:
        obj.shape_key_remove(shapekey_to_remove)


def remove_shapekeys_all(obj):
    if has_shapekeys(obj):
        for sk in obj.data.shape_keys.key_blocks:
            if sk != obj.data.shape_keys.reference_key:
                sk.value = 0
                obj.shape_key_remove(sk)
        obj.shape_key_remove(obj.data.shape_keys.reference_key)


def get_shapekeys_names(obj):
    shapekeys_names = []
    if has_shapekeys(obj):
        for sk in obj.data.shape_keys.key_blocks:
            shapekeys_names.append(sk.name)
    return shapekeys_names


def has_shapekeys(obj):
    return hasattr(obj.data.shape_keys, 'key_blocks')
    return None


def update_bendy_bones(armat):
    if armat:
        armature_rest_lengths = get_rest_lengths(armat)
        select_and_change_mode(armat, 'POSE')
        pose_bones = get_pose_bones(armat)
        for p_bone in pose_bones:
            if p_bone.name in armature_rest_lengths:
                length = armature_rest_lengths[p_bone.name]
                stretch_to_constraint = get_bone_constraint_by_type(p_bone, 'STRETCH_TO')
                set_bone_constraint_parameter(stretch_to_constraint, 'rest_length', length)


def link_to_scene(obj):
    scn = bpy.context.scene
    if obj.name:
        if obj.name in bpy.data.objects:
            if obj.name not in scn.object_bases:
                scn.objects.link(obj)
            else:
                print_log_report("WARNING", "The object {0} is already linked to the scene".format(obj.name))
        else:
            print_log_report("ERROR", "Cannot link obj {0} because it's not appended to sccene".format(obj.name))


def import_object_from_lib(lib_filepath, name, final_name=None, stop_import=True):
    if name != "":
        if stop_import == True:
            print_log_report("INFO", "Appending object {0} from {1}".format(name, simple_path(lib_filepath)))
            if name in bpy.data.objects:
                print_log_report("WARNING", "Object {0} already in the scene. Import stopped".format(name))
                return None

            if final_name:
                if final_name in bpy.data.objects:
                    print_log_report("WARNING", "Object {0} already in the scene. Import stopped".format(final_name))
                    return None

        append_object_from_library(lib_filepath, [name])
        obj = get_object_by_name(name)
        if obj:
            print_log_report("INFO", "Object '{0}' imported".format(name))
            if final_name:
                obj.name = final_name
                print_log_report("INFO", "Object '{0}' renamed as '{1}'".format(name, final_name))
            return obj
        else:
            print_log_report("WARNING", "Object {0} not found in library {1}".format(name, simple_path(lib_filepath)))
    return None


def append_object_from_library(lib_filepath, obj_names, suffix=None):
    scn = bpy.context.scene

    try:
        with bpy.data.libraries.load(lib_filepath) as (data_from, data_to):
            if suffix:
                names_to_append = [name for name in data_from.objects if suffix in name]
                data_to.objects = names_to_append
            else:
                names_to_append = obj_names
                data_to.objects = [name for name in names_to_append if name in data_from.objects]
    except:
        print_log_report("CRITICAL", "lib {0} not found".format(lib_filepath))
        return None

    for obj in data_to.objects:
        link_to_scene(obj)
        obj_parent = get_object_parent(obj)
        if obj_parent:
            link_to_scene(obj_parent)


def append_mesh_from_library(lib_filepath, mesh_names, suffix=None):
    scn = bpy.context.scene

    try:
        with bpy.data.libraries.load(lib_filepath) as (data_from, data_to):
            if suffix:
                names_to_append = [name for name in data_from.meshes if suffix in name]
                data_to.meshes = names_to_append
            else:
                names_to_append = mesh_names
                data_to.meshes = [name for name in names_to_append if name in data_from.meshes]
    except:
        print_log_report("CRITICAL", "lib {0} not found".format(lib_filepath))
        return None


def read_object_names_from_library(lib_filepath):
    try:
        with bpy.data.libraries.load(lib_filepath) as (data_from, data_to):
            for name in data_from.objects:
                print("OBJ_LIB: ", name)
    except:
        print_log_report("CRITICAL", "lib {0} not found".format(lib_filepath))
        return None


def is_armature_linked(obj, armat):
    if obj.type == 'MESH':
        for modfr in obj.modifiers:
            if modfr.type == 'ARMATURE':
                if modfr.object == armat:
                    return True
    return False


def has_deformation_vgroups(obj, armat):
    if obj.type == 'MESH':
        if armat:
            for vgroup in obj.vertex_groups:
                for b in armat.data.bones:
                    if b.name == vgroup.name:
                        return True
    return False


def is_rigged(obj, armat):
    # if is_armature_linked(obj, armat):
    if has_deformation_vgroups(obj, armat):
        return True
    return False


def get_boundary_verts(obj):
    polygons_dict = {}
    for polyg in obj.data.polygons:
        for i in polyg.vertices:
            if str(i) not in polygons_dict:
                indices = [n for n in polyg.vertices if n != i]
                polygons_dict[str(i)] = indices
            else:
                for vert_id in polyg.vertices:
                    if vert_id != i and vert_id not in polygons_dict[str(i)]:
                        polygons_dict[str(i)].append(vert_id)

    return polygons_dict


def get_object_groups(obj):
    obj_groups = {}
    for grp in obj.vertex_groups:
        weights = []
        for idx in range(len(obj.data.vertices)):
            try:
                if grp.weight(idx) > 0:
                    weights.append([idx, grp.weight(idx)])
            except:
                pass
        obj_groups[grp.name] = weights
    return obj_groups
