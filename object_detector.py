import torch
import torchvision.models as models
import torchvision.transforms as transforms

from nabot_controller import NabotController
import logging
import numpy as np
from PIL import Image
import random
import time

class ObjectDetector():
    def __init__(self, model_name='resnet'):
        if model_name == 'resnet':
            self.model = models.detection.fasterrcnn_resnet50_fpn(pretrained=True)
        
        if torch.cuda.is_available():
            self.model.cuda()

        self.model.eval()

        normalize = transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                 std=[0.229, 0.224, 0.225])
        
        self.input_transform = transforms.Compose([
            # transforms.Scale(256),
            # transforms.CenterCrop(224),
            transforms.ToTensor(),
            # normalize,
        ])

        self.COCO_NAMES = [
            '__background__', 'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus',
            'train', 'truck', 'boat', 'traffic light', 'fire hydrant', 'N/A', 'stop sign',
            'parking meter', 'bench', 'bird', 'cat', 'dog', 'horse', 'sheep', 'cow',
            'elephant', 'bear', 'zebra', 'giraffe', 'N/A', 'backpack', 'umbrella', 'N/A', 'N/A',
            'handbag', 'tie', 'suitcase', 'frisbee', 'skis', 'snowboard', 'sports ball',
            'kite', 'baseball bat', 'baseball glove', 'skateboard', 'surfboard', 'tennis racket',
            'bottle', 'N/A', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl',
            'banana', 'apple', 'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza',
            'donut', 'cake', 'chair', 'couch', 'potted plant', 'bed', 'N/A', 'dining table',
            'N/A', 'N/A', 'toilet', 'N/A', 'tv', 'laptop', 'mouse', 'remote', 'keyboard', 'cell phone',
            'microwave', 'oven', 'toaster', 'sink', 'refrigerator', 'N/A', 'book',
            'clock', 'vase', 'scissors', 'teddy bear', 'hair drier', 'toothbrush'
        ]



    def predict(self, images):
        input_image = self.normalize_input(images)

        if input_image.ndim == 3:
            input_image = input_image[np.newaxis]

        if torch.cuda.is_available():
            input_image = input_image.cuda()
        # compute output
        start = time.time()
        with torch.no_grad():
            pred = self.model(input_image)
        # torch.cuda.synchronize()
        gpu_time = time.time() - start
        logging.info("detector: time spent on gpu {}".format(gpu_time))

        lables = list(map(lambda x: self.COCO_NAMES[x], pred[0]['labels'].cpu().numpy()))
        return pred[0]['boxes'].cpu().numpy(), lables, pred[0]['scores'].cpu().numpy()

    def normalize_input(self, input_image):
        return self.input_transform(input_image)


if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s  %(name)s  %(levelname)s: %(message)s', level=logging.INFO)
    object_detector = ObjectDetector()
    nabot = NabotController()

    robot_image = nabot.get_image()
    bounding_boxes, lables, confidence = object_detector.predict(robot_image)
    
