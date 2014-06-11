from __future__ import division
from __future__ import print_function
from __future__ import with_statement

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
import subprocess
import math
import time
import shutil
import multiprocessing
import math
import photos.utils
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

def gist_image_given_photo(photo):
    return photos.utils.open_image(photo.image_square_300).resize((256,256),PIL.Image.ANTIALIAS)

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
      image=gist_image_given_photo(x)
      image.save(posixpath.join(gistdir,'{}{:07}.jpg'.format(prefix,i)),'JPEG')
  #print('.')

def gist_measure_photo(measure,query_metric,query_photo):
  metric=gist_descriptor(gist_image_given_photo(query_photo))
  return measure(metric-query_metric)

def gist_query_all(gist_query_pk):
  return Photo.objects.exclude(pk=gist_query_pk).order_by('pk')

def gist_query_whitebalanced(gist_query_pk):
  return Photo.objects.exclude(pk=gist_query_pk).filter(whitebalanced=True).order_by('pk')

def gist_query_substance_and_scene_category(gist_query_pk,s,s2):
  # returns list of unique Photo objects
  photos=[]
  unique_photo_pks=set((gist_query_pk,))
  mats=MaterialShape.objects.filter(photo__scene_category_correct=True,photo__inappropriate=False,photo__license__publishable=True,substance__name=s,photo__scene_category__name=s2).order_by('pk')
  for x in mats:
    pk=x.photo.pk
    if pk not in unique_photo_pks:
      photos.append(x.photo)
    unique_photo_pks.add(pk)
  return photos

def gist_query_substance_and_object_type(gist_query_pk,s,s2):
  # returns list of unique Photo objects
  photos=[]
  unique_photo_pks=set((gist_query_pk,))
  mats=MaterialShape.objects.filter(
      photo__scene_category_correct=True,
      photo__inappropriate=False,
      photo__license__publishable=True,
      substance__name=s,name__name=s2).order_by('pk')
  for x in mats:
    pk=x.photo.pk
    if pk not in unique_photo_pks:
      photos.append(x.photo)
    unique_photo_pks.add(pk)
  return photos

def gist_query_substance(gist_query_pk,s):
  # returns list of unique Photo objects
  photos=[]
  unique_photo_pks=set((gist_query_pk,))
  mats=MaterialShape.objects.filter(photo__scene_category_correct=True,photo__inappropriate=False,photo__license__publishable=True,substance__name=s).order_by('pk')
  for x in mats:
    pk=x.photo.pk
    if pk not in unique_photo_pks:
      photos.append(x.photo)
    unique_photo_pks.add(pk)
  return photos

def gist_query_category(gist_query_pk,s):
  photos=[]
  unique_photo_pks=set((gist_query_pk,))
  mats=MaterialShape.objects.filter(photo__scene_category_correct=True,photo__inappropriate=False,photo__license__publishable=True,photo__scene_category__name=s).order_by('pk')
  for x in mats:
    pk=x.photo.pk
    if pk not in unique_photo_pks:
      photos.append(x.photo)
    unique_photo_pks.add(pk)
  return photos

def gist_search_photo(prefix,photos,gistdir,ngist,query_metric,measure,gist_query_pk,query_gist_image,nworker=4):
  rlprint=ratelimit(interval=15)(print)
  rlwrite=ratelimit(interval=15)(gist_write_results)

  query_gist_image.save(posixpath.join(gistdir,'query.jpg'),'JPEG')

  pool=multiprocessing.Pool(nworker)
  results=[]
  for x in photos:
    results.append(pool.apply_async(gist_measure_photo,(measure,query_metric,x)))

  best=[(float('inf'),None)]*ngist
  gist_clear_results(gistdir,prefix)
  work_units,work_done,work_t0=len(photos),0,time.time()
  for (i,x) in enumerate(photos):
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
      print('match dist={} pk={}'.format(x[0],x[1].pk),file=f)

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
  c=wd.c()
  d=wd.d()
  return lab,(c,d)

def write_latex(outdir,images,prefix,query_image):
    for i in images[:10]:
        print (i)
  #otex=posixpath.join(outdir,'{}.tex'.format(prefix))
  #with open(otex,'w') as f:
    #print(r'''\documentclass{article}
#\usepackage{graphicx}
#\usepackage{fullpage}
#\usepackage{paralist}
#\usepackage{multirow}
#\usepackage{caption}
#\usepackage{subcaption}
#\usepackage{amssymb,amsmath}
#\usepackage{tikz}
#\usetikzlibrary{arrows}
#\begin{document}''',file=f)
    #x=query_image
    #pname=posixpath.join(outdir,'{}query{}'.format(prefix,posixpath.splitext(x)[1]))
    #shutil.copyfile(x,pname)
    #print(r'''\begin{figure}[h]
#\centering
#\includegraphics[width=2.0in]{%s}
#\caption{query} \label{fig:%s}
#\end{figure}''' % (posixpath.split(pname)[1],prefix+'query'),file=f)
    #print(r'\begin{figure}',file=f)
    #for i,x in enumerate(images):
      #pname=posixpath.join(outdir,'{}{:03}{}'.format(prefix,i,posixpath.splitext(x)[1]))
      #shutil.copyfile(x,pname)
      #print(r'''\begin{minipage}[b]{.5\linewidth}
#\centering \includegraphics[width=1.0in]{%s}
#\subcaption{A subfigure}\label{fig:%s}
#\end{minipage}''' % (posixpath.split(pname)[1],prefix+str(i)),file=f)
    #print(r'\end{figure}',file=f)
    #print(r'''\end{document}''',file=f)

def do_color(query_pk,kind,kind2):
  outdir='/srv/labelmaterial/server/gist/{}/{}'.format(kind2,query_pk)
  try:
    os.makedirs(outdir)
  except:
    pass
  #subprocess.check_call(r'''mkdir -p {}'''.format(outdir),shell=True)
  nmatch=8
  measure=numpy.linalg.norm

  # find the query shape

  #query_photo=Photo.objects.filter(pk=query_pk)[0]
  #print(query_photo)
  #rgb=(query_photo.dominant_r,query_photo.dominant_g,query_photo.dominant_b)
  #print(rgb)
  query_bsdf=ShapeBsdfLabel_wd.objects.get(pk=query_pk)
  lab,wardcd=extract_bsdf(query_bsdf)
  print(query_bsdf.color,query_bsdf.contrast,query_bsdf.d())
  print(lab,wardcd)

  # get all shapes

  #allbsdf=ShapeBsdfLabel_wd.objects.filter(shape__photo__scene_category_correct=True,shape__photo__inappropriate=False,shape__photo__license__publishable=True,shape__photo__scene_category__name='living room',shape__name__name='Sofa/couch').exclude(pk=query_pk).exclude(shape__photo__pk=query_bsdf.shape.photo.pk)
  #allbsdf=ShapeBsdfLabel_wd.objects.filter(shape__photo__scene_category_correct=True,shape__photo__inappropriate=False,shape__photo__license__publishable=True,shape__name__name='Sofa/couch').exclude(pk=query_pk).exclude(shape__photo__pk=query_bsdf.shape.photo.pk)
  allbsdf=ShapeBsdfLabel_wd.objects.filter(shape__photo__scene_category_correct=True,shape__photo__inappropriate=False,shape__photo__license__publishable=True).exclude(pk=query_pk).exclude(shape__photo__pk=query_bsdf.shape.photo.pk)
  print(len(allbsdf))
  def E(x):
    if x.shape.substance==None: return float('inf')
    if x.shape.substance.name!=kind: return float('inf')
    if x.shape.substance_entropy>0.5: return float('inf')
    if x.shape.area<0.05: return float('inf')
    lab2,wardcd2=extract_bsdf(x)
    return lab.delta_e(lab2) # cie2000 delta e
  def D(x):
    if x.shape.substance==None: return float('inf')
    if x.shape.substance.name!=kind: return float('inf')
    if x.shape.substance_entropy>0.5: return float('inf')
    if x.shape.area<0.05: return float('inf')
    lab2,wardcd2=extract_bsdf(x)
    return gloss_distance(wardcd,wardcd2)
  def F(x):
    return x.shape.photo
    #return x.shape.image_crop.path # shape only
    #return x.shape.image_bbox.path # original photo crop
    #return x.shape.photo.image_span12.path # photo 1200x120
    #return x.shape.photo.image_orig.path # original photo

  ordering=list(enumerate(allbsdf))

  # sort by gloss
  photo_D=[(D(x),F(x),x) for x in allbsdf]
  photo_D.sort(key=lambda x: x[0])
  photo_D=photo_D[:nmatch]
  #ordering.sort(key=lambda x: D(x[1]))
  #photo_D=[F(allbsdf[x[0]]) for x in ordering[:nmatch]]
  prefix='gloss'
  for i,x in enumerate(photo_D):
    image=gist_image_given_photo(x[1])
    image.save(posixpath.join(outdir,'{}{:07}.jpg'.format(prefix,i)),'JPEG')
  print(list(x[0] for x in photo_D))

  # sort by color
  photo_E=[(E(x),F(x),x) for x in allbsdf]
  photo_E.sort(key=lambda x: x[0])
  photo_E=photo_E[:nmatch]
  #ordering.sort(key=lambda x: E(x[1]))
  #photo_E=[F(allbsdf[x[0]]) for x in ordering[:nmatch]]
  prefix='color'
  for i,x in enumerate(photo_E):
    image=gist_image_given_photo(x[1])
    image.save(posixpath.join(outdir,'{}{:07}.jpg'.format(prefix,i)),'JPEG')
  print(list(x[0] for x in photo_E))

  # sort by gloss, color matched
  photo_DE=[(D(x),F(x),x) for x in allbsdf if E(x)<2.7*2]
  photo_DE.sort(key=lambda x: x[0])
  photo_DE=photo_DE[:nmatch]
  #ordering=[x for x in ordering if E(x[1])<2.7*10] # select near color matches
  #assert len(ordering)>nmatch
  #ordering.sort(key=lambda x: D(x[1]))
  #photo_DE=[F(allbsdf[x[0]]) for x in ordering[:nmatch]]
  prefix='matchgloss'
  for i,x in enumerate(photo_DE):
    image=gist_image_given_photo(x[1])
    image.save(posixpath.join(outdir,'{}{:07}.jpg'.format(prefix,i)),'JPEG')
  print(list(x[0] for x in photo_DE))

  with open(posixpath.join(outdir,'do_color.txt'),'w') as f:
    f.write('photo_D:\n{}\n'.format('\n'.join('{} bsdf={} pk={}'.format(x[0],x[2].pk,x[1].pk) for x in photo_D)))
    f.write('photo_E:\n{}\n'.format('\n'.join('{} bsdf={} pk={}'.format(x[0],x[2].pk,x[1].pk) for x in photo_E)))
    f.write('photo_DE:\n{}\n'.format('\n'.join('{} bsdf={} pk={}'.format(x[0],x[2].pk,x[1].pk) for x in photo_DE)))

def do_gist(gist_query_pk,kind,kind2):
  ngist=8 # the top ngist images are kept
  gistdir='/srv/labelmaterial/server/gist/{}/{}'.format(kind2,gist_query_pk)
  #subprocess.check_call(r'''mkdir -p {}'''.format(gistdir),shell=True)
  try:
    os.makedirs(gistdir)
  except Exception as e:
    print (e)
  #subprocess.check_call(r'''rm {}/*'''.format(gistdir),shell=True)
  measure=numpy.linalg.norm

  #result_pk={} # photo pk
  #result_image={} # 256x256 PIL image

  query_photo=Photo.objects.get(pk=gist_query_pk)
  query_gist_image=gist_image_given_photo(query_photo)
  query_metric=gist_descriptor(query_gist_image)

  #photos=gist_query_substance(gist_query_pk,kind)
  #photos=gist_query_category(gist_query_pk,kind)
  #photos=gist_query_substance_and_scene_category(gist_query_pk,kind,'kitchen')
  photos=gist_query_substance_and_object_type(gist_query_pk,kind,'Sofa/couch')
  photos=photos[:500]
  print('Starting search of {} in {} photos'.format(gist_query_pk,len(photos)))
  gist_search_photo('gist',photos,gistdir,ngist,query_metric,measure,gist_query_pk,query_gist_image)

# to return all photos that don't have issues:
#Photo.objects.filter(scene_category_correct=True,
                     #inappropriate=False,
                     #license__publishable=True)

  #gist_category='kitchen' # only select images from this category
  #photos = Photo.objects \
  #  .filter(scene_category__name=gist_category, whitebalanced=True) \
  #  .order_by('pk')

class Command(BaseCommand):
  args=''
  help='gist test'
  def handle(self,*args,**options):
    # query_pk=4692 # granite island (the one without shape)
    # query_pk=5007 # granite island (the one with shape 38101 ward 12685)
    # old query pk above this mark (may not have a good license)
    #query_pk=11080,None # nice living room with 80s lamp
    #query_pk=102319,[30537] # nice bedroom with vanity
    #query_pk=125873 # nasty hotel room
    #query_pk=72931,None # wood loft
    #query_pk=60271,None # ugly living room
    #query_pk=76005,None # modern office lounge
    #query_pk=597,None # busy living room
    #query_pk=34538,None # brick wall living room
    #query_pk=63254,None # bright sofa area
    query_pk=58420,[35508,35465] # art room, white sofa, red chair
    #query_pk=65852,None # not bad living room
    #query_pk=105618 # room with big red couch
    #for query_pk in [(58420,[35508,35465])]:
    #  #do_gist(query_pk[0],'Fabric/cloth','fabric')
    #  #do_gist(query_pk[0],'living room','living')
    #  for x in query_pk[1]:
    #    do_color(x,'Fabric/cloth','living')
    #    print('photo={} bsdf={}'.format(query_pk[0],x))
    #for query_pk in [(5007,[12668,12678,13005])]:
    #  do_gist(query_pk[0],'Granite','kitchen')
    #  for x in query_pk[1]:
    #    do_color(x,'Granite','kitchen')
    #    print('photo={} bsdf={}'.format(query_pk[0],x))
    from photos.tasks import do_gist_tmp
    for photo in gist_query_substance_and_object_type(105618, 'Fabric/cloth', 'Sofa/couch'):
        do_gist_tmp.delay(photo.pk, 'Fabric/cloth', 'photo-%s' % photo.pk)

    #for query_pk in [(105618,None)]:
      #do_gist(query_pk[0],'Fabric/cloth','bigred')
      #do_gist(query_pk[0],'living room','living')
      #for x in query_pk[1]:
      #  do_color(x,'Fabric/cloth','living')
      #  print('photo={} bsdf={}'.format(query_pk[0],x))


