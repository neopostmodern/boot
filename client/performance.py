import json
import os.path
from time import sleep
from timeit import default_timer as timer
from math import degrees
from .audio import Audio
from .exec import threadable
from .constants import RENDER_BASE_PATH
from .midi import MIDI


class Performance:
    def __init__(self, hardware):
        self._hardware = hardware
        self._audio = hardware.audio
        self._abort = False
        self._goto = None
        self._frame_index = 0
        self._muted = False
        
    def abort(self):
        print("ABORT!")
        self._abort = True
        
    def prepare(self):
        with open(os.path.join(RENDER_BASE_PATH, 'play.json'), 'r') as json_file:
          self._instructions = json.load(json_file)  
        
        print(self._instructions['meta'])

        audio_file_names = self._instructions['audio_files']
        for audio_file_name in audio_file_names:
          self._audio.preload(os.path.join(RENDER_BASE_PATH, audio_file_name))
        
    @threadable
    def act(self, finish_callback = lambda: None):          
        fps = self._instructions['fps']
        frames = self._instructions['frames']
        
        marker = {}
        for frame in frames:
          for instruction in frame['instructions']:
            if instruction.startswith('marker'):
              marker_name = instruction.split(":")[1]
              marker[marker_name] = frame['index']
                
        start_time = timer()
        self._frame_index = 0
        self._abort = False
        self._goto = None
        while self._frame_index < len(frames):
          frame = frames[self._frame_index]
          
          print(f"{frame['index']}/{len(frames)} [{frame['_absolute_index']}]")
          for audio_file_path in frame['audio']:
            if not self._muted:
              print(f"Play audio {audio_file_path}")
              self._audio.play_preloaded_file(os.path.join(RENDER_BASE_PATH, audio_file_path))
            
          for instruction in frame['instructions']:
            instruction_type, raw_expression, raw_duration = instruction.split(':')
            duration_frames = int(raw_duration)
            duration_seconds = duration_frames / fps
            expression = raw_expression.split(';')[0]
            expression_arguments = raw_expression.split(';')[1:]
            if instruction_type == 'hardware':
              eval(f"self._hardware.{expression}")
            elif instruction_type == 'log':
              print("LOG:", expression)
            elif instruction_type == 'mute':
              self._muted = True
            elif instruction_type == 'unmute':
              self._muted = False
            elif instruction_type == 'marker':
              pass
            elif instruction_type == 'midi':
              if expression == 'play':
                self._hardware.midi.listen(expression_arguments[0])
              else:
                MIDI.play(expression)
            elif instruction_type == 'logic':
              if expression == 'abort_if_no_sound':
                def abort_no_sound():
                  self._goto = marker['aborted-ending']
                self._hardware.microphone.monitor(duration_seconds, callback_after_timeout=abort_no_sound)
              elif expression == 'wait_for_sound':
                if expression_arguments[0].startswith('goto'):
                  goto_target = expression_arguments[0].split('=')[1]
                  goto_marker_frame = marker[goto_target]
                  def goto():
                    self._goto = goto_marker_frame
                  self._hardware.microphone.monitor(duration_seconds, callback_on_sound=goto, invert='invert' in expression_arguments)
                else:
                  print(f"Unknown callback for 'wait_for_sound' logic instruction: {instruction}")
              elif expression == 'end':
                self._abort = True
              else:
                print(f"Unknown logic instruction: {instruction}")
            else:
              print(f"Unknown instruction: {instruction}")
          
          # print(frame['servos'])
          for servo_name, servo_radians in frame['servos'].items():
            servo_angle = degrees(servo_radians)
            if servo_name == 'croco base right':
              self._hardware.crocos.base_right(45 + servo_angle)
            elif servo_name == 'croco base center':
              self._hardware.crocos.base_center(45 + servo_angle)
            elif servo_name == 'croco base left':
              self._hardware.crocos.base_left(45 + servo_angle)
            elif servo_name == 'croco jaw center':
              self._hardware.crocos.jaw_center(max(62 - servo_angle * 0.55, 45))
            elif servo_name == 'croco jaw left':
              self._hardware.crocos.jaw_left(min(28 + servo_angle * 0.7, 40))
            elif servo_name == 'croco jaw right':
              self._hardware.crocos.jaw_right(min(32 + servo_angle, 55))
            else:
              print(f"Unknown servo {servo_name}")
               
          if self._goto is not None:
            start_time -= (self._goto - self._frame_index) / fps
            self._frame_index = self._goto
            self._goto = None
          else:
            self._frame_index += 1

          wall_time = timer() - start_time
          next_frame_time = (frame['index'] + 1) / fps
          time_to_next_frame = next_frame_time - wall_time
          if time_to_next_frame <= 0:
            print(f"Warning! Drift of {time_to_next_frame:.3f}s at frame {frame['index']}! (Actual offender unknown)")
            continue
            
          sleep(next_frame_time - wall_time)
          
          if self._abort:
            break
          
        finish_callback()
    
    @threadable
    def play(self, finish_callback = lambda: None):
        self.prepare()
        self.act(finish_callback=finish_callback)


if __name__ == "__main__":
    from hardware import Hardware
    
    hardware = Hardware()
    performance = Performance(hardware)
    performance.play()
