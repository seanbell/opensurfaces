Querying the database
=====================

This page describes how to query the database, once you have it installed on
your local machine (installation instructions here: :doc:`setup`).

Method 1: use the Python shell
------------------------------

To try some of these queries interactively, start a Python shell:

.. code-block:: bash

    ./scripts/django_shell.py

and then perform one of the below example queries to obtain a Django `QuerySet
<https://docs.djangoproject.com/en/1.6/ref/models/querysets/>`_.
The ``shell_plus`` command automatically imports all models.

Method 2: write a Python script
-------------------------------

To write your own script that connects to Django, the easiest method is to add
a "mangement command".  When you call these scripts, Django will automatically
set up the necessary environment so that you have full access to all models,
databases, celery workers, etc.

1. Create a new Django app (if you haven't already):

   .. code-block:: bash

       ./scripts/create_app.sh YOUR_APP_NAME

2. Register your app with Django: add ``'YOUR_APP_NAME'`` to the end of the
   ``INSTALLED_APPS`` tuple in ``server/config/settings_local.py``

3. Write your script in ``server/YOUR_APP_NAME/cmd/your_script.py``.  Here is
   an example:

   .. code-block:: py

        from django.core.management.base import BaseCommand

        # import your models here, e.g.
        from photos.models import Photo
        from shapes.models import MaterialShape

        class Command(BaseCommand):
            args = ''
            help = 'Some documentation'

            def handle(self, *args, **options):

                # your code here
                num_photos = Photo.objects.all().count()
                print "There are %s photo records" % num_photos

   You can find more examples in ``server/shapes/cmd``, ``server/photos/cmd``,
   etc.

   Django documentation for management commands: `here
   <https://docs.djangoproject.com/en/1.6/howto/custom-management-commands/>`_.


4. Call the script from the ``server/`` directory:

   .. code-block:: bash

       ./manage.py your_script



Example queries: Photos
-----------------------

* All photos with **correct scene labels** and no special effects:

  .. code-block:: py

      photos_qset = Photo.objects.filter(
          special=False,                               # no synthetic/rendered photo
          inappropriate=False,                         # no sexual content
          rotated=False,                               # not rotated
          stylized=False,                              # no images with distorted color space
          nonperspective=False,                        # no fisheye
          scene_category_correct_score__isnull=False,  # scene category has been scored
          scene_category_correct=True,                 # scene category label correct
          license__creative_commons=True,              # creative commons license
      ).order_by('-scene_category_correct_score')      # order by decreasing CUBAM score

  Since these filters are common, you can use
  :attr:`photos.models.Photo.DEFAULT_FILTERS` as a shortcut:

  .. code-block:: py

      photos_qset = Photo.objects.filter(**Photo.DEFAULT_FILTERS) \
          .order_by('-scene_category_correct_score')

* All **white balanced** photos with correct scene labels, ordered by decreasing
  CUBAM score:

  .. code-block:: py

      photos_qset = Photo.objects \
          .filter(whitebalanced=True, **Photo.DEFAULT_FILTERS) \
          .order_by('-whitebalanced_score')

* All photos that contain **at least 6 material shapes**, ordered by decreasing
  number of shapes:

  .. code-block:: py

      photos_qset = Photo.objects \
          .filter(num_shapes__gte=6, **Photo.DEFAULT_FILTERS) \
          .order_by('-num_shapes')

* **Download** a copy of all photos in a ``QuerySet`` at a horizontal
  resolution of 2048 pixels.  Assuming you already have a set of photos as
  ``photos_qset``:

  .. code-block:: py

      import os
      from common.utils import progress_bar

      save_dir = "some_output_directory"
      for p in progress_bar(photos_qset):
          with open(os.path.join(save_dir, '%s.jpg' % p.id)) as f:
              p.image_2048.seek(0)
              f.write(p.image_2048.read())

  *Note:* Since we pay Amazon for all outgoing bandwidth, we would appreciate
  if you minimized the number of times that you download image data.

* Other filters: look at :class:`photos.models.Photo` for a list of all
  attributes for filtering.


Example queries: Shapes
-----------------------

Note that for shape segmentations (``MaterialShape`` instances), ``name`` is
the object name and ``substance`` is the material name.

* All shapes that have a material of either "Wood" or "Painted":

  .. code-block:: py

    materials = ['Wood', 'Painted']

    shapes_qset = MaterialShape.objects \
        .filter(**Shape.DEFAULT_FILTERS) \
        .filter(substance__name__in=materials)

* All shapes with an object label of either "Wall" or "Floor":

  .. code-block:: py

    materials = ['Wall', 'Floor']

    shapes_qset = MaterialShape.objects \
        .filter(**Shape.DEFAULT_FILTERS) \
        .filter(name__name__in=materials)

* All shapes with at least 100 vertices:

  .. code-block:: py

    shapes_qset = MaterialShape.objects \
        .filter(**Shape.DEFAULT_FILTERS) \
        .filter(num_vertices__gt=100)

* Other filters: look at :class:`shapes.models.MaterialShape` for a list of
  all attributes for filtering.


Example queries: BRDFs
----------------------

* All BSDFs that are close to an existing ``bsdf``, within ``dE`` change in
  ``L*a*b*`` color and ``dc`` change in gloss:

    .. code-block:: py

        bsdf_qset = ShapeBsdfLabel_wd.objects.filter(
            shape__photo__inappropriate=False,
            shape__correct=True,
            color_L__gte=bsdf.color_L - dE,
            color_L__lte=bsdf.color_L + dE,
            color_a__gte=bsdf.color_a - dE,
            color_a__lte=bsdf.color_a + dE,
            color_b__gte=bsdf.color_b - dE,
            color_b__lte=bsdf.color_b + dE,
            contrast__gte=bsdf.contrast - dc,
            contrast__lte=bsdf.contrast + dc,
            shape__bsdf_wd_id=F('id'),
        )

* Other filters: look at :class:`bsdfs.models.ShapeBsdfLabel_wd` for a list
  of all attributes for filtering.


Example queries: Normals
------------------------

* Look at :class:`normals.models.ShapeRectifiedNormalLabel` for a list of
  all attributes for filtering.
