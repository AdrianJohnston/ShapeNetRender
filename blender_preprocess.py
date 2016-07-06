import sys
sys.path.append("/home/adrian/Software/blender-2.75a-linux-glibc211-x86_64/2.75/python/lib/python3.4/site-packages/")
import bpy
import os


from __future__ import print_function
import sys, os
import argparse
import glob


def blender_preprocess():

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



binvox_exec = "binvox"
binvox_args = "-e"
cwd = os.getcwd()

output_dir = os.path.join(cwd, 'output')

filetypes = ['*.obj', '*.off', '*.ply']

def insensitive_glob(pattern):
    def either(c):
        return '[%s%s]'%(c.lower(),c.upper()) if c.isalpha() else c
    return glob.glob(''.join(map(either,pattern)))


def get_files(d):

	os.chdir(d)
	files = []
	for t in filetypes:
		r = insensitive_glob(t)
		if len(r) > 0:
			files = files + r

	return files

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description = 'Default Experiment Template')
	parser.add_argument('-i', '--input_dir', required=True, help='Input folder directory')
	parser.add_argument('-o', '--output_dir', default= output_dir,help='Model directory to load or save model_file from')
	parser.add_argument('-d', '--output_dim', default=32, type=int)
	parser.add_argument('-b', '--binvox_path', default=cwd, type=str)
	parser.add_argument('-n', '--num_classes', default=55, type=int)
	parser.add_argument('-t', '--output_type', default='binvox', help='specify voxel file type (default binvox, also supported: hips, mira, vtk, raw, schematic, msh)')
	args = parser.parse_args()
	print (args)


	#Build the binvox terminal cmd
	binvox_exec = os.path.join(args.binvox_path, binvox_exec)
	binvox_exec = binvox_exec + " -e -cb -d " + str(args.output_dim) + " -t " + args.output_type

	classes = []

	input_dir_abs = os.path.abspath(args.input_dir)
	for d in os.listdir(input_dir_abs):

		path = os.path.join(input_dir_abs, d)
		# add only dirs
		if os.path.isdir(path):
			classes.append(path)



	#They are all in one directory - Use the input directory
	FLAT_DIRECTORY  = len(classes) == 0
	if FLAT_DIRECTORY:
		print("Flat directory, using input directory")
		classes.append(input_dir_abs)

	print(classes)


	data = {}

	for d in classes:
		data[d] = get_files(d)

	for d, files in data.iteritems():
		# print(d)
		c = d.split('/')[-1]
		print (c)

		#path contains the output directory
		path = os.path.join(args.output_dir, c)
		if not os.path.isdir(path):
			os.makedirs(path)

		# print(files)
		for f in files:
			convert2binvox(os.path.join(d, f),path)


