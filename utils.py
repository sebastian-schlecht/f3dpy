"""
Package of helpers for reading Food3D data. The data itself is stored
in binary form using compressed numpy arrays. Appropriate files for loading
are provided below. Please note that we already did the registration on-the-fly
before dumping the frames; accelerometer data has not been captured as
we did not have access to the sensor via our API at the point of recording.

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

import os
import numpy as np
import h5py
import random

def load(filename):
    """
    Load a record file from disk into memory
    """
    if not os.path.isfile(filename):
        raise ValueError("File %s does not exist." % filename)
    try:
        if filename.endswith("_depth.npz"):
            return np.load(filename)["arr_0"].astype(np.float32)
        elif filename.endswith("_bgr.npz"):
            array = np.load(filename)["arr_0"]

            # Arrays are BGRA, we ommit alpha values
            array = array[:,:,0:3]

            # We barrel roll to RGB and transpose channels to first axis
            return array[:,:,::-1].transpose((2, 0, 1)).astype(np.uint8)
        else:
            raise ValueError("File doesn't seem to be food3d data.")
    except Exception as e:
        print "Could not read file: %s with error: %s" % (filename, str(e))


def convert_npy_to_npz(filename):
    data = np.load(filename)
    new_name = filename.replace(".npy", "") + ".npz"
    np.savez(new_name, data)

def transform_depth(depth):
    """
    Transform the depth into the space of meters and clean invalid values
    """
    depth[depth == np.inf] = 0
    depth[depth == np.nan] = 0

    # Convert to meters
    return depth / 1000.


def _parse_and_build(classes, filename, f):
    """
    Parse a given hash of classes, read the files one by one and dump them into the DB as specified by 'filename'
    """
    try:
        os.remove(filename)
    except:
        pass

    tuples = []
    for key in classes:
        for t in classes[key]:
            tuples.append(t)

    if len(tuples) == 0:
        return
    # Shuffle
    random.shuffle(tuples)

    # Create db
    file = h5py.File(filename)

    images = []
    depths = []

    idx = 0
    for t in tuples:
        print "Reading RGBD pair %i out of %i" % (idx, len(tuples))
        idx += 1
        rgb = load(t[0])
        if rgb is not None:
            images.append(rgb[np.newaxis,:,::f,::f])
        d = load(t[1])
        if d is not None:
            d = transform_depth(d)
            depths.append(d[np.newaxis,::f,::f])

    images = np.concatenate(images)
    depths = np.concatenate(depths)

    file.create_dataset("images", data=images)
    file.create_dataset("depths", data=depths)

    file.close()


def get_files(dataset):
    """
    Get files by reading their names from the folders
    """
    # Get all subdirectories
    subdirs = [os.path.join(dataset,o) for o in os.listdir(dataset) if os.path.isdir(os.path.join(dataset,o))]

    # Crawl files
    classes = {}
    for dir in subdirs:
        classes[dir] = []
        bgrs = [os.path.join(dir,o) for o in os.listdir(dir) if os.path.isfile(os.path.join(dir,o)) and o.endswith("_bgr.npz")]
        for bgr in bgrs:
            depth = bgr.split("_bgr.npz")[0] + "_depth.npz"
            classes[dir].append((bgr, depth))

    return classes

def sample(dataset, to):
    """
    Randomly sample images from the classes into a folder
    """
    classes = get_files(dataset=dataset)

    for key in classes:
        cname = key.split("/")[2]
        arr = classes[key]
        i = np.random.randint(len(arr))
        pair = arr[i]
        rgb = load(pair[0]).transpose((1,2,0))

        from PIL import Image
        img = Image.fromarray(rgb)
        img.save(to + "/" + cname + ".jpg")


def build_db(dataset, target, f, split=0.7):
    """
    Parse files and write to HDF5 DBs
    """
    classes = get_files(dataset)
    # Partition DB
    c_array = [(key, classes[key]) for key in classes]
    c_array_sorted = sorted(c_array, key= lambda item : len(item[1]))

    train = {}
    val = {}
    idx = 0.
    n = float(len(c_array_sorted))

    # TODO Think of a better split
    for element in reversed(c_array_sorted):
        p = np.random.randint(0,1000) / 1000.
        if p < split:
            train[element[0]] = element[1]
        else:
            val[element[0]] = element[1]
        idx += 1.

    _parse_and_build(train, "%s-train.h5" % target, f)
    _parse_and_build(val, "%s-val.h5" % target, f)
