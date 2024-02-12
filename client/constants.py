from enum import Enum
from typing import NamedTuple, Union
from config.config import config

RENDER_BASE_PATH = config["client"]["media_directory_absolute_path"]


class Language:
    ENGLISH = "en"
    GERMAN = "de"


class Config:
    THREADING = "threading"


# hardware


class OnboardPin:
    PSU = 21
    START_BUTTON_EN_LED = 13
    START_BUTTON_EN_SWITCH = 6
    START_BUTTON_DE_LED = 19
    START_BUTTON_DE_SWITCH = 26
    ORGAN = 5


class I2CAddress:
    LED_EXTENSION = 0x21
    SERVOS_RIGHT = 0x40
    SERVOS_LEFT = 0x60


class LedExtensionPin:
    A_MINOR = 2
    A_MAJOR = 0
    D_MINOR = 3
    D_MAJOR = 1
    G_MINOR = 4
    C_MAJOR = 5
    F_MAJOR = 6
    B_FLAT_MAJOR = 7


class ServoSide(Enum):
    LEFT = "left"
    RIGHT = "right"


class ServosLeftPin(Enum):
    HIHAT = 15
    CROCO_JAW_CENTER = 0
    CROCO_BASE_LEFT = 4
    CROCO_JAW_LEFT = 7


class ServosRightPin(Enum):
    RIDE = 0
    CROCO_BASE_RIGHT = 4
    CROCO_JAW_RIGHT = 5
    CROCO_BASE_CENTER = 8


class ServoName(Enum):
    HIHAT = "hihat"
    RIDE = "ride"
    CROCO_BASE_RIGHT = "crocodile base right"
    CROCO_BASE_CENTER = "crocodile base center"
    CROCO_BASE_LEFT = "crocodile base left"
    CROCO_JAW_LEFT = "crocodile jaw left"
    CROCO_JAW_CENTER = "crocodile jaw center"
    CROCO_JAW_RIGHT = "crocodile jaw right"


class ServoConfig(NamedTuple):
    side: ServoSide
    pin: Union[ServosLeftPin, ServosRightPin]
    min_angle: float = 19
    max_angle: float = 71


ServoConfigs = {
    ServoName.HIHAT: ServoConfig(ServoSide.LEFT, ServosLeftPin.HIHAT),
    ServoName.RIDE: ServoConfig(
        ServoSide.RIGHT, ServosRightPin.RIDE, min_angle=20, max_angle=65
    ),
    ServoName.CROCO_BASE_RIGHT: ServoConfig(
        ServoSide.RIGHT, ServosRightPin.CROCO_BASE_RIGHT
    ),
    ServoName.CROCO_BASE_CENTER: ServoConfig(
        ServoSide.RIGHT, ServosRightPin.CROCO_BASE_CENTER
    ),
    ServoName.CROCO_BASE_LEFT: ServoConfig(
        ServoSide.LEFT, ServosLeftPin.CROCO_BASE_LEFT
    ),
    ServoName.CROCO_JAW_RIGHT: ServoConfig(
        ServoSide.RIGHT, ServosRightPin.CROCO_JAW_RIGHT, min_angle=40, max_angle=60
    ),
    ServoName.CROCO_JAW_CENTER: ServoConfig(
        ServoSide.LEFT, ServosLeftPin.CROCO_JAW_CENTER, min_angle=45, max_angle=62
    ),
    ServoName.CROCO_JAW_LEFT: ServoConfig(
        ServoSide.LEFT, ServosLeftPin.CROCO_JAW_LEFT, min_angle=28, max_angle=40
    ),
}


# midi/music


class ChordType:
    MAJOR = "major"
    MINOR = "minor"


class MidiChannel:
    DRUMS = 0
    CHORDS = 1
    SYSTEM = 2


class MidiMessageType(Enum):
    ON = True
    OFF = False


class DrumMidiNote:
    RIDE = 51
    HIHAT = 42
    CLICK = 37


class ChordMidiNote:
    A_MAJOR = 21
    A_MINOR = 20
    D_MAJOR = 14
    D_MINOR = 13
    G_MINOR = 18
    C_MAJOR = 12
    F_MAJOR = 17
    B_FLAT_MAJOR = 22


MIDI_MAPPING_CHORDS = {
    ChordMidiNote.C_MAJOR: LedExtensionPin.C_MAJOR,
    ChordMidiNote.D_MAJOR: LedExtensionPin.D_MAJOR,
    ChordMidiNote.D_MINOR: LedExtensionPin.D_MINOR,
    ChordMidiNote.F_MAJOR: LedExtensionPin.F_MAJOR,
    ChordMidiNote.G_MINOR: LedExtensionPin.G_MINOR,
    ChordMidiNote.A_MAJOR: LedExtensionPin.A_MAJOR,
    ChordMidiNote.A_MINOR: LedExtensionPin.A_MINOR,
    ChordMidiNote.B_FLAT_MAJOR: LedExtensionPin.B_FLAT_MAJOR,
}

# class ChordMidiNote:
#  A = 21
#  D = 14
#  G = 19
#  C = 12
#  F = 17
#  B_FLAT = 22
