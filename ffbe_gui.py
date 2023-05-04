import PyQt5.QtWidgets
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QScrollArea, QLabel, QTextEdit, QComboBox, QLineEdit, QPlainTextEdit, QTextBrowser
from PyQt5.QtCore import Qt, QObject
from PyQt5 import QtWidgets, uic
import sys
import ffbe_automator
import threading

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

        self.obj_log = self.findChild(QObject, 'obj_log')
        self.obj_debug = self.findChild(QObject, 'obj_debug')

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
        self.le_rep.setText("50")
        self.le_players = self.findChild(QLineEdit, 'le_players')
        self.le_players.setText("1")

        self.show()

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
            self.update()
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
        print(self.debug)
        self.my_automator = ffbe_automator.Automator(self.window_name, self.device_type, 'play_multi', debug=self.debug,log=self.log)
        self.my_automator.play_multi(self.rep_time, self.num_of_players)
    def log(self, msg:str, flag:str=None):
        write = False
        if flag == None:
            write = True
        elif (flag.lower() == "error") or (flag.lower() == 'e'):
            if not msg in self.log_list:
                write = True
        else:
            pass
        if write == True:
            self.log_list.append(msg)
            self.obj_log.append(msg)
            self.obj_log.verticalScrollBar().setValue(self.obj_log.verticalScrollBar().maximum() + 50)
            self.obj_log.update()
    def debug(self, msg:str, flag:str=None):
        write = False
        if flag == None:
            write = True
        elif (flag.lower() == "error") or (flag.lower() == 'e'):
            if not msg in self.debug_list:
                write = True
        else:
            pass
        if write == True:
            self.debug_list.append(msg)
            self.obj_debug.append(msg)
            # self.obj_debug.append(msg.strip())

            # self.te_debug.append(msg)
            # text = self.te_debug.toPlainText() + msg + '\n'
            # self.te_debug.setText(text)
            # self.obj_debug.verticalScrollBar().setValue(self.obj_debug.verticalScrollBar().maximum() + 200)
            # self.obj_debug.update()
    def update(self):
        # self.obj_log.verticalScrollBar().setValue(self.obj_log.verticalScrollBar().maximum() + 50)
        # self.obj_log.update()
        # self.obj_debug.verticalScrollBar().setValue(self.obj_debug.verticalScrollBar().maximum() + 200)
        # self.obj_debug.update()
        pass
if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    widget = MyWidget()
    # sys.exit(app.exec())
    sys.exit(app.exec_())