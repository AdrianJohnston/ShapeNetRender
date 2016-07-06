from __future__ import print_function
from mitsuba.core import *
import mitsuba
from mitsuba.render import Scene
import multiprocessing
from mitsuba.render import *
from MitsubaShape import *

#My imports
from Material import *
from Integrator import *
from Sampler import *
from Sensor import *
from Film import *
from MitsubaConfig import *

sensorProps = None

scheduler = Scheduler.getInstance()

import time

# Start up the scheduling system with one worker per local core
# for i in range(0, multiprocessing.cpu_count()):
for i in range(0, 4):

    w = LocalWorker(i, "wkr%i" % i)
    scheduler.registerWorker(w)

scheduler.start()
queue = RenderQueue()


#mesh_file = 'data/car_000000027.ply'
#mesh_file = '/home/adrian/model/Medieval_City.obj'

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


def render_scene(passes, scene_config, render_config):

    camera_params = render_config["CameraParams"]
    start= render_config["iteration_start"]
    end= render_config["iteration_end"]
    output_path = render_config["OutputPath"]
    pmgr = PluginManager.getInstance()

    for index in range(start,end):
        camera = camera_params[index]
        new_transform = camera["new_transform"]
        for p in passes:

            destination = output_path + '%03i' % (index)
            if p.type == RenderTargetType.DEPTH:
                destination += "_d"
            elif p.type == RenderTargetType.NORMAL:
                destination += "_n"

            scene = Scene()
            pass_config = scene_config
            #Set the pass integrator
            pass_config['integrator'] = p.config
            sceneResID = register_scene_config(scene, pmgr, scene_config)

            newScene = mitsuba.render.Scene(scene)
            pmgr = PluginManager.getInstance()
            newSensor = pmgr.createObject(scene.getSensor().getProperties())
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
            j = RenderJob('myRenderJob' + str(index), newScene, queue, sceneResID)
            j.start()

        queue.waitLeft(0)

def compute_configs(model_pos, camera_pos):

    configs = []

    for xt in translations:
        original_x = camera_pos[0]
        for yt in translations:
            original_y = camera_pos[1]
            for x in xangles:
                for y in yangles:
                    original_Z = camera_pos[2]
                    for s in range(num_scale):

                        #for y in range(yangles):
                            #Set the correct destination file
                        new_camera = camera_pos
                        z = (s - offset)

                        new_camera[0] = original_x + xt
                        new_camera[2] = original_Z + z
                        current_config = {}
                        current_config["Camera"]  = new_camera
                        current_config["X"]= x
                        current_config["Y"]= y
                        current_config["scale"]= s

                        yrotation = Transform.rotate(Vector(1, 0, 0), y)
                        xrotation = Transform.rotate(Vector(0, 1, 0), x)
                        rotationCur = xrotation * yrotation
                        #
                        #     #Set the new camera position, applying the rotations
                        new_pos = rotationCur*new_camera
                        new_transform = Transform.lookAt(Point(new_pos), Point(0, 0, 0), Vector(0, 1, 0))
                        current_config["new_pos"] = new_pos
                        current_config["new_transform"] = new_transform
                        configs.append(current_config)

    return configs

def init_scene(render_config):


    model_pos = render_config["InitialModelPos"]
    camera_pos = render_config["InitialCameraPos"]
    mesh_file = render_config["MeshFile"]
    #Bed pos - This needs to be configured per class perhaps

    #camera_matrix = Transform(Matrix4x4([[0.1,0.017,-1.0,0.0],[0.0,1.0,0.0,0.1],[1.0,0.0,0.1,0.0],[4.3,-6.0,-7.0,1.0]]))
    a = MitsubaShape(shape_type=MitsubaShape.PLY_TYPE, to_world=Transform.translate(model_pos), filename=mesh_file)

    #integrator = create_integrator(RenderTargetType.AO, hide_emitters=False)
    integrator = create_integrator(RenderTargetType.DIRECT, hide_emitters=True)
    depth_integrator = create_integrator(RenderTargetType.DEPTH, hide_emitters=True)

    sampler = Sampler(SamplerType.HALTON, num_samples=num_samples)
    film = Film(FilmType.LDR, image_width, image_height)
    sensor = Sensor(SensorType.PERSPECTIVE, sampler=sampler, film=film, to_world=Transform.translate(camera_pos))

    #List containing the integrators to use in Multi-Pass rendering
    passes = [integrator, depth_integrator]

    if scene_mode == "DIRECT":

        scene_config = {
            'type' : 'scene',
            'a': a.config,
            'sensor' : sensor.config
        }
    elif scene_mode == "ENV_MAP":

        scene_config = {
            'type' : 'scene',
            'a': a.config,
            'envmap' : {
                 'type' : 'sunsky',
                 #'hour' : 10.0,
                 'radiance': Spectrum(1.0),
                 'samplingWeight': 1.0
            },
            'sensor' : sensor.config
        }
    else:
        print("ERROR please set scene mode")
        sys.exit(-1)


    start_t = time.time()
    render_scene(passes, scene_config, render_config)

    # Wait for all jobs to finish and release resources
    queue.waitLeft(0)

    finish_t = time.time()
    print("Run Time:", finish_t-start_t)

def main():
    # Encodes parameters on how to instantiate the 'perspective' plugin
    render_config = {}

    model_pos = Vector(0.0, 0.0, 0.0)
    camera_pos = Vector(0, 2.5, 5.0)
    render_config["InitialModelPos"] = model_pos
    render_config["InitialCameraPos"] = camera_pos
    config = compute_configs(model_pos, camera_pos)
    render_config["OutputPath"] = destination_path
    render_config["CameraParams"] = config
    render_config["iteration_start"] = 2
    render_config["iteration_end"] = 4
    render_config["MeshFile"] = '/home/adrian/Data/bed1.ply'

    init_scene(render_config)

    ##OLD POSITIONS
    #Car pos
    # camera_pos = Vector(0, 0.0, -12)
    # model_pos = Vector(0.5, -0.5, -2.0)

    #camera_pos = Vector(4, 44.0, -7.0)
    #model_pos = Vector(0.0, 0.0, 0.0)


def start(args):

    render_config = {}
    start, end = args

    model_pos = Vector(0.0, 0.0, 0.0)
    camera_pos = Vector(0, 2.5, 5.0)
    config = compute_configs(model_pos, camera_pos)

    render_config["InitialModelPos"] = model_pos
    render_config["InitialCameraPos"] = camera_pos
    render_config["OutputPath"] = destination_path
    render_config["CameraParams"] = config
    render_config["MeshFile"] = '/home/adrian/Data/bed1.ply'
    render_config["iteration_start"] = int(start)
    render_config["iteration_end"] = int(end)
    render_config["InitialModelPos"] = Vector(render_config["InitialModelPos"])
    render_config["InitialCameraPos"] = Vector(render_config["InitialCameraPos"])

    init_scene(render_config)




import sys

if __name__ == "__main__":

    args = sys.argv
    print (args)


    start(args[1:])