import PyQt5
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QVBoxLayout, QWidget
from PyQt5.uic import loadUi
from PyQt5.QtCore import Qt

class MyWindow(QWidget):
    def __init__(self):
        super().__init__()
        loadUi("test_gui.ui", self)
        self.obj_pb1.clicked.connect(self.btn_clicked)
    def btn_clicked(self):
        msg = (self.obj_input.text())
        self.obj_output.append(msg)
        # self.obj_output.setText(msg)

if __name__ == '__main__':
    app = QApplication([])
    window = MyWindow()
    window.show()
    app.exec_()


