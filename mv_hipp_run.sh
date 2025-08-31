#!/bin/bash

SRC_DIR=$1        # source directory with .obj files
DEST_DIR=$2  # output directory

mkdir -p "$DEST_DIR"  # create destination if not exists

for file in "$SRC_DIR"*.obj; do
    echo "Processing $file ..."
    blender phong.blend --background --python phong.py -- "$file" "$DEST_DIR"
done
