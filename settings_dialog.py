from PyQt5.QtWidgets import QDialog, QComboBox, QVBoxLayout, QLabel, QHBoxLayout, QPushButton, QInputDialog, \
    QLineEdit, QMessageBox, QSplitter, QFrame, QFormLayout, QDoubleSpinBox, QSpinBox
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
        self.combo_set_micro = QComboBox()
        self.edt_res_width = QSpinBox()
        self.edt_res_height = QSpinBox()
        self.edt_offset_left = QSpinBox()
        self.edt_offset_right = QSpinBox()
        self.edt_offset_top = QSpinBox()
        self.edt_offset_bottom = QSpinBox()
        self.edt_pixels_in_mm = QDoubleSpinBox()
        self.edt_work_height = QDoubleSpinBox()
        self.edt_focus = QLineEdit()
        self.edt_zoom_ratio = QLineEdit()
        self.init_ui()

    # Создание элементов формы
    def init_ui(self):
        self.setMinimumWidth(480)
        layout_main = QVBoxLayout()

        lbl_micros = QLabel("Выбранная камера")
        # lbl_micros.setAlignment(Qt.AlignHCenter)
        font_title = lbl_micros.font()
        font_title.setBold(True)
        font_title.setPixelSize(16)
        lbl_micros.setFont(font_title)
        layout_main.addWidget(lbl_micros)
        layout_micros = QHBoxLayout()
        self.combo_micros.currentIndexChanged.connect(self.combo_micros_changed)
        layout_micros.addWidget(self.combo_micros)
        btn_micros_add = QPushButton("Добавить")
        btn_micros_add.setMaximumWidth(80)
        btn_micros_add.clicked.connect(self.btn_micros_add_click)
        layout_micros.addWidget(btn_micros_add)
        btn_micros_edt = QPushButton("Изменить")
        btn_micros_edt.setMaximumWidth(80)
        btn_micros_edt.clicked.connect(self.btn_micros_edt_click)
        layout_micros.addWidget(btn_micros_edt)
        btn_micros_del = QPushButton("Удалить")
        btn_micros_del.setMaximumWidth(80)
        btn_micros_del.clicked.connect(self.btn_micros_del_click)
        layout_micros.addWidget(btn_micros_del)
        layout_main.addLayout(layout_micros)

        for edt_px in [self.edt_res_width, self.edt_res_height, self.edt_offset_left, self.edt_offset_right,
                       self.edt_offset_top, self.edt_offset_bottom]:
            edt_px.setMinimum(0)
            edt_px.setMaximum(40000)
            edt_px.setSuffix(" px")

        lbl_resolution = QLabel("Разрешение")
        lbl_resolution.setFont(font_title)
        layout_main.addWidget(lbl_resolution)
        layout_resolution = QHBoxLayout()
        layout_resolution.addWidget(QLabel("Ширина"))
        self.edt_res_width.setValue(1024)
        self.edt_res_width.setMinimum(20)
        layout_resolution.addWidget(self.edt_res_width)
        layout_resolution.addWidget(QLabel("Высота"))
        self.edt_res_height.setValue(768)
        self.edt_res_height.setMinimum(10)
        layout_resolution.addWidget(self.edt_res_height)
        layout_main.addLayout(layout_resolution)

        lbl_set_micro = QLabel("Режимы съемки")
        lbl_set_micro.setFont(font_title)
        layout_main.addWidget(lbl_set_micro)
        layout_set_micro = QHBoxLayout()
        self.combo_set_micro.currentIndexChanged.connect(self.combo_set_micro_changed)
        layout_set_micro.addWidget(self.combo_set_micro)
        btn_set_micro_add = QPushButton("Добавить")
        btn_set_micro_add.setMaximumWidth(80)
        btn_set_micro_add.clicked.connect(self.btn_set_micro_add_click)
        layout_set_micro.addWidget(btn_set_micro_add)
        btn_set_micro_edt = QPushButton("Изменить")
        btn_set_micro_edt.setMaximumWidth(80)
        btn_set_micro_edt.clicked.connect(self.btn_set_micro_edt_click)
        layout_set_micro.addWidget(btn_set_micro_edt)
        btn_set_micro_del = QPushButton("Удалить")
        btn_set_micro_del.setMaximumWidth(80)
        btn_set_micro_del.clicked.connect(self.btn_set_micro_del_click)
        layout_set_micro.addWidget(btn_set_micro_del)
        layout_main.addLayout(layout_set_micro)

        layout_offset = QFormLayout()
        layout_offset.addRow(QLabel("Размер отступа слева"), self.edt_offset_left)
        layout_offset.addRow(QLabel("Размер отступа справа"), self.edt_offset_right)
        layout_offset.addRow(QLabel("Размер отступа сверху"), self.edt_offset_top)
        layout_offset.addRow(QLabel("Размер отступа снизу"), self.edt_offset_bottom)

        layout_offset.addRow(QLabel("Пикселей на мм"), self.edt_pixels_in_mm)
        layout_offset.addRow(QLabel("Высота работы камеры, мм"), self.edt_work_height)
        layout_offset.addRow(QLabel("Фокус"), self.edt_focus)
        layout_offset.addRow(QLabel("Увеличение"), self.edt_zoom_ratio)

        layout_main.addLayout(layout_offset)

        layout_main.addWidget(QPushButton("ОК"))

        self.setLayout(layout_main)

    def combo_micros_changed(self):
        print(self.combo_micros.currentText())

    def combo_set_micro_changed(self):
        print(self.combo_set_micro.currentText())

    def btn_micros_add_click(self):
        input_dialog = QInputDialog()
        text, ok = input_dialog.getText(self, "Добавление камеры", "Наименование", QLineEdit.Normal)

        if ok:
            self.combo_micros.addItem(text)
            self.combo_micros.setCurrentIndex(self.combo_micros.count() - 1)

    def btn_micros_edt_click(self):
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

    def btn_micros_del_click(self):
        if self.combo_micros.count() == 0:
            return
        dlg_result = QMessageBox.question(self,
                                          "Confirm Dialog",
                                          "Вы действительно хотите удалить выбранную камеру со всеми настройками?",
                                          QMessageBox.Yes | QMessageBox.No,
                                          QMessageBox.No)
        if dlg_result == QMessageBox.Yes:
            input_dialog = QInputDialog()
            text, ok = input_dialog.getText(self, "Удаление камеры",
                                            "Для удаления напишите \"удалить\"", QLineEdit.Normal)
            if ok and str.lower(text) == "удалить":
                self.combo_micros.removeItem(self.combo_micros.currentIndex())

    def btn_set_micro_add_click(self):
        input_dialog = QInputDialog()
        text, ok = input_dialog.getText(self, "Добавление настройки", "Наименование", QLineEdit.Normal)

        if ok:
            self.combo_set_micro.addItem(text)
            self.combo_set_micro.setCurrentIndex(self.combo_set_micro.count() - 1)

    def btn_set_micro_edt_click(self):
        if self.combo_set_micro.count() == 0:
            return
        input_dialog = QInputDialog()
        text, ok = input_dialog.getText(self,
                                        "Переименование настройки", "Наименование",
                                        QLineEdit.Normal, self.combo_set_micro.currentText())
        if ok and text:
            i = self.combo_set_micro.currentIndex()
            self.combo_set_micro.removeItem(self.combo_set_micro.currentIndex())
            self.combo_set_micro.insertItem(i, text)
            self.combo_set_micro.setCurrentIndex(i)

    def btn_set_micro_del_click(self):
        if self.combo_set_micro.count() == 0:
            return
        dlg_result = QMessageBox.question(self,
                                          "Confirm Dialog",
                                          "Вы действительно хотите удалить выбранную настройку полностью?",
                                          QMessageBox.Yes | QMessageBox.No,
                                          QMessageBox.No)
        if dlg_result == QMessageBox.Yes:
            input_dialog = QInputDialog()
            text, ok = input_dialog.getText(self, "Удаление настройки",
                                            "Для удаления напишите \"удалить\"", QLineEdit.Normal)
            if ok and str.lower(text) == "удалить":
                self.combo_set_micro.removeItem(self.combo_set_micro.currentIndex())
