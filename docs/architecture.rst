Sytem architecture
==================

The OpenSurfaces webserver runs using a number of interacting systems:
gunicorn, nginx, postgres, celery, and memcached.  All of these components are
automatically configured and should work out of the box.  However, should you
need to change/debug/modify the webserver, you need to understand how all the
components fit together.

.. toctree::
    :maxdepth: 2

    architecture/components
    architecture/directory_structure
    architecture/settings
    architecture/image_data
    architecture/installed_packages
