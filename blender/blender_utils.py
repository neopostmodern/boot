import bpy
import json
import os.path
from subprocess import run
from urllib.request import Request, urlopen
from datetime import datetime

from config.config import config

# bpy.ops.script.reload()

# Set the path for the JSON output file
output_base_path = config["output"]["base_absolute_path"]
audio_renders_base_path = os.path.join(
    output_base_path, config["output"]["audio"]["renders_relative_path"]
)
main_audio_file = os.path.join(
    audio_renders_base_path, config["output"]["audio"]["main_file_basename"]
)
audio_file_extension = config["output"]["audio"]["file_extension"]
output_file_path = os.path.join(output_base_path, config["output"]["output_filename"])
audio_channels = list(range(1, 4))


def get_master_track_file_name(track_identifier=None):
    return (
        main_audio_file
        + (f"_{track_identifier}" if track_identifier else "")
        + audio_file_extension
    )


def render_audio():
    for channel in bpy.data.scenes["Scene"].sequence_editor.channels:
        channel.mute = True

    for channel in audio_channels:
        bpy.data.scenes["Scene"].sequence_editor.channels[
            f"Channel {channel}"
        ].mute = False
        bpy.ops.sound.mixdown(
            "INVOKE_DEFAULT",
            filepath=get_master_track_file_name(channel),
            container="WAV",
            codec="PCM",
        )
        bpy.data.scenes["Scene"].sequence_editor.channels[
            f"Channel {channel}"
        ].mute = True

    for channel in bpy.data.scenes["Scene"].sequence_editor.channels:
        channel.mute = False


def create_audio_snippet(sequence):
    audio_file_name = os.path.join(
        audio_renders_base_path,
        f"{sequence.frame_final_start}-{sequence.frame_final_end}"
        + audio_file_extension,
    )
    start_time = (
        max(sequence.frame_final_start - bpy.context.scene.frame_start, 0)
        / bpy.context.scene.render.fps
    )
    print(
        "start",
        sequence.frame_final_start,
        bpy.context.scene.frame_start,
        max(sequence.frame_final_start - bpy.context.scene.frame_start, 0),
    )
    end_time = (
        min(sequence.frame_final_end, bpy.context.scene.frame_end)
        - bpy.context.scene.frame_start
    ) / bpy.context.scene.render.fps
    ffmpeg_inputs = " ".join(
        [f'-i "{get_master_track_file_name(channel)}"' for channel in audio_channels]
    )
    # todo: the channel number and layout is very hardcoded at the moment
    command = f"""ffmpeg -hide_banner {ffmpeg_inputs} -ss {start_time:.2f} -t {end_time - start_time:.2f} -filter_complex "join=inputs=3:channel_layout=3c,pan=8c|c0=c1|c1=c1|c4=c2|c5=c2|c6=c0|c7=c0" -y {audio_file_name}"""
    print(command)
    command_result = run(command, shell=True, capture_output=True, text=True)
    if command_result.returncode != 0:
        print(command_result)
        print(command_result.stdout)
        print(command_result.stderr)
    return audio_file_name


def bake_speech_movements():
    def get_context_area(
        context, context_dict, area_type="GRAPH_EDITOR", context_screen=False
    ):
        """
        context : the current context
        context_dict : a context dictionary. Will update area, screen, scene,
                    area, region
        area_type: the type of area to search for
        context_screen: Boolean. If true only search in the context screen.
        """
        if not context_screen:  # default
            screens = bpy.data.screens
        else:
            screens = [context.screen]
        for screen in screens:
            for area_index, area in screen.areas.items():
                if area.type == area_type:
                    for region in area.regions:
                        if region.type == "WINDOW":
                            context_dict["area"] = area
                            context_dict["screen"] = screen
                            context_dict["scene"] = context.scene
                            context_dict["window"] = context.window
                            context_dict["region"] = region
                            return area
        return None

    context = bpy.context.copy()
    area = get_context_area(bpy.context, context)
    # todo: investigate whether shadow contexting works now and then remove all commented code
    print(context)
    print(context["scene"])
    print(area)
    # area = bpy.context.window.screen.areas[-2] # bpy.context.area
    # print("bake!", area.ui_type)

    # previous_area_type = area.type
    try:
        # todo: understand where this property is added and document it
        bake_objects = [
            any_object for any_object in bpy.data.objects if "bake" in any_object
        ]
        for bake_object in bake_objects:

            context["area"].type = "GRAPH_EDITOR"
            context["scene"].frame_set(context["scene"].frame_start)
            bake_object.select_set(True)
            bake_object.rotation_euler[0] = 0.0
            bake_object.keyframe_insert("rotation_euler", index=0, frame=1)
            bake_object.animation_data.action.fcurves[0].select = True
            bpy.ops.graph.sound_bake(
                context,
                filepath=get_master_track_file_name(bake_object["bake"]),
                release=0.3,
                threshold=0.5,
            )
            bpy.ops.graph.bake(context)
            bpy.ops.graph.unbake(context)
            bake_object.animation_data.action.fcurves[0].select = False
            bake_object.select_set(False)
    except Exception as error:
        print(error)
    # finally:
    #   area.type = previous_area_type
    #   pass


def export():
    render_audio()
    bake_speech_movements()

    servo_curve_map = {}

    servo_objects = [
        any_object for any_object in bpy.data.objects if "servo" in any_object
    ]

    for servo_object in servo_objects:
        for fcurve in servo_object.animation_data.action.fcurves:
            last_keyframe_value = None
            for keyframe in fcurve.keyframe_points:
                if (
                    last_keyframe_value is not None
                    and last_keyframe_value != keyframe.co.y
                ):
                    servo_curve_map[servo_object["servo"]] = fcurve
                    break
                last_keyframe_value = keyframe.co.y

    frames = []
    audio_files = []
    servo_last_values = {}

    for frame in range(bpy.context.scene.frame_start, bpy.context.scene.frame_end + 1):
        # bpy.context.scene.frame_set(frame)
        servo_parameters = {}

        for servo_name, fcurve in servo_curve_map.items():
            servo_frame_value = fcurve.evaluate(frame)

            if servo_frame_value != servo_last_values.get(servo_name):
                servo_parameters[servo_name] = servo_frame_value

            servo_last_values[servo_name] = servo_frame_value

        frames.append(
            {
                "index": frame - bpy.context.scene.frame_start,
                "_absolute_index": frame,
                "servos": servo_parameters,
                "audio": [],
                "instructions": [],
            }
        )

    sequencer = bpy.context.scene.sequence_editor
    for sequence in sequencer.sequences:
        if (
            sequence.frame_final_start < bpy.context.scene.frame_start
            or sequence.frame_final_start > bpy.context.scene.frame_end
        ):
            continue

        sequence_start_frame = frames[
            int(sequence.frame_final_start - bpy.context.scene.frame_start)
        ]
        if sequence.type == "TEXT":
            sequence_start_frame["instructions"].append(
                f"{sequence.text}:{sequence.frame_final_duration}"
            )
        elif sequence.type == "SOUND":
            if sequence.channel not in audio_channels:
                continue

            # todo: get folder names from config!
            sequence_audio_file_name = (
                "audio/" + create_audio_snippet(sequence).split("/audio/")[1]
            )  # sequence.name
            sequence_start_frame["audio"].append(sequence_audio_file_name)
            audio_files.append(sequence_audio_file_name)
        else:
            print("Unknown sequence:", sequence)

    with open(output_file_path, "w") as output_file:
        json.dump(
            {
                "meta": {
                    "filename": bpy.data.filepath,
                    "render_time": datetime.now().isoformat(),
                },
                "fps": bpy.context.scene.render.fps,
                "audio_files": audio_files,
                "frames": frames,
            },
            output_file,
            indent=4,
        )

    print(f"Done rendering: {output_file_path}")


def upload_render():
    run(
        f"rsync -avz {config['output']['base_absolute_path']}"
        f" {config['client']['username']}@{config['client']['hostname']}"
        f":{config['client']['media_directory_absolute_path']}",
        shell=True,
    )
    print("Synchronization complete.")


def trigger_remote_play():
    request = Request(f"{config['client']['http_origin']}/exec?method=performance.play")
    with urlopen(request) as response:
        print(response.read().decode("utf-8"))
