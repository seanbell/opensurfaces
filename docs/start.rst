Getting Started
===============

This page walks you through installing a copy of the OpenSurfaces server on an
Ubuntu Linux machine.  I have only tested Ubuntu 12.04.

If not using Ubuntu, you can create a virtual machine using `VirtualBox
<https://www.virtualbox.org/>`_ and install `Ubuntu 12.04
<http://releases.ubuntu.com/12.04/>`_.

Installing the server
---------------------

This script sets up everything you need (installs packages, downloads all data,
sets up webserver and database):

.. code-block:: bash

   ./install_all.sh

The webserver and database will use ~15G of disk space when fully expanded.

**Prompts:** The installer will automatically ask you to specify some variables
the first time.  If you want to re-run the installer with different answers,
delete ``scripts/config.sh`` before running the installer again.

**Wait an hour:** The installer will take some time to finish, with most of the
time spent compiling numpy/scipy and building database indices.  Note that you
may have to give a ``sudo`` password multiple times since the installer takes
so long.

**Problems**: If you have problems with the installation, you can run the
entire installer again after fixing any issues.  Note that re-running the
installer will destroy any existing data, reverting it back to the original
dataset.  Please tell me about any problems you have by filing a bug report on
https://github.com/seanbell/opensurfaces or by emailing me at
:email:`sbell@cs.cornell.edu` (Sean Bell).


Visit the homepage
------------------

At this point, the website should be publicly viewable from your machine.  You
can now visit ``http://$SERVER_NAME/`` in a web browser (``SERVER_NAME`` is
defined in ``scripts/config.sh`` if you forgot what it is set to; the default
is ``localhost``).  To help set up things for the first time, ``DEBUG`` mode is
turned on.

To turn *off* the public webserver, run

.. code-block:: bash

    ./scripts/make_private.sh

and to turn it back *on*:

.. code-block:: bash

    ./scripts/make_public.sh

Unfortunately not everything is set up yet -- continue to :doc:`setup` for
additional setup information.
