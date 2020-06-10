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
#
# Teto, for MB-Lab

import logging

import bpy
import bmesh

logger = logging.getLogger(__name__)

class MeshHistory:
    
    def __init__(self, name="", obj=None):
        self.vertices_history = []
        self.edges_history = []
        self.faces_history = []
        self.vertices_recover = []
        self.edges_recover = []
        self.faces_recover = []
        self.set_name(name)
        self.counter_vert = 0
        self.counter_edge = 0
        self.counter_face = 0
        self.object = obj
    
    def clear(self):
        self.vertices_history = []
        self.edges_history = []
        self.faces_history = []
        self.object = None
        
    # reset recovery with actual values.
    def clear_recover(self):
        self.vertices_recover = self.vertices_history.copy()
        self.edges_recover = self.edges_history.copy()
        self.faces_recover = self.faces_history.copy()
        
    def has_elements(self, type='VERTEX'):
        if type == "EDGE":
            return len(self.edges_history) > 0
        elif type == "FACE":
            return len(self.faces_history) > 0
        return len(self.vertices_history) > 0
    
    def get_length(self, type='VERTEX'):
        if type == "EDGE":
            return len(self.edges_history)
        elif type == "FACE":
            return len(self.faces_history)
        return len(self.vertices_history)
        
    def set_name(self, name = ""):
        self.name = name
    
    def set_object(self, obj):
        if self.object == None:
            self.object = obj
        
    def add_selection(self):
        bm = bmesh.from_edit_mesh(self.object.data)
        element = bm.select_history
        if element == None: # Could happen
            return
        e = element.active
        if e == None: # Could happen
            return
        index = e.index
        if isinstance(e, bmesh.types.BMVert):
            self.vertices_history.append(index)
            self.counter_vert = len(self.vertices_history)-1
        elif isinstance(e, bmesh.types.BMEdge):
            self.edges_history.append(index)
            self.counter_edge = len(self.edges_history)-1
        elif isinstance(e, bmesh.types.BMFace):
            self.faces_history.append(index)
            self.counter_face = len(self.faces_history)-1
        else:
            print('Not found :')
            print(type(e))
    
    def get_previous(self, type='VERTEX'):
        if type == 'VERTEX':
            if self.counter_vert > 0:
                self.counter_vert -= 1
            return get_history(type, self.counter_vert)
        elif type == 'EDGE':
            if self.counter_edge > 0:
                self.counter_edge -= 1
            return get_history(type, self.counter_edge)
        elif type == 'FACE':
            if self.counter_face > 0:
                self.counter_face -= 1
            return get_history(type, self.counter_face)
        return []
            
    def get_next(self, type='VERTEX'):
        if type == 'VERTEX':
            if self.counter_vert < len(self.vertices_history)-1:
                self.counter_vert += 1
            return get_history(type, self.counter_vert)
        elif type == 'EDGE':
            if self.counter_edge < len(self.edges_history)-1:
                self.counter_edge += 1
            return get_history(type, self.counter_edge)
        elif type == 'FACE':
            if self.counter_face < len(self.faces_history)-1:
                self.counter_face += 1
            return get_history(type, self.counter_face)
        return []
    
    def get_last(self, type='VERTEX'):
        if type == 'VERTEX':
            self.counter_vert = len(self.vertices_history)-1
            return get_history(type, self.counter_vert)
        elif type == 'EDGE':
            self.counter_edge = len(self.edges_history)-1
            return get_history(type, self.counter_edge)
        elif type == 'FACE':
            self.counter_face = len(self.faces_history)-1
            return get_history(type, self.counter_face)
        return []
    
    def get_first(self, type='VERTEX'):
        if type == 'VERTEX':
            self.counter_vert = 0
            return get_history(type, self.counter_vert)
        elif type == 'EDGE':
            self.counter_edge = 0
            return get_history(type, self.counter_edge)
        elif type == 'FACE':
            self.counter_face = 0
            return get_history(type, self.counter_face)
        return []
    
    def get_history(self, type='VERTEX', index=-1):
        if type == 'VERTEX':
            if index > -1:
                return [self.vertices_history[index]]
            return self.vertices_history
        elif type == 'EDGE':
            if index > -1:
                return [self.edges_history[index]]
            return self.edges_history
        elif type == 'FACE':
            if index > -1:
                return [self.faces_history[index]]
            return self.faces_history
        return []
    
    def select_previous(self, type='VERTEX'):
        select_in_a_mesh(self.object, self.get_previous(type), type)
    
    def select_next(self, type='VERTEX'):
        select_in_a_mesh(self.object, self.get_next(type), type)
        
    def select_first(self, type='VERTEX'):
        select_in_a_mesh(self.object, self.get_first(type), type)
        
    def select_last(self, type='VERTEX'):
        select_in_a_mesh(self.object, self.get_last(type), type)
        
    def select_all(self, type='VERTEX'):
        select_in_a_mesh(self.object, self.get_history(type), type)        
    
    # For conveniency
    def unselect_all(self):
        bpy.ops.object.select_all(action='DESELECT')
    
    # If end < 0 only start is removed.
    def remove(self, type, start, end=-1):
        if start < 0:
            return []
        if end < 0:
            if type == 'EDGE':
                return self.edges_history.pop(start)
            elif type == 'FACE':
                return self.faces_history.pop(start)
            return self.vertices_history.pop(start)
        if type == 'EDGE':
            returned = self.edges_history[start, end]
            del self.edges_history[start, end]
            return returned
        elif type == 'FACE':
            returned = self.faces_history[start, end]
            del self.faces_history[start, end]
            return returned
        returned = self.vertices_history[start, end]
        del self.vertices_history[start, end]
        return returned
    
    # Here index = the 'name' of index.
    def remove_index(self, index, type='VERTEX'):
        if type == 'EDGE':
            for i in range(len(self.edges_history)):
                if self.edges_history[i] == index:
                    return self.remove(type, i)
        elif type == 'FACE':
            for i in range(len(self.faces_history)):
                if self.faces_history[i] == index:
                    return self.remove(type, i)
        else:
            for i in range(len(self.vertices_history)):
                if self.vertices_history[i] == index:
                    return self.remove(type, i)
    
    def remove_selected(self):
        bm = bmesh.from_edit_mesh(self.object.data)
        element = bm.select_history
        if element == None: # Could happen
            return
        e = element.active
        if e == None: # Could happen
            return
        index = e.index
        if isinstance(e, bmesh.types.BMVert):
            return self.remove_index(index, 'VERTEX')
        elif isinstance(e, bmesh.types.BMEdge):
            return self.remove_index(index, 'EDGE')
        elif isinstance(e, bmesh.types.BMFace):
            return self.remove_index(index, 'FACE')
        else:
            print('Not found :')
            print(type(e))
    
    def remove_all(self, type='VERTEX'):
        if type == 'EDGE':
            self.edges_history.clear()
        elif type == 'FACE':
            self.faces_history.clear()
        else :
            self.vertices_history.clear()
    
    def set(self, type, indices):
        if type == 'EDGES':
            self.edges_history = indices.copy()
            self.edges_recover = indices.copy()
        elif type == 'FACES':
            self.faces_history = indices.copy()
            self.faces_recover = indices.copy()
        else:
            self.vertices_history = indices.copy()
            self.vertices_recover = indices.copy()
    
    def recover(self, type):
        if type == 'EDGES':
            self.edges_history = self.edges_recover.copy()
        elif type == 'FACES':
            self.faces_history = self.faces_recover.copy()
        else:
            self.vertices_history = self.vertices_recover.copy()

    # The active element is added,
    # and first in the list is removed.
    def push_selection(self, type='VERTEX'):
        self.add_selection()
        self.remove(type, 0)
        
    # A dictionnary with the name as key.
    # Value is a dict with keys : 'VERTEX'; 'EDGE'; 'FACE'
    # Value for each key are lists with indices.
    def set_standalone_form(self, hist_dict, obj = None):
        if len(hist_dict) < 1:
            return
        self.vertices_history = []
        self.edges_history = []
        self.faces_history = []
        if obj != None:
            self.object = obj
        for key, item in hist_dict.items():
            self.name = key
            for sub_key, sub_item in item.items():
                if sub_key == 'VERTEX':
                    self.vertices_history = sub_item
                elif sub_key == 'EDGE':
                    self.edges_history = sub_item
                elif sub_key == 'FACE':
                    self.faces_history = sub_item
            return # because there's just 1 key+value...
    
    def get_standalone_form(self):
        item = {
            'VERTEX' : self.vertices_history,
            'EDGE' : self.edges_history,
            'FACE' : self.faces_history
            }
        return {self.name : item}
    
    def get_measures_file_form(self):
        return self.vertices_history

class MeshHandling:
    
    def __init__(self, the_name="", obj=None):
        self.history = {}
        self.name = the_name # Name of the file
        self.set_object(obj)
    
    def set_object(self, obj):
        if obj == None:
            return
        self.object = obj
        if len(self.history) > 0:
            for item in self.history.values():
                item.set_object(obj)
    
    def get_mesh_history(self, name):
        if name in self.history:
            return self.history[name]
        return None
    
    def set_mesh_history(self, hist):
        if hist == None:
            return
        self.history[hist.name] = hist
    
    def create_mesh_history(self, name):
        hist = MeshHistory(name, self.object)
        self.set_mesh_history(hist)
        return self.get_mesh_history(name)
    
    def get_for_measures_save(self):
        return_dict = {}
        for value in self.history.values():
            key, item = value.get_measures_file_form()
            return_dict[key] = item
        return return_dict
    
    def get_histories(self):
        return self.history
        
# -----------------------------------------------------------
#                   General methods
# -----------------------------------------------------------    


# Select vertices, lines, faces, etc in a mesh.
# Rough method, no many checks.
def select_global(mesh, int_list, unselect_all=True, vertices=False, edges=False, faces=False):
    if len(int_list) < 1 or mesh == None:
        return
    if unselect_all:
        bpy.ops.mesh.select_all(action='DESELECT')
    bm = bmesh.from_edit_mesh(mesh.data)
    if vertices:
        for vert in bm.verts:
            if vert.index in int_list:
                vert.select = True
    if edges:
        for ed in bm.edges:
            if ed.index in int_list:
                ed.select = True
    if faces:
        for fa in bm.faces:
            if fa.index in int_list:
                fa.select = True
    bmesh.update_edit_mesh(mesh.data, True)

def select_in_a_mesh(mesh, int_list, type, unselect_all=True):
    if type == 'VERTEX':
        select_global(mesh, int_list, unselect_all, vertices=True)
    elif type == 'EDGE':
        select_global(mesh, int_list, unselect_all, edges=True)
    elif type == 'FACE':
        select_global(mesh, int_list, unselect_all, faces=True)

def unselect_all():
    bpy.ops.mesh.select_all(action='DESELECT')

# No security checks...
# The file must be a dict with names of historic selection as keys
# The value is itsel a dict with 'VERTEX', 'EDGE' or 'FACE' as keys
# and a list with indices in integer.
# Return a dict of MeshHistory
def load_standalone(filepath, obj=None):
    file = file_ops.load_json_data(filepath, "Load history from file")
    if file == None:
        return
    history_list = {}
    for key, item in file.items():
        temp = MeshHistory(key, obj)
        temp.set_standalone_form(item)
        history_list[temp.name] = temp
    return history_list

# For conveniency
def save_in_json(filepath, history_list):
    file_ops.save_json_data(filepath, history_list)