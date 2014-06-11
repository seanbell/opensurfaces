"""
Common utilities.

.. note::
    Many of these functions are *ad hoc* and may change between versions.

"""

import os
import re
import csv
import math
import json
import uuid
import gzip
import pickle
import cPickle
import string
import random
import hashlib
import logging
import datetime
import base64
import numconv
from tempfile import NamedTemporaryFile
from cStringIO import StringIO
from numbers import Number
from PIL import Image
from collections import Counter
from clint.textui import progress
from pilkit.utils import open_image

from django.conf import settings
from django.core.cache import cache
from django.utils.encoding import smart_str, force_unicode
from django.core.files import File
from django.db import models, connection
from django.db.models.loading import get_model
from django.db.models.query import QuerySet
from django.db.models import Avg, Sum, Count, Max, Min, StdDev
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import render
from django.http import HttpResponse

from imagekit.utils import img_to_fobj
from queued_storage.utils import import_attribute

EXT_TO_FORMAT = {
    'png': 'PNG',
    'jpg': 'JPEG'
}

_first_cap_re = re.compile('(.)([A-Z][a-z]+)')
_all_cap_re = re.compile('([a-z0-9])([A-Z])')

logger = logging.getLogger(__name__)


def import_module(name):
    """ Import a module by name and return it """
    module = __import__(name)
    for n in name.split('.')[1:]:
        module = getattr(module, n)
    return module


def import_modules(module_names):
    """ Import a list of modules by name and return them """
    modules = []
    for name in module_names:
        modules.append(import_module(name))
    return modules


def get_opensurfaces_storage():
    return import_attribute(settings.OPENSURFACES_FILE_STORAGE)()


def pickle_zip(fname, obj):
    """ Pickle and gzip ``obj`` to disk with filename ``fname`` """
    cPickle.dump(obj=obj, file=gzip.open(fname, "wb"), protocol=cPickle.HIGHEST_PROTOCOL)


def unpickle_zip(fname):
    """ Unpickle a gzipped file from disk with filename ``fname`` """
    try:
        return cPickle.load(gzip.open(fname, "rb"))
    except:
        # try non-zippped
        with open(fname, 'rb') as f:
            return pickle.load(f)


def captcha_random_chars():
    """ Return a string to use for a CAPTCHA """
    chars, ret = u'abcdefghjkmnprtuvwxyz', u''
    for _ in range(4):
        ret += random.choice(chars)
    return ret.upper(), ret


def get_content_type_id(instance):
    """ Return the ``ContentType`` id associated with ``instance`` """
    return ContentType.objects.get_for_model(instance).id


def get_content_tuple(instance):
    """ Return (content type id, object id) """
    return (ContentType.objects.get_for_model(instance).id, instance.id)


def unique_instance_name(obj):
    """
    Return a unique alpha-numeric string for a model instance (base 62).  The
    name is generated from the current time, the object id (or count if not
    created), its content type id, and the server MAC address.
    """
    ct_id = get_content_type_id(obj)
    clock_seq = obj.pk if obj.pk else obj.__class__.objects.count()
    uuid_int128 = uuid.uuid1(clock_seq=clock_seq).int
    return numconv.NumConv(radix=62).int2str((ct_id << 128) + uuid_int128)


def queryset_progress_bar(queryset):
    """ Returns an iterator for a queryset that renders a progress bar with a
    countdown timer """
    count = queryset.count()
    if count:
        return progress.bar(queryset.iterator(), expected_size=count)
    else:
        return []


def progress_bar(l, show_progress=True):
    """ Returns an iterator for a list or queryset that renders a progress bar
    with a countdown timer """
    if show_progress:
        if isinstance(l, QuerySet):
            return queryset_progress_bar(l)
        else:
            return progress.bar(l)
    else:
        return l


def unit_interval_infinite_generator():
    """
    Never-ending generator that yields all floats in the range [0, 1], in the
    order:

        0, 1, 1/2, 1/4, 3/4, 1/8, 3/8, 5/8, 7/8, 1/16, 3/16, 5/16, ...

    The same value is never returned twice, and eventually all floating point
    numbers in the range [0, 1] are returned.  The point of this generator is
    to sweep a range, iteratively increasing the density of the sweep, so
    that if you want to stop the sweep early, you have still swept the
    majority of the range.

    :return: floats in the range [0, 1].
    """

    yield 0.0
    yield 1.0
    den = 2

    while True:
        for x in xrange(1, den):
            if (x & 1) != 0:
                yield float(x) / den
        den *= 2


def chunk_list_generator(lst, chunksize):
    """ Generator that chunks a list ``lst`` into sublists of size ``chunksize`` """

    if lst:
        chunksize = max(chunksize, 1)
        for i in xrange(0, len(lst), chunksize):
            yield lst[i:i + chunksize]


#def queryset_batch_delete(queryset, batch_size=100000, show_progress=False):
    #""" Delete a large queryset, batching into smaller queries (sometimes huge
    #commands crash) """
    #if show_progress:
        #print 'queryset_batch_delete: fetching ids for %s' % queryset.model
    #ids = queryset.values_list('pk', flat=True)
    #if len(ids) <= batch_size:
        #queryset.delete()
    #else:
        #iterator = range(0, len(ids), batch_size)
        #if show_progress:
            #progress.bar(iterator)
        #for i in iterator:
            #queryset.filter(pk__in=ids[i:i+batch_size]).delete()
    #return len(ids)


def all_aggregations(queryset, key):
    """ Performs all available aggregations on a queryset """
    return queryset.filter(**{key + '__isnull': False}).aggregate(
        min=Min(key),
        avg=Avg(key),
        max=Max(key),
        std=StdDev(key),
        count=Count(key),
        sum=Sum(key),
    )


def todo_view(request):
    """ Renders a placeholder view """
    return render(request, 'todo.html', {})


def recursive_sum(x):
    """
    Recursively sums together numbers contained in x.
    Supports: int, float, dict, list, tuple, str, unicode, and json-encoded strings.
    """
    if isinstance(x, Number):
        return x
    elif isinstance(x, basestring):
        return recursive_sum(json.loads(x))
    elif isinstance(x, dict):
        return sum(recursive_sum(t) for t in x.values())
    elif isinstance(x, (list, tuple)):
        return sum(recursive_sum(t) for t in x)
    else:
        return None


def recursive_dict_exclude(d, excludes):
    """ Recursively exclude a key from a nested dictionary """
    if isinstance(d, dict):
        return {
            k: recursive_dict_exclude(v, excludes) for k, v in d.iteritems()
            if k not in excludes
        }
    else:
        return d


def scale_dict_values(d, scale, exclude=[]):
    """ Return a new dictionary with numeric values multiplied by ``scale``.

    :param exclude: collection of items to exclude.
    """

    ret = {}
    for k in d:
        val = d[k]
        if k not in exclude and isinstance(val, (int, long, float, complex)):
            ret[k] = val * scale
        else:
            ret[k] = val
    return ret


# from django.template.loader import get_template
# from cacheback.decorators import cacheback
#@cacheback(15*60)
# def cached_template_render(template_name, context):
    # return get_template(template_name).render(context)

def random_lowercase_str(N):
    """ Return a random lowercase string of length ``N`` """
    return ''.join(random.choice(string.ascii_lowercase) for x in range(N))


def dump_model_csv_view(app_name, model_name):

    response = HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] = (
        'attachment; filename="%s-%s.csv"' % (app_name, model_name))
    writer = csv.writer(response)

    model = get_model(app_name, model_name)
    fields = [f[0].attname for f in model._meta.get_fields_with_model()]

    writer.writerow(fields)
    for obj in model.objects.all().order_by('pk'):
        writer.writerow([getattr(obj, f) for f in fields])

    return response


def dump_queryset_to_static_csv(queryset, values, filename, dirname='generated'):
    """
    Create a CSV in the staticfiles of a queryset.  Values is a list of fields
    to grab.  Optionally, you may specify a rename a field by specifying a
    tuple instead of a string as (field_name, csv_name).  The path is relative
    to the staticfiles root.  The URL of the file is returned.
    """

    # save on disk in static files
    fullpath = os.path.join(settings.STATIC_ROOT, dirname, filename)

    logger.debug('Exporting CSV: %s' % fullpath)

    # make sure the dir exists
    fullpathdir = os.path.dirname(fullpath)
    if not os.path.exists(fullpathdir):
        os.makedirs(fullpathdir)

    # if the file already exists, write to a temporary file then move
    # when done
    temppath = fullpath
    while os.path.exists(temppath):
        temppath = '%s.%s.tmp' % (fullpath, random_lowercase_str(8))

    values_fields = [(v[0] if isinstance(v, (tuple, list)) else v)
                     for v in values]
    values_names = [(v[1] if isinstance(v, (tuple, list)) else v)
                    for v in values]

    with open(temppath, 'wb') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(values_names)
        for row in queryset.values_list(*values_fields):
            writer.writerow(row)

    if temppath != fullpath:
        os.rename(temppath, fullpath)

    return settings.STATIC_URL + dirname + '/' + filename


# def dump_to_static_file(s, filename, dirname='generated'):
    #"""
    # Create a file in the staticfiles.  The path is relative to the
    # staticfiles root.  The URL of the file is returned.
    #"""

    # save on disk in static files
    # fullpath = os.path.join(settings.STATIC_ROOT, dirname, filename)

    # make sure the dir exists
    # fullpathdir = os.path.dirname(fullpath)
    # if not os.path.exists(fullpathdir):
        # os.makedirs(fullpathdir)

    # if the file already exists, write to a temporary file then move
    # when done
    # temppath = fullpath
    # while os.path.exists(temppath):
        # temppath = '%s.%s.tmp' % (fullpath, random_lowercase_str(8))

    # with open(temppath, 'wb') as f:
        # f.write(s)

    # if temppath != fullpath:
        # os.rename(temppath, fullpath)

    # return settings.STATIC_URL + dirname + '/' + filename


def json_response(d):
    """ Return a ``HttpResponse`` containing the JSON message
    ``d`` union ``{"result": "success"}`` """
    d2 = {'result': 'success'}
    d2.update(d)
    return HttpResponse(json.dumps(d2), mimetype="application/json")


def json_success_response():
    """ Return a ``HttpResponse`` containing the JSON message
    ``{"message": "success", "result": "success"}`` """
    return HttpResponse(
        '{"message": "success", "result": "success"}',
        mimetype='application/json')


def json_error_response(error):
    """ Return a ``HttpResponse`` containing the JSON message
    ``{"result": "error", "message": error}`` """
    return HttpResponse(
        json.dumps({'result': 'error', 'message': error}),
        mimetype='application/json')


def html_error_response(request, error):
    return render(request, "error.html", {'message': error}, status=404)


def single_instance_task(timeout=3600 * 12):
    """
    Decorator that ensures that a celery task is only run once.
    Default timeout is 12 hours.

    See: http://stackoverflow.com/questions/4095940/running-unique-tasks-with-celery
    See: http://ask.github.com/celery/cookbook/tasks.html#ensuring-a-task-is-only-executed-one-at-a-time

    .. note::
        This only works if all tasks share the same django cache.
    """
    def task_exc(func):
        def wrapper(*args, **kwargs):
            lock_id = "single_instance_task:" + func.__name__
            acquire_lock = lambda: cache.add(lock_id, True, timeout)
            release_lock = lambda: cache.delete(lock_id)
            if acquire_lock():
                try:
                    func(*args, **kwargs)
                finally:
                    try:
                        release_lock()
                    except:
                        pass
            else:
                logger.info('Task %s already running' % func.__name__)
        wrapper.__name__ = func.__name__
        return wrapper
    return task_exc


def get_celery_worker_status():
    """
    Detects if working
    """
    # from
    # http://stackoverflow.com/questions/8506914/detect-whether-celery-is-available-running
    ERROR_KEY = "ERROR"
    try:
        from celery.task.control import inspect
        insp = inspect()
        d = insp.stats()
        if not d:
            d = {ERROR_KEY: 'No running Celery workers were found.'}
    except IOError as e:
        from errno import errorcode
        msg = "Error connecting to the backend: " + str(e)
        if len(e.args) > 0 and errorcode.get(e.args[0]) == 'ECONNREFUSED':
            msg += ' Check that the RabbitMQ server is running.'
        d = {ERROR_KEY: msg}
    except ImportError as e:
        d = {ERROR_KEY: str(e)}
    return d


def celery_available():
    """
    Return true if celery is available
    """
    status = get_celery_worker_status()
    if not status:
        return False
    return ("ERROR" not in status)


def run_async_if_celery(task, *args, **kwargs):
    """
    Run async if celery is online, else run serially
    """
    if celery_available():
        task.delay(*args, **kwargs)
    else:
        task(*args, **kwargs)


def estimate_count_fast(app, model):
    ''' postgres really sucks at full table counts, this is a faster version
    see: http://wiki.postgresql.org/wiki/Slow_Counting and
    http://chase-seibert.github.com/blog/2012/06/01/djangopostgres-optimize-count-by-replacing-with-an-estimate.html
    '''
    cursor = connection.cursor()
    cursor.execute(
        "select reltuples from pg_class where relname='website_%s';" % type)
    row = cursor.fetchone()
    return int(row[0])


def compute_entropy(values):
    """ Return the shannon entropy of a list of values.

    :param values: observations that will be processed into a histogram
    """
    num_values = len(values)
    if num_values == 0:
        return None
    if num_values == 1:
        return 0
    counts = [h[1] for h in Counter(values).most_common()]
    probs = [float(c) / num_values for c in counts]
    return -sum([p * math.log(p, 2) for p in probs])


def md5sum(filename_or_file):
    """ Returns the md5 hash of a file """
    md5 = hashlib.md5()
    if isinstance(filename_or_file, basestring):
        file = open(filename_or_file, 'rb')
    else:
        file = filename_or_file.open('rb')
    for chunk in iter(lambda: file.read(128 * md5.block_size), b''):
        md5.update(chunk)
    file.close()
    return md5.hexdigest()


def prepare_votes_bar(obj, obj_votes_attr, obj_result_attr, vote_attr, name):
    votes = getattr(obj, obj_votes_attr).filter(
        invalid=False).values_list(vote_attr, flat=True)
    score = getattr(obj, obj_result_attr + '_score')
    return prepare_votes_bar_impl(votes, score, name)


def prepare_votes_bar_impl(votes, score, name):
    num_yes = sum(1 for v in votes if v)
    num_no = sum(1 for v in votes if not v)
    perc_yes, perc_no = to_int_percent([num_yes, num_no])

    context = {
        'name': name,
        'num_total': num_yes + num_no,
        'num_yes': num_yes,
        'num_no': num_no,
        'perc_yes': perc_yes,
        'perc_no': perc_no,
    }

    if score:
        if score >= 1:
            score_yes = 100
        elif score <= -1:
            score_yes = 0
        else:
            score_yes = int(50 * (1 + score))
        score_no = 100 - score_yes
        context.update({
            'score': score,
            'score_positive': (score > 0),
            'score_yes': score_yes,
            'score_no': score_no,
        })

    return context


def get_upload_dir(obj, attr, time=None):
    """ Returns the directory used to save obj.attr files """
    if not time:
        time = datetime.datetime.now()
    upload_to = obj._meta.get_field(attr).upload_to
    return os.path.normpath(force_unicode(
        datetime.datetime.now().strftime(smart_str(upload_to))))


def save_obj_attr_file(obj, attr, filename, content, save=True, time=None):
    """ Saves a file onto an attribute of an object """

    # If the file doesn't have a name, Django will raise an Exception while
    # trying to save it, so we create a named temporary file.
    # (from django-imagekit)
    if not getattr(content, 'name', None):
        f = NamedTemporaryFile()
        f.write(content.read())
        f.seek(0)
        content = File(f)

    path = os.path.join(get_upload_dir(obj, attr, time), filename)
    logger.info("Saving %s" % path)
    getattr(obj, attr).save(path, content, save)


def save_obj_attr_image(obj, attr, img, suffix='', format='png', save=True):
    """
    Saves a PIL image to a file field (attr) on a model instance (obj).
    The filename is a hash of the image contant plus an optional suffix.
    """

    # save to buffer
    format = format.lower()
    content = img_to_fobj(img, format=EXT_TO_FORMAT[format])

    # choose a name that will not collide
    basename = unique_instance_name(obj)
    filename = '%s%s.%s' % (basename, suffix, format)

    # save object
    save_obj_attr_file(obj, attr, filename, content, save=save)


def save_obj_attr_base64_image(obj, attr, screenshot, suffix='',
                               format='png', save=True):
    """
    Saves a screenshot to a file field (attr) on a model instance (obj).
    The filename is a hash of the image contant plus an optional suffix.
    """

    # extract image data and format
    img_data = base64.decodestring(screenshot[screenshot.index(',') + 1:])
    img = Image.open(StringIO(img_data))
    save_obj_attr_image(obj, attr=attr, img=img, suffix=suffix,
                        format=format, save=save)


def compute_label_reward(label):
    """ compute the per-label reward """
    if label.mturk_assignment:
        hit = label.mturk_assignment.hit
        count = hit.contents.count()
        if count:
            return hit.hit_type.reward / count
    return None


def camel_to_underscore(name):
    """ Convert CamelCase names to camel_case style """
    s1 = _first_cap_re.sub(r'\1_\2', name)
    return _all_cap_re.sub(r'\1_\2', s1).lower()


def to_int_percent(items):
    """ Converts a list of numbers to a list of integers that exactly sum to
    100. """

    nitems = len(items)
    total = sum(items)
    if total == 0:
        return [0] * nitems

    perc = [100 * p // total for p in items]
    s = sum(perc)

    i = 0
    while s < 100:
        if items[i] > 0:
            perc[i] += 1
            s += 1
        i = (i + 1) % nitems

    return perc


def dict_union(a, b):
    """
    Return the union of two dictionaries without editing either.
    If a key exists in both dictionaries, the second value is used.
    """
    if not a:
        return b if b else {}
    if not b:
        return a
    ret = a.copy()
    ret.update(b)
    return ret


def dict_max_value(d):
    """
    Return the (key, value) with the maximum value.  This is the fastest way of
    doing this:
    http://stackoverflow.com/questions/268272/getting-key-with-maximum-value-in-dictionary
    """
    k = list(d.keys())
    v = list(d.values())
    max_v = max(v)
    return (k[v.index(max_v)], max_v)


def rgb_to_hex(r, g, b):
    """ Convert ``(r, g, b)`` in range [0.0, 1.0] to ``"RRGGBB"`` hex string. """
    return hex((
        ((int(r * 255) & 0xff) << 16) |
        ((int(g * 255) & 0xff) << 8) |
        (int(b * 255) & 0xff))
    )[2:]


def create_image_pair_grid_list(
        image_pairs, ncols=64, size=64, padding=0,
        show_progress=False, downsample_ratio=1):
    """ Greate a grid of images from a list of files """

    from pilkit.processors import ResizeToFit, ResizeCanvas

    nshapes = len(image_pairs)
    if downsample_ratio > 1:
        nshapes = (nshapes + downsample_ratio - 1) / downsample_ratio
        image_pairs = image_pairs[:nshapes]

    gridsize = size + padding
    nrows = (nshapes + ncols - 1) / ncols
    ncols = min(ncols, nshapes)
    out = Image.new(
        'RGBA', (ncols * gridsize, nrows * gridsize * 2),
        color=(255, 255, 255, 255))

    row = 0
    col = 0
    iterator = progress.bar(image_pairs) if show_progress else image_pairs
    for pair in iterator:
        for off, obj in enumerate(pair):
            try:
                thumb = open_image(obj)
            except Exception as e:
                print e
                continue
            thumb = ResizeToFit(size, size).process(thumb)
            thumb = ResizeCanvas(
                size, size, color=(255, 255, 255, 255)).process(thumb)
            out.paste(thumb, box=(
                col * gridsize,
                (2 * row + off) * gridsize,
                col * gridsize + size,
                (2 * row + off) * gridsize + size,
            ))
        col += 1
        if col >= ncols:
            col = 0
            row += 1

    # fix transparency (composite with pure opaque white)
    out.putdata([
        p if p[3] == 255
        else (
            (p[0] * p[3] + 255 * (255 - p[3])) / 255,
            (p[1] * p[3] + 255 * (255 - p[3])) / 255,
            (p[2] * p[3] + 255 * (255 - p[3])) / 255,
            255
        ) for p in out.getdata()
    ])

    return out


def create_image_grid_qset(qset, image_attr, ncols=40, size=64, padding=0,
                           show_progress=False, downsample_ratio=1, max_qset_size=None):
    """ Greate a grid of images from a queryset """

    from pilkit.processors import ResizeToFit, ResizeCanvas

    # clamp number of shapes
    nshapes = qset.count()
    if downsample_ratio > 1:
        nshapes = (nshapes + downsample_ratio - 1) / downsample_ratio
    if max_qset_size:
        nshapes = min(nshapes, max_qset_size)
    qset = qset[:nshapes]

    gridsize = size + padding
    nrows = (nshapes + ncols - 1) / ncols
    ncols = min(ncols, nshapes)
    out = Image.new(
        'RGB', (ncols * gridsize, nrows * gridsize), color=0xffffff)

    row = 0
    col = 0
    iterator = queryset_progress_bar(qset) if show_progress else qset
    for obj in iterator:
        try:
            thumb = open_image(getattr(obj, image_attr))
        except Exception as e:
            print e
            continue
        thumb = ResizeToFit(size, size).process(thumb)
        thumb = ResizeCanvas(size, size, color=(255, 255, 255)).process(thumb)
        out.paste(thumb, box=(
            col * gridsize,
            row * gridsize,
            col * gridsize + size,
            row * gridsize + size,
        ))
        col += 1
        if col >= ncols:
            col = 0
            row += 1

    return out


def group_iterable_by_attr(iterable, attr):
    """ Returns a dictionary mapping
    { val : [elements such that e.attr = val] } """
    groups = {}
    for e in iterable:
        val = getattr(e, attr)
        if val in groups:
            groups[val].append(e)
        else:
            groups[val] = [e]
    return groups


def get_foreign_key(model_class, field_name):
    """ Return the foreign keym model for model_class.field_name """
    try:
        field_object, model, direct, m2m = \
            model_class._meta.get_field_by_name(field_name)
        if (direct and (not m2m) and
                isinstance(field_object, models.ForeignKey)):
            return field_object.rel.to
    except:
        pass
    return None


def has_foreign_key(model_class, field_name):
    """ Return true if model_class has a foreign key with a given name """
    return (get_foreign_key(model_class, field_name) is not None)


class DateTimeJSONEncoder(json.JSONEncoder):

    """ JSON encoder that can handle datetime instances """
    def default(self, obj):
        if hasattr(obj, 'isoformat'):
            return obj.isoformat()
        else:
            return json.JSONEncoder.default(self, obj)
