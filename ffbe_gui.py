import time

import PyQt5.QtWidgets
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QScrollArea, QLabel, QTextEdit, QComboBox, QLineEdit, QPlainTextEdit, QTextBrowser
from PyQt5.QtCore import Qt, QObject, QEvent, QCoreApplication
from PyQt5 import QtWidgets, uic
import sys
import ffbe_automator
import threading

class MsgEvent(QEvent):
    def __init__(self):
        super().__init__(QEvent.User)
class MyWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.log_list = []
        self.debug_list = []

        # Load the UI file
        uic.loadUi('ffbe_widget.ui', self)

        # Connect any signals and slots
        btn_list = self.findChildren(QtWidgets.QPushButton)
        for b in btn_list:
            b.clicked.connect(self.on_button_clicked)
        self.pb_quest = self.findChild(QtWidgets.QPushButton, 'pb_quest')
        self.pb_multi = self.findChild(QtWidgets.QPushButton, 'pb_multi')

        # self.obj_log = self.findChild(QObject, 'obj_log')
        # self.obj_debug = self.findChild(QObject, 'obj_debug')

        self.cb_device_type = self.findChild(QComboBox)
        self.cb_device_type.addItem("nox_1920_1080")
        self.cb_device_type.addItem("android")
        self.cb_device_type.setCurrentIndex(0)
        self.cb_device_type.currentIndexChanged.connect(self.handle_device_type)

        self.le_window_name = self.findChild(QLineEdit, 'le_window_name')
        self.le_window_name.setText("facebook")
        # self.le_window_name.setText("hyuntamansei")
        # self.le_window_name.setText("SM-N950N")
        self.le_rep = self.findChild(QLineEdit, 'le_rep')
        self.le_rep.setText("30")
        self.le_players = self.findChild(QLineEdit, 'le_players')
        self.le_players.setText("1")

        self.show()

        self.log_widget = Output_Widget()
        self.obj_log = self.log_widget.obj_output
        self.log_widget.setWindowTitle("Log")
        self.log_widget.show()

        self.debug_widget = Output_Widget()
        self.obj_debug = self.debug_widget.obj_output
        self.debug_widget.setWindowTitle("Debug")
        self.debug_widget.show()

        self.debug_flag = False
        # self.thread_loop = threading.Thread(target=self.startLoop)
        # self.thread_loop.start()
    def event(self, event: QEvent) -> bool:
        # print(f"Handling events, type: {event.type()}, and msgEvent type: {MsgEvent.Type}")
        # if event.eventType() == MsgEvent.Type:
        if event.type() == QEvent.User:
            self.show_msg()
            # print("User Event")
            return True
        else:
            return super().event(event)
    def startLoop(self):
        while True:
            self.show_msg()
            time.sleep(0.5)
    def handle_device_type(self):
        cb_text = self.cb_device_type.currentText()
        if cb_text == 'android':
            self.le_window_name.setText("SM-N950N")
    def on_button_clicked(self):
        sender = self.sender().objectName()
        btn_text = self.sender().text()
        self.set_params()
        if sender == 'pb_quest':
            if not 'on' in btn_text:
                self.quest_thread = threading.Thread(target=self.start_quest)
                self.quest_thread.start()
                self.sender().setText('Quest: on')
            else:
                try:
                    self.my_automator.stop()
                finally:
                    self.sender().setText('Quest: off')
        elif sender == 'pb_multi':
            if not 'on' in btn_text:
                self.multi_thread = threading.Thread(target=self.start_multi)
                self.multi_thread.start()
                self.sender().setText('Multi: on')
            else:
                try:
                    self.my_automator.stop()
                finally:
                    self.sender().setText('Multi: off')
        elif sender == 'pb_update':
            self.gui_update()
        else:
            self.debug("wrong operation")

    def set_params(self):
        self.device_type = self.cb_device_type.currentText()
        self.window_name = self.le_window_name.text()
        self.rep_time = int(self.le_rep.text())
        self.num_of_players = int(self.le_players.text())

    def start_quest(self):
        self.my_automator = ffbe_automator.Automator(self.window_name, self.device_type, 'play_quest', self.debug, self.log)
        self.my_automator.play_quest(self.rep_time)
    def start_multi(self):
        self.log("Startig multi automation")
        self.my_automator = ffbe_automator.Automator(self.window_name, self.device_type, 'play_multi', debug=self.debug, log=self.log)
        self.my_automator.play_multi(self.rep_time, self.num_of_players)
    def log(self, msg:str, flag:str=None):
        self.log_list.append(msg)
        msg_event = MsgEvent()
        QCoreApplication.postEvent(self, msg_event)
    def debug(self, msg:str):
        self.debug_list.append(msg)
        msg_event = MsgEvent()
        QCoreApplication.postEvent(self, msg_event)
    def show_msg(self):
        msg = ''
        for m in self.debug_list:
            msg += m + '\n'
        self.obj_debug.setText(msg)
        msg = ''
        for m in self.log_list:
            msg += m + '\n'
        self.obj_log.setText(msg)
        self.gui_update()
    def gui_update(self):
        self.obj_log.verticalScrollBar().setValue(self.obj_log.verticalScrollBar().maximum() + 50)
        self.obj_debug.verticalScrollBar().setValue(self.obj_debug.verticalScrollBar().maximum() + 50)
        pass
class Output_Widget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi('output_gui.ui', self)

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    widget = MyWidget()
    # sys.exit(app.exec())
    sys.exit(app.exec_())