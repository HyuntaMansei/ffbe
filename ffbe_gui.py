import win32gui
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QScrollArea, QLabel, QTextEdit, QComboBox, QLineEdit, QPlainTextEdit, QTextBrowser, QSizePolicy
from PyQt5.QtCore import Qt, QObject, QEvent, QCoreApplication
from PyQt5 import QtWidgets, uic
import sys
import ffbe_automator
import threading
import pygetwindow as gw
from ppadb.client import Client as AdbClient
class MsgEvent(QEvent):
    def __init__(self):
        super().__init__(QEvent.User)
class MyWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.init_arguments()
        self.init_preparation()
        self.init_ui()
        self.init_device_list()
        self.init_msg_boxes()
        self.init_others()

    def init_arguments(self):
        self.arguments = sys.argv[1:]
        try:
            self.initial_x = int(self.arguments[0])
            self.initial_y = int(self.arguments[1])
        except:
            self.initial_x = 200
            self.initial_y = 800
    def init_preparation(self):
        # variable settings
        self.device_names = ['initiator', 'terminator', "facebook", "boringstock2", "SM-N950N", "SM-G950N", "SM-A826S", "SM-A826S"]
        self.device_types = ['nox_1920_1080', 'android', 'nox_1280_720', 'android_q2']
        self.device_index_by_name = {'initiator':2, 'terminator':2, 'facebook':0, 'boringstock2':0, 'SM-N950N':1, 'SM-G950N':1, "SM-A826S":3}

    def init_device_list(self):
        self.connected_device_name_and_handle = [] #(name, hwnd)
        self.connected_device_name_and_serial = [] #(name, serial, device)
        windows = gw.getAllWindows()
        for window in windows:
            # print(f"HWND: {window._hWnd} and Window Name: {window.title}")
            if window.title in self.device_names:
                self.connected_device_name_and_handle.append((window.title, window._hWnd))
        print("Connected Devices: ", self.connected_device_name_and_handle)
        # Connect to the ADB server
        adb = AdbClient(host="127.0.0.1", port=5037)
        # Get the device list
        devices = adb.devices()
        # Print the serial numbers and names of connected devices
        for device in devices:
            device_name = device.shell("getprop ro.product.model").strip()
            self.connected_device_name_and_serial.append((device_name, device.serial, device))
        print("Connected Devices(name and serial): ",self.connected_device_name_and_serial)
        self.cb_device_type.clear()
        self.cb_device_serial.clear()
        self.cb_window_name.clear()
        self.cb_window_hwnd.clear()
        for t in self.device_types:
            self.cb_device_type.addItem(t)
        for nh in self.connected_device_name_and_handle:
            self.cb_window_name.addItem(nh[0])
            self.cb_window_hwnd.addItem(str(nh[1]))
        for ns in self.connected_device_name_and_serial:
            self.cb_device_serial.addItem(ns[1])
    def init_ui(self):
        # Load the UI file
        uic.loadUi('ffbe_widget.ui', self)
        # Connect any signals and slots
        btn_list = self.findChildren(QtWidgets.QPushButton)
        for b in btn_list:
            b.clicked.connect(self.on_button_clicked)
        # Connect the slot function to the currentTextChanged signal
        self.cb_window_name.currentTextChanged.connect(self.on_cb_window_name_text_changed)
        self.le_rep = self.findChild(QLineEdit, 'le_rep')
        self.le_rep.setText("300")
        self.le_players = self.findChild(QLineEdit, 'le_players')
        self.le_players.setText("4")
        self.le_sleep_multiple.setText("4")
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
        self.log_widget.showMinimized()

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
        print(f"Initial position: {self.initial_x,self.initial_y}")
        self.error_widget.move(self.initial_x,self.initial_y)
        self.error_widget.showMinimized()
    def init_others(self):
        self.device_initiated = False
        self.move(300,800)
    def event(self, event: QEvent) -> bool:
        # print(f"Handling events, type: {event.type()}, and msgEvent type: {MsgEvent.Type}")
        # if event.eventType() == MsgEvent.Type:
        if event.type() == QEvent.User:
            self.show_msg()
            return True
        else:
            return super().event(event)
    def set_device_name_and_type(self):
        self.init_device_list()
        device_name = self.find_device_name()
        self.cb_window_name.setCurrentText(device_name)
        self.device_initiated = True
    def find_device_name(self):
        try:
            return self.connected_device_name_and_handle[0][0]
        except:
            return None
        # for dn in self.device_names:
        #     # except_device_list = ['SM-A826S']
        #     # if not dn in except_device_list:
        #     hwnd = win32gui.FindWindow(None, dn)
        #     print(f"{dn} : {hwnd}")
        #     if hwnd > 0:
        #         return dn
    def get_hwnd_by_name(self, device_name):
        hwnd = None
        for nh in self.connected_device_name_and_handle:
            if nh[0] == device_name:
                hwnd = nh[1]
                break
        print(f"Found hwnd: {hwnd}")
        return hwnd
    def get_serial_by_name(self, device_name):
        serial = None
        for ns in self.connected_device_name_and_serial:
            if ns[0] == device_name:
                serial = ns[1]
                break
        return serial
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
                self.error(f"Something Wrong here in on_button_clicked. Btn Clicked: {btn_text}")
                found = False
        return found
    def on_cb_window_name_text_changed(self, text):
        #hwnd, device_type, serial
        device_name = text
        try:
            self.cb_window_hwnd.setCurrentText(str(self.get_hwnd_by_name(device_name)))
            self.cb_device_type.setCurrentIndex(self.device_index_by_name[device_name])
            self.cb_device_serial.setCurrentText(self.get_serial_by_name(device_name))
        except:
            self.error("Error in on_cb_window_name_text_changed")
        print("Text changed:", text)
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
            self.automator.set_window_and_device(window_name=self.window_name, window_hwnd=self.window_hwnd, device_type=self.device_type, device_serial=self.device_serial)
            self.automator.set_job(job=job)
            self.automator.set_user_params(rep_time=self.rep_time, num_of_players=self.num_of_players,
                                           finish_button=self.sender(), sleep_multiple=self.sleep_multiple)
            print("Starting automator thread")
            target = self.automator.start_automation
            self.automator_thread = threading.Thread(target=target)
            self.automator_thread.start()
            if 'off' == btn_text.split()[-1]:
                self.sender().setText(on_text)
    def set_params(self):
        self.window_name = self.cb_window_name.currentText()
        self.window_hwnd = self.cb_window_hwnd.currentText()
        self.device_type = self.cb_device_type.currentText()
        self.device_serial = self.cb_device_serial.currentText()
        print(f"Setting parameters: ", self.window_name, self.window_hwnd, self.device_type, self.device_serial)
        self.rep_time = int(self.le_rep.text())
        self.num_of_players = int(self.le_players.text())
        self.sleep_multiple = int(self.le_sleep_multiple.text())
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