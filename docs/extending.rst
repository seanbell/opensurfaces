Extending the system
====================

The OpenSurfaces system was designed to be a modular platform and can handle
new pipelines of experiments.  You can add new experiments that use
OpenSurfaces data as input, or you can make a completely new pipeline.

**Important:** If you want to create a new experiment, we do not recommend
adding to any of the existing apps (``bsdfs``, ``shapes``, ``photos``, etc.).
While there is nothing stopping you, you will find it difficult to properly
organize your experiment, and you will be unable to incorporate any
improvements that we publish.  Instead, create new django apps and add your
experiment there.  Use ``scripts/create_app.sh <app_name>`` to create a new app.

.. .. toctree::
..     :maxdepth: 2
..
..     add/part1
..     add/part2
..     add/part3
..     add/part4
