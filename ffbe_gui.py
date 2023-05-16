import time

import PyQt5.QtWidgets
import win32gui
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QScrollArea, QLabel, QTextEdit, QComboBox, QLineEdit, QPlainTextEdit, QTextBrowser, QSizePolicy
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
        self.init_others()
    def init_ui(self):
        # Load the UI file
        uic.loadUi('ffbe_widget.ui', self)
        # variable settings
        self.device_names = ["facebook", "boringstock2", "SM-N950N", "SM-G950N"]
        self.device_index_by_name = {'facebook':0, 'boringstock2':0, 'SM-N950N':1, 'SM-G950N':1}
        self.device_types = ['nox_1920_1080', 'android']
        # Connect any signals and slots
        btn_list = self.findChildren(QtWidgets.QPushButton)
        for b in btn_list:
            b.clicked.connect(self.on_button_clicked)
        self.pb_init = self.findChild(QtWidgets.QPushButton, 'pb_init')
        self.pb_quest = self.findChild(QtWidgets.QPushButton, 'pb_quest')
        self.pb_multi = self.findChild(QtWidgets.QPushButton, 'pb_multi')
        self.pb_summon = self.findChild(QtWidgets.QPushButton, 'pb_summon')
        self.pb_raid = self.findChild(QtWidgets.QPushButton, 'pb_raid')
        self.pb_multi_client = self.findChild(QtWidgets.QPushButton, 'pb_multi_client')

        self.cb_device_type = self.findChild(QObject, 'cb_device_type')
        for t in self.device_types:
            self.cb_device_type.addItem(t)
        # self.cb_device_type.currentIndexChanged.connect(self.handle_device_type)
        self.cb_window_name = self.findChild(QObject, 'cb_window_name')
        for n in self.device_names:
            self.cb_window_name.addItem(n)
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
        self.log_widget.show()
        self.log_widget.move(0,0)

        self.debug_widget = Output_Widget(600,600)
        self.obj_debug = self.debug_widget.obj_output
        self.debug_widget.setWindowTitle("Debug")
        self.debug_widget.show()
        self.debug_widget.move(400,0)

        self.error_widget = Output_Widget()
        self.obj_error = self.debug_widget.obj_output
        self.error_widget.setWindowTitle("Error")
        self.error_widget.show()
        self.error_widget.move(1000,0)
    def init_others(self):
        self.device_initiated = False
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
        self.cb_window_name.setCurrentText(self.device_name)
        self.cb_device_type.setCurrentIndex(self.device_index_by_name[self.device_name])
        self.device_initiated = True
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
        print(f"Btn clicked, sender: {sender}, text: {btn_text}")
        if (sender != 'pb_init') and not self.device_initiated:
            print("Auto initiating")
            self.set_device_name_and_type()
        self.set_params()
        if sender == 'pb_init':
            self.set_device_name_and_type()
            self.debug("Setting the device name and type")
        elif sender == 'pb_quest':
            if not 'on' in btn_text:
                self.quest_thread = threading.Thread(target=self.start_quest)
                self.quest_thread.start()
                self.sender().setText('Quest: on')
            else:
                try:
                    self.automator.stop()
                finally:
                    self.sender().setText('Quest: off')
        elif sender == 'pb_multi':
            if not 'on' in btn_text:
                self.multi_thread = threading.Thread(target=self.start_multi)
                self.multi_thread.start()
                self.sender().setText('Multi: on')
            else:
                try:
                    self.automator.stop()
                finally:
                    self.sender().setText('Multi: off')
        elif sender == 'pb_multi_client':
            if not 'on' in btn_text:
                self.multi_client_thread = threading.Thread(target=self.start_multi_client)
                self.multi_client_thread.start()
                self.sender().setText('Multi(c): on')
            else:
                try:
                    self.automator.stop()
                finally:
                    self.sender().setText('Multi(c): off')
        elif sender == 'pb_update':
            self.gui_update()
        elif sender == 'pb_summon':
            if 'off' == btn_text.split()[-1]:
                self.summon_thread = threading.Thread(target=self.start_summon)
                self.summon_thread.start()
                self.sender().setText('Summon: on')
            else:
                self.automator.stop()
                self.sender().setText('Summon: off')
        elif sender == 'pb_raid':
            if 'off' == btn_text.split()[-1]:
                self.raid_thread = threading.Thread(target=self.start_raid)
                self.raid_thread.start()
                self.sender().setText('Raid: on')
            else:
                self.automator.stop()
                self.sender().setText('Raid: off')
        elif sender == 'pb_raid_host2':
            self.pb_raid_host2_clicked(sender, btn_text)
        elif sender == 'pb_raid_host4':
            self.pb_raid_host4_clicked(sender, btn_text)
        elif sender == 'pb_raid_client':
            self.pb_raid_host2_clicked(sender, btn_text)
        else:
            self.debug("wrong operation")
    def pb_raid_host2_clicked(self, sender, btn_text):
        if 'off' == btn_text.split()[-1]:
            self.automator_thread = threading.Thread(target=self.start_raid_client)
            self.automator_thread.start()
            self.sender().setText('R host2: on')
        else:
            self.automator.stop()
            self.sender().setText('R host2: off')
    def pb_raid_host4_clicked(self, sender, btn_text):
        target=self.start_raid_host4
        if 'off' == btn_text.split()[-1]:
            print("aa")
            self.automator_thread = threading.Thread(target=target)
            self.automator_thread.start()
            self.sender().setText('R host4: on')
        else:
            print("bb")
            self.automator.stop()
            self.sender().setText('R host4: off')
    def set_params(self):
        self.device_type = self.cb_device_type.currentText()
        self.window_name = self.cb_window_name.currentText()
        self.rep_time = int(self.le_rep.text())
        self.num_of_players = int(self.le_players.text())
    def start_quest(self):
        self.automator = ffbe_automator.Automator(self.window_name, self.device_type, 'play_quest', self.debug, self.log)
        self.automator.play_quest(self.rep_time, finish_button=self.pb_quest)
    def start_multi(self):
        print(self.window_name, self.device_type)
        self.automator = ffbe_automator.Automator(self.window_name, self.device_type, 'play_multi', debug=self.debug, log=self.log)
        self.automator.play_multi(self.rep_time, self.num_of_players, finish_button=self.pb_multi)
    def start_multi_client(self):
        print(self.window_name, self.device_type)
        self.automator = ffbe_automator.Automator(self.window_name, self.device_type, 'play_multi_client', debug=self.debug, log=self.log)
        self.automator.play_multi_client(self.rep_time, finish_button=self.pb_multi_client)
    def start_summon(self):
        self.automator = ffbe_automator.Automator(self.window_name, self.device_type, 'summon', debug=self.debug, log=self.log)
        self.automator.summon(self.rep_time, finish_button=self.pb_summon)
    def start_raid(self):
        self.automator = ffbe_automator.Automator(self.window_name, self.device_type, 'play_raid', debug=self.debug, log=self.log)
        self.automator.play_raid(self.rep_time, self.num_of_players, finish_button=self.pb_raid)
    def start_raid_host2(self):
        self.automator = ffbe_automator.Automator(self.window_name, device_type=self.device_type, debug=self.debug, log=self.log)
        self.automator.play_raid(self.rep_time, self.num_of_players, finish_button=self.pb_raid_host2)
    def start_raid_host4(self):
        finish_button = self.pb_raid_host4
        job = "play_raid_host4"
        self.automator = ffbe_automator.Automator(self.window_name, device_type=self.device_type, debug=self.debug, log=self.log)
        self.automator.set_user_param(rep_time=self.rep_time, num_of_players=self.num_of_players, finish_button=finish_button)
        self.automator.start_automation(job=job)
    def start_raid_client(self):
        finish_button = self.pb_raid_client
        job = "play_raid_client"
        self.automator = ffbe_automator.Automator(self.window_name, device_type=self.device_type, debug=self.debug, log=self.log)
        self.automator.set_user_param(rep_time=self.rep_time, num_of_players=self.num_of_players, finish_button=finish_button)
        self.automator.start_automation(job=job)
    def log(self, msg:str):
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
        for m in self.log_list:
            msg += m + '\n'
        self.obj_log.setText(msg)
        msg = ''
        for m in self.debug_list:
            msg += m + '\n'
        self.obj_debug.setText(msg)
        for m in self.error_list:
            msg += m + '\n'
        self.obj_error.setText(msg)
        self.gui_update()
    def gui_update(self):
        self.obj_log.verticalScrollBar().setValue(self.obj_log.verticalScrollBar().maximum() + 50)
        self.obj_debug.verticalScrollBar().setValue(self.obj_debug.verticalScrollBar().maximum() + 50)
        self.obj_error.verticalScrollBar().setValue(self.obj_debug.verticalScrollBar().maximum() + 50)
class Output_Widget(QtWidgets.QWidget):
    def __init__(self, width=400, height=400):
        super().__init__()
        # uic.loadUi('output_gui.ui', self)
        layout = QVBoxLayout(self)
        self.obj_output = QTextBrowser()
        self.obj_output.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.obj_output)
        self.obj_output.setMinimumSize(width, height)
        font = QFont('Arial', 14)
        font.setWeight(QFont.Bold)
        self.obj_output.setFont(font)
if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    widget = MyWidget()
    sys.exit(app.exec_())