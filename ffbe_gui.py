import PyQt6.QtWidgets
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QScrollArea, QLabel, QTextEdit, QComboBox, QLineEdit, QPlainTextEdit, QTextBrowser
from PyQt6.QtCore import Qt
from PyQt6 import QtWidgets, uic
import sys
import ffbe_automator
import threading

class MyWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.log_list = []
        self.debug_list = []

        # Load the UI file
        uic.loadUi('ffbe_widget2.ui', self)

        # Connect any signals and slots
        btn_list = self.findChildren(QtWidgets.QPushButton)
        for b in btn_list:
            b.clicked.connect(self.on_button_clicked)


        self.tb_log = self.findChild(QTextBrowser, 'tb_log')
        self.tb_log.setReadOnly(True)
        self.tb_debug = self.findChild(QTextBrowser, 'tb_debug')
        self.tb_debug.setReadOnly(True)

        self.cb_device_type = self.findChild(QComboBox)
        self.cb_device_type.addItem("nox_1920_1080")
        self.cb_device_type.addItem("android")
        self.cb_device_type.currentIndexChanged.connect(self.handle_device_type)

        self.le_window_name = self.findChild(QLineEdit, 'le_window_name')
        self.le_window_name.setText("facebook")
        # self.le_window_name.setText("hyuntamansei")
        # self.le_window_name.setText("SM-N950N")
        self.le_rep = self.findChild(QLineEdit, 'le_rep')
        self.le_rep.setText("20")
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
        self.my_automator = ffbe_automator.Automator(self.window_name, self.device_type, 'play_multi', self.debug, self.log)
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
            self.tb_log.append(msg)
            self.tb_log.verticalScrollBar().setValue(self.tb_log.verticalScrollBar().maximum() + 50)
            self.tb_log.update()
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
            self.tb_debug.append(msg)
            # text = self.tb_debug.toPlainText() + msg + '\n'
            # self.tb_debug.setText(text)
            self.tb_debug.verticalScrollBar().setValue(self.tb_debug.verticalScrollBar().maximum() + 200)
            self.tb_debug.update()

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    widget = MyWidget()
    sys.exit(app.exec())
    # sys.exit(app.exec_())