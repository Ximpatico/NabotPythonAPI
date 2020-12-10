
import numpy as np
import matplotlib.pyplot as plt
import math

cmap = plt.cm.viridis

def parse_command():
    import argparse

    parser.add_argument('--gpu', default='0', type=str, metavar='N', help="gpu id")
    parser.add_argument('-m', '--model', default='resnet', type=str, help="name of the model to use: resnet, mobilenet, etc")
    parser.set_defaults(cuda=True)

    args = parser.parse_args()
    return args


def colored_depthmap(depth, d_min=None, d_max=None):
    if d_min is None:
        d_min = np.min(depth)
    if d_max is None:
        d_max = np.max(depth)
    depth_relative = (depth - d_min) / (d_max - d_min)
    return 255 * cmap(depth_relative)[:,:,:3] # H, W, C