class SamplerType:

    HALTON = 'halton'
    #TODO: Check these Samplers
    SOBEL = 'sobel'
    GAUSSIAN = 'gaussian'


class Sampler:

    def __init__(self, sampler_t, num_samples):
        self.type = sampler_t
        self.num_samples = num_samples
        self.config = self.__create_config()

    def __create_config(self):
        result = {
            'type': self.type,
            'sampleCount': self.num_samples
        }
        return result