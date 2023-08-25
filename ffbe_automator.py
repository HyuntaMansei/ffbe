import win32gui
import win32con
import time
import datetime
import locator
from ppadb.client import Client as AdbClient
import inspect
import threading
import os
import re
class Timer:
    def __init__(self):
        self.is_running = False
        self.elap_times = []
        self.start_time = None

    def click(self):
        if self.is_running == True:
            elap_time = time.time() - self.start_time
            self.elap_times.append(elap_time)
            return elap_time
        else:
            self.is_running = True
            self.start_time = time.time()

    def restart(self):
        self.is_running = True
        self.elap_times = []
        self.start_time = time.time()
class Automator:
    def __init__(self):
        print("Creating Automator.")
        self.log = print
        self.debug = print
        self.error = print
        self.init_internal_vars()
        self.init_other()
        # Define all internal variables
        self.device_type = None
        self.job = None
        self.running = False
        self.keep_click_running = False
        self.stop_keep_click_index = 1
        print("Automator has made.")
    def set_msg_handlers(self, log=print, debug=print, error=print):
        self.log = log
        self.debug = debug
        self.error = error
    def set_window_and_device(self, window_name: str, window_hwnd: str = None, device_type: str = None,
                              device_serial: str = None):
        print("In def, set_window_and_device")
        self.device_type = device_type
        self.init_device(window_name=window_name, window_hwnd=window_hwnd, device_serial=device_serial)
    def set_job(self, job=None):
        self.job = job

    def set_user_params(self, rep_time, num_of_players, finish_button, sleep_multiple=5):
        print("In def, set_user_params", end='')
        self.rep_time = rep_time
        self.num_of_players = num_of_players
        self.finish_button = finish_button
        self.sleep_mul = sleep_multiple
        print(" >> Finished.")

    def init_automation_list(self):
        # Need to add code when add new automation
        self.automation_by_job = {}
        # Get all the methods of the class
        methods = inspect.getmembers(self, predicate=inspect.ismethod)
        # Extract the names of the methods
        method_names = [name for name, _ in methods]
        # match 'play_quest' > self.play_quest / 'summon' > self.summon
        for m in method_names:
            if 'play' == m.split('_')[0]:
                self.automation_by_job[m] = getattr(self, m)
                self.automation_by_job[m[5:]] = getattr(self, m)
            else:
                self.automation_by_job['play_' + m] = getattr(self, m)
                self.automation_by_job[m] = getattr(self, m)

    def init_device(self, window_name: str = None, window_hwnd: str = None, device_serial: str = None):
        print(f"In def, init_device")
        if window_hwnd:
            self.my_hwnd = int(window_hwnd)
        else:
            self.my_hwnd = win32gui.FindWindow(None, window_name)
        self.my_device = None
        if not "gpg" in self.device_type.lower():
            self.my_client = AdbClient()
            for dev in self.my_client.devices():
                # Get the device properties
                device_name = dev.get_properties()["ro.product.model"].strip()
                # Retrieve the device name
                if device_name == window_name:
                    if device_serial:
                        # print(f"{device_serial} and {dev.serial}")
                        if device_serial == dev.serial:
                            self.my_device = dev
                            # self.sc_off()
                            break
                    else:
                        pass
                        # self.my_device = dev
                # self.my_device = self.my_client.devices()[0]
        else:
            # When device is Google Play Games
            print(self.device_type, " - Nothing to Init.")
            self.my_device = "GPG"
        self.debug(f"With window name {window_name}, found device: {self.my_device} and hwnd: {self.my_hwnd}.")

    def init_internal_vars(self):
        self.confidence = 0.95
        self.sleep_mul = 5

    def init_other(self):
        self.stop_watch_started = False
        self.init_automation_list()
        self.timer = Timer()
        self.limit_timer = Timer()

    # From here, called from start_automation
    def set_img_base_path(self):
        device_type = self.device_type
        self.debug("--In set_params--")
        self.automation_path = './a_orders/'
        if device_type == 'nox_1920_1080':
            self.img_path = './images/1920_1080/'
        elif device_type == 'nox_1280_720':
            self.img_path = './images/1280_720/'
        elif device_type == 'android':
            self.img_path = './images/1280_720/'
        elif device_type == 'android_q2':
            self.img_path = './images/1600_720/'
        elif device_type == 'blue_1280_720':
            self.img_path = './images/1280_720_blue/'
        elif device_type == 'gpg_3840_2160':
            self.img_path = './images/3840_2160/'
        elif device_type == 'gpg_1920_1080':
            self.img_path = './images/1920_1080/'
        else:
            self.error(f"No such device type: {device_type}")
            return False
        return True

    def create_locator(self):
        self.debug("Starting: def init_locator")
        job = self.job

        if 'gpg' in self.device_type:
            _,_,w,h = win32gui.GetClientRect(self.my_hwnd)
            img_path = f"./images/{w}_{h}"
            if os.path.isdir(img_path):
                self.img_path = img_path
                print(f"New image path as {self.img_path}")
            else:
                print(f"Error!! No image path for {img_path}")
        self.automation_path = os.path.join(self.automation_path, job.replace('play_', ''))
        self.locator = locator.Locator(self.my_hwnd, self.automation_path, self.img_path, error=self.error)
        self.locator.load_conf(self.device_type)
        self.locator.confidence = self.confidence
        self.time_limit = 300
        if not 'gpg' in self.device_type:
            self.locator.connect_click_method(self.my_device.input_tap)

    def start_automation(self):
        # Suppose all variables in fit.
        self.debug(f"Starting: def start_automation. Job: {self.job}")
        self.set_img_base_path()
        self.create_locator()
        job = self.job
        # Need to add code to handle special case
        self.pre_automation_processing()
        self.automation_by_job[job]()

    def stop(self):
        self.running = False

    def elapsed_time(self):
        return time.time() - self.start_time

    def init_time(self):
        self.start_time = time.time()

    def stop_watch(self):
        if self.stop_watch_started == False:
            self.init_time()
            self.stop_watch_started = True
        else:
            self.log(f"Elapsed_time: {time.strftime('%M:%S', time.gmtime(self.elapsed_time()))}")
            self.stop_watch_started = False

    # From here, specific automation
    def play_quest(self):
        self.running = True
        self.locator.confidence = 0.90
        self.log(f"Starting quest automation.")
        rep_time = self.rep_time
        finish_button = self.finish_button
        is_imgs = ["common", "select_chapter"]
        self.start_keep_clicks()
        cnt = 0
        while self.running:
            # 퀘스트 자동 진행
            self.debug("Before battle, trying to click sortie")
            while (not self.locator.locate('auto')) and self.running:
                if self.locator.locate(is_imgs):
                    if self.locator.locate('scene3_selected'):
                        self.locator.click(xy='top_quest')
                        time.sleep(2)
                    elif self.locator.locate_and_click('scene3_unselected'):
                        time.sleep(2)
                        self.locator.click(xy='top_quest')
                        time.sleep(2)
                    elif self.locator.locate_and_click('scene2_unselected'):
                        time.sleep(2)
                        self.locator.click(xy='top_quest')
                        time.sleep(2)
                if self.locator.locate_and_click(is_imgs, target='top_quest'):
                    time.sleep(4)
                time.sleep(1)
                if not self.locator.locate(['sortie', 'sortie_eq', 'common', 'select_party']):
                    self.locator.click('story_skip1')
                    time.sleep(5)
            self.debug("In battle stage")
            self.stop_watch()
            while (not self.locator.locate('end_of_quest')) and self.running:
                time.sleep(5)
            self.debug("Battle Ended.")
            self.debug("The quest ended")
            self.debug(f"After battle, until 'select chapter', repeating, ... story skip")
            while ((not self.locator.locate(is_imgs)) and not self.locator.locate('sortie', 'sortie_eq')) and self.running:
                self.locator.locate_and_click('end_of_quest')
                if not self.locator.locate(is_imgs):
                    self.locator.click('story_skip1')
                    time.sleep(5)
            cnt += 1
            self.log(f"Completed: {cnt} and {rep_time - cnt} left.")
            self.stop_watch()
            if cnt >= rep_time:
                break
        if (finish_button != None) and self.running:
            self.log("Automaiton completed.")
            finish_button.click()
        self.debug("Quit automation.")
    def play_quest_with_different_party(self):
        self.running = True
        self.locator.confidence = 0.95
        self.log(f"Starting quest automation with different party.")
        rep_time = self.rep_time
        finish_button = self.finish_button
        self.start_keep_clicks()
        cnt = 0
        while self.running:
            # 퀘스트 자동 진행
            self.debug("Before battle, trying to click sortie")
            sorties = ["sortie", "sortie_quest", "sortie_eq", "sortie_12", "sortie_confirm"]
            while (not self.locator.locate('auto')) and self.running:
                # 처음시작에는 현재 파티 그대로. 전투 끝난 후에는 파티를 한번 변경해 준다.
                self.locator.locate_and_click(sorties)
                if not self.locator.locate(['sortie', 'sortie_eq', 'common', 'select_chapter', 'select_party']):
                    self.locator.click('story_skip1')
                    time.sleep(5)
            self.debug("In battle stage")
            self.stop_watch()
            while (not self.locator.locate('end_of_quest')) and self.running:
                time.sleep(5)
            self.debug("The Quest ended")
            self.debug(f"After battle, until 'select chapter', repeating, ... story skip")
            while (not self.locator.locate(sorties)) and self.running:
                self.locator.locate_and_click('back_to_sortie')
                if not self.locator.locate(['sortie', 'sortie_eq', 'common', 'select_chapter', 'select_party']):
                    self.locator.click('story_skip1')
                    time.sleep(5)
            cnt += 1
            self.log(f"Completed: {cnt} and {rep_time - cnt} left.")
            self.stop_watch()
            if cnt >= rep_time:
                break

            # Change party
            self.debug("Select next party")
            select_next_parties = ["select_next_party", "select_next_party_quest", "select_next_party_eq"]
            time.sleep(5)
            while (not self.locator.locate("select_party_scroll")) and self.running:
                self.debug("Selecting party button")
                self.locator.locate_and_click(["select_party", "select_party_quest"])
                time.sleep(2)
            time.sleep(3)
            while (not self.locator.locate_and_click(select_next_parties)) and self.running:
                self.debug("Selecting next party")
                time.sleep(1)
            self.debug("Next party selected")
            time.sleep(3)

        if (finish_button != None) and self.running:
            self.log("Automaiton completed.")
            finish_button.click()
        self.debug("Quit automation.")
    def play_multi(self):
        self.locator.confidence = 0.90
        rep_time = self.rep_time
        num_of_players = self.num_of_players
        finish_button = self.finish_button
        self.running = True
        self.time_limit = 1200
        self.log("Starting multi automation")
        cnt = 0

        self.start_keep_clicks()

        sorties = ['sortie','sortie_6','sortie_12','sortie_18','sortie_multi']
        while self.running:
            self.init_time()
            self.debug(f"Before battle stage.")
            while (not self.locator.locate('auto')) and self.running:
                num_of_party = None
                # Check the number of party.
                if self.locator.locate("party_four"):
                    num_of_party = 4
                elif self.locator.locate("party_three"):
                    num_of_party = 3
                elif self.locator.locate("party_two"):
                    num_of_party = 2
                else:
                    num_of_party = 1
                if num_of_party >= num_of_players:
                    self.debug(
                        f"Trying to click sortie, # of players: {num_of_players}, elap. time: {int(self.elapsed_time())} sec")
                    self.locator.locate_and_click(sorties)
                if (self.elapsed_time() > 180) and (self.locator.get_path("checking_the_result")):
                    while (self.locator.locate('checking_the_result')) and self.running:
                        self.debug("Kicking some checking the result!")
                        if self.locator.locate_and_click('checking_the_result'):
                            while True:
                                time.sleep(1)
                                self.locator.locate_and_click('expel')
                                time.sleep(1)
                                if (not self.locator.locate('expel')) and (
                                not self.locator.locate('checking_the_result')):
                                    break
                            self.init_time()
                if (self.elapsed_time() > self.time_limit) and (self.locator.get_path("kick_out")):
                    self.debug("Kicking all out!")
                    while (not self.locator.locate('party_one')) and self.running:
                        self.locator.locate_and_click('kick_out')
                        self.locator.locate_and_click('expel')
                    self.init_time()
                # Recover Stamina if needed
                if self.locator.locate(['short_of_stamina', 'item']):
                    self.recover_stamina()
                time.sleep(self.sleep_mul)
            self.debug("\n'Auto' is located. In battle stage")
            self.timer.restart()
            targets = ['organize']
            while (not self.locator.locate(targets)) and self.running:
                time.sleep(self.sleep_mul * 5)
            # after battle stage
            self.debug("After battle stage")
            cnt += 1
            self.log(f"Completed: {cnt} and {rep_time - cnt} left.")
            self.log(f"Elapsed_time: {time.strftime('%M:%S', time.gmtime(self.timer.click()))}")
            if not self.running:
                self.log("Aborting automation")
                break
            if cnt >= rep_time:
                self.log("Automation completed. Exiting.")
                finish_button.click()
                break
    def play_multi_client(self):
        self.running = True
        cnt = 0
        self.log("Starting multi_client automation")
        self.start_keep_clicks()
        targets = ["cancel_ready", "exit_room"]
        while self.running:
            self.timer.restart()
            while (not self.locator.locate('auto')) and self.running:
                time.sleep(10)
            self.debug("In battle stage.")
            while (not self.locator.locate('cancel_ready')) and self.running:
                time.sleep(10)
            cnt += 1
            self.debug("After battle stage.")
            self.log(f"Completed {cnt} times.")
    def play_multi_client_any(self):
        self.running = True
        cnt = 0
        self.log("Starting multi_client automation")
        self.start_keep_clicks()
        cnt = 0
        exit_targets = ['cancel_ready','exit_room','ok','ok_multi','x','x_multi','next']
        exit_finish = ['refresh','recruit_list', 'auto', 'cancel', 'cancel_multi']
        while self.running:
            self.timer.restart()
            self.limit_timer.restart()
            while (not self.locator.locate('auto')) and self.running:
                time.sleep(10)
                limit_time = int(self.limit_timer.click())
                print(f"Limit_timer: {limit_time}")
                if limit_time > 600:
                    self.debug("In exit code")
                    self.stop_keep_click()
                    while (not self.locator.locate(exit_finish)) and (not self.locator.locate('auto')) and self.running:
                        self.locator.locate_and_click(exit_targets)
                        time.sleep(3)
                    self.start_keep_click()
                    self.limit_timer.restart()
            self.debug("In battle stage.")
            while (not self.locator.locate('cancel_ready')) and self.running:
                time.sleep(10)
            cnt += 1
            self.debug("After battle stage.")
            self.log(f"Completed {cnt} times.")
    def play_hardship(self):
        self.locator.confidence = 0.98
        rep_time = self.rep_time
        num_of_players = self.num_of_players
        finish_button = self.finish_button
        self.running = True
        self.time_limit = 1200
        self.log("Starting hardship automation")
        cnt = 0

        self.start_keep_clicks()

        sorties = ['sortie', 'sortie2', 'sortie3']
        autos = ['auto', 'auto_hardship']
        while True:
            self.timer.restart()
            self.debug(f"Before battle stage.")
            while (not self.locator.locate('companion')) and self.running:
                time.sleep(5)
            self.debug(f"Companion located.")
            while (not self.locator.locate(autos)) and self.running:
                print("Trying to locating auto")
                if not self.locator.locate('no_companion'):
                    self.locator.locate_and_click(sorties)
                time.sleep(4)
            self.debug("Auto located. In battle stage")
            while (not self.locator.locate('back_to_sortie_sc')) and self.running:
                self.locator.locate_and_click(sorties)
                time.sleep(5)
            # after battle stage
            self.debug("After battle stage")
            cnt += 1
            self.log(f"Completed: {cnt} and {rep_time - cnt} left.")
            self.log(f"Elapsed_time: {time.strftime('%M:%S', time.gmtime(self.timer.click()))}")
            while (not self.locator.locate(sorties)) and self.running:
                self.locator.locate_and_click('back_to_sortie_sc')
                time.sleep(2)
            if not self.running:
                self.log("Aborting automation")
                break
            if cnt >= rep_time:
                self.log("Automation completed. Exiting.")
                finish_button.click()
                break
    def play_raid(self):
        self.pre_automation_processing()
        self.locator.confidence = 0.98
        rep_time = self.rep_time
        num_of_players = self.num_of_players
        finish_button = self.finish_button
        self.running = True
        self.time_limit = 600
        self.log("Starting solo RAID automation")
        self.log(f"path: {self.automation_path}")

        self.start_keep_clicks()

        cnt = 0
        while self.running:
            self.debug("In play_raid, location A")
            # while not self.my_locator.locate('auto'):
            while (not self.locator.locate('auto')) and self.running:
                self.locator.locate_and_click('challenge')
                if self.locator.locate('get_reward'):
                    finish_button.click()
                    self.log(f"Automation completed.")
                    break
                time.sleep(5)
            self.log("In battle stage.")
            self.timer.restart()
            while (not self.locator.locate('challenge')) and self.running:
                time.sleep(5)
            cnt += 1
            self.log(f"Completed {cnt} and {rep_time - cnt} left.")
            self.log(f"Elapsed_time: {time.strftime('%M:%S', time.gmtime(self.timer.click()))}")
            if not self.running:
                self.log("Aborting automation")
                break
            if cnt >= rep_time:
                self.log(f"Automation completed.")
                finish_button.click()
                break
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
            self.debug(f"Battle completed {cnt} times. {rep_time - cnt} left.")
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
            targets = ["end_of_quest", "next", "next_raid", "ok", "ok2", "try", "cancel", "4_people_room",
                       "create_room", 'cancel2']
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
    def play_100tower(self):
        self.running = True
        self.locator.confidence = 0.95
        finish_button = self.finish_button
        self.log("Starting 100 tower automation")
        targets = ["end_of_quest"]
        self.start_keep_clicks()
        rep_time = self.rep_time
        cnt = 0
        while self.running:
            self.debug("Before battle stage")
            while self.running and (not self.locator.locate("auto")):
                self.locator.locate_and_click(targets)
                time.sleep(1)
            self.debug("In battle stage")
            self.timer.restart()
            while self.running and (not self.locator.locate("end_of_quest")):
                time.sleep(1)
            self.debug("After battle stage")
            cnt += 1
            self.log(f"Completed {cnt} and left {rep_time - cnt} times")
            self.log(f"Elapsed_time: {time.strftime('%M:%S', time.gmtime(self.timer.click()))}")
            while self.running and (not self.locator.locate("sortie2")):
                self.locator.locate_and_click('end_of_quest')
                time.sleep(1)
            if cnt >= rep_time and self.running:
                self.log("Automation completed. Exit now.")
                finish_button.click()
                break
    def summon(self):
        rep_time = self.rep_time
        finish_button = self.finish_button
        self.running = True
        self.log("Starting summon automation")
        cnt = 0
        while self.running:
            print(not self.locator.locate('confirm_summon'))
            while (not self.locator.locate('confirm_summon')) and self.running:
                print("In while loop")
                self.locator.locate_and_click('ok')
                self.locator.locate_and_click('once_again')
                self.locator.locate_and_click('skip')
            if self.locator.locate_and_click('confirm_summon'):
                cnt += 1
                self.log(f"Summon Completed {cnt} times. {rep_time - cnt} times left.")
            if cnt >= rep_time:
                break
        if (finish_button != None) and self.running:
            finish_button.click()
    def skip_battle(self):
        self.pre_automation_processing()
        self.locator.confidence = 0.98
        rep_time = self.rep_time
        num_of_players = self.num_of_players
        finish_button = self.finish_button
        self.running = True
        self.time_limit = 600
        self.log("Starting solo RAID automation")
        self.log(f"path: {self.automation_path}")

        self.start_keep_clicks()

        self.log("Starting skip battle automation")
        self.log(f"path: {self.automation_path}")
        cnt = 0
        while self.running:
            targets = ["skip_battle"]
            while (not self.locator.locate("end_of_quest")) and self.running:
                self.locator.locate_and_click(targets)
                time.sleep(3)
            cnt += 1
            self.log(f"Battle Skipped. {cnt} times. {rep_time - cnt} left.")
            targets2 = ["end_of_quest"]
            while (not self.locator.locate("skip_battle")) and self.running:
                self.locator.locate_and_click(targets2)
                time.sleep(3)
            if cnt >= rep_time:
                self.log("Automation Completed.")
                # self.running = False
                finish_button.click()
                break
    def recover_stamina(self, recover_cnt=8):
        # Recovering
        self.debug("Start recovering stamina")
        targets = ['yes', 'item']
        self.stop_keep_click()
        time.sleep(1)
        while (not self.locator.locate('recover_amount')) and self.running:
            self.locator.locate_and_click(targets)
            time.sleep(0.5)
        time.sleep(2)
        # self.debug("Trying to swipe up")
        # self.my_device.shell("input swipe 900 600 900 300 1000")
        # time.sleep(2)
        for cnt in range(recover_cnt):
            self.locator.locate_and_click('120')
            time.sleep(0.5)
        # while (not self.locator.locate('sortie')) and self.running:
        recover_targets = ["recover", "ok_recover"]
        for c in range(10):
            if self.locator.locate('dismiss') or (not self.running):
                break
            self.locator.locate_and_click(recover_targets)
            time.sleep(1)
        self.debug("Finished recovering")
        self.start_keep_click()
    def sc_off(self):
        self.my_device.shell("settings put system screen_brightness 0")
    def test(self):
        self.running = True
        cnt = 0
        self.log("Testing!!")
        targets = []
        self.start_keep_clicks()

        while self.running:
            self.locator.locate_and_click(targets)
            time.sleep(1)
    def list_all_methos(self):
        # Get all the methods of the class
        methods = inspect.getmembers(self, predicate=inspect.ismethod)
        # Extract the names of the methods
        method_names = [name for name, _ in methods]
        print(method_names)
    def pre_automation_processing(self):
        win32gui.SetForegroundWindow(self.my_hwnd)
    def keep_click(self, target_dir: str = None, sleep_time=None, keep_awake=False):
        if target_dir == None:
            target_dir = 'kc'
        if sleep_time == None:
            sleep_time = 1
        self.debug(f"Func, keep_click, starts now. Img_dir: {os.path.join(self.automation_path, target_dir)}")
        locator_kc = locator.Locator(self.my_hwnd, self.automation_path, self.img_path, error=self.error)
        locator_kc.load_conf(self.device_type)
        locator_kc.confidence = self.confidence
        if not 'gpg' in self.device_type:
            locator_kc.connect_click_method(self.my_device.input_tap)
        while self.running:
            if self.keep_click_running or keep_awake:
                result = locator_kc.locate_and_click_all_dir(target_dir)
                if result:
                    print(f"Successfully clicked for {target_dir}")
                for i in range(int(sleep_time)):
                    time.sleep(1)
                    if not self.running:
                        break
            else:
                print(f"Skip keep_click loop for {target_dir}")
                for i in range(5 * int(sleep_time)):
                    time.sleep(1)
                    if not self.running:
                        break
    def keep_click_on_text(self, target_list, sleep_time=None, keep_awake=False):
        if sleep_time == None:
            sleep_time = 1
        locator_kc = locator.Locator(self.my_hwnd, self.automation_path, self.img_path, error=self.error)
        locator_kc.load_conf(self.device_type)
        locator_kc.confidence = self.confidence
        if not 'gpg' in self.device_type:
            pass
            locator_kc.connect_click_method(self.my_device.input_tap)
        while self.running:
            time.sleep(10)
            if self.keep_click_running or keep_awake:
                for target in target_list:
                    result = locator_kc.locate_and_click(target)
                    if result:
                        print(f"Successfully clicked for {target} by keep click with SleepTime: {sleep_time}")
                for i in range(int(sleep_time)):
                    time.sleep(1)
                    if not self.running:
                        break
            else:
                print(f"Skip keep_click loop for {target_list} sleep time: {sleep_time}")
                for i in range(5 * int(sleep_time)):
                    time.sleep(1)
                    if not self.running:
                        break
    def keep_click_conditional(self, target_list, start_list, finish_list, sleep_time=None):
        if sleep_time == None:
            sleep_time = 1
        locator_kc = locator.Locator(self.my_hwnd, self.automation_path, self.img_path,
                                     error=self.error)
        locator_kc.load_conf(self.device_type)
        locator_kc.confidence = self.confidence
        if not 'gpg' in self.device_type:
            locator_kc.connect_click_method(self.my_device.input_tap)
        while self.running:
            if locator_kc.locate(start_list):
                self.debug(f"Keep_click_conditional:{start_list} with {sleep_time} sl_time in operation. Stop keep_click.")
                print(f"Keep_click_conditional:{start_list} with {sleep_time} sl_time in operation. Stop keep_click.")
                self.stop_keep_click()
                time.sleep(3)
                while self.running and (not locator_kc.locate(finish_list)):
                    print(f"Locating {target_list} in keep_click_conditional")
                    locator_kc.locate_and_click(target_list)
                    time.sleep(sleep_time)
                self.start_keep_click()
                self.debug(
                    f"Keep_click_conditional:{start_list} with {sleep_time} sl_time finished. keep_click_index:{self.stop_keep_click_index}.")
                print(f"Keep_click_conditional:{start_list} with {sleep_time} sl_time finished. keep_click_index:{self.stop_keep_click_index}.")
            time.sleep(sleep_time * 2)
    def keep_click_conditional_backup(self, target_dir: str = 'kc_cond', sleep_time=None):
        if sleep_time == None:
            sleep_time = 1
        locator_kc = locator.Locator(self.my_hwnd, os.path.join(self.automation_path, target_dir), self.img_path,
                                     error=self.error)
        locator_kc.load_conf(self.device_type)
        locator_kc.confidence = self.confidence
        if not 'gpg' in self.device_type:
            locator_kc.connect_click_method(self.my_device.input_tap)
        while self.running:
            if locator_kc.locate_dir('start_cond'):
                self.debug(f"Keep_click_conditional:{target_dir} in operation. Stop keep_click.")
                print(f"Keep_click_conditional:{target_dir} in operation. Stop keep_click.")
                time.sleep(3)
                self.stop_keep_click()
                while self.running and (not locator_kc.locate_dir('finish_cond')):
                    print(f"Locating {locator_kc.img_path} in keep_click_conditional")
                    locator_kc.locate_and_click_all_dir("")
                    time.sleep(sleep_time)
                self.start_keep_click()
                self.debug(
                    f"Keep_click_conditional:{target_dir} finished. keep_click_index:{self.stop_keep_click_index}.")
                print(f"Keep_click_conditional:{target_dir} finished. keep_click_index:{self.stop_keep_click_index}.")
            time.sleep(sleep_time * 2)
    def start_keep_clicks_backup(self, sleep_mul=None):
        if sleep_mul == None:
            if self.sleep_mul != None:
                sleep_mul = self.sleep_mul
            else:
                sleep_mul = 1
        target_thread = self.keep_click
        thread_list = []
        # Specify the directory path
        directory = self.automation_path + '/kc/'
        # Get a list of all subdirectories in the specified directory
        subdirectories = [name for name in os.listdir(directory) if os.path.isdir(os.path.join(directory, name))]
        print(f"Subdirectories: {subdirectories}")
        for s in subdirectories:
            try:
                sd = float(s)
            except Exception as e:
                print(f"Exception: {e} with s in function - start_keep_clicks")
                continue
            if sd != 0:
                thread_list.append(threading.Thread(target=target_thread, args=('kc/' + s, sd * sleep_mul)))
            else:
                thread_list.append(threading.Thread(target=target_thread, args=('kc/' + s, 1 * sleep_mul, True)))
            print(f"Making Keep_click thread for {s} with sleep time: {sd * sleep_mul}")
        if thread_list == []:
            thread_list.append(threading.Thread(target=target_thread, args=('kc', sleep_mul)))
            print(f"Making Keep_click thread as basic directory")
        for t in thread_list:
            t.start()
        self.start_keep_clicks_conditional()
        self.start_keep_click()
    def start_keep_clicks(self, sleep_mul=None):
        pass
        if sleep_mul == None:
            if self.sleep_mul != None:
                sleep_mul = self.sleep_mul
            else:
                sleep_mul = 1
        target_thread = self.keep_click_on_text
        thread_list = []
        # Load kc.txt
        kc_path = os.path.join(self.automation_path, 'kc.txt')
        self.load_kc_from_text(kc_path)
        self.debug(self.kc_list)
        for kc in self.kc_list:
            sd = kc['time']
            if sd != 0:
                thread_list.append(threading.Thread(target=target_thread, args=(kc['targets'], sd * sleep_mul)))
            else:
                thread_list.append(threading.Thread(target=target_thread, args=(kc['targets'], 1 * sleep_mul, True)))
            print(f"Making Keep_click thread for {kc['targets']} with sleep time: {sd * sleep_mul}")
        for t in thread_list:
            t.start()
        self.start_keep_clicks_conditional()
        self.start_keep_click()
    def start_keep_clicks_conditional(self, sleep_mul=None):
        if sleep_mul == None:
            if self.sleep_mul != None:
                sleep_mul = self.sleep_mul
            else:
                sleep_mul = 1
        # Load kc_cond.txt
        kc_cond_path = os.path.join(self.automation_path, 'kc_cond.txt')
        self.load_kc_cond_from_text(kc_cond_path)
        target_thread = self.keep_click_conditional
        thread_list = []
        for kc_cond in self.kc_cond_list:
            sl_time = kc_cond['time']
            target_list = kc_cond['targets']
            start_list = kc_cond['start']
            finish_list = kc_cond['finish']
            thread_list.append(threading.Thread(target=target_thread, args=(target_list, start_list, finish_list, sl_time * sleep_mul)))
            print(f"Making Keep_click_conditional thread for {start_list} with sleep time: {sl_time * sleep_mul}")
        for t in thread_list:
            t.start()
    def stop_keep_click(self):
        self.stop_keep_click_index += 1
        if self.keep_click_running == True:
            self.keep_click_running = False
            print(f"Stopping keep click. stop_keep_click_index={self.stop_keep_click_index}.")
    def start_keep_click(self):
        self.stop_keep_click_index -= 1
        if self.stop_keep_click_index <= 0:
            print(f"Starting keep click. stop_keep_click_index={self.stop_keep_click_index}.")
            self.keep_click_running = True
    def load_kc_from_text(self, file_path):
        path = file_path
        with open(path, 'r') as f:
            lines = f.readlines()
        p = re.compile('\[\d*\]')
        kc_list = []
        img_list = []
        for l in lines:
            m = re.match(p, l)
            if m:
                if img_list:
                    kc_list.append({'time': (int(cur_time)), 'targets': img_list})
                cur_time = m.group()[1:-1]
                img_list = []
            else:
                img_list.append(l.strip())
        if img_list:
            kc_list.append({'time': (int(cur_time)), 'targets': img_list})
        self.kc_list = kc_list
    def load_kc_cond_from_text(self, file_path):
        path = file_path
        self.kc_cond_list = []
        if os.path.isfile(path):
            with open(path, 'r') as f:
                lines = f.readlines()
            p = re.compile('\[.*\]')
            kc_cond_list = []
            img_dict = {}
            for l in lines:
                m = re.match(p, l)
                if m:
                    label = m.group()[1:-1]
                    if label == 'start':
                        if img_dict:
                            kc_cond_list.append({
                                'time': (int(cur_time)),
                                'targets': img_dict['target'],
                                'start': img_dict['start'],
                                'finish': img_dict['finish']})
                            img_dict = {}
                        cur_img_category = 'start'
                        img_dict[cur_img_category] = []
                    elif label == 'finish':
                        cur_img_category = 'finish'
                        img_dict[cur_img_category] = []
                    elif re.match('\d+', label):
                        cur_time = m.group()[1:-1]
                        cur_img_category = 'target'
                        img_dict[cur_img_category] = []
                else:
                    if l.strip():
                        img_dict[cur_img_category].append(l.strip())
            if img_dict:
                kc_cond_list.append({'time': (int(cur_time)), 'targets': img_dict['target'], 'start': img_dict['start'],
                                     'finish': img_dict['finish']})
            self.kc_cond_list = kc_cond_list
    def close(self):
        self.running = False
