Image data
----------

To avoid downloading all image data at once, images are downloaded lazily from
our S3 bucket, *as they are accessed*.  If local copies are available, they are
used.  Otherwise, images are downloaded asynchronously (using celery).  If
python code requests image data (e.g. access image width) and it is not already
downloaded, then the file will be downloaded synchronously (not using celery).
OpenSurfaces data is downloaded from ``OPENSURFACES_REMOTE_STORAGE_URL`` and
saved to ``OPENSURFACES_LOCAL_STORAGE`` (default: local filesystem in
``$DATA_DIR/media``).

Notes
~~~~~

It is important to have celery running when using the webserver, or this system
will not work.

Further, it is important that you run all code that might touch image data as
the server user (``www-data``).  The relevant scripts in ``scripts/`` should
use the correct user.

If you accidentally run the webserver as the incorrect user, you can fix the
permissions with:

.. code-block:: bash

    ./scripts/fix_permissions.sh

Configuration
~~~~~~~~~~~~~

You can configure where local data is saved by modifying
``OPENSURFACES_LOCAL_STORAGE`` (in ``config/settings_local.py``).  Note that if
you change the storage to something remote like S3, you will need to update the
backend in ``common.backends.OpenSurfacesStorage`` to cache
``self.local.exists(...)``.  Otherwise, the system will be so slow that is is
unusable.

You can also disable this remote downloading system by editing the
configuration in ``config/settings_local.py``:

.. code-block:: py

    OPENSURFACES_USE_REMOTE_DATA = True

If you turn this off, then it is assumed that all image data is available in
``DEFAULT_FILE_STORAGE``, and no data will be downloaded from our OpenSurfaces.
If, for example, you wanted to start from scratch with your own dataset, and
not use any of the data we collected, then you would set
``OPENSURFACES_USE_REMOTE_DATA = False``.


