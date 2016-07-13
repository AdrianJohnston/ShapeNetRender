import sys
sys.path.append("/home/adrian/Software/blender-2.75a-linux-glibc211-x86_64/2.75/python/lib/python3.4/site-packages/")
import bpy
import os
import argparse
from mathutils import *
from math import *

def scale_mesh(obj):
    #Centre the obj
    #obj.matrix_world = Matrix()
    bb = obj.bound_box
    bx = bb[7][0]
    by = bb[7][1]
    bz = bb[7][2]
    factor = max(bx, max(by,bz))
    print ("Scaling by ", factor)
    sf = 1.0 / factor if not factor == 0.0 else 1.0
    obj.scale = Vector([sf,sf,sf])


def centre_mesh(obj):

    bb = obj.bound_box

    max = Vector(bb[7])
    min = Vector(bb[0])
    centre = (max - min) / 2
    obj.location -= centre


def preprocess_mesh(obj):
    #Reset the rotation
    # obj.rotation_euler = (0,0,0)
    scale_mesh(obj)
    return obj


def export_obj(filepath):

    bpy.ops.export_scene.obj(filepath=filepath, axis_forward='-Z', axis_up='Y',
                             use_mesh_modifiers=True, use_edges=True, use_smooth_groups=True,
                             use_smooth_groups_bitflags=False, use_normals=True, use_uvs=True, use_materials=True,
                             use_triangles=False)

    return


def export_ply(filepath):
    bpy.ops.export_mesh.ply(filepath=filepath, axis_forward='-Z', axis_up='Y')
    return


def blender_preprocess(input_file, output_file, export_type):

    #Import the mesh
    bpy.ops.import_scene.obj(filepath=input_file, )

    filename = input_file.split("/")[-1].split(".")[0]
    obj = bpy.data.objects[filename]
    print (obj.name)
    # preprocess_mesh(obj)

    export_type = export_type.lower()
    if export_type == 'obj':
        export_obj(output_file)
    elif export_type == 'ply':
        bpy.context.scene.objects.active = obj
        export_ply(output_file)
    else:
        print("Export type:", export_type, "not supported")

if __name__ == "__main__":

    argv = sys.argv
    argv = argv[argv.index("--") + 1:]

    sys.argv = argv
    usage_text = \
        "Run blender in background mode with this script:"
    "  blender --background --python " + __file__ + " -- [options]"

    parser = argparse.ArgumentParser(description=usage_text)
    parser.add_argument('-i', '--input', required=True, help='Input file')
    parser.add_argument('-o', '--output', required=True, help='Output file')
    parser.add_argument('-t', '--export_type', default='ply', help='Output File Format [obj, ply] are supported')
    args = parser.parse_args(sys.argv)

    blender_preprocess(args.input, args.output, args.export_type)

