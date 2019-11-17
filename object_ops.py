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



import bpy
import numpy as np

from copy import deepcopy as dc
from math import radians

from . import algorithms


def get_body_mesh():
    if bpy.context.object.type == 'ARMATURE':
        return bpy.context.object.children[0]
    else:
        return bpy.context.object

def get_skeleton():
    if bpy.context.object.type == 'ARMATURE':
        return bpy.context.object
    else:
        return bpy.context.object.parent

#get selected verts, edges, and faces information
def get_sel():
    mode = bpy.context.active_object.mode
    vt = bpy.context.object.data.vertices
    fa = bpy.context.object.data.polygons
    bpy.ops.object.mode_set(mode='OBJECT')
    countv = len(vt)
    selv = np.empty(countv, dtype=np.bool)
    vt.foreach_get('select', selv)
    co = np.empty(countv * 3, dtype=np.float32)
    vt.foreach_get('co', co)
    co.shape = (countv, 3)
    vidx = np.empty(countv, dtype=np.int32)
    vt.foreach_get('index', vidx)
    countf = len(fa)
    selfa = np.empty(countf, dtype=np.bool)
    fa.foreach_get('select', selfa)
    fidx = np.empty(countf, dtype=np.int32)
    fa.foreach_get('index', fidx)
    fac = np.array([i.vertices[:] for i in fa])
    #New indexes
    v_count = len(vidx[selv])
    f_count = len(fidx[selfa])
    new_idx = [i for i in range(v_count)]
    nv_Dict = {o: n for n, o in enumerate(vidx[selv].tolist())}
    new_f = [[nv_Dict[i] for i in nest] for nest in fac[selfa]]
    return dc([co[selv], new_f, nv_Dict])


###############################################################################################################################
# OBJECT CREATION

#creates new mesh
def obj_mesh(co, faces, collection):
    cur = bpy.context.object
    mesh = bpy.data.meshes.new("Obj")
    mesh.from_pydata(co, [], faces)
    mesh.validate()
    mesh.update(calc_edges=True)
    Object = bpy.data.objects.new("Obj", mesh)
    Object.data = mesh
    bpy.data.collections[collection].objects.link(Object)
    bpy.context.view_layer.objects.active = Object
    cur.select_set(False)
    Object.select_set(True)

#creates new object
def obj_new(Name, co, faces, collection):
    obj_mesh(co, faces, collection)
    bpy.data.objects["Obj"].name = Name
    bpy.data.meshes[bpy.data.objects[Name].data.name].name = Name

#delete objects from list
def obj_del(objects: list):
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects:
        obj.select_set(state=True)
        bpy.ops.object.delete()

#set active object and select objects from list
def active_ob(object, objects):
    bpy.ops.object.select_all(action='DESELECT')
    bpy.data.objects[object].select_set(state=True)
    bpy.context.view_layer.objects.active = bpy.data.objects[object]
    if objects is not None:
        for o in objects:
            bpy.data.objects[o].select_set(state=True)


# ------------------------------------------------------------------------
#Create Target
def add_empty(Name, collection, matrix_final):
    obj_empty = bpy.data.objects.new(Name, None)
    bpy.data.collections[collection].objects.link(obj_empty)
    #draw size
    obj_empty.empty_display_size = 0.01
    obj_empty.matrix_world = matrix_final

# ------------------------------------------------------------------------
#Create Capsule
def capsule_data(length, radius, cap_coord):
    sc = np.eye(3)
    sc[0][0] = radius
    sc[1][1] = radius
    sc[2][2] = length/4
    coord = np.array([[i[0], i[1], i[2] + 2] for i in cap_coord])
    nc = coord @ sc
    return nc

def add_rd_capsule(Name, length, radius, cap_coord, faces, collection):
    cor = capsule_data(length, radius, cap_coord)
    obj_new(Name, cor, [], faces, collection)
    try:
        bpy.ops.rigidbody.objects_add(type='ACTIVE')
    except:
        pass

###############################################################################################################################
# MATH OPS

#Rotation Matrix
def rotation_matrix(xrot, yrot, zrot):
    rot_mat = np.array([
        [np.cos(zrot)*np.cos(yrot), -np.sin(zrot)*np.cos(xrot) + np.cos(zrot)*np.sin(yrot)*np.sin(xrot), np.sin(zrot)*np.sin(xrot) + np.cos(zrot)*np.sin(yrot)*np.cos(xrot)],
        [-np.sin(yrot), np.cos(yrot)*np.sin(xrot), np.cos(yrot)*np.cos(xrot)]
        ])
    return rot_mat


#Rotation Matrix X 90 degrees
def rot_mat_x_90(List):
    rmx90 = rotation_matrix(radians(90), 0, 0)
    new_co = [i @ rmx90 for i in List]
    return new_co

def rot_obj(obj, rot_mat):
    vt = obj.data.vertices
    countv = len(vt)
    co = np.empty(countv * 3, dtype=np.float32)
    vt.foreach_get('co', co)
    np.round(co, 5)
    co.shape = (countv, 3)
    List = co.tolist()
    #rm = rot_mat_x_90(List)
    #vt.foreach_set('co', rm)
    for i, v in enumerate(List):
        vt[i].co = v

###############################################################################################################################
# VERTEX_GROUP OPS

#Create Vertex Group
def add_vert_group(object, vgroup, index):
    nvg = bpy.data.objects[object].vertex_groups.new(name=vgroup)
    nvg.add(index, 1.0, "ADD")

#Set Vertex Weight
def set_weight(object, index, weight):
    bpy.data.meshes[object].vertices[index].groups[0].weight = weight

#vertex group index list
def vg_idx_list(vgn):
    return([v.index for v in bpy.context.object.data.vertices if v.select and bpy.context.object.vertex_groups[vgn].index in [vg.group for vg in v.groups]])

#vertex group {name: [indexes]} dictionary
def vg_idx_dict(gs):
    vn = [v.name for v in bpy.context.object.vertex_groups[:]]
    vd = {n: vg_idx_list(n) for n in vn}
    vdd = {k: vd[k] for k in vd if vd[k] != []}
    return dc({d: [gs[2][i] for i in vdd[d]] for d in vdd})


#vertex group index list
def vidx_list(vgn):
    return([[v.index, v.groups[0].weight] for v in bpy.context.object.data.vertices if v.select and bpy.context.object.vertex_groups[vgn].index in [vg.group for vg in v.groups]])

#vertex group {name: [indexes]} dictionary
def vidx_dict():
    vn = [v.name for v in bpy.context.object.vertex_groups[:]]
    vd = {n: vidx_list(n) for n in vn}
    vdd = {k: vd[k] for k in vd if vd[k] != []}
    return dc(vdd)

# ------------------------------------------------------------------------

#transfer vertex weight to new object
def transfer_vt(Name, viw):
    vg = bpy.data.objects[Name].vertex_groups
    vt = bpy.data.objects[Name].data.vertices
    for vgroup in viw:
        nvg = bpy.data.objects[Name].vertex_groups.new(name=vgroup)
        nvg.add(viw[vgroup], 1.0, "ADD")

def add_wt(Name, vid):
    vt = bpy.data.objects[Name].data.vertices
    for v in vid:
        for i in vid[v]:
            vt[i[0]].groups[0].weight = i[1]

def copy_wt(Name, viw, vid):
    transfer_vt(Name, viw)
    add_wt(Name, vid)

###############################################################################################################################
# COLLECTION OPS

#get a list of all objects in collection
def collection_object_list(collection):
    return [o.name for o in bpy.data.collections[collection].objects[:]]

#Add new collections
def new_collection(Name):
    new_coll = bpy.data.collections.new(Name)
    bpy.context.scene.collection.children.link(new_coll)

###############################################################################################################################
# PARENTING OPS

def adoption(parent, child, type, index):
    '''types: OBJECT, ARMATURE, LATTICE, VERTEX, VERTEX_3, BONE'''
    par = bpy.data.objects[parent]
    ch = bpy.data.objects[child]
    ch.parent = par
    ch.matrix_world = par.matrix_world @ par.matrix_world.inverted()
    ch.parent_type = type
    if type == 'VERTEX':
        ch.parent_vertices[0] = index
    if type == 'BONE':
        ch.parent_bone = index

def add_parent(parent, children):
    active_ob(parent, children)
    bpy.ops.object.parent_set(type='OBJECT', keep_transform=True)
    bpy.ops.object.select_all(action='DESELECT')



###############################################################################################################################
# MODIFIER OPS

#Add modifier
def add_modifier(Object, Name, Type):
    Object.modifiers.new(Name, type=Type)

#Apply Modifier
def apply_mod(Ref):
    act = bpy.context.view_layer.objects.active
    for o in bpy.context.view_layer.objects:
        for m in o.modifiers:
            if Ref in m.name:
                bpy.context.view_layer.objects.active = o
                bpy.ops.object.modifier_apply(modifier=m.name)
    bpy.context.view_layer.objects.active = act

#
def set_scene_modifiers_status_by_type(modfr_type, visib):
    for obj in bpy.data.objects:
        for modfr in obj.modifiers:
            if modfr.type == modfr_type:
                set_modifier_viewport(modfr, visib)

#
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

#
def disable_object_modifiers(obj, types_to_disable=[]):
    for modfr in obj.modifiers:
        modifier_type = modfr.type
        if modifier_type in types_to_disable:
            set_modifier_viewport(modfr, False)
            logger.info("Modifier %s of %s can create unpredictable fitting results. MB-Lab has disabled it",
                        modifier_type, obj.name)
        elif types_to_disable == []:
            set_modifier_viewport(modfr, False)
            logger.info("Modifier %s of %s can create unpredictable fitting results. MB-Lab has disabled it",
                        modifier_type, obj.name)

#
def get_object_modifiers_visibility(obj):
    # Store the viewport visibility for all modifiers of the obj
    obj_modifiers_status = {}
    for modfr in obj.modifiers:
        modfr_name = get_modifier_name(modfr)
        modfr_status = get_modifier_viewport(modfr)
        if modfr_name:
            obj_modifiers_status[modfr_name] = modfr_status
    return obj_modifiers_status

#
def set_object_modifiers_visibility(obj, modifier_status):
    # Store the viewport visibility for all modifiers of the obj
    for modfr in obj.modifiers:
        modfr_name = get_modifier_name(modfr)
        if modfr_name in modifier_status:
            set_modifier_viewport(modfr, modifier_status[modfr_name])

#
def get_modifier(obj, modifier_name):
    return obj.modifiers.get(modifier_name)

#
def get_modifier_name(modfr):
    return getattr(modfr, 'name')

#
def apply_modifier(obj, modifier):
    modifier_name = get_modifier_name(modifier)
    if modifier_name in obj.modifiers:
        set_active_object(obj)
        try:
            bpy.ops.object.modifier_apply(apply_as='DATA', modifier=modifier_name)
        except AttributeError:
            logger.warning("Problems in applying %s. Is the modifier disabled?", modifier_name)

#
def move_up_modifier(obj, modifier):
    modifier_name = get_modifier_name(modifier)
    set_active_object(obj)
    for n in range(len(obj.modifiers)):
        bpy.ops.object.modifier_move_up(modifier=modifier_name)

#
def move_down_modifier(obj, modifier):
    modifier_name = get_modifier_name(modifier)
    set_active_object(obj)
    for n in range(len(obj.modifiers)):
        bpy.ops.object.modifier_move_down(modifier=modifier_name)

#
def remove_modifier(obj, modifier_name):
    print("Removing ", modifier_name)
    if modifier_name in obj.modifiers:
        obj.modifiers.remove(obj.modifiers[modifier_name])

#
def disable_modifier(modfr):
    logger.info("Disable %s", modfr.name)
    for mdf in ('show_viewport', 'show_render', 'show_in_editmode', 'show_on_cage'):
        if hasattr(modfr, mdf):
            setattr(modfr, mdf, False)

#
def get_modifier_viewport(modfr):
    return getattr(modfr, 'show_viewport', None)

#
def set_modifier_viewport(modfr, value):
    if hasattr(modfr, 'show_viewport'):
        modfr.show_viewport = value

#
def new_modifier(obj, name, modifier_type, parameters):
    if name in obj.modifiers:
        logger.info("Modifier %s already present in %s", modifier_type, obj.name)
        return obj.modifiers[name]
    _new_modifier = obj.modifiers.new(name, modifier_type)
    for parameter, value in parameters.items():
        if hasattr(_new_modifier, parameter):
            try:
                setattr(_new_modifier, parameter, value)
            except AttributeError:
                logger.info("Setattr failed for attribute '%s' of modifier %s", parameter, name)
    return _new_modifier

#
def set_modifier_parameter(modifier, parameter, value):
    if hasattr(modifier, parameter):
        try:
            setattr(modifier, parameter, value)
        except AttributeError:
            logger.info("Setattr failed for attribute '%s' of modifier %s", parameter, modifier)


###############################################################################################################################
# ARMATURE OPS

###############################################################################################################################
# SHAPEKEY OPS

