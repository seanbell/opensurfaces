from __future__ import division
from __future__ import print_function

#from decimal import Decimal
#from clint.textui import progress

#from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
#from django.core.exceptions import ObjectDoesNotExist
#from django.contrib.contenttypes.models import ContentType
#from django.db import transaction

#from mturk.utils import get_mturk_connection, extract_mturk_attr
#from mturk.models import Experiment, MtHitType, MtHit

import os
import posixpath
import PIL
import leargist
import numpy.linalg
import math
import time
import shutil
import multiprocessing
import math
from colormath.color_objects import RGBColor

from django.db.models import Count
from photos.models import Photo
from shapes.models import MaterialShape
from bsdfs.models import ShapeBsdfLabel_wd

def ratelimit(n=0,interval=0.0,timefn=time.time):
  def d(f):
    count=[n,interval,timefn]
    if interval>0.0: count[1]=count[2]()-interval
    def c(*args,**kwds):
      if n>0: count[0]=count[0]+1
      t=count[1]
      if interval>0.0: t=count[2]()
      if count[0]>=n and t-count[1]>=interval:
        count[0]=0
        count[1]=t
        f(*args,**kwds)
    return c
  return d

def gist_image(a):
  image=PIL.Image.open(a)
  #print(a,image.size)
  w,h=image.size
  if w>h:
    c=(w-h)//2
    image=image.crop((c,0,c+h,h))
  else:
    c=(h-w)//2
    image=image.crop((0,c,w,c+w))
  return image.resize((256,256),PIL.Image.ANTIALIAS)

def gist_descriptor(image):
  return leargist.color_gist(image)

def gist_clear_results(gistdir,prefix):
  for x in os.listdir(gistdir):
    if x.startswith(prefix):
      try:
        os.remove(posixpath.join(gistdir,x))
      except:
        pass

def gist_write_results(gistdir,best,prefix):
  for i in range(len(best)):
    m,x=best[i]
    if x!=None:
      image=gist_image(x)
      image.save(posixpath.join(gistdir,'{}{:07}.jpg'.format(prefix,i)),'JPEG')
  #print('.')

def gist_measure(measure,query_metric,x):
  metric=gist_descriptor(gist_image(x))
  return measure(metric-query_metric)

def gist_query_all(gist_query_pk):
  return Photo.objects.exclude(pk=gist_query_pk).order_by('pk')

def gist_query_whitebalanced(gist_query_pk):
  return Photo.objects.exclude(pk=gist_query_pk).filter(whitebalanced=True).order_by('pk')

def gist_query_substance(gist_query_pk,s):
  photos=[]
  unique_photo_pks=set((gist_query_pk,))
  mats=MaterialShape.objects.filter(substance__name=s).order_by('pk')
  for x in mats:
    pk=x.photo.pk
    if pk not in unique_photo_pks:
      photos.append(x.photo)
    unique_photo_pks.add(pk)
  return photos

def gist_search(prefix,photos,gistdir,ngist,query_metric,measure,gist_query_pk,nworker=4):
  rlprint=ratelimit(interval=15)(print)
  rlwrite=ratelimit(interval=15)(gist_write_results)

  pklookup={}
  for x in photos:
    pklookup[x.image_orig.path]=x.pk
  files=[x.image_orig.path for x in photos]

  pool=multiprocessing.Pool(nworker)
  results=[]
  for (i,x) in enumerate(files):
    results.append(pool.apply_async(gist_measure,(measure,query_metric,x)))

  best=[(float('inf'),None)]*ngist
  gist_clear_results(gistdir,prefix)
  work_units,work_done,work_t0=len(files),0,time.time()
  for (i,x) in enumerate(files):
    m=results[i].get()
    if m<best[-1][0]:
      best.pop()
      best.append((m,x))
      best.sort(key=lambda x: x[0])
    rlwrite(gistdir,best,prefix)
    work_done=work_done+1
    rlprint('{}/{}, {} min remaining'.format(work_done,work_units,(work_units/work_done-1)*(time.time()-work_t0)/60))
  gist_write_results(gistdir,best,prefix)
  with open(posixpath.join(gistdir,'{}.txt'.format(prefix)),'w') as f:
    print('query pk={}'.format(gist_query_pk),file=f)
    for x in best:
      print('match dist={} pk={} path={}'.format(x[0],pklookup[x[1]],x[1]),file=f)

def gloss_distance(cdi,cdj):
  ci,di=cdi
  cj,dj=cdj
  return math.sqrt((ci-cj)**2+(1.78*(di-dj))**2)

def lab_distance(labi,labj):
  return math.sqrt((labi[0]*labj[0])**2+(labi[1]*labj[1])**2+(labi[2]*labj[2])**2)

def extract_bsdf(wd):
  color=RGBColor()
  color.set_from_rgb_hex(wd.color)
  lab=color.convert_to('lab')
  c=wd.contrast
  d=wd.d()
  return lab,(c,d)

def write_latex(outdir,images,prefix,query_image):
  otex=posixpath.join(outdir,'{}.tex'.format(prefix))
  with open(otex,'w') as f:
    print(r'''\documentclass{article}
\usepackage{graphicx}
\usepackage{fullpage}
\usepackage{paralist}
\usepackage{multirow}
\usepackage{caption}
\usepackage{subcaption}
\usepackage{amssymb,amsmath}
\usepackage{tikz}
\usetikzlibrary{arrows}
\begin{document}''',file=f)
    x=query_image
    pname=posixpath.join(outdir,'{}query{}'.format(prefix,posixpath.splitext(x)[1]))
    shutil.copyfile(x,pname)
    print(r'''\begin{figure}[h]
\centering
\includegraphics[width=2.0in]{%s}
\caption{query} \label{fig:%s}
\end{figure}''' % (posixpath.split(pname)[1],prefix+'query'),file=f)
    print(r'\begin{figure}',file=f)
    for i,x in enumerate(images):
      pname=posixpath.join(outdir,'{}{:03}{}'.format(prefix,i,posixpath.splitext(x)[1]))
      shutil.copyfile(x,pname)
      print(r'''\begin{minipage}[b]{.5\linewidth}
\centering \includegraphics[width=1.0in]{%s}
\subcaption{A subfigure}\label{fig:%s}
\end{minipage}''' % (posixpath.split(pname)[1],prefix+str(i)),file=f)
    print(r'\end{figure}',file=f)
    print(r'''\end{document}''',file=f)

def do_color():
  outdir='/vol/labelmaterial/data/media/gist'
  gist_query_pk=3625 # photo pk
  query_ward_pk=10374 # ward pk
  query_substance='Granite'
  gist_prefix='granite'
  nmatch=10
  measure=numpy.linalg.norm

  query_photo=Photo.objects.filter(pk=gist_query_pk)[0]
  query_gist_image=gist_image(query_photo.image_orig.path)
  query_gist_image.save(posixpath.join(outdir,'query.jpg'),'JPEG')
  query_metric=gist_descriptor(query_gist_image)

  photos=gist_query_substance(gist_query_pk,query_substance)
  gist_search(gist_prefix,photos,outdir,nmatch,query_metric,measure,gist_query_pk)

  #query_photo=Photo.objects.filter(pk=query_pk)[0]
  #print(query_photo)
  #rgb=(query_photo.dominant_r,query_photo.dominant_g,query_photo.dominant_b)
  #print(rgb)
  query_bsdf=ShapeBsdfLabel_wd.objects.filter(pk=query_ward_pk)[0]
  lab,wardcd=extract_bsdf(query_bsdf)
  print(query_bsdf.color,query_bsdf.contrast,query_bsdf.d())
  print(lab,wardcd)

  search_space=set()
  pklookup={}
  shapes=MaterialShape.objects.filter(substance__name=query_substance).exclude(photo__pk=gist_query_pk)
  for x in shapes:
    search_space.add(x.pk)
    pklookup[x.pk]=x
  print(len(search_space))
  def E2(shape):
    if shape.substance_entropy>2.0:
      yield 10000.0
      yield 10000.0
      yield 10000.0
      yield 10000.0
      return
    color=RGBColor()
    color.set_from_rgb_hex(shape.dominant_rgb0)
    lab2=color.convert_to('lab')
    yield lab.delta_e(lab2) # cie2000 delta e
    color.set_from_rgb_hex(shape.dominant_rgb1)
    lab2=color.convert_to('lab')
    yield lab.delta_e(lab2) # cie2000 delta e
    color.set_from_rgb_hex(shape.dominant_rgb2)
    lab2=color.convert_to('lab')
    yield lab.delta_e(lab2) # cie2000 delta e
    color.set_from_rgb_hex(shape.dominant_rgb3)
    lab2=color.convert_to('lab')
    yield lab.delta_e(lab2) # cie2000 delta e
  ordering=list(enumerate(search_space))
  ordering.sort(key=lambda x: min(tuple(E2(pklookup[x[1]]))))
  print('best:')
  for i,pk in ordering[:nmatch]:
    print(pk,pklookup[pk].photo.pk)
  print('worst:')
  for i,pk in ordering[-nmatch:]:
    print(pk,pklookup[pk].photo.pk)

  best=[]
  unique_best=set()
  for i,pk in ordering:
    photopk=pklookup[pk].photo.pk
    if photopk not in unique_best:
      unique_best.add(photopk)
      best.append((0,pklookup[pk].photo.image_orig.path))
  print(best[:nmatch])
  gist_write_results(outdir,best[:nmatch],'color')

  return

  allbsdf=ShapeBsdfLabel_wd.objects.exclude(pk=query_ward_pk)
  print(len(allbsdf))
  def E(x):
    lab2,wardcd2=extract_bsdf(x)
    return lab.delta_e(lab2) # cie2000 delta e
  def D(x):
    lab2,wardcd2=extract_bsdf(x)
    return gloss_distance(wardcd,wardcd2)
  def F(x):
    #return x.shape.image_crop.path # shape only
    return x.shape.image_bbox.path # original photo crop
    #return x.shape.photo.image_span12.path # photo 1200x120
    #return x.shape.photo.image_orig.path # original photo

  ordering=list(enumerate(allbsdf))

  # sort by gloss
  ordering.sort(key=lambda x: D(x[1]))
  original_D=[F(allbsdf[x[0]]) for x in ordering[:nmatch]]
  write_latex(outdir,original_D,'deltaD',F(query_bsdf))

  # sort by color
  ordering.sort(key=lambda x: E(x[1]))
  original_E=[F(allbsdf[x[0]]) for x in ordering[:nmatch]]
  write_latex(outdir,original_E,'deltaE',F(query_bsdf))

  # sort by gloss, color matched
  ordering=[x for x in ordering if E(x[1])<2.3] # select near color matches
  assert len(ordering)>nmatch
  ordering.sort(key=lambda x: D(x[1]))
  original_DE=[F(allbsdf[x[0]]) for x in ordering[:nmatch]]
  write_latex(outdir,original_DE,'deltaDE',F(query_bsdf))

def do_gist():
  gistdir='/vol/labelmaterial/data/media/gist'
  ngist=10 # the top ngist images are kept
  gist_query_pk=3305 # pk of the query image
  measure=numpy.linalg.norm

  query_photo=Photo.objects.filter(pk=gist_query_pk)[0]
  query_gist_image=gist_image(query_photo.image_orig.path)
  query_gist_image.save(posixpath.join(gistdir,'query.jpg'),'JPEG')
  query_metric=gist_descriptor(query_gist_image)

  photos=gist_query_substance(gist_query_pk,'Wood - natural color')
  gist_search('wood',photos,gistdir,ngist,query_metric,measure,gist_query_pk)

  photos=gist_query_whitebalanced(gist_query_pk)
  gist_search('wb',photos,gistdir,ngist,query_metric,measure,gist_query_pk)

  #gist_category='kitchen' # only select images from this category
  #photos = Photo.objects \
  #  .filter(scene_category__name=gist_category, whitebalanced=True) \
  #  .order_by('pk')

class Command(BaseCommand):
  args=''
  help='gist test'
  def handle(self,*args,**options):
    #do_gist()
    do_color()


