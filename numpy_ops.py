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
# ManuelbastioniLAB - Copyright (C) 2015-2018 Manuel Bastioni

import bpy
import os
import numpy as np

from . import algorithms
from . import file_ops


def dict_to_nparray(Dict):
    Keys = np.array([i for i in Dict])
    Values = [np.array(Dict[i]) for i in Dict]
    return Keys, Values

def save_to_npz(fileName, *data):
    np.savez(fileName, *data)

def load_npz(fileName):
    with np.load(fileName, allow_pickle=True) as container:
        return [container[key] for key in container]
    
def get_data_index(Key, Keys):
    L = Keys.tolist()
    idx = L.index(Key)
    return idx

def get_data_value(Key, fileName):
    data = load_npz(fileName)[1][get_data_index(Key, load_npz(fileName)[0])]
    data = data.tolist()
    return data

def add_array(Key, Value, fileName):
    Keys, Values = load_npz(fileName)
    V = np.array(Value)
    Values = Values.tolist()
    L = Keys.tolist()
    if Key not in L:
        Values.append(V)
        L.append(Key)
    else:
        idx = L.index(Key)
        Values[idx] = Value
    NL = np.array(L)
    Values = np.array(Values)
    data = NL, Values
    save_to_npz(fileName, *data)
    
def remove_array(Key, fileName, List):
    Keys, Values = load_npz(fileName)
    L = Keys.tolist()
    idx = L.index(Key)
    L.remove(Key)
    L = np.array(L)
    Values = Values.tolist()
    Values.pop(idx)
    Values = np.array(Values)
    data = L, Values
    List.append([Key, Values[idx]])
    save_to_npz(fileName, *data)

######################################################

def get_path_to(Folder):
    data_dir = file_ops.get_data_path()
    return os.path.join(data_dir, Folder)
    
def get_file(Folder, fileName):
    fo = get_path_to(Folder)
    return os.path.join(fo, fileName)

def get_data(Folder, fileName):
    File = get_file(Folder, fileName)
    data = load_npz(File)
    return data

def dict_to_npz(Dict, fileName):
    Keys, Values = dict_to_nparray(Dict)
    data = Keys, Values
    save_to_npz(fileName, *data)






    




