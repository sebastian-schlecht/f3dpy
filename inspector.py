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
    rgb, depth = get_current_pair()
    rgb = rgb.transpose((1,2,0))
    depth = transform_depth(depth)
    ax1.imshow(rgb)
    ax2.imshow(depth)

    ax1.set_title("Current class: %s\nFile-Id: %s" % (current_key, ordered_files[current_key][pair_idx][0].replace("_bgr.npz", "")))
    ax2.set_title("Max/Min Depth: %f/%f" % (depth.max(), depth.min()))

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
    elif event.key == 'j':
        next_class()
    elif event.key == 'h':
        previous_class()
    elif event.key == 'd':
        delete()
    elif event.key == 'c':
        snap()

    render()

fig, (ax1, ax2) = plt.subplots(1,2)

fig.canvas.mpl_connect('key_press_event', press)
render()
plt.show()
