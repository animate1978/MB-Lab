import bpy
import logging
import os
import json
from bpy_extras.io_utils import ExportHelper, ImportHelper
from bpy.app.handlers import persistent
from . import humanoid, animationengine, proxyengine
from . import facerig
from . import algorithms
import time
import ctypes
import sys
import platform
import random
from bpy.props import EnumProperty, StringProperty, BoolVectorProperty

random.seed(23483)
addon_path = os.path.dirname(os.path.realpath(__file__))
yasp_sphinx_dir = os.path.join(addon_path, "yasp", "sphinxinstall", "lib")
yasp_libs_dir = os.path.join(addon_path, "yasp", "yaspbin")
sys.path.append(yasp_libs_dir)
pocketsphinxlib = None
sphinxadlib = None
sphinxbaselib = None
yasplib = None
libs_loaded = True

logger = logging.getLogger(__name__)

# Load the .so files we need
# Then import yasp
# Now we're ready to do some speech parsing
def yasp_load_dep():
    global libs_loaded
    pocketsphinx = os.path.join(yasp_sphinx_dir, "libpocketsphinx.so")
    sphinxad = os.path.join(yasp_sphinx_dir, "libsphinxad.so")
    sphinxbase = os.path.join(yasp_sphinx_dir, "libsphinxbase.so")
    yasp = os.path.join(yasp_libs_dir, "_yasp.so")
    if not os.path.exists(pocketsphinx) or \
       not os.path.exists(sphinxad) or \
       not os.path.exists(sphinxbase) or \
       not os.path.exists(yasp):
           logger.critical("libraries don't exist. Reinstall")
    try:
        sphinxbaselib = ctypes.cdll.LoadLibrary(os.path.abspath(sphinxbase))
        sphinxadlib = ctypes.cdll.LoadLibrary(os.path.abspath(sphinxad))
        pocketsphinxlib = ctypes.cdll.LoadLibrary(os.path.abspath(pocketsphinx))
        yasplib = ctypes.cdll.LoadLibrary(os.path.abspath(yasp))
    except Exception as e:
        print(e)
        logger.critical("Failed to load libraries")
        libs_loaded = False


if platform.system() == "Linux":
    yasp_load_dep()
    if libs_loaded:
        import yasp

# class maps yasp phoneme Mapper
# YASP produces a more nuanced phonemes. We need to reduce that to the set
# of phonemes which we use for the animation
class YASP2MBPhonemeMapper(object):
    def __init__(self):
        self.yasp_2_mb_phoneme_map = None
        data_path = algorithms.get_data_path()
        if not data_path:
            logger.critical("CRITICAL", "%s not found. Please check your Blender addons directory. Might need to reinstall ManuelBastioniLab", data_path)
            raise ValueError("No Data directory")

        map_file = os.path.join(data_path, 'face_rig', 'yasp_map.json')
        if not map_file:
            logger.critical("CRITICAL", "%s not found. Please check your Blender addons directory. Might need to reinstall ManuelBastioniLab", map_file)
        with open(map_file, 'r') as f:
            self.yasp_2_mb_phoneme_map = json.load(f)

    def get_phoneme_animation_data(self, phoneme):
        try:
            anim_data = self.yasp_2_mb_phoneme_map[phoneme]
        except:
            return None
        return anim_data

class Bone(object):
    def __init__(self, bone):
        # keeps the frame number of the keyframe, the value of the
        # z rotation and boolean if it's fake or real.
        self.animation_data = {}
        self.mybone = bone

    def get_name(self):
        return self.mybone.name

    # inserts an actual keyframe if actual=True. If actual=False then it
    # inserts it in the list, but doesn't create a keyframe. The purpose
    # of that is we might want to do a heuristics pass over the keyframes
    # to clean it up.
    def insert_keyframe(self, frame, value):
        self.animation_data[frame] = value

    def del_keyframe(self, frame):
        try:
            self.mybone.keyframe_delete('rotation_quaternion', index=3, frame=frame)
        except:
            return

    def del_keyframes(self):
        for k, v in self.animation_data.items():
            try:
                self.mybone.keyframe_delete('rotation_quaternion', index=3,
                                            frame=k)
            except:
                return
        self.animation_data = {}

    def animate(self):
        for k, v in self.animation_data.items():
            self.mybone.rotation_quaternion[3] = v
            self.mybone.keyframe_insert('rotation_quaternion', index=3, frame=k)

    # run our list of heuristics over the list of keyframes we have
    # 01 Heuristic: If a bone is being reset to 0 and it has been set to
    # some other value less than 5 frames before, or is going to be
    # set to another value less than 5 frames after, then skip setting
    # that bone
    # 02 Heuristic: If a bone is being set to some value != 0, but it has
    # been set to 0 or some other value < 5 frames before, and it's
    # going to be set to another value != 0 < 5 frames after, then
    # recalculate the value of this key frame to be the average of the
    # two constraining key frames.
    # 03 Heuristic: If a bone is being set to some value != 0 but it
    # has been set to some value != 0 < 5 frames before, and it's
    # going to be set to another value >= 0 < 5 frames after, then set
    # the value of that keyframe to be the average of the two
    # constraining keyframes.
    # 04 Heuristic: if the time between the end of the word and the start
    # of the next one is greater than 15 frames, then the mouth should be
    # closed. if it's greater than 20 frames then key frames to close the
    # mouth are inserted 5 frames after the word and 5 frames before the
    # next one
    def heuristic_pass(self):
        prev_k = 0
        key_list = list(self.animation_data.keys())
        value_list = list(self.animation_data.values())
        num_kf = len(key_list)
        # the animation data is in chronological order
        i = 0
        for k in key_list:
            if i == 0 or i == (num_kf - 1):
                i = i + 1
                continue
            prev_key = key_list[i-1]
            next_key = key_list[i+1]
            if k - prev_key <= 2 and next_key - k <= 2:
                self.animation_data[k] = (value_list[i-1] + value_list[i+1]) / 2
            i = i + 1
        return

    def heuristic_pass2(self, window_size):
        # Define a window, where the current key frame is in the middle.
        # The current key frame is calculated as the average of the values
        # of the key frames surrounding it.
        if window_size == 0:
            return
        key_list = list(self.animation_data.keys())
        value_list = list(self.animation_data.values())
        num_kf = len(key_list)
        i = 0
        # this is a float for upper/lower calculations just convert it to
        # an int
        wsi = int(window_size)
        for k in key_list:
            upper = min(num_kf - 1, i + wsi)
            lower = min(i, i - wsi)
            lower = max(i, lower)
            total_value = 0
            for j in range(lower, upper):
                total_value = total_value + value_list[j]
            # use the float value to calculate the avg
            avg = total_value / window_size
            # don't drop the key frame value more than a 1/3 of its
            # original value
            avg = max(self.animation_data[k] - self.animation_data[k]/3, avg)
            self.animation_data[k] = avg
            i = i + 1

# each sequence can have multiple markers associated with it.
class Sequence(object):
    def __init__(self, seq):
        self.sequence = seq
        self.markers = []
        self.bones = {}
        self.bones_set = False

    def set_bones(self, bones):
        if self.bones_set == True:
            return

        self.bones_set = True

        for bone in bones:
            b = Bone(bone)
            self.bones[b.get_name()] = b

    # Markers are added in sequential order
    def add_marker(self, m):
        self.markers.append(m)

    def del_marker(self, m):
        if m in self.markers:
            self.markers.remove(m)

    def rm_marker_from_scene(self, scn):
        for m in self.markers:
            scn.timeline_markers.remove(m)
        self.markers = []

    def is_sequence(self, s):
        return (self.sequence == s)

    def mark_seq_at_frame(self, mname, frame, scn):
        m = scn.timeline_markers.new(mname, frame=frame)
        self.add_marker(m)

    def move_to_next_marker(self, scn):
        cur_frame = scn.frame_current
        found = False
        for m in self.markers:
            if m.frame > cur_frame:
                found = True
                break
        if found:
            scn.frame_current = m.frame

    def move_to_prev_marker(self, scn):
        cur_frame = scn.frame_current
        found = False
        for m in reversed(self.markers):
            if m.frame < cur_frame:
                found = True
                break
        if found:
            scn.frame_current = m.frame

    def reset_all_bones(self, frame):
        for k, bone in self.bones.items():
            bone.insert_keyframe(frame, 0)

    def set_keyframe(self, m, pm, idx):
        delta = 0
        # Heuristic: If the delta between this marker and the previous
        # marker is >= 12 frames then we want to set a rest
        # in/out poses
        # Heuristic: If the delta is < 12 then we want to have a rest pose
        # in the middle
        if pm:
            delta = m.frame - pm.frame
        if delta >= 12:
            percent = round(delta * 0.08)
            percent2 = round(delta * 0.20)
            self.reset_all_bones(pm.frame + percent)
            self.set_random_rest_pose(pm.frame + percent2)
            self.set_random_rest_pose(m.frame - percent2)
            self.reset_all_bones(m.frame - percent)
        elif delta < 12 and delta > 7:
            self.reset_all_bones(pm.frame + round(delta/2))
            self.set_random_rest_pose(pm.frame + round(delta/2))

        if idx == 0:
            if (m.frame - 1) <= 5:
                frame = 1
            else:
                frame = m.frame - 5
            self.reset_all_bones(frame)
        self.reset_all_bones(m.frame)

        phonemes = yaspmapper.get_phoneme_animation_data(m.name)
        if not phonemes:
            logger.critical("Can't find corresponding mapping for:", m.name)
            return
        for phone in phonemes:
            bone_name = 'ph_'+phone[0]
            bone = self.bones[bone_name]
            bone.insert_keyframe(m.frame, phone[1])


    # go through the markers on the selected sequence.
    # for each marker look up the marker name in our mapper
    # Set the corresponding bones in the list to the values specified.
    def animate_all_markers(self):
        idx = 0
        bpy.ops.pose.select_all(action='DESELECT')
        pm = None
        # first pass is to create keyframe entries in every bone for each
        # marker
        for m in self.markers:
            self.set_keyframe(m, pm, idx)
            pm = m
            idx = idx + 1

        self.reset_all_bones(m.frame + 5)

        # second pass is to run a heuristic pass on the animation data and
        # animate
        for k, bone in self.bones.items():
            bone.heuristic_pass2(float(bpy.context.scene.yasp_avg_window_size))
            bone.animate()

    def animate_marker_at_frame(self, cur_frame):
        idx = 0
        found = False
        pm = None
        for m in self.markers:
            if m.frame == cur_frame:
                found = True
                break
            pm = m
            idx = idx + 1

        if found:
            self.set_keyframe(m, pm, idx)

    def del_all_keyframes(self):
        for k, bone in self.bones.items():
            bone.del_keyframes()
        phoneme_rig = bpy.data.objects.get('MBLab_skeleton_phoneme_rig')
        phoneme_rig.animation_data_clear()

    def del_keyframe(self, frame):
        for k, bone in self.bones.items():
            bone.del_keyframe(frame)

    def set_random_rest_pose(self, frame):
        bone = self.bones['ph_REST']
        bone.insert_keyframe(frame, random.uniform(0, 1))

class SequenceMgr(object):
    def __init__(self):
        self.sequences = []
        self.orig_frame_set = False

    def set_orig_frame(self, scn):
        if not self.orig_frame_set:
            self.orig_frame_start = scn.frame_start
            self.orig_frame_end = scn.frame_end
            self.orig_frame_set = True

    def add_sequence(self, s):
        seq = Sequence(s)
        self.sequences.append(seq)

    def del_sequence(self, s):
        if s in self.sequences:
                self.sequences.remove(s)

    def get_sequence(self, s):
        for seq in self.sequences:
            if seq.is_sequence(s):
                return seq
        return None

    def set_bones(self, s, bones):
        seq = self.get_sequence(s)
        if not seq:
            return
        seq.set_bones(bones)

    def unmark_sequence(self, s, scn):
        seq = self.get_sequence(s)
        if not seq:
            return
        seq.rm_marker_from_scene(scn)

    def rm_seq_from_scene(self, s, scn):
        seq = self.get_sequence(s)
        if not seq:
            return
        scn.sequence_editor.sequences.remove(s)
        seq.rm_marker_from_scene(scn)
        self.del_sequence(seq)

    def mark_seq_at_frame(self, s, mname, frame, scn):
        seq = self.get_sequence(s)
        if not seq:
            return False
        seq.mark_seq_at_frame(mname, frame, scn)

    def move_to_next_marker(self, s, scn):
        seq = self.get_sequence(s)
        if not seq:
            return
        seq.move_to_next_marker(scn)

    def move_to_prev_marker(self, s, scn):
        seq = self.get_sequence(s)
        if not seq:
            return
        seq.move_to_prev_marker(scn)

    def animate_all_markers(self, s):
        seq = self.get_sequence(s)
        if not seq:
            return
        seq.animate_all_markers()

    def animate_current(self, s, scn):
        seq = self.get_sequence(s)
        if not seq:
            return
        seq.animate_marker_at_frame(scn.frame_current)

    def del_keyframe(self, s, scn):
        seq = self.get_sequence(s)
        if not seq:
            return
        seq.del_keyframe(scn.frame_current)

    def del_all_keyframes(self, s, scn):
        seq = self.get_sequence(s)
        if not seq:
            return
        seq.del_all_keyframes()

    def restore_start_end_frames(self):
        bpy.context.scene.frame_start = self.orig_frame_start
        bpy.context.scene.frame_end = self.orig_frame_end

seqmgr = SequenceMgr()
yaspmapper = YASP2MBPhonemeMapper()

class YASP_OT_mark(bpy.types.Operator):
    bl_idname = "yasp.mark_audio"
    bl_label = "Mark"
    bl_description = "Run YASP and mark audio"

    def mark_audio(self, json_str, offset, seq, scn):
        jdict = json.loads(json_str)
        word_list = []
        # iterate over the json dictionary to and create markers
        try:
            word_list = jdict['words']
        except:
            return False

        for word in word_list:
            try:
                phonemes = word['phonemes']
            except:
                return False
            for phone in phonemes:
                try:
                    # calculate the frame to insert the marker
                    frame = round((scn.render.fps/scn.render.fps_base) *
                                  (phone['start'] / 100))
                    cur_frame = offset + frame
                    seqmgr.mark_seq_at_frame(seq, phone['phoneme'], cur_frame, scn)
                except Exception as e:
                    logger.critical(e)
                    return False
        return True

    def free_json_str(self, json_str):
        #yasp.yasp_free_json_str(json_str)
        return

    def run_yasp(self, wave, transcript, offset):
        if not wave or not transcript:
            self.report({'ERROR'}, "bad wave or transcript files")
            return None

        logs = yasp.yasp_logs()
        yasp.yasp_setup_logging(logs, None, "MB_YASP_Logs")
        json_str = yasp.yasp_interpret_get_str(wave, transcript, None)
        yasp.yasp_finish_logging(logs)
        if not json_str:
            self.report({'ERROR'}, "Couldn't parse speech")
            return None
        if os.path.exists("MB_YASP_Logs"):
            os.remove("MB_YASP_Logs")

        return json_str

    def execute(self, context):
        scn = context.scene
        wave = scn.yasp_wave_path
        transcript = scn.yasp_transcript_path

        if not os.path.isfile(wave) or \
           not os.path.isfile(transcript):
            self.report({'ERROR'}, 'Bad path to wave or transcript')
            return {'FINISHED'}

        if not scn.yasp_start_frame:
            start_frame = 1
        else:
            try:
                start_frame = int(scn.yasp_start_frame)
            except:
                self.report({'ERROR'}, 'Bad start frame')
                return {'FINISHED'}

        json_str = self.run_yasp(wave, transcript, start_frame)
        if not json_str:
            return {'FINISHED'}

        # find a free channel in the sequence editor
        channels = []
        for s in scn.sequence_editor.sequences_all:
            channels.append(s.channel)
        channels.sort()

        channel_select = 1
        for c in channels:
            if c > channel_select:
                break
            channel_select = c + 1
        #insert the wave file
        seq = scn.sequence_editor.sequences.new_sound(os.path.basename(wave), wave,
                   channel_select, start_frame)

        seqmgr.add_sequence(seq)

        if not self.mark_audio(json_str, start_frame, seq, scn):
            seqmgr.rm_seq_from_scene(seq, scn)
            self.report({'ERROR'}, 'Failed to mark the audio file')
            # some memory management
            self.free_json_str(json_str)
            return {'FINISHED'}

        # some memory management
        self.free_json_str(json_str)

        # set the end frame
        end = 0
        for s in scn.sequence_editor.sequences_all:
            if s.frame_final_end > end:
                end = s.frame_final_end
        scn.frame_end = end
        return {'FINISHED'}

class YASP_OT_unmark(bpy.types.Operator):
    bl_idname = "yasp.unmark_audio"
    bl_label = "Unmark"
    bl_description = "Unmark the audio file and remove"

    def execute(self, context):
        scn = context.scene

        seq = scn.sequence_editor.active_strip
        if seq and seq.select:
            seqmgr.unmark_sequence(seq, scn)
        else:
            self.report({'ERROR'}, 'Must select a strip to unmark')

        seqmgr.restore_start_end_frames()

        return {'FINISHED'}

class YASP_OT_delete_seq(bpy.types.Operator):
    bl_idname = "yasp.delete_seq"
    bl_label = "Remove Strip"
    bl_description = "Delete active sequence"

    def execute(self, context):
        scn = context.scene
        seq = scn.sequence_editor.active_strip
        if seq and seq.select:
            seqmgr.rm_seq_from_scene(seq, scn)
            if len(scn.sequence_editor.sequences_all) == 0:
                seqmgr.restore_start_end_frames()
        else:
            self.report({'ERROR'}, 'Must select a strip to delete')

        return {'FINISHED'}

def set_animation_prereq(scn):
    seq = scn.sequence_editor.active_strip
    if not seq or not seq.select:
        return 'STRIP_ERROR', None

    phoneme_rig = bpy.data.objects.get('MBLab_skeleton_phoneme_rig')
    if not phoneme_rig:
        return 'RIG_ERROR', None

    # select the rig and put it in POSE mode
    for obj in bpy.data.objects:
        obj.select_set(False)
    phoneme_rig.select_set(True)
    bpy.context.view_layer.objects.active = phoneme_rig
    bpy.ops.object.mode_set(mode='POSE')
    seqmgr.set_bones(seq, bpy.context.object.pose.bones)
    return 'SUCCESS', seq


class YASP_OT_setallKeyframes(bpy.types.Operator):
    bl_idname = "yasp.set_all_keyframes"
    bl_label = "Animate"
    bl_description = "Set all marked lip-sync keyframe"

    def execute(self, context):
        scn = context.scene
        rc, seq = set_animation_prereq(scn)
        if (rc == 'STRIP_ERROR'):
            self.report({'ERROR'}, "Must select a strip to operate on")
            return {'FINISHED'}
        elif (rc == 'RIG_ERROR'):
            self.report({'ERROR'}, "Phoneme Rig not found")
            return {'FINISHED'}

        # insert key frames on all markers.
        seqmgr.animate_all_markers(seq)
        return {'FINISHED'}

class YASP_OT_deleteallKeyframes(bpy.types.Operator):
    bl_idname = "yasp.delete_all_keyframes"
    bl_label = "Remove Animation"
    bl_description = "Set all marked lip-sync keyframe"

    def execute(self, context):
        scn = context.scene
        rc, seq = set_animation_prereq(scn)
        if (rc == 'STRIP_ERROR'):
            self.report({'ERROR'}, "Must select a strip to operate on")
            return {'FINISHED'}
        elif (rc == 'RIG_ERROR'):
            self.report({'ERROR'}, "Phoneme Rig not found")
            return {'FINISHED'}

        seqmgr.del_all_keyframes(seq, scn)
        return {'FINISHED'}

class YASP_OT_set(bpy.types.Operator):
    bl_idname = "yasp.set_keyframe"
    bl_label = "Set"
    bl_description = "Set a lip-sync keyframe"

    def execute(self, context):
        scn = context.scene
        rc, seq = set_animation_prereq(scn)
        if (rc == 'STRIP_ERROR'):
            self.report({'ERROR'}, "Must select a strip to operate on")
            return {'FINISHED'}
        elif (rc == 'RIG_ERROR'):
            self.report({'ERROR'}, "Phoneme Rig not found")
            return {'FINISHED'}

        seqmgr.animate_current(seq, scn)
        return {'FINISHED'}

class YASP_OT_unset(bpy.types.Operator):
    bl_idname = "yasp.del_keyframe"
    bl_label = "Unset"
    bl_description = "Unset a lip-sync keyframe"

    def execute(self, context):
        scn = context.scene
        rc, seq = set_animation_prereq(scn)
        if (rc == 'STRIP_ERROR'):
            self.report({'ERROR'}, "Must select a strip to operate on")
            return {'FINISHED'}
        elif (rc == 'RIG_ERROR'):
            self.report({'ERROR'}, "Phoneme Rig not found")
            return {'FINISHED'}

        seqmgr.del_keyframe(seq, scn)
        return {'FINISHED'}

class YASP_OT_next(bpy.types.Operator):
    bl_idname = "yasp.next_marker"
    bl_label = "next"
    bl_description = "Jump to next marker"

    def execute(self, context):
        scn = context.scene

        seq = scn.sequence_editor.active_strip
        if seq and seq.select:
            seqmgr.move_to_next_marker(seq, scn)
        else:
            self.report({'ERROR'}, "Must select a strip")

        return {'FINISHED'}

class YASP_OT_prev(bpy.types.Operator):
    bl_idname = "yasp.prev_marker"
    bl_label = "prev"
    bl_description = "Jump to previous marker"

    def execute(self, context):
        scn = context.scene

        seq = scn.sequence_editor.active_strip
        if seq and seq.select:
            seqmgr.move_to_prev_marker(seq, scn)
        else:
            self.report({'ERROR'}, "Must select a strip")

        return {'FINISHED'}

class VIEW3D_PT_tools_mb_yasp(bpy.types.Panel):
    bl_label = "Speech Parser"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "MB-Lab"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        scn = context.scene
        layout = self.layout
        wm = context.window_manager
        col = layout.column(align=True)

        seqmgr.set_orig_frame(scn)

        if platform.system() != "Linux":
            col.label(text="Linux only feature", icon='ERROR')
            return

        if not libs_loaded:
            col.label(text="Libraries not loaded", icon='ERROR')
            return

        col.label(text="Path to WAV file")
        col.prop(scn, "yasp_wave_path", text='')
        col.label(text="Path to transcript file")
        col.prop(scn, "yasp_transcript_path", text="")
        col.label(text="Start on frame")
        col.prop(scn, "yasp_start_frame", text="")
        col.label(text="Window Size")
        col.prop(scn, "yasp_avg_window_size", text="")
        col = layout.column(align=True)
        row = col.row(align=False)
        row.operator('yasp.mark_audio', icon='MARKER_HLT')
        row.operator('yasp.unmark_audio', icon='MARKER')
        col = layout.column(align=True)
        col.operator('yasp.set_all_keyframes', icon='DECORATE_KEYFRAME')
        col = layout.column(align=True)
        col.operator('yasp.delete_all_keyframes', icon='KEYFRAME')
        col = layout.column(align=True)
        row = col.row(align=False)
        row.operator('yasp.set_keyframe', icon='KEYFRAME_HLT')
        row.operator('yasp.del_keyframe', icon='KEYFRAME')
        col = layout.column(align=True)
        row = col.row(align=False)
        row.operator('yasp.prev_marker', icon='PREV_KEYFRAME')
        row.operator('yasp.next_marker', icon='NEXT_KEYFRAME')
        col = layout.column(align=True)
        col.operator('yasp.delete_seq', icon='KEYFRAME')


