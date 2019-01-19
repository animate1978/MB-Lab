import bpy
import os
from . import algorithms as a
from . import settings as set
from pathlib import Path, PurePath

dr = set.data_path


def namesofallconfig(configtype, inproject = "", seconddir = ""): # lists all json files in a specified project
    return namesofallfile("json", PurePath(inproject, configtype, seconddir))


def namesofallfile(thefiletype, thepath="", filename="*"):
    thepath = dr.glob('**/' + str(thepath) + '/' + filename + '.' + thefiletype)
    return str(thepath)



class PathDirectory:  # TODO determine if needed. With pathlib I don't think it is
    """
    This is a map of the the "project" directories remapped/'merged' together.
    It should NOT move files around in the data folder.
    """
    # adapted from https://stackoverflow.com/questions/18510733/python-mapping-all-files-inside-a-folder

    def __init__(self):
        self.full_config = []
        self.projects = []
        self.get_proj()

    def get_proj(self):
        print("get_proj")
        for i, projects in enumerate(dr.iterdir()):
            inproj = projects
            self.projects.append(inproj)
            print(inproj.name)
        print(list(dr.glob('**/data/*.json')))







        #
        #
        #
        # proj_list = {}
        # data_dirs_list = {}
        # for projects in os.listdir(set.data_path):
        #     inproj = os.path.join(set.data_path, projects)
        #     proj_contents = {}
        #
        #
        #     proj_list[projects] = proj_contents
        #
        #
        #     print(projects)
        #     for dirs in os.listdir(inproj):
        #         print(os.path.join(inproj, dirs))
        #         if os.path.isdir(os.path.join(inproj, dirs)):
        #             try:
        #                 data_dirs_list[dirs][projects] = " "
        #             except KeyError:
        #                 data_dirs_list[dirs] = {}
        #                 data_dirs_list[dirs][projects] = " "
        #
        # print(proj_list)
        # print(data_dirs_list)
        # i = 0
        # for root, dirs, files in os.walk(set.data_path):
        #     if root == set.data_path:
        #         print("get projects")
        #         self.projects = dirs.copy()
        #     print(i,": ",root, "contains", len(files), "non-directory files")
        #     print(i,"dirs:",dirs)
        #     i += 1
        #     # print(" ",dirs)
        #     # print(" ",files)
        # print(self.projects)
        #
        # print(set.data_path)