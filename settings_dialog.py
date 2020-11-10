from PyQt5.QtWidgets import QDialog, QComboBox, QVBoxLayout, QLabel, QWidget, QHBoxLayout, QPushButton
from PyQt5.QtCore import Qt
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

        self.combo_micros = QComboBox()
        self.init_ui()

    # Создание элементов формы
    def init_ui(self):
        main_layout = QVBoxLayout()

        micros_lbl = QLabel("Выбранный микроскоп")
        micros_lbl.setAlignment(Qt.AlignHCenter)
        font_title = micros_lbl.font()
        font_title.setBold(True)
        font_title.setPixelSize(18)
        micros_lbl.setFont(font_title)
        main_layout.addWidget(micros_lbl)
        micros_layout = QHBoxLayout()
        self.combo_micros.currentIndexChanged.connect(self.combo_micros_changed)
        micros_layout.addWidget(self.combo_micros)
        micros_btn_add = QPushButton("Добавить")
        micros_btn_add.clicked.connect(self.micros_btn_add_click)
        micros_layout.addWidget(micros_btn_add)
        micros_edt_add = QPushButton("Изменить")
        micros_edt_add.clicked.connect(self.micros_btn_edt_click)
        micros_layout.addWidget(micros_edt_add)
        micros_del_add = QPushButton("Удалить")
        micros_del_add.clicked.connect(self.micros_btn_del_click)
        micros_layout.addWidget(micros_del_add)
        main_layout.addLayout(micros_layout)

        self.setLayout(main_layout)

    def combo_micros_changed(self):
        print(self.combo_micros.currentText())

    def micros_btn_add_click(self):
        pass

    def micros_btn_edt_click(self):
        pass

    def micros_btn_del_click(self):
        pass