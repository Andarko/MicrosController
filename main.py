# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

import asyncio
import time

import pygame
import websockets
import logging
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QSizePolicy
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QGridLayout
from PyQt5.QtWidgets import QAction, QInputDialog, QLineEdit, QLabel, QPushButton, QTextEdit, QFormLayout
from PyQt5.QtCore import QEvent, Qt
import sys
import keyboard
import datetime
import os

from PyQt5 import QtGui
from vassal import Terminal
from threading import Thread
import json
import math
from pynput.keyboard import Key, Listener


# Класс главного окна
class MainWindow(QMainWindow):
    # Инициализация
    def __init__(self):
        super().__init__()
        # self.micros_controller = MicrosController('localhost', 5001)
        self.loop = asyncio.get_event_loop()
        self.micros_controller = MicrosController(self.loop)
        if not self.micros_controller.thread_server or not self.micros_controller.thread_server.is_alive():
            self.micros_controller.thread_server.start()
        time.sleep(2.0)
        print("server started")
        # self.micros_controller.coord_check()
        self.continuous_mode = False
        self.closed = False
        self.key_shift_pressed = False
        self.keyboard_buttons = {Qt.Key_Up: KeyboardButton(), Qt.Key_Right: KeyboardButton(),
                                 Qt.Key_Down: KeyboardButton(), Qt.Key_Left: KeyboardButton(),
                                 Qt.Key_Plus: KeyboardButton(), Qt.Key_Minus: KeyboardButton() }
        self.thread_continuous = Thread(target=self.continuous_move)
        self.thread_continuous.start()

        # Доступные для взаимодействия компоненты формы
        self.lbl_img = QLabel()
        self.lbl_coord = QLabel("Текущие координаты:")
        self.btn_init = QPushButton("Инициализация")
        self.btn_move = QPushButton("Двигать в ...")
        self.btn_manual = QPushButton("Ручной режим")
        self.edt_border_x1 = QTextEdit()
        self.edt_border_y1 = QTextEdit()
        self.edt_border_x2 = QTextEdit()
        self.edt_border_y2 = QTextEdit()
        self.btn_border = QPushButton("Определить границы")
        self.btn_scan = QPushButton("Новая съемка")

        self.init_ui()

    # Создание элементов формы
    def init_ui(self):

        # keyboard.add_hotkey("Ctrl + 1", lambda: print("Left"))

        # Основное меню
        menu_bar = self.menuBar()
        # Меню "Файл"
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
        right_layout.addWidget(self.btn_scan)

        self.installEventFilter(self)

        self.resize(1280, 720)
        self.move(300, 300)
        self.setMinimumSize(800, 600)

        self.show()

    def closeEvent(self, event):
        self.closed = True

    def device_init(self):
        self.micros_controller.coord_init()
        self.setWindowTitle(str(self.micros_controller))

    def device_check(self):
        self.micros_controller.coord_check()
        self.setWindowTitle(str(self.micros_controller))

    def device_move(self):
        input_dialog = QInputDialog()
        text, ok = input_dialog.getText(self,
                                        "Введите дистанцию в миллиметрах",
                                        "Дистанция:",
                                        QLineEdit.Normal,
                                        str(int(self.micros_controller.coord[0] / 80)) + ';'
                                        + str(int(self.micros_controller.coord[1] / 80)) + ';'
                                        + str(int(self.micros_controller.coord[2] / 80)))

        if ok:
            coord = [80 * int(item) for item in text.split(';')]
            self.micros_controller.coord_move(coord)
            self.setWindowTitle(str(self.micros_controller))

    def device_manual(self, status):
        self.continuous_mode = status
        self.control_elements_enabled(not status)

    def control_elements_enabled(self, status):
        self.btn_init.setEnabled(status)
        self.btn_move.setEnabled(status)
        self.btn_border.setEnabled(status)
        self.btn_scan.setEnabled(status)

    # Тестовая функция для рисования круга и спирали
    def test_circle(self):
        self.micros_controller.coord_check()
        count = 200
        r = 0.0
        # r = 20
        for i in range(20*count + 1):
            r += 1 / 10
            alfa = (i / count) * 2 * math.pi
            dx = int(r * math.sin(alfa))
            dy = int(r * math.cos(alfa))
            self.micros_controller.coord_move([dx, dy, 0], mode='continuous')

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

    # Обработчики событий формы и ее компонентов
    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Shift:
                self.key_shift_pressed = True
            elif event.key() in self.keyboard_buttons:
                self.keyboard_buttons[event.key()].key_press()
        elif event.type() == QEvent.KeyRelease:
            if event.key() in self.keyboard_buttons:
                self.keyboard_buttons[event.key()].key_release()
            elif event.key() == Qt.Key_Shift:
                self.key_shift_pressed = False
        return QMainWindow.eventFilter(self, obj, event)

    def continuous_move(self):
        while not self.closed:
            if self.continuous_mode:
                # someone_clicked = False
                steps_count = 24
                if self.key_shift_pressed:
                    steps_count = 8
                if self.keyboard_buttons[Qt.Key_Up].check_click():
                    self.micros_controller.coord_move([0, steps_count, 0], mode="continuous")
                    # someone_clicked = True
                if self.keyboard_buttons[Qt.Key_Right].check_click():
                    self.micros_controller.coord_move([steps_count, 0, 0], mode="continuous")
                    # someone_clicked = True
                if self.keyboard_buttons[Qt.Key_Down].check_click():
                    self.micros_controller.coord_move([0, -steps_count, 0], mode="continuous")
                    # someone_clicked = True
                if self.keyboard_buttons[Qt.Key_Left].check_click():
                    self.micros_controller.coord_move([-steps_count, 0, 0], mode="continuous")
                    # someone_clicked = True
                if self.keyboard_buttons[Qt.Key_Plus].check_click():
                    self.micros_controller.coord_move([0, 0, steps_count], mode="continuous")
                    # someone_clicked = True
                if self.keyboard_buttons[Qt.Key_Minus].check_click():
                    self.micros_controller.coord_move([0, 0, -steps_count], mode="continuous")
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
        print(self.clicked)

    # Получен сигнал отпуска
    def key_release(self):
        self.released = True
        self.time_released = time.time()
        print(self.clicked)

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


# Класс, который общается с контроллером станка
# 1. Проверяет наличие сервера
# 2. Запускает сервер на Raspberry pi
# 3. Управляет движениями станка
class MicrosController:
    def __init__(self, loop, hostname="192.168.42.100", port=8080):
        # Параметры подключения к серверу raspberry pi
        self.hostname = hostname
        self.port = port
        # Текущий статус севрера
        self.server_status = 'uninit'
        # Текущий статус станка: работает или нет
        self.operation_status = ''
        self.coord = [-1, -1, -1]
        self.manual_mode = True
        self.manual_left_count = 0
        self.manual_right_count = 0
        self.loop = loop
        self.thread_server = Thread(target=self.server_start)

    def __repr__(self):
        return "coord = " + str(self.coord) + "; server status = " + self.server_status \
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
            "x": x_step,
            "y": y_step,
            "z": z_step,
            "mode": mode  # continuous/discret/init/check
        }

        data_string = json.dumps(data)
        return data_string

    def result_unpack(self, result):
        result_str = json.loads(result)
        self.coord = [result_str['x'], result_str['y'], result_str['z']]
        self.operation_status = result_str['status']
        self.server_status = result_str['status']

    def coord_init(self):
        # loop = asyncio.get_event_loop()
        data = self.get_request(x_step=0, y_step=0, z_step=0, mode="init")
        result = self.loop.run_until_complete(self.produce(message=data, host=self.hostname, port=self.port))
        self.result_unpack(result)

    def coord_check(self):
        # loop = asyncio.get_event_loop()
        data = self.get_request(x_step=0, y_step=0, z_step=0, mode="check")
        result = self.loop.run_until_complete(self.produce(message=data, host=self.hostname, port=self.port))
        self.result_unpack(result)

    def coord_move(self, coord, mode="discret"):
        if mode == "discret" and min(self.coord) >= 0:
            dx = coord[0] - self.coord[0]
            dy = coord[1] - self.coord[1]
            dz = coord[2] - self.coord[2]
        elif mode == "continuous":
            dx = coord[0]
            dy = coord[1]
            dz = coord[2]
        # loop = asyncio.get_event_loop()
        data = self.get_request(x_step=dx, y_step=dy, z_step=dz, mode=mode)

        result = self.loop.run_until_complete(self.produce(message=data, host=self.hostname, port=self.port))
        print("<=" + str(result))
        self.result_unpack(result)

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


def print_hi(name):
    # Use a breakpoint in the code line below to debug your script.
    print(f'Hi, {name}')  # Press Ctrl+F8 to toggle the breakpoint.


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainWindow()
    sys.exit(app.exec_())

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
