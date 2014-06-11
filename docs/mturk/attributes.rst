.. _mturk-model-attributes:

Model attributes
----------------

To simplify implementation, each model (e.g. ``MaterialShape``, ``Photo``, ...)
is expected to have certain attributes that implement various parts of the
MTurk pipeline.  For example, models that store user responses ("output content
model") is expected to have an ``mturk_submit`` method, and models that are
used in tasks are expected to have an ``MTURK_PREFETCH`` list indicating which
fields should be pre-fetched from the database.

Input models
~~~~~~~~~~~~

As part of the MTurk API, the following attributes are expected to exist on
input models to tasks:

.. py:attribute:: MTURK_PREFETCH

    Tuple of strings.
    When preparing to show a task, ``MTURK_PREFETCH`` declares which foreign
    key relationships will be used, thereby using 1 database query instead of
    many.

    For example, if you have a model ``PhotoPair`` that represents a pair of
    photos (``photo1`` and ``photo2``) that you are going to show to a user,
    you can fetch both photos at the same time by specifying:

    .. code-block:: py

        class PhotoPair(...):

            photo1 = ...
            photo2 = ...
            ...

            MTURK_PREFETCH = ('photo1', 'photo2')

Output models
~~~~~~~~~~~~~

The following attributes are expected to exist on output models for tasks.
See ``server/intrinsic/models.py`` for example implementations.

.. py:method:: mturk_submit(user, hit_contents, results, time_ms, time_active_ms, version, mturk_assignment=None, **kwargs)

    This function is called when a MTurk HIT is submitted, and is in charge of
    storing the user's response in the database.  This function is free to
    perform slow operations, since it will be performed asynchronously by a
    celery worker.

    :param user: mturk worker

    :param hit_contents: list of contents that the user was presented

    :param results: a dictionary, mapping the ``id`` of each content to the
        user's response.  This is returned by the javascript interface in the
        MTurk task.

    :param time_ms: total time taken by user, as a dictionary

    :param time_active_ms: only the time that the user was in the window, as a dictionary

    :param version: version string send by javascript interface

    :param mturk_assignment: :class:`mturk.models.MtAssignment` instances

    :return: a dictionary mapping contents to a list of objects created from that content.
        The dictionary key is of the form (ContentType id, object id), called a
        "content tuple", i.e. ``{ common.utils.get_content_tuple(content):
        [new_obj] } for content in hit_contents``.

.. py:method:: mturk_grade_test(test_content_wrappers, test_contents, results)

    Process the results of a secret test (i.e. a subset of the objects have
    known answers).  This only needs to be implemented if the experiment has
    test contents.

    :param test_content_wrappers: a list (or ``QuerySet``) of
        :class:`mturk.models.ExperimentTestContent` instances.  You should not
        need to use this list, since ``test_contents`` contains the actual test
        objects.

    :param test_contents: a list of the test objects shown to users.  Entry
        `i` in the list corresponds to entry `i` of ``test_content_wrappers``.

    :param results: a dictionary, mapping the ``id`` of each content to the
        user's response.  This is returned by the javascript interface in the
        MTurk task.

    :return: ``(responses, responses_correct)`` where the :math:`i^\text{th}`
        entry in ``responses`` is the extracted response from the
        :math:`i^\text{th}` entry of ``test_contents``, and the :math:`i^\text{th}`
        entry of ``responses_correct`` is a ``bool`` indicating whether the
        :math:`i^\text{th}` item in ``test_contents`` was correctly answered.

.. note::
    The ``mturk_grade_test`` method was added after the original OpenSurfaces
    publication, so many models do not contain this method.  See
    ``server/intrinsic/models.py`` for a complete example.
