#!/bin/bash
#
# Copies static files to the data directory.
#

# Load config
DIR="$( builtin cd "$( dirname "$( readlink -f "${BASH_SOURCE[0]}" )" )" && pwd )"
source "$DIR/load_config.sh"

echo "Collect static files..."
sudo -u $SERVER_USER bash -c "builtin cd $SRC_DIR; ./manage.py collectstatic --noinput"
