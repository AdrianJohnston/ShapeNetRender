import sys
sys.path.append("/home/adrian/Software/blender-2.75a-linux-glibc211-x86_64/2.75/python/lib/python3.4/site-packages/")
import bpy
import os


data_path = "/home/adrian/PycharmProjects/sandbox/data/"
file = "car_000000027"
file_ext = ".off"
output_ext = ".ply"
output_location = "/home/adrian/PycharmProjects/sandbox/data/"

#Import the mesh
bpy.ops.import_mesh.off(filepath=os.path.join(data_path, file) + file_ext)

#Need to add scaling and normailisation here

obj = bpy.data.objects[1]

#Reset the rotation
obj.rotation_euler = (0,0,0)

forward = '-Z'
up = 'Y'

bpy.ops.export_mesh.ply(filepath=os.path.join(data_path, file) + output_ext, axis_forward=forward, axis_up=up)