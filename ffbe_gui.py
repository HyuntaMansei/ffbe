import time

import PyQt5.QtWidgets
import win32gui
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
        self.init_ui()
        self.init_msg_boxes()
    def init_ui(self):
        # Load the UI file
        uic.loadUi('ffbe_widget.ui', self)
        # variable settings
        self.device_names = ["facebook", "boringstock2", "SM-N950N"]
        self.device_index_by_name = {'facebook':0, 'boringstock2':0, 'SM-N950N':1}
        self.device_types = ['nox_1920_1080', 'android']
        # Connect any signals and slots
        btn_list = self.findChildren(QtWidgets.QPushButton)
        for b in btn_list:
            b.clicked.connect(self.on_button_clicked)
        self.pb_quest = self.findChild(QtWidgets.QPushButton, 'pb_quest')
        self.pb_multi = self.findChild(QtWidgets.QPushButton, 'pb_multi')
        self.pb_summon = self.findChild(QtWidgets.QPushButton, 'pb_summon')

        self.cb_device_type = self.findChild(QComboBox)
        for t in self.device_types:
            self.cb_device_type.addItem(t)
        self.cb_device_type.currentIndexChanged.connect(self.handle_device_type)
        self.le_window_name = self.findChild(QLineEdit, 'le_window_name')
        self.le_rep = self.findChild(QLineEdit, 'le_rep')
        self.le_rep.setText("30")
        self.le_players = self.findChild(QLineEdit, 'le_players')
        self.le_players.setText("1")
        self.show()
    def init_msg_boxes(self):
        self.log_list = []
        self.debug_list = []
        self.error_list = []

        self.log_widget = Output_Widget()
        self.obj_log = self.log_widget.obj_output
        self.log_widget.setWindowTitle("Log")
        self.log_widget.resize(400, 1000)
        self.log_widget.findChild(QObject, 'obj_output').resize(400, 1000)
        self.log_widget.show()

        self.debug_widget = Output_Widget()
        self.obj_debug = self.debug_widget.obj_output
        self.debug_widget.setWindowTitle("Debug")
        self.debug_widget.show()

        self.error_widget = Output_Widget()
        self.obj_error = self.debug_widget.obj_output
        self.error_widget.setWindowTitle("Error")
        self.error_widget.show()
    def event(self, event: QEvent) -> bool:
        # print(f"Handling events, type: {event.type()}, and msgEvent type: {MsgEvent.Type}")
        # if event.eventType() == MsgEvent.Type:
        if event.type() == QEvent.User:
            self.show_msg()
            return True
        else:
            return super().event(event)
    def set_device_name_and_type(self):
        self.device_name = self.find_device_name()
        self.le_window_name.setText(self.device_name)
        self.cb_device_type.setCurrentIndex(self.device_index_by_name[self.device_name])
    def find_device_name(self):
        for dn in self.device_names:
            hwnd = win32gui.FindWindow(None, dn)
            print(f"{dn} : {hwnd}")
            if hwnd > 0:
                return dn
        return None
    def find_device_index_by_name(self, device_name):
        try:
            index = self.device_index_by_name[device_name]
            return index
        except:
            self.error("No such device name in the list")
            return None
    def handle_device_type(self):
        pass
    def on_button_clicked(self):
        sender = self.sender().objectName()
        btn_text = self.sender().text()
        self.set_params()
        print(f"Btn clicked, sender: {sender}, text: {btn_text}")
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
        elif sender == 'pb_summon':
            print(btn_text)
            if 'off' == btn_text.split()[-1]:
                print("AA")
                self.summon_thread = threading.Thread(target=self.start_summon)
                self.summon_thread.start()
                self.sender().setText('Summon: on')
            else:
                print("BB")
                self.summon_automator.stop()
                self.sender().setText('Summon: off')
        else:
            self.debug("wrong operation")
    def set_params(self):
        self.set_device_name_and_type()
        self.device_type = self.cb_device_type.currentText()
        self.window_name = self.le_window_name.text()
        self.rep_time = int(self.le_rep.text())
        self.num_of_players = int(self.le_players.text())
    def start_quest(self):
        self.my_automator = ffbe_automator.Automator(self.window_name, self.device_type, 'play_quest', self.debug, self.log)
        self.my_automator.play_quest(self.rep_time, finish_button=self.pb_quest)
    def start_multi(self):
        print(self.window_name, self.device_type)
        self.my_automator = ffbe_automator.Automator(self.window_name, self.device_type, 'play_multi', debug=self.debug, log=self.log)
        self.my_automator.play_multi(self.rep_time, self.num_of_players, finish_button=self.pb_multi)
    def start_summon(self):
        self.summon_automator = ffbe_automator.Automator(self.window_name, self.device_type, 'summon', debug=self.debug, log=self.log)
        self.summon_automator.summon(self.rep_time, finish_button=self.pb_summon)
    def log(self, msg:str, flag:str=None):
        self.log_list.append(msg)
        msg_event = MsgEvent()
        QCoreApplication.postEvent(self, msg_event)
    def debug(self, msg:str):
        self.debug_list.append(msg)
        msg_event = MsgEvent()
        QCoreApplication.postEvent(self, msg_event)
    def error(self, msg:str):
        print(f"Error occurred: ", msg)
        self.error_list.append(msg)
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
        for m in self.error_list:
            msg += m + '\n'
        self.obj_error.setText(msg)
        self.gui_update()
    def gui_update(self):
        self.obj_log.verticalScrollBar().setValue(self.obj_log.verticalScrollBar().maximum() + 50)
        self.obj_debug.verticalScrollBar().setValue(self.obj_debug.verticalScrollBar().maximum() + 50)
        self.obj_error.verticalScrollBar().setValue(self.obj_debug.verticalScrollBar().maximum() + 50)
class Output_Widget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi('output_gui.ui', self)
if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    widget = MyWidget()
    sys.exit(app.exec_())