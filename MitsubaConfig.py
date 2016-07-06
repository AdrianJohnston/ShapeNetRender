from __future__ import print_function
import sys, os

def frange(x, y, step):
  while x < y:
    yield x
    x += step


working_dir = "Path/"
models = ["Hello," , "World"]
classes = ["Car", "Plane", "Chair", "Table", "Bed"]

image_width = 28
image_height = 28
# image_width = 320
# image_height = 240
num_samples = 32

yangles = [y for y in frange(5,16, 1.0)]
xangles = [x for x in frange(5,16, 1.0)]
num_views = len(xangles) * len(yangles)

MAX_VIEWS = 1000
num_passes = 2

total_views = num_views * num_passes

num_scale = 2
offset = num_scale/2
print ("Size:", (num_views*num_scale))
translations = [xt for xt in frange(-0.5,1.0, 0.5)]
num_images = len(yangles) * len(xangles) * len(translations) * len(translations) * num_scale
destination_path = '/home/adrian/Data/new_training/'

#Max number of renderers per instance
num_images_instace = num_images// MAX_VIEWS

#Direct lighting or Envmap lighting
scene_mode = "ENV_MAP"

