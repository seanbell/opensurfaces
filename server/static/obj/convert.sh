#!/bin/bash
# converts OBJ to THREE.JS format

for f; do python ~/opt/three.js/utils/exporters/obj/convert_obj_three.py -i $f -o $(basename $f .obj).js -t binary -s smooth; done
