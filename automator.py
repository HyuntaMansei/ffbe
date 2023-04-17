import mss
import mss.tools
import win32gui
from PIL import Image
import pyautogui
import time
import configparser

class Automator:
    def __init__(self, hwnd:str=None, path:str='./', confidence=0.95):
        self.sct = mss.mss()
        self.basic_init(path, confidence)
        if hwnd != None:
            self.size_init(hwnd)
    def basic_init(self, path, confidence=0.95, waiting_time=10):
        self.confidence = confidence
        self.clicking_time = 0.5
        self.set_path(path)
        self.trial_number = waiting_time
        self.xys = {}
        self.click_on_device = None
    def load_conf(self, device_type:str):
        config = configparser.ConfigParser()
        config.read('./config.ini')
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
        if rect != None:
            pass
        elif window_text != None:
            self.hwnd = win32gui.FindWindow(None, window_text)
        elif hwnd != None:
            self.hwnd = hwnd
        else:
            return False
        self.client_xy0 = win32gui.ClientToScreen(self.hwnd, (0,0))
        self.client_size = (win32gui.GetClientRect(self.hwnd)[2], win32gui.GetClientRect(self.hwnd)[3])
        self.rect = (self.client_xy0[0], self.client_xy0[1], self.client_xy0[0]+self.client_size[0], self.client_xy0[1]+self.client_size[1])
        print(self.client_xy0)
        print(self.client_size)
    def get_path(self, img_name:str):
        return self.img_path + img_name + '.png'
    def locate(self, img_name: str, trial_number=1):
        for count in range(int(trial_number)):
            img = self.sct.grab(self.rect)
            pil_img = Image.frombytes("RGB", img.size, img.bgra, "raw", "BGRX")
            loc = pyautogui.locate(self.get_path(img_name), pil_img, confidence=self.confidence)
            if loc != None:
                print(f"Locating: {loc}, center:{loc[0]+int(loc[2]/2), loc[1]+int(loc[3]/2)}")
                print("Saving sc.png")
                pil_img.save('sc.png')
                return (loc[0]+int(loc[2]/2), loc[1]+int(loc[3]/2))
        return None
    def locate_on_screen(self, img_name:str):
        loc = self.locate(img_name)
        try:
            return (self.client_xy0[0]+loc[0], self.client_xy0[1]+loc[1])
        except:
            return None
    def click_on_screen(self, xy):
        prev_pos = pyautogui.position()
        time.sleep(self.clicking_time)
        if self.click_on_device != None:
            x, y = win32gui.ScreenToClient(self.hwnd, xy)
            xy = (x-self.real_cli_x0, y-self.real_cli_y0)
            self.click_on_device(xy[0], xy[1])
            print(f"clicking as dev xy: {xy}")
            time.sleep(self.clicking_time)
        else:
            pyautogui.click(xy)
            time.sleep(self.clicking_time)
            pyautogui.moveTo(prev_pos.x, prev_pos.y)
        return xy
    def click(self, xy):
        if type(xy) == tuple:
            pass
        elif xy in self.xys.keys():
            xy = self.xys[xy]
        else:
            self.read_coor()
            if xy in self.xys.keys():
                xy = self.xys[xy]
            else:
                return False
        loc = win32gui.ClientToScreen(self.hwnd, xy)
        return self.click_on_screen(loc)
    def locate_and_click(self, img_name: str, xy=None, trial_number = 1):
        for count in range(trial_number):
            loc = self.locate_on_screen(img_name)
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
    def read_coor(self, file_name:str=None):
        if file_name != None:
            with open(file_name, 'r') as f:
                lines = f.readlines()
                for l in lines:
                    self.xys[l.split('=')[0].strip()] = (int(l.split('=')[1].split(',')[0].strip()), int(l.split('=')[1].split(',')[1].strip()))
            self.coor_file_path = file_name
        elif self.coor_file_path != None:
            self.read_coor(self.coor_file_path)
        else:
            return False