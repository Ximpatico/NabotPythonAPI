import numpy as np
import os
import cv2
import signal
import sys
import logging
import threading

import tkinter.ttk as ttk
import tkinter as tk
from tkinter import Frame, RAISED, BOTH, Button, RIGHT, Canvas, Scale, HORIZONTAL
import datetime

from robot_controller import RobotController

class GraphicalInterface():
    def __init__(self, *args, **kwargs):
        threading.Thread.__init__(self)
        self.kwargs = kwargs
        self.enable_joysticks = True
        if 'enable_joysticks' in self.kwargs:
            self.enable_joysticks = self.kwargs['enable_joysticks']

        logging.getLogger("requests").setLevel(logging.WARNING)
        
        self.stop_robot = False
        self.logger = logging.getLogger('GUI')
        self.curr_image = None
        self.joint_states = []
        self.num_empty_commands = 0

        self.robot_ctrl = RobotController.getInstance(*args, **kwargs)
        self.logger.info('initializing robot...')
        self.robot_ctrl.init_robot()
        self.logger.info('robot successfully initilized')

        if 'robot_init_pos' in self.kwargs:
            self.logger.info('Sending robot to center.')
            self.robot_ctrl.send_robot_to_center(goal=kwargs['robot_init_pos'])
            self.logger.info('Robot centered.')
            
        
        np.set_printoptions(precision=2)

        self.image_size = (640, 360)
        if 'image_size' in self.kwargs:
            self.image_size = self.kwargs['image_size']


    def callback(self):
        self.parent.quit()

    def run(self):
        
        self.parent = tk.Tk()

        self.main_frame = Frame(self.parent)
        self.main_frame.pack()
        if self.enable_joysticks:
            self.create_widgets()
        
        self.robot_controller()

        # def signal_handler(sig, frame):
        #     self.logger.info('You pressed Ctrl+C')
        #     # cap.release()
        #     cv2.destroyAllWindows()
        #     self.logger.info("Stopping Robot...")
        #     self.stop_robot = True
        #     self.robot_ctrl.send_joint_command_to_robot([0, 0, 0, 0, 0, 0], use_thread=False)
        #     sys.exit(0)

        # signal.signal(signal.SIGINT, signal_handler)  

        self.parent.mainloop()   

    def robot_controller(self):
        self.curr_image = self.robot_ctrl.get_image_cv2()
        if self.curr_image is None:
            self.parent.after(10, self.robot_controller)
            return
        
        img = cv2.resize(self.curr_image, self.image_size)
        cv2.imshow('frame', img / 255.0)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            return
        
        if self.stop_robot == True:
            return

        if self.enable_joysticks:
            x = -self.canvas.joystick_x
            y = -self.canvas.joystick_y
            v = (100 - abs(x)) * (y / 100) + y
            w = (100 - abs(y)) * (x / 100) + x 
            x = (v - w) // 2
            y = (v + w) // 2
            command_to_send = [x, y, self.scale1.get(), self.scale2.get(), self.scale4.get(), self.scale3.get()]
        

            self.robot_ctrl.send_joint_command_to_robot(command_to_send)
            # self.robot_ctrl.update_joint_states()
        
        self.parent.after(10, self.robot_controller)
        

    def create_widgets(self):
        self.main_frame.style = ttk.Style()
        self.main_frame.winfo_toplevel().title("Nabot Controls")
        self.main_frame.style.theme_use('default')
        self.main_frame.configure(background='black')

        def create_canvas():
            class Joystick(tk.Canvas):
                pass

            self.canvas = Joystick(self.main_frame, width=400, height=400)
            self.canvas.joystick_x = 0
            self.canvas.joystick_y = 0
            self.canvas.is_moving = False

            def paint(event):
                # self.canvas.create_rectangle(0, 0, 200, 200, fill='red')
                reset_canvas()
                self.canvas.create_oval(0, 0, 400, 400, fill='black', outline='gray')
                x1, y1 = event.x - 75, event.y - 75
                x2, y2 = event.x + 75, event.y + 75
                self.canvas.create_oval(x1, y1, x2, y2, fill='blue')

                self.canvas.joystick_x = (event.x - 200) * 7 / 10
                self.canvas.joystick_y = (event.y - 200) * 7 / 10

                self.canvas.joystick_x = min(max(self.canvas.joystick_x, -100), 100)
                self.canvas.joystick_y = min(max(self.canvas.joystick_y, -100), 100)

            def reset(event):
                self.canvas.is_moving = False
                self.canvas.joystick_x = 0
                self.canvas.joystick_y = 0
                reset_canvas()
                logging.debug('move the robot, x:{} y:{}'.format(self.canvas.joystick_x, self.canvas.joystick_y))
            
            def reset_canvas():
                self.canvas.create_rectangle(0, 0, 400, 400, fill='black')
                self.canvas.create_oval(0, 0, 400, 400, fill='black', outline='gray')
                self.canvas.create_oval(125, 125, 275, 275, fill='gray')

            self.canvas.pack(side='left')
            
            # self.canvas.bind('<Button-1>', start)
            self.canvas.bind('<B1-Motion>', paint)
            self.canvas.bind('<ButtonRelease-1>', reset)
            reset_canvas()


            def scale1_command(val):
                val = self.scale1.get()

            def scale1_stop(event):
                self.scale1.set(0)

            self.scale1 = Scale(from_=100, to=-100, label='head', command=scale1_command)
            self.scale1.bind('<ButtonRelease-1>', scale1_stop)
            self.scale1.pack(side='left')
            
            def scale2_command(val):
                val = self.scale2.get()

            def scale2_stop(event):
                self.scale2.set(0)

            self.scale2 = Scale(from_=100, to=-100, label='elbow', command=scale2_command)
            self.scale2.bind('<ButtonRelease-1>', scale2_stop)
            self.scale2.pack(side='left')
            self.scale3 = Scale(from_=0, to=100, orient=HORIZONTAL, label='Gripper')
            self.scale3.pack(side='top')

            
            def scale4_command(val):
                val = self.scale4.get()

            def scale4_stop(event):
                self.scale4.set(0)

            self.scale4 = Scale(from_=-100, to=100, orient=HORIZONTAL, command=scale4_command, label='wrist')
            self.scale4.bind('<ButtonRelease-1>', scale4_stop)
            self.scale4.pack(side='top')


        create_canvas()