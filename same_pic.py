# -*- coding:utf-8 -*-
#==========================================
#从dist 中选择和src相同的图片
#xufeng02.zhou
#2018-05-28
#===========================================

from numpy  import *
import os
import sys
import shutil
import argparse

if __name__ == '__main__':
    src = "./"
    dist = "copy"
    result = "result"
    parser = argparse.ArgumentParser()
    parser.add_argument("--src", help="src dir to copy")
    parser.add_argument("--dist", help="dist dir to copy")
    parser.add_argument("--result", help="number to copy")
    args = parser.parse_args()

    src = args.src
    dist = args.dist
    result = args.result

    file_list1 = os.listdir(src)
    file_list2 = os.listdir(dist)

    if not os.path.exists(result):
        os.mkdir(result)

    for file in file_list1:
        if file in file_list2:
            path = os.path.join(dist, file)
            cp_path = os.path.join(result, file)
            shutil.copyfile(path, cp_path)