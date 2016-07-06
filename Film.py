from __future__ import print_function
from mitsuba.core import *

class FilmType():
    LDR = 'ldrfilm'
    HDR = 'hdrfilm'


class Film:

    def __init__(self, film_type, width, height):
        self.type = film_type
        self.width = width
        self.height = height
        self.config = self.__create_config()

    def __create_config(self):

        film = {
            'type' : self.type,
            'width' : self.width,
            'height' : self.height,
            'banner' : False
        }

        return film
