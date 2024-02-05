import bpy
import sys
from importlib import reload
from types import ModuleType

stdout = sys.stdout

# todo: this STDOUT hack causes the blender UI to disappear when invoking `bpy.ops.script.reload()` – need to find a workaround-workaround
class new_stdout(object):
    """from: https://stackoverflow.com/a/17601387"""

    def write(*args, **kwargs):
        # do whatever

        """from https://blender.stackexchange.com/a/142317"""
        for window in bpy.context.window_manager.windows:
            screen = window.screen
            for area in screen.areas:
                if area.type == "CONSOLE":
                    override = {"window": window, "screen": screen, "area": area}
                    bpy.ops.console.scrollback_append(
                        override,
                        text=str(" ".join([str(x) for x in args[1:]])),
                        type="OUTPUT",
                    )


sys.stdout = new_stdout()

# this path can't be managed from config, because we're inside Blender and have no notion of where the config even is
RELATIVE_PATH_TO_CODEBASE_ROOT = "../scripting"

scripts_path = bpy.path.abspath(f"//{RELATIVE_PATH_TO_CODEBASE_ROOT}/")
if scripts_path not in sys.path:
    sys.path.append(scripts_path)

import blender.blender_utils as blender_utils


def recursive_module_reload(module):
    """from: https://stackoverflow.com/a/17194836"""
    if module.__name__.startswith("bpy") or module.__name__ in ["os", "builtins"]:
        return

    try:
        reload(module)
    except ImportError:
        return

    for attribute_name in dir(module):
        attribute = getattr(module, attribute_name)
        if type(attribute) is ModuleType:
            recursive_module_reload(attribute)


def reload_blender_utils():
    recursive_module_reload(blender_utils)


class RenderOperator(bpy.types.Operator):
    """Generate files only locally"""

    bl_idname = "npm.render"
    bl_label = "Render Operator"

    def execute(self, context):
        reload_blender_utils()
        blender_utils.export()
        return {"FINISHED"}


def HT_render_button(self, context):
    self.layout.operator(operator="npm.render", text="Render", icon="REC")


class RenderUploadOperator(bpy.types.Operator):
    """Generate files and transfer to theater"""

    bl_idname = "npm.render_upload"
    bl_label = "Render Upload Operator"

    def execute(self, context):
        reload_blender_utils()
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
        reload_blender_utils()
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
