# import bpy
import os
# from os.path import join, getsize
# import json
# from bpy_extras.io_utils import ExportHelper, ImportHelper
# from bpy.app.handlers import persistent
from pathlib import Path
# from . import humanoid, animationengine, proxyengine
# from . import bl_info

# mblab_humanoid = 0
# mblab_retarget = animationengine.RetargetEngine()
# mblab_shapekeys = animationengine.ExpressionEngineShapeK()
# mblab_proxy = proxyengine.ProxyEngine()

debug_level = 0
data_path = Path(os.path.dirname(os.path.realpath(__file__)), "data")

def init(context):
    from . import humanoid, animationengine, proxyengine
    from . import multiloading as ml
    from . import algorithms as a

    global mblab_humanoid
    global mblab_retarget
    global mblab_shapekeys
    global mblab_proxy

    mblab_humanoid = humanoid.Humanoid(context["version"])
    mblab_retarget = animationengine.RetargetEngine()
    mblab_shapekeys = animationengine.ExpressionEngineShapeK()
    mblab_proxy = proxyengine.ProxyEngine()

    global loadedlib
    loadedlib = ml.PathDirectory()
    morphlist = ml.namesofallconfig("morphs")
    a.print_log_report("D", morphlist)
    a.print_log_report("D", ml.namesofallconfig("morphs", "Core"))
    a.print_log_report("D", ml.namesofallconfig("morphs", "Anime"))
    a.print_log_report("d", ml.namesofallconfig("anthropometry"))
