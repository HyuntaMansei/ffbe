import win32gui
import win32con
import time
import datetime
import locator
from ppadb.client import Client as AdbClient
import threading
class Automator:
    def __init__(self, window_name:str, device_type:str, automation_name, debug=print, log=print):
        self.debug = debug
        self.log = log
        self.device_init(window_name)
        self.set_params(device_type, automation_name)
    def device_init(self, window_name:str):
        self.my_client = AdbClient()
        print(self.debug)
        self.debug(f"devices: {self.my_client.devices()}")
        self.my_device = self.my_client.devices()[0]
        self.my_hwnd = win32gui.FindWindow(None, window_name)
        self.debug(f"hwnd: {self.my_hwnd}")
    def set_params(self, device_type, automation_name):
        self.debug("--In set_params--")
        if device_type == 'nox_1920_1080':
            self.automation_path = './1920_1080/'
        elif device_type == 'nox_1280_720':
            self.automation_path = './1280_720/'
        elif device_type == 'android':
            self.automation_path = './1280_720/'
        else:
            pass
        if automation_name == 'play_quest':
            self.automation_path += 'quest/'
        elif automation_name == 'play_multi':
            self.automation_path += 'multi/'
        elif automation_name == 'summon':
            self.automation_path += 'summon/'
        else:
            pass
        self.debug(f"my_hwnd:{self.my_hwnd}, path={self.automation_path}")
        self.debug(f"my_device:{self.my_device}, device_type:{device_type}")
        self.my_locator = locator.Locator(self.my_hwnd, self.automation_path, debug=self.debug, log=self.log)
        self.my_locator.load_conf(device_type)
        self.my_locator.confidence = 0.85
        self.my_locator.connect_click_method(self.my_device.input_tap)
        self.debug("--End of set_param def--")
    def play_quest(self, rep_time):
        self.running = True
        self.log(f"Starting quest automain.")
        for cnt in range(rep_time):
            # 퀘스트 자동 진행

            self.debug("Before battle, trying to click sortie")
            while (not self.my_locator.locate('sortie')) and self.running:
                self.my_locator.locate_and_click('select_chapter', xy='top_quest')
            ##skip 하기 누르기
            while (self.my_locator.locate('auto') == None) and self.running:
                self.my_locator.locate_and_click('sortie')
                self.my_locator.click('story_skip1')
                time.sleep(2)
                self.my_locator.click('story_skip2')
            self.debug("In battle stage")
            start_time = time.time()
            while (not self.my_locator.locate('next') and self.running):
                time.sleep(1)
            self.debug("Mission complete")
            elasped_time = time.time() - start_time
            self.debug(f"elasped_time: {time.strftime('%M:%S', time.gmtime(elasped_time))}")
            self.debug("Until end_of_quest")
            while (self.my_locator.locate('end_of_quest') == None) and self.running:
                self.my_locator.locate_and_click('next')
                self.my_locator.locate_and_click('close')
                self.my_locator.locate_and_click('later')
                self.my_locator.locate_and_click('no_evaluate')
            time.sleep(2)
            self.debug("The quest ended")
            time.sleep(10)
            count = 0
            self.debug(f"after batlle, until 'select chapter', repeating, ... story skip, count={count}")
            while (self.my_locator.locate('select_chapter', trial_number=2) == None) and self.running:
                self.my_locator.locate_and_click('end_of_quest')
                self.my_locator.locate_and_click('ok')
                self.my_locator.locate_and_click('later')
                self.my_locator.locate_and_click('close')
                if not self.my_locator.locate('select_chapter'):
                    self.my_locator.click('story_skip1')
                    time.sleep(1)
                if not self.my_locator.locate('select_chapter'):
                    self.my_locator.click('story_skip3')
                count += 1
                self.my_locator.locate_and_click('story')
            if not self.running:
                self.debug("Quit automation")
                break
            self.log(f"Battle Completed {cnt+1} times")
        self.log("Automaiton completed")
    def play_multi(self, rep_time, num_of_players, finish_button=None):
        self.running = True
        # multi auto play
        self.my_locator.confidence = 0.90
        self.time_limit = 300
        self.log("Starting multi automation")
        for cnt in range(rep_time):
            self.init_time()
            self.debug(f"Before battle stage.")
            while (not self.my_locator.locate('auto')) and self.running:
                sortie_cond = False
                if num_of_players == 1:
                    sortie_cond = True
                elif num_of_players == 2:
                    if not self.my_locator.locate('one_person'):
                        sortie_cond = True
                elif num_of_players == 3:
                    if (self.my_locator.locate('three_people')) or (self.my_locator.locate('four_people')):
                        sortie_cond = True
                elif num_of_players == 4:
                    if (self.my_locator.locate('four_people')):
                        sortie_cond = True
                if sortie_cond:
                    self.debug(f"Trying to click sortie, # of players: {num_of_players}, elap_time: {int(self.elasped_time())} sec")
                    self.my_locator.locate_and_click('sortie')
                self.my_locator.locate_and_click('sortie_confirm')
                # self.my_locator.locate_and_click('ok')
                if self.elasped_time() > 30:
                     while (self.my_locator.locate('checking_the_result')) and self.running:
                         self.debug("Kicking some checking the result!")
                         if self.my_locator.locate_and_click('checking_the_result'):
                            while True:
                                time.sleep(1)
                                self.my_locator.locate_and_click('expel')
                                time.sleep(1)
                                if (not self.my_locator.locate('expel')) and (not self.my_locator.locate('checking_the_result')):
                                    break
                if self.elasped_time() > self.time_limit:
                    self.debug("Kicking all out!")
                    while (not self.my_locator.locate('one_person')) and self.running:
                        self.my_locator.locate_and_click('kick_out')
                        self.my_locator.locate_and_click('expel')
                    self.init_time()
            self.debug("\n'Auto' is located. In battle stage")
            start_time = time.time()
            while (not self.my_locator.locate('next')) and self.running:
                self.my_locator.locate_and_click('ok')
                self.my_locator.locate_and_click('ok2')
                self.my_locator.locate_and_click('give_up')
                if self.my_locator.locate_and_click('yes'):
                    break
                time.sleep(1)
            # after battle stage
            self.debug("After battle stage")
            elapsed_time = time.time() - start_time
            self.log(f"Elapsed_time: {time.strftime('%M:%S', time.gmtime(elapsed_time))}")
            while (not self.my_locator.locate('organize')) and self.running:
                self.my_locator.locate_and_click('next')
                # self.my_locator.locate_and_click('ok')
                self.my_locator.locate_and_click('cancel')
                self.my_locator.locate_and_click('go_back')
            if not self.running:
                self.log("Quit automation")
                break
            self.log(f"Completed: {cnt+1} times")
        if (finish_button != None) and self.running:
            finish_button.click()
    def summon(self, rep_time, finish_button = None):
        self.running = True
        # multi auto play
        self.my_locator.confidence = 0.95
        self.time_limit = 300
        self.log("Starting summon automation")
        summon_cnt = 0
        while self.running:
            print(not self.my_locator.locate('confirm_summon'))
            while (not self.my_locator.locate('confirm_summon')) and self.running:
                print("In while loop")
                self.my_locator.locate_and_click('ok')
                self.my_locator.locate_and_click('once_again')
                self.my_locator.locate_and_click('skip')
            if self.my_locator.locate_and_click('confirm_summon'):
                summon_cnt += 1
                self.log(f"Summon: {summon_cnt} times, {rep_time-summon_cnt} times left.")
            if summon_cnt >= rep_time:
                break
        if (finish_button != None) and self.running:
            finish_button.click()
    def stop(self):
        self.running = False
    def connect_debug(self, debug):
        self.debug = debug
    def connect_log(self, log):
        self.log = log
    def elasped_time(self):
        return time.time() - self.start_time
    def init_time(self):
        self.start_time = time.time()