#!/usr/bin/env bash
#
# Start a celery worker
#

DIR="$( builtin cd "$( dirname "$( readlink -f "${BASH_SOURCE[0]}" )" )" && pwd )"
source $DIR/load_config.sh

celery_cmd="source $VENV_DIR/bin/activate; builtin cd $SRC_DIR; celery worker -A config -Q intrinsic --loglevel=info --concurrency=32 --maxtasksperchild=1"

sudo -u $SERVER_USER bash -c "$celery_cmd"
