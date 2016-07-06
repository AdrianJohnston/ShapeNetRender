from __future__ import print_function
from RenderUtils import *


class IntegratorType:
    MULTI = 'multichannel'
    DIRECT = 'direct'
    AO = 'ao',
    PATH = 'path'
    #TODO: Add others

def create_integrator(integrator_type, hide_emitters=False):

    if type_check(integrator_type, IntegratorType):
        return Integrator(integrator_type, hide_emitters)
    elif type_check(integrator_type, RenderTargetType):
        return MultiChannelIntegrator(integrator_type, hide_emitters)
    else:
        raise Exception('Invalid Integrator Type')


class Integrator:

    def __init__(self, integrator_type, hide_emitters=False):
        self.type = integrator_type
        self.hide_emitters = hide_emitters
        self.config = self.create_config()

    def create_config(self):
        result = {
            'type': self.type,
            'hideEmitters': self.hide_emitters
        }
        return result


class RenderTargetType(IntegratorType):
    '''
    position: 3D position in world space
    relPosition: 3D position in camera space
    distance: Ray distance to the shading point
    geoNormal: Geometric surface normal
    shNormal: Shading surface normal
    uv: UV coordinate value
    albedo: Albedo value of the BSDF
    # shapeIndex: Integer index of the high-level shape
    primIndex: Integer shape primitive index
    '''

    DEPTH = 'distance'
    NORMAL = 'geoNormal'
    POSITION = 'position'
    CAMERA_POS = 'relPosition'
    SH_NORMAL = 'shNormal'
    UV = 'uv'
    ALBEDO = 'albedo'
    SHAPE_INDEX = 'shapeIndex'
    INDEX = 'primIndex'




class MultiChannelIntegrator(Integrator):
    '''
    This is a complex integrator for retrieving fields from the scene. Similar to Multiple Render Targets in OpenGL
    Note: If there is more than one attachment, the Film needs to be HDR
    '''

    # 'integrator' : {
        #     'type' : 'multichannel',
        #     'depth' : {
        #         'type' : 'field',
        #         'field' : 'distance'
        #     },
    # }


    def __init__(self, integrator_type, hide_emitters=False):

        self.type = integrator_type
        self.hide_emitters = hide_emitters
        Integrator.__init__(self, integrator_type, hide_emitters)
        self.attach_render_target(self.type)

    def create_config(self):
        config = Integrator.create_config(self)
        config['type'] = 'multichannel'
        return config

    def attach_render_target(self, target_type):
        self.config[target_type] = {
            'type': 'field',
            'field': target_type,
            'undefined': 1.0
        }


if __name__ == "__main__":

    integrator = create_integrator(RenderTargetType.DEPTH)
    print(integrator.config)
