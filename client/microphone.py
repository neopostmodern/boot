import math
from time import sleep
from timeit import default_timer as timer

import numpy
import sounddevice as sd
from .exec import threadable
from .audio import Audio

FILTER_LOWEST_FREQUENCY = 600
FILTER_HIGHEST_FREQUENCY = 1500

LOUDNESS_THRESHOLD = 0.003

# weird constants for copied code
columns = 80
gain = 10
block_duration = 50

class Microphone:
    def __init__(self):
        self._device_index = Audio.discover_device_index()
        self._samplerate = sd.query_devices(self._device_index, 'input')['default_samplerate']
        self._stopped = False
    
    @threadable
    def monitor(self, timeout, callback_on_sound = lambda: None, callback_after_timeout = lambda: None, continuos = False, verbose = False, invert = False):
        delta_f = (FILTER_HIGHEST_FREQUENCY - FILTER_LOWEST_FREQUENCY) / (columns - 1)
        fftsize = math.ceil(self._samplerate / delta_f)
        low_bin = math.floor(FILTER_LOWEST_FREQUENCY / delta_f)

        def callback(indata, frames, time, status):
            nonlocal start_time
            if status or self._stopped:
                return
                
            if any(indata):
                magnitude = numpy.abs(numpy.fft.rfft(indata[:, 0], n=fftsize))
                magnitude *= gain / fftsize
                #line = (gradient[int(numpy.clip(x, 0, 1) * (len(gradient) - 1))]
                #        for x in magnitude[low_bin:low_bin + columns])
                #print(*line, sep='', end='\x1b[0m\n')
                
                loudness = numpy.average(magnitude)
                threshold_passed = loudness > LOUDNESS_THRESHOLD
                if threshold_passed != invert:
                    print("loud!")
                    callback_on_sound()
                    if continuos:
                        start_time = timer()
                    else:
                        self._stopped = True
                if verbose:
                    c = '#' if loudness > LOUDNESS_THRESHOLD else '-'
                    print(f"→{loudness:.5f} {int(loudness * 20000) * c}") #, magnitude)
            else:
                print('no input')

        start_time = timer()
        self._stopped = False
        with sd.InputStream(device=self._device_index, channels=1, callback=callback,
                            blocksize=int(self._samplerate * block_duration / 1000),
                            samplerate=self._samplerate):
            while not self._stopped:
                sleep(block_duration / 1000)
                if timer() - start_time > timeout:
                    callback_after_timeout()
                    break
                    
    def stop(self):
        self._stopped = True
                
if __name__ == '__main__':
    def print_test():
        print('Audio was detected!')
    
    mic = Microphone()
    mic.monitor(10, print_test)
    sleep(5)
    mic.stop()
    sleep(10)
