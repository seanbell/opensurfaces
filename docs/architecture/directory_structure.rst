.. _directory-structure:

Directory structure
-------------------

The OpenSurfaces repository has the following structure:

::

    server/              -- Django application ($SRC_DIR)
        config/
            settings.py                 -- general settings
            settings_local.py           -- settings specific to one machine
            settings_local_template.py  -- template for settings_local.py

        static/          -- common static files
        templates/       -- common templates

                         -- Django apps:
        common/          -- common utilities by all other packages
        home/            -- Home page, publications page
        mturk/           -- mturk platform
        accounts/        -- user accounts
        photos/          -- photos and scene categories
        shapes/          -- shape segmentation, object name, material name
        poly/            -- polygon utilities and segmentation UI
        bsdfs/           -- BSDF matching
        normals/         -- surface normals
        intrinsic/       -- intrinsic images
        licenses/        -- copyright licensing / creative commons
        analytics/       -- statistics web pages

    venv/                -- virtual python environment ($VENV_DIR)
        bin/
            activate     -- sets up virtualenv in the current shell
            ...
        ...

    scripts/             -- bash scripts
        config.sh        -- settings for bash scripts
        ...

    run/                 -- dynamic files for the running website
        gunicorn.sock    -- socket file (nginx <--> gunicorn communication)
        gunicorn.log     -- web access log (only dynamic pages)
        ...

    docs/                -- documentation
        ...

    triangulate/         -- utility to triangulate complex polygons
        ...

    prefilter/           -- prefiltered environment maps for BRDF matching
        ...

    opt/                 -- external libraries
        ...

    $DATA_DIR/           -- local data (defined in scripts/config.sh)
        static/          -- copies of static files to be served by nginx
        media/           -- local files/images (if not served from S3)

    $BACKUP_DIR/         -- database backups (defined in scripts/config.sh)
        pg_dump.sql.gz   -- postgresql dump file used for restoring the database
        ...

Each Django app is organized as follows:

::

    APP_NAME/

        models.py          -- Django models
        tasks.py           -- Celery tasks
        urls.py            -- URL mapping (from URL to functions in views.py)
        views.py           -- view functions
        tests.py           -- unit tests
        admin.py           -- registers models with the Django admin interface
        signals.py         -- register Django signals
        *.py               -- other modules specific to APP_NAME

        management/
            commands/      -- management commands (call with ./manage.py cmd)
                ...

        templates/
            APP_NAME/      -- templates (HTML, SVG fragments)
                ...

        static/            -- static files (served by nginx)
            js/
                APP_NAME/  -- coffeescript/javascript files
                    ...
            css/
                APP_NAME/  -- less/css files
                    ...
            img/
                APP_NAME/  -- images
                    ...

        cmd -> management/commands
        css -> static/APP_NAME/css
        js  -> static/APP_NAME/js
        img -> static/APP_NAME/img

.. note::
    For ``templates`` and ``static``, all files are in an additional nested
    level, i.e. ``APP_NAME/static/APP_NAME/css`` instead of
    ``APP_NAME/static/css``.

When Django merges all the directories together, if you don't have the extra
``APP_NAME`` subdirectory, different apps will potentially overwrite each
other.  Since the extra subdirectory is annoying, there are symlinks (``js ->
static/APP_NAME/js``, ``css -> static/APP_NAME/css``, etc.) for convenience.


