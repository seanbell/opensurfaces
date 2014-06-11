Running experiments
===================

This section outlines the steps in running experiments with our platform.

Sandbox experiments
-------------------

Before spending any money, you should veriy that everything works in the MTurk
sandbox.

make sure you are in production mode
    See :doc:`../setup` for instructions on how to set up the server and run in
    production mode.

switch to sandbox mode
    Set ``MTURK_SANDBOX = True`` in ``server/config/settings_local.py``.

    This will use https://workersandbox.mturk.com instead of
    https://www.mturk.com/.

configure the experiments
    For the experiments that you want to run, edit the ``experiments.py`` file
    in those apps (e.g. ``intrinsic/experiments.py``).  The most important
    parameter is ``auto_add_hits``.  Set this to ``True`` if you want to run
    this experiment.

start the experiments
    The following commands will dispatch tasks to MTurk:

    .. code-block:: bash

        ./manage.py mtconfigure
        ./manage.py mtconsume

    See :ref:`mturk-commands` for documentation of these commands.

verify that it works
    Navigate to http://workersandbox.mturk.com and find your task on the
    sandbox marketplace.

    Try submitting some results and check that they show up in the admin
    submission view (http://YOUR_HOSTNAME/mturk/admin/submission/)

expire experiments
    To expire all experiments, run:

    .. code-block:: bash

        ./manage.py mtexpire '.*'


Paid experiments
----------------

This section outlines the step in running paid experiments with our platform.


make sure you are in production mode
    See :doc:`../setup` for instructions on how to set up the server and run in
    production mode.

disable sandbox mode
    Set ``MTURK_SANDBOX = False`` in ``server/config/settings_local.py``.  This
    will switch to the main https://www.mturk.com/ server.

configure the experiments
    For the experiments that you want to run, edit the ``experiments.py`` file
    in those apps (e.g. ``intrinsic/experiments.py``).  The most important
    parameter is ``auto_add_hits``.  Set this to ``True`` if you want to run
    this experiment.

start the experiments
    The following commands will dispatch tasks to MTurk:

    .. code-block:: bash

        ./manage.py mtconfigure
        ./manage.py mtconsume

    Note that if all input objects have received the specified number of
    labels, then no work will be dispatched.  See :ref:`mturk-commands` for
    documentation of these commands.

monitor workers
    Watch users by either setting up Google Analytics or viewing the server log:

    .. code-block:: bash

        tail -f run/gunicorn.log

    It will take ~10min before you see the first submissions.

review submissions
    There are two methods to reviewing submissions:

    1. Automatically approve all submissions.  When using both tutorials and
       sentinels, I find that the proportion of high quality submissions is
       high enough to approve all workers.  While some bad work sneaks by I
       find that it is not worth rejecting, since workers get upset and don't
       like the uncertainty.

       To approve all submissions, set ``MTURK_AUTO_APPROVE = True`` in
       ``server/config/settings_local.py``.  This will approve with celery,
       which could have a long delay.  Workers like seeing instant approvals (I
       found that my submission rate increased by 50-100%), so it is worth
       running

       .. code-block:: bash

           ./manage.py mtapprove_loop '.*'

       while the experiment is running to automatically approve everything as
       quickly as possible.  The argument is a regular expression on the
       Experiment ``slug`` (human-readable ID).

    2. Manual review.
       Unfortunately I haven't had time to update the admin interface to have
       approve/reject buttons (since I always approve all submissions).  You
       can manually approve/reject by opening a Python shell on the server
       (``./scripts/django_shell.sh``) and running the command:

       .. code-block:: py

           MtAssignment.objects.get(id='ID').approve(feedback='Thank you!')

       or

       .. code-block:: py

           MtAssignment.objects.get(id='ID').reject(feedback='You made too many mistakes.')

       where ``ID`` is the assignment ID.

       I find that quality tends to be consistent within a worker, so you could
       write a loop to iterate over known good workers and approve those:

       .. code-block:: py

           GOOD_WORKER_MTURK_IDS = [ ... ]

           asst_qset = MtAssignment.objects.filter(
               status='S', worker__mturk_worker_id__in=GOOD_WORKER_MTURK_IDS)
           for asst in asst_qset:
               try:
                   asst.approve(feedback='Thank you!')
               except:
                   pass

       See :class:`mturk.models.MtAssignment` for more assignment-related methods.

    Note that approve/reject commands have a high chance of failing.  The
    Amazon MTurk server takes a while to recognize that a certain assignment is
    ready for approval.  The above scripts take this into account, so don't
    worry about lots of errors in the celery logs regarding approvals.

grant bonuses
    You can grant bonuses to assignments in the Python shell
    (``./scripts/django_shell.sh``) with the command:

    .. code-block:: py

           MtAssignment.objects.get(id='ID').grant_bonus(price=0.10, reason='You did a great job')

    where ``ID`` is the assignment ID.

    Note that users are promised small bonuses for completing feedback.  This
    is automatically handled by the :meth:`mturk.models.MtAssignment.approve`
    method.

stop experiments
    To expire all experiments, run:

    .. code-block:: bash

        ./manage.py mtexpire '.*'

sync status
    OpenSurfaces stores a local copy of the status of each HIT and Assignment.
    To make sure that local data is synchronized, run:

    .. code-block:: bash

        ./manage.py mtsync

check account balance
    To print your Amazon account balance to the console, run:

    .. code-block:: bash

        ./manage.py mtbalance

CUBAM
    If an experiment uses CUBAM to aggregate binary answers, run this to update
    all labels:

    .. code-block:: py

        ./manage.py mtcubam

    *Warning*: this will take several hours to run if you have millions of
    labels.


To add your own experiment, see :doc:`../extending`.


