#!/bin/bash
#
# Set up nginx and gunicorn
#

# find the scripts directory (note the /..)
DIR="$( builtin cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
source $DIR/load_config.sh
cd "$REPO_DIR"

# increase sudo timeout
sudo -v

# kill any existing installation
bash "$DIR/make_private.sh"
sudo rm -f /etc/nginx/sites-available/$PROJECT_NAME

# create a new installation
bash "$DIR/make_public.sh"

echo "$0: done"
