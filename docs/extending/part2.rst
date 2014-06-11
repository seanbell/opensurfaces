Part 2: Create views
====================

This part describes how to create HTML views to view your data in the browser.

Create a URL mapping
~~~~~~~~~~~~~~~~~~~~

We will enable two ways of viewing photo triplets: list all triplets, or show a
single triplet.  This corresponds to two view functions which will be assigned
two URL patterns.

The two view functions are:

==================  ========================================================
``triplet_all``     show all triplets with endless scrolling
``triplet_detail``  show one triplet in detail with the individual responses
==================  ========================================================

First, we create the URL mappings in ``urls.py`` (``server/tutorial_app/urls.py``):

.. literalinclude:: ../../server/tutorial_app/urls.py
   :language: py

Next, we need to register the app URLs.  In ``server/config/urls.py``, add

.. code-block:: py

    url(r'^tutorial_app/', include('tutorial_app.urls')),

to the ``urlpatterns`` tuple.

Write view functions
~~~~~~~~~~~~~~~~~~~~

To handle pagination for ``triplet_all``, we will use
``django-endless-pagination`` (Version 1.1, not 2.0) to show an "endless" list
of entries that shows more items as the user scrolls down the page.

Here we show example code for the two view functions, with inline comments
(``server/tutorial_app/views.py``):

.. literalinclude:: ../../server/tutorial_app/views.py
    :language: py


Write HTML templates
~~~~~~~~~~~~~~~~~~~~

These two view functions need HTML templates, stored in:
``server/tutorial_app/templates/tutorial_app/``.  Note the double nested
directory.  See :ref:`directory-structure` for why this is important.

Since templates are very project-dependent, we will simply list the templates
that we had to write for this demo:

    ``server/tutorial_app/templates/tutorial_app/triplet_thumb.html``
        HTML fragment showing the triplet after aggregating all responses, and contains a small
        overlay showing which photo is closer, and the CUBAM score.

    ``server/tutorial_app/templates/tutorial_app/triplet_response_thumb.html``
        HTML fragment showing single user's response to which pair is closer in the triplet.

    ``server/tutorial_app/templates/tutorial_app/triplet_photos.html``:
        HTML fragment showing the three photos in a triplet, arranged either
        horizontally or vertically depending on ``triplet_photo_row``.

    ``server/tutorial_app/templates/tutorial_app/triplet_detail.html``
        Page showing details about a specific triplet.

    ``server/tutorial_app/templates/tutorial_app/triplet_all.html``
        Page containing a list of all triplets.

As an example, here is one of the templates:
(``server/tutorial_app/templates/tutorial_app/triplet_thumb.html``):

.. literalinclude:: ../../server/tutorial_app/templates/tutorial_app/triplet_thumb.html
    :language: html
    :tab-width: 2
