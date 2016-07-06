# ShapeNetRender

Pacakge for rendering out images of the ShapeNet dataset

This library uses blender to perform pre-processing. 
It expects the $BLENDER env variable to point at the blender executable


This code is still a work in progress.

It uses the Mitsuba Physically Based Renderer to render the images:

Possible output targets include:
    - RGB
    - Depth
    - Vertex Position
    - Normals
    - Texture Coordinates 