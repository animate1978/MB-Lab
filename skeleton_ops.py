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

from . import utils
from . import algorithms

logger = logging.getLogger(__name__)

ik_joints_head = ['IK_control_a_L_head', 'IK_control_a_R_head',
    'IK_control_ebw_L_head', 'IK_control_ebw_R_head', 'IK_control_fg01_L_head',
    'IK_control_fg01_R_head', 'IK_control_fg02_L_head', 'IK_control_fg02_R_head',
    'IK_control_fg03_L_head', 'IK_control_fg03_R_head', 'IK_control_fg04_L_head',
    'IK_control_fg04_R_head', 'IK_control_fg05_L_head', 'IK_control_fg05_R_head',
    'IK_control_fg06_L_head', 'IK_control_fg06_R_head', 'IK_control_ft_L_head',
    'IK_control_ft_R_head', 'IK_control_h_L_head', 'IK_control_h_R_head',
    'IK_control_hd_head', 'IK_control_hip_pos_head', 'IK_control_hl_L_head',
    'IK_control_hl_R_head', 'IK_control_kn_L_head', 'IK_control_kn_R_head',
    'IK_control_lsp_head', 'IK_control_ts_L_head', 'IK_control_ts_R_head',
    'IK_control_usp_head']

ik_joints_tail = ['IK_control_a_L_tail', 'IK_control_a_R_tail', 'IK_control_ebw_L_tail',
    'IK_control_ebw_R_tail', 'IK_control_fg01_L_tail', 'IK_control_fg01_R_tail',
    'IK_control_fg02_L_tail', 'IK_control_fg02_R_tail', 'IK_control_fg03_L_tail',
    'IK_control_fg03_R_tail', 'IK_control_fg04_L_tail', 'IK_control_fg04_R_tail',
    'IK_control_fg05_L_tail', 'IK_control_fg05_R_tail', 'IK_control_fg06_L_tail',
    'IK_control_fg06_R_tail', 'IK_control_ft_L_tail', 'IK_control_ft_R_tail',
    'IK_control_h_L_tail', 'IK_control_h_R_tail', 'IK_control_hd_tail',
    'IK_control_hip_pos_tail', 'IK_control_hl_L_tail', 'IK_control_hl_R_tail',
    'IK_control_kn_L_tail', 'IK_control_kn_R_tail', 'IK_control_lsp_tail',
    'IK_control_ts_L_tail', 'IK_control_ts_R_tail', 'IK_control_usp_tail']

normal_joints_head = ['abd_muscle_01_H_L_head', 'abd_muscle_01_H_R_head',
    'abd_muscle_01_L_head', 'abd_muscle_01_R_head', 'abd_muscle_01_T_L_head',
    'abd_muscle_01_T_R_head', 'bcs_muscle_01_H_L_head', 'bcs_muscle_01_H_R_head',
    'bcs_muscle_01_L_head', 'bcs_muscle_01_R_head', 'bcs_muscle_01_T_L_head',
    'bcs_muscle_01_T_R_head', 'bk_muscle_02_H_L_head', 'bk_muscle_02_H_R_head',
    'bk_muscle_02_L_head', 'bk_muscle_02_R_head', 'bk_muscle_02_T_L_head',
    'bk_muscle_02_T_R_head', 'breast_L_head', 'breast_R_head', 'calf_L_head',
    'calf_R_head', 'calf_twist_L_head', 'calf_twist_R_head', 'clavicle_L_head',
    'clavicle_R_head', 'foot_L_head', 'foot_R_head', 'glt_muscle_02_H_L_head',
    'glt_muscle_02_H_R_head', 'glt_muscle_02_L_head', 'glt_muscle_02_R_head',
    'glt_muscle_02_T_L_head', 'glt_muscle_02_T_R_head', 'hand_L_head', 'hand_R_head',
    'head_head', 'index00_L_head', 'index00_R_head', 'index01_L_head', 'index01_R_head',
    'index02_L_head', 'index02_R_head', 'index03_L_head', 'index03_R_head',
    'lgs_muscle_01_H_L_head', 'lgs_muscle_01_H_R_head', 'lgs_muscle_01_L_head',
    'lgs_muscle_01_R_head', 'lgs_muscle_01_T_L_head', 'lgs_muscle_01_T_R_head',
    'lgs_muscle_02_H_L_head', 'lgs_muscle_02_H_R_head', 'lgs_muscle_02_L_head',
    'lgs_muscle_02_R_head', 'lgs_muscle_02_T_L_head', 'lgs_muscle_02_T_R_head',
    'lgs_muscle_03_H_L_head', 'lgs_muscle_03_H_R_head', 'lgs_muscle_03_L_head',
    'lgs_muscle_03_R_head', 'lgs_muscle_03_T_L_head', 'lgs_muscle_03_T_R_head',
    'lgs_muscle_04_H_L_head', 'lgs_muscle_04_H_R_head', 'lgs_muscle_04_L_head',
    'lgs_muscle_04_R_head', 'lgs_muscle_04_T_L_head', 'lgs_muscle_04_T_R_head',
    'lgs_muscle_05_H_L_head', 'lgs_muscle_05_H_R_head', 'lgs_muscle_05_L_head',
    'lgs_muscle_05_R_head', 'lgs_muscle_05_T_L_head', 'lgs_muscle_05_T_R_head',
    'lowerarm_L_head', 'lowerarm_R_head', 'lowerarm_twist_L_head',
    'lowerarm_twist_R_head', 'lwrl_muscle_01_H_L_head', 'lwrl_muscle_01_H_R_head',
    'lwrl_muscle_01_L_head', 'lwrl_muscle_01_R_head', 'lwrl_muscle_01_T_L_head',
    'lwrl_muscle_01_T_R_head', 'lwrl_muscle_02_H_L_head', 'lwrl_muscle_02_H_R_head',
    'lwrl_muscle_02_L_head', 'lwrl_muscle_02_R_head', 'lwrl_muscle_02_T_L_head',
    'lwrl_muscle_02_T_R_head', 'lwrl_muscle_03_H_L_head', 'lwrl_muscle_03_H_R_head',
    'lwrl_muscle_03_L_head', 'lwrl_muscle_03_R_head', 'lwrl_muscle_03_T_L_head',
    'lwrl_muscle_03_T_R_head', 'lwrl_muscle_04_H_L_head', 'lwrl_muscle_04_H_R_head',
    'lwrl_muscle_04_L_head', 'lwrl_muscle_04_R_head', 'lwrl_muscle_04_T_L_head',
    'lwrl_muscle_04_T_R_head', 'lwrm_muscle_01_H_L_head', 'lwrm_muscle_01_H_R_head',
    'lwrm_muscle_01_L_head', 'lwrm_muscle_01_R_head', 'lwrm_muscle_01_T_L_head',
    'lwrm_muscle_01_T_R_head', 'lwrm_muscle_02_H_L_head', 'lwrm_muscle_02_H_R_head',
    'lwrm_muscle_02_L_head', 'lwrm_muscle_02_R_head', 'lwrm_muscle_02_T_L_head',
    'lwrm_muscle_02_T_R_head', 'lwrm_muscle_03_H_L_head', 'lwrm_muscle_03_H_R_head',
    'lwrm_muscle_03_L_head', 'lwrm_muscle_03_R_head', 'lwrm_muscle_03_T_L_head',
    'lwrm_muscle_03_T_R_head', 'lwrm_muscle_04_H_L_head', 'lwrm_muscle_04_H_R_head',
    'lwrm_muscle_04_L_head', 'lwrm_muscle_04_R_head', 'lwrm_muscle_04_T_L_head',
    'lwrm_muscle_04_T_R_head', 'middle00_L_head', 'middle00_R_head', 'middle01_L_head',
    'middle01_R_head', 'middle02_L_head', 'middle02_R_head', 'middle03_L_head',
    'middle03_R_head', 'neck_head', 'nk_muscle_01_H_L_head', 'nk_muscle_01_H_R_head',
    'nk_muscle_01_L_head', 'nk_muscle_01_R_head', 'nk_muscle_01_T_L_head',
    'nk_muscle_01_T_R_head', 'nk_muscle_02_H_L_head', 'nk_muscle_02_H_R_head',
    'nk_muscle_02_T_L_head', 'nk_muscle_02_T_R_head', 'nk_muscle_03_H_head',
    'nk_muscle_03_T_head', 'nk_muscle_03_head', 'nk_muscle_04_H_head',
    'nk_muscle_04_T_head', 'nk_muscle_04_head', 'pct_muscle_01_H_L_head',
    'pct_muscle_01_H_R_head', 'pct_muscle_01_L_head', 'pct_muscle_01_R_head',
    'pct_muscle_01_T_L_head', 'pct_muscle_01_T_R_head', 'pelvis_head', 'pinky00_L_head',
    'pinky00_R_head', 'pinky01_L_head', 'pinky01_R_head', 'pinky02_L_head',
    'pinky02_R_head', 'pinky03_L_head', 'pinky03_R_head', 'ring00_L_head',
    'ring00_R_head', 'ring01_L_head', 'ring01_R_head', 'ring02_L_head', 'ring02_R_head',
    'ring03_L_head', 'ring03_R_head', 'root_head', 'rot_helper01_L_head',
    'rot_helper01_R_head', 'rot_helper02_L_head', 'rot_helper02_R_head',
    'rot_helper03_L_head', 'rot_helper03_R_head', 'rot_helper04_L_head',
    'rot_helper04_R_head', 'rot_helper06_L_head', 'rot_helper06_R_head',
    'shld_muscle01_H_L_head', 'shld_muscle01_H_R_head', 'shld_muscle01_L_head',
    'shld_muscle01_R_head', 'shld_muscle01_T_L_head', 'shld_muscle01_T_R_head',
    'shld_muscle02_H_L_head', 'shld_muscle02_H_R_head', 'shld_muscle02_L_head',
    'shld_muscle02_R_head', 'shld_muscle02_T_L_head', 'shld_muscle02_T_R_head',
    'spine01_head', 'spine02_head', 'spine03_head', 'spn_muscle_01_H_head',
    'spn_muscle_01_T_head', 'spn_muscle_01_head', 'struct_ft01_L_head',
    'struct_ft01_R_head', 'struct_ft02_L_head', 'struct_ft02_R_head',
    'struct_ft03_L_head', 'struct_ft03_R_head', 'struct_hd_head', 'struct_nk_head',
    'tcs_muscle_01_H_L_head', 'tcs_muscle_01_H_R_head', 'tcs_muscle_01_L_head',
    'tcs_muscle_01_R_head', 'tcs_muscle_01_T_L_head', 'tcs_muscle_01_T_R_head',
    'thigh_L_head', 'thigh_R_head', 'thigh_twist_L_head', 'thigh_twist_R_head',
    'thumb01_L_head', 'thumb01_R_head', 'thumb02_L_head', 'thumb02_R_head',
    'thumb03_L_head', 'thumb03_R_head', 'toes_L_head', 'toes_R_head', 'upperarm_L_head',
    'upperarm_R_head', 'upperarm_twist_L_head', 'upperarm_twist_R_head']

normal_joints_tail = ['abd_muscle_01_H_L_tail', 'abd_muscle_01_H_R_tail',
    'abd_muscle_01_L_tail', 'abd_muscle_01_R_tail', 'abd_muscle_01_T_L_tail',
    'abd_muscle_01_T_R_tail', 'bcs_muscle_01_H_L_tail', 'bcs_muscle_01_H_R_tail',
    'bcs_muscle_01_L_tail', 'bcs_muscle_01_R_tail', 'bcs_muscle_01_T_L_tail',
    'bcs_muscle_01_T_R_tail', 'bk_muscle_02_H_L_tail', 'bk_muscle_02_H_R_tail',
    'bk_muscle_02_L_tail', 'bk_muscle_02_R_tail', 'bk_muscle_02_T_L_tail',
    'bk_muscle_02_T_R_tail', 'breast_L_tail', 'breast_R_tail', 'calf_L_tail',
    'calf_R_tail', 'calf_twist_L_tail', 'calf_twist_R_tail', 'clavicle_L_tail',
    'clavicle_R_tail', 'foot_L_tail', 'foot_R_tail', 'glt_muscle_02_H_L_tail',
    'glt_muscle_02_H_R_tail', 'glt_muscle_02_L_tail', 'glt_muscle_02_R_tail',
    'glt_muscle_02_T_L_tail', 'glt_muscle_02_T_R_tail', 'hand_L_tail', 'hand_R_tail',
    'head_tail', 'index00_L_tail', 'index00_R_tail', 'index01_L_tail', 'index01_R_tail',
    'index02_L_tail', 'index02_R_tail', 'index03_L_tail', 'index03_R_tail',
    'lgs_muscle_01_H_L_tail', 'lgs_muscle_01_H_R_tail', 'lgs_muscle_01_L_tail',
    'lgs_muscle_01_R_tail', 'lgs_muscle_01_T_L_tail', 'lgs_muscle_01_T_R_tail',
    'lgs_muscle_02_H_L_tail', 'lgs_muscle_02_H_R_tail', 'lgs_muscle_02_L_tail',
    'lgs_muscle_02_R_tail', 'lgs_muscle_02_T_L_tail', 'lgs_muscle_02_T_R_tail',
    'lgs_muscle_03_H_L_tail', 'lgs_muscle_03_H_R_tail', 'lgs_muscle_03_L_tail',
    'lgs_muscle_03_R_tail', 'lgs_muscle_03_T_L_tail', 'lgs_muscle_03_T_R_tail',
    'lgs_muscle_04_H_L_tail', 'lgs_muscle_04_H_R_tail', 'lgs_muscle_04_L_tail',
    'lgs_muscle_04_R_tail', 'lgs_muscle_04_T_L_tail', 'lgs_muscle_04_T_R_tail',
    'lgs_muscle_05_H_L_tail', 'lgs_muscle_05_H_R_tail', 'lgs_muscle_05_L_tail',
    'lgs_muscle_05_R_tail', 'lgs_muscle_05_T_L_tail', 'lgs_muscle_05_T_R_tail',
    'lowerarm_L_tail', 'lowerarm_R_tail', 'lowerarm_twist_L_tail',
    'lowerarm_twist_R_tail', 'lwrl_muscle_01_H_L_tail', 'lwrl_muscle_01_H_R_tail',
    'lwrl_muscle_01_L_tail', 'lwrl_muscle_01_R_tail', 'lwrl_muscle_01_T_L_tail',
    'lwrl_muscle_01_T_R_tail', 'lwrl_muscle_02_H_L_tail', 'lwrl_muscle_02_H_R_tail',
    'lwrl_muscle_02_L_tail', 'lwrl_muscle_02_R_tail', 'lwrl_muscle_02_T_L_tail',
    'lwrl_muscle_02_T_R_tail', 'lwrl_muscle_03_H_L_tail', 'lwrl_muscle_03_H_R_tail',
    'lwrl_muscle_03_L_tail', 'lwrl_muscle_03_R_tail', 'lwrl_muscle_03_T_L_tail',
    'lwrl_muscle_03_T_R_tail', 'lwrl_muscle_04_H_L_tail', 'lwrl_muscle_04_H_R_tail',
    'lwrl_muscle_04_L_tail', 'lwrl_muscle_04_R_tail', 'lwrl_muscle_04_T_L_tail',
    'lwrl_muscle_04_T_R_tail', 'lwrm_muscle_01_H_L_tail', 'lwrm_muscle_01_H_R_tail',
    'lwrm_muscle_01_L_tail', 'lwrm_muscle_01_R_tail', 'lwrm_muscle_01_T_L_tail',
    'lwrm_muscle_01_T_R_tail', 'lwrm_muscle_02_H_L_tail', 'lwrm_muscle_02_H_R_tail',
    'lwrm_muscle_02_L_tail', 'lwrm_muscle_02_R_tail', 'lwrm_muscle_02_T_L_tail',
    'lwrm_muscle_02_T_R_tail', 'lwrm_muscle_03_H_L_tail', 'lwrm_muscle_03_H_R_tail',
    'lwrm_muscle_03_L_tail', 'lwrm_muscle_03_R_tail', 'lwrm_muscle_03_T_L_tail',
    'lwrm_muscle_03_T_R_tail', 'lwrm_muscle_04_H_L_tail', 'lwrm_muscle_04_H_R_tail',
    'lwrm_muscle_04_L_tail', 'lwrm_muscle_04_R_tail', 'lwrm_muscle_04_T_L_tail',
    'lwrm_muscle_04_T_R_tail', 'middle00_L_tail', 'middle00_R_tail', 'middle01_L_tail',
    'middle01_R_tail', 'middle02_L_tail', 'middle02_R_tail', 'middle03_L_tail',
    'middle03_R_tail', 'neck_tail', 'nk_muscle_01_H_L_tail', 'nk_muscle_01_H_R_tail',
    'nk_muscle_01_L_tail', 'nk_muscle_01_R_tail', 'nk_muscle_01_T_L_tail',
    'nk_muscle_01_T_R_tail', 'nk_muscle_02_H_L_tail', 'nk_muscle_02_H_R_tail',
    'nk_muscle_02_L_tail', 'nk_muscle_02_R_tail', 'nk_muscle_02_T_L_tail',
    'nk_muscle_02_T_R_tail', 'nk_muscle_03_H_tail', 'nk_muscle_03_T_tail',
    'nk_muscle_03_tail', 'nk_muscle_04_H_tail', 'nk_muscle_04_T_tail',
    'nk_muscle_04_tail', 'pct_muscle_01_H_L_tail', 'pct_muscle_01_H_R_tail',
    'pct_muscle_01_L_tail', 'pct_muscle_01_R_tail', 'pct_muscle_01_T_L_tail',
    'pct_muscle_01_T_R_tail', 'pelvis_tail', 'pinky00_L_tail', 'pinky00_R_tail',
    'pinky01_L_tail', 'pinky01_R_tail', 'pinky02_L_tail', 'pinky02_R_tail',
    'pinky03_L_tail', 'pinky03_R_tail', 'ring00_L_tail', 'ring00_R_tail',
    'ring01_L_tail', 'ring01_R_tail', 'ring02_L_tail', 'ring02_R_tail',
    'ring03_L_tail', 'ring03_R_tail', 'root_tail', 'rot_helper01_L_tail',
    'rot_helper01_R_tail', 'rot_helper02_L_tail', 'rot_helper02_R_tail',
    'rot_helper03_L_tail', 'rot_helper03_R_tail', 'rot_helper04_L_tail',
    'rot_helper04_R_tail', 'rot_helper06_L_tail', 'rot_helper06_R_tail',
    'shld_muscle01_H_L_tail', 'shld_muscle01_H_R_tail', 'shld_muscle01_L_tail',
    'shld_muscle01_R_tail', 'shld_muscle01_T_L_tail', 'shld_muscle01_T_R_tail',
    'shld_muscle02_H_L_tail', 'shld_muscle02_H_R_tail', 'shld_muscle02_L_tail',
    'shld_muscle02_R_tail', 'shld_muscle02_T_L_tail', 'shld_muscle02_T_R_tail',
    'spine01_tail', 'spine02_tail', 'spine03_tail', 'spn_muscle_01_H_tail',
    'spn_muscle_01_T_tail', 'spn_muscle_01_tail', 'struct_ft01_L_tail',
    'struct_ft01_R_tail', 'struct_ft02_L_tail', 'struct_ft02_R_tail',
    'struct_ft03_L_tail', 'struct_ft03_R_tail', 'struct_hd_tail', 'struct_nk_tail',
    'tcs_muscle_01_H_L_tail', 'tcs_muscle_01_H_R_tail', 'tcs_muscle_01_L_tail',
    'tcs_muscle_01_R_tail', 'tcs_muscle_01_T_L_tail', 'tcs_muscle_01_T_R_tail',
    'thigh_L_tail', 'thigh_R_tail', 'thigh_twist_L_tail', 'thigh_twist_R_tail',
    'thumb01_L_tail', 'thumb01_R_tail', 'thumb02_L_tail', 'thumb02_R_tail',
    'thumb03_L_tail', 'thumb03_R_tail', 'toes_L_tail', 'toes_R_tail', 'upperarm_L_tail',
    'upperarm_R_tail', 'upperarm_twist_L_tail', 'upperarm_twist_R_tail']

base_bones = ['breast_L', 'breast_R', 'calf_L', 'calf_R', 'calf_twist_L',
    'calf_twist_R', 'clavicle_L', 'clavicle_R', 'foot_L', 'foot_R',
    'hand_L', 'hand_R', 'head', 'index00_L', 'index00_R', 'index01_L',
    'index01_R', 'index02_L', 'index02_R', 'index03_L', 'index03_R',
    'lowerarm_L', 'lowerarm_R', 'lowerarm_twist_L', 'lowerarm_twist_R',
    'middle00_L', 'middle00_R', 'middle01_L', 'middle01_R', 'middle02_L',
    'middle02_R', 'middle03_L', 'middle03_R', 'neck', 'pelvis',
    'pinky00_L', 'pinky00_R', 'pinky01_L', 'pinky01_R', 'pinky02_L',
    'pinky02_R', 'pinky03_L', 'pinky03_R', 'ring00_L', 'ring00_R',
    'ring01_L', 'ring01_R', 'ring02_L', 'ring02_R', 'ring03_L',
    'ring03_R', 'spine01', 'spine02', 'spine03', 'thigh_L', 'thigh_R',
    'thigh_twist_L', 'thigh_twist_R', 'thumb01_L', 'thumb01_R',
    'thumb02_L', 'thumb02_R', 'thumb03_L', 'thumb03_R', 'toes_L',
    'toes_R', 'upperarm_L', 'upperarm_R', 'upperarm_twist_L',
    'upperarm_twist_R']

muscle_bones = ['abd_muscle_01_L', 'abd_muscle_01_R', 'bcs_muscle_01_L',
    'bcs_muscle_01_R', 'bk_muscle_02_L', 'bk_muscle_02_R', 'breast_L',
    'breast_R', 'calf_L', 'calf_R', 'clavicle_L', 'clavicle_R', 'foot_L',
    'foot_R', 'glt_muscle_02_L', 'glt_muscle_02_R', 'hand_L', 'hand_R',
    'head', 'index00_L', 'index00_R', 'index01_L', 'index01_R',
    'index02_L', 'index02_R', 'index03_L', 'index03_R',
    'lgs_muscle_01_L', 'lgs_muscle_01_R', 'lgs_muscle_02_L',
    'lgs_muscle_02_R', 'lgs_muscle_03_L', 'lgs_muscle_03_R',
    'lgs_muscle_04_L', 'lgs_muscle_04_R', 'lgs_muscle_05_L',
    'lgs_muscle_05_R', 'lowerarm_L', 'lowerarm_R',
    'lowerleg_muscle_01_L', 'lowerleg_muscle_01_R',
    'lwrl_muscle_01_L', 'lwrl_muscle_01_R', 'lwrl_muscle_02_L',
    'lwrl_muscle_02_R', 'lwrl_muscle_03_L', 'lwrl_muscle_03_R',
    'lwrl_muscle_04_L', 'lwrl_muscle_04_R', 'lwrm_muscle_01_L',
    'lwrm_muscle_01_R', 'lwrm_muscle_02_L', 'lwrm_muscle_02_R',
    'lwrm_muscle_03_L', 'lwrm_muscle_03_R', 'lwrm_muscle_04_L',
    'lwrm_muscle_04_R', 'middle00_L', 'middle00_R', 'middle01_L',
    'middle01_R', 'middle02_L', 'middle02_R', 'middle03_L', 'middle03_R',
    'neck', 'nk_muscle_01_L', 'nk_muscle_01_R', 'nk_muscle_02_L',
    'nk_muscle_02_R', 'nk_muscle_03', 'nk_muscle_04', 'pct_muscle_01_L',
    'pct_muscle_01_R', 'pelvis', 'pinky00_L', 'pinky00_R', 'pinky01_L',
    'pinky01_R', 'pinky02_L', 'pinky02_R', 'pinky03_L', 'pinky03_R',
    'ring00_L', 'ring00_R', 'ring01_L', 'ring01_R', 'ring02_L',
    'ring02_R', 'ring03_L', 'ring03_R', 'shld_muscle01_L',
    'shld_muscle01_R', 'shld_muscle02_L', 'shld_muscle02_R', 'spine01',
    'spine02', 'spine03', 'spn_muscle_01', 'tcs_muscle_01_L',
    'tcs_muscle_01_R', 'thigh_L', 'thigh_R', 'thumb01_L', 'thumb01_R',
    'thumb02_L', 'thumb02_R', 'thumb03_L', 'thumb03_R', 'toes_L',
    'toes_R', 'upperarm_L', 'upperarm_R']
    
# ------------------------------------------------------------------------
#    All methods to help creating skeleton
# ------------------------------------------------------------------------

# Returns a list of joints.
def sort_joints(ik=False, head=False, content=[]):
    global ik_joints_head
    global ik_joints_tail
    global normal_joints_head
    global normal_joints_tail
    final_list = []
    tmp = []
    if ik:
        if head:
            tmp = ik_joints_head
        else:
            tmp = ik_joints_tail
    elif head:
        tmp = normal_joints_head
    else:
        tmp = normal_joints_tail
    # Now we sort or not what the name must contain.
    if len(content) < 1:
        return tmp
    return utils.sort_str_content(tmp, contains=content, constraint_and=True)

def get_enum_prop_joints(ik=False, head=False, contains=[]):
    final_list = sort_joints(ik, head, contains)
    return algorithms.create_enum_property_items(final_list)
        