import sys
from PyQt5.QtWidgets import QApplication, QDialog, QPushButton, QVBoxLayout, QFormLayout, QLabel, QLineEdit, QDialogButtonBox, QHBoxLayout, QCheckBox, QRadioButton
from PyQt5.uic import loadUiType
import configparser

# Load the UI file dynamically
UI_PATH = "ffbe_settings.ui"
Ui_SettingsDialog, QDialog = loadUiType(UI_PATH)
class SettingsDialog(QDialog, Ui_SettingsDialog):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
    def test_def(self):
        pass
    def other_init(self):
        self.check_boxes = self.findChildren(QCheckBox)
        self.radio_boxes = self.findChildren(QRadioButton)
        self.load_from_file()
        self.initial_check()
    def load_from_file(self):
        file_path = './macro_settings.txt'
        conf = configparser.ConfigParser()
        conf.read(file_path, encoding='utf-8')
        self.checked_boxes = [s.strip() for s in conf['default']['checked_box'].split('/')]
        print(self.checked_boxes)
        self.checked_rbs = [s.strip() for s in conf['default']['checked_rb'].split('/')]
        print(self.checked_rbs)
    def save_to_file(self):
        str_checked_boxes = '/'.join(self.checked_boxes)
        str_checked_rbs = '/'.join(self.checked_rbs)
        pass
    def initial_check(self):
        print("Initial Checking")
        for c in self.check_boxes:
            if c.text() in self.checked_boxes:
                c.setChecked(True)
                print(f"Checking: {c.text()}")
        for c in self.radio_boxes:
            if c.text() in self.checked_rbs:
                c.setChecked(True)
def show_settings_popup():
    dialog = SettingsDialog()
    dialog.other_init()
    result = dialog.exec_()  # Show the dialog and get the result (Accepted/Rejected)
def main():
    app = QApplication(sys.argv)

    # Create your main window (if any)
    # ...

    button = QPushButton('Open Settings')
    button.clicked.connect(show_settings_popup)
    button.show()

    sys.exit(app.exec_())
if __name__ == '__main__':
    main()