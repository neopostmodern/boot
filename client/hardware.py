from time import sleep
import RPi.GPIO as GPIO
from .devices.MCP23017 import MCP23017
from Adafruit_PCA9685 import PCA9685
from .constants import (
    OnboardPin,
    LedExtensionPin,
    ServoConfigs,
    ServoName,
    ServoSide,
    I2CAddress,
    Language,
)
from .performance import Performance
from .midi import MIDI
from .microphone import Microphone
from .audio import Audio

# GPIO.cleanup()  # should be moved to "end"/"shutdown"
GPIO.setmode(GPIO.BCM)


class PSU:
    def __init__(self):
        GPIO.setup(OnboardPin.PSU, GPIO.OUT)

    def turn_on(self):
        GPIO.output(OnboardPin.PSU, GPIO.HIGH)

    def turn_off(self):
        GPIO.output(OnboardPin.PSU, GPIO.LOW)

    def is_on(self):
        return GPIO.input(OnboardPin.PSU) == GPIO.HIGH


class LEDExtension:
    def __init__(self):
        self._mcp = MCP23017(address=I2CAddress.LED_EXTENSION, num_gpios=16)
        for pin in range(8):
            self._mcp.pinMode(pin, MCP23017.OUTPUT)

        self.turn_all_off()

    def turn_all_off(self):
        for pin in range(8):
            self._mcp.output(pin, MCP23017.LOW)

    def set(self, pin, value: bool):
        self._mcp.output(pin, MCP23017.HIGH if value else MCP23017.LOW)

    def lightshow(self, time_per_step=1, reverse=False):
        pins = [
            LedExtensionPin.B_FLAT_MAJOR,
            LedExtensionPin.F_MAJOR,
            LedExtensionPin.C_MAJOR,
            LedExtensionPin.G_MINOR,
            LedExtensionPin.D_MAJOR,
            LedExtensionPin.D_MINOR,
            LedExtensionPin.A_MAJOR,
            LedExtensionPin.A_MINOR,
        ]
        if reverse:
            pins.reverse()

        for pin in pins:
            self._mcp.output(pin, MCP23017.HIGH)
            sleep(time_per_step)
            self._mcp.output(pin, MCP23017.LOW)

    def long_lightshow(self, iterations=6, time_per_step=0.2):
        for iteration in range(iterations):
            self.lightshow(time_per_step, reverse=(iteration % 2 == 0))

    def set_c_major(self, value: bool):
        self.set(LedExtensionPin.C_MAJOR, value)

    def set_a_minor(self, value: bool):
        self.set(LedExtensionPin.A_MINOR, value)


class StartButtons:
    def __init__(self):
        GPIO.setup(OnboardPin.START_BUTTON_EN_LED, GPIO.OUT)
        GPIO.setup(OnboardPin.START_BUTTON_EN_SWITCH, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(OnboardPin.START_BUTTON_DE_LED, GPIO.OUT)
        GPIO.setup(OnboardPin.START_BUTTON_DE_SWITCH, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    def turn_LED_on(self, language):
        if language == Language.ENGLISH:
            GPIO.output(OnboardPin.START_BUTTON_EN_LED, GPIO.HIGH)
        elif language == Language.GERMAN:
            GPIO.output(OnboardPin.START_BUTTON_DE_LED, GPIO.HIGH)
        else:
            raise ValueError("Unknown language: " + language)

    def turn_LED_off(self, language):
        if language == Language.ENGLISH:
            GPIO.output(OnboardPin.START_BUTTON_EN_LED, GPIO.LOW)
        elif language == Language.GERMAN:
            GPIO.output(OnboardPin.START_BUTTON_DE_LED, GPIO.LOW)
        else:
            raise ValueError("Unknown language: " + language)

    def probe(self, language):
        # caution, using a pull-up = everything slightly reversed
        if language == Language.ENGLISH:
            return GPIO.input(OnboardPin.START_BUTTON_EN_SWITCH) == GPIO.LOW
        elif language == Language.GERMAN:
            return GPIO.input(OnboardPin.START_BUTTON_DE_SWITCH) == GPIO.LOW
        else:
            raise ValueError("Unknown language: " + language)

    def subscribe(self, language, callback):
        if language == Language.ENGLISH:
            GPIO.add_event_detect(
                OnboardPin.START_BUTTON_EN_SWITCH,
                GPIO.FALLING,
                bouncetime=1000,
                callback=callback,
            )
        elif language == Language.GERMAN:
            GPIO.add_event_detect(
                OnboardPin.START_BUTTON_DE_SWITCH,
                GPIO.FALLING,
                bouncetime=1000,
                callback=callback,
            )
        else:
            raise ValueError("Unknown language: " + language)


class Organ:
    def __init__(self, psu: PSU):
        self._psu = psu
        GPIO.setup(OnboardPin.ORGAN, GPIO.OUT)

    def turn_on(self):
        if not self._psu.is_on():
            raise RuntimeError("PSU is not switched on")

        GPIO.output(OnboardPin.ORGAN, GPIO.HIGH)

    def turn_off(self):
        GPIO.output(OnboardPin.ORGAN, GPIO.LOW)


class Servos:
    FREQUENCY = 330
    DEFAULT_TRAVEL_SPEED = 0.013

    def __init__(self, psu: PSU):
        self._psu = psu
        self._servos_left = PCA9685(address=I2CAddress.SERVOS_LEFT)
        self._servos_left.set_pwm_freq(Servos.FREQUENCY)
        self._servos_right = PCA9685(address=I2CAddress.SERVOS_RIGHT)
        self._servos_right.set_pwm_freq(Servos.FREQUENCY)

    @staticmethod
    def _angle_to_pulse_width(angle):
        return int(angle * Servos.FREQUENCY / 10)

    @staticmethod
    def estimate_travel_time(servo_name: ServoName, angle: float):
        return abs(angle) * Servos.DEFAULT_TRAVEL_SPEED

    def set(self, servo_name: ServoName, angle: float):
        try:
            servo_config = ServoConfigs[servo_name]
        except KeyError:
            raise ValueError(f"No such servo: {servo_name}")

        if angle < servo_config.min_angle or angle > servo_config.max_angle:
            raise ValueError(
                f"Angle {angle:.1f}° outside of safe range [{servo_config.min_angle:.1f}°, "
                f'{servo_config.max_angle:.1f}°] for servo "{servo_name.value}"!'
            )

        if not self._psu.is_on():
            raise RuntimeError("PSU is not switched on")

        servo_driver = (
            self._servos_left
            if servo_config.side == ServoSide.LEFT
            else self._servos_right
        )
        servo_driver.set_pwm(
            servo_config.pin.value, 0, Servos._angle_to_pulse_width(angle)
        )


class Drums:
    def __init__(self, servos: Servos):
        self._servos = servos

    def hit(
        self,
        servo_name: ServoName,
        resting_angle: float,
        hit_angle: float,
        travel_time=None,
    ):
        self._servos.set(servo_name, hit_angle)
        sleep(
            Servos.estimate_travel_time(servo_name, hit_angle - resting_angle)
            if travel_time is None
            else travel_time
        )
        self._servos.set(servo_name, resting_angle)

    def hihat(self):
        # self.hit(ServoName.HIHAT, 52, 54.5, 0.08) # 55, 56.9, 0.08
        self.hit(ServoName.HIHAT, 52, 55, 0.08)

    def click(self):
        self.hit(ServoName.HIHAT, 41, 34, 0.1)

    def ready_to_click(self):
        self._servos.set(ServoName.HIHAT, 41)

    def gong(self):
        # self.hit(ServoName.RIDE, 45, 62, 0.15)
        self.hit(ServoName.RIDE, 41, 60, 0.12)

    def ride(self):
        # self.hit(ServoName.RIDE, 26, 24, 0.1)
        self.hit(ServoName.RIDE, 26, 24, 0.02)

    def ride_neutral(self):
        self._servos.set(ServoName.RIDE, 41)

    def ride_stop(self):
        self._servos.set(ServoName.RIDE, 24)


class Crocos:
    def __init__(self, servos: Servos):
        self._servos = servos

    def base_right(self, angle: float):
        self._servos.set(ServoName.CROCO_BASE_RIGHT, angle)

    def base_center(self, angle: float):
        self._servos.set(ServoName.CROCO_BASE_CENTER, angle)

    def base_left(self, angle: float):
        """servo:crocodile base left"""
        self._servos.set(ServoName.CROCO_BASE_LEFT, angle)

    def jaw_right(self, angle: float):
        """servo:crocodile jaw right"""
        self._servos.set(ServoName.CROCO_JAW_RIGHT, angle)

    def jaw_center(self, angle: float):
        """servo:crocodile jaw center"""
        self._servos.set(ServoName.CROCO_JAW_CENTER, angle)

    def jaw_left(self, angle: float):
        """servo:crocodile jaw left"""
        self._servos.set(ServoName.CROCO_JAW_LEFT, angle)


class Hardware:
    def __init__(self):
        self.audio = Audio()
        self.psu = PSU()
        self.start_buttons = StartButtons()
        self.led_extension = LEDExtension()
        self.organ = Organ(self.psu)
        self.servos = Servos(self.psu)
        self.drums = Drums(self.servos)
        self.crocos = Crocos(self.servos)
        self.performance = Performance(self)
        self.midi = MIDI(self)
        self.microphone = Microphone()

        self._play_lock = False

        def on_finish():
            print("Finish!")
            self.start_buttons.turn_LED_on(Language.GERMAN)
            self.start_buttons.turn_LED_on(Language.ENGLISH)
            self.led_extension.turn_all_off()
            self.organ.turn_off()
            self.psu.turn_off()
            self._play_lock = False

        def play_wrapper(channel):
            # todo: switch language based on channel
            print(f"Hardware play triggered (channel {channel})!")
            sleep(0.1)
            if not (
                self.start_buttons.probe(Language.GERMAN)
                or self.start_buttons.probe(Language.ENGLISH)
            ):
                print(">> False alarm.")
                return

            if self._play_lock:
                print(">> Duplicate call.")
                return

            print("Let's do this!")
            self._play_lock = True
            self.psu.turn_on()
            self.start_buttons.turn_LED_off(Language.GERMAN)
            self.start_buttons.turn_LED_off(Language.ENGLISH)
            self.performance.play(finish_callback=on_finish)

        self.start_buttons.turn_LED_on(Language.GERMAN)
        self.start_buttons.turn_LED_on(Language.ENGLISH)
        self.start_buttons.subscribe(Language.GERMAN, play_wrapper)
        self.start_buttons.subscribe(Language.ENGLISH, play_wrapper)
