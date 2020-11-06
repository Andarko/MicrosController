# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

import asyncio
# import shutil
import time
import os
import websockets

from PyQt5.QtGui import QImage
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QSizePolicy, QFileDialog, QMessageBox
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout
from PyQt5.QtWidgets import QAction, QInputDialog, QLineEdit, QLabel, QPushButton, QTextEdit, QFormLayout
from PyQt5.QtCore import QEvent, Qt
import sys
import numpy as np
import cv2
import datetime
import zipfile

from PyQt5 import QtGui
from vassal import Terminal
from threading import Thread
import json
import math
import xml.etree.ElementTree as Xml

from settings_dialog import SettingsDialog, ProgramSettings


# Класс главного окна
class MainWindow(QMainWindow):
    # Инициализация
    def __init__(self):
        super().__init__()

        # self.micros_controller = TableController('localhost', 5001)
        self.loop = asyncio.get_event_loop()
        self.table_controller = TableController(self.loop)
        self.micros_controller = MicrosController()

        if not self.table_controller.thread_server or not self.table_controller.thread_server.is_alive():
            self.table_controller.thread_server.start()
        time.sleep(2.0)
        # self.micros_controller.coord_check()
        self.continuous_mode = False
        self.closed = False
        self.key_shift_pressed = False
        # self.keyboard_buttons = {Qt.Key_Up: KeyboardButton(), Qt.Key_Right: KeyboardButton(),
        #                          Qt.Key_Down: KeyboardButton(), Qt.Key_Left: KeyboardButton(),
        #                          Qt.Key_Plus: KeyboardButton(), Qt.Key_Minus: KeyboardButton()}
        self.keyboard_buttons = {Qt.Key_W: KeyboardButton(), Qt.Key_D: KeyboardButton(),
                                 Qt.Key_S: KeyboardButton(), Qt.Key_A: KeyboardButton(),
                                 Qt.Key_Plus: KeyboardButton(), Qt.Key_Minus: KeyboardButton()}
        self.thread_continuous = Thread(target=self.continuous_move)
        self.thread_continuous.start()

        self.dir_for_img = "SavedImg"
        self.path_for_xml_file = os.path.join(self.dir_for_img, "settings.xml")

        self.programSettings = ProgramSettings()
        # TEST Для удобства тестирования передаю в контроллер стола контроллер камеры
        self.table_controller.test = True
        if self.table_controller.test:
            self.table_controller.micros_controller = self.micros_controller
            self.table_controller.programSettings = self.programSettings

        self.pixels_in_mm = self.programSettings.pixels_in_mm
        self.snap_width_half = self.programSettings.snap_width_half
        self.snap_height_half = self.programSettings.snap_height_half
        self.snap_width = 2 * self.snap_width_half
        self.snap_height = 2 * self.snap_height_half
        self.delta_x = int(self.snap_width_half * self.pixels_in_mm / 5)
        self.delta_y = int(self.snap_height_half * self.pixels_in_mm / 5)
        # Наличие несохраненного изображения
        self.unsaved = False

        if self.table_controller.test:
            print("Внимание! Программа работает в тестовом режиме!")

        # Доступные для взаимодействия компоненты формы
        self.lbl_img = QLabel()
        self.lbl_coord = QLabel("Текущие координаты:")
        self.btn_init = QPushButton("Инициализация")
        self.btn_move_mid = QPushButton("Двигать в середину")
        self.btn_move = QPushButton("Двигать в ...")
        self.btn_manual = QPushButton("Ручной режим")
        self.edt_border_x1 = QTextEdit()
        self.edt_border_y1 = QTextEdit()
        self.edt_border_x2 = QTextEdit()
        self.edt_border_y2 = QTextEdit()
        self.btn_border = QPushButton("Определить границы")
        self.btn_scan = QPushButton("Новая съемка")
        self.btn_save_scan = QPushButton("Сохранить съемку")

        self.init_ui()

        # snap = self.micros_controller.snap(1500, 2500, 2500, 3500)
        # self.lbl_img.setPixmap(self.micros_controller.numpy_to_pixmap(snap))

    # Создание элементов формы
    def init_ui(self):

        # keyboard.add_hotkey("Ctrl + 1", lambda: print("Left"))

        # Основное меню
        menu_bar = self.menuBar()
        # Меню "Станок"
        device_menu = menu_bar.addMenu("&Станок")
        device_menu_action_init = QAction("&Инициализация", self)
        device_menu_action_init.setShortcut("Ctrl+N")
        device_menu_action_init.triggered.connect(self.device_init)
        device_menu.addAction(device_menu_action_init)

        device_menu.addSeparator()
        device_menu_action_check = QAction("&Проверка", self)
        device_menu_action_check.setShortcut("Ctrl+C")
        device_menu_action_check.triggered.connect(self.device_check)
        device_menu.addAction(device_menu_action_check)

        device_menu.addSeparator()
        device_menu_action_move = QAction("&Двигать", self)
        device_menu_action_move.setShortcut("Ctrl+M")
        device_menu_action_move.triggered.connect(self.device_move)
        device_menu.addAction(device_menu_action_move)

        device_menu.addSeparator()
        device_menu_action_test_circle = QAction("&Круг", self)
        device_menu_action_test_circle.triggered.connect(self.test_circle)
        device_menu.addAction(device_menu_action_test_circle)

        device_menu.addSeparator()
        device_menu_action_exit = QAction("&Выйти", self)
        device_menu_action_exit.setShortcut("Ctrl+Q")
        device_menu_action_exit.setStatusTip("Закрыть приложение")
        device_menu_action_exit.triggered.connect(self.close)
        device_menu.addAction(device_menu_action_exit)
        menu_bar.addMenu(device_menu)

        # Меню "Настройки"
        services_menu = menu_bar.addMenu("&Сервис")
        services_menu_action_settings = QAction("&Настройки", self)
        services_menu_action_settings.triggered.connect(self.services_menu_action_settings_click)
        services_menu.addAction(services_menu_action_settings)
        menu_bar.addMenu(services_menu)

        # установка центрального виджета и лайаута
        main_widget = QWidget(self)
        central_layout = QHBoxLayout()
        main_widget.setLayout(central_layout)
        self.setCentralWidget(main_widget)

        # левый лайаут с изображением
        left_layout = QVBoxLayout()
        central_layout.addLayout(left_layout)
        self.lbl_img.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.lbl_img.setStyleSheet("border: 1px solid red")
        left_layout.addWidget(self.lbl_img)

        # правый лайаут с панелью
        right_layout = QVBoxLayout()
        central_layout.addLayout(right_layout)
        right_layout.addWidget(self.lbl_coord)
        self.btn_init.clicked.connect(self.device_init)
        right_layout.addWidget(self.btn_init)
        self.btn_move.clicked.connect(self.device_move)
        right_layout.addWidget(self.btn_move)
        self.btn_move_mid.clicked.connect(self.device_move_mid)
        right_layout.addWidget(self.btn_move_mid)

        self.btn_manual.setCheckable(True)
        self.btn_manual.setChecked(False)
        self.btn_manual.toggled["bool"].connect(self.device_manual)
        right_layout.addWidget(self.btn_manual)

        # self.edt_border_x1.setLineWrapMode(QTextEdit_LineWrapMode=QTextEdit.NoWrap)
        border_layout = QVBoxLayout()
        right_layout.addStretch()
        right_layout.addLayout(border_layout)
        border_layout.addWidget(QLabel("Границы съемки:"))
        # border_form_layout = QGridLayout()
        border_form_layout = QFormLayout()
        # self.edt_border_x1.setWordWrapMode(QtGui.QTextOption.NoWrap)
        self.edt_border_x1.setMaximumHeight(30)
        self.edt_border_y1.setMaximumHeight(30)
        self.edt_border_x2.setMaximumHeight(30)
        self.edt_border_y2.setMaximumHeight(30)

        border_form_layout.addRow(QLabel("x1"), self.edt_border_x1)
        border_form_layout.addRow(QLabel("y1"), self.edt_border_y1)
        border_form_layout.addRow(QLabel("x2"), self.edt_border_x2)
        border_form_layout.addRow(QLabel("y2"), self.edt_border_y2)
        border_form_layout.setSpacing(0)
        # border_form_layout.setSpacing(2)
        # border_form_layout.addWidget(QLabel("x1"), 0, 0)
        # border_form_layout.addWidget(self.edt_border_x1, 1, 0)
        # border_form_layout.addWidget(QLabel("y1"), 2, 0)
        # border_form_layout.addWidget(self.edt_border_y1, 3, 0)
        # border_form_layout.addWidget(QLabel("x2"), 0, 1)
        # border_form_layout.addWidget(self.edt_border_x2, 1, 1)
        # border_form_layout.addWidget(QLabel("y2"), 2, 1)
        # border_form_layout.addWidget(self.edt_border_y2, 3, 1)

        border_layout.addLayout(border_form_layout)

        right_layout.addWidget(self.btn_border)
        self.btn_border.clicked.connect(self.border_find)
        right_layout.addWidget(self.btn_scan)
        self.btn_scan.clicked.connect(self.scan)
        right_layout.addWidget(self.btn_save_scan)
        self.btn_save_scan.clicked.connect(self.save_scan)
        self.btn_save_scan.setEnabled(False)

        self.installEventFilter(self)

        self.resize(1280, 720)
        self.move(300, 300)
        self.setMinimumSize(800, 600)

        self.show()

    # Тестовая обертка функции движения, чтобы обходиться без подключенного станка
    def coord_move(self, coord, mode="discrete"):
        self.table_controller.coord_move(coord, mode)
        snap = self.micros_controller.snap(int(self.pixels_in_mm * (self.table_controller.coord_mm[0]
                                                                    - self.snap_width_half)),
                                           int(self.pixels_in_mm * (self.table_controller.coord_mm[1]
                                                                    - self.snap_height_half)),
                                           int(self.pixels_in_mm * (self.table_controller.coord_mm[0]
                                                                    + self.snap_width_half)),
                                           int(self.pixels_in_mm * (self.table_controller.coord_mm[1]
                                                                    + self.snap_height_half)))
        self.lbl_img.setPixmap(self.micros_controller.numpy_to_pixmap(snap))
        self.lbl_img.repaint()
        self.setWindowTitle(str(self.table_controller))
        return snap

    def closeEvent(self, event):
        if self.unsaved:
            dlg_result = QMessageBox.question(self,
                                              "Confirm Dialog",
                                              "Данные последней съемки не сохранены. Хотите сперва их сохранить?",
                                              QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                                              QMessageBox.Yes)
            if dlg_result == QMessageBox.Yes:
                if not self.save_scan():
                    return
            elif dlg_result == QMessageBox.Cancel:
                event.ignore()
        self.closed = True

    @staticmethod
    def services_menu_action_settings_click(self):
        settings_dialog = SettingsDialog(self.programSettings)
        settings_dialog.setAttribute(Qt.WA_DeleteOnClose)
        settings_dialog.exec()

    def device_init(self):
        self.control_elements_enabled(False)
        self.table_controller.coord_init()
        self.setWindowTitle(str(self.table_controller))
        self.control_elements_enabled(True)

    def device_check(self):
        self.table_controller.coord_check()
        self.setWindowTitle(str(self.table_controller))

    def device_move(self):
        self.control_elements_enabled(False)
        input_dialog = QInputDialog()
        text, ok = input_dialog.getText(self,
                                        "Введите дистанцию в миллиметрах",
                                        "Дистанция:",
                                        QLineEdit.Normal,
                                        str(int(self.table_controller.coord_mm[0])) + ';'
                                        + str(int(self.table_controller.coord_mm[1])) + ';'
                                        + str(int(self.table_controller.coord_mm[2])))

        if ok:
            coord = [int(item) for item in text.split(';')]
            self.coord_move(coord)
            self.setWindowTitle(str(self.table_controller))

        self.control_elements_enabled(True)

    def device_move_mid(self):
        self.control_elements_enabled(False)
        x = int(self.table_controller.limits_step[0] / self.table_controller.steps_in_mm / 2)
        y = int(self.table_controller.limits_step[1] / self.table_controller.steps_in_mm / 2)
        self.coord_move([x, y, self.table_controller.coord_mm[2]])
        self.setWindowTitle(str(self.table_controller))
        self.control_elements_enabled(True)

    def device_manual(self, status):
        self.continuous_mode = status
        self.control_elements_enabled(not status)

    def control_elements_enabled(self, status):
        self.btn_init.setEnabled(status)
        self.btn_move.setEnabled(status)
        self.btn_move_mid.setEnabled(status)
        self.btn_border.setEnabled(status)
        self.btn_scan.setEnabled(status)
        self.edt_border_x1.setEnabled(status)
        self.edt_border_y1.setEnabled(status)
        self.edt_border_x2.setEnabled(status)
        self.edt_border_y2.setEnabled(status)

    # Тестовая функция для рисования круга и спирали
    def test_circle(self):
        self.table_controller.coord_check()
        count = 200
        r = 0.0
        # r = 20
        for i in range(20*count + 1):
            r += 1 / 10
            alfa = (i / count) * 2 * math.pi
            dx = int(r * math.sin(alfa))
            dy = int(r * math.cos(alfa))
            self.coord_move([dx, dy, 0], mode='continuous')

            # self.micros_controller.coord_move([self.micros_controller.coord[0] + dx,
            #                                    self.micros_controller.coord[1] + dy,
            #                                    self.micros_controller.coord[2]])

        # for d in range(1, 7):
        #     print(d)
        #     d_steps = int(2 ** d)
        #     for i in range(100):
        #         self.micros_controller.coord_move([d_steps, 0, 0], mode='continuous')
        #     for i in range(100):
        #         self.micros_controller.coord_move([-d_steps, 0, 0], mode='continuous')
        #     for i in range(100):
        #         self.micros_controller.coord_move([0, d_steps, 0], mode='continuous')
        #     for i in range(100):
        #         self.micros_controller.coord_move([0, -d_steps, 0], mode='continuous')

    # Функция идет по границе изделия и записывает пределы для съемки
    def border_find(self):
        self.control_elements_enabled(False)
        try:
            if self.table_controller.server_status == 'uninitialized':
                self.table_controller.coord_init()
            # Перевод камеры к позиции, где должна располагаться микросхема

            x = int(self.table_controller.limits_step[0] / self.table_controller.steps_in_mm / 2)
            y = int(self.table_controller.limits_step[1] / self.table_controller.steps_in_mm / 2)
            snap = self.coord_move([x, y, self.snap_height], mode="discrete")

            all_x = list()
            all_y = list()
            all_x.append(x)
            all_y.append(y)

            # snap = self.micros_controller.snap(self.pixels_in_mm * (x - self.snap_width_half),
            #                                    self.pixels_in_mm * (y - self.snap_height_half),
            #                                    self.pixels_in_mm * (x + self.snap_width_half),
            #                                    self.pixels_in_mm * (y + self.snap_height_half))
            #
            # self.lbl_img.setPixmap(self.micros_controller.numpy_to_pixmap(snap))
            # self.lbl_img.repaint()
            # Направления для поиска краев
            direction_sequence = [[1, 0], [0, 1], [-1, 0], [0, -1], [1, 0], [0, 1]]
            previous_direction = None
            in_border = False

            for direction in direction_sequence:
                # Берем следующий фрейм до тех пор, пока не выйдем за границу изделтя
                next_frame = True
                while next_frame:
                    # При наличии предыдущего направления движения (все, кроме первого направления)
                    # проверяем, не смещается ли изделие поперек линии поиска
                    if previous_direction:
                        steps_count = self.check_object_inside(snap, previous_direction, [self.delta_x, self.delta_y])
                        # Проверяем - не ушли ли мы вовнутрь объекта
                        while steps_count > 0:
                            x += int(self.delta_x * steps_count * previous_direction[0] / self.pixels_in_mm)
                            y -= int(self.delta_y * steps_count * previous_direction[1] / self.pixels_in_mm)
                            all_x.append(x)
                            all_y.append(y)
                            snap = self.coord_move([x, y, self.snap_height], mode="discrete")
                            # snap = self.micros_controller.snap(self.pixels_in_mm * (x - self.snap_width_half),
                            #                                    self.pixels_in_mm * (y - self.snap_height_half),
                            #                                    self.pixels_in_mm * (x + self.snap_width_half),
                            #                                    self.pixels_in_mm * (y + self.snap_height_half))
                            # self.lbl_img.setPixmap(self.micros_controller.numpy_to_pixmap(snap))
                            # self.lbl_img.repaint()
                            print('x = ' + str(x) + '; y = ' + str(y) + ' inside correction')

                            steps_count = self.check_object_inside(snap,
                                                                   previous_direction,
                                                                   [self.delta_x, self.delta_y])
                        previous_opposite_direction = list()
                        previous_opposite_direction.append(-previous_direction[0])
                        previous_opposite_direction.append(-previous_direction[1])

                        steps_count = self.check_object_outside(snap,
                                                                previous_opposite_direction,
                                                                [self.delta_x, self.delta_y])
                        # Проверяем - не ушли ли мы наружу объекта
                        while steps_count > 0:
                            x += int(self.delta_x * steps_count * previous_opposite_direction[0] / self.pixels_in_mm)
                            y -= int(self.delta_y * steps_count * previous_opposite_direction[1] / self.pixels_in_mm)
                            all_x.append(x)
                            all_y.append(y)
                            snap = self.coord_move([x, y, self.snap_height], mode="discrete")
                            # snap = self.micros_controller.snap(self.pixels_in_mm * (x - self.snap_width_half),
                            #                                    self.pixels_in_mm * (y - self.snap_height_half),
                            #                                    self.pixels_in_mm * (x + self.snap_width_half),
                            #                                    self.pixels_in_mm * (y + self.snap_height_half))
                            # self.lbl_img.setPixmap(self.micros_controller.numpy_to_pixmap(snap))
                            # self.lbl_img.repaint()
                            print('x = ' + str(x) + '; y = ' + str(y) + ' outside correction')
                            steps_count = self.check_object_outside(snap,
                                                                    previous_direction,
                                                                    [self.delta_x, self.delta_y])

                    check_border_result = self.find_border_in_image(snap,
                                                                    direction,
                                                                    [self.delta_x, self.delta_y])
                    # Можно идти в направлении поиска границы еще
                    if check_border_result.startswith('next'):
                        steps_count = int(check_border_result[4])
                        x += int(self.delta_x * direction[0] * steps_count / self.pixels_in_mm)
                        y -= int(self.delta_y * direction[1] * steps_count / self.pixels_in_mm)
                        all_x.append(x)
                        all_y.append(y)
                        snap = self.coord_move([x, y, self.snap_height], mode="discrete")
                        # snap = self.micros_controller.snap(self.pixels_in_mm * (x - self.snap_width_half),
                        #                                    self.pixels_in_mm * (y - self.snap_height_half),
                        #                                    self.pixels_in_mm * (x + self.snap_width_half),
                        #                                    self.pixels_in_mm * (y + self.snap_height_half))
                        # self.lbl_img.setPixmap(self.micros_controller.numpy_to_pixmap(snap))
                        # self.lbl_img.repaint()
                    print('x = ' + str(x) + '; y = ' + str(y))

                    if check_border_result == 'stop':
                        next_frame = False
                previous_direction = direction
            self.edt_border_x1.setText(str(min(all_x)))
            self.edt_border_y1.setText(str(min(all_y)))
            self.edt_border_x2.setText(str(max(all_x)))
            self.edt_border_y2.setText(str(max(all_y)))
        finally:
            self.control_elements_enabled(True)
            QMessageBox.information(self, "Info Dialog", "Границы определены", QMessageBox.Ok, QMessageBox.Ok)

    # Вспомогательная функция для определения - достигла ли камера границы при поиске в заданном направлении
    @staticmethod
    def find_border_in_image(img, direction, delta):
        # Проверяем - не стало ли по направлению движения "чисто" (все линии)
        if direction[0] != 0:
            middle = int(img.shape[1] / 2)
            if direction[0] > 0:
                middle -= 1
            for i in range(5, 0, -1):
                x = middle + i * delta[0] * direction[0]
                for y in range(img.shape[0]):
                    if img[y][x][0] < 200 or img[y][x][1] < 200 or img[y][x][2] < 200:
                        return 'next' + str(i)
        else:
            middle = int(img.shape[0] / 2)
            if direction[1] > 0:
                middle -= 1
            for i in range(5, 0, -1):
                y = middle + i * delta[1] * direction[1]
                for x in range(img.shape[1]):
                    if img[y][x][0] < 200 or img[y][x][1] < 200 or img[y][x][2] < 200:
                        return 'next' + str(i)

        return 'stop'

    @staticmethod
    # Вспомогательная функция - перед поиском границ проверяем, что камера не уехала от объекта
    # Возвращает - сколько надо сделать шагов "внутрь"
    def check_object_outside(img, direction, delta):
        if direction[0] != 0:
            middle = int(img.shape[1] / 2)
            if direction[0] > 0:
                middle -= 1
            # Ищем хоть 1 пиксель объекта
            for i in range(5, 0, -1):
                white = True
                x = middle + i * delta[0] * direction[0]
                for y in range(img.shape[0]):
                    if img[y][x][0] < 200 or img[y][x][1] < 200 or img[y][x][2] < 200:
                        white = False
                        break
                if white:
                    return i
        else:
            white = True
            middle = int(img.shape[0] / 2)
            if direction[1] > 0:
                middle -= 1
            # Ищем хоть 1 пиксель объекта
            for i in range(5, 0, -1):
                y = middle + i * delta[1] * direction[1]
                for x in range(img.shape[1]):
                    if img[y][x][0] < 200 or img[y][x][1] < 200 or img[y][x][2] < 200:
                        white = False
                        break
                if white:
                    return i

        return 0

    @staticmethod
    # Вспомогательная функция - перед поиском границ проверяем, что камера не уехала внутрь объекта
    # Возвращает - сколько надо сделать шагов "наружу"
    def check_object_inside(img, direction, delta):
        if direction[0] != 0:
            middle = int(img.shape[1] / 2)
            if direction[0] > 0:
                middle -= 1
            # Ищем хоть одну "белую" линию "снаружи". Если она есть - значит все нормально
            for i in range(5, 0, -1):
                white = True
                x = middle + i * delta[0] * direction[0]
                for y in range(img.shape[0]):
                    if img[y][x][0] < 200 or img[y][x][1] < 200 or img[y][x][2] < 200:
                        white = False
                        break
                if not white:
                    return i
        else:
            middle = int(img.shape[0] / 2)
            if direction[1] > 0:
                middle -= 1
            # Ищем хоть одну "белую" линию "снаружи". Если она есть - значит все нормально
            for i in range(5, 0, -1):
                white = True
                y = middle + i * delta[1] * direction[1]
                for x in range(img.shape[1]):
                    if img[y][x][0] < 200 or img[y][x][1] < 200 or img[y][x][2] < 200:
                        white = False
                        break
                if not white:
                    return i
        return 0

    def scan(self):
        if self.unsaved:
            dlg_result = QMessageBox.question(self,
                                              "Confirm Dialog",
                                              "Данные последней съемки не сохранены. Хотите сперва их сохранить?",
                                              QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                                              QMessageBox.Yes)
            if dlg_result == QMessageBox.Yes:
                if not self.save_scan():
                    return
            elif dlg_result == QMessageBox.Cancel:
                return
        try:
            x1 = float(self.edt_border_x1.toPlainText())
            y1 = float(self.edt_border_y1.toPlainText())
            x2 = float(self.edt_border_x2.toPlainText())
            y2 = float(self.edt_border_y2.toPlainText())
        except ValueError:
            print("Неверный формат данных")
            return

        if self.table_controller.server_status == 'uninitialized':
            self.table_controller.coord_init()

        # Определяем на сколько мм выступает все поле съемки из целого числа кадров
        # x_overage = x2 - x1 - self.snap_width * int((x2 - x1) / self.snap_width)
        x_overage = (x2 - x1) % self.snap_width
        x_count = int((x2 - x1) // self.snap_width) + 1
        x_deficit = 0
        if x_overage > 0:
            # А это - сколько надо добавить к полю съемки, чтобы получилось целое число кадров
            x_deficit = self.snap_width - x_overage
            x_count += 1
            x2 += x_deficit / 2
            x1 -= x_deficit / 2

        # y_overage = y2 - y1 - self.snap_height * int((y2 - y1) / self.snap_height)
        y_overage = (y2 - y1) % self.snap_height
        y_count = int((y2 - y1) // self.snap_height + 1)
        y_deficit = 0
        if y_overage > 0:
            y_deficit = self.snap_height - y_overage
            y_count += 1
            y2 += y_deficit / 2
            y1 -= y_deficit / 2
        print("x1={0}; y1={1}; x2={2}; y2={3}".format(x1, y1, x2, y2))
        # Работа с директорией для сохранения изображений
        # shutil.rmtree(self.dir_for_img)
        if not os.path.exists(self.dir_for_img):
            os.mkdir(self.dir_for_img)
        for file in os.listdir(self.dir_for_img):
            os.remove(os.path.join(self.dir_for_img, file))
        # Получение и сохранение изображений в директорию
        left_dir = abs(self.table_controller.coord_mm[0] - x1) > abs(self.table_controller.coord_mm[0] - x2)

        # выбираем обход изображения, исходя из того - ближе мы к его верху или низу
        j_start = 0
        j_finish = y_count
        j_delta = 1
        if abs(self.table_controller.coord_mm[1] - y1) > abs(self.table_controller.coord_mm[1] - y2):
            j_start = y_count - 1
            j_finish = -1
            j_delta = -1

        for j in range(j_start, j_finish, j_delta):
            y = y1 + j * self.snap_height
            # В проге просмотра ось y вернута вниз
            j_r = y_count - 1 - j
            if left_dir:
                x_range = range(x_count - 1, -1, -1)
            else:
                x_range = range(0, x_count, 1)
            for i in x_range:
                x = x1 + i * self.snap_width
                snap = self.coord_move([x, y, self.snap_height], mode="discrete")
                cv2.imwrite(os.path.join(self.dir_for_img, "S_{0}_{1}.jpg".format(j_r + 1, i + 1)), snap[:, :, ::-1])
                print('x = ' + str(x) + '; y = ' + str(y))

            left_dir = not left_dir

        # выбираем обход изображения, исходя из того - ближе мы к его верху или низу
        # y_start = y1
        # y_finish = y2 + 1
        # y_delta = self.snap_height
        # j = int((y2 - y1) / self.snap_height) + 1
        # d_j = -1
        # if abs(self.table_controller.coord_mm[1] - y1) > abs(self.table_controller.coord_mm[1] - y2):
        #     y_start = y2
        #     y_finish = y1 - 1
        #     y_delta = -self.snap_height
        #     j = 1
        #     d_j = 1

        # for y in range(y_start, y_finish, y_delta):
        #     if left_dir:
        #         i = int((x2 - x1) / self.snap_width) + 1
        #         for x in range(x2, x1 - 1, -self.snap_width):
        #             snap = self.coord_move([x, y, self.snap_height], mode="discrete")
        #             # snap = self.micros_controller.snap(self.pixels_in_mm * (x - self.snap_width_half),
        #             #                                    self.pixels_in_mm * (y - self.snap_height_half),
        #             #                                    self.pixels_in_mm * (x + self.snap_width_half),
        #             #                                    self.pixels_in_mm * (y + self.snap_height_half))
        #             # self.lbl_img.setPixmap(self.micros_controller.numpy_to_pixmap(snap))
        #             # self.lbl_img.repaint()
        #             cv2.imwrite(os.path.join(self.dir_for_img, "S_{0}_{1}.jpg".format(j, i)), snap[:, :, ::-1])
        #             print('x = ' + str(x) + '; y = ' + str(y))
        #             i -= 1
        #     else:
        #         i = 0
        #         for x in range(x1, x2 + 1, self.snap_width):
        #             i += 1
        #             snap = self.coord_move([x, y, self.snap_height], mode="discrete")
        #             # snap = self.micros_controller.snap(self.pixels_in_mm * (x - self.snap_width_half),
        #             #                                    self.pixels_in_mm * (y - self.snap_height_half),
        #             #                                    self.pixels_in_mm * (x + self.snap_width_half),
        #             #                                    self.pixels_in_mm * (y + self.snap_height_half))
        #             # self.lbl_img.setPixmap(self.micros_controller.numpy_to_pixmap(snap))
        #             # self.lbl_img.repaint()
        #             cv2.imwrite(os.path.join(self.dir_for_img, "S_{0}_{1}.jpg".format(j, i)), snap[:, :, ::-1])
        #             print('x = ' + str(x) + '; y = ' + str(y))
        #     left_dir = not left_dir
        #     j += d_j

        # Создание файла описания XML
        root = Xml.Element("Root")
        elem_rc = Xml.Element("RowCount")
        elem_rc.text = str(int((y2 - y1) / self.snap_height) + 1)
        root.append(elem_rc)
        elem_cc = Xml.Element("ColCount")
        elem_cc.text = str(int((x2 - x1) / self.snap_width) + 1)
        root.append(elem_cc)
        elem_img = Xml.Element("Image")
        root.append(elem_img)
        img_format = Xml.SubElement(elem_img, "Format")
        img_format.text = "jpg"
        img_size = Xml.SubElement(elem_img, "ImgSize")
        img_size_width = Xml.SubElement(img_size, "Width")
        img_size_width.text = str(int(self.snap_width * self.pixels_in_mm))
        img_size_height = Xml.SubElement(img_size, "Height")
        img_size_height.text = str(int(self.snap_height * self.pixels_in_mm))
        img_con_area = Xml.SubElement(elem_img, "ConnectionArea")
        ica_x = Xml.SubElement(img_con_area, "X")
        ica_x.text = str(0)
        ica_y = Xml.SubElement(img_con_area, "Y")
        ica_y.text = str(0)
        ica_width = Xml.SubElement(img_con_area, "Width")
        ica_width.text = str(int(self.snap_width * self.pixels_in_mm))
        ica_height = Xml.SubElement(img_con_area, "Height")
        ica_height.text = str(int(self.snap_height * self.pixels_in_mm))

        tree = Xml.ElementTree(root)
        with open(self.path_for_xml_file, "w") as f_obj:
            tree.write(self.path_for_xml_file)
        self.btn_save_scan.setEnabled(True)
        QMessageBox.information(self, "Info Dialog", "Сканирование завершено", QMessageBox.Ok, QMessageBox.Ok)
        self.unsaved = True

    # Сохранение изображений в архивный файл
    def save_scan(self):
        if not os.path.exists(self.path_for_xml_file):
            return False
        file_filter = "Microscope scans (*.misc)"
        a = QFileDialog.getSaveFileName(self, "Выберите место сохранения файла", "/",
                                        "All files (*.*);;Microscope scans (*.misc)", file_filter)

        if len(a[0]) > 0:
            ext = os.path.splitext(a[0])
            if ext[1] == ".misc":
                file_name = a[0]
            else:
                file_name = ext[0] + ".misc"
            if os.path.exists(file_name):
                dlg_result = QMessageBox.question(self, "Confirm Dialog",
                                                  "Файл уже существует. " +
                                                  "Хотите его перезаписать?" +
                                                  " Это удалит данные в нем",
                                                  QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if dlg_result == QMessageBox.No:
                    return False
        else:
            return False

        z = zipfile.ZipFile(file_name, 'w')
        for root, dirs, files in os.walk(self.dir_for_img):
            for file in files:
                if file:
                    z.write(os.path.join(self.dir_for_img, file), file, compress_type=zipfile.ZIP_DEFLATED)
        QMessageBox.information(self, "Info Dialog", "Файл сохранен", QMessageBox.Ok, QMessageBox.Ok)
        self.unsaved = False
        return True

    # Обработчики событий формы и ее компонентов
    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress:
            # print("Press " + str(event.key()))
            if event.key() == Qt.Key_Shift:
                self.key_shift_pressed = True
            elif event.key() in self.keyboard_buttons:
                self.keyboard_buttons[event.key()].key_press()
        elif event.type() == QEvent.KeyRelease:
            # print("Release " + str(event.key()))
            if event.key() in self.keyboard_buttons:
                self.keyboard_buttons[event.key()].key_release()
            elif event.key() == Qt.Key_Shift:
                self.key_shift_pressed = False
        return QMainWindow.eventFilter(self, obj, event)

    # def keyPressEvent(self, event):
    #     print(event.key())

    def continuous_move(self):
        while not self.closed:
            if self.continuous_mode:
                # someone_clicked = False
                steps_count = 24
                if self.key_shift_pressed:
                    steps_count = 8
                if self.keyboard_buttons[Qt.Key_W].check_click():
                    self.coord_move([0, steps_count, 0], mode="continuous")
                    # someone_clicked = True
                if self.keyboard_buttons[Qt.Key_D].check_click():
                    self.coord_move([-steps_count, 0, 0], mode="continuous")
                    # someone_clicked = True
                if self.keyboard_buttons[Qt.Key_S].check_click():
                    self.coord_move([0, -steps_count, 0], mode="continuous")
                    # someone_clicked = True
                if self.keyboard_buttons[Qt.Key_A].check_click():
                    self.coord_move([steps_count, 0, 0], mode="continuous")
                    # someone_clicked = True
                if self.keyboard_buttons[Qt.Key_Plus].check_click():
                    self.coord_move([0, 0, steps_count], mode="continuous")
                    # someone_clicked = True
                if self.keyboard_buttons[Qt.Key_Minus].check_click():
                    self.coord_move([0, 0, -steps_count], mode="continuous")
                    # someone_clicked = True
                # if someone_clicked:
                time.sleep(0.001)


# Класс-помощник для отслеживания ручного управления установкой клавишами
class KeyboardButton:
    def __init__(self):
        # Считается ли, что сейчас кнопка нажата (и необходимо выполнять движение установки)
        self.clicked = False
        # Последний полученный сигнал от кнопки был release? Если нет, то последний сигнал был press
        self.released = True
        # Время получения последнего сигнала release
        self.time_released = 0.0

    # Получен сигнал нажатия
    def key_press(self):
        self.clicked = True
        self.released = False
        # print(self.clicked)

    # Получен сигнал отпуска
    def key_release(self):
        self.released = True
        self.time_released = time.time()
        # print(self.clicked)

    # Проверка - нажата ли кнопка и обработка таймера
    def check_click(self):
        if self.clicked:
            if self.released:
                #
                if time.time() - self.time_released > 0.02:
                    self.clicked = False
            else:
                # Слишком длительное отсутствие сигнала press воспринимается, как необходимость остановки
                if time.time() - self.time_released > 1.00:
                    self.clicked = False

        # print(self.clicked)
        return self.clicked


# Класс управления микроскопом (пока тестовая подделка)
class MicrosController:
    def __init__(self):
        self.test_img_path = "/home/andrey/Projects/MicrosController/TEST/MotherBoard.jpg"
        self.test_img = cv2.imread(self.test_img_path)[:, :, ::-1]

    @staticmethod
    def numpy_to_q_image(image):
        q_img = QImage()
        if image.dtype == np.uint8:
            if len(image.shape) == 2:
                channels = 1
                height, width = image.shape
                bytes_per_line = channels * width
                q_img = QImage(
                    image.data, width, height, bytes_per_line, QImage.Format_Indexed8
                )
                q_img.setColorTable([QtGui.qRgb(i, i, i) for i in range(256)])
            elif len(image.shape) == 3:
                if image.shape[2] == 3:
                    height, width, channels = image.shape
                    bytes_per_line = channels * width
                    q_img = QImage(
                        image.data, width, height, bytes_per_line, QImage.Format_RGB888
                    )
                elif image.shape[2] == 4:
                    height, width, channels = image.shape
                    bytes_per_line = channels * width
                    fmt = QImage.Format_ARGB32
                    q_img = QImage(
                        image.data, width, height, bytes_per_line, QImage.Format_ARGB32
                    )
        return q_img

    def numpy_to_pixmap(self, img):
        q_img = self.numpy_to_q_image(img)
        pixmap = QtGui.QPixmap.fromImage(q_img)
        return pixmap

    def snap(self, x1: int, y1: int, x2: int, y2: int):
        time.sleep(0.1)
        # return np.copy(self.test_img[y1:y2, x1:x2, :])
        # Переворачиваем координаты съемки
        y2_r = 6400 - y1
        y1_r = 6400 - y2
        return np.copy(self.test_img[y1_r:y2_r, x1:x2, :])


# Класс, который общается с контроллером станка
# 1. Проверяет наличие сервера
# 2. Запускает сервер на Raspberry pi
# 3. Управляет движениями станка
class TableController:
    def __init__(self, loop, hostname="192.168.42.100", port=8080):
        # Параметры подключения к серверу raspberry pi
        self.hostname = hostname
        self.port = port
        # Текущий статус севрера
        self.server_status = 'uninitialized'
        # Текущий статус станка: работает или нет
        self.operation_status = ''
        self.coord_step = [-1, -1, -1]
        self.coord_mm = [-1, -1, -1]
        self.manual_mode = True
        self.manual_left_count = 0
        self.manual_right_count = 0
        self.loop = loop
        self.thread_server = Thread(target=self.server_start)

        self.steps_in_mm = 80
        self.limits_step = (340 * self.steps_in_mm, 640 * self.steps_in_mm, 70 * self.steps_in_mm)
        # Режим тестирования - без работы с установкой
        self.test: bool
        # self.micros_controller: MicrosController = None
        # self.programSettings: ProgramSettings = None

    def __repr__(self):
        return "coord = " + str(self.coord_mm) + "; server status = " + self.server_status \
               + "; last op status = " + self.operation_status

    async def consumer(self):
        url = f"ws://{self.hostname}:{self.port}"
        async with websockets.connect(url) as web_socket:
            await self.hello(web_socket)

    @staticmethod
    async def hello(web_socket) -> None:
        async for message in web_socket:
            print(message)

    @staticmethod
    async def produce(message: str, host: str, port: int) -> None:
        async with websockets.connect(f"ws://{host}:{port}")as ws:
            await ws.send(message)
            result = await ws.recv()
            return result

    @staticmethod
    def get_request(x_step: int, y_step: int, z_step: int, mode: str):
        data = {
            "x": -x_step,
            "y": y_step,
            "z": z_step,
            "mode": mode  # continuous/discrete/init/check
        }
        data_string = json.dumps(data)
        return data_string

    def result_unpack(self, result):
        result_str = json.loads(result)
        # Переворот по оси Х
        self.coord_step = [self.limits_step[0] - result_str['x'], result_str['y'], result_str['z']]
        self.coord_mm = [int(self.coord_step[0] / self.steps_in_mm),
                         int(self.coord_step[1] / self.steps_in_mm),
                         int(self.coord_step[2] / self.steps_in_mm)]

        self.operation_status = result_str['status']
        self.server_status = result_str['status']

    def coord_init(self):
        if not self.test:
            data = self.get_request(x_step=0, y_step=0, z_step=0, mode="init")
            result = self.loop.run_until_complete(self.produce(message=data, host=self.hostname, port=self.port))
            self.result_unpack(result)
        else:
            self.coord_step = [self.limits_step[0], 0, 0]
            self.coord_mm = [self.limits_step[0] / self.steps_in_mm, 0, 0]
            self.operation_status = 'init'
            self.server_status = 'init'

    def coord_check(self):
        if not self.test:
            # loop = asyncio.get_event_loop()
            data = self.get_request(x_step=0, y_step=0, z_step=0, mode="check")
            result = self.loop.run_until_complete(self.produce(message=data, host=self.hostname, port=self.port))
            self.result_unpack(result)

    # Команда движения установки
    def coord_move(self, coord, mode="discrete"):
        if not self.test:
            if min(self.coord_step) < 0:
                return
            # В режиме точечного перемещения надо передавать миллиметры
            if mode == "discrete":
                dx = coord[0] * self.steps_in_mm - self.coord_step[0]
                dy = coord[1] * self.steps_in_mm - self.coord_step[1]
                dz = coord[2] * self.steps_in_mm - self.coord_step[2]
            # В режиме непрерывного перемещения надо передавать шаги
            else:
                # if mode == "continuous"
                dx = coord[0]
                dy = coord[1]
                dz = coord[2]
            # loop = asyncio.get_event_loop()
            data = self.get_request(x_step=dx, y_step=dy, z_step=dz, mode=mode)
            result = self.loop.run_until_complete(self.produce(message=data, host=self.hostname, port=self.port))
            f = open('test.txt', 'a')
            now = datetime.datetime.now()
            f.write(now.strftime("%d.%m.%Y %H:%M:%S") + "<=" + str(result) + '\r\n')
            self.result_unpack(result)
        else:
            if mode == "discrete":
                self.coord_mm[0] = coord[0]
                self.coord_mm[1] = coord[1]
                self.coord_mm[2] = coord[2]
                self.coord_step[0] = self.coord_mm[0] * self.steps_in_mm
                self.coord_step[1] = self.coord_mm[1] * self.steps_in_mm
                self.coord_step[2] = self.coord_mm[2] * self.steps_in_mm
            else:
                # if mode == "continuous"
                coord[0] = -coord[0]
                for i in range(3):
                    self.coord_step[i] += coord[i]
                    if self.coord_step[i] < 0:
                        self.coord_step[i] = 0
                    if self.coord_step[i] > self.limits_step[i]:
                        self.coord_step[i] = self.limits_step[i]
                    self.coord_mm[i] = self.coord_step[i] / self.steps_in_mm

                # snap = self.micros_controller.snap(self.programSettings.pixels_in_mm * (self.coord_mm[0] -
        #                                                                         self.programSettings.snap_width_half),
        #                                    self.programSettings.pixels_in_mm * (self.coord_mm[1] -
        #                                                                         self.programSettings.snap_height_half),
        #                                    self.programSettings.pixels_in_mm * (self.coord_mm[0] +
        #                                                                         self.programSettings.snap_width_half),
        #                                    self.programSettings.pixels_in_mm * (self.coord_mm[1] +
        #                                                                         self.programSettings.snap_height_half))

        # self.lbl_img.setPixmap(self.micros_controller.numpy_to_pixmap(snap))
        # self.lbl_img.repaint()
        self.operation_status = 'init'
        self.server_status = 'init'

    def server_check(self):
        pass

    def server_start(self):
        # os.system("python3 /home/andrey/Projects/MicrosController/ServerExamples/server.py")
        # shell = Terminal(["python3 /home/andrey/Projects/MicrosController/ServerExamples/server.py"])

        shell = Terminal(["ssh pi@" + self.hostname, "python3 server.py", ])
        shell.run()

    def server_connect(self):
        pass

    def init(self):
        return self.send_json_request("init request")

    # функция отправки json для управления станком
    @staticmethod
    def send_json_request(json_request):
        answer = "ok"
        return answer


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainWindow()
    sys.exit(app.exec_())

# See PyCharm help at https://www.jetbrains.com/help/pycharm/

