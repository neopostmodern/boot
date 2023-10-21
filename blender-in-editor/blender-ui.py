import bpy
import sys
import imp

# this path can't be managed from config, because we're inside Blender and have no notion of where the config even is
RELATIVE_PATH_TO_CODEBASE_ROOT = "../scripting"

scripts_path = bpy.path.abspath(f"//{RELATIVE_PATH_TO_CODEBASE_ROOT}/")
if scripts_path not in sys.path:
    sys.path.append(scripts_path)

import blender.blender_utils as blender_utils


class RenderOperator(bpy.types.Operator):
    """Generate files only locally"""

    bl_idname = "npm.render"
    bl_label = "Render Operator"

    def execute(self, context):
        imp.reload(blender_utils)
        blender_utils.export()
        return {"FINISHED"}


def HT_render_button(self, context):
    self.layout.operator(operator="npm.render", text="Render", icon="REC")


class RenderUploadOperator(bpy.types.Operator):
    """Generate files and transfer to theater"""

    bl_idname = "npm.render_upload"
    bl_label = "Render Upload Operator"

    def execute(self, context):
        imp.reload(blender_utils)
        blender_utils.export()
        blender_utils.upload_render()
        return {"FINISHED"}


def HT_render_upload_button(self, context):
    self.layout.operator(
        operator="npm.render_upload", text="Render & Upload", icon="CURVE_PATH"
    )


class PlayOperator(bpy.types.Operator):
    """Play on theater"""

    bl_idname = "npm.play"
    bl_label = "Play"

    def execute(self, context):
        imp.reload(blender_utils)
        blender_utils.trigger_remote_play()
        return {"FINISHED"}


def HT_play_button(self, context):
    self.layout.operator(operator="npm.play", text="Play", icon="PLAY")


if __name__ == "__main__":
    bpy.utils.register_class(RenderOperator)
    bpy.utils.register_class(RenderUploadOperator)
    bpy.utils.register_class(PlayOperator)
    bpy.types.TOPBAR_MT_editor_menus.append(HT_render_button)
    bpy.types.TOPBAR_MT_editor_menus.append(HT_render_upload_button)
    bpy.types.TOPBAR_MT_editor_menus.append(HT_play_button)
