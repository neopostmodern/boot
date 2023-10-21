import sounddevice as sd
import soundfile as sf
import threading
from config.config import config
from .exec import threadable

class Audio:
  @staticmethod
  def discover_device_index():
    for device in sd.query_devices():
      if config['client']['soundcard']['name'] not in device['name']:
        continue
      
      return device['index']

  def __init__(self):
    self._audio_files = {}      
    self._device_index = Audio.discover_device_index()
      
      
  def preload(self, file_name):
    self._audio_files[file_name] = sf.read(file_name) #, always_2d=True)
    
  @threadable 
  def play_preloaded_file(self, file_name):
    print(f"Starting: {file_name}")
    event = threading.Event() 
    data, fs = self._audio_files[file_name]
    print(f"Loaded {data.shape[1]} channel audio with {data.shape[0]} samples")
    current_frame = 0
    def callback(outdata, frames, time, status):
      nonlocal current_frame
      if status:
          print(status)
      chunksize = min(len(data) - current_frame, frames)
      outdata[:chunksize] = data[current_frame:current_frame + chunksize]
      if chunksize < frames:
          outdata[chunksize:] = 0
          raise sd.CallbackStop()
      current_frame += chunksize
    try:
      stream = sd.OutputStream(samplerate=fs, device=self._device_index, channels=data.shape[1], callback=callback, finished_callback=event.set)
      with stream:
        event.wait()
      print(f"Finished: {file_name}")
    except sd.PortAudioError:
      print("Failed to play audio!")

