#!/bin/bash
#
# Perform all database migrations
#

DIR="$( builtin cd "$( dirname "$( readlink -f "${BASH_SOURCE[0]}" )" )" && pwd )"
source $DIR/load_config.sh

set -x -e
builtin cd $SRC_DIR
sudo -u $SERVER_USER ./manage.py syncdb
sudo -u $SERVER_USER ./manage.py migrate
