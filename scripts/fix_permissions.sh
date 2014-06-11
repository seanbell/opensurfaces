#!/bin/bash
#
# Fixes permissions for the project.  You may need to run this if you ran
# "./manage.py runserver" as the current user instead of $SERVER_USER.
#

DIR="$( builtin cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $DIR/load_config.sh

# pass the username as the first argument (useful if using sudo)
LOCAL_USER=$USER
if [ $# -ge 1 ]; then
	LOCAL_USER=$1
fi

# Repository: owned by local user, viewable by webserver.
# (since the local user will be writing new files here).
sudo chown -R $LOCAL_USER:$SERVER_GROUP $REPO_DIR/server

# Run: only server has ownership
sudo chown -R $SERVER_USER:$SERVER_GROUP $REPO_DIR/run

# Data directories: owned by webserver, but editable by user.
# (since the webserver will be writing new files here).
sudo chown -R $SERVER_USER:$LOCAL_USER $DATA_DIR

# Backup: only local user has ownership
sudo chown -R $LOCAL_USER:$LOCAL_USER $BACKUP_DIR

# Data and backup: user and group have full edit permissions, no files are
# executable, and 'other' has read-only permissions.
sudo bash -c "find $DATA_DIR $BACKUP_DIR -type d -exec chmod 775 {} \+"
sudo bash -c "find $DATA_DIR $BACKUP_DIR -type f -exec chmod 664 {} \+"
