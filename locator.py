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
            # self.debug(f"No such file: {img_path}")
            self.error(f"No such file: {img_path}")
            return False
        return img_path
    def locate_and_click(self, t_str, target=None, confidence=None):
        """
        검색할 이미지와 클릭할 타겟을 받아서, 이미지가 검색될 경우 타켓을 클릭.
        타겟이 없을 경우 이미지 클릭.
        target과 t_str의 when의 값이 동시에 존재해서는 안 된다. > Error 리턴
        :param t_str: 검색할 이미지 | list of 이미지
        :param target: 클릭할 좌표 | None
        :return: 클릭한 좌표값
        """
        # t_str이 리스트라면 재귀 호출
        if type(t_str) == list:
            res_list =[]
            for img in t_str:
                res = self.locate_and_click(img, target=target, confidence=confidence)
                if res:
                    res_list.append(res)
                    time.sleep(1)
            return res_list
        else:
            res = self.get_target_option(t_str=t_str)
            # Error check - when과 target이 동시에 존재
            if(res["when"] and target):
                print(f"double target Error with [{t_str}] and [{target}]")
                return False
            if res["confidence"]:
                confidence = res["confidence"]
            if not res["when"]:
                # t_str에 when이 없는 경우.
                when = res["target"]
                loc = self.locate(when, confidence=confidence)
                if loc:
                    if target:
                        self.debug(f"Suc. to located [{when}] and clicking target: [{target}]")
                        return self.click_on_screen(target)
                    else:
                        self.debug(f"Suc. to located and clicking [{when}] and Loc on window:[{loc}]")
                        return self.click_on_screen(loc)
                return None
            else:
                # t_str에 when이 있는 경우, 함수의 parameter인 target이 없다.
                when = res["when"]
                t_str_target = res["target"]
                # 수정중
                loc = self.locate(when, confidence=confidence)
                if loc:
                    c_res = self.click_on_screen(t_str_target)
                    if c_res:
                        self.debug(f"Suc. to located [{when}] and clicked target: [{t_str_target}]")
                    return c_res
                return None
    def locate(self, t_str, confidence=None):
        """
        이미지 서치 후 Window 기준 중심 좌표를 리턴한다.
        리스트에 대해서는 순차대로 검색 후, 첫번째 일치 좌표를 리턴한다.
        :param t_str: 단일 이미지 이름 | list of 이미지이름
        :return: window 기준 중심 좌표
        """
        if not win32gui.IsWindowVisible(self.hwnd):
            self.error("Window is not visible. return None")
            return None
        # especially for list of images
        if type(t_str) == list:
            for image in t_str:
                result = self.locate(image, confidence=confidence)
                if result:
                    self.debug(f"Successfully located: [{os.path.join(self.img_path,image)}] at {result} in list")
                    return result
            return None
        res = self.get_target_option(t_str=t_str)
        if res["confidence"]:
            confidence = res["confidence"]
        if type(res["target"]) == list:
            return self.locate(res["target"], confidence)
        img = self.sct.grab(self.rect)
        pil_img = Image.frombytes("RGB", img.size, img.bgra, "raw", "BGRX")
        loc = None
        try:
            img_path = self.get_path(res["target"])
            if img_path:
                if confidence:
                    loc = pyautogui.locate(img_path, pil_img, confidence=confidence)
                elif self.confidence:
                    loc = pyautogui.locate(img_path, pil_img, confidence=self.confidence)
                else:
                    loc = pyautogui.locate(img_path, pil_img)
        except Exception as e:
            print(f"Exception: {e} with t_str:{t_str} in locate")
        if loc:
            center = (loc[0]+int(loc[2]/2), loc[1]+int(loc[3]/2))
            return center
        return None
    def click_on_screen(self, target):
        """
        click_on_client와 동일한 기능으로 이해하면 됨.
        Client 기준 좌표 또는 target의 이름을 받아서 클릭
        :param target: Client기준 좌표 | target 이름
        :return: > 클릭한 target. 클릭 안 했으면 False.
        """
        if type(target) == list:
            res_list = []
            for t in target:
                res = self.click_on_screen(t)
                if res:
                    res_list.append(res)
            return res_list
        elif type(target) == tuple:
            xy = target
        elif target in self.xys.keys():
            xy = self.xys[target]
        else:
            self.read_coordinates()
            if target in self.xys.keys():
                xy = self.xys[target]
            else:
                print(f"No target as {target}, try to locate_and_click.")
                return self.locate_and_click(t_str=target)
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
            time.sleep(self.sltime_before_click)
            pyautogui.moveTo(to_click_xy[0], to_click_xy[1], duration=0.2)
            pyautogui.click(to_click_xy[0], to_click_xy[1])
            print(f"Clicking {target} as device xy: {to_click_xy} by pyautogui click")
            time.sleep(self.sltime_after_click)
            pyautogui.moveTo(prev_pos.x, prev_pos.y)
        return target
    def get_target_option(self, t_str):
        p_target = re.compile("^\w*")
        p_addi_target = re.compile("\|\w*")
        p_when = re.compile("@\w*")
        p_confidence = re.compile("#[\w.]*")
        when, confidence = None, None
        try:
            target = re.search(p_target, t_str).group()
            mat = re.findall(p_addi_target, t_str)
            if mat:
                target = [target,]
                for m in mat:
                    target.append(m[1:])
                print(f"Double target: {target} in {t_str}")
            mat = re.search(p_when, t_str)
            if mat:
                when = mat.group()[1:]
            mat = re.search(p_confidence, t_str)
            if mat:
                confidence = mat.group()[1:]
        except Exception as e:
            print(f"Exception [{e}] in t_str:{t_str}")
            return False
        res = {"target":target, "when":when, "confidence":confidence}
        return res
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