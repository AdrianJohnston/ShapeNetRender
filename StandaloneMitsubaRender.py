from __future__ import print_function
import mitsuba
from mitsuba.core import *
import mitsuba
from mitsuba.render import Scene
import multiprocessing
from mitsuba.render import *
from MitsubaShape import *
import sys, os
#My imports
from Material import *
from Integrator import *
from Sampler import *
from Sensor import *
from Film import *
import numpy as np


sensorProps = None

scheduler = Scheduler.getInstance()

import time

# Start up the scheduling system with one worker per local core
for i in range(0, 4):
    w = LocalWorker(i, "wkr%i" % i)
    scheduler.registerWorker(w)

scheduler.start()
queue = RenderQueue()
#
# image_width = 224
# image_height = 224
# # image_width = 320
# # image_height = 240
# num_samples = 32
#
# #mesh_file = 'data/car_000000027.ply'
# mesh_file = '/media/adrian/Data/test_objs/bath3.obj'
# # mesh_file = '/media/adrian/Data/Datasets/train/02691156/model_000003.obj'
#
# output_dir = '/media/adrian/Data/rendered_imgs/'

def frange(x, y, jump):
  while x < y:
    yield x
    x += jump

def register_scene_config(scene, pmgr, scene_config):

        scene_node = pmgr.create(scene_config)
        scene.addChild(scene_node)
        scene.configure()

        scene.initialize()
        sceneResID = scheduler.registerResource(scene)
        return sceneResID


def get_filename(filepath):

    filename = filepath.split('/')[-1].split('.')[0]
    return filename

def check_mkdir(dir):

    if not os.path.exists(dir):
        os.makedirs(dir)

    return

def append_dir_suffix(path, suffix):

    #Strip the trailing slash
    if path.endswith('/'):
        path = path[:-1]

    return path + '_' + suffix

def main(input_file, output_dir, output_name, img_width, img_height, num_samples):

    pmgr = PluginManager.getInstance()

    # Bed pos
    camera_pos = Vector(0, 2.5, 6.0)
    model_pos = Vector(0.0, 0, 0.0)

    a = MitsubaShape(shape_type=MitsubaShape.PLY_TYPE, to_world=Transform.translate(model_pos), filename=input_file)

    # integrator = create_integrator(RenderTargetType.AO, hide_emitters=False)
    integrator = create_integrator(RenderTargetType.DIRECT, hide_emitters=False)
    depth_integrator = create_integrator(RenderTargetType.DEPTH, hide_emitters=False)
    position_integrator = create_integrator(RenderTargetType.POSITION, hide_emitters=False)
    normal_integrator = create_integrator(RenderTargetType.NORMAL, hide_emitters=False)
    #uv_integrator = create_integrator(RenderTargetType.UV, hide_emitters=False)

    sampler = Sampler(SamplerType.HALTON, num_samples=num_samples)
    film = Film(FilmType.LDR, img_width, img_height)
    sensor = Sensor(SensorType.PERSPECTIVE, sampler=sampler, film=film, to_world=Transform.translate(camera_pos))

    scene_config = {
        'type': 'scene',
        'a': a.config,
        # 'b':b.config,
        'envmap': {
            'type': 'sunsky',
            'hour': 12.0,
            'albedo': Spectrum(1.0),
            'samplingWeight': 1.0,
        },
        # 'envmap' : {
        #      'type' : 'sunsky',
        #      #'hour' : 10.0,
        #      'radiance': Spectrum(1.0),
        #      'samplingWeight': 1.0
        # },
        'sensor': sensor.config
    }

    # scene_config['cube'] = create_object('cube', Transform.translate(model_pos), bsdf=create_bsdf())
    num_views = 6
    xangles = [y for y in frange(0, 360, np.floor(360 / num_views))]
    # xangles = [x for x in frange(0,12, 1.0)]
    yangles = [0.0]
    print(yangles)
    # num_views = len(xangles) * len(yangles)
    # step_size = 360/(num_views)
    step_size = 1

    # List containing the integrators to use in Multi-Pass rendering
    passes = [integrator, depth_integrator, normal_integrator, position_integrator]

    start = time.time()
    render_count = 0
    num_scale = 1
    offset = num_scale / 2
    print("Size:", (num_views * num_scale))

    # translations = [xt for xt in frange(-0.5,1.0, 0.5)]
    translations = []

    num_images = len(yangles) * len(xangles) * len(translations) * len(translations) * num_scale
    print("Number of images: ", str(num_images))

    j = None

    filename = get_filename(input_file)

    # for xt in translations:
    original_x = camera_pos[0]
    # for yt in translations:
    original_y = camera_pos[1]
    for x in xangles:
        for y in yangles:

            original_Z = camera_pos[2]
            new_camera = camera_pos
            new_camera[0] = original_x
            new_camera[2] = original_Z

            for p in passes:

                i = render_count
                scene = Scene()
                pass_config = scene_config

                destination = output_dir

                if p.type == RenderTargetType.DIRECT or p.type == RenderTargetType.PATH:
                    destination = os.path.join(destination, 'rgb')
                elif p.type == RenderTargetType.DEPTH:
                    destination = os.path.join(destination, 'depth')
                elif p.type == RenderTargetType.NORMAL:
                    destination = os.path.join(destination, 'normal')
                elif p.type == RenderTargetType.SH_NORMAL:
                    destination = os.path.join(destination, 'sh_normal')
                elif p.type == RenderTargetType.POSITION:
                    destination = os.path.join(destination, 'pos')
                elif p.type == RenderTargetType.UV:
                    destination = os.path.join(destination, 'uv')

                check_mkdir(destination)
                destination = os.path.join(destination, output_name + '_%03i' % (i))

                    # Set the pass integrator
                pass_config['integrator'] = p.config
                sceneResID = register_scene_config(scene, pmgr, scene_config)

                # Create a shallow copy of the scene so that the queue can tell apart the two
                # rendering processes. This takes almost no extra memory
                newScene = mitsuba.render.Scene(scene)
                pmgr = PluginManager.getInstance()
                newSensor = pmgr.createObject(scene.getSensor().getProperties())

                # Calculate the rotations
                yrotation = Transform.rotate(Vector(1, 0, 0), y)
                xrotation = Transform.rotate(Vector(0, 1, 0), x)
                rotationCur = xrotation * yrotation

                # Set the new camera position, applying the rotations
                new_pos = rotationCur * new_camera
                print(new_pos)
                new_transform = Transform.lookAt(Point(new_pos), Point(0, 0, 0), Vector(0, 1, 0))
                newSensor.setWorldTransform(new_transform)

                newFilm = pmgr.createObject(scene.getFilm().getProperties())
                newFilm.configure()
                newSensor.addChild(newFilm)
                newSensor.configure()
                newScene.addSensor(newSensor)
                newScene.setSensor(newSensor)
                newScene.setSampler(scene.getSampler())
                newScene.setDestinationFile(destination)

                # Create a render job and insert it into the queue. Note how the resource
                # ID of the original scene is provided to avoid sending the full scene
                # contents over the network multiple times.
                j = RenderJob('myRenderJob' + str(i), newScene, queue, sceneResID)
                j.start()

            queue.waitLeft(0)
            render_count += 1

        print("Full Set")

    # Wait for all jobs to finish and release resources
    queue.waitLeft(0)

    finish = time.time()
    print("Run Time:", finish - start)


def render(config):
    print ("Render Config:", config)
    return 10

import sys
import argparse
if __name__ == "__main__":

    args = sys.argv
    print (args)

    parser = argparse.ArgumentParser(description='Default Experiment Template')
    parser.add_argument('-i', '--input_mesh', default='/media/adrian/Data/test_objs/plane.ply', help='Input mesh file directory')
    parser.add_argument('-o', '--output_dir', default='/media/adrian/Data/rendered_imgs/', help='Directory to write imgs out to')
    parser.add_argument('-on', '--output_name', default='img', help='The output filename')
    parser.add_argument('-iw', '--img_width', default=224, type=int)
    parser.add_argument('-ih', '--img_height', default=224, type=int)
    parser.add_argument('-b', '--blender_path', default='/home/adrian/Software/blender-2.76b/blender', type=str)
    parser.add_argument('-nsm', '--num_samples' ,default=32, help="Number of raytracing samples")
    args = parser.parse_args()
    print(args)

    main(args.input_mesh, args.output_dir, args.output_name, args.img_width, args.img_height, args.num_samples)