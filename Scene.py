import mitsuba
from mitsuba.core import *

class Scene:

    def __init__(self):
        self.graph = []
        self.config = self.__create_config()

    def attach_node(self, node):
        self.graph.append(node)
        self.config.update(node)

    def __create_config(self):
        scene = {
            'type': 'scene'
        }
