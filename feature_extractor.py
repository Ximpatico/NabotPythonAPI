import torch
import torchvision.models as models
import torchvision.transforms as transforms

import logging
import numpy as np
from PIL import Image
import random
import time

class FeatureExtractor():
    def __init__(self, model_name='resnet'):
        if model_name == 'resnet':
            self.model = resnet18 = models.resnet18(pretrained=True)
        elif model_name == 'alexnet':
            self.model = models.alexnet(pretrained=True)
        elif model_name == 'vgg16':
            self.model = models.vgg16(pretrained=True)
        elif model_name == 'densenet':
            self.model = models.densenet161(pretrained=True)
        elif model_name == 'inception':
            self.model = models.inception_v3(pretrained=True)
        elif model_name == 'googlenet':
            self.model = models.googlenet(pretrained=True)
        elif model_name == 'mobilenet':
            self.model = models.mobilenet_v2(pretrained=True)
        elif model_name == 'resnext':
            self.model = models.resnext50_32x4d(pretrained=True)
        elif model_name == 'wide_resnet':
            self.model = models.wide_resnet50_2(pretrained=True)

        if torch.cuda.is_available():
            self.model.cuda()

        self.model.eval()

        normalize = transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                 std=[0.229, 0.224, 0.225])
        
        self.input_transform = transforms.Compose([
            transforms.Scale(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            normalize,
        ])

    def get_features(self, images):
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
        logging.info("classifier: time spent on gpu {}".format(gpu_time))
        return pred.cpu()

    def normalize_input(self, input_image):
        return self.input_transform(input_image)



if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s  %(name)s  %(levelname)s: %(message)s', level=logging.INFO)
    input_img = Image.new('RGB',(224,224))
    pixels = input_img.load()
    for x in range(input_img.size[0]):
        for y in range(input_img.size[1]):
            pixels[x, y] = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

    FE = FeatureExtractor(model_name='mobilenet')
    
    features = FE.get_features(input_img)
    print(features.size())