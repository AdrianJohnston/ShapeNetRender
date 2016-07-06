from __future__ import print_function
import sys
import os
import argparse
import glob

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



def process(cmd, input_file, output_path, filetype='obj'):


    new_file = os.path.split(input_file)[1].split('.')[0]
    output_file = os.path.join(output_path, new_file)
    cmd = cmd + "-i " + input_file + " -o " + output_file + '.' +filetype.lower()
    return cmd

    # if os.path.exists(new_binvox_path):
    #    output_binvox_file = new_binvox_path.split('/')[-1]
    #    output_binvox_file = os.path.join(output_path, output_binvox_file)
    #    # print(new_binvox_path, output_binvox_file)
    #    os.rename(new_binvox_path, output_binvox_file)

def dry_exec(cmd, debug=False):
    if debug:
        print(cmd)

    return cmd

def exec_cmd(cmd):
    os.system(cmd)
    return cmd

import multiprocessing as mp

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description = 'Default Experiment Template')
    parser.add_argument('-i', '--input_dir', required=True, help='Input folder directory')
    parser.add_argument('-o', '--output_dir', default= output_dir,help='Model directory to load or save model_file from')
    parser.add_argument('-b', '--blender_path', default=cwd, type=str)
    parser.add_argument('-n', '--num_classes', default=55, type=int)
    parser.add_argument('-d', '--dry_run', default=False, action='store_true')
    parser.add_argument('-j', '--num_processes', default=4)
    parser.add_argument('-t', '--export_type', default='ply', help='Output file type [obj, ply] supported')
    args = parser.parse_args()
    print (args)


    #Build the binvox terminal cmd
    blender_cmd = "$BLENDER -b -P " + os.path.join(cwd, 'preprocess_mesh.py') + " -- "

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

    pool_data = []

    for d, files in data.iteritems():
        # print(d)
        c = d.split('/')[-1]
        # print (c)

        #path contains the output directory
        path = os.path.join(args.output_dir, c)
        if not os.path.isdir(path):
            os.makedirs(path)

        for f in files:
            pool_data.append((d, f, path))

        # print(files)
    cmds = []
    for d, f, path in pool_data:
        cmd = process(blender_cmd, os.path.join(d, f), path, args.export_type)
        cmds.append(cmd)

    print(len(cmds))

    pool = mp.Pool(processes=args.num_processes)  # start 4 worker processes

    if args.dry_run:
        res = pool.map(dry_exec, cmds)
        print("Dry Run, num exec:", len(res))

    else:
        res = pool.map(exec_cmd, cmds)
        print("Full Run, num exec:", len(res))
