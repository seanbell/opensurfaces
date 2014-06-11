Component description
---------------------

virtualenv
    wraps all python packages so that you can have two copies of the same
    package.  For this codebase, all Python packages are installed inside a
    virtual environment (``venv/`` directory).  Before installing any
    new Python packages, set up the environment with:

    .. code-block:: bash

        source venv/bin/activate

    Otherwise, you will install into the global Ubuntu directory and the
    webserver will not find the packages.  Then, install python packages
    locally
    (**without** ``sudo``) with:

    .. code-block:: bash

        pip install some-package

gunicorn
    manages the pool of workers that run python code to generate dynamic
    webpages.  You can manage this service using:

    .. code-block:: bash

        sudo supervisorctl (start|stop|restart) $PROJECT_NAME

    where ``PROJECT_NAME`` is defined in ``scripts/config.sh`` (default:
    ``opensurfaces``).

    Logs are saved locally to ``run/gunicorn.log``, so you can view requests as
    they arrive with:

    .. code-block:: bash

        tail -f run/gunicorn.log


nxinx
    manages incoming HTTP requests and communicates via a socket with
    gunicorn.  The configuration for the nginx webserver is
    ``/etc/nginx/sites-available/PROJECT_NAME``, where ``PROJECT_NAME``
    is specified in ``scripts/config.sh`` (default: ``opensurfaces``).

    You can manage this service using:

    .. code-block:: bash

        sudo service nginx (start|stop|restart)

    Note that if you make a python code change, you only need to restart
    gunicorn, not nginx.

    Logs are saved locally to ``run/nginx-access.log`` and
    ``run/nginx-error.log`` and rotated automatically.  The default
    configuration is to rotate weekly and keep 52 old logs.  Edit
    ``/etc/logrotate.d/nginx`` if you want to change this.

postgresql
    is the database server that holds all annotations and metadata.
    Images and static files are not stored in the database.  The python process
    connects to the database as per the ``DATABASES`` setting stored in
    ``server/config/settings_local.py``.

    You can manage this service using:

    .. code-block:: bash

        sudo service postgresql (start|stop|restart)

    You can save a snapshot of the database as a backup (to ``BACKUP_DIR``) with:

    .. code-block:: bash

        ./scripts/dump_database.sh

    and you can revert from the most recent backup with:

    .. code-block:: bash

        ./scripts/restore_database.sh``

    Logs are stored in the default location:

    ::

        /var/log/postgresql/postgresql-PSQL_VERSION-labelmaterial.log

    where ``PSQL_VERSION`` is specified in ``scripts/config.sh`` (default:
    ``9.1``).  Note that the database cluster/name/user is ``"labelmaterial"``
    and not ``PROJECT_NAME``.  This is the old name of the project; changing it
    would break all of our database backups.

celery
    runs asynchronous tasks such as cache updates, processing incoming
    MTurk submissions, adding new tasks to MTurk, updating counters.

    Currently you need to run this service manually using:

    .. code-block:: bash

        ./scripts/start_worker.sh <concurrency>

    where ``concurrency`` is the number of workers.  Never set this to more
    than half the number of cores on your machine, since *all* layers are
    running on the same machine.

    If you change any celery code (in a ``tasks.py`` file), the worker will
    **not** automatically run the newest code.  You need to shut down the
    worker and start it up again.

    To kill all pending tasks (warning: this will discard pending MTurk
    submissions), run (from the ``server`` directory):

    ..code-block:: bash

        celery purge

rabbitmq
    is the messaging service used to communicate between celery nodes.

    You shouldn't have to manage this service.

memcached
    is an in-memory cache that stores HTML fragments so they don't need to be
    regenerated.

    You can manage this service using:

    .. code-block:: bash

        sudo service memcached (start|stop|restart)

    Note that the installer changes the global settings for memcached in
    ``/etc/memcached.conf`` (it increased the max filesize -- yes I know that
    this degrades performance).


**How it all fits together**: Incoming web requests are handled by Nginx.
Requests for static content (URL starts with ``/static/``) are returned
immediately by Nginx, while all other dynamic requests are handled by Python
workers running Django.  Gunicorn manages this pool of workers and
communicates with Nginx over a socket file (``run/gunicorn.sock``).  The
gunicorn workers fetch data from a PostgreSQL database and assemble pages
from HTML templates.  For speed, rendered HTML is cached in memcached, and
slow tasks are run asynchronously using celery.  Details of each system are
given below:


