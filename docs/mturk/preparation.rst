Preparation to use MTurk
------------------------

Before you can run experiments on MTurk, you need to obtain an MTurk account
and an SSL certificate.

obtain an mturk account
    You need an Amazon MTurk Requester account from
    https://requester.mturk.com/.  Place your secret key info in
    ``MTURK_AWS_ACCESS_KEY_ID`` and ``MTURK_AWS_SECRET_ACCESS_KEY`` in the file
    ``server/config/settings_local.py``.

    Note that there is room for two sets of keys: we allow for you to use
    different keys for sandbox mode.  While you can make the two sets the same,
    you my find it useful to use an entirely different account for the sandbox.

obtain an SSL certificate
    Unfortunately you need to set up SSL in order to properly use MTurk as a
    nested iframe (this wasn't always the case).  Without a certificate, the
    browsers of your workers will notice that ``mturk.com`` is served over
    HTTPS, but that your task is served over HTTP, and refuse to serve your
    task.

    If you already have an SSL certificate for your server (with the
    appropriate hostname), you can use that.  Otherwise, I had good success
    obtaining a reasonably cheap SSL certificate with `Gandi
    <https://www.gandi.net/ssl?lang=en>`_.  Any other provider also works.

    Once you have the certificate, update nginx to have a path to your
    certificate by editing ``/etc/nginx/sites-available/PROJECT_NAME``, where
    ``PROJECT_NAME`` is specified in ``scripts/config.sh`` (default:
    ``opensurfaces``).

    Update ``server/config/settings_local.py`` with ``ENABLE_SSL = True``.

    Restart both nginx and gunicorn (see :doc:`../architecture`).  You should now
    be able to visit the site with the ``https:`` prefix.


.. note::
    If you want to use our segmentation task (``"segment_material"``), then:
    you need to install CGAL (version >= 4.1, < 5, from http://www.cgal.org)
    and build the ``triangulate`` program (``cd triangulate;
    ./build.sh``).  The Ubuntu version of CGAL is too old.  Note that you
    may have to add ``/usr/local/lib`` to your ``LD_LIBRARY_PATH`` if it not
    already there.
