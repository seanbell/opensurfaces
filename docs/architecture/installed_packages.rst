.. _installed-packages:

Installed packages
------------------


Relevant Django packages
~~~~~~~~~~~~~~~~~~~~~~~~

While you can see a complete list of django packages in the ``INSTALLED_APPS``
setting in ``server/config/settings.py``, these are the most relevant Django
packages used by OpenSurfaces:

south
    Database migrations (changing anything in ``models.py`` files) are handled
    by South.  You should learn how to use South if you want to modify the
    database schema (e.g. to add a model).

storages and S3
    I use ``django-storages`` to help abstract how images are stored.  Right now,
    all image data is stored on Amazon's S3 service.  S3 is configured in
    ``server/config/settings_local.py``.  By default, as a debugging safety
    net, writes are disabled to S3 (via the ``S3_ENABLE_WRITE`` settting).
    This is done by replacing the standard Boto storage with the python class
    ``common.backends.ReadOnlyS3BotoStorage``

compressor
    ``django-compressor`` allows us to write static files in ``coffeescript``
    and ``less``, and have them automatically compiled to ``javascript`` and
    ``css`` respectively.

cacheback
    Many expensive pages (e.g. the homepage) take a long time to prepare (~20s)
    but still need to be updated ocassionally.  The ``django-cacheback``
    package provides a mechanism to serve cached copies of pages, and then
    asynchronously update the pages when stale (via celery) instead of waiting
    20s whenever the cache expires.

imagekit
    Thumbnails are automatically resized by ``django-imagekit``.  In the
    future, I plan to remove this dependency and manage thumbnails manually.
    Note that since the filename is computed from a hash of the thumbnail
    settings, changing the version of imagekit will invalidate all thumbnails,
    thus breaking the website.  So, if you want to change the version of
    ``imagekit``, you need to delete all old thumbnails (manually), and then
    recreate them.


Ubuntu
~~~~~~

The installer (``scripts/install/install_packages.sh``) will automatically
install and update the following Ubuntu packages:

.. literalinclude:: ../../scripts/install/requirements-ubuntu.txt

::

	postgresql-$PSQL_VERSION
	postgresql-contrib-$PSQL_VERSION
	postgresql-server-dev-$PSQL_VERSION

Python
~~~~~~

and these Python packages:

::

    setuptools
    versiontools

Inside a separate ``virtualenv`` environment, these Python packages will be
installed (separate from your root Python packages):

.. literalinclude:: ../../scripts/install/requirements-python-0.txt
.. literalinclude:: ../../scripts/install/requirements-python-1.txt
