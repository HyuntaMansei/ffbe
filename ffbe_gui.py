import time
import pandas
import win32gui
import win32process
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QScrollArea, QLabel, QTextEdit, QComboBox, QLineEdit, QPlainTextEdit, QTextBrowser, QSizePolicy
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QLineEdit, QInputDialog
from PyQt5.QtCore import Qt, QObject, QEvent, QCoreApplication
from PyQt5 import QtWidgets, uic
from screeninfo import get_monitors
import sys
import ffbe_automator
import threading
import pygetwindow as gw
from ppadb.client import Client as AdbClient
import mysql.connector
import requests
import psutil
import setting_gui
import configparser
import inspect
from typing import Type
import operation_status_checker as osc
def get_window_rect(hwnd):
    rect = win32gui.GetWindowRect(hwnd)
    x, y, width, height = rect
    return x, y, x + width, y + height
def calculate_center_distance(hwnd1, hwnd2):
    # Get window rectangles
    x1, y1, right1, bottom1 = get_window_rect(hwnd1)
    x2, y2, right2, bottom2 = get_window_rect(hwnd2)

    # Calculate center points
    center_x1, center_y1 = (x1 + right1) // 2, (y1 + bottom1) // 2
    center_x2, center_y2 = (x2 + right2) // 2, (y2 + bottom2) // 2

    # Calculate distance between centers
    distance = ((center_x2 - center_x1)**2 + (center_y2 - center_y1)**2)**0.5

    return distance
def config_to_dict(config):
    config_dict = {}
    for section_name in config.sections():
        section_dict = {}
        for key, value in config[section_name].items():
            section_dict[key] = value
        config_dict[section_name] = section_dict
    return config_dict
def get_public_ip():
    try:
        response = requests.get('https://ipinfo.io/json')
        ip_data = response.json()
        public_ip = ip_data['ip']
        return public_ip
    except requests.RequestException:
        return "Unable to get public IP address"
def close_all_apps_backup(device):
    print(f"Closing apps on device: {device.serial}")
    device.shell("am kill-all")
def close_all_apps(device):
    print(f"Closing apps on device: {device.serial}")
    # Get the list of running processes
    processes = device.shell("ps")
    print(processes)
    processes = device.shell("ps").splitlines()
    print(processes)
    # Extract package names from the processes
    package_names = [line.split()[-1] for line in processes if len(line.split()) > 1]
    # Close each app
    for package_name in set(package_names):
        device.shell(f"am force-stop {package_name}")
class MsgEvent(QEvent):
    def __init__(self):
        super().__init__(QEvent.User)
class AutomatorParas:
    def __init__(self):
        self.rep_time = None
        self.num_of_players = None
        self.sleep_multiple = None
        self.operation_option1 = None
        self.operation_option2 = None
        self.test_para = None
    def show_yourself(self):
        print('='*50)
        print(f"rep_time:{self.rep_time}, num_of_players:{self.num_of_players}, sleep_multiple:{self.sleep_multiple}")
        print(f"operation_option1:{self.operation_option1}, operation_option2:{self.operation_option2}, test_para:{self.test_para}")
        print('=' * 50)
class MyWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.macro_version = '0.32'
        self.is_automator_initiated = None
        self.adb_devices = None
        self.my_dev = None
        self.device_names = []
        self.device_types = []
        self.device_index_by_name = {}
        self.window_name = None
        self.window_hwnd = None
        self.device_type = None
        self.device_serial = None
        self.initial_device_name_hint = None
        self.connected_device_name_and_handle = [] #(name, hwnd), name is window title
        self.connected_device_name_and_serial = [] #(name, serial, device)
        # Automator settings
        self.automator_paras = AutomatorParas()
        self.rep_time = None
        self.num_of_players = None
        self.sleep_multiple = None
        self.test_para = None
        self.operation_option1 = None
        self.operation_option2 = None
        self.device_mode = None
        # Widget Objects
        self.setting_dialog = None
        self.operation_status_checker: Type[osc.OperationStatusChecker] = None
        self.automator = None
        self.dic_of_text_lists_for_cb_operation_option = {}
        self.init_arguments()
        self.init_preparation()
        self.init_ui()
        self.init_device_list()
        self.init_server_connection()
        self.init_msg_boxes()
        self.init_setting_gui()
        self.init_others()
    def init_arguments(self):
        self.arguments = sys.argv[1:]
        try:
            self.initial_x = int(self.arguments[0])
            self.initial_y = int(self.arguments[1])
        except:
            self.initial_x = int(1920/3)
            self.initial_y = int(1080/3)
        if len(self.arguments) >= 3:
            self.device_name_hint = True
            self.initial_device_name_hint = self.arguments[2]
        else:
            self.device_name_hint = False
            self.initial_device_name_hint = None
        self.ip = ""
    def init_preparation(self):
        # variable settings
        self.macro_version = '0.312'
        self.is_automator_initiated = False
        self.device_names = ['leonis','jchoi82kor','initiator', 'terminator', "facebook", "boringstock2", "SM-N950N", "SM-G950N", "SM-A826S", "SM-A826S"]
        self.device_types = ['nox_1920_1080', 'android', 'nox_1280_720', 'android_q2', 'blue_1280_720', 'gpg_3840_2160', 'gpg_1920_1080']
        self.device_index_by_name = {'leonis':2,'jchoi82kor':2, 'initiator':2, 'terminator':2, 'facebook':0, 'boringstock2':0, 'SM-N950N':1, 'SM-G950N':1, "SM-A826S":3}
        self.add_device_name_and_type()
        # Read config_oper_option
        config_for_operation_option = configparser.ConfigParser()
        try:
            config_for_operation_option.read("config_for_operation_option.txt", encoding='UTF-8')
        except Exception as e:
            print(e)
            return False
        self.dic_of_text_lists_for_cb_operation_option = config_to_dict(config_for_operation_option)
    def add_device_name_and_type(self):
        # find window hwnd using process name
        blue_stack_hwnds = self.get_hwnd_by_process_name("HD-Player.exe")
        for bh in blue_stack_hwnds:
            # print(bh)
            window_name = win32gui.GetWindowText(bh)
            self.device_names.append(window_name)
            self.device_index_by_name[window_name] = 4 #for blue_stack
        nox_hwnds = self.get_hwnd_by_process_name("Nox.exe")
        for nh in nox_hwnds:
            # print(nh)
            window_name = win32gui.GetWindowText(nh)
            self.device_names.append(window_name)
            self.device_index_by_name[window_name] = 2  # for nox
        # For Google Play Games
        gpg_hwnds = self.get_hwnd_by_process_name("crosvm.exe")
        for nh in gpg_hwnds:
            # print(nh)
            window_name = win32gui.GetWindowText(nh)
            self.device_names.append(window_name)
            monitors = get_monitors()
            for monitor in monitors:
                width = monitor.width
                height = monitor.height
                bigger = width if width > height else height
                if bigger == 3840:
                    self.device_index_by_name[window_name] = 5  # for gpg
                elif bigger == 1920:
                    self.device_index_by_name[window_name] = 6  # for gpg
                else:
                    pass
                break
    def init_device_list(self):
        windows = gw.getAllWindows()
        # print(f"DeviceNames: {self.device_names}")
        for window in windows:
            # print(f"HWND: {window._hWnd} and Window Name: {window.title}")
            if window.title in self.device_names:
                self.connected_device_name_and_handle.append((window.title, window._hWnd))
        # print("Connected Devices: ", self.connected_device_name_and_handle)
        # Connect to the ADB server
        try:
            adb = AdbClient(host="127.0.0.1", port=5037)
            # adb.remote_connect(host="127.0.0.1", port=59666)
            # Get the device list
            self.adb_devices = adb.devices()
            # Print the serial numbers and names of connected devices
            for device in self.adb_devices:
                device_name = device.shell("getprop ro.product.model").strip()
                self.connected_device_name_and_serial.append((device_name, device.serial, device))
        except Exception as e:
            print(f"Exception:{e}")
        # for Google Play Games
        gpg_hwnds = self.get_hwnd_by_process_name("crosvm.exe")
        if gpg_hwnds:
            try:
                device_name = win32gui.GetWindowText(gpg_hwnds[0])
                self.connected_device_name_and_serial.append((device_name, device_name, device_name))
            except Exception as e:
                print(f"Exception:{e}")
        print("Connected Devices(name and serial): ", self.connected_device_name_and_serial)
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
    def init_server_connection(self):
        """
        서버에 접속 후,
        1. 버전을 확인하고, 패스워드를 비교
        2. operation_description과 연결된 function_name을 받아온다.
        """
        # password = self.show_password_dialog()
        password = 'leonis'
        # Call the function to get the public IP address
        self.ip = get_public_ip()
        # print("Your public IP address is:", ip)

        server_version, server_password = self.get_version_and_pass()

        if not password == server_password:
            print(f"Error. Wrong password. Closing")
            self.exit()
            return False
        if not self.match_version(server_version):
            print(f"Error. Out of version {self.macro_version}. Server version is {server_version}. Need to update.")
            self.exit()
            return False
        if not self.init_oper_desc_and_func_name():
            print("Error downloading operation description and function name.")
            self.exit()
            return False
        print(f"Server connected. Version: {self.macro_version}")
    def match_version(self, server_version):
        if server_version[:3] <= self.macro_version[:3]:
            return True
        else:
            return False
    def get_version_and_pass(self):
        connection = mysql.connector.connect(host='146.56.43.43',user='ffbeuser',password='leonis',database='ffbe')
        cursor = connection.cursor()
        query = "select * from version_info ORDER BY seq desc limit 1;"
        cursor.execute(query)
        results = cursor.fetchall()
        cursor.close()
        connection.close()
        try:
            server_version = results[0][1]
            server_password = results[0][2]
        except Exception as e:
            print(f"Exception: {e} with result: {results} in get_version_and_pass")
            return False, False
        return server_version, server_password
    def exit(self):
        try:
            self.automator.running = False
        except:
            print("No automator present.")
        print("Closing macro.")
        self.close()
    def init_oper_desc_and_func_name(self):
        """
        동작 설명과 automator에서 연결된 함수 이름을 받아온다.
        :return:
        """
        self.operation_description = []
        self.operation_function_name = {}
        # 서버 연결해서 받아오기
        # desc = 'test'
        # func = 'multi_client_any'
        connection = mysql.connector.connect(host='146.56.43.43',user='ffbeuser',password='leonis',database='ffbe')
        # cursor = connection.cursor()
        query = "SELECT * FROM operation_list where in_use = 'y'"
        # cursor.execute(query)
        # results = cursor.fetchall()
        # index = cursor.column_names
        df = pandas.read_sql(query, connection)
        print(df)
        df = df.sort_values(by='sort_order')
        for _, row in df.iterrows():
            self.operation_description.append(row['operation_description'])
            self.operation_function_name[row['operation_description']] = row['function_name']
            # self.operation_description.append(row[2])
            # self.operation_function_name[row[2]] = row[3]
        # cursor.close()
        connection.close()
        # combo box에 설명 채우기
        self.cb_operation.clear()
        for d in self.operation_description:
            self.cb_operation.addItem(d)
        return True
    def init_ui(self):
        # Load the UI file
        uic.loadUi('ffbe_widget.ui', self)
        # Connect any signals and slots
        btn_list = self.findChildren(QtWidgets.QPushButton)
        for b in btn_list:
            b.clicked.connect(self.on_button_clicked)
        # Connect the slot function to the currentTextChanged signal
        self.cb_window_name.currentTextChanged.connect(self.on_cb_window_name_text_changed)
        self.cb_operation.currentTextChanged.connect(self.on_cb_operation_text_changed)
        self.le_rep.setText("300")
        self.le_players.setText("4")
        self.le_sleep_multiple.setText("3")
        self.cb_gui_mode.addItem('E')
        self.cb_gui_mode.addItem('A')
        self.cb_gui_mode.addItem('B')
        self.cb_gui_mode.setCurrentText('E')
        self.device_mode = 'E'
        self.show()
    def init_msg_boxes(self):
        self.log_list = []
        self.debug_list = []
        self.error_list = []

        if not self.initial_x:
            cur_pos = self.mapToGlobal(self.geometry().topLeft())
            self.initial_x, self.initial_y = cur_pos.x(), cur_pos.y()
        self.log_widget = Output_Widget(650,300)
        self.obj_log = self.log_widget.obj_output
        self.log_widget.setWindowTitle("Log")
        self.log_widget.show()
        self.log_widget.move(self.initial_x,self.initial_y)
        self.log_widget.showMinimized()

        self.debug_widget = Output_Widget(1000,600)
        self.obj_debug = self.debug_widget.obj_output
        self.debug_widget.setWindowTitle("Debug")
        self.debug_widget.show()
        self.debug_widget.move(self.initial_x,self.initial_y)
        self.debug_widget.showMinimized()

        self.error_widget = Output_Widget()
        self.obj_error = self.error_widget.obj_output
        self.error_widget.setWindowTitle("Error")
        self.error_widget.show()
        self.error_widget.move(self.initial_x,self.initial_y)
        self.error_widget.showMinimized()
    def init_others(self):
        self.device_initiated = False
        if self.initial_x:
            print(f"Initial position: {self.initial_x, self.initial_y}")
            self.move(self.initial_x,self.initial_y)
        else:
            cur_pos = self.mapToGlobal(self.geometry().topLeft())
            self.initial_x, self.initial_y = cur_pos.x(), cur_pos.y()
        self.operation_status_checker = osc.OperationStatusChecker()
    def init_setting_gui(self):
        serial = self.cb_device_serial.currentText()
        self.setting_dialog = setting_gui.SettingsDialog()
        if serial:
            gui_mode = self.cb_gui_mode.currentText()
            if gui_mode == 'E':
                setting_section_name = serial
            else:
                setting_section_name = serial + '_' + self.cb_gui_mode.currentText()
            print(f"serial: {setting_section_name}")
            print(f"Initiate with serial - {setting_section_name}")
            self.setting_dialog.initUi(setting_section_name)
        else:
            self.setting_dialog.initUi()
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
        nearest_hwnd = self.get_nearest_hwnd()
        if nearest_hwnd:
            self.cb_window_hwnd.setCurrentText(str(nearest_hwnd))
        self.device_initiated = True
    def find_device_name(self):
        try:
            return self.connected_device_name_and_handle[0][0]
        except:
            return None
    def get_hwnd_by_process_name(self, process_name):
        hwnd_found = []
        def enum_windows_callback(hwnd, lparam):
            nonlocal hwnd_found
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            try:
                process = psutil.Process(pid)
                if process_name.lower() == process.name().lower():
                    if win32gui.IsWindowVisible(hwnd):
                        hwnd_found.append(hwnd)
            except psutil.NoSuchProcess:
                pass
        win32gui.EnumWindows(enum_windows_callback, None)
        return hwnd_found
        # print(get_hwnd_by_process_name("HD-Player.exe"))
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
        if self.initial_device_name_hint:
            for ns in self.connected_device_name_and_serial:
                if ns[0] == device_name:
                    if self.initial_device_name_hint in ns[1]:
                        serial = ns[1]
                        print("Fount device with hint")
                        break
                    else:
                        continue
        if serial:
            return serial
        # Hint doesn't exist or Serial of hint doesn't exist
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
    def get_nearest_hwnd(self):
        print("Finding Nearest hwnd")
        myHwnd = self.winId()
        device_name = self.cb_window_name.currentText()
        hwnds = set([nh[1] for nh in self.connected_device_name_and_handle if nh[0] == device_name])
        hwnd_and_distance = sorted([(hwnd, calculate_center_distance(myHwnd, hwnd)) for hwnd in hwnds], key=lambda x:x[1])
        print(hwnd_and_distance[0][0])
        return hwnd_and_distance[0][0]
    def on_button_clicked(self):
        sender_name = self.sender().objectName()
        btn_text = self.sender().text()
        print(f"Btn clicked, sender: {sender_name}, text: {btn_text}")
        found = False
        self.write_log_to_server(sender_name)
        if not self.device_initiated:
            print("Auto initiating")
            self.set_device_name_and_type()
            self.pb_operation.setText(self.cb_operation.currentText())
            # return True
        elif sender_name.lower() == 'pb_pause':
            try:
                self.operation_status_checker.pause()
                if 'off' in self.sender().text().lower():
                    self.sender().setText('Pause:On')
                else:
                    self.sender().setText('Pause:Off')
            except Exception as e:
                self.error_handler(e)
        elif sender_name.lower() == 'pb_esc':
            try:
                self.start_thread(self.on_pb_ese)
            except Exception as e:
                self.error_handler(e)
        elif sender_name.lower() == 'pb_a':
            try:
                self.start_thread(self.on_pb_a)
            except Exception as e:
                self.error_handler(e)
        elif sender_name.lower() == 'pb_b':
            try:
                self.start_thread(self.on_pb_b)
            except Exception as e:
                self.error_handler(e)
        else:
            self.set_params()
            # Automatic btns.
            try:
                if 'on' in self.pb_pause.text().lower():
                    self.sender().setText('Pause:Off')
                self.start_automator(sender_name=sender_name, btn_text=btn_text)
                found = True
            except Exception as e:
                self.error(f"Exception:{e}. in on_button_clicked. Btn Clicked: {btn_text}")
                found = False
            return found
    def open_settings(self):
        cur_pos = self.mapToGlobal(self.geometry().topLeft())
        print(f"Setting cur position: {cur_pos}")
        self.init_setting_gui()
        self.setting_dialog.set_position(cur_pos)
        self.setting_dialog.exec_()
    def set_foreground(self):
        try:
            win32gui.SetForegroundWindow(self.window_hwnd)
        except Exception as e:
            print(e)
            window_hwnd = self.cb_window_hwnd.currentText()
            try:
                win32gui.SetForegroundWindow(window_hwnd)
            except Exception as e:
                print(e)
    def start_thread(self, target_function):
        target_thread = threading.Thread(target=target_function)
        target_thread.start()
    def on_pb_ese(self):
        my_device = self.my_dev
        my_device.input_keyevent(3)
        self.init_setting_gui()
        my_device.shell("am force-stop com.square_enix.android_googleplay.WOTVffbeww")
        self.device_mode = 'E'
        self.cb_gui_mode.setCurrentText('E')
    def on_pb_a(self):
        self.device_mode = 'A'
        self.cb_gui_mode.setCurrentText('A')
        self.init_setting_gui()
        my_device = self.my_dev
        my_device.input_keyevent(3)
        time.sleep(1)
        my_device.shell("am force-stop com.square_enix.android_googleplay.WOTVffbeww")
        time.sleep(1)
        my_device.input_tap(300, 80)
        self.set_foreground()
    def on_pb_b(self):
        self.device_mode = 'B'
        self.cb_gui_mode.setCurrentText('B')
        self.init_setting_gui()
        my_device = self.my_dev
        my_device.input_keyevent(3)
        time.sleep(1)
        my_device.shell("am force-stop com.square_enix.android_googleplay.WOTVffbeww")
        time.sleep(1)
        my_device.input_tap(600, 80)
        self.set_foreground()
    def on_cb_operation_text_changed(self, text):
        cur_text = self.pb_operation.text()
        try:
            if not ('on' in cur_text) and not (cur_text.lower() == 'init') and not (cur_text.lower() == '초기화') :
                self.pb_operation.setText(text)
        except Exception as e:
            self.error(f"Error in on_cb_operation_text_changed, text: {text} with {e}")

        cb_text = self.cb_operation.currentText()
        if cb_text in self.dic_of_text_lists_for_cb_operation_option.keys():
            self.cb_operation_option1.clear()
            self.cb_operation_option2.clear()
            try:
                option1_list = [i.strip() for i in self.dic_of_text_lists_for_cb_operation_option[cb_text]['option1_list'].split(',')]
            except Exception as e:
                self.error_handler(e)
            try:
                option2_list = [i.strip() for i in self.dic_of_text_lists_for_cb_operation_option[cb_text]['option2_list'].split(',')]
            except Exception as e:
                self.error_handler(e)
            self.cb_operation_option1.addItems([""] + option1_list)
            self.cb_operation_option2.addItems([""] + option2_list)
        else:
            self.cb_operation_option1.clear()
            self.cb_operation_option1.addItems([""])
            self.cb_operation_option2.clear()
            self.cb_operation_option2.addItems([""])
    def on_cb_window_name_text_changed(self, text):
        #hwnd, device_type, serial
        device_name = text
        try:
            self.cb_window_hwnd.setCurrentText(str(self.get_hwnd_by_name(device_name)))
            self.cb_device_type.setCurrentIndex(self.device_index_by_name[device_name])
            self.cb_device_serial.setCurrentText(self.get_serial_by_name(device_name))
        except Exception as e:
            self.error(f"Error in on_cb_window_name_text_changed: {e}")
        print("Text changed:", text)
    def on_cb_device_serial_text_changed(self, text):
        self.device_serial = self.cb_device_serial.currentText()
        self.set_my_device(self.device_serial)
    def on_le_test_para_text_finished(self, text):
        self.test_para = text
        print(text)
    def start_automator(self, sender_name=None, btn_text=None, operation_type=""):
        operation_description = self.cb_operation.currentText()
        base_text = operation_description
        on_text = base_text + ': on'
        off_text = base_text + ': off'
        job = self.operation_function_name[operation_description]
        print(f"Starting automator. Sender name:{sender_name}, btn_text:{btn_text}, on_text:{on_text}, off_text:{off_text}, job:{job}")
        if 'on' == btn_text.split()[-1] or operation_type.lower() == 'off':
            self.sender().setText(off_text)
            self.exit_event.set()
            self.automator.stop()

        else:
            self.operation_status_checker = osc.OperationStatusChecker()
            self.operation_status_checker.reset()
            self.exit_event = threading.Event()
            self.automator = ffbe_automator.Automator(self.exit_event)
            self.automator.convert_to_A = self.on_pb_a
            self.automator.convert_to_B = self.on_pb_b
            self.automator.set_msg_handlers(log=self.log, debug=self.debug, error=self.error)
            self.automator.set_window_and_device(window_name=self.window_name, window_hwnd=self.window_hwnd, device_type=self.device_type, device_serial=self.device_serial)
            self.automator.set_job(job=job)
            self.automator.set_user_params(automator_paras=self.automator_paras, operation_status_checker=self.operation_status_checker, finish_button=self.sender())
            # self.automator.set_user_params(rep_time=self.rep_time, num_of_players=self.num_of_players,
            #                                finish_button=self.sender(), sleep_multiple=self.sleep_multiple,operation_option1=self.operation_option1, operation_option2=self.operation_option2, operation_status_checker=self.operation_status_checker, test_para=self.test_para)
            self.automator.set_automator_settings(self.setting_dialog)
            print("Starting automator thread")
            target = self.automator.start_automation
            self.automator_thread = threading.Thread(target=target)
            self.sender().setText(on_text)
            try:
                self.automator_thread.start()
            except:
                pass
    def set_params(self):
        self.window_name = self.cb_window_name.currentText()
        self.window_hwnd = self.cb_window_hwnd.currentText()
        self.device_type = self.cb_device_type.currentText()
        self.device_serial = self.cb_device_serial.currentText()
        self.set_my_device(self.device_serial)
        print(f"Setting parameters: ", self.window_name, self.window_hwnd, self.device_type, self.device_serial)
        self.automator_paras.rep_time = int(self.le_rep.text())
        self.automator_paras.num_of_players = int(self.le_players.text())
        self.automator_paras.sleep_multiple = int(self.le_sleep_multiple.text())
        self.automator_paras.operation_option1 = self.cb_operation_option1.currentText()
        self.automator_paras.operation_option2 = self.cb_operation_option2.currentText()
        self.automator_paras.test_para = self.le_test_para.text()
    def set_my_device(self, serial=None):
        if not serial:
            serial = self.cb_device_serial.currentText()
        my_dev = None
        if self.adb_devices:
            for dev in self.adb_devices:
                if dev.serial == serial:
                    my_dev = dev
        if my_dev:
            self.my_dev = my_dev
            return True
        else:
            return False
    def log(self, msg):
        self.log_list.append(f"{msg}")
        msg_event = MsgEvent()
        QCoreApplication.postEvent(self, msg_event)
    def debug(self, msg):
        self.debug_list.append(f"{msg}")
        msg_event = MsgEvent()
        QCoreApplication.postEvent(self, msg_event)
    def error(self, msg):
        msg = f"{msg}"
        if not (msg in self.error_list):
            print(f"Error occurred-[{msg}]")
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
        msg = ''
        for m in self.error_list:
            msg += m + '\n'
        self.obj_error.setText(msg)
        self.gui_update()
    def gui_update(self):
        self.obj_log.verticalScrollBar().setValue(self.obj_log.verticalScrollBar().maximum())
        self.obj_debug.verticalScrollBar().setValue(self.obj_debug.verticalScrollBar().maximum())
        self.obj_error.verticalScrollBar().setValue(self.obj_error.verticalScrollBar().maximum())
        try:
            label_text = self.automator.locator.img_path
            self.lb_info.setText(label_text)
        except Exception as e:
            print(e)
    def closeEvent(self, event):
        self.automator.close()
        QApplication.quit()
    def show_password_dialog(self):
        password, ok = QInputDialog.getText(None, "Password", "Enter password:", QLineEdit.Password)
        if ok:
            # Check the entered password here or perform any required actions
            # print("Entered Password:", password)
            return password
    def write_log_to_server(self, button_name:str):
        connection = mysql.connector.connect(host='146.56.43.43',user='ffbeuser',password='leonis',database='ffbe')
        cursor = connection.cursor()
        query = "INSERT INTO user_log (user_ip, order_date, order_button) values (%s, now(), %s);"
        values = (self.ip, button_name)
        cursor.execute(query, values)
        connection.commit()
        cursor.close()
        connection.close()
    def error_handler(self, msg=None):
        caller = inspect.currentframe().f_back.f_code.co_name
        if msg:
            text = f"Exception in {caller} as : {msg}"
        else:
            text = f"Exception in {caller}"
        print(text)
        self.error(text)
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
    window_title = f"for WingedAngel v.{widget.macro_version}"
    widget.setWindowTitle(window_title)
    sys.exit(app.exec_())