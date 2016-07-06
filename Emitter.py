from __future__ import print_function
from mitsuba.core import *

class EmitterType:

    SUN_SKY = 'sunsky'
    SKY = 'sky'
    SUN = 'sun'
    DIRECTIONAL = 'directional'
    CONSTANT = 'constant'

class Emitter:

    def __init__(self, emitter_type, sample_weight=1.0, to_world=Transform()):
        self.type = emitter_type
        self.sample_weight = sample_weight
        self.to_world = to_world
        self.config = self.create_config()

    def create_config(self):

        config = {
            'type' : self.type,
            'toWorld': self.to_world,
            'sampleWeight': self.sample_weight
        }

        return config


class ComplexEmitter(Emitter):

    def __init__(self, emitter_type, to_world=Transform(), sample_weight=1.0, hour=15.0, min=0.0, sec=0.0,
                 albedo=Spectrum(), direction=Vector(0)):

        self.hour = hour
        self.min = min
        self.sec = sec
        self.albedo = albedo
        self.direction = direction
        Emitter.__init__(self, emitter_type, sample_weight=sample_weight, to_world=to_world)

          #self.configure()

    def create_config(self):
        config = Emitter.create_config(self)

        config['hour'] = self.hour
        config['min'] = self.min
        config['sec'] = self.sec

        if self.type == EmitterType.SUN_SKY or self.type == EmitterType.SKY or self.type == EmitterType.SUN:
            config['sunDirection'] = self.direction
        else:
            config['direction'] = self.direction

        if self.type == EmitterType.SUN_SKY or self.type == EmitterType.SKY:
            config['albedo'] = self.albedo

        return config

    def configure(self):
        self.config = self.create_config()

if __name__ == "__main__":

    # e = Emitter(EmitterType.DIRECTIONAL)
    # print (e.config)

    sunsky = ComplexEmitter(EmitterType.SUN_SKY, to_world=Transform.translate(Vector(10,0,0)),albedo=Spectrum(1.0), hour=12.0)
    print (sunsky.config)