Setup
=====

See :doc:`start` for installation instructions.

Running the webserver
---------------------

1) Run celery
~~~~~~~~~~~~~
The server delegates certain tasks to celery, which should be running at all
times.

In a separate window (or tmux session), run ``./scripts/start_worker.sh
<concurrency>``, where ``concurrency`` is the number of workers (you only need
1-4, at most half the number of cores).  This will be left open permanently.
This is not run as a background daemon since you cannot run it indefinitely
when in debug mode, and you may want to frequently restart the service and/or
view its current output.

Optional: Running without celery
""""""""""""""""""""""""""""""""

Note that for debug purposes, you can run all asynchronous tasks synchronously
by editing the file ``server/config/settings_local.py`` and setting:

.. code-block:: py

    CELERY_ALWAYS_EAGER = True

In this mode, the server will run more slowly but a worker is not necessary.

2) Run the server
~~~~~~~~~~~~~~~~~
You can then run the webserver a couple of different ways.  I recommend the
first method while developing / exploring the code.

private debug mode (with runserver)
    The easiest way to debug the server is with:

    .. code-block:: bash

        ./scripts/run_debug_server.sh

    and visit ``localhost:8000`` in the browser (to use a port other than 8000,
    run ``./scripts/run_debug_server.sh <port>``).  In this mode, the website
    is only visible to your machine, and only one user can view the website at
    a time.  Stack traces are viewable in the browser.  If you make code
    changes, the webserver should auto-restart.

    This script sets ``DEBUG = True`` (in ``server/config/settings_local.py``),
    kills any publicly running server, and then starts a Django server
    (``runserver``) as the server user.  Note that you cannot run as the local
    user since static files (created dynamically) need to be saved with the
    correct owner.

public debug mode (with nginx and gunicorn)
    With ``DEBUG = True`` (in ``server/config/settings_local.py``), you can
    also run with gunicorn and nginx.  This will serve pages publicly.  This is
    useful when you were in production mode, but temporarily want to debug some
    problem on a remote server.  As with the above mode, stack traces are
    displayed in the web browser.  To automatically set ``DEBUG = True``,
    and enable nginx/gunicorn (if disabled), you can run:

    .. code-block:: bash

        ./scripts/enable_debug.sh

    In this mode, you can also profile how well your code is running by setting
    ``DEBUG_TOOLBAR = True`` (in ``server/config/settings_local.py``).
    See :doc:`architecture` for information on how to start/stop nginx and gunicorn.

production mode (with nginx and gunicorn)
    When in production mode (e.g. running MTurk experiments or hosting the
    final webserver), you should set ``DEBUG = False`` and ``ENABLE_CACHING =
    True`` (in ``server/config/settings_local.py``).  To automatically set
    these variables, enable nginx (if disabled), and restart gunicorn, you can
    run:

    .. code-block:: bash

        ./scripts/enable_production.sh

    In production mode, stack traces are emailed to the ``ADMINS`` variable in
    ``server/config/settings_local.py``.
    See :doc:`architecture` for information on how to start/stop nginx and gunicorn.

.. note::
    You should not run in debug for long periods of time (e.g. weeks or
    months), since every query executed is retained in memory.  Eventually you
    will run out of memory.


Making changes to the code
--------------------------

Whenever you change any python code, html templates, static files, etc., you
need to restart/notify the appropriate server components:

flush caches
    Run the following script to update static files, restart gunicorn, flush
    memcached, and rebuild the docs:

    .. code-block:: bash

        ./scripts/files_changed.sh

    After flushing the cache, the first view for each page will be very slow
    (the home page is the slowest, at ~20s).  You can pre-emptively visit the
    main pages with the command:

    .. code-block:: bash

        ./scripts/warm_cache.sh

    Note that you can disable HTML caching by setting ``ENABLE_CACHING =
    False`` (in ``server/config/settings_local.py``).  With caching disabled
    and ``DEBUG = True``, you only need to run ``scripts/files_changed.sh``
    after modifying static files (css, js, less, etc).

update celery worker
    If you modify code that runs on celery (anything in a ``<app>/tasks.py``
    file), you need to restart the celery worker.

    Kill the worker you started with ``./scripts/start_worker.sh`` and start a
    new one.
