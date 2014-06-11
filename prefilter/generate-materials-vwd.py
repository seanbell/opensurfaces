#!/usr/bin/env python

import os
import sys


def cmd(command):
    """ Run system command and exit on failure """
    print command
    if os.system(command) != 0:
        print 'Error running "%s"' % command
        print 'Exiting'
        sys.exit(1)



if __name__ == '__main__':

    # global params:
    scene = 'scenes/scene.xml'
    envname = 'ennis'
    outdir = 'tex-vwd'
    alpha_max = 0.2
    alpha_count = 16
    rows, cols = 4, 4
    scale = 1.0

    if not os.path.isdir(outdir):
        os.makedirs(outdir)

    bsdf_type = 'ward'


    # DIFFUSE
    c = 0
    alpha = 0.2
    name = '%s/%s-c%d.exr' % (outdir, bsdf_type, c)
    cmd('mitsuba %s -D envname=%s -D bsdf=%s -D component=%d -D alpha=%f -o %s' % (
        scene, envname, bsdf_type, c, alpha, name))
    png_name = '%s/%s-%d-%s.png' % (outdir, bsdf_type, c, envname)
    cmd('mtsutil encodehdr rgbe %d %d %f %s %s' % (
        1, 1, scale, name, png_name))

    # SPECULAR
    c = 1

    alpha_values = [1e-3 + f * alpha_max / (alpha_count - 1) for f in xrange(
        alpha_count)]

    names = [('%s/%s-c%d-a%d.exr' % (
        outdir, bsdf_type, c, i)) for i in xrange(alpha_count)]

    # render images
    for (i, alpha) in enumerate(alpha_values):
        cmd('mitsuba %s -D envname=%s -D bsdf=%s -D component=%d -D alpha=%f -o %s' % (
            scene, envname, bsdf_type, c, alpha, names[i]))

    # package into png grid
    png_name = '%s/%s-%d-%s.png' % (outdir, bsdf_type, c, envname)
    cmd('mtsutil encodehdr rgbe %d %d %f %s %s' % (
        rows, cols, scale, ' '.join(names), png_name))
    #cmd('scp %s scb:~/www/demo/%s/' % (png_name, outdir))

    # build thumbnails
    thumb_names = ['%s/%s-thumb-%s-%d.png' % (outdir, bsdf_type, n, c) for n in ('min', 'max')]
    cmd('mtsutil tonemap -f png -s 32,32 -o %s %s' % (thumb_names[0], names[0]))
    cmd('mtsutil tonemap -f png -s 32,32 -o %s %s' % (thumb_names[1], names[-1]))
    #cmd('scp %s scb:~/www/demo/%s/' % (' '.join(thumb_names), outdir))
