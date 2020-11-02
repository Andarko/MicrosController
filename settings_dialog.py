from PyQt5.QtWidgets import QDialog
import configparser


class ProgramSettings(object):
    def __init__(self):
        self.pixels_in_mm = 10
        self.snap_width_half = 10
        self.snap_height_half = 5


class SettingsDialog(QDialog):
    def __init__(self, program_settings=ProgramSettings()):
        super().__init__()