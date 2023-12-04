import sys
from PyQt5.QtWidgets import QApplication, QDialog, QPushButton, QVBoxLayout, QFormLayout, QLabel, QLineEdit, QDialogButtonBox, QHBoxLayout, QCheckBox, QRadioButton, QDesktopWidget, QGridLayout, QTabWidget
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
        self.section_name = None
        self.conf = None
        self.tabs = None
        self.tab_names = []
        self.gridLayout = {}
        self.check_boxes = {}
        self.radio_boxes = {}
        self.checked_cbs = {}
        self.checked_rbs = {}
        self.selected_party = None

    def test_def(self):
        pass
    def print_objects_in_layout(self, layout):
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item is not None:
                widget = item.widget()
                if widget is not None:
                    print(f"Widget name: {widget.objectName()}, Widget type: {type(widget).__name__}")
    def find_objects_in_layout(self, layout, object_type=None):
        objs = []
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item is not None:
                widget = item.widget()
                if widget is not None:
                    if object_type:
                        if isinstance(widget, object_type):
                            objs.append(widget)
                    else:
                        objs.append(widget)
                    # print(f"Widget name: {widget.objectName()}, Widget type: {type(widget).__name__}")
        return objs
    def initUi(self, serial=None):
        self.section_name = serial
        print(f"Sectin Name: {serial}")
        self.tab_names = ["DW", "PQDP"]
        self.gridLayout['DW'] = self.findChild(QGridLayout, 'gridLayout_DW')
        self.gridLayout['PQDP'] = self.findChild(QGridLayout, 'gridLayout_PQDP')
        self.check_boxes['DW'] = self.find_objects_in_layout(self.gridLayout['DW'], QCheckBox)
        self.radio_boxes['DW'] = self.find_objects_in_layout(self.gridLayout['DW'], QRadioButton)
        self.check_boxes['PQDP'] = self.find_objects_in_layout(self.gridLayout['PQDP'], QCheckBox)
        self.radio_boxes['PQDP'] = self.find_objects_in_layout(self.gridLayout['PQDP'], QRadioButton)

        for t in self.tab_names:
            self.checked_cbs[t] = []
            self.checked_rbs[t] = []
        self.load_from_file()
        self.initial_check()
    def load_from_file(self):
        self.conf = configparser.ConfigParser()
        try:
            self.conf.read(self.file_path, encoding='UTF-8')
        except Exception as e:
            print(e)
        section_name = 'DEFAULT'
        if self.section_name in self.conf.sections():
            section_name = self.section_name
        try:
            for t in self.tab_names:
                self.checked_cbs[t] = [s.strip() for s in self.conf[section_name]['checked_cb_'+t].split('/')]
                self.checked_rbs[t] = [s.strip() for s in self.conf[section_name]['checked_rb_'+t].split('/')]
        except Exception as e:
            print(e)
        # print(self.checked_cbs)
        # print(self.checked_rbs)
    def initial_check(self):
        # print("Initial Checking")
        for t in self.tab_names:
            for c in self.check_boxes[t]:
                try:
                    if c.text() in self.checked_cbs[t]:
                        c.setChecked(True)
                except Exception as e:
                    print(e, f" with {c}")
            for r in self.radio_boxes[t]:
                try:
                    if r.text() in self.checked_rbs[t]:
                        r.setChecked(True)
                except Exception as e:
                    print(e, f" with {r}")
        if not (self.rb_pvp_1.isChecked() or self.rb_pvp_5.isChecked()):
            self.rb_pvp_5.setChecked(True)
        if not self.cb_story.isChecked():
            self.cb_story_changed(0)
    def custom_accept(self):
        print("In custom_accept")
        self.checked_cbs = {}
        self.checked_rbs = {}
        for t in self.tab_names:
            self.checked_cbs[t] = []
            self.checked_rbs[t] = []
            for cb in self.check_boxes[t]:
                if cb.isChecked():
                    self.checked_cbs[t].append(cb.text())
            for rb in self.radio_boxes[t]:
                if rb.isChecked():
                    self.checked_rbs[t].append(rb.text())
        print("Checked Box: ", self.checked_cbs)
        print("Checked RadioBtns: ", self.checked_rbs)
        self.save_to_file()
        self.accept()
    def save_to_file(self):
        print("Saving Setting")
        str_checked_cbs = {}
        str_checked_rbs = {}
        section_name = 'DEFAULT'
        print(self.section_name)
        if self.section_name:
            section_name = self.section_name
            if not (section_name in self.conf.sections()):
                self.conf.add_section(section_name)
        print(f"Section Name: {section_name}")
        for t in self.tab_names:
            str_checked_cbs[t] = '/'.join(self.checked_cbs[t])
            str_checked_rbs[t] = '/'.join(self.checked_rbs[t])
            self.conf[section_name]['checked_cb_'+t] = str_checked_cbs[t]
            self.conf[section_name]['checked_rb_'+t] = str_checked_rbs[t]
        print("Saving setting")
        with open(self.file_path, 'w', encoding='UTF-8') as configfile:
            self.conf.write(configfile)
        print("Saving setting")
    def select_all_DW(self):
        for cb in self.check_boxes['DW']:
            cb.setChecked(True)
    def deselect_all_DW(self):
        for cb in self.check_boxes['DW']:
            cb.setChecked(False)
    def select_all_PQDP(self):
        for cb in self.check_boxes['PQDP']:
            cb.setChecked(True)
    def deselect_all_PQDP(self):
        for cb in self.check_boxes['PQDP']:
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
            new_x = int(pos.x() / 2)
            new_y = int((pos.y() / 2)-400)
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
    sd.exec_()
    # print(sd.checked_rbs)
    # print(sd.checked_cbs)
    # print(sd.selected_party)
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()