from PyQt5.QtWidgets import QDialog
import configparser


class ShotSetting(object):
    def __init__(self):
        self.pixels_in_mm = 10.0
        self.snap_width_half = 10.0
        self.snap_height_half = 5.0


class ProgramSettings(object):
    def __init__(self):
        self.pixels_in_mm = 10.0
        self.snap_width_half = 10.0
        self.snap_height_half = 5.0


class SettingsDialog(QDialog):
    def __init__(self, program_settings: ProgramSettings()):
        super().__init__()