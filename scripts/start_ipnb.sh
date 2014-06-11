#!/bin/bash
#
# Start the ipython notebook server.  It is visible to admin users via
# http://$SERVER_NAME/accounts/admin-shell/
#

DIR="$( builtin cd "$( dirname "$( readlink -f "${BASH_SOURCE[0]}" )" )" && pwd )"
source $DIR/load_config.sh

builtin cd $SRC_DIR
sudo -u $SERVER_USER bash -c "export PYTHONPATH=$SRC_DIR:$PYTHONPATH; ./manage.py shell_plus --notebook"
