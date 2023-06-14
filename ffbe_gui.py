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
        self.device_names = ['initiator', 'terminator', "facebook", "boringstock2", "SM-N950N", "SM-G950N", "SM-A826S", "SM-A826S"]
        self.device_types = ['nox_1920_1080', 'android', 'nox_1280_720', 'android_q2']
        self.device_index_by_name = {'initiator':2, 'terminator':2, 'facebook':0, 'boringstock2':0, 'SM-N950N':1, 'SM-G950N':1, "SM-A826S":3}
        # Connect any signals and slots
        btn_list = self.findChildren(QtWidgets.QPushButton)
        for b in btn_list:
            b.clicked.connect(self.on_button_clicked)

        self.cb_device_type = self.findChild(QObject, 'cb_device_type')
        for t in self.device_types:
            self.cb_device_type.addItem(t)
        self.cb_window_name = self.findChild(QObject, 'cb_window_name')
        for n in self.device_names:
            self.cb_window_name.addItem(n)
        self.le_rep = self.findChild(QLineEdit, 'le_rep')
        self.le_rep.setText("300")
        self.le_players = self.findChild(QLineEdit, 'le_players')
        self.le_players.setText("4")
        self.show()
    def init_msg_boxes(self):
        self.log_list = []
        self.debug_list = []
        self.error_list = []

        self.log_widget = Output_Widget(650,300)
        self.obj_log = self.log_widget.obj_output
        self.log_widget.setWindowTitle("Log")
        self.log_widget.show()
        self.log_widget.move(1500,300)

        self.debug_widget = Output_Widget(1000,600)
        self.obj_debug = self.debug_widget.obj_output
        self.debug_widget.setWindowTitle("Debug")
        self.debug_widget.show()
        self.debug_widget.move(400,0)
        self.debug_widget.showMinimized()

        self.error_widget = Output_Widget()
        self.obj_error = self.debug_widget.obj_output
        self.error_widget.setWindowTitle("Error")
        self.error_widget.show()
        self.error_widget.move(1000,0)
        self.error_widget.showMinimized()
    def init_others(self):
        self.device_initiated = False
        self.move(1100,800)
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
            # except_device_list = ['SM-A826S']
            # if not dn in except_device_list:
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
    def on_button_clicked(self):
        sender_name = self.sender().objectName()
        btn_text = self.sender().text()
        print(f"Btn clicked, sender: {sender_name}, text: {btn_text}")
        found = False
        if (sender_name != 'pb_init') and not self.device_initiated:
            print("Auto initiating")
            self.set_device_name_and_type()
        # Non automatic btns.
        self.set_params()
        if sender_name == 'pb_init':
            self.set_device_name_and_type()
            self.debug("Setting the device name and type")
            found = True
        # Automatic btns.
        else:
            try:
                self.start_automator(sender_name=sender_name, btn_text=btn_text)
                found = True
            except:
                self.error(f"Something Wrong here in on_button_clicked. Btn Clicked: {btn_text}.")
                found = False
        return found
    def start_automator(self, sender_name=None, btn_text=None):
        base_text = btn_text.split(':')[0]
        on_text = base_text + ': on'
        off_text = base_text + ': off'
        job = sender_name.replace('pb_', 'play_')
        print(f"Starting automator. Sender name:{sender_name}, btn_text:{btn_text}, on_text:{on_text}, off_text:{off_text}, job:{job}")
        if 'on' == btn_text.split()[-1]:
            self.automator.stop()
            self.sender().setText(off_text)
        else:
            self.automator = ffbe_automator.Automator()
            self.automator.set_msg_handlers(log=self.log, debug=self.debug, error=self.error)
            self.automator.set_window_and_device(window_name=self.window_name, device_type=self.device_type)
            self.automator.set_job(job=job)
            self.automator.set_user_params(rep_time=self.rep_time, num_of_players=self.num_of_players,
                                           finish_button=self.sender())
            print("Starting automator thread")
            target = self.automator.start_automation
            self.automator_thread = threading.Thread(target=target)
            self.automator_thread.start()
            if 'off' == btn_text.split()[-1]:
                self.sender().setText(on_text)
    def set_params(self):
        self.device_type = self.cb_device_type.currentText()
        self.window_name = self.cb_window_name.currentText()
        self.rep_time = int(self.le_rep.text())
        self.num_of_players = int(self.le_players.text())
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
        self.obj_log.verticalScrollBar().setValue(self.obj_log.verticalScrollBar().maximum())
        self.obj_debug.verticalScrollBar().setValue(self.obj_debug.verticalScrollBar().maximum())
        self.obj_error.verticalScrollBar().setValue(self.obj_debug.verticalScrollBar().maximum())
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