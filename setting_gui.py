import sys
from PyQt5.QtWidgets import QApplication, QDialog, QPushButton, QVBoxLayout, QFormLayout, QLabel, QLineEdit, QDialogButtonBox, QHBoxLayout, QCheckBox, QRadioButton, QDesktopWidget
from PyQt5.uic import loadUiType
import configparser

# Load the UI file dynamically
UI_PATH = "ffbe_settings.ui"
Ui_SettingsDialog, QDialog = loadUiType(UI_PATH)
class SettingsDialog(QDialog, Ui_SettingsDialog):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.file_path = 'macro_settings.txt'
        self.conf = None
        self.checked_boxes = None
        self.checked_rbs = None
        self.selected_party = None
        self.check_boxes = None
        self.radio_boxes = None
    def test_def(self):
        pass
    def initUi(self):
        self.check_boxes = self.findChildren(QCheckBox)
        self.radio_boxes = self.findChildren(QRadioButton)
        self.load_from_file()
        self.initial_check()
    def load_from_file(self):
        self.conf = configparser.ConfigParser()
        try:
            self.conf.read(self.file_path, encoding='UTF-8')
        except Exception as e:
            print(e)
        # print(self.conf['default']['checked_box'])
        # print(self.conf['default']['checked_rb'])
        self.checked_boxes = []
        self.checked_rbs = []
        try:
            self.checked_boxes = [s.strip() for s in self.conf['default']['checked_box'].split('/')]
            self.checked_rbs = [s.strip() for s in self.conf['default']['checked_rb'].split('/')]
            self.selected_party = [s.strip() for s in self.conf['default']['checked_box'].split('/')]
        except Exception as e:
            print(e)
        # print(self.checked_boxes)
        # print(self.checked_rbs)
    def initial_check(self):
        # print("Initial Checking")
        for c in self.check_boxes:
            if c.text() in self.checked_boxes:
                c.setChecked(True)
                # print(f"Checking: {c.text()}")
        for c in self.radio_boxes:
            if c.text() in self.checked_rbs:
                c.setChecked(True)
        if not self.cb_story.isChecked():
            self.cb_story_changed(0)
    def custom_accept(self):
        self.checked_boxes = []
        self.checked_rbs = []
        for order in self.check_boxes:
            if order.isChecked():
                self.checked_boxes.append(order.text())
        # print("Checked Box: ", self.checked_boxes)
        for rb in self.radio_boxes:
            if rb.isChecked():
                self.checked_rbs.append(rb.text())
        # print("Checked radio_btns: ", self.checked_rbs)
        self.save_to_file()
        self.accept()
    def save_to_file(self):
        str_checked_boxes = '/'.join(self.checked_boxes)
        str_checked_rbs = '/'.join(self.checked_rbs)
        if self.conf.has_section('default'):
            self.conf['default']['checked_box'] = str_checked_boxes
            self.conf['default']['checked_rb'] = str_checked_rbs
        else:
            self.conf.add_section('default')
            self.conf['default']['checked_box'] = str_checked_boxes
            self.conf['default']['checked_rb'] = str_checked_rbs
        with open(self.file_path, 'w', encoding='UTF-8') as configfile:
            self.conf.write(configfile)
    def select_all(self):
        for cb in self.check_boxes:
            cb.setChecked(True)
    def deselect_all(self):
        for cb in self.check_boxes:
            cb.setChecked(False)
    def cb_story_changed(self, state):
        # print(state)
        if not state:
            self.cb_hard_quest.setEnabled(False)
            if not self.cb_another_world.isChecked():
                self.cb_party_name_xp.setEnabled(False)
        else:
            self.cb_hard_quest.setEnabled(True)
            self.cb_party_name_xp.setEnabled(True)
    def cb_another_world_changed(self, state):
        # print(state)
        if not state:
            if not self.cb_story.isChecked():
                self.cb_party_name_xp.setEnabled(False)
        else:
            self.cb_hard_quest.setEnabled(True)
            self.cb_party_name_xp.setEnabled(True)
    def set_position(self, pos):
        desktop = QDesktopWidget()
        # Get the screen size of the primary screen
        primary_screen_size = desktop.screenGeometry()
        print(primary_screen_size.width())
        print(primary_screen_size.height())
        is_4k = True if (primary_screen_size.width() >= 3840) or (primary_screen_size.height() >= 3840) else False
        print(f"moving to pos:{pos.x(), pos.y()}")
        if is_4k:
            new_x = int(pos.x() / 2)
            new_y = int((pos.y() / 2)-400)
            self.move(new_x, new_y)
        else:
            new_x = int(pos.x())
            new_y = int(pos.y()-400)
            self.move(new_x, new_y)
        print(f"moved to pos:{new_x, new_y}")
def show_settings_popup():
    dialog = SettingsDialog()
    dialog.initUi()
    result = dialog.exec_()  # Show the dialog and get the result (Accepted/Rejected)
def main():
    app = QApplication(sys.argv)
    # Create your main window (if any)
    sd = SettingsDialog()
    sd.initUi()
    sd.load_from_file()
    sd.exec_()
    print(sd.checked_rbs)
    print(sd.checked_boxes)
    print(sd.selected_party)
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()