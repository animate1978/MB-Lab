import bpy
import os
import numpy as np
import logging

from . import algorithms
from . import file_ops

logger = logging.getLogger(__name__)

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

# def load_npz_dict(fileName):
#     cwd = os.getcwd()
#     os.chdir(path)
#     fpath = fileName + '.npz'
#     with np.load(f'r') as f:
#         data = {item: list(f[item]) for item in f}
#     os.chdir(cwd)
#     return data

#################################################################################################################################
# New Code #

def new_npz(fileName, data):
    np.savez_compressed(fileName, **data)

def write_npz_dict(fileName, data):
    with np.load(fileName, 'rb') as f:
        np.savez(f, **data)

def load_npz_dict(fileName):
    with np.load(fileName, 'r', allow_pickle=True) as f:
        data = {item: f[item].tolist() for item in f}
    return data

def load_npz_data(fileName, item):
    with np.load(fileName, 'r', allow_pickle=True) as f:
        data = f[item].tolist()
    return data

def load_npz_keys(fileName):
    with np.load(fileName, 'r', allow_pickle=True) as f:
        data = [i for i in f]
    return data

def append_npz_dict(fileName, Name, info):
    with np.load(fileName, 'r', allow_pickle=True) as f:
        data = {item: f[item].tolist() for item in f}
    data.update({Name: info})
    np.savez(fileName, **data)

def remove_npz_data(fileName, item):
    with np.load(fileName, 'r', allow_pickle=True) as f:
        data = {item: f[item].tolist() for item in f}
    info = data.pop(item)
    np.savez(fileName, **data)
    return info

def remove_style(fileName, List, style):
    with np.load(fileName, 'r+', allow_pickle=True) as f:
        d = {item: f[item].tolist() for item in f}
        rs = [style, d[style]]
        List.append(rs)
        d.pop(style)
        np.savez(fileName, **d)

def replace_style(fileName,  List):
    try:
        if List == []:
            pass
    except:
        print("List is empty")
    finally:
        with np.load(fileName, 'r+', allow_pickle=True) as f:
            data = {item: f[item].tolist() for item in f}
            rl = List[-1]
            List.remove(rl)
            info = {rl[0]: rl[1]}
            data.update(**info)
            np.savez(fileName, **data)

def hair_style_backup(Path, files):
    for file in files:
        f = os.path.join(Path, file)
        fileName = "{}{}".format(f, ".npz")
        data = load_npz_dict(fileName)
        desktop = os.path.expanduser("~/Desktop")
        bu = os.path.join(desktop, file)
        np.savez_compressed(bu, **data)


