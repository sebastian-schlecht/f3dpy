"""
Inspector OpenCV App to clean & view data
--------------------------------------------------------------------

The MIT License (MIT)

Copyright (c) 2016 Sebastian Schlecht

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""
import matplotlib.pyplot as plt
import matplotlib.mlab as mlab

import numpy as np
import sys
import os
import collections

from utils import get_files, load, transform_depth

DS_PATH = "../data"
TRASH_PATH = "../trash"
SNAP_PATH = "../snaps"

files = get_files(DS_PATH)
ordered_files = collections.OrderedDict(sorted(files.items()))
keys = [k for k, v in ordered_files.items()]

global key_idx
key_idx = 0

global pair_idx
pair_idx = 0

global current_key
current_key = keys[key_idx]


def get_current_pair():
    files = ordered_files[current_key][pair_idx]
    return [load(i) for i in files]


def render():
    ax1.cla()
    ax2.cla()
    ax3.cla()
    ax4.cla()
    ax5.cla()
    ax6.cla()

    rgb, depth = get_current_pair()
    rgb = rgb.transpose((1,2,0))
    depth = transform_depth(depth)
    gray = np.dot(rgb[...,:3], [0.299, 0.587, 0.114])
    dx = np.diff(gray, axis=1)[1:,:] # remove the first row
    dy = np.diff(gray, axis=0)[:,1:] # remove the first column
    dnorm = np.sqrt(dx**2 + dy**2)
    sharpness = np.average(dnorm)

    ax1.imshow(rgb)
    ax1.set_title("RGB")

    ax4.imshow(-gray, cmap=plt.get_cmap('Greys'))
    ax4.set_title("Grayscale")

    ax2.imshow(depth, cmap=plt.get_cmap('Greys'))
    ax2.set_title("Depth (Greyscale)")

    ax5.imshow(depth)
    ax5.set_title("Depth (Jet)")

    text =  "Relative sharpness: %f\n" % (sharpness)
    text += "Current class: %s\n" % current_key
    text += "File-Id: %s\n" % ordered_files[current_key][pair_idx][0].replace("_bgr.npz", "")
    ax3.text(0, 0, text, fontsize=10, transform = ax3.transAxes)
    ax6.hist(depth.flatten(), 150, facecolor='green')

    fig.canvas.draw()

def next_class():
    global key_idx
    global current_key
    global pair_idx
    if key_idx + 1 >= len(keys):
        key_idx = 0
    else:
        key_idx += 1
    current_key = keys[key_idx]
    pair_idx = 0


def previous_class():
    global key_idx
    global current_key
    global pair_idx
    if key_idx - 1 < 0:
        key_idx = len(keys) - 1
    else:
        key_idx -= 1
    current_key = keys[key_idx]
    pair_idx = 0



def next_image():
    global pair_idx
    if pair_idx + 1 >= len(ordered_files[current_key]):
        pair_idx = 0
    else:
        pair_idx += 1

def previous_image():
    global pair_idx
    if pair_idx - 1 < 0:
        pair_idx = len(ordered_files[current_key]) - 1
    else:
        pair_idx -= 1

def delete():
    cname = current_key.split("/")[-1]
    files = ordered_files[current_key][pair_idx]
    try:
        for file in files:
            head, tail = os.path.split(file)
            if not os.path.exists(TRASH_PATH + "/" + cname):
                os.makedirs(TRASH_PATH + "/" + cname)
            os.rename(file, TRASH_PATH + "/" + cname + "/" + tail)

        del ordered_files[current_key][pair_idx]
    except Exception as e:
        print "Failed to move file %s to trash." % file

def snap():
    from PIL import Image

    cname = current_key.split("/")[-1]
    rgb, _ = get_current_pair()
    img = Image.fromarray(rgb.transpose((1,2,0)))
    img.save(SNAP_PATH + "/" + cname + ".jpg")



def press(event):
    if event.key == 'right':
        next_image()
    elif event.key == 'left':
        previous_image()
    elif event.key == 'down':
        next_class()
    elif event.key == 'up':
        previous_class()
    elif event.key == 'd':
        delete()
    elif event.key == 'c':
        snap()

    render()

fig, ((ax1, ax2, ax3), (ax4, ax5, ax6)) = plt.subplots(2,3)

fig.canvas.mpl_connect('key_press_event', press)
render()
plt.show()
