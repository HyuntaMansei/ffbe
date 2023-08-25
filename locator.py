import os.path
import threading
import re
import mss
import mss.tools
import win32gui
from PIL import Image
import pyautogui
import time
import configparser
class Locator:
    def __init__(self, hwnd:str=None, automation_path='./a_orders', img_path='./images/', confidence=0.95, debug=print, log=print, error=print):
        print("---Initiating Locator---")
        # print(hwnd, path, log, debug)
        self.debug = debug
        self.log = log
        self.error = error
        self.xys = {}
        self.sct = mss.mss()
        self.basic_init(automation_path, img_path, confidence)
        if hwnd != None:
            self.size_init(hwnd)
        th_rect_checker = threading.Thread(target=self.rect_checker)
        th_rect_checker.start()
        print("---End of Initializing Locator---")
    def basic_init(self, automation_path, img_path, confidence=0.95):
        print("In basic_init of Locator")
        self.confidence = confidence
        self.sltime_before_click = 0.1
        self.sltime_after_click = 0.1
        self.multi_click_interval = 0.1
        self.automation_path = automation_path
        self.img_path = img_path
        self.click_on_device = None
        self.debug_msg_list = []
        self.print_debug = print
        print("End of basic_init of Locator")
    def load_conf(self, device_type:str):
        print("In load_conf of Locator")
        config = configparser.ConfigParser()
        config.read('./locator_config.txt')
        self.device_type = device_type
        self.conf = config[device_type]
        # self.conf['dev_size']
        self.real_cli_x0, self.real_cli_y0 = (int(self.conf['real_cli_xy0'].split(',')[0]), int(self.conf['real_cli_xy0'].split(',')[1]))
        self.coor_file_path = self.conf['coordinates_path']
        self.read_coordinates()
    def connect_click_method(self, click):
        self.click_on_device = click
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
        self.debug(f"New xy0 = {self.client_xy0} and size: {self.client_size}")
        print("End of size_init")
    def rect_checker(self):
        while True:
            try:
                new_rect = win32gui.GetWindowRect(self.hwnd)
                if self.cur_rect != new_rect:
                    self.debug("Resizing rect")
                    self.size_init(self.hwnd)
                time.sleep(2)
            except Exception as e:
                print(f"Exception:{e} in rect_checker")
                self.error("Fail to find window. Exiting.")
                time.sleep(10)
                # exit signal 보내기.
    def get_path(self, img_name:str):
        img_name = img_name.strip()
        if img_name[-4:] != '.png':
            img_path = os.path.join(self.img_path, img_name + '.png')
        else:
            img_path = os.path.join(self.img_path, img_name)
        if not os.path.exists(img_path):
            self.debug(f"No such file: {img_path}")
            return False
        return img_path
    def locate(self, image_name):
        """
        이미지 서치 후 Window 기준 중심 좌표를 리턴한다.
        리스트에 대해서는 순차대로 검색 후, 첫번째 일치 좌표를 리턴한다.
        :param image_name: 단일 이미지 이름 | list of 이미지이름
        :return: window 기준 중심 좌표
        """
        if not win32gui.IsWindowVisible(self.hwnd):
            self.error("Window is not visible. return None")
            return None
        # especially for list of images
        if type(image_name) == list:
            for image in image_name:
                result = self.locate(image)
                if result != None:
                    self.debug(f"Successfully located: {os.path.join(self.img_path,image)} at {result}")
                    return result
            return None
        img = self.sct.grab(self.rect)
        pil_img = Image.frombytes("RGB", img.size, img.bgra, "raw", "BGRX")
        loc = None
        try:
            img_path = self.get_path(image_name)
            if img_path:
                if self.confidence:
                    loc = pyautogui.locate(img_path, pil_img, confidence=self.confidence)
                else:
                    loc = pyautogui.locate(img_path, pil_img)
        except Exception as e:
            print(f"Exception: {e} with img_path:{img_path} in locate")
        if loc:
            center = (loc[0]+int(loc[2]/2), loc[1]+int(loc[3]/2))
            return center
        return None
    def click(self, target):
        """
        click_on_client와 동일한 기능으로 이해하면 됨.
        Client 기준 좌표 또는 target의 이름을 받아서 클릭(click_on_screen 호출)
        :param target: Client기준 좌표 | target 이름
        :return: 클릭한 좌표
        """
        if type(target) == tuple:
            xy = target
        elif target in self.xys.keys():
            xy = self.xys[target]
        else:
            self.read_coordinates()
            if target in self.xys.keys():
                xy = self.xys[target]
            else:
                pass
                print(f"No target as {target}")
                return False
        prev_pos = pyautogui.position()
        # 위에서 계산한 좌표를 클릭
        # click_on_device가 있는 경우와 그렇지 않은경우(GPG)
        if self.click_on_device:
            to_click_xy = (xy[0] - self.real_cli_x0, xy[1] - self.real_cli_y0)
            self.click_on_device(xy[0]-self.real_cli_x0, xy[1]-self.real_cli_y0)
            print(f"Clicking {target} as device xy: {to_click_xy} by click_on_device")
            time.sleep(self.sltime_after_click)
        else:
            to_click_xy = (self.client_xy0[0]+xy[0] - self.real_cli_x0, self.client_xy0[1]+xy[1] - self.real_cli_y0)
            pyautogui.click(to_click_xy[0], to_click_xy[1])
            print(f"Clicking {target} as device xy: {to_click_xy} by pyautogui click")
            time.sleep(self.sltime_after_click)
            pyautogui.moveTo(prev_pos.x, prev_pos.y)
        return xy
    def locate_and_click(self, img_name, target=None):
        """
        검색할 이미지와 클릭할 타겟을 받아서, 이미지가 검색될 경우 타켓을 클릭.
        타겟이 없을 경우 이미지 클릭.
        :param img_name: 검색할 이미지 | list of 이미지
        :param target: 클릭할 좌표 | None
        :return: 클릭한 좌표값
        """
        if type(img_name) == list:
            res_list =[]
            for img in img_name:
                res = self.locate_and_click(img)
                if res:
                    res_list.append(res)
            return res_list
        else:
            loc = self.locate(img_name)
            if loc:
                if target:
                    self.debug(f"Suc. to located and clicking coordinate: {target}")
                    return self.click(target)
                else:
                    self.debug(f"Suc. to located and clicking {img_name} and Loc on window:{loc}")
                    return self.click(loc)
            return None
    def locate_dir(self, dir_path):
        path = os.path.join(self.automation_path,dir_path)
        try:
            images_in_dir = []
            for f in os.listdir(path):
                if os.path.isfile(os.path.join(path, f)):
                    if f.split('.')[-1] == 'txt':
                        with open(os.path.join(path, f), "r") as file:
                            lines = [f.strip() for f in file.readlines()]  # Read all lines into a list
                        images_in_dir.extend(lines)
                    elif f.split('.')[-1] == "png":
                        images_in_dir.append(os.path.join(dir_path,f))
                    else:
                        self.error(f"Unknown File Extension: {f}")
            # print(images_in_dir)
            return self.locate(images_in_dir)
        except Exception as e:
            print(f"with {e}, No such dir: {path}")
            return None
    def locate_and_click_all_dir(self, dir_name, target=None):
        click_interval = self.multi_click_interval
        path = os.path.join(self.automation_path, dir_name)
        images_in_dir = []
        for f in os.listdir(path):
            if os.path.isfile(os.path.join(path, f)):
                if f.split('.')[-1] == 'txt':
                    with open(os.path.join(path, f), "r") as file:
                        lines = [f.strip() for f in file.readlines()]  # Read all lines into a list
                    images_in_dir.extend(lines)
                elif f.split('.')[-1] == "png":
                    images_in_dir.append(os.path.join(dir_name,f))
                else:
                    self.error(f"Unknown File Extension: {f}")
        # print(images_in_dir)
        result_list = []
        result = None
        for image in images_in_dir:
            if target:
                result = self.locate_and_click(image, target=target)
            else:
                result = self.locate_and_click(image)
            if result:
                result_list.append(result)
                time.sleep(click_interval)
        if result_list != []:
            return result_list
        else:
            return None
    def set_coor_file_path(self, file_name):
        """
        좌표가 적혀있는 파일 이름을 설정.
        :param file_name:
        :return:
        """
        self.coor_file_path = self.img_path + file_name
    def read_coordinates(self):
        cord_file_path = "./coordinates.txt"
        try:
            cord_list = self.read_config(cord_file_path)[self.device_type]
            for l in cord_list:
                self.xys[l.split('=')[0].strip()] = (int(l.split('=')[1].split(',')[0].strip()), int(l.split('=')[1].split(',')[1].strip()))
        except Exception as e:
            print(f"Error in func. read_coordinates, with {e}")
            return False
    def read_config(self, filepath):
        # print(f"In func. read_config, filepath={filepath}")
        with open(filepath, 'r') as f:
            lines = f.readlines()
        p = re.compile('\[.+\]')
        config_dict = {}
        content = []
        for l in lines:
            m = re.match(p,l)
            if m:
                if content:
                    config_dict[cur_label] = content
                cur_label = m.group()[1:-1]
                content = []
            else:
                content.append(l.strip())
        if content:
            config_dict[cur_label] = content
        return config_dict