.. _architecture-settings:

Settings
--------

Settings for this project are split up in a few different places:

::

    scripts/config.sh                    (for Bash scripts)
    server/config/settings.py            (for Django)
    server/config/settings_local.py      (for Django, specific to one machine)

At install time, the files on the left are filled in and then saved as the
files on the right:

::

    config_template.sh          -->  config.sh
    settings_local_template.sh  -->  settings_local.py

Each file described in more detail:

``scripts/config.sh``
  used by all Bash scripts and contains basic info about the server.  By
  default, this does not exist.  To create it, either copy the template
  (``config_template.sh``) and fill in the fields, or run
  ``scripts/create_config.py``.

  This file is excluded from the git repository.

``server/config/settings.py``
  global Django settings that can be shared between different deployments.
  While every project should be able to share the same settings in this file,
  feel free to modify it.

  This file imports the local settings (``settings_local.py``), thereby merging
  all Django settings.

``server/config/settings_local.py``
  logal Django settings particular to a server instance.  When you use the
  install script (``scripts/install_all.sh``), this file is automatically
  populated with settings from ``scripts/config.sh``.

  This file is excluded from the git repository.


