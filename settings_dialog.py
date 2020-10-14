from PyQt5.QtWidgets import QDialog
import configparser


class ProgramSettings(object):
    def __init__(self):
        self.snap_height = 20


class SettingsDialog(QDialog):
    def __init__(self, program_settings=ProgramSettings()):
        super().__init__()