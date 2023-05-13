import os.path
import threading

import mss
import mss.tools
import win32gui
from PIL import Image
import pyautogui
import time
import configparser

class Locator:
    def __init__(self, hwnd:str=None, path:str='./', confidence=0.95, debug=print, log=print):
        print("---Initiating Locator---")
        print(hwnd, path, log, debug)
        self.debug = debug
        self.log = log
        self.sct = mss.mss()
        self.basic_init(path, confidence)
        if hwnd != None:
            self.size_init(hwnd)
        th_rect_checker = threading.Thread(target=self.rect_checker)
        th_rect_checker.start()
        print("---End of Initializing Locator---")
    def basic_init(self, path, confidence=0.95, waiting_time=10):
        print("In basic_init of Locator")
        self.confidence = confidence
        self.sltime_before_click = 0.1
        self.sltime_after_click = 0.1
        self.set_path(path)
        self.read_coordinates(path + "coordinates.txt")
        self.trial_number = waiting_time
        self.click_on_device = None
        self.debug_msg_list = []
        self.print_debug = print
        print("End of basic_init of Locator")
    def load_conf(self, device_type:str):
        print("In load_conf of Locator")
        config = configparser.ConfigParser()
        config.read('./locator_config.txt')
        self.conf = config[device_type]
        # self.conf['dev_size']
        self.real_cli_x0, self.real_cli_y0 = (int(self.conf['real_cli_xy0'].split(',')[0]), int(self.conf['real_cli_xy0'].split(',')[1]))
    def connect_click_method(self, click):
        self.click_on_device = click
    def set_path(self, img_path:str):
        self.img_path = img_path
        if self.img_path[-1] != ("/" or "\\"):
            self.img_path += "\\"
    def size_init(self, hwnd=None, window_text=None, rect=None):
        print("In size_init")
        if rect != None:
            pass
        elif window_text != None:
            self.hwnd = win32gui.FindWindow(None, window_text)
        elif hwnd != None:
            self.hwnd = hwnd
        else:
            return False
        self.cur_rect = win32gui.GetWindowRect(self.hwnd)
        self.client_xy0 = win32gui.ClientToScreen(self.hwnd, (0,0))
        self.client_size = (win32gui.GetClientRect(self.hwnd)[2], win32gui.GetClientRect(self.hwnd)[3])
        self.rect = (self.client_xy0[0], self.client_xy0[1], self.client_xy0[0]+self.client_size[0], self.client_xy0[1]+self.client_size[1])
        # print(self.client_xy0)
        # print(self.client_size)
        print("End of size_init")
    def rect_checker(self):
        while True:
            new_rect = win32gui.GetWindowRect(self.hwnd)
            if self.cur_rect != new_rect:
                self.debug("Resizing rect")
                self.size_init(self.hwnd)
            time.sleep(2)
    def get_path(self, img_name:str):
        img_path = self.img_path + img_name + '.png'
        if os.path.exists(img_path) == False:
            self.debug(f"No such file: {img_path}", "e")
            return False
        return img_path
    def locate_by_folder(self, folder_name:str, confidence=None):
        ret_value = None
        if folder_name[-1] != '/' and folder_name[-1] != '\\':
            prev_path = self.img_path
            self.img_path = self.img_path + folder_name + '\\'
    def locate(self, img_name: str, trial_number=1, confidence = None):
        if confidence == None:
            confidence = self.confidence
        for count in range(int(trial_number)):
            img = self.sct.grab(self.rect)
            pil_img = Image.frombytes("RGB", img.size, img.bgra, "raw", "BGRX")
            try:
                img_path = self.get_path(img_name)
                if img_path:
                    loc = pyautogui.locate(img_path, pil_img, confidence=confidence)
                else:
                    loc = None
            except:
                loc = None
            if loc != None:
                # print(f"Locating: {loc}, center:{loc[0]+int(loc[2]/2), loc[1]+int(loc[3]/2)}")
                # print("Saving sc.png")
                # pil_img.save('sc.png')
                return (loc[0]+int(loc[2]/2), loc[1]+int(loc[3]/2))
        return None
    def locate_on_screen(self, img_name:str, confidence = None):
        if confidence == None:
            confidence = self.confidence
        loc = self.locate(img_name, confidence=confidence)
        try:
            return (self.client_xy0[0]+loc[0], self.client_xy0[1]+loc[1])
        except:
            return None
    def click_on_screen(self, xy):
        prev_pos = pyautogui.position()
        time.sleep(self.sltime_before_click)
        if self.click_on_device != None:
            x, y = win32gui.ScreenToClient(self.hwnd, xy)
            xy = (x-self.real_cli_x0, y-self.real_cli_y0)
            # print(f"clicking as device xy: {xy}")
            self.click_on_device(xy[0], xy[1])
            time.sleep(self.sltime_after_click)
        else:
            pyautogui.click(xy)
            time.sleep(self.sltime_after_click)
            pyautogui.moveTo(prev_pos.x, prev_pos.y)
        return xy
    def click(self, xy):
        if type(xy) == tuple:
            pass
        elif xy in self.xys.keys():
            xy = self.xys[xy]
        else:
            self.read_coordinates()
            if xy in self.xys.keys():
                xy = self.xys[xy]
            else:
                xy = win32gui.ScreenToClient(self.locate(xy))
                if not xy:
                    return False
        loc = win32gui.ClientToScreen(self.hwnd, xy)
        return self.click_on_screen(loc)
    def locate_and_click(self, img_name: str, xy=None, trial_number = 1, confidence = None):
        if confidence == None:
            confidence = self.confidence
        for count in range(trial_number):
            loc = self.locate_on_screen(img_name, confidence=confidence)
            if loc != None:
                if xy == None:
                    return self.click_on_screen(loc)
                else:
                    self.click(xy)
                    return loc
            time.sleep(1)
        return None
    def wait_and_click(self, img_name: str, xy=None, trial_number=None):
        if trial_number == None:
            trial_number = self.trial_number
        return self.locate_and_click(img_name, xy=xy, trial_number=trial_number)
    def read_coordinates(self, file_name:str=None):
        print(f"In read_coordinates, file_name:{file_name}")
        self.xys = {}
        if file_name != None:
            with open(file_name, 'r') as f:
                lines = f.readlines()
                for l in lines:
                    print(f"reading coordinates: {l}")
                    try:
                        self.xys[l.split('=')[0].strip()] = (int(l.split('=')[1].split(',')[0].strip()), int(l.split('=')[1].split(',')[1].strip()))
                    except:
                        print(f"reading error")
            self.coor_file_path = file_name
        elif self.coor_file_path != None:
            self.read_coordinates(self.coor_file_path)
        else:
            return False
    # def debug(self, msg:str):
    #     if not msg in self.debug_msg_list:
    #         self.debug_msg_list.append(msg)
    #         self.print_debug(msg)