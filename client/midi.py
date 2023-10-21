from subprocess import run
from threading import Thread
import os.path

import mido

from .constants import MidiChannel, MidiMessageType, ChordType, ChordMidiNote, DrumMidiNote, LedExtensionPin, MIDI_MAPPING_CHORDS, RENDER_BASE_PATH
from .exec import threadable
from .audio import Audio 

def system_music_files(language):
  return [os.path.join(RENDER_BASE_PATH, config['client']['music_directory_name'], f"song_{part}_{language}.wav") if part is not None else None for part in [
    'a',
    None,
    'b',
    'c',
    'd'
  ]] 

class MIDI:
  def __init__(self, hardware):
    self._hardware = hardware
    self._audio = hardware.audio
    
    drums = self._hardware.drums
    self._midi_mapping_drums = {
      DrumMidiNote.RIDE: drums.ride,
      DrumMidiNote.HIHAT: drums.hihat,
      DrumMidiNote.CLICK: drums.click
    }


  @threadable
  def listen(self, language):
    led_extension = self._hardware.led_extension
    
    music_files = system_music_files(language)
    for music_file in music_files:
      if music_file is None:
        continue
      
      self._audio.preload(music_file)
    
    with mido.open_input() as in_port:
      for midi_message in in_port:
        if midi_message.type != 'note_on' and midi_message.type != 'note_off':
          continue
          
        message_type = MidiMessageType.ON if midi_message.type == 'note_on' and midi_message.velocity > 0 else MidiMessageType.OFF 
        
        if midi_message.channel == MidiChannel.DRUMS:
          if message_type != MidiMessageType.ON:
            continue
            
          action = self._midi_mapping_drums.get(midi_message.note, None)
          if action is not None:
            Thread(target=action).start()
          else:
            raise ValueError("Unknown MIDI message: " + midi_message)
        
        elif midi_message.channel == MidiChannel.CHORDS:
          led_extension.set(
            MIDI_MAPPING_CHORDS[midi_message.note], 
            message_type == MidiMessageType.ON
          )
        
        elif midi_message.channel == MidiChannel.SYSTEM:
          if message_type != MidiMessageType.ON:
            continue
          
          if midi_message.note == 59:
            # signal stop listening
            break
          
          system_index = midi_message.note - 60
          
          if system_index == 1:
            self._hardware.drums.hihat()
          
          music_file = music_files[system_index]
          print(f"SYSTEM {midi_message.note} → {midi_message.note - 60} → {music_files[system_index]}") 
          if music_file is not None:
            self._audio.play_preloaded_file(music_file)
        
        else:
          print(f"Unknown MIDI channel: {midi_message.channel}")

  
  @staticmethod
  def unlisten():
    MIDI.play('unlisten') # contains a single note 59 on channel SYSTEM
          
  @staticmethod
  def play(midi_file_basename = 'master'):
    run(f"aplaymidi {config['client']['midi_directory_absolute_path']}/{midi_file_basename}.mid -p `aplaymidi -l | grep RtMidi | awk '{{print $1}}'` &", shell=True)
     
     

#midi_mapping_chords = {
#  ChordMidiNote.C: {
#    ChordType.MAJOR: LedExtensionPin.C_MAJOR
#  },
#  ChordMidiNote.D: {
#    ChordType.MAJOR: LedExtensionPin.D_MAJOR,
#    ChordType.MINOR: LedExtensionPin.D_MINOR
#  },
#  ChordMidiNote.F: {
#    ChordType.MAJOR: LedExtensionPin.F_MAJOR
#  },
#  ChordMidiNote.G: {
#    ChordType.MINOR: LedExtensionPin.G_MINOR
#  },
#  ChordMidiNote.A: {
#    ChordType.MAJOR: LedExtensionPin.A_MAJOR,
#    ChordType.MINOR: LedExtensionPin.A_MINOR
#  },
#  ChordMidiNote.B_FLAT: {
#    ChordType.MAJOR: LedExtensionPin.B_FLAT_MAJOR,
#  },
#}          

#          if midi_message.type == 'note_on' and midi_message.velocity > 0:
#            chord_type = ChordType.MAJOR if midi_message.velocity >= 64 else ChordType.MINOR
#            led_extension_pin = midi_mapping_chords[midi_message.note][chord_type]
#            led_extension.set(led_extension_pin, True)
#          else:
#            major_chord_pin = midi_mapping_chords[midi_message.note].get(ChordType.MAJOR, None)
#            minor_chord_pin = midi_mapping_chords[midi_message.note].get(ChordType.MINOR, None)
#            if major_chord_pin is not None:
#              led_extension.set(major_chord_pin, False)
#            if minor_chord_pin is not None:
#              led_extension.set(minor_chord_pin, False)
