#!/bin/bash
#
# This script sets up directories and fixes permissions
#

# find the scripts directory (note the /..)
DIR="$( builtin cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
source $DIR/load_config.sh
cd "$REPO_DIR"

# increase sudo timeout
sudo -v

echo "Creating directories..."
sudo mkdir -p $DATA_DIR/media
sudo mkdir -p $DATA_DIR/static
sudo mkdir -p $BACKUP_DIR

echo "Fixing permissions..."
bash "$DIR/fix_permissions.sh"

echo "Fixing celerybeat-schedule..."
sudo rm -f $SRC_DIR/celerybeat-schedule

echo "Cleaning old static files..."
sudo rm -rf $DATA_DIR/static/*

echo "$0: done"
