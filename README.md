# OpenSurfaces

OpenSurfaces is a large database of annotated surfaces created from real-world
consumer photographs. Our annotation framework draws on crowdsourcing to
segment surfaces from photos, and then annotate them with rich surface
properties, including material, texture and contextual information.

Documentation is available at: http://opensurfaces.cs.cornell.edu/docs/

**Ubuntu**:
If you are on Ubuntu 12.04 or later, you can run `install_all.sh` to install
all components (will use ~15G disk space).

**Other systems**:
You will need to rewrite the installer (all files in `install/`) to use local
paths and package names specific to your distribution, but otherwise it should
work.

**Windows**:
If you're on Windows, install (VirtualBox)[https://www.virtualbox.org/] and
install Ubuntu 12.04 as a virtual machine since some of the required packages
don't have Windows versions.

**Mac**:
This might run on Mac OSX.  The core django code should run, but you may need
to find replacements for some components and rewrite some of the Bash code in
`scripts/`.
