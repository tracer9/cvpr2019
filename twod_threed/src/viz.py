import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

from twod_threed.src import data_utils

import h5py
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
import os
import torch

# Constants for how to plot the pose
THREED_RADIUS = 750                                # space around the subject for 3D
TWOD_RADIUS = 750                                # space around the subject for 2D

# Joints in H3.6M -- data has 32 joints, but only 17 that move; these are the indices.
H36M_NAMES = ['']*32
H36M_NAMES[0]  = 'Hip'
H36M_NAMES[1]  = 'RHip'
H36M_NAMES[2]  = 'RKnee'
H36M_NAMES[3]  = 'RFoot'
H36M_NAMES[6]  = 'LHip'
H36M_NAMES[7]  = 'LKnee'
H36M_NAMES[8]  = 'LFoot'
H36M_NAMES[12] = 'Spine'
H36M_NAMES[13] = 'Thorax'
H36M_NAMES[14] = 'Neck/Nose'
H36M_NAMES[15] = 'Head'
H36M_NAMES[17] = 'LShoulder'
H36M_NAMES[18] = 'LElbow'
H36M_NAMES[19] = 'LWrist'
H36M_NAMES[25] = 'RShoulder'
H36M_NAMES[26] = 'RElbow'
H36M_NAMES[27] = 'RWrist'

# Stacked Hourglass produces 16 joints. These are the names.
SH_NAMES = ['']*16
SH_NAMES[0]  = 'RFoot'
SH_NAMES[1]  = 'RKnee'
SH_NAMES[2]  = 'RHip'
SH_NAMES[3]  = 'LHip'
SH_NAMES[4]  = 'LKnee'
SH_NAMES[5]  = 'LFoot'
SH_NAMES[6]  = 'Hip'
SH_NAMES[7]  = 'Spine'
SH_NAMES[8]  = 'Thorax'
SH_NAMES[9]  = 'Head'
SH_NAMES[10] = 'RWrist'
SH_NAMES[11] = 'RElbow'
SH_NAMES[12] = 'RShoulder'
SH_NAMES[13] = 'LShoulder'
SH_NAMES[14] = 'LElbow'
SH_NAMES[15] = 'LWrist'

# MPII joints
# 0 - r ankle,
# 1 - r knee,
# 2 - r hip,
# 3 - l hip,
# 4 - l knee,
# 5 - l ankle,
# 6 - pelvis,
# 7 - thorax,
# 8 - upper neck,
# 9 - head top,
# 10 - r wrist,
# 11 - r elbow,
# 12 - r shoulder,
# 13 - l shoulder,
# 14 - l elbow,
# 15 - l wrist


def viz_3d_pose(points):
    """
    Given joint points, vizualize them on a plot and return them as a np.ndarray

    :param points: The 2d points of the joints to visualize
    :param ax: matplotlib 2d axis to draw on
    :return: A image in the form of a numpy array, the image is of a matplotlib figure
    """
    fig = plt.figure(figsize=(10.0, 10.0))
    ax = fig.add_subplot(111, projection='3d')
    plt.axis('off')

    _plot3Dpose(points, ax)

    # convert fig to a numpy array
    # see: https://stackoverflow.com/questions/7821518/matplotlib-save-plot-to-numpy-array
    fig.canvas.draw()
    data = np.fromstring(fig.canvas.tostring_rgb(), dtype=np.uint8, sep='')
    data = data.reshape(fig.canvas.get_width_height()[::-1] + (3,))

    # avoid unecessary memory consumption
    plt.close(fig)

    return data



def viz_2d_pose(points):
    """
    Given joint points, vizualize them on a plot and return them as a np.ndarray

    :param points: The 2d points of the joints to visualize
    :param ax: matplotlib 2d axis to draw on
    :return: A image in the form of a numpy array, the image is of a matplotlib figure
    """
    fig = plt.figure(figsize=(10.0, 10.0))
    ax = fig.add_subplot(111)
    plt.axis('off')

    _plot2Dpose(points, ax)

    # convert fig to a numpy array
    # see: https://stackoverflow.com/questions/7821518/matplotlib-save-plot-to-numpy-array
    fig.canvas.draw()
    data = np.fromstring(fig.canvas.tostring_rgb(), dtype=np.uint8, sep='')
    data = data.reshape(fig.canvas.get_width_height()[::-1] + (3,))

    # avoid unecessary memory consumption
    plt.close(fig)
    
    return data



def _plot3Dpose(channels, ax, lcolor="#3498db", rcolor="#e74c3c", add_labels=False): # blue, orange
    """
    Visualize a 3d skeleton on a matplotlib axis

    :param channels: 1x48 dim vector or a 16x3 dim tensor. Representing the pose to plot.
    :param ax: matplotlib 3d axis to draw on
    :param lcolor: color for left part of the body
    :param rcolor: color for right part of the body
    :param add_labels: whether to add coordinate labels
    :return: Nothing. Draws on ax.
    """
    # Get joint coords from the input and make sure its correct shape
    vals = channels if type(channels) is np.ndarray else channels.cpu().detach().numpy()
    vals = np.reshape(vals, (-1, 3))

    # I = np.array([1, 2, 3, 1, 7, 8, 1, 13, 14, 15, 14, 18, 19, 14, 26, 27]) - 1       # h36m start points
    # J = np.array([2, 3, 4, 7, 8, 9, 13, 14, 15, 16, 18, 19, 20, 26, 27, 28]) - 1      # h36m end points
    # LR = np.array([1, 1, 1, 0, 0, 0, 0, 0,  0,  0,  0,  0,  0,  1, 1, 1], dtype=bool) # h36m right size edges
    I  = np.array([0, 1, 2, 5, 4, 3, 6, 7, 15, 14, 13, 10, 11, 12, 8])                  # stacked hourglass start points
    J  = np.array([1, 2, 6, 4, 3, 6, 7, 8, 14, 13,  8, 11, 12,  8, 9])                  # stacked hourglass end points
    LR = np.array([1, 1, 1, 0, 0, 0, 0, 0,  0,  0,  0,  1,  1,  1, 0], dtype=bool)      # stacked hourglass end points

    # Make connection matrix
    for i in np.arange(len(I)):
        x, y, z = [np.array( [vals[I[i], j], vals[J[i], j]] ) for j in range(3)]
        ax.plot(x, y, z, lw=2, c=lcolor if LR[i] else rcolor)

    xroot, yroot, zroot = vals[0,0], vals[0,1], vals[0,2]
    ax.set_xlim([-THREED_RADIUS+xroot, THREED_RADIUS+xroot])
    ax.set_ylim([-THREED_RADIUS+yroot, THREED_RADIUS+yroot])
    ax.set_zlim([-THREED_RADIUS+zroot, THREED_RADIUS+zroot])
    if add_labels:
        ax.set_xlabel("x")
        ax.set_ylabel("y")
        ax.set_zlabel("z")

    # Get rid of the ticks
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_zticks([])

    # Get rid of the ticks and tick labels
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_zticks([])

    ax.get_xaxis().set_ticklabels([])
    ax.get_yaxis().set_ticklabels([])
    ax.set_zticklabels([])
    ax.set_aspect('equal')

    # Get rid of the panes (actually, make them white)
    white = (1.0, 1.0, 1.0, 0.0)
    ax.w_xaxis.set_pane_color(white)
    ax.w_yaxis.set_pane_color(white)
    # Keep z pane

    # Get rid of the lines in 3d
    ax.w_xaxis.line.set_color(white)
    ax.w_yaxis.line.set_color(white)
    ax.w_zaxis.line.set_color(white)



def _plot2Dpose(channels, ax, lcolor="#3498db", rcolor="#e74c3c", add_labels=False):
    """
    Visualize a 2d skeleton on a matplotlib axis

    :param channels: 1x32 vector or a 16x2. The pose to plot.
    :param ax: matplotlib 2d axis to draw on
    :param lcolor: color for left part of the body
    :param rcolor: color for right part of the body
    :param add_labels: whether to add coordinate labels
    :return: Nothing. Draws on ax.
    """
    # Get joint coords from the input and make sure its correct shape
    vals = channels if type(channels) is np.ndarray else channels.cpu().detach().numpy()
    vals = np.reshape(vals, (-1, 2))

    # I = np.array([1, 2, 3, 1, 7, 8, 1, 13, 14, 15, 14, 18, 19, 14, 26, 27]) - 1       # h36m start points
    # J = np.array([2, 3, 4, 7, 8, 9, 13, 14, 15, 16, 18, 19, 20, 26, 27, 28]) - 1      # h36m end points
    # LR = np.array([1, 1, 1, 0, 0, 0, 0, 0,  0,  0,  0,  0,  0,  1, 1, 1], dtype=bool) # h36m right size edges
    I  = np.array([0, 1, 2, 5, 4, 3, 6, 7, 15, 14, 13, 10, 11, 12, 8])                  # stacked hourglass start points
    J  = np.array([1, 2, 6, 4, 3, 6, 7, 8, 14, 13,  8, 11, 12,  8, 9])                  # stacked hourglass end points
    LR = np.array([1, 1, 1, 0, 0, 0, 0, 0,  0,  0,  0,  1,  1,  1, 0], dtype=bool)      # stacked hourglass end points

    # Make connection matrix
    for i in np.arange( len(I) ):
        x, y = [np.array( [vals[I[i], j], vals[J[i], j]] ) for j in range(2)]
        ax.plot(x, y, lw=2, c=lcolor if LR[i] else rcolor)

    # Get rid of the ticks
    ax.set_xticks([])
    ax.set_yticks([])

    # Get rid of tick labels
    ax.get_xaxis().set_ticklabels([])
    ax.get_yaxis().set_ticklabels([])

    xroot, yroot = vals[0,0], vals[0,1]
    ax.set_xlim([-TWOD_RADIUS+xroot, TWOD_RADIUS+xroot])
    ax.set_ylim([-TWOD_RADIUS+yroot, TWOD_RADIUS+yroot])
    if add_labels:
        ax.set_xlabel("x")
        ax.set_ylabel("z")

    ax.set_aspect('equal')