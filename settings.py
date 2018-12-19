import bpy
import os
import json
from bpy_extras.io_utils import ExportHelper, ImportHelper
from bpy.app.handlers import persistent
from . import humanoid, animationengine, proxyengine, algorithms, pose
# from . import bl_info

mblab_humanoid = 0
mblab_retarget = animationengine.RetargetEngine()
mblab_shapekeys = animationengine.ExpressionEngineShapeK()
mblab_proxy = proxyengine.ProxyEngine()


def init(context):
    global mblab_humanoid
    global mblab_retarget
    global mblab_shapekeys
    global mblab_proxy
    mblab_humanoid = humanoid.Humanoid(context["version"])
