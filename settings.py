import bpy
import os
import json
from bpy_extras.io_utils import ExportHelper, ImportHelper
from bpy.app.handlers import persistent
# from . import humanoid, animationengine, proxyengine
# from . import bl_info

# mblab_humanoid = 0
# mblab_retarget = animationengine.RetargetEngine()
# mblab_shapekeys = animationengine.ExpressionEngineShapeK()
# mblab_proxy = proxyengine.ProxyEngine()

debug_level = 0
data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "data") # from get_data_path

def init(context):
    from . import humanoid, animationengine, proxyengine

    global mblab_humanoid
    global mblab_retarget
    global mblab_shapekeys
    global mblab_proxy

    mblab_humanoid = humanoid.Humanoid(context["version"])
    mblab_retarget = animationengine.RetargetEngine()
    mblab_shapekeys = animationengine.ExpressionEngineShapeK()
    mblab_proxy = proxyengine.ProxyEngine()