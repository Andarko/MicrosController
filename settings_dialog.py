from PyQt5.QtWidgets import QDialog, QComboBox, QVBoxLayout, QLabel, QHBoxLayout, QPushButton, QInputDialog, \
    QLineEdit, QMessageBox, QSplitter, QFrame
from PyQt5.QtCore import Qt, QSize


class MicrosSettings(object):
    def __init__(self):
        self.name: str
        self.resolution: QSize


class ShotSetting(object):
    def __init__(self):
        self.pixels_in_mm = 10.0
        self.snap_width_half = 10.0
        self.snap_height_half = 5.0


class ProgramSettings(object):
    def __init__(self):
        self.micros_settings: MicrosSettings()
        self.pixels_in_mm = 10.0
        self.snap_width_half = 10.0
        self.snap_height_half = 5.0


class SettingsDialog(QDialog):
    def __init__(self, program_settings: ProgramSettings()):
        super().__init__()
        self.all_micros_settings = list()
        self.combo_micros = QComboBox()
        self.init_ui()

    # Создание элементов формы
    def init_ui(self):
        self.setMinimumWidth(640)
        main_layout = QVBoxLayout()

        micros_lbl = QLabel("Выбранный микроскоп")
        micros_lbl.setAlignment(Qt.AlignHCenter)
        font_title = micros_lbl.font()
        font_title.setBold(True)
        font_title.setPixelSize(16)
        micros_lbl.setFont(font_title)
        main_layout.addWidget(micros_lbl)
        micros_layout = QHBoxLayout()
        self.combo_micros.currentIndexChanged.connect(self.combo_micros_changed)
        micros_layout.addWidget(self.combo_micros)
        micros_btn_add = QPushButton("Добавить")
        micros_btn_add.setMaximumWidth(80)
        micros_btn_add.clicked.connect(self.micros_btn_add_click)
        micros_layout.addWidget(micros_btn_add)
        micros_edt_add = QPushButton("Изменить")
        micros_edt_add.setMaximumWidth(80)
        micros_edt_add.clicked.connect(self.micros_btn_edt_click)
        micros_layout.addWidget(micros_edt_add)
        micros_del_add = QPushButton("Удалить")
        micros_del_add.setMaximumWidth(80)
        micros_del_add.clicked.connect(self.micros_btn_del_click)
        micros_layout.addWidget(micros_del_add)
        main_layout.addLayout(micros_layout)

        splitter = QSplitter(Qt.Horizontal)
        
        main_layout.addWidget(splitter)

        main_layout.addWidget(QPushButton("ОК"))

        self.setLayout(main_layout)

    def combo_micros_changed(self):
        print(self.combo_micros.currentText())

    def micros_btn_add_click(self):
        input_dialog = QInputDialog()
        text, ok = input_dialog.getText(self, "Добавление камеры", "Наименование", QLineEdit.Normal)

        if ok:
            self.combo_micros.addItem(text)
            self.combo_micros.setCurrentIndex(self.combo_micros.count() - 1)

    def micros_btn_edt_click(self):
        if self.combo_micros.count() == 0:
            return
        input_dialog = QInputDialog()
        text, ok = input_dialog.getText(self,
                                        "Переименование камеры", "Наименование",
                                        QLineEdit.Normal, self.combo_micros.currentText())
        if ok and text:
            i = self.combo_micros.currentIndex()
            self.combo_micros.removeItem(self.combo_micros.currentIndex())
            self.combo_micros.insertItem(i, text)
            self.combo_micros.setCurrentIndex(i)

    def micros_btn_del_click(self):
        if self.combo_micros.count() == 0:
            return
        dlg_result = QMessageBox.question(self,
                                          "Confirm Dialog",
                                          "Вы действительно хотите удалить камеру со всеми настройками?",
                                          QMessageBox.Yes | QMessageBox.No,
                                          QMessageBox.No)
        if dlg_result == QMessageBox.Yes:
            input_dialog = QInputDialog()
            text, ok = input_dialog.getText(self, "Удаление камеры",
                                            "Для удаления напишите \"удалить\"", QLineEdit.Normal)
            if ok and str.lower(text) == "удалить":
                self.combo_micros.removeItem(self.combo_micros.currentIndex())
