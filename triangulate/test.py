#!/usr/bin/env python
import subprocess
from Tkinter import *

raise NotImplementedError("TODO: update parsing to the new data format")

master = Tk()
w = Canvas(master, width=1024, height=768)

with open('tests/test4.txt') as f:
    polygons = str(subprocess.check_output(
        ["build/release/triangulate"],
        stdin=f
    )).split('\n')

colors = ["red", "blue", "green"]
color_idx = 0

for polygon in polygons:
    if len(polygon) < 3: continue
    verts, tris, lines = polygon.split('|')

    verts = [(100 + 400 * float(t[0]), 100 + 400 * float(t[1])) for t in [p.split() for p in verts.split(';')] if len(t) == 2]
    tris  = [(int(t[0]), int(t[1]), int(t[2])) for t in [p.split() for p in tris.split(';')] if len(t) == 3]
    lines = [(int(t[0]), int(t[1])) for t in [p.split() for p in lines.split(';')] if len(t) == 2]

    print 'verts:', verts
    print 'tris:', tris
    print 'lines:', lines

    if color_idx == 0:
        for t in tris:
            w.create_polygon([verts[v] for v in t], fill=colors[color_idx])

        for l in lines:
            x0,y0 = verts[l[0]]
            x1,y1 = verts[l[1]]
            w.create_line(x0, y0, x1, y1, width=4)
            #w.create_line(0, 100, 200, 0, fill="red", dash=(4, 4))

    color_idx += 1

w.pack()
mainloop()
