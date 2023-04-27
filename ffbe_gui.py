import PyQt5.QtWidgets
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QScrollArea, QLabel, QTextEdit, QComboBox, QLineEdit
from PyQt5.QtCore import Qt
from PyQt5 import QtWidgets, uic
import sys
import ffbe_automator
import threading

class MyWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        # Load the UI file
        uic.loadUi('ffbe_widget.ui', self)

        # Connect any signals and slots
        btn_list = self.findChildren(QtWidgets.QPushButton)
        for b in btn_list:
            b.clicked.connect(self.on_button_clicked)

        self.te_log = QTextEdit()
        self.te_log.setReadOnly(True)
        self.te_debug = QTextEdit()
        self.te_debug.setReadOnly(True)

        self.sa_log = self.findChild(QScrollArea, 'sa_log')
        self.sa_log.setWidget(self.te_log)
        self.sa_debug = self.findChild(QScrollArea, 'sa_debug')
        self.sa_debug.setWidget(self.te_debug)

        self.cb_device_type = self.findChild(QComboBox)
        self.cb_device_type.addItem("nox_1920_1080")
        self.cb_device_type.addItem("android")

        self.le_window_name = self.findChild(QLineEdit, 'le_window_name')
        self.le_window_name.setText("facebook")
        # self.le_window_name.setText("hyuntamansei")
        self.le_rep = self.findChild(QLineEdit, 'le_rep')
        self.le_rep.setText("20")
        self.le_players = self.findChild(QLineEdit, 'le_players')
        self.le_players.setText("1")

        self.show()

    def on_button_clicked(self):
        sender = self.sender().objectName()
        btn_text = self.sender().text()
        self.set_params()
        msg = []
        if sender == 'pb_quest':
            if not 'on' in btn_text:
                self.quest_thread = threading.Thread(target=self.start_quest)
                self.quest_thread.start()
                self.sender().setText('Quest: on')
            else:
                try:
                    self.my_automator.running = False
                    # self.quest_thread._stop()
                # self.quest_thread._delete()
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
                    # self.multi_thread._stop()
                # self.multi_thread._delete()
                finally:
                    self.sender().setText('Multi: off')
        else:
            msg.append("wrong operation")
        for m in msg:
            self.te_log.append(m)
            self.te_debug.append(m)
    # def on_combobox_changed(self, index):
    #     self.set_params(self.cb_device_type.itemText(index))

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

    def debug(self, msg:str):
        self.te_debug.append(msg)
    def log(self, msg:str):
        self.te_log.append(msg)

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    widget = MyWidget()
    sys.exit(app.exec_())