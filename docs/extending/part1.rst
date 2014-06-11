Part 1: Create models
=====================

This part describes how to create the database models to describe your data.

Create a Django app
-------------------

Create a new Django app with

.. code-block:: bash

    ./scripts/create_app.sh tutorial_app

In ``server/config/settings.py``, add ``'tutorial_app',`` to the end of
``tutorial_app`` add ``'tutorial_app.experiments',`` to ``MTURK_MODULES``.
This registers your app with Django and our MTurk platform respectively.

Create models
-------------

In ``server/tutorial_app/models.py``, create Django models to encapsulate both
the tasks that need to be performed, as well as the MTurk responses to each
task.  Examples can be found in
``server/(intrinsic|normals|bsdfs|shapes|photos|...)/models.py``.

In the below example, ``PhotoTriplet`` is a set of 3 photos, and users will judge
whether ``photo0`` is closer to ``photo1`` or to ``photo2``.
The two ``mturk_*`` methods are documented below (:ref:`add-mturk-methods`).

File ``server/tutorial_app/models.py``:

.. literalinclude:: ../../server/tutorial_app/models.py
   :language: py
   :lines: 1-48


.. _add-mturk-methods:

Write MTurk methods
-------------------

As part of the MTurk API, see :ref:`mturk-model-attributes` for the attributes
expected to exist on models.

Here is an example implementation (file ``server/tutorial_app/models.py``):

.. literalinclude:: ../../server/tutorial_app/models.py
   :language: py
   :pyobject: PhotoTripletResponse


Migrate the database
--------------------

Update the database to include your new models:

.. code-block:: bash

    ./manage.py schemamigration tutorial_app --auto
    ./manage.py migrate

It's important that you read the Django South documentation if you do not
already understand what these commands do.  Using South is a key part of any
Django project (though in future versions of Django, this functionality will
be part of the main library and not a 3rd party addon).
