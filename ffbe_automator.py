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
import pandas as pd
import setting_gui
import operation_status_checker as osc
from typing import Type
from ffbe_gui import AutomatorParas
import copy
def print_for_debug():
    print('*'*100)
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
        self.convert_to_A = None
        self.convert_to_B = None
        # Define all internal variables
        self.device_type = None
        self.job = None
        self.finish_button = None
        self.operation_status_checker: Type[osc.OperationStatusChecker] = None
        self.running = False
        self.keep_click_running = False
        self.stop_keep_click_index = 1
        self.checked_cbs = {}
        self.checked_rbs = {}
        self.automator_paras = AutomatorParas()
        self.init_internal_vars()
        self.init_other()
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
    def set_user_params(self, automator_paras:AutomatorParas=None, operation_status_checker=None, finish_button=None):
        if automator_paras:
            self.automator_paras = automator_paras
            self.automator_paras.show_yourself()
        if operation_status_checker:
            self.operation_status_checker = operation_status_checker
        if finish_button:
            self.finish_button = finish_button
    def set_automator_settings(self, automator_settings):
        print("Setting automator config")
        # self.checked_cbs = [cb.lower() for cb in automator_settings.checked_cbs]
        self.checked_cbs = automator_settings.checked_cbs
        self.checked_rbs = automator_settings.checked_rbs
        print("Settings: ", self.checked_cbs, " and ", self.checked_rbs)
    def set_img_base_path(self):
        device_type = self.device_type
        self.debug("--set_img_base_path--")
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
    def set_automation_path(self, work_name):
        self.automation_path = os.path.join('./a_orders', work_name)
        print(f"Setting automation_path as :{self.automation_path}")
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
        self.automator_paras.sleep_multiple = 5
    def init_other(self):
        self.stop_watch_started = False
        self.init_automation_list()
        self.timer = Timer()
        self.limit_timer = Timer()
        # self.operation_status_checker = operation_status_checker.OperationStatusChecker()
    # From here, called from start_automation
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
        if self.operation_status_checker:
            self.locator.set_operation_status_checker(self.operation_status_checker)
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
    def finish_automation(self):
        if self.finish_button and self.running:
            print(f"Finishing Automation")
            self.finish_button.click()
        elif not self.running:
            print(f"Automation already stopped")
        elif not self.finish_button:
            print(f"No finish button. Unable to stop")
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
        option1 = self.automator_paras.operation_option1
        option2 = self.automator_paras.operation_option2
        finish_button = self.finish_button
        print(f"option1:{option1}")
        print(f"option2:{option2}")
        if option1 == '이벤트':
            self.play_quest_event(inCall=True)
        elif option1 == '파티별':
            self.play_quest_with_different_party(inCall=True)
        elif option1 == '이벤트(파티별)':
            self.play_quest_event_with_different_party(inCall=True)
        else:
            self.play_quest_plain(inCall=True)
        self.close()
    def play_quest_event(self, inCall=False):
        self.running = True
        self.locator.confidence = 0.95
        self.log(f"Starting event quest automation.")
        rep_time = self.automator_paras.rep_time
        finish_button = self.finish_button
        is_imgs = ["pic_common_is", "cmd_select_chapter"]
        is_for_tor = ["cmd_normal_tor", "cmd_hard_tor"]
        self.set_automation_path('quest_event')
        keep_clicker = Keep_Clicker(self)
        keep_clicker.start_keep_clicks()
        cnt = 0
        while self.running:
            # 이벤트 퀘스트 자동 진행
            self.debug("Before battle, trying to click sortie")
            while (not self.locator.locate('auto')) and self.running:
                banner_for_new_quest = ['banner_new_quest|']
                if self.locator.locate_and_click(is_imgs, target=banner_for_new_quest):
                    time.sleep(2)
                if not self.locator.locate(['sortie', 'sortie_eq', 'common', 'select_party']):
                    self.locator.click_on_screen('story_skip1')
                    time.sleep(2)
            self.debug("In battle stage")
            while (not self.locator.locate('end_of_quest')) and self.running:
                time.sleep(5)
            self.debug("Battle Ended.")
            self.debug(f"After battle, until 'select chapter', repeating, ... story skip")
            while (not (self.locator.locate(is_imgs) or self.locator.locate(['sortie', 'sortie_eq']) or self.locator.locate(is_for_tor))) and self.running:
                self.locator.locate_and_click('end_of_quest')
                if not self.locator.locate(is_imgs):
                    self.locator.click_on_screen('story_skip1')
                    time.sleep(5)
            cnt += 1
            self.log(f"Completed: {cnt} and {rep_time - cnt} left.")
            if cnt >= rep_time:
                break
        if not inCall:
            self.log("Automation completed.")
            self.close()
        self.debug("Quit automation.")
        keep_clicker.close()
    def play_quest_event_with_different_party(self, inCall=False):
        self.running = True
        self.locator.confidence = 0.95
        self.log(f"Starting event quest with different party automation.")
        rep_time = self.automator_paras.rep_time
        finish_button = self.finish_button
        is_imgs = ["pic_common_is", "cmd_select_chapter"]
        is_for_tor = ["cmd_normal_tor", "cmd_hard_tor"]
        # self.set_automation_path('quest_event')
        # keep_clicker = Keep_Clicker(self)
        # keep_clicker.start_keep_clicks()
        cnt = 0
        while self.running:
            # 이벤트 퀘스트 자동 진행
            self.debug("Before battle, trying to click sortie")
            banner_for_new_quest = ['banner_new_quest|pic_scroll_down_daily|pic_scroll_down_daily2']
            cnt_for_eq = 0
            while (not self.locator.locate(['sortie', 'sortie_eq', 'select_party'])) and self.running:
                if self.locator.locate_and_click(banner_for_new_quest):
                    time.sleep(2)
                cnt_for_eq += 1
                if cnt_for_eq > 10:
                    finish_button.click()
                    time.sleep(2)
            self.debug("In Waiting Room")
            self.play_quest_with_different_party(inCall=True)
            self.debug("PQDP with a quest finished. Step to next quest")
            while(not self.locator.locate(is_imgs)):
                self.locator.locate_and_click('cmd_back_top_left')
                time.sleep(3)
            cnt += 1
            self.log(f"Completed: {cnt} times.")
            if cnt >= rep_time:
                break
            time.sleep(1)
            if self.locator.locate(is_imgs) and (not self.locator.locate(banner_for_new_quest)):
                print(f"Event quest with different party Finished")
                break
        if (finish_button != None) and self.running and inCall==False:
            self.log("Automation completed.")
            finish_button.click()
        self.debug("Quit automation.")
    def play_quest_plain(self, inCall = False):
        self.running = True
        self.locator.confidence = 0.95
        self.log(f"Starting quest automation.")
        rep_time = self.automator_paras.rep_time
        finish_button = self.finish_button
        is_imgs = ["pic_common_is", "cmd_select_chapter"]
        is_for_tor = ["cmd_normal_tor", "cmd_hard_tor"]
        # self.start_keep_clicks()
        self.set_automation_path('quest_plain')
        keep_clicker = Keep_Clicker(self)
        keep_clicker.start_keep_clicks()
        cnt = 0
        while self.running:
            # 퀘스트 자동 진행
            self.debug("Before battle, trying to click sortie")
            while (not self.locator.locate('auto')) and self.running:
                if self.locator.locate(is_imgs) or self.locator.locate(is_for_tor):
                    self.debug("A")
                    if self.locator.locate('scene3_selected'):
                        pass
                    elif self.locator.locate_and_click('scene3_unselected'):
                        pass
                    elif self.locator.locate_and_click('scene2_unselected'):
                        pass
                    time.sleep(4)
                    # check to switch another chapter
                    if not self.running:
                        break
                    if self.locator.locate('pic_completed_top_quest'):
                        self.locator.locate_and_click('cmd_select_chapter')
                        time.sleep(3)
                        self.locator.locate_and_click('banner_next_chapter|banner_top_chapter')
                        time.sleep(3)
                    if self.locator.locate('pic_completed_top_quest'):
                        print("No new quest to play")
                        finish_button.click()
                if self.locator.locate_and_click(is_imgs, target='top_quest'):
                    time.sleep(4)
                elif self.locator.locate_and_click(is_for_tor, target='top_quest_for_tor'):
                    self.debug("B")
                    time.sleep(4)
                time.sleep(1)
                if not self.locator.locate(['sortie', 'sortie_eq', 'common', 'select_party']):
                    self.locator.click_on_screen('story_skip1')
                    time.sleep(5)
            self.debug("In battle stage")
            self.stop_watch()
            while (not self.locator.locate('end_of_quest')) and self.running:
                time.sleep(5)
            self.debug("Battle Ended.")
            self.debug("The quest ended")
            self.debug(f"After battle, until 'select chapter', repeating, ... story skip")
            while (not (self.locator.locate(is_imgs) or self.locator.locate(['sortie', 'sortie_eq']) or self.locator.locate(is_for_tor))) and self.running:
                self.locator.locate_and_click('end_of_quest')
                if not self.locator.locate(is_imgs):
                    self.locator.click_on_screen('story_skip1')
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
        keep_clicker.close()
    def play_quest_with_different_party(self, inCall=False, rep_time=None):
        self.running = True
        self.locator.confidence = 0.95
        self.log(f"Starting quest automation with different party.")
        if not rep_time:
            rep_time = self.automator_paras.rep_time
        finish_button = self.finish_button
        self.set_automation_path('quest_with_different_party')
        keep_clicker = Keep_Clicker(self)
        keep_clicker.start_keep_clicks()
        cnt = 0
        print('a'*100)
        print(self.checked_cbs['PQDP'])
        print('a' * 100)
        selected_party = self.checked_cbs['PQDP']
        # 퀘스트 자동 진행
        self.debug("Before battle, select party then click sortie")
        party_list = ['화','빙','풍','토','뇌','수','명','암']
        img_for_party_dic = {
            '화':'select_fire_cb_party','빙':'select_ice_cb_party','풍':'select_wind_cb_party','토':'select_earth_cb_party','뇌':'select_lightning_cb_party','수':'select_water_cb_party','명':'select_light_cb_party','암':'select_dark_cb_party'
        }
        time.sleep(2)
        self.locator.locate_and_click('cb_select_party')
        time.sleep(2)
        for i in range(3):
            self.locator.locate_and_click('pic_scroll_up_select_party')
            time.sleep(1)
        for party in party_list:
            if not self.running:
                break
            if not (party in selected_party):
                continue
            self.locator.confidence = 0.80
            select_next_party = img_for_party_dic[party]
            self.debug(select_next_party)
            # Change party
            time.sleep(2)
            self.debug("Selecting party button")
            while (not self.locator.locate("pic_opened_cb_select_party")) and self.running:
                self.locator.locate_and_click("select_party")
                time.sleep(1)
            time.sleep(1)
            self.debug(f"Selecting next party: {select_next_party}")
            while (not self.locator.locate_and_click(select_next_party)) and self.running:
                time.sleep(1)
            self.debug("Next party selected")
            time.sleep(2)
            self.locator.confidence = 0.95
            # 출격
            sorties = ["sortie", "sortie_quest", "sortie_eq", "sortie_12", "sortie_confirm"]
            while (not self.locator.locate('auto')) and self.running:
                self.locator.locate_and_click(sorties)
                if not self.locator.locate(['sortie', 'sortie_eq', 'common', 'select_chapter', 'select_party']):
                    self.locator.click_on_screen('story_skip1')
                    time.sleep(5)
            self.debug("In battle stage")
            self.stop_watch()
            while (not self.locator.locate('cmd_end_of_quest_popup_quest')) and self.running:
                if self.locator.locate(sorties):
                    break
                time.sleep(5)
            self.debug("The Quest ended")
            while (not self.locator.locate(sorties)) and self.running:
                print("In while loop of ... ")
                self.locator.locate_and_click('cmd_back_to_sortie_popup_quest')
                if not self.locator.locate(['sortie', 'sortie_eq', 'common', 'select_chapter', 'select_party']):
                    self.locator.click_on_screen('story_skip1')
                    self.locator.locate_and_click('yes')
                    time.sleep(5)
            cnt += 1
            self.log(f"Completed: {cnt} and {rep_time - cnt} left.")
            self.stop_watch()
        self.debug("Automation completed.")
        if (finish_button != None) and self.running and inCall==False:
            self.log("Automation completed.")
            finish_button.click()
        self.debug("Quit automation.")
        keep_clicker.close()
    def play_multi(self):
        self.locator.confidence = 0.95
        rep_time = self.automator_paras.rep_time
        num_of_players = self.automator_paras.num_of_players
        finish_button = self.finish_button
        self.running = True
        self.time_limit = 900
        self.log("Starting multi automation")
        cnt = 0

        # self.start_keep_clicks()
        keep_clicker = Keep_Clicker(self)
        keep_clicker.start_keep_clicks()

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
                if (self.elapsed_time() > 500) and (self.locator.get_path("checking_the_result")):
                    while (self.locator.locate('checking_the_result')) and self.running:
                        self.debug("Kicking someone checking the result!")
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
                    self.recover_stamina(keep_clicker=keep_clicker)
                time.sleep(self.automator_paras.sleep_multiple)
            self.debug("\n'Auto' is located. In battle stage")
            self.timer.restart()
            targets = ['organize']
            cancels = ["cancel", "cancel_friend", "cancel_multi", "cmd_cancel_popup_multi"]
            while (not self.locator.locate(targets)) and self.running:
                self.locator.locate_and_click(cancels)
                time.sleep(self.automator_paras.sleep_multiple * 5)
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
        keep_clicker.close()
    def play_multi_client_any(self, inCall = False):
        self.running = True
        self.locator.confidence = 0.95
        self.log("Starting multi_client automation")
        keep_clicker_for_PMCA = Keep_Clicker(self)
        keep_clicker_for_PMCA.set_operation_status_checker(self.operation_status_checker)
        if inCall:
            keep_clicker_for_PMCA.set_automation_path('a_orders\multi_client_any')
        keep_clicker_for_PMCA.start_keep_clicks()
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
                    keep_clicker_for_PMCA.stop_keep_click()
                    while (not self.locator.locate(exit_finish)) and (not self.locator.locate('auto')) and self.running:
                        self.locator.locate_and_click(exit_targets)
                        time.sleep(3)
                    keep_clicker_for_PMCA.start_keep_click()
                    self.limit_timer.restart()
            self.debug("In battle stage.")
            while (not self.locator.locate('cancel_ready')) and self.running:
                time.sleep(10)
            cnt += 1
            self.debug("After battle stage.")
            self.log(f"Completed {cnt} times.")
        keep_clicker_for_PMCA.close()
    def play_raid_host(self):
        self.locator.confidence = 0.95
        rep_time = self.automator_paras.rep_time
        num_of_players = self.automator_paras.num_of_players
        finish_button = self.finish_button
        self.running = True
        self.log("Starting multi automation")
        cnt = 0
        # self.start_keep_clicks()
        keep_clicker = Keep_Clicker(self)
        keep_clicker.start_keep_clicks()
        while self.running:
            time.sleep(10)
            pass
        keep_clicker.close()
    def play_raid_full_auto(self):
        self.locator.confidence = 0.95
        rep_time = self.automator_paras.rep_time
        num_of_players = self.automator_paras.num_of_players
        finish_button = self.finish_button
        print(self.automator_paras.test_para)
        if self.automator_paras.test_para:
            quest_to_play = self.automator_paras.test_para.lower()
        else:
            quest_to_play = None
        self.running = True
        self.log("Starting multi automation")
        raid_loop_cnt = 0
        cnt = 0
        kc_for_raid = Keep_Clicker(self)
        kc_for_raid.set_target_file(kc_file_name='kc_for_raid.txt', kc_cond_file_name='kc_cond_for_raid.txt')
        sc = Serial_Clicker(self)

        while self.running:
            # 첫화면은 레이드 출격 전 화면 또는 스토리 출격 전 화면
            # skip battle이 있으면 스토리, 없으면 레이드
            if self.locator.locate("cmd_skip_battle_quest"):
                # In story sortie
                # kc_for_story.start_keep_clicks()
                print("Try to skip battle for 9 times")
                self.skip_battle(9, in_call=True)
                print("Skip battle finished.")
                print("Let's go to raid")
                sc.start_serial_click_thread("to_raid")
                while self.running:
                    if self.locator.locate(["cmd_sortie_raid", "cmd_get_last_reward_raid"]):
                        break
                    time.sleep(5)
                print("Arrived to raid screen")
            elif self.locator.locate(["cmd_sortie_raid", "cmd_get_last_reward_raid"]):
                # In raid sortie
                kc_for_raid.start_keep_clicks()
                while self.running:
                    if self.locator.locate("cmd_get_last_reward_raid"):
                        break
                    time.sleep(5)
                print("All raid finished.")
                kc_for_raid.stop_keep_click()
                raid_loop_cnt += 1
                self.log(f"Raid finished for {raid_loop_cnt} * 10 time(s), {rep_time-raid_loop_cnt} time(s) left.")
                if raid_loop_cnt >= rep_time:
                    break
                print("Let's go to quest")
                quest_by_para = {
                    'fire':'to_quest_fire_stone', 'wind':'to_quest_wind_stone', 'water':'to_quest_water_stone',
                    'ice':'to_quest_ice_stone','earth':'to_quest_earth_stone','dark':'to_quest_dark_stone',
                    'lightning':'to_quest_lightning_stone','light':'to_quest_light_stone',
                    'gold':'to_quest_golden_room'
                }
                if quest_to_play:
                    try:
                        to_quest_string = quest_by_para[quest_to_play]
                    except Exception as e:
                        print(f"{e} with {quest_to_play}")
                        self.error(f"{e} with {quest_to_play}")
                        to_quest_string = 'to_quest'
                else:
                    to_quest_string = 'to_quest'
                sc.start_serial_click_thread(to_quest_string)
                while self.running:
                    if self.locator.locate('cmd_ok_popup_skip_battle'):
                        print("Try to skip battle for 10 times")
                        self.skip_battle(10, in_call=True)
                        print("Skip battle finished.")
                        break
                    time.sleep(5)
                print("Let's go to raid")
                sc.start_serial_click_thread("to_raid")
                while self.running:
                    if self.locator.locate(["cmd_sortie_raid", "cmd_get_last_reward_raid"]):
                        break
                    time.sleep(5)
                print("Arrived to raid screen")
            else:
                print("Error! Start from raid or quest sortie screen")
                time.sleep(5)
        print("Full Auto raid finished.")
        if self.running:
            finish_button.click()
        kc_for_raid.close()
        sc.close()
    def whim_store(self):
        self.locator.confidence = 0.95
        option1 = self.automator_paras.operation_option1
        option2 = self.automator_paras.operation_option2
        finish_button = self.finish_button
        self.running = True
        if option1 == '변덕런(풀)':
            self.whim_store_full(inCall=True)
        elif option1 == '초코보':
            self.whim_store_plain(inCall=True, target='chocobo')
        elif option1 == '초코보(풀)':
            self.whim_store_full(inCall=True, target='chocobo')
        else:
            self.whim_store_plain(inCall=True)
        self.finish_automation()
    def whim_store_plain(self, inCall=False, target='whim_store'):
        self.locator.confidence = 0.95
        finish_button = self.finish_button
        self.running = True
        self.log("Starting skip battle for whim store")
        print("Starting skip battle for whim store")
        self.log(f"path: {self.automation_path}")
        cnt = 0
        kc = Keep_Clicker(self)
        kc.set_automation_path("./a_orders/whim_store")
        kc.start_keep_clicks()
        finish_target = 'cmd_later_popup_store' if target == 'whim_store' else 'cmd_later_popup_chocobo'
        while (not self.locator.locate(finish_target)) and self.running:
            time.sleep(1)
        cnt += 1
        if target == 'whim_store':
            print("Succeed to find whim store")
        else:
            print("Succeed to find fever run")
        if self.running and (not inCall):
            finish_button.click()
        kc.close()
        # sc.close()
    def whim_store_full(self, inCall=False, target = 'whim_store'):
        self.locator.confidence = 0.95
        finish_button = self.finish_button
        self.running = True
        self.log("Starting skip battle for whim store")
        print("Starting skip battle for whim store")
        self.log(f"path: {self.automation_path}")
        cnt = 0
        sc = Serial_Clicker(self)
        sc.set_path_and_file(automation_path='./a_orders/whim_store', sc_file_name="sc.txt")
        dw_in_order = [
            "pre스토리xp","스토리20"
        ]
        self.from_is_to_menu()
        for dw in dw_in_order:
            try:
                print("Starting DW for ", dw)
                sc.start_serial_click_thread(sc_name=dw, click_interval=0.1)
            except Exception as e:
                print(e)
            while (not sc.serial_click_finished) and self.running:
                time.sleep(3)
            if not self.running:
                break
        print("Skip battle until whim store or fever run")
        self.whim_store_plain(inCall=True, target=target)
        print("Succeed to find whim store or fever run")
        if self.running and (not inCall):
            finish_button.click()
        sc.close()
    def play_chocobo_run(self):
        option1 = self.automator_paras.operation_option1
        option2 = self.automator_paras.operation_option2

        # if option1 == '2hour':
        #     pass
        # elif option1 == '5hour':
        #     pass
        # else:

        ticket_hour = option1
        self.play_chocobo_run_plain(ticket_hour=ticket_hour)

    def play_chocobo_run_plain(self, ticket_hour='2hour'):
        self.locator.confidence = 0.95
        option1 = self.automator_paras.operation_option1
        option2 = self.automator_paras.operation_option2
        rep_time = self.automator_paras.rep_time

        self.running = True
        self.log("Starting Sample Automation")

        cnt_chocobo = 0
        chocobo_sc = Serial_Clicker(self)
        chocobo_sc.set_path_and_file(automation_path='chocobo', sc_file_name='chocobo_sc.txt')
        if '10' in ticket_hour:
            ticket_target = 'cmd_10hour_popup_speedy_expedition'
        elif '5' in ticket_hour:
            ticket_target = 'cmd_5hour_popup_speedy_expedition'
        else:
            ticket_target = 'cmd_2hour_popup_speedy_expedition'
        click_targets = [ticket_target, 'cmd_ok_popup_excess_fragment']
        while self.running:
            if cnt_chocobo >= rep_time:
                break
            chocobo_sc.start_serial_click_thread(sc_name='speedy_expedition', click_interval=1)
            if self.locator.locate('cmd_retrieve_speedy_expedition'):
                while (not self.locator.locate_and_click('cmd_retrieve_speedy_expedition#0.99')) and self.running:
                    self.locator.locate_and_click(click_targets)
                    time.sleep(1)
                cnt_chocobo += 1
            self.locator.locate_and_click(ticket_target)
            time.sleep(1)

        self.log(f"Chocobo Automation Completed")
        self.finish_automation()
        chocobo_sc.close()
    def reincarnation(self):
        self.locator.confidence = 0.95
        rep_time = self.automator_paras.rep_time
        num_of_players = self.automator_paras.num_of_players
        finish_button = self.finish_button
        test_para = self.automator_paras.test_para

        self.running = True
        self.log("Starting multi automation")

        cnt_reincarnation = 0
        # kc_for_reincarnation = Keep_Clicker(self)
        # kc_for_reincarnation.set_target_file(kc_file_name='kc_for_reincarnation.txt')
        # sc = Serial_Clicker(self)

        while self.running:
            if self.locator.locate('text_3star_remain_popup2_reincarnation'):
                while self.running and (not self.locator.locate('cmd_ok_popup_reincarnation')):
                    self.locator.locate_and_click(['cmd_reinforce_popup_excla', 'cb_stop_reincarnation_unchecked'])
                    if self.locator.locate('text_stop_reincarnation_checked'):
                        self.locator.locate_and_click('cmd_reinforce_popup2')
                while self.running and (not self.locator.locate('text_0star_remain_popup2_reincarnation')):
                    self.locator.locate_and_click('cmd_ok_popup_reincarnation')
            cnt_reincarnation += 1
            self.log(f"윤회 {cnt_reincarnation}회 완료")
            time.sleep(3)
            if self.locator.locate('text_0star_remain_popup2_reincarnation'):
                while self.running and (not self.locator.locate('text_3star_remain_popup2_reincarnation')):
                    self.locator.locate_and_click('cmd_reincarnate_popup')
                    time.sleep(2)
                    self.locator.locate_and_click('cmd_reincarnate_popup2')
                    time.sleep(2)
                    self.locator.locate_and_click('cmd_max_popup2_select_item')
                    time.sleep(2)
                    self.locator.locate_and_click('cmd_decide_popup2_reincarnation')
                    time.sleep(2)
                    self.locator.locate_and_click('cmd_ok_popup_reincarnation')
                    time.sleep(1)
            if cnt_reincarnation >= rep_time:
                break
        self.log(f"Reincarnation Completed")
        if self.running:
            finish_button.click()
        # kc_for_reincarnation.close()
    def template_automation(self):
        self.locator.confidence = 0.95
        option1 = self.automator_paras.operation_option1
        option2 = self.automator_paras.operation_option2
        rep_time = self.automator_paras.rep_time
        num_of_players = self.automator_paras.num_of_players
        test_para = self.automator_paras.test_para
        finish_button = self.finish_button

        self.running = True
        self.log("Starting Sample Automation")

        cnt_reincarnation = 0
        template_kc = Keep_Clicker(self)
        template_kc.set_target_file(kc_file_name='template_kc.txt')
        template_sc = Serial_Clicker(self)
        template_sc.set_path_and_file(automation_path='template', sc_file_name='template_sc')

        while self.running:
            if cnt_reincarnation >= rep_time:
                break
        self.log(f"SampleAutomation Completed")
        self.finish_automation()
        template_kc.close()
    def skip_battle(self, rep_time=None, in_call=False):
        self.locator.confidence = 0.95
        if not rep_time:
            rep_time = self.automator_paras.rep_time
        num_of_players = self.automator_paras.num_of_players
        finish_button = self.finish_button
        self.running = True

        kc = Keep_Clicker(self)
        kc.set_automation_path("./a_orders/skip_battle")
        kc.start_keep_clicks()

        self.log("Starting skip battle automation")
        print("Starting skip battle automation")
        self.log(f"path: {self.automation_path}")
        cnt = 0
        while self.running:
            targets = ["cmd_skip_battle", "cmd_skip_battle_quest"]
            while (not self.locator.locate("cmd_end_of_quest_skip_battle")) and self.running:
                self.locator.locate_and_click(targets)
                targets_for_no_stamina = ['text_short_of_stamina', 'select_chapter','pic_common_is']
                if self.locator.locate(targets_for_no_stamina):
                    # 체력이 부족해서 팅겨나온 상황
                    self.recover_stamina(keep_clicker=kc, recover_cnt=8)
                time.sleep(3)
            cnt += 1
            self.log(f"Battle Skipped. {cnt} times. {rep_time - cnt} left.")
            targets2 = ["cmd_end_of_quest_skip_battle"]
            while (not self.locator.locate(targets)) and self.running:
                self.locator.locate_and_click(targets2)
                targets_for_no_stamina2 = ['text_short_of_stamina', 'select_chapter','pic_common_is']
                if self.locator.locate(targets_for_no_stamina2):
                    # 체력이 부족해서 팅겨나온 상황
                    self.recover_stamina(keep_clicker=kc, recover_cnt=8)
                    self.locator.locate_and_click(["pic_mission_completed_quest", "pic_mission_completed_quest2"])
                time.sleep(3)
            if cnt >= rep_time:
                self.log("Automation Completed.")
                if not in_call:
                    finish_button.click()
                break
        kc.close()
    def gil_summon(self):
        rep_time = self.automator_paras.rep_time
        finish_button = self.finish_button
        self.running = True
        self.log("Starting Gil-summon automation")
        kc = Keep_Clicker(self)
        kc.sleep_mul=3
        kc.start_keep_clicks()
        cnt = 0
        while self.running:
            while (not self.locator.locate('cmd_summon_popup_confirm')) and self.running:
                print("In while loop, processing")
                time.sleep(3)
            if self.locator.locate_and_click('cmd_summon_popup_confirm'):
                time.sleep(3)
                cnt += 1
                self.log(f"Summon Completed {cnt} times. {rep_time - cnt} times left.")
            if cnt >= rep_time:
                break
        if (finish_button != None) and self.running:
            finish_button.click()
        kc.close()
    def recover_stamina(self, keep_clicker=None, recover_cnt=8):
        # Recovering
        self.debug("---Start recovering stamina---")
        if keep_clicker:
            keep_clicker.stop_keep_click()
        time.sleep(1)

        while self.running and (self.locator.locate('text_short_of_stamina')):
            self.locator.locate_and_click('cmd_no_popup_short_of_stamina')

        if recover_cnt >= 8:
            sc = Serial_Clicker(self)
            sc.set_path_and_file(automation_path='./a_orders/', sc_file_name="sc_for_recover_stamina.txt")

            sc.start_serial_click_thread(sc_name='체력회복')
            while self.running and (not sc.serial_click_finished):
                time.sleep(1)
            for i in range(3):
                self.locator.locate_and_click("cmd_close_popup_stamina|cmd_ok_popup_recover_stamina|cmd_cancel_popup_recover_stamina")
                time.sleep(1)
        else:
            targets = 'yes|item|icon_plus_stamina'
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
            time.sleep(2)
            recover_targets = ["recover", "ok_recover",'cmd_ok_popup_recover_stamina']
            while (self.locator.locate(['ok_recover', 'recover_amount','cmd_ok_popup_recover_stamina'])) and self.running:
                self.locator.locate_and_click(recover_targets)
                time.sleep(1)
            # for c in range(2):
            #     if (not self.locator.locate('recover_amount')) or (not self.running):
            #         break
            #     self.locator.locate_and_click(recover_targets)

        self.debug("Finished recovering")
        if keep_clicker:
            keep_clicker.start_keep_click()
    def daily_work(self):
        option1 = self.automator_paras.operation_option1
        option2 = self.automator_paras.operation_option2
        finish_button = self.finish_button
        print(f"option1:{option1}")
        print(f"option2:{option2}")
        if option1 == 'A and B':
            self.convert_to_A()
            self.log("Starting Daily Work automation for A")
            self.daily_work_plain(inCall=True)
            self.convert_to_B()
            self.log("Starting Daily Work automation for B")
            self.daily_work_plain(inCall=False)
        else:
            self.daily_work_plain(inCall=False)
        if finish_button and self.running:
            self.finish_button.click()
    def from_is_to_menu(self, inCall=True):
        self.running = True
        cnt = 0
        self.log("Starting from_is_to_menu")
        print("Starting from_is_to_menu")
        kc = Keep_Clicker(self)
        kc.set_automation_path('daily_work')
        kc.set_operation_status_checker(self.operation_status_checker)
        kc.start_keep_clicks()
        to_is_targets = ["pic_is", "pic_rank_dark1", "pic_arrow_down_is", "pic_arrow_down_is2", "pic_arrow_down_is_sp_w", "pic_arrow_down_is_sp_m",
                         'cmd_close_popup_is_premium_goods', 'icon_x_popup_is_sp1', 'icon_x_popup_is_sp2', 'icon_x_popup_is_sp3']
        while (not (self.locator.locate("menu_mogri_store#0.99") or self.locator.locate("menu_present#0.99"))) and self.running:
            for t in to_is_targets:
                self.locator.locate_and_click(t)
                time.sleep(1)
        print("Arrived to menu screen")
        kc.close()
    def daily_work_plain(self, inCall=False):
        self.running = True
        cnt = 0
        self.log("Starting Daily Work automation")
        print("Starting Daily Work automation")

        self.from_is_to_menu()

        self.operation_status_checker.reset()
        kc = Keep_Clicker(self)
        kc.set_automation_path('daily_work')
        kc.set_operation_status_checker(self.operation_status_checker)
        kc.start_keep_clicks()

        sc = Serial_Clicker(self)
        sc.set_path_and_file(sc_file_name="sc.txt")
        sc.set_operation_status_checker(self.operation_status_checker)
        print("work to do: ", self.checked_cbs)
        dw_in_order = [
            "백그라운드","체력회복", "초코보", "소환", "상점", "길드", "PVP", "이계의성", "스토리", "친구", "미션", "스탬프", "선물", "백그라운드반복", "멀티클라"
        ]
        si_for_dw = [float(i) for i in range(1, len(dw_in_order) + 1)]
        df = pd.DataFrame({'dw': dw_in_order, 'si': si_for_dw})
        df = df.sort_values(by='si', ascending=True)
        dw_in_order_after_sort = df['dw'].tolist()
        dw_to_do = self.checked_cbs['DW']
        self.debug(f"Works in order: {dw_in_order_after_sort}, works to do: {dw_to_do}")
        def get_si(dw: str, df: pd.DataFrame):
            try:
                si = df[df['dw'] == dw]['si'].iloc[0]
            except Exception as e:
                print(e)
                si = 0
            return si
        si_to_start = get_si(self.automator_paras.operation_option2, df)
        for dw in dw_in_order_after_sort:
            if get_si(dw, df) < si_to_start:
                continue
            if dw in dw_to_do:
                self.log(f"Starting DW for {dw}")
                self.debug(f"Starting DW for {dw}")
                if dw == '백그라운드':
                    time.sleep(5)
                    if self.locator.locate("icon_background_repetition"):
                        sc.start_serial_click_thread(sc_name=dw)
                    else:
                        continue
                elif dw == '체력회복':
                    time.sleep(2)
                    kc.stop_keep_click()
                    sc.start_serial_click_thread(sc_name=dw)
                    while (not sc.serial_click_finished) and self.running:
                        time.sleep(3)
                    kc.start_keep_click()
                elif dw == '멀티클라':
                    if inCall == False:
                        print("멀티클라")
                        self.play_multi_client_any(inCall=True)
                elif dw.lower() == 'pvp':
                    print(f"Testing: {self.checked_rbs['DW']}")
                    if 'pvp1회' in self.checked_rbs['DW']:
                        sc.start_serial_click_thread(sc_name="pvp1회")
                    else:
                        sc.start_serial_click_thread(sc_name="pvp5회")
                elif dw == '이계의성':
                    if '파티명:xp' in dw_to_do:
                        sc.start_serial_click_thread(sc_name='이계의성xp')
                    else:
                        sc.start_serial_click_thread(sc_name=dw)
                elif dw == '스토리':
                    if ('파티명:xp' in dw_to_do) and (not ('이계의성' in dw_to_do)):
                        sc.start_serial_click_thread(sc_name='pre스토리xp')
                    else:
                        sc.start_serial_click_thread(sc_name='pre스토리')
                    while (not sc.serial_click_finished) and self.running:
                        time.sleep(3)
                    if not ('하드퀘스트' in dw_to_do):
                        sc.start_serial_click_thread(sc_name='스토리no하드')
                    else:
                        sc.start_serial_click_thread(sc_name=dw)
                elif dw == '백그라운드반복':
                    sc.start_serial_click_thread(sc_name=dw, click_interval=0.3)
                else:
                    try:
                        sc.start_serial_click_thread(sc_name=dw)
                    except Exception as e:
                        print(e)
                while (not sc.serial_click_finished) and self.running:
                    if dw == '백그라운드':
                        self.locator.locate_and_click('cmd_ok_popup_background')
                    time.sleep(3)
                if not self.running:
                    break
        while self.running:
            if sc.serial_click_finished:
                break
            time.sleep(1)
        self.log("Func. Daily Work finished")
        print("Func. Daily Work finished")
        if self.running and (not inCall):
            self.finish_button.click()
        kc.close()
        sc.close()
    def test(self):
        self.running = True
        cnt = 0
        self.log("Testing!!")
        self.recover_stamina(recover_cnt=2)
        # self.skip_battle(rep_time=2, in_call=True)
        print("Func. test finished")
        if self.running:
            self.finish_button.click()
    def test2(self):
        self.running = True
        cnt = 0
        self.log("Testing2!!")

        print("Testing2"*50)


        a_path = f'./a_orders/raid_full_auto'
        sc_name = 'to_raid'

        keep_clicker = Keep_Clicker(self)
        keep_clicker.set_automation_path(a_path)
        keep_clicker.start_keep_clicks()

        serial_clicker = Serial_Clicker(self)
        serial_clicker.set_path_and_file(automation_path=a_path)
        serial_clicker.start_serial_click(sc_name=sc_name)
        while self.running:
            time.sleep(2)
        if self.running:
            self.finish_button.click()
        keep_clicker.close()
        serial_clicker.close()
    def list_all_methos(self):
        # Get all the methods of the class
        methods = inspect.getmembers(self, predicate=inspect.ismethod)
        # Extract the names of the methods
        method_names = [name for name, _ in methods]
        print(method_names)
    def pre_automation_processing(self):
        win32gui.SetForegroundWindow(self.my_hwnd)
    def close(self):
        self.running = False
        if self.finish_button:
            btn_text = self.finish_button.text()
            if 'on' in btn_text:
                self.finish_button.click()
class Keep_Clicker:
    def __init__(self, automator:Automator=None):
        self.log = print
        self.debug = print
        self.error = print
        self.sleep_mul = 1
        self.automation_path = None
        self.kc_file_name = None
        self.kc_cond_file_name = None
        self.kc_list = []
        self.kc_cond_list = []
        self.img_path = None
        self.my_hwnd = None
        self.confidence = 0.95
        self.device_type = None
        self.my_device = None
        self.operation_status_checker = None
        self.running = True
        self.keep_click_running = False
        self.stop_keep_click_index = 1
        if automator:
            self.set_variables(automator=automator)
    def set_variables(self, automator:Automator):
        self.log = automator.log
        self.debug = automator.debug
        self.error = automator.error
        self.automation_path = automator.automation_path
        self.img_path = automator.img_path
        self.my_hwnd = automator.my_hwnd
        self.sleep_mul = automator.automator_paras.sleep_multiple
        self.confidence = automator.confidence
        self.device_type = automator.device_type
        self.my_device = automator.my_device
        self.running = True
    def set_automation_path(self, automation_path):
        if 'a_orders' in automation_path:
            self.automation_path = automation_path
        else:
            self.automation_path = os.path.join("./a_orders", automation_path)
    def set_target_file(self, kc_file_name=None, kc_cond_file_name=None):
        if kc_file_name:
            self.kc_file_name = kc_file_name
        if kc_cond_file_name:
            self.kc_cond_file_name = kc_cond_file_name
    def set_operation_status_checker(self, operation_status_checker):
        self.operation_status_checker = operation_status_checker
    def start_keep_clicks(self, sleep_mul=None):
        if sleep_mul == None:
            if self.sleep_mul != None:
                sleep_mul = self.sleep_mul
            else:
                sleep_mul = 1
        target_thread = self.keep_click_on_text
        thread_list = []
        # Load kc.txt
        if self.kc_file_name:
            kc_path = os.path.join(self.automation_path, self.kc_file_name)
        else:
            self.kc_file_name = 'kc.txt'
            kc_path = os.path.join(self.automation_path, 'kc.txt')
        if not self.load_kc_from_text(kc_path):
            print(f"Error in def, start_keep_clicks with path: {kc_path}")
            return False
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
        if self.kc_cond_file_name:
            kc_cond_path = os.path.join(self.automation_path, self.kc_cond_file_name)
        else:
            kc_cond_path = os.path.join(self.automation_path, 'kc_cond.txt')
        if not self.load_kc_cond_from_text(kc_cond_path):
            print("Error in def - start_keep_clicks_conditional")
            return False
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
    def keep_click_on_text(self, target_list, sleep_time=None, keep_awake=False):
        if sleep_time == None:
            sleep_time = 1
        locator_kc = locator.Locator(self.my_hwnd, self.automation_path, self.img_path, error=self.error)
        locator_kc.load_conf(self.device_type)
        if self.operation_status_checker:
            locator_kc.set_operation_status_checker(self.operation_status_checker)
        locator_kc.confidence = self.confidence
        if not ('gpg' in self.device_type):
            locator_kc.connect_click_method(self.my_device.input_tap)
        while self.running:
            if self.keep_click_running or keep_awake:
                for target in target_list:
                    if not (self.running and (self.keep_click_running or keep_awake)):
                        break
                    result = locator_kc.locate_and_click(target)
                    if result:
                        print(f"Successfully clicked for [{target}] by keep click with SleepTime: {sleep_time}")
                for i in range(int(sleep_time)):
                    if not (self.running and (self.keep_click_running or keep_awake)):
                        break
                    time.sleep(1)
            else:
                print(f"Skip keep_click loop for {target_list} sleep time: {sleep_time}")
                for i in range(5 * int(sleep_time)):
                    if not self.running:
                        break
                    time.sleep(1)
    def keep_click_conditional(self, target_list, start_list, finish_list, sleep_time=None):
        if sleep_time == None:
            sleep_time = 1
        locator_kc = locator.Locator(self.my_hwnd, self.automation_path, self.img_path, error=self.error)
        locator_kc.load_conf(self.device_type)
        if self.operation_status_checker:
            locator_kc.set_operation_status_checker(self.operation_status_checker)
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
    def start_keep_click(self):
        self.stop_keep_click_index -= 1
        if self.stop_keep_click_index <= 0:
            print(f"Starting keep click. stop_keep_click_index={self.stop_keep_click_index}.")
            self.keep_click_running = True
    def stop_keep_click(self):
        self.stop_keep_click_index += 1
        if self.keep_click_running == True:
            self.keep_click_running = False
            print(f"Stopping keep click. stop_keep_click_index={self.stop_keep_click_index}.")
    def load_kc_from_text(self, file_path):
        path = file_path
        if os.path.isfile(path):
            with open(path, 'r') as f:
                lines = f.readlines()
        else:
            return False
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
        return kc_list
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
            return kc_cond_list
        return False
    def close(self):
        if self.kc_cond_file_name:
            print(f"Stopping keep_clicker for [{self.kc_file_name}] and [{self.kc_cond_file_name}] in {self.automation_path}")
        else:
            print(f"Stopping keep_clicker for [{self.kc_file_name}] in {self.automation_path}")
        self.running = False
        self.keep_click_running = False
        if self.operation_status_checker:
            self.operation_status_checker.stop()
class Serial_Clicker():
    def __init__(self, automator:Automator=None):
        self.log = print
        self.debug = print
        self.error = print
        self.sleep_mul = 1
        self.automation_path = None
        self.sc_file_name = None
        self.sc_list = {}
        self.img_path = None
        self.my_hwnd = None
        self.confidence = 0.95
        self.device_type = None
        self.my_device = None
        self.operation_status_checker:Type[osc.OperationStatusChecker] = None
        self.running = True
        self.serial_click_running = True
        self.serial_click_finished = True
        self.stop_serial_click_index = 1
        if automator:
            self.set_variables(automator=automator)
    def set_variables(self, automator: Automator):
        self.log = automator.log
        self.debug = automator.debug
        self.error = automator.error
        self.sleep_mul = automator.automator_paras.sleep_multiple
        self.automation_path = automator.automation_path
        self.img_path = automator.img_path
        self.my_hwnd = automator.my_hwnd
        self.confidence = automator.confidence
        self.device_type = automator.device_type
        self.my_device = automator.my_device
        self.running = True
    def set_path_and_file(self, automation_path=None, sc_file_name=None):
        if automation_path:
            if 'a_orders' in automation_path:
                self.automation_path = automation_path
            else:
                self.automation_path = os.path.join('./a_orders' ,automation_path)
        if sc_file_name:
            self.sc_file_name = sc_file_name
    def set_operation_status_checker(self, operation_status_checker):
        self.operation_status_checker = operation_status_checker
    def start_serial_click_thread(self, sc_name=None, click_interval=2):
        target_thread = self.start_serial_click
        args = (sc_name, click_interval)
        thread_to_run = threading.Thread(target=target_thread, args=args)
        thread_to_run.start()
    def start_serial_click(self, sc_name=None, click_interval=2):
        while (not self.serial_click_finished) and self.running:
            time.sleep(3)
        self.serial_click_finished = False
        if self.sc_file_name:
            sc_file_name = self.sc_file_name
        else:
            sc_file_name = "sc.txt"
            self.sc_file_name = sc_file_name
        self.load_sc_from_text(os.path.join(self.automation_path, sc_file_name))
        if self.sc_list:
            if sc_name:
                sc_targets = self.sc_list[sc_name]
            else:
                sc_targets = self.sc_list[list(self.sc_list.keys())[0]]
        else:
            print(f"No target in {sc_file_name}")
            return False
        self.debug(f"-----Start SC for {sc_name}-----")
        locator_sc = locator.Locator(self.my_hwnd, self.automation_path, self.img_path, error=self.error)
        locator_sc.load_conf(self.device_type)
        if self.operation_status_checker:
            locator_sc.set_operation_status_checker(self.operation_status_checker)
        locator_sc.confidence = self.confidence
        if not ('gpg' in self.device_type):
            locator_sc.connect_click_method(self.my_device.input_tap)
        for i, t in enumerate(sc_targets):
            if i == 0:
                prev_target = None
                pprev_target = None
                ppprev_target = None
                target = sc_targets[i]
            elif i == 1:
                prev_target = sc_targets[i - 1]
                pprev_target = None
                ppprev_target = None
                target = sc_targets[i]
            elif i == 2:
                prev_target = sc_targets[i - 1]
                pprev_target = sc_targets[i-2]
                ppprev_target = None
                target = sc_targets[i]
            else:
                prev_target = sc_targets[i-1]
                pprev_target = sc_targets[i-2]
                ppprev_target = sc_targets[i-3]
                target = sc_targets[i]
            print(f"for {i}, target = {target}, prev_targets = {prev_target, pprev_target}")
            self.debug(f"for {i}, target = {target}, prev_targets = {prev_target, pprev_target}")
            if self.serial_click_running:
                cs_cnt = 0
                while self.running and self.serial_click_running:
                    if prev_target:
                        if (cs_cnt>5) and ppprev_target:
                            if locator_sc.locate_and_click(ppprev_target):
                                time.sleep(click_interval)
                        if (cs_cnt>2) and pprev_target:
                            if locator_sc.locate_and_click(pprev_target):
                                time.sleep(click_interval)
                        if locator_sc.locate_and_click(prev_target):
                            time.sleep(click_interval)
                    cs_cnt+=1
                    if locator_sc.locate(target):
                        break
            if not self.running:
                break
        print(f"Serial Click Finished for [{sc_targets}]")
        self.serial_click_finished = True
    def resume(self):
        self.stop_serial_click_index -= 1
        if self.stop_serial_click_index <= 0:
            print(f"Starting keep click. stop_serial_click_index={self.stop_serial_click_index}.")
            self.serial_click_running = True
    def stop(self):
        self.stop_serial_click_index += 1
        if self.serial_click_running == True:
            self.serial_click_running = False
            print(f"Stopping serial click. stop_serial_click_index={self.stop_serial_click_index}.")
    def load_sc_from_text(self, file_path):
        global sc_name
        path = file_path
        if os.path.isfile(path):
            with open(path, 'r', encoding='UTF-8') as f:
                lines = f.readlines()
        else:
            return False
        p = re.compile('\[\w*\]')
        sc_list = {}
        img_list = []
        for l in lines:
            m = re.match(p, l)
            if m:
                if img_list:
                    sc_list[sc_name] = img_list
                    # sc_list.append({'time': (int(sc_name)), 'targets': img_list})
                sc_name = m.group()[1:-1]
                img_list = []
            else:
                if l.strip():
                    img_list.append(l.strip())
        if img_list:
            sc_list[sc_name] = img_list
            # sc_list.append({'time': (int(sc_name)), 'targets': img_list})
        self.sc_list = sc_list
        return sc_list
    def close(self):
        print(f"Serial Clicker for [{self.sc_file_name}] in {self.automation_path} stops now.")
        self.running = False
        self.serial_click_running = False

if __name__ == '__main__':
    automator = Automator()
    automator_setting = setting_gui.SettingsDialog()
    automator_setting.initUi()
    automator_setting.load_from_file()
    print(automator_setting.selected_party)
    print("aaa")