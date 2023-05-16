import win32gui
import win32con
import time
import datetime
import locator
from ppadb.client import Client as AdbClient
import threading
class Automator:
    def __init__(self, window_name:str, job = "", device_type:str="", automation_name="", debug=print, log=print):
        self.debug = debug
        self.log = log
        self.device_init(window_name)
        self.job = job
        self.device_type = device_type
        self.automation_name = automation_name
        self.stop_watch_started = False
        # self.set_params(automation_name)
    def device_init(self, window_name:str):
        self.my_client = AdbClient()
        print(self.debug)
        self.debug(f"devices: {self.my_client.devices()}")
        self.my_device = None
        for dev in self.my_client.devices():
            # Get the device properties
            properties = dev.get_properties()
            # Retrieve the device name
            device_name = properties["ro.product.model"]
            if device_name == window_name:
                self.my_device = dev
                break
        self.my_hwnd = win32gui.FindWindow(None, window_name)
        self.debug(f"hwnd: {self.my_hwnd}")
    def set_user_param(self, rep_time, num_of_players, finish_button):
        self.rep_time = rep_time
        self.num_of_players = num_of_players
        self.finish_button = finish_button
    def start_automation(self, job:str=None):
        if job == None:
            job = self.job
        if job == "play_raid_client":
            self.set_params("play_raid_client")
            self.play_raid_client()
        elif job == 'play_raid_host4':
            self.set_params("play_raid_host4")
            self.play_raid_host4()
    def set_params(self, automation_name=None):
        self.debug("--In set_params--")
        device_type = self.device_type
        if automation_name == None:
            automation_name = self.automation_name
        if device_type == 'nox_1920_1080':
            self.automation_path = './1920_1080/'
        elif device_type == 'nox_1280_720':
            self.automation_path = './1280_720/'
        elif device_type == 'android':
            self.automation_path = './1280_720/'
        else:
            pass

        self.automation_path += automation_name.replace('play_', '')

        self.debug(f"my_hwnd:{self.my_hwnd}, path={self.automation_path}")
        self.debug(f"my_device:{self.my_device}, device_type:{device_type}")
        self.locator = locator.Locator(self.my_hwnd, self.automation_path)
        self.locator.load_conf(device_type)
        self.locator.confidence = 0.9
        self.time_limit = 300
        self.locator.connect_click_method(self.my_device.input_tap)
        self.debug("--End of set_param def--")
    def play_quest(self, rep_time, finish_button = None, initial_img_name = None):
        self.set_params('play_quest')
        self.running = True
        self.log(f"Starting quest automation.")
        initial_img_names = [
            "select_chapter", "an_alchemist_of_steel", "light_stone"
        ]
        for cnt in range(rep_time):
            # 퀘스트 자동 진행
            self.debug("Before battle, trying to click sortie")
            while (self.locator.locate('sortie') == None) and self.running:
                # for img_name in initial_img_names:
                #     self.my_locator.locate_and_click(img_name, xy='top_quest')
                self.locator.locate_and_click(initial_img_names, xy='top_quest')
            ##skip 하기 누르기
            while (self.locator.locate('auto') == None) and self.running:
                self.locator.locate_and_click('sortie')
                self.locator.click('story_skip1')
                time.sleep(2)
                self.locator.click('story_skip2')
            self.debug("In battle stage")
            start_time = time.time()
            while (self.locator.locate('next') == None) and self.running:
                time.sleep(1)
            self.debug("Mission complete")
            elasped_time = time.time() - start_time
            self.debug(f"elasped_time: {time.strftime('%M:%S', time.gmtime(elasped_time))}")
            self.debug("Until end_of_quest")
            while (self.locator.locate('end_of_quest') == None) and self.running:
                self.locator.locate_and_click('next')
                self.locator.locate_and_click('close')
                self.locator.locate_and_click('later')
                self.locator.locate_and_click('no_evaluate')
            time.sleep(2)
            self.debug("The quest ended")
            time.sleep(10)
            count = 0
            self.debug(f"after batlle, until 'select chapter', repeating, ... story skip, count={count}")
            while (self.locator.locate(initial_img_names, trial_number=2) == None) and self.running:
                self.locator.locate_and_click('end_of_quest')
                self.locator.locate_and_click('ok')
                self.locator.locate_and_click('later')
                self.locator.locate_and_click('close')
                if not self.locator.locate('select_chapter'):
                    self.locator.click('story_skip1')
                    time.sleep(1)
                if not self.locator.locate('select_chapter'):
                    self.locator.click('story_skip3')
                count += 1
                self.locator.locate_and_click('story')
            if not self.running:
                self.debug("Quit automation")
                break
            self.log(f"Battle Completed {cnt+1} times")
        self.log("Automaiton completed")
        if (finish_button != None) and self.running:
            finish_button.click()
    def play_multi(self, rep_time, num_of_players, finish_button=None):
        self.set_params('play_multi')
        self.running = True
        # multi auto play
        self.locator.confidence = 0.90
        self.time_limit = 300
        self.log("Starting multi automation")
        for cnt in range(rep_time):
            self.init_time()
            self.debug(f"Before battle stage.")
            while (not self.locator.locate('auto')) and self.running:
                sortie_cond = False
                if num_of_players == 1:
                    sortie_cond = True
                elif num_of_players == 2:
                    if not self.locator.locate('one_person'):
                        sortie_cond = True
                elif num_of_players == 3:
                    if (self.locator.locate('three_people')) or (self.locator.locate('four_people')):
                        sortie_cond = True
                elif num_of_players == 4:
                    if (self.locator.locate('four_people')):
                        sortie_cond = True
                if sortie_cond:
                    self.debug(f"Trying to click sortie, # of players: {num_of_players}, elap_time: {int(self.elasped_time())} sec")
                    self.locator.locate_and_click('sortie')
                self.locator.locate_and_click('sortie_confirm')
                # self.my_locator.locate_and_click('ok')
                if self.elasped_time() > 30:
                     while (self.locator.locate('checking_the_result')) and self.running:
                         self.debug("Kicking some checking the result!")
                         if self.locator.locate_and_click('checking_the_result'):
                            while True:
                                time.sleep(1)
                                self.locator.locate_and_click('expel')
                                time.sleep(1)
                                if (not self.locator.locate('expel')) and (not self.locator.locate('checking_the_result')):
                                    break
                if self.elasped_time() > self.time_limit:
                    self.debug("Kicking all out!")
                    while (not self.locator.locate('one_person')) and self.running:
                        self.locator.locate_and_click('kick_out')
                        self.locator.locate_and_click('expel')
                    self.init_time()
            self.debug("\n'Auto' is located. In battle stage")
            start_time = time.time()
            while (not self.locator.locate('next')) and self.running:
                self.locator.locate_and_click('ok')
                self.locator.locate_and_click('ok2')
                self.locator.locate_and_click('give_up')
                if self.locator.locate_and_click('yes'):
                    break
                time.sleep(1)
            # after battle stage
            self.debug("After battle stage")
            elapsed_time = time.time() - start_time
            self.log(f"Elapsed_time: {time.strftime('%M:%S', time.gmtime(elapsed_time))}")
            while (not self.locator.locate('organize')) and self.running:
                self.locator.locate_and_click('next')
                # self.my_locator.locate_and_click('ok')
                self.locator.locate_and_click('cancel')
                self.locator.locate_and_click('go_back')
            if not self.running:
                self.log("Quit automation")
                break
            self.log(f"Completed: {cnt+1} times")
        if (finish_button != None) and self.running:
            finish_button.click()
    def play_multi_client(self, rep_time, finish_button=None):
        self.set_params('play_multi_client')
        self.running = True
        # multi auto play
        self.locator.confidence = 0.90
        self.time_limit = 300
        self.log("Starting multi_client automation")
        targets = [
            "cancel", "go_back", "next", "ok", "ready"
        ]
        while self.running:
            self.locator.locate_and_click(targets)
            time.sleep(1)
    def play_raid(self, rep_time, num_of_players, finish_button=None):
        self.set_params('play_raid')
        self.running = True
        # raid auto play
        self.locator.confidence = 0.90
        self.time_limit = 300
        self.log("Starting raid automation")
        self.log(f"path: {self.automation_path}")
        cnt = 0
        while self.running:
            self.debug("In play_raid, location A")
            # while not self.my_locator.locate('auto'):
            while (self.locator.locate('auto') == None) and self.running:
                self.locator.locate_and_click('sortie')
                self.locator.locate_and_click('next_raid')
                self.locator.locate_and_click('next')
                self.locator.locate_and_click('end_of_quest')
                self.locator.locate_and_click('try')
                self.locator.locate_and_click('ok')
            self.log("In battle stage.")
            while (not self.locator.locate('end_of_quest')) and self.running:
                pass
            cnt += 1
            self.log(f"Completed {cnt} times. {rep_time-cnt} times left.")
    def play_raid_host2(self, rep_time, finish_button=None):
        self.set_params("play_raid_host2")
        self.running = True
        # raid auto play
        self.locator.confidence = 0.90
        self.time_limit = 300
        self.log("Starting raid host2 automation")
        self.log(f"path: {self.automation_path}")
        cnt = 0
        while self.running:
            targets = [
                       "sortie"
            ]
            while (not self.locator.locate("auto")) and self.running:
                if self.locator.locate("checking_the_result"):
                    self.locator.locate_and_click(targets)
            self.debug("In battle stage")
            start_time = time.time()

            while (not self.locator.locate("next")) and self.running:
                time.sleep(1)
            elasped_time = time.time() - start_time
            cnt += 1
            self.debug(f"Battle completed {cnt} times. {rep_time-cnt} left.")
            self.debug(f"Elasped_time: {time.strftime('%M:%S', time.gmtime(elasped_time))}")
            targets = ["next", "end_of_quest", "ok", "next_raid", "try"]
            while (not self.locator.locate("sortie")) and self.running:
                self.locator.locate_and_click(targets)
                time.sleep(1)
    def play_raid_host4(self):
        self.running = True
        # raid auto play
        self.log("Starting raid host4 automation")
        self.log(f"path: {self.automation_path}")
        cnt = 0
        while self.running:
            targets = ["sortie"]
            targets2 = ["help", "send_help", "ok", 'ok2']
            while (not self.locator.locate("auto")) and self.running:
                self.locator.locate_and_click(targets2)
                if self.locator.locate("4_people"):
                    self.locator.locate_and_click(targets)
            self.debug("In battle stage")
            self.stop_watch()
            while (not self.locator.locate("next")) and self.running:
                time.sleep(2)
            self.debug("Battle Ended")
            cnt += 1
            self.log(f"Completed {cnt} times. {self.rep_time - cnt} remains.")
            self.stop_watch()
            targets = ["end_of_quest", "next", "next_raid", "ok", "ok2", "try", "cancel", "4_people_room", "create_room"]
            while (not self.locator.locate("sortie")) and self.running:
                self.locator.locate_and_click(targets)
    def play_raid_client(self):
        self.running = True
        # raid auto play
        self.locator.confidence = 0.90
        self.time_limit = 300
        self.log("Starting raid client automation")
        self.log(f"path: {self.automation_path}")
        cnt = 0
        while self.running:
            pass
            targets = ["ready", "try"]
            while (not self.locator.locate("auto")) and self.running:
                self.locator.locate_and_click(targets)
            self.debug("In battle stage")
            start_time = time.time()
            while (not self.locator.locate("next")) and self.running:
                time.sleep(2)
            self.debug("Battle Ended")
            elap_time = time.time() - start_time
            self.log(f"Completed {cnt} times. {self.rep_time - cnt} remains.")
            self.log(f"Elasped_time: {time.strftime('%M:%S', time.gmtime(elap_time))}")
            targets = ["end_of_quest", "next", "next_raid", "ok", "try", "cancel"]
            while (not self.locator.locate("ready")) and self.running:
                self.locator.locate_and_click(targets)
    def summon(self, rep_time, finish_button = None):
        self.running = True
        # multi auto play
        self.locator.confidence = 0.95
        self.time_limit = 300
        self.log("Starting summon automation")
        summon_cnt = 0
        while self.running:
            print(not self.locator.locate('confirm_summon'))
            while (not self.locator.locate('confirm_summon')) and self.running:
                print("In while loop")
                self.locator.locate_and_click('ok')
                self.locator.locate_and_click('once_again')
                self.locator.locate_and_click('skip')
            if self.locator.locate_and_click('confirm_summon'):
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
    def stop_watch(self):
        if self.stop_watch_started == False:
            self.start_time = time.time()
            self.stop_watch_started = True
        else:
            self.log(f"Elasped_time: {time.strftime('%M:%S', time.gmtime(self.elasped_time()))}")
            self.stop_watch_started = False