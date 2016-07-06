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

# Start up the scheduling system with one worker per local core
for i in range(0, multiprocessing.cpu_count()):
    w = LocalWorker(i, "wkr%i" % i)
    scheduler.registerWorker(w)

scheduler.start()
queue = RenderQueue()

image_width = 400
image_height = 400
num_samples = 64



def init_scene():

    pmgr = PluginManager.getInstance()
    scene = Scene()
    scene.setDestinationFile('renderedResult')

    camera_pos = Vector(0, 0.0, -12)
    model_pos = Vector(0.5, -0.5, -2.0)

    a = MitsubaShape(shape_type=MitsubaShape.PLY_TYPE, to_world=Transform.translate(model_pos), filename='/media/adrian/Data/Datasets/train/02691156/model_0000003.obj')
    b = MitsubaShape(shape_type=MitsubaShape.CUBE, to_world=Transform.translate(model_pos))

    integrator = Integrator(Integrator.DIRECT, hide_emitters=True)

    sampler = Sampler(SamplerType.HALTON, num_samples=num_samples)
    film = Film(FilmType.LDR, image_width, image_height)
    sensor = Sensor(SensorType.PERSPECTIVE, sampler=sampler, film=film, to_world=Transform.translate(camera_pos))

    scene_config = {
        'type' : 'scene',
        'a': a.config,
        'envmap' : {
             'type' : 'sunsky',
             'hour' : 12.0,
             'albedo' : Spectrum(1.0),
             'samplingWeight' : 1.0,
        },
        # 'envmap' : {
        #      'type' : 'constant',
        #      #'hour' : 10.0,
        #      'radiance' : Spectrum(1.0),
        #      'samplingWeight' : 0.5
        # },
        # 'integrator' : {
        #     'type' : 'multichannel',
        #     'depth' : {
        #         'type' : 'field',
        #         'field' : 'distance'
        #     },
        # },
        'integrator' : integrator.config,
        'sensor' : sensor.config
    }

    # scene_config['cube'] = create_object('cube', Transform.translate(model_pos), bsdf=create_bsdf())
    scene_node = pmgr.create(scene_config)
    scene.addChild(scene_node)
    scene.configure()

    scene.initialize()
    sceneResID = scheduler.registerResource(scene)

    num_views = 6
    step_size = 360/(num_views)
    for i in range(num_views):
        destination = 'results/result_%03i' % i
        # Create a shallow copy of the scene so that the queue can tell apart the two
        # rendering processes. This takes almost no extra memory
        newScene = mitsuba.render.Scene(scene)
        pmgr = PluginManager.getInstance()
        newSensor = pmgr.createObject(scene.getSensor().getProperties())
        # <change the position of 'newSensor' here>

        rotationCur = Transform.rotate(Vector(0, 1, 0), i*step_size)
        new_pos = rotationCur*camera_pos
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
        job = RenderJob('myRenderJob' + str(i), newScene, queue, sceneResID)
        job.start()

    # Wait for all jobs to finish and release resources
    queue.waitLeft(0)

def main():
    # Encodes parameters on how to instantiate the 'perspective' plugin
    init_scene()

if __name__ == "__main__":
    main()