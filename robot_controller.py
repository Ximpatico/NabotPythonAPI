import time
import requests
import numpy as np
import logging
from PIL import Image
from socket import timeout
import urllib
import cv2
import threading

class RobotController():
    robot_state = [0, 0, 0, 0] # arm, wrist_ud, wrist_rot, gripper
    robot_command = [0, 0, 0, 0, 0, 0] # forward, left_right, arm, wrist_ud, wrist_rot, gripper
    last_robot_command = [0, 0, 0, 0, 0, 0] # forward, left_right, arm, wrist_ud, wrist_rot, gripper
    robot_state_names = ["ARM_QUERY", "WRIST_UD_QUERY", "WRIST_ROTATE_QUERY", "CLAW_QUERY"]
    robot_command_names = ["WHEEL_LEFT_FORWARD", "WHEEL_RIGHT_FORWARD", "ARM_UP", "WRIST_UD_UP", "WRIST_ROTATE_LEFT", "CLAW_POSITION"]

    init_commands = ["BAT", "GET_SSID", "VIDEO_FLIP", "VIDEO_MIRROR", "ACEAA", "BCQAA", "CCIAA", "INIT_ALL"]
    messageCount = 0
    
    __instance = None

    @staticmethod
    def getInstance(*args, **kwargs):
      """ Static access method. """
      if RobotController.__instance == None:
         RobotController(*args, **kwargs)
      return RobotController.__instance
    
    def __init__(self, *args, **kwargs):
        self.curr_image = None
        """ Virtually private constructor. """
        if RobotController.__instance != None:
            raise Exception("RobotController is a singleton!")
        else:
            RobotController.__instance = self

        self.logger = logging.getLogger('Robot Controller')
        self.update_image()
        

    def init_robot(self):
        for cmd in self.init_commands:
            self.send_single_command_to_robot(cmd, 0)
        self.logger.info('Initialized robot')

    def get_image_cv2(self):
        return cv2.imdecode(self.curr_image, cv2.IMREAD_COLOR)

    def get_latest_image(self):
        if self.curr_image is None:
            return None
        opencv_im = cv2.imdecode(self.curr_image, cv2.IMREAD_COLOR)
        return Image.fromarray(cv2.cvtColor(opencv_im, cv2.COLOR_BGR2RGB))

    def update_image(self):
        # download the image, convert it to a NumPy array, and then read
        # it into OpenCV format
        try:
            resp = urllib.request.urlopen("http://192.168.99.1/ajax/snapshot.jpg", timeout=0.2)
            latest_image = np.asarray(bytearray(resp.read()), dtype="uint8")
            self.curr_image = np.copy(latest_image)

            threading.Timer(0.2, self.update_image).start()
            # return Image.fromarray(self.latest_image)
        
        except timeout:
            self.logger.debug("updating camera frame request timed out ... skipping")
            threading.Timer(0.2, self.update_image).start()
        except Exception as e:
            threading.Timer(0.2, self.update_image).start()

    def send_robot_to_center(self, goal=[40, 50, 50, 0]):
        self.send_robot_to_goal(goal=goal)

    def send_robot_to_goal(self, goal=[40, 50, 50, 0]):
        command = [0, 0, 0, 0, 0, 0]
        goal = np.asarray(goal).astype(np.float32)
        loop_counter = 0
        last_command_time = time.time()
        while(True):
            if time.time() - last_command_time > .1:
                self.update_joint_states()
                time.sleep(.1)
                joint_states = np.asarray(self.get_joint_states()).astype(np.float32)
                self.logger.debug(joint_states)
                diff = (goal - joint_states ) * 6
                diff[2] /= 4
                for i, d in enumerate(diff[:-1]):
                    diff[i] = min( 30, max(diff[i], -30))
                #     if -5 < d < 5:
                #         diff[i] = 0
                diff[0] = -diff[0]
                self.logger.debug(diff)
                self.logger.debug(np.max(np.abs(diff[:-1])))
                print(diff )
                if np.max(np.abs(diff[:-1])) < 10 or loop_counter > 10:
                    self.send_joint_command_to_robot([0, 0, 0, 0, 0, goal[-1]])
                    break
                # if np.all(joint_states > 0.1) or loop_counter > 10:
                command[2:5] = diff[:-1]
                command[5] = goal[3]
                self.send_joint_command_to_robot(command)
                last_command_time = time.time()
                loop_counter += 1
                
        self.logger.info('Went to goal position.')

    def open_gripper(self, ):
        self.send_joint_command_to_robot([0, 0, 0, 0, 0, 1])
        time.sleep(2)

    def close_gripper(self, ):
        self.send_joint_command_to_robot([0, 0, 0, 0, 0, 100])
        time.sleep(2)

    def send_single_command_to_robot(self, cmd, value):

        URL = "http://192.168.99.1/ajax/command.json?" + self.generate_single_command(1, cmd, value)
        time.sleep(0.01)
        try:
            r = requests.get(url = URL, verify=False, timeout=1)
            data = r.json()
            
            if 'response' in data:
                aJsonString = data['response']
                if ("ARM" in aJsonString) and (len(aJsonString) >= 4):
                    self.robot_state[0] = int(aJsonString[4:])
                elif ("WRIST_UD" in aJsonString) and len(aJsonString) >= 9:
                    self.robot_state[1] = int(aJsonString[9:])
                elif ("WRIST_ROTATE" in aJsonString) and len(aJsonString) >= 13:
                    self.robot_state[2] = int(aJsonString[13:])
                elif ("CLAW" in aJsonString and len(aJsonString) >= 5):
                    self.robot_state[3] = int(aJsonString[5:])
        except:
            self.logger.warning("Error parsing robot's response")
    
    def send_joint_command_to_robot(self, jointValues, use_thread=False):
        self.send_joint_command_to_robot_helper(jointValues)
    
    def send_joint_command_to_robot_helper(self, jointValues):
        self.robot_command = jointValues
        URL = "http://192.168.99.1/ajax/command.json?"

        for i in range(len(self.robot_command)) :
            if (i > 0):
                URL += "&";
            URL += self.generate_single_command(i + 1, self.robot_command_names[i], self.robot_command[i])
            self.last_robot_command[i] = self.robot_command[i]
        time.sleep(0.01)
        try:
            r = requests.get(url = URL, verify=False, timeout=1)
        except requests.exceptions.Timeout:
            self.logger.warning("request timeout")
        except Exception as e:
            self.logger.warning(e)

    def update_joint_states(self):
        for cmd in self.robot_state_names:
            self.send_single_command_to_robot(cmd, 0)

    def get_joint_states(self):
        return self.robot_state

    def generate_single_command(self, number, command, parameter):
        cmd_str = self._command_string(command, parameter)
        if(command == "EYE_LED_STATE"):
            return "command" + str(number) + "=eye_led_state()"
        if(command == "CLAW_LED_STATE"):
            return "command" + str(number) + "=claw_led_state()"
        if(command == "GET_SSID"):
            return "command" + str(number) + "=get_ssid()"
        if(command == "VIDEO_FLIP"):
            return "command" + str(number) + "=video_flip(0)"
        if(command == "VIDEO_MIRROR"):
            return "command" + str(number) + "=video_mirror(0)"
        if(command == "ACEAA"):
            return "command" + str(number) + "=mebolink_message_send(!ACEAA)"
        if(command == "BCQAA"):
            return "command" + str(number) + "=mebolink_message_send(!BCQAA)"
        if(command == "CCIAA"):
            return "command" + str(number) + "=mebolink_message_send(!CCIAA)"
        if(command == "INIT_ALL"):
            return "command" + str(number) + "=mebolink_message_send(!CVVDSAAAAAAAAAAAAAAAAAAAAAAAAYtBQfA4uAAAAAAAAAAQfAoPAcXAAAA)"
        return "command" + str(number) + "=mebolink_message_send(" + cmd_str + ")"
    
    def _command_string(self, cmd, para):
        if ( cmd == "BAT"):
            return "BAT=?"
        elif ( cmd == "LIGHT_ON"):
            return self.new_cmd() + "RAAAAAAAVd"
        elif ( cmd == "LIGHT_OFF"):
            return self.new_cmd() + "RAAAAAAAVc"

        elif ( cmd == "WHEEL_LEFT_FORWARD"):
            return self.new_cmd() + "F" + self.enc_spd(para)
        elif ( cmd == "WHEEL_RIGHT_FORWARD"):
            return self.new_cmd() + "E" + self.enc_spd(para)

        elif ( cmd == "ARM_UP"):
            return self.new_cmd() + "G" + self.enc_spd(para)
        elif ( cmd == "ARM_QUERY"):
            return "ARM=?"

        elif ( cmd == "WRIST_UD_UP"):
            return self.new_cmd() + "H" + self.enc_spd(para)
        elif ( cmd == "WRIST_UD_QUERY"):
            return "WRIST_UD=?"

        elif ( cmd == "WRIST_ROTATE_LEFT"):
            return self.new_cmd() + "I" + self.enc_spd(para)
        elif ( cmd == "WRIST_ROTATE_QUERY"):
            return "WRIST_ROTATE=?"

        elif ( cmd == "CLAW_POSITION"):
            return self.new_cmd() + "N" + self.enc_spd(para)
        elif ( cmd == "CLAW_QUERY"):
            return "CLAW=?"

        elif ( cmd == "CAL_ARM"):
            return self.new_cmd() + "DE"
        elif ( cmd == "CAL_WRIST_UD"):
            return self.new_cmd() + "DI"
        elif ( cmd == "CAL_WRIST_ROTATE"):
            return self.new_cmd() + "DQ"
        elif ( cmd == "CAL_CLAW"):
            return self.new_cmd() + "Dg"
        elif ( cmd == "CAL_ALL"):
            return self.new_cmd() + "D_"

        elif ( cmd == "VERSION_QUERY"):
            return "VER=?"
        elif ( cmd == "REBOOT_CMD"):
            return self.new_cmd() + "DE"

        elif ( cmd == "SET_REG"):
            return ""
        elif ( cmd == "QUERY_REG"):
            return "REG" + (para / 100 % 10) + (para / 10 % 10) + (para % 10) + "=?"
        elif ( cmd == "SAVE_REG"):
            return "REG=FLUSH"

        elif ( cmd == "WHEEL_LEFT_SPEED"):
            return self.new_cmd() + "F" + self.enc_spd(para)
        elif ( cmd == "WHEEL_RIGHT_SPEED"):
            return self.new_cmd() + "E" + self.enc_spd(para)

        elif ( cmd == "QUERY_EVENT"):
            return "*"
        else:
            return ""

    def new_cmd(self):
        result = "!" + self._to_base64(self.messageCount & 63)
        self.messageCount += 1
        return result

    def enc_spd(self, speed):
        return self._encode_base64(speed, 2)
    
    def _to_base64(self, val):
        str = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
        return "" + str[val & 63]


    def _encode_base64(self, val, chars_count):
        result = ""
        for i in range(chars_count):
            result += self._to_base64(int(val) >> int(i * 6))
        return result
