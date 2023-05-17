import win32gui
import win32con
import time
import datetime
import locator
from ppadb.client import Client as AdbClient
import threading
class Automator:
    def __init__(self, window_name:str, device_type:str=None, job=None, log=print, debug=print, error=print):
        self.log = log
        self.debug = debug
        self.error = error

        self.debug("Creating Automator.")
        self.init_device(window_name=window_name)
        self.device_type = device_type
        self.job = job
        self.init_int_vars()
        self.init_other()
        # self.set_params(automation_name)
    def set_automation_list(self):
        # Need to add code when add new automation
        self.automation_by_job = {}
        self.automation_by_job['play_quest'] = self.play_quest
        self.automation_by_job['play_multi'] = self.play_multi
        self.automation_by_job['play_multi_client'] = self.play_multi_client
        self.automation_by_job['play_raid'] = self.play_raid
        self.automation_by_job['play_raid_host2'] = self.play_raid_host2
        self.automation_by_job['play_raid_host4'] = self.play_raid_host4
        self.automation_by_job['play_raid_client'] = self.play_raid_client
        self.automation_by_job['play_summon'] = self.summon
        self.automation_by_job['play_skip_battle'] = self.skip_battle
        # self.automation_by_job[''] = self.
    def init_int_vars(self):
        self.confidence = 0.9
    def init_other(self):
        self.stop_watch_started = False
        self.set_automation_list()
    def init_device(self, window_name:str=None):
        self.my_client = AdbClient()
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
        self.debug(f"With window name {window_name}, found device: {self.my_device} and hwnd: {self.my_hwnd}.")

    def set_img_base_path(self):
        device_type = self.device_type
        self.debug("--In set_params--")
        if device_type == 'nox_1920_1080':
            self.automation_path = './1920_1080/'
        elif device_type == 'nox_1280_720':
            self.automation_path = './1280_720/'
        elif device_type == 'android':
            self.automation_path = './1280_720/'
        else:
            self.error(f"No such device type: {device_type}")
            return False
        return True
    def init_locator(self):
        self.debug("Starting: def init_locator")
        job = self.job
        self.automation_path += job.replace('play_', '')
        self.debug(f"Locator Path: {self.automation_path}")
        self.locator = locator.Locator(self.my_hwnd, self.automation_path)
        self.locator.load_conf(self.device_type)
        self.locator.confidence = self.confidence
        self.time_limit = 300
        self.locator.connect_click_method(self.my_device.input_tap)
    def start_automation(self):
        # Suppose all variables in fit.
        self.debug(f"Starting: def start_automation. Job: {self.job}")
        self.set_img_base_path()
        self.init_locator()
        job = self.job
        # Need to add code to handle special case
        self.automation_by_job[job]()
    def set_user_params(self, rep_time, num_of_players, finish_button):
        self.rep_time = rep_time
        self.num_of_players = num_of_players
        self.finish_button = finish_button
    def stop(self):
        self.running = False
    def elasped_time(self):
        return time.time() - self.start_time
    def init_time(self):
        self.start_time = time.time()
    def stop_watch(self):
        if self.stop_watch_started == False:
            self.init_time()
            self.stop_watch_started = True
        else:
            self.log(f"Elasped_time: {time.strftime('%M:%S', time.gmtime(self.elasped_time()))}")
            self.stop_watch_started = False
    def play_quest(self):
        self.running = True
        self.log(f"Starting quest automation.")
        rep_time = self.rep_time
        finish_button = self.finish_button
        targets = ["select_chapter", "an_alchemist_of_steel", "light_stone"]
        for cnt in range(rep_time):
            # 퀘스트 자동 진행
            self.debug("Before battle, trying to click sortie")
            while (self.locator.locate('sortie') == None) and self.running:
                self.locator.locate_and_click(targets, xy='top_quest')
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
            while (self.locator.locate(targets, trial_number=2) == None) and self.running:
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
    def play_multi(self):
        rep_time = self.rep_time
        num_of_players = self.num_of_players
        finish_button = self.finish_button
        self.running = True
        self.time_limit = 300
        self.log("Starting multi automation")
        for cnt in range(rep_time):
            self.stop_watch()
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
            while (not self.locator.locate('next')) and self.running:
                self.locator.locate_and_click('ok')
                self.locator.locate_and_click('ok2')
                self.locator.locate_and_click('give_up')
                if self.locator.locate_and_click('yes'):
                    break
                time.sleep(1)
            # after battle stage
            self.debug("After battle stage")
            self.stop_watch()
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
    def play_multi_client(self):
        self.running = True
        self.time_limit = 300
        self.log("Starting multi_client automation")
        targets = ["cancel", "go_back", "next", "ok", "ready"]
        while self.running:
            self.locator.locate_and_click(targets)
            time.sleep(1)
    def play_raid(self):
        rep_time = self.rep_time
        self.running = True
        self.log("Starting single raid automation")
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
    def play_raid_host2(self):
        rep_time = self.rep_time
        self.running = True
        self.log("Starting raid host2 automation")
        self.log(f"path: {self.automation_path}")
        cnt = 0
        while self.running:
            targets = ["sortie"]
            while (not self.locator.locate("auto")) and self.running:
                if self.locator.locate("checking_the_result"):
                    self.locator.locate_and_click(targets)
            self.debug("In battle stage")
            self.stop_watch()

            while (not self.locator.locate("next")) and self.running:
                time.sleep(1)
            cnt += 1
            self.debug(f"Battle completed {cnt} times. {rep_time-cnt} left.")
            self.stop_watch()
            targets = ["next", "end_of_quest", "ok", "next_raid", "try"]
            while (not self.locator.locate("sortie")) and self.running:
                self.locator.locate_and_click(targets)
                time.sleep(1)
    def play_raid_host4(self):
        self.running = True
        self.locator.confidence = 0.95
        self.log("Starting raid host4 automation")
        self.log(f"path: {self.automation_path}")
        cnt = 0
        while self.running:
            targets = ["sortie"]
            targets2 = ["help", "send_help", "ok", 'ok2']
            while (not self.locator.locate("auto")) and self.running:
                self.locator.locate_and_click(targets2)
                if self.num_of_players == 3:
                    if self.locator.locate("more_than_3"):
                        self.locator.locate_and_click(targets)
                else:
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
            targets = ["end_of_quest", "next", "next_raid", "ok", "ok2", "try", "cancel", "4_people_room", "create_room", 'cancel2']
            while (not self.locator.locate("sortie")) and self.running:
                self.locator.locate_and_click(targets)
    def play_raid_client(self):
        self.running = True
        self.log("Starting raid client automation")
        self.log(f"path: {self.automation_path}")
        cnt = 0
        while self.running:
            pass
            targets = ["ready", "try"]
            while (not self.locator.locate("auto")) and self.running:
                self.locator.locate_and_click(targets)
            self.debug("In battle stage")
            self.stop_watch()
            while (not self.locator.locate("next")) and self.running:
                time.sleep(2)
            self.debug("Battle Ended")
            cnt += 1
            self.log(f"Completed {cnt} times. {self.rep_time - cnt} remains.")
            self.stop_watch()
            targets = ["end_of_quest", "next", "next_raid", "ok", 'ok2', "try", "cancel"]
            while (not self.locator.locate("ready")) and self.running:
                self.locator.locate_and_click(targets)
                time.sleep(1.5)
    def summon(self):
        rep_time = self.rep_time
        finish_button = self.finish_button
        self.running = True
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
    def skip_battle(self):
        self.running = True
        self.log("Starting skip battle automation")
        self.log(f"path: {self.automation_path}")
        rep_time = self.rep_time
        cnt = 0
        while self.running:
            targets = ["skip_battle", "decide"]
            while (not self.locator.locate("ok")) and self.running:
                self.locator.locate_and_click(targets)
            cnt += 1
            self.debug(f"Battle Skipped. {cnt} times. {rep_time-cnt} left.")
            targets2 = ["x", "ok", "ok2", "next", "end_of_quest", ]
            while (not self.locator.locate("skip_battle")) and self.running:
                self.locator.locate_and_click(targets2)
            if cnt >= rep_time:
                break
