import mitsuba, multiprocessing, sys, time
from mitsuba.core import Scheduler, PluginManager, Thread, Vector, Point2i, \
Vector2i, LocalWorker, Properties, Bitmap, Spectrum, Appender, EWarn, \
Transform, FileStream
from mitsuba.render import RenderQueue, RenderJob, Scene, RenderListener
from PyQt4.QtCore import Qt, QPoint, QSize, QRect, pyqtSignal
from PyQt4.QtGui import QApplication, QMainWindow, QPainter, QImage, \
QProgressBar, QWidget, QSizePolicy
Signal = pyqtSignal
class MitsubaRenderBuffer(RenderListener):
    """
    Implements the Mitsuba callback interface to capture notifications about
    rendering progress. Partially completed image blocks are efficiently
    tonemapped into a local 8-bit Mitsuba Bitmap instance and exposed as a QImage.
    """
    RENDERING_FINISHED = 0
    RENDERING_CANCELLED = 1
    RENDERING_UPDATED = 2

    GEOMETRY_CHANGED = 3
    def __init__(self, queue, callback):
        super(MitsubaRenderBuffer, self).__init__()
        self.bitmap = self.qimage = None
        self.callback = callback
        self.time = 0
        self.size = Vector2i(0, 0)
        queue.registerListener(self)

    def workBeginEvent(self, job, wu, thr):
        """ Callback: a worker thread started rendering an image block.
        Draw a rectangle to highlight this """
        _ = self._get_film_ensure_initialized(job)
        self.bitmap.drawWorkUnit(wu.getOffset(), wu.getSize(), thr)
        self._potentially_send_update()

    def workEndEvent(self, job, wr, cancelled):
        """ Callback: a worker thread finished rendering an image block.
        Tonemap the associated pixels and store them in 'self.bitmap' """
        film = self._get_film_ensure_initialized(job)
        film.develop(wr.getOffset(), wr.getSize(), wr.getOffset(), self.bitmap)
        self._potentially_send_update()

    def refreshEvent(self, job):
        """ Callback: the entire image changed (some rendering techniques
        do this occasionally). Hence, tonemap the full film. """
        film = self._get_film_ensure_initialized(job)
        film.develop(Point2i(0), self.size, Point2i(0), self.bitmap)
        self._potentially_send_update()

    def finishJobEvent(self, job, cancelled):
        """ Callback: the rendering job has finished or was cancelled.
        Re-develop the image once more for the final result. """
        film = self._get_film_ensure_initialized(job)
        film.develop(Point2i(0), self.size, Point2i(0), self.bitmap)
        self.callback(MitsubaRenderBuffer.RENDERING_CANCELLED if cancelled else MitsubaRenderBuffer.RENDERING_FINISHED)

    def _get_film_ensure_initialized(self, job):
        """ Ensure that all internal data structure are set up to deal
        with the given rendering job """
        film = job.getScene().getFilm()
        size = film.getSize()

        if self.size != size:
            self.size = size
            # Round the buffer size to the next power of 4 to ensure 32-bit
            # aligned scanlines in the underlying buffer. This is needed so
            # that QtGui.QImage and mitsuba.Bitmap have exactly the same
            # in-memory representation.

            bufsize = Vector2i((size.x + 3) // 4 * 4, (size.y + 3) // 4 * 4)
            # Create an 8-bit Mitsuba bitmap that will store tonemapped pixels
            self.bitmap = Bitmap(Bitmap.ERGB, Bitmap.EUInt8, bufsize)
            self.bitmap.clear()
            # Create a QImage that is backed by the Mitsuba Bitmap instance
            # (i.e. without doing unnecessary bitmap copy operations)
            self.qimage = QImage(self.bitmap.getNativeBuffer(), self.size.x,
            self.size.y, QImage.Format_RGB888)
            self.callback(MitsubaRenderBuffer.GEOMETRY_CHANGED)
        return film

    def _potentially_send_update(self):
        """ Send an update request to any attached widgets, but not too often """
        now = time.time()
        if now - self.time > .25:
            self.time = now
            self.callback(MitsubaRenderBuffer.RENDERING_UPDATED)

class RenderWidget(QWidget):
    """ This simple widget attaches itself to a Mitsuba RenderQueue instance
    and displays the progress of everything that's being rendered """
    renderingUpdated = Signal(int)

    def __init__(self, parent, queue, default_size = Vector2i(0, 0)):
        QWidget.__init__(self, parent)
        self.buffer = MitsubaRenderBuffer(queue, self.renderingUpdated.emit)
        # Need a queued conn. to avoid threading issues between Qt and Mitsuba
        self.renderingUpdated.connect(self._handle_update, Qt.QueuedConnection)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.default_size = default_size

    def sizeHint(self):
        size = self.buffer.size if not self.buffer.size.isZero() else self.default_size
        return QSize(size.x, size.y)

    def _handle_update(self, event):
        image = self.buffer.qimage
        # Detect when an image of different resolution is being rendered
        if image.width() > self.width() or image.height() > self.height():
            self.updateGeometry()
            self.repaint()

    def paintEvent(self, event):
        """ When there is more space then necessary, display the image centered
        on a black background, surrounded by a light gray border """
        QWidget.paintEvent(self, event)
        qp = QPainter(self)
        qp.fillRect(self.rect(), Qt.black)
        image = self.buffer.qimage

        if image is not None:
            offset = QPoint((self.width() - image.width()) / 2, (self.height() - image.height()) / 2)
            qp.setPen(Qt.lightGray)
            qp.drawRect(QRect(offset - QPoint(1, 1), image.size() + QSize(1, 1)))
            qp.drawImage(offset, image)

        qp.end()

class MitsubaDemo(QMainWindow):
    renderProgress = Signal(int)

    def __init__(self):
        super(MitsubaDemo, self).__init__()
        # Initialize Mitsuba
        self.initializeMitsuba()
        self.job = self.createRenderJob()
        self.job.setInteractive(True)
        # Initialize the user interface
        status = self.statusBar()
        self.rwidget = RenderWidget(self, self.queue, self.scene.getFilm().getSize())
        progress = QProgressBar(status)
        status.setContentsMargins(0,0,5,0)
        status.addPermanentWidget(progress)
        status.setSizeGripEnabled(False)
        self.setWindowTitle('Mitsuba/PyQt demo')
        self.setCentralWidget(self.rwidget)

        # Hide the scroll bar once the rendering is done
        def renderingUpdated(event):

            if event == MitsubaRenderBuffer.RENDERING_FINISHED:
                status.showMessage("Done.")
                progress.hide()

        self.renderProgress.connect(progress.setValue, Qt.QueuedConnection)
        self.rwidget.renderingUpdated.connect(renderingUpdated, Qt.QueuedConnection)

        # Start the rendering process
        status.showMessage("Rendering ..")
        self.job.start()

    def initializeMitsuba(self):
        # Start up the scheduling system with one worker per local core
        self.scheduler = Scheduler.getInstance()
        for i in range(0, multiprocessing.cpu_count()):
            self.scheduler.registerWorker(LocalWorker(i, 'wrk%i' % i))

        self.scheduler.start()
        # Create a queue for tracking render jobs
        self.queue = RenderQueue()
        # Get a reference to the plugin manager
        self.pmgr = PluginManager.getInstance()
        # Process Mitsuba log and progress messages within Python

        class CustomAppender(Appender):
            def append(self2, logLevel, message):
                print(message)

            def logProgress(self2, progress, name, formatted, eta):
                # Asynchronously notify the main thread
                self.renderProgress.emit(progress)

        logger = Thread.getThread().getLogger()
        logger.setLogLevel(EWarn) # Display warning & error messages
        logger.clearAppenders()
        logger.addAppender(CustomAppender())

        def closeEvent(self, e):
            self.job.cancel()
            self.queue.join()
            self.scheduler.stop()

    def createRenderJob(self):
        self.scene = self.pmgr.create({
        'type' : 'scene',
        'sphere' : {
        'type' : 'sphere',
        },
        'envmap' : {
        'type' : 'sky'
        },
        'sensor' : {
        'type' : 'perspective',
        'toWorld' : Transform.translate(Vector(0, 0, -5)),
        'sampler' : {
        'type' : 'halton',
        'sampleCount' : 64
        }
        }
        })

        return RenderJob('rjob', self.scene, self.queue)

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            self.close()

def main():
    import signal
    # Stop the program upon Ctrl-C (SIGINT)
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = QApplication(sys.argv)
    demo = MitsubaDemo()
    demo.show()
    demo.raise_()
    retval = app.exec_()
    sys.exit(retval)

if __name__ == '__main__':
    main()