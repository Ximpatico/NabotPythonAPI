import time
import requests
import numpy as np
import logging
import enum
from typing import List

from robot_controller import RobotController
from direction import Direction

class NabotController():
    def __init__(self, *args, **kwargs):
        self.robot_controller = RobotController.getInstance(*args, **kwargs)
        self.stop_command = [0,0,0,0,0,0]
        self.logger = logging.getLogger("NabotController")

    def get_image(self):
        im = self.robot_controller.get_latest_image()
        while im is None:
            time.sleep(1)
            im = self.robot_controller.get_latest_image()
        return im

    def update_joint_states(self):
        self.robot_controller.update_joint_states()
    
    def get_joint_states(self):
        return self.robot_controller.get_joint_states()

    def stop(self, milliseconds:float = 0):
        if milliseconds > 0:
            time.sleep(milliseconds/1000)
        
        self.robot_controller.send_joint_command_to_robot(self.stop_command)

    def wait(self, milliseconds:float):
        if milliseconds > 0:
            time.sleep(milliseconds/1000)

    def rotate(self, direction: Direction, power:float, steps=1):
        wheels_command = [0.0, 0.0]
        if direction == Direction.LEFT or direction == Direction.CCW:
            wheels_command = [-power, power]
        if direction == Direction.RIGHT or direction == Direction.CW:
            wheels_command = [power, -power]
        
        self.logger.info("sending the rotate to {} for {} steps".format(direction.name, steps))

        for i in range(steps):
            self.robot_controller.send_joint_command_to_robot(wheels_command)
            time.sleep(.5)
        
        self.robot_controller.send_joint_command_to_robot([0.0, 0.0])

    def move(self, direction: Direction, power:float, steps: int):
        wheels_command = [0.0, 0.0]
        if direction == Direction.FORWARD:
            wheels_command = [power, power]
        if direction == Direction.BACKWARD:
            wheels_command = [-power, -power]
        
        self.logger.info("sending the Move {} for {} steps".format(direction.name, steps))

        for i in range(steps):
            self.robot_controller.send_joint_command_to_robot(wheels_command)
            time.sleep(.5)
        
        self.robot_controller.send_joint_command_to_robot([0.0, 0.0])

    def goto_position(self, joints: List[int]):
        self.robot_controller.send_robot_to_goal(goal=joints)

    def pick(self):
        self.robot_controller.send_robot_to_goal([100, 67, 48, 1])
        self.robot_controller.close_gripper()
        self.robot_controller.send_robot_to_goal([90, 67, 48, 100])

    def place(self):
        self.robot_controller.send_robot_to_goal([65, 67, 48, 100])
        self.move(Direction.FORWARD, 25, 2)
        self.robot_controller.open_gripper()
        self.move(Direction.BACKWARD, 25, 2)
        self.robot_controller.send_robot_to_goal([100, 67, 48, 1])

    def explore(self, direction: Direction):
        pass
    
    def align(self):
        pass

    def look(self):
        pass

    def approach(self):
        pass

    def is_stuck(self):
        pass

    
    

if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s  %(name)s  %(levelname)s: %(message)s', level=logging.INFO)
    nabot = NabotController()

    nabot.update_joint_states()
    print(nabot.get_joint_states())
    
    robot_image = nabot.move(Direction.FORWARD, power=30, steps=2)