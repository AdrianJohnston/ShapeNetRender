from __future__ import print_function
import sys, os
from MitsubaConfig import *
from multiprocessing import Pool, Process


def main():

    # args = [ (x, y) for x,y in zip(range(0,4), range(1,5))]
    cmd = "python MitsubaRender.py "
    cmds = [ cmd + str(x) + " " + str(y) for x,y in zip(range(0,num_images), range(1,num_images+1))]

    print("Total #images:", num_images)
    for cmd in cmds:
        print(cmd)
        os.system(cmd)



if __name__ == "__main__":
    main()

