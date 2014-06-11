Mechanical Turk
===============

OpenSurfaces contains a complete generic pipeline for running experiments on
Mechanical Turk.

It includes features such as:

  * API: abstraction of the MTurk API into clean python functions.

  * Admin interface: view submissions are they arrive, worker feedback,
    assignment statistics, experiment lists, scheduling info, task/tutorial
    previews.

  * Pipeline: scheduler for sorting and batching items together, filtering and
    regrouping results, and then feeding the output of one task as the input of
    another task.

  * Task tutorials: MTurk HITs can start with a mandatory tutorial that must
    be completed before any work is done.

  * Sentinel quality management: each task can be supplemented with secret
    items with known answers.  Users that perform poorly are banned (locally,
    not flagged on MTurk).

  * Dynamic generation of examples to show each user different subsets of a
    large database of examples.

  * Feedback: survey to gather thoughts from workers.

  * CUBAM: machine learning model for automatically modeling the competence and
    bias of workers, for tasks with binary answers (as described in Welinder
    P., Branson S., Belongie S., Perona, P. “The Multidimensional Wisdom of
    Crowds.” Conference on Neural Information Processing Systems (NIPS) 2010).

  * UI: MTurk interfaces for segmentation, object/material/scene labeling, BRDF
    appearance matching, 3D surface normal, binary quality filtering, point
    filtering, relative point comparisons.

**Contents**

.. toctree::
    :maxdepth: 2

    mturk/preparation
    mturk/run
    mturk/commands
    mturk/configuration
    mturk/attributes
