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

sensorProps = None

scheduler = Scheduler.getInstance()

import time

# Start up the scheduling system with one worker per local core
for i in range(0, multiprocessing.cpu_count()):
    w = LocalWorker(i, "wkr%i" % i)
    scheduler.registerWorker(w)

scheduler.start()
queue = RenderQueue()

image_width = 304
image_height = 228
# image_width = 320
# image_height = 240
num_samples = 64

mesh_file = 'data/car_000000027.ply'
#mesh_file = '/home/adrian/model/Medieval_City.obj'


def register_scene_config(scene, pmgr, scene_config):

        scene_node = pmgr.create(scene_config)
        scene.addChild(scene_node)
        scene.configure()

        scene.initialize()
        sceneResID = scheduler.registerResource(scene)
        return sceneResID

def init_scene():

    pmgr = PluginManager.getInstance()

    camera_pos = Vector(0, 0.0, -12)
    model_pos = Vector(0.5, -0.5, -2.0)

    #camera_pos = Vector(4, 44.0, -7.0)
    #model_pos = Vector(0.0, 0.0, 0.0)

    #camera_matrix = Transform(Matrix4x4([[0.1,0.017,-1.0,0.0],[0.0,1.0,0.0,0.1],[1.0,0.0,0.1,0.0],[4.3,-6.0,-7.0,1.0]]))

    cube_pos = Vector(-0.5, 0.0, -1.0)

    a = MitsubaShape(shape_type=MitsubaShape.PLY_TYPE, to_world=Transform.translate(model_pos), filename=mesh_file)
    b = MitsubaShape(shape_type=MitsubaShape.CUBE, to_world=Transform.translate(cube_pos))

    #integrator = create_integrator(RenderTargetType.AO, hide_emitters=False)
    integrator = create_integrator(RenderTargetType.DIRECT, hide_emitters=True)
    depth_integrator = create_integrator(RenderTargetType.INDEX, hide_emitters=True)

    sampler = Sampler(SamplerType.HALTON, num_samples=num_samples)
    film = Film(FilmType.LDR, image_width, image_height)
    sensor = Sensor(SensorType.PERSPECTIVE, sampler=sampler, film=film, to_world=Transform.translate(camera_pos))

    scene_config = {
        'type' : 'scene',
        'a': a.config,
        # 'b':b.config,
        # 'envmap' : {
        #      'type' : 'sunsky',
        #      'hour' : 12.0,
        #      'albedo' : Spectrum(1.0),
        #      'samplingWeight' : 1.0,
        # },
        # 'envmap' : {
        #      'type' : 'sunsky',
        #      #'hour' : 10.0,
        #      'radiance': Spectrum(1.0),
        #      'samplingWeight': 1.0
        # },
        'sensor' : sensor.config
    }

    # scene_config['cube'] = create_object('cube', Transform.translate(model_pos), bsdf=create_bsdf())

    yangles = range(0,1)
    xangles = range(0,1)
    num_views = len(xangles) * len(yangles)
    #step_size = 360/(num_views)
    step_size = 1

    #List containing the integrators to use in Multi-Pass rendering
    passes = [integrator, depth_integrator]

    start = time.time()
    render_count = 0
    num_scale = 1
    offset = num_scale/2
    print ("Size:", (num_views*num_scale))

    for x in xangles:
        for y in yangles:
            original_Z = camera_pos[2]
            for s in range(num_scale):

                #for y in range(yangles):
                    #Set the correct destination file
                new_camera = camera_pos
                z = (s - offset)
                print ("Z:", z)
                print(new_camera[2])
                new_camera[2] = original_Z + z
                print(new_camera[2])

                for p in passes:

                    i = render_count
                    scene = Scene()
                    pass_config = scene_config

                    destination = 'results/%03i' % i
                    if p.type == RenderTargetType.DEPTH:
                        destination += "_d"
                    elif p.type == RenderTargetType.NORMAL:
                        destination += "_n"

                    #Set the pass integrator
                    pass_config['integrator'] = p.config
                    sceneResID = register_scene_config(scene, pmgr, scene_config)

                    # Create a shallow copy of the scene so that the queue can tell apart the two
                    # rendering processes. This takes almost no extra memory
                    newScene = mitsuba.render.Scene(scene)
                    pmgr = PluginManager.getInstance()
                    newSensor = pmgr.createObject(scene.getSensor().getProperties())

                    #Calculate the rotations
                    yrotation = Transform.rotate(Vector(1, 0, 0), y)
                    xrotation = Transform.rotate(Vector(0, 1, 0), x)
                    rotationCur = xrotation * yrotation

                    #Set the new camera position, applying the rotations
                    new_pos = rotationCur*new_camera
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

                render_count += 1


    # Wait for all jobs to finish and release resources
    queue.waitLeft(0)

    finish = time.time()
    print("Run Time:", finish-start)

def main():
    # Encodes parameters on how to instantiate the 'perspective' plugin
    init_scene()

if __name__ == "__main__":
    main()