
class Material:

    TWO_SIDEDED = 'twosided'

    def __init__(self):
        self.config = self.__create_config()

    def __create_config(self):

        result = {
            'type' : 'twosided',
            'bsdf' : {
                'type' : 'roughdiffuse'
                #'specularReflectance' : Spectrum(0.4),
            }
        }

        return result