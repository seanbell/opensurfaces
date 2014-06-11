import os
import lxml.html
import urllib2
from time import time
from collections import deque

from celery import shared_task
from celery.utils.log import get_task_logger
from imagekit.registry import cachefile_registry, generator_registry

from django.conf import settings
from django.contrib.contenttypes.models import ContentType

from common.utils import single_instance_task

logger = get_task_logger(__name__)


@shared_task
@single_instance_task(timeout=12 * 3600)
def prefetch_page_task(base_url=None, maxdepth=2):
    """ Prefetch pages, breadth-first, to populate the cache.  """
    if not settings.ENABLE_CACHING:
        logger.info("Caching disabled -- not prefetching")
        return
    if not base_url:
        base_url = settings.SITE_URL
    if not base_url.endswith('/'):
        base_url += '/'

    to_visit = deque()
    to_visit.append((base_url, 0))
    visited = set()
    while len(to_visit) > 0:
        url, depth = to_visit.popleft()
        visited.add(url)
        if not url.startswith(base_url):
            continue
        try:
            start = time()
            text = urllib2.urlopen(url).read()
            elapsed = time() - start
            logger.info('prefetch (%s, %.3f s): %s' % (depth, elapsed, url))
        except Exception as exc:
            logger.error(
                'prefetch (%s): error fetching %s: %s' % (depth, url, exc))
            return
        if depth < maxdepth:
            try:
                html = lxml.html.fromstring(text)
            except Exception as exc:
                logger.error(
                    'prefetch (%s): error parsing %s: %s' % (depth, url, exc))
                continue
            html.make_links_absolute(url)
            for element, attribute, link, pos in html.iterlinks():
                if (attribute.lower() == 'href' and link.endswith('/') and
                        link not in visited):
                    to_visit.append((link, depth + 1))


@shared_task
def os_remove_file(path):
    print 'Deleting file: %s' % path
    os.remove(path)


@shared_task
def opensurfaces_storage_transfer(name):
    """ Called by ``common.backends.OpenSurfacesStorage.ensure_local(...)`` """
    from common.utils import get_opensurfaces_storage
    storage = get_opensurfaces_storage()
    storage.ensure_local(name, async=False)


@shared_task
def generate_thumbs_by_id_task(generator_id):
    for file in cachefile_registry.get(generator_id):
        print '%s' % file.name
        try:
            file.generate()
        except Exception, err:
            print 'FAILED: %s' % err


@shared_task
def ensure_thumbs_exist_task(ct_id, pk):
    ct = ContentType.objects.get_for_id(ct_id)
    obj = ct.model_class().objects.get(pk=pk)
    visited = set()
    for gen_id in generator_registry.get_ids():
        split = gen_id.split(':')
        if len(split) == 3:
            f = split[2]
            if f not in visited:
                visited.add(f)
                if hasattr(obj, f):
                    file = getattr(obj, f)
                    try:
                        file.generate(force=False)
                        #logger.info('%s: %s' % (f, file.url))
                    except Exception as exc:
                        logger.info("Error generating thumb: %s" % exc)
