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

#creates new mesh
def obj_mesh(co, faces, collection):
    cur = bpy.context.object
    mesh = bpy.data.meshes.new("Obj")
    mesh.from_pydata(co, [], faces)
    mesh.validate()
    mesh.update(calc_edges = True)
    Object = bpy.data.objects.new("Obj", mesh)
    Object.data = mesh
    bpy.data.collections[collection].objects.link(Object)
    bpy.context.view_layer.objects.active = Object
    cur.select_set(False)
    Object.select_set(True)

#creates new object
def obj_new(Name, co, faces, collection):
    obj_mesh(co, faces, collection)
    bpy.data.objects["Obj"].name = Name #"Hair"
    bpy.data.meshes[bpy.data.objects[Name].data.name].name = Name

# ------------------------------------------------------------------------ 
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


