import os, sys
from subprocess import Popen
import argparse
import multiprocessing as mp
from StandaloneMitsubaRender import *



if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Process some integers.')

    parser.add_argument('-f', '--file', nargs=1, type=str, help='Mesh file to render')
    parser.add_argument('-t', '--filetype', nargs=1, type=str, default='PLY', help='Mesh file type [PLY, OBJ]')
    parser.add_argument('-xr','--xrot', nargs=2, default=[0,0], type=int, help='X Rotation Range')
    parser.add_argument('-yr','--yrot', nargs=2, default=[0,0], type=int, help='Y Rotation Range')
    parser.add_argument('-zr','--zrot', nargs=2, default=[0,0], type=int, help='Z Rotation Range')

    parser.add_argument('-xrs','--x_rot_step', nargs=1, default=[1.0], type=float, help='X Rotation Step Size')
    parser.add_argument('-yrs','--y_rot_step', nargs=1, default=[1.0], type=float, help='Y Rotation Step Size')
    parser.add_argument('-zrs','--z_rot_step', nargs=1, default=[1.0], type=float, help='Z Rotation Step Size')

    parser.add_argument('-xt','--xtrans', nargs=2, default=[0,0], type=int, help='X Translation Range')
    parser.add_argument('-yt','--ytrans', nargs=2, default=[0,0], type=int, help='Y Translation Range')
    parser.add_argument('-zt','--ztrans', nargs=2, default=[0,0], type=int, help='Z Translation Range')

    parser.add_argument('-d','--depth', default=False, type=bool, help='Add a depth pass')
    parser.add_argument('-n', '--normal', default=False, type=bool, help='Add a normal pass')
    parser.add_argument('')
    args = parser.parse_args()
    render_args = []
    # print vars(args)



    pool = mp.Pool()
    result = pool.apply(render, [vars(args)])

    print("result", result)
    # Popen([render_script, args])