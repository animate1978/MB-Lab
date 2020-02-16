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
# Teto for this part.

import logging
import json
import os
import bpy
import numpy
from . import algorithms

standard_expressions_list = ["abdomExpansion_min", "abdomExpansion_max",
    "browOutVertL_min", "browOutVertL_max", "browOutVertR_min",
    "browOutVertR_max", "browsMidVert_min", "browsMidVert_max",
    "browSqueezeL_min", "browSqueezeL_max", "browSqueezeR_min",
    "browSqueezeR_max", "cheekSneerL_max", "cheekSneerR_max",
    "chestExpansion_min", "chestExpansion_max", "deglutition_min",
    "deglutition_max", "eyeClosedL_min", "eyeClosedL_max",
    "eyeClosedPressureL_min", "eyeClosedPressureL_max",
    "eyeClosedPressureR_min", "eyeClosedPressureR_max",
    "eyeClosedR_min", "eyeClosedR_max", "eyesHoriz_min",
    "eyesHoriz_max", "eyeSquintL_min", "eyeSquintL_max",
    "eyeSquintR_min", "eyeSquintR_max", "eyesSmile_max",
    "eyesVert_min", "eyesVert_max", "jawHoriz_min", "jawHoriz_max",
    "jawOut_min", "jawOut_max", "mouthBite_min", "mouthBite_max",
    "mouthChew_min", "mouthChew_max", "mouthClosed_min",
    "mouthClosed_max", "mouthHoriz_min", "mouthHoriz_max",
    "mouthInflated_min", "mouthInflated_max", "mouthLowerOut_min",
    "mouthLowerOut_max", "mouthOpen_min", "mouthOpen_max",
    "mouthOpenAggr_min", "mouthOpenAggr_max", "mouthOpenHalf_max",
    "mouthOpenLarge_min", "mouthOpenLarge_max", "mouthOpenO_min",
    "mouthOpenO_max", "mouthOpenTeethClosed_min",
    "mouthOpenTeethClosed_max", "mouthSmile_min", "mouthSmile_max",
    "mouthSmileL_max", "mouthSmileOpen_min", "mouthSmileOpen_max",
    "mouthSmileOpen2_min", "mouthSmileOpen2_max", "mouthSmileR_max",
    "nostrilsExpansion_min", "nostrilsExpansion_max",
    "pupilsDilatation_min", "pupilsDilatation_max", "tongueHoriz_min",
    "tongueHoriz_max", "tongueOut_min", "tongueOut_max",
    "tongueOutPressure_max", "tongueTipUp_max", "tongueVert_min",
    "tongueVert_max"]

standard_expressions = [("AA", "abdomExpansion_min", "abdomen"),
    ("AB", "abdomExpansion_max", "abdomen"),
    ("AC", "browOutVertL_min", "brow"),
    ("AD", "browOutVertL_max", "brow"),
    ("AE", "browOutVertR_min", "brow"),
    ("AF", "browOutVertR_max", "brow"),
    ("AG", "browsMidVert_min", "brow"),
    ("AH", "browsMidVert_max", "brow"),
    ("AI", "browSqueezeL_min", "brow"),
    ("AJ", "browSqueezeL_max", "brow"),
    ("AK", "browSqueezeR_min", "brow"),
    ("AL", "browSqueezeR_max", "brow"),
    ("AM", "cheekSneerL_max", "cheek"),
    ("AN", "cheekSneerR_max", "cheek"),
    ("AO", "chestExpansion_min", "chest"),
    ("AP", "chestExpansion_max", "chest"),
    ("AQ", "deglutition_min", "deglutition"),
    ("AR", "deglutition_max", "deglutition"),
    ("AS", "eyeClosedL_min", "eye"),
    ("AT", "eyeClosedL_max", "eye"),
    ("AU", "eyeClosedPressureL_min", "eye"),
    ("AV", "eyeClosedPressureL_max", "eye"),
    ("AW", "eyeClosedPressureR_min", "eye"),
    ("AX", "eyeClosedPressureR_max", "eye"),
    ("AY", "eyeClosedR_min", "eye"),
    ("AY", "eyeClosedR_max", "eye"),
    ("AZ", "eyesHoriz_min", "eye"),
    ("BA", "eyesHoriz_max", "eye"),
    ("BB", "eyeSquintL_min", "eye"),
    ("BC", "eyeSquintL_max", "eye"),
    ("BD", "eyeSquintR_min", "eye"),
    ("BE", "eyeSquintR_max", "eye"),
    ("BF", "eyesSmile_max", "eye"),
    ("BG", "eyesVert_min", "eye"),
    ("BH", "eyesVert_max", "eye"),
    ("BI", "jawHoriz_min", "jaw"),
    ("BJ", "jawHoriz_max", "jaw"),
    ("BK", "jawOut_min", "jaw"),
    ("BL", "jawOut_max", "jaw"),
    ("BM", "mouthBite_min", "mouth"),
    ("BN", "mouthBite_max", "mouth"),
    ("BO", "mouthChew_min", "mouth"),
    ("BP", "mouthChew_max", "mouth"),
    ("BQ", "mouthClosed_min", "mouth"),
    ("BR", "mouthClosed_max", "mouth"),
    ("BS", "mouthHoriz_min", "mouth"),
    ("BT", "mouthHoriz_max", "mouth"),
    ("BU", "mouthInflated_min", "mouth"),
    ("BV", "mouthInflated_max", "mouth"),
    ("BW", "mouthLowerOut_min", "mouth"),
    ("BX", "mouthLowerOut_max", "mouth"),
    ("BY", "mouthOpen_min", "mouth"),
    ("BZ", "mouthOpen_max", "mouth"),
    ("CA", "mouthOpenAggr_min", "mouth"),
    ("CB", "mouthOpenAggr_max", "mouth"),
    ("CC", "mouthOpenHalf_max", "mouth"),
    ("CD", "mouthOpenLarge_min", "mouth"),
    ("CE", "mouthOpenLarge_max", "mouth"),
    ("CF", "mouthOpenO_min", "mouth"),
    ("CG", "mouthOpenO_max", "mouth"),
    ("CH", "mouthOpenTeethClosed_min", "mouth"),
    ("CI", "mouthOpenTeethClosed_max", "mouth"),
    ("CJ", "mouthSmile_min", "mouth"),
    ("CK", "mouthSmile_max", "mouth"),
    ("CL", "mouthSmileL_max", "mouth"),
    ("CM", "mouthSmileOpen_min", "mouth"),
    ("CN", "mouthSmileOpen_max", "mouth"),
    ("CO", "mouthSmileOpen2_min", "mouth"),
    ("CP", "mouthSmileOpen2_max", "mouth"),
    ("CQ", "mouthSmileR_max", "mouth"),
    ("CR", "nostrilsExpansion_min", "nostrils"),
    ("CS", "nostrilsExpansion_max", "nostrils"),
    ("CT", "pupilsDilatation_min", "pupils"),
    ("CU", "pupilsDilatation_max", "pupils"),
    ("CV", "tongueHoriz_min", "tongue"),
    ("CW", "tongueHoriz_max", "tongue"),
    ("CX", "tongueOut_min", "tongue"),
    ("CY", "tongueOut_max", "tongue"),
    ("CZ", "tongueOutPressure_max", "tongue"),
    ("DA", "tongueTipUp_max", "tongue"),
    ("DB", "tongueVert_min", "tongue"),
    ("DC", "tongueVert_max", "tongue"),
    ("NE", "NEW (overwrite below)", "new")]

body_parts_expr = [
    ("AB", "abdom", ""),
    ("BR", "brow", ""),
    ("CH", "cheek", ""),
    ("CE", "chest", ""),
    ("DE", "deglutition", ""),
    ("EY", "eye", ""),
    ("JA", "jaw", ""),
    ("MO", "mouth", ""),
    ("NO", "nostrils", ""),
    ("PU", "pupils", ""),
    ("TO", "tongue", ""),
    ("NE", "NEW (below)", "")]

min_max_expr = [("MI", "min", "min = 0"),
   ("MA", "max", "max = 1")]

expression_ID_list = [("HU", "Humans", "Standard in MB-Lab"),
   ("AN", "Anime", "Standard in MB-Lab"),
   ("OT", "OTHER", "For another model")
   ]

expression_name = ["", "", 0]
#the number is for autosaves.

#operator_for_base_expr = {}

logger = logging.getLogger(__name__)

def get_standard_expressions_list():
    return standard_expressions_list

def get_standard_base_expr(key=None):
    if key == None:
        return standard_expressions
    value = None
    for index in range(len(standard_expressions)):
        if key in standard_expressions[index]:
            value = standard_expressions[index]
            return value[1]
    return ""

def get_body_parts_expr(key=None):
    if key == None:
        return body_parts_expr
    value = None
    for index in range(len(body_parts_expr)):
        if key in body_parts_expr[index]:
            value = body_parts_expr[index]
            return value[1]
    return ""

def get_min_max_expr(key=None):
    if key == None:
        return min_max_expr
    value = None
    for index in range(len(min_max_expr)):
        if key in min_max_expr[index]:
            value = min_max_expr[index]
            return value[1]
    return ""

def set_expression_name(name):
    global expression_name
    expression_name[0] = name

def get_expression_name():
    return expression_name[0]

def set_expression_ID(id):
    global expression_name
    expression_name[1] = "Expressions_ID" + id + "_max"

def get_expression_ID():
    return expression_name[1]

def get_expression_ID_list():
    return expression_ID_list
    
def get_next_number():
    expression_name[2] += 1
    if expression_name[2] < 10:
        return "00" + str(expression_name[2])
    elif expression_name[2] < 100:
        return "0" + str(expression_name[2])
    elif expression_name[2] > 999:
        return "999"
    return str(expression_name[2])

def get_all_expression_files(data_path, data_type_path, body_type):
    #Get all files in morphs directory, with standard ones.
    #Used when the engine loads expressions librairies.
    dir = os.path.join(data_path, data_type_path)
    found_files = []
    body_type_split = body_type.split('_')[:2]
    list = os.listdir(dir)
    for item in list:
        if item == body_type:
            found_files += [os.path.join(dir, item)]
    for item in list:
        if item.split('_')[:2] == body_type_split and item != body_type:
            found_files += [os.path.join(dir, item)]
    return found_files

"""def add_operator(name, operator):
    operator_for_base_expr[name] = operator

def reset_operator():
    global operator_for_base_expr
    operator_for_base_expr.clear()
"""