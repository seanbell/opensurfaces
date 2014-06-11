#!/bin/bash
#
# Start a Python shell in the correct virtualenv and Django context
#

# load config
DIR="$( builtin cd "$( dirname "$( readlink -f "${BASH_SOURCE[0]}" )" )" && pwd )"
source $DIR/load_config.sh

# "manage.py" needs to start in "$SRC_DIR" in order to find the virtualenv
builtin cd $SRC_DIR

# "shell_plus" is an addon that auto-loads all of our models
sudo -u $SERVER_USER ./manage.py shell_plus
