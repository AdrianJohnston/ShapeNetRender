from __future__ import print_function
from mitsuba.core import *

class SensorType:
    PERSPECTIVE = 'perspective'
    ORTHOGRAPIC = 'orthographic'

class Sensor:

    def __init__(self, sensor_type, sampler, film, to_world=Transform()):
        self.type = sensor_type
        self.sampler = sampler
        self.film =film
        self.to_world = to_world
        self.config = self.__create_config()

    def __create_config(self):
        sensor = {
            'type': self.type,
            'toWorld': self.to_world,
            'sampler': self.sampler.config,
            'film': self.film.config,
            'nearClip' : 1.0,
            'farClip': 20.0,
        }

        return sensor