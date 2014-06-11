.. _mturk-experiments-py:

Experiment configuration (``<app>/experiments.py``)
---------------------------------------------------

In each application that contains MTurk experiments, there is an
``experiments.py`` file describing how the experiment is configured.

For this section, see ``experiments.py`` files in each app for examples of how
they are implemented.  Note that if you add your own Django app, you must
register your app in both ``settings.INSTALLED_APPS`` and in
``settings.MTURK_MODULES``.

Each ``experiments.py`` file must contain the following methods:

.. py:method:: configure_experiments()

    Configure the experiment in the database, by calling :meth:`mturk.utils.configure_experiment`.

    This function is automatically called by the command ``./manage.py
    mtconfigure``.

.. py:method:: content_priority(experiment, obj)

    Return a priority to assign to ``obj`` for an experiment.  Higher
    priority objects are shown first.  Note that this is only called once
    at the time that ``obj`` is discovered.

    :param experiment: experiment being considered, instance of
        :class:`mturk.models.Experiment`

    :param obj: object to be assigned priority

    :return: priority, with higher values being served first

.. py:method:: make_reject_message(experiment, hit, perc)

    Return a reject message for when the submission performs too poorly
    with sentinel objects.  Return ``None`` to use a default message.  This
    function is called by ``mturk.views.external.make_reject_message``.

    :param experiment: experiment being considered, instance of
        :class:`mturk.models.Experiment`

    :param hit: HIT being rejected, instance of
        :class:`mturk.models.MtHit`

    :param perc: ``int`` percentage of answers that the user got correct, from
        0 to 100.

    :rtype: string or ``None``

.. py:method:: external_task_extra_context(slug, context)

    Optionally add extra context for each task (called by
    ``mturk.views.external.external_task_GET``)

    :param slug: string ID for experiment

    :param context: context dictionary to be modified

.. py:method:: configure_qualifications()

    Optionally create any MTurk qualifications.  If
    ``MTURK_CONFIGURE_QUALIFICATIONS = True`` (in
    ``server/config/settings.py``), this is called every time new tasks are
    dispatched.  This is not called when on the sandbox.

.. py:method:: update_votes_cubam(show_progress=False)

    Aggregate all user responses together using CUBAM.  This function is
    automatically called by ``mturk.tasks.mturk_update_votes_cubam_task``.

    :param show_progress: if ``True``, print messages to the console showing
        the progress.

    :return: optionally return the list of objects that have changed state,
        if another module is interested.  This list will be sent to the
        ``update_changed_objects`` method of all other ``experiments`` modules.

.. py:method:: update_changed_objects(changed_objects)

    Optionally perform some action when objects change state.  Note that since
    passing around a list of changed objects is expensive, methods will only
    return the list of changed objects if it knows that it will be used
    elsewhere.

    This function is automatically called by
    mturk.tasks.mturk_update_votes_cubam_task with all objects that were
    changed by new votes.

    :param changed_objects: a list of objects that were changed by CUBAM.


