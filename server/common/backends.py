import logging
import urllib2
import urlparse

from django.conf import settings
from django.core.files.storage import Storage
from django.core.files.base import ContentFile
from django.core.exceptions import ImproperlyConfigured
from django.utils.http import urlquote
from django.core.cache import cache

from storages.backends.s3boto import S3BotoStorage
from imagekit.cachefiles.backends import CachedFileBackend
from queued_storage.utils import import_attribute

logger = logging.getLogger(__name__)


class ReadOnlyHttpStorage(Storage):
    """ Read-only file storage that downloads files over HTTP.

    :param prefix: URL prefix.  Paths are appended to the prefix to get the
        full URL.
    """

    def __init__(self, prefix=None):
        self.prefix = prefix
        if not self.prefix:
            self.prefix = settings.HTTP_STORAGE_URL
        if not self.prefix or not self.prefix.startswith('http://'):
            raise ImproperlyConfigured(
                "ReadOnlyHttpStorage expects a HTTP URL, not '%s'" % self.prefix)
        if not self.prefix.endswith("/"):
            self.prefix = self.prefix + "/"

    def listdir(self, name):
        raise NotImplementedError()

    def size(self, name):
        raise NotImplementedError()

    def exists(self, name):
        if name:
            url = self.url(name)
            try:
                urllib2.urlopen(url)
                return True         # URL Exist
            except ValueError:
                return False        # URL not well formatted
            except urllib2.URLError:
                return False        # URL don't seem to be alive
        else:
            return False

    def url(self, name):
        if name:
            return urlparse.urljoin(self.prefix, urlquote(name))
        else:
            return ""

    def _open(self, name, mode='rb'):
        if 'w' in mode:
            raise IOError("Cannot write to read-only http storage")
        url = self.url(name)
        file_content = urllib2.urlopen(url).read()
        return ContentFile(file_content)

    def delete(self, name):
        raise IOError("Cannot write to read-only http storage")

    def save(self, name, content):
        raise IOError("Cannot write to read-only http storage")

    def _save(self, name, content):
        raise IOError("Cannot write to read-only http storage")


class OpenSurfacesStorage(Storage):
    """
    Special filesystem for OpenSurfaces that serves files locally, downloading
    remote data as needed from the public OpenSurfaces S3 repository.  Since we
    pay for bandwidth, we would appreciate if you did not try and replace this
    with some system that no longer cached downloads locally.

    :param local: optionally, specify a different local storage.  Use ``None``
        to use ``settings.OPENSURFACES_LOCAL_STORAGE`` (default: filesystem
        storage that saves in ``media/``).  **Note:** we assume that checking
        ``exists()`` on the local storage is fast.  If this is not the case
        (e.g. you are using S3 as the local filesystem), then you should extend
        this class to cache info about which files exist.

    :param readonly: if ``True``, do not allow writes.

    :param cache_prefix: prefix for cache, to avoid clashes with other systems
        that use the cache.

    :param cache_timeout: timeout for cache.  If a download takes longer than this,
        it will be restarted.
    """

    def __init__(self, local=None, readonly=False, cache_prefix=None,
                 cache_timeout=300):

        self.local = local
        self.readonly = readonly
        self.cache_prefix = cache_prefix
        self.cache_timeout = cache_timeout

        if not self.cache_prefix:
            self.cache_prefix = 'OpenSurfacesStorage'

        if not self.local:
            self.local = import_attribute(settings.OPENSURFACES_LOCAL_STORAGE)()

        self.remote = ReadOnlyHttpStorage(prefix=settings.OPENSURFACES_REMOTE_STORAGE_URL)

    def get_cache_key(self, name):
        return '%s:%s' % (self.cache_prefix, name)

    def ensure_local(self, name, async=False):
        """
        Ensure that the file has been transferred to our local filesystem.
        """
        if async:
            # use a cache to avoid double downloading.  Storing "True' in the
            # cache indicates that a remote transfer has been queued.
            cache_key = self.get_cache_key(name)
            if not cache.get(cache_key):
                cache.set(cache_key, True, self.cache_timeout)

                from common.tasks import opensurfaces_storage_transfer
                opensurfaces_storage_transfer.delay(name)
        else:
            if not self.local.exists(name) and self.remote.exists(name):
                #logger.debug("Transferring '%s' to local storage" % name)
                self.local.save(name, self.remote.open(name))

    def listdir(self, name):
        raise NotImplementedError()

    def exists(self, name):
        return self.local.exists(name) or self.remote.exists(name)

    def size(self, name):
        self.ensure_local(name)
        return self.local.size(name)

    def delete(self, name):
        """ We cannot delete since a missing file is indistinguishable from
        not-yet-downloading. """
        raise IOError("Cannot delete from read-only http storage")

    def url(self, name):
        if self.local.exists(name):
            return self.local.url(name)
        else:
            self.ensure_local(name, async=True)
            return self.remote.url(name)

    def _open(self, name, mode='rb'):
        if 'w' in mode and self.readonly:
            raise IOError("Cannot write to read-only http storage")
        self.ensure_local(name)
        return self.local.open(name, mode)

    def _save(self, name, content):
        if self.readonly:
            raise IOError("Cannot write to read-only http storage")
        else:
            self.local.save(name, content)


class ReducedRedundancyS3BotoStorage(S3BotoStorage):
    """
    Amazon S3 storage with reduced redundancy
    """
    def __init__(self, *args, **kwargs):
        super(ReducedRedundancyS3BotoStorage, self).__init__(
            reduced_redundancy=True, *args, **kwargs)


class ReadOnlyS3BotoStorage(S3BotoStorage):
    """
    Amazon S3 storage with write disabled
    """

    def delete(self, name):
        logger.info("Prevented file delete: %s" % name)

    def save(self, name, content):
        logger.info("Prevented file save: %s" % name)

    def _save(self, name, content):
        logger.info("Prevented file save: %s" % name)


class ImageKitFileBackend(CachedFileBackend):
    """
    This fixes problems with the default ImageKit backend.
    The default ImageKit backend is doing something weird with file_exists.
    It returns False when the file exists.  It also seems to have some race conditions.
    """

    def file_exists(self, file):
        key = self.get_key(file)
        exists = self.cache.get(key)
        if exists is None:
            exists = not file.closed or file.storage.exists(file.name)
            self.cache.set(key, exists, 2592000)
        return exists

    def ensure_exists(self, file):
        if not self.file_exists(file):
            self.create(file)

    def create(self, file):
        key = self.get_key(file)
        key_lock = key + '_lock'
        if self.cache.add(key_lock, True, 300):
            try:
                file.generate(force=True)
                self.cache.set(key, True, 2592000)
            finally:
                self.cache.delete(key_lock)
        else:
            logger.debug('Thumbnail creation already started')
