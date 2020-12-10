# Instalation
To install the dependency's run the following command

```
pip3 install -r requirement.txt
```

# Nabot's Python API
This repository is inteded for controlling Nabot. Please feel free to clone the repository and change/add features you are interested in and send us a pull request to share it with others.

# Manual Control

To control the robot manually run the manual_control.py
Before running the code make sure you are connected to the Nabot via Wifi.

```
    python3 manual_control.py
```
After running the script, two windows should will open, one for Nabot's camera feed and the other one for controlling it. In the logs you might see request timeouts from time to time which is normal.

# Robot Controller
In addition to controlling the robot using UI elements, you can control it by code! Just instantiate the class NabotController(nabot_controller.py) and use its function. You extend this class to add more functionalities to your Nabot.

Using the NabotController class you can send commands to Nabot, get its joint states, get its latest image, and a lot more.
Here is an example of controlling nabot.
```
nabot = NabotController()

robot_image = nabot.move(Direction.FORWARD, power=30, steps=2)
```

Here is another example that updates Nabot's joint states and print them.

```
nabot = NabotController()

nabot.update_joint_states()
print(nabot.get_joint_states())

```

You can find this code at the end of the nabot_controller.py file.

# Object Detection

Object detection is the process of feeding an image to a nueral network which tries to detect objects in it. In the example below we are getting Nabot's latest image from the class NabotController and passing it to an instance of the ObjectDetector class. The predict function gets an image as input and returns 3 outputs. First, is the bounding boxes for the detections. Second one is the label associated with each bounding box and the last one is network's confidence in its prediction which is between 0 and 1.

```
object_detector = ObjectDetector()
nabot = NabotController()
# make sure you are connected to Nabot's wifi - otherwise the get_image function waits till its connected to Nabot
robot_image = nabot.get_image()
bounding_boxes, lables, confidence = object_detector.predict(robot_image)
```