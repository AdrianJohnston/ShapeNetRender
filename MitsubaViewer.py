import mitsuba, multiprocessing, sys
from mitsuba.core import *
from mitsuba.render import *
from PyQt4.QtCore import QPoint
from PyQt4.QtGui import QApplication, QMainWindow, QPainter, QImage

class MitsubaView(QMainWindow):

    def __init__(self):
        super(MitsubaView, self).__init__()
        self.setWindowTitle('Mitsuba/PyQt demo')
        self.initializeMitsuba()
        self.image = self.render(self.init_scene())
        self.resize(self.image.width(), self.image.height())


    def initializeMitsuba(self):
        # Start up the scheduling system with one worker per local core
        self.scheduler = Scheduler.getInstance()
        for i in range(0, multiprocessing.cpu_count()):

            w = LocalWorker(i, "wkr%i" % i)
            self.scheduler.registerWorker(w)
            # Create a queue for tracking render jobs
            self.queue = RenderQueue()
            # Get a reference to the plugin manager
            self.pmgr = PluginManager.getInstance()

        self.scheduler.start()

    def shutdownMitsuba(self):
        self.queue.join()
        self.scheduler.stop()

    def createScene(self):
        # Create a simple scene containing a sphere
        sphere = self.pmgr.createObject(Properties("sphere"))
        sphere.configure()
        scene = Scene()
        scene.addChild(sphere)
        scene.configure()
        # Don't automatically write an output bitmap file when the
        # rendering process finishes (want to control this from Python)
        scene.setDestinationFile('')
        return scene

    def init_scene(self):
        scene_node = self.pmgr.create({
            'type' : 'scene',
            'sphere' : {
                'type' : 'sphere',
            },
            'envmap' : {
                'type' : 'sunsky'
            },
            'integrator' : {
                'type' : 'field',
                'field' : 'distance'

            },
            'sensor' : {
                'type' : 'perspective',
                'toWorld' : Transform.translate(Vector(0, 0, -5)),
                'sampler' : {
                    'type' : 'halton',
                    'sampleCount' : 64

                },
                'film' : {
                    'type' : 'hdrfilm',
                        'width' : 500,
                        'height' : 500
                }
            }
        })

        # Set the integrator - TODO make it output field information


        return scene_node

    def render(self, scene):
        # Create a render job and insert it into the queue
        job = RenderJob('myRenderJob', scene, self.queue)
        job.start()
        # Wait for the job to finish
        self.queue.waitLeft(0)
        # Develop the camera's film into an 8 bit sRGB bitmap
        film = scene.getFilm()
        size = film.getSize()
        bitmap = Bitmap(Bitmap.ERGB, Bitmap.EUInt8, size)
        film.develop(Point2i(0, 0), size, Point2i(0, 0), bitmap)
        # Write to a PNG bitmap file
        outFile = FileStream("rendering.png", FileStream.ETruncReadWrite)
        bitmap.write(Bitmap.EPNG, outFile)
        outFile.close()
        # Also create a QImage (using a fast memory copy in C++)
        return QImage(bitmap.getNativeBuffer(),
        size.x, size.y, QImage.Format_RGB888)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawImage(QPoint(0, 0), self.image)
        painter.end()

def main():
    app = QApplication(sys.argv)
    view = MitsubaView()
    view.show()
    view.raise_()
    retval = app.exec_()
    view.shutdownMitsuba()
    sys.exit(retval)

if __name__ == '__main__':
    main()