from mitsuba.core import *

def create_bsdf():

    material = {
        'type' : 'twosided',
        'bsdf' : {
            'type' : 'roughdiffuse',
            #'specularReflectance' : Spectrum(0.4),
        }
    }
    return material

class MitsubaShape:

    PLY_TYPE = 'ply'
    OBJ_TYPE = 'obj'
    CUBE = 'cube'
    SPHERE = 'sphere'
    CONE = 'cone'
    #Add more as needed

    default_material = create_bsdf()

    def __init__(self, shape_type, bsdf=default_material, to_world=Transform(),flip_normals=False, filename=""):
        self.type = shape_type
        print ('Type:', self.type)
        self.bsdf = bsdf
        self.to_world = to_world
        self.flip_normals = flip_normals
        self.filename = filename
        self.config = self.__create_config()

    def __create_config(self):
        object = {
        'type' : self.type,
        'toWorld' : self.to_world,
        'bsdf' : self.bsdf,
        'flipNormals' : self.flip_normals,
        }

        if self.type == MitsubaShape.PLY_TYPE or self.type == MitsubaShape.OBJ_TYPE:
            object['filename'] = self.filename

        return object

