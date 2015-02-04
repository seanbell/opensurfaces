#!/usr/bin/env bash
#
# Start a celery worker
#

DIR="$( builtin cd "$( dirname "$( readlink -f "${BASH_SOURCE[0]}" )" )" && pwd )"
source $DIR/load_config.sh

concurrency=2
if [ $# -ge 1 ]; then
	concurrency=$1
fi

user=$SERVER_USER
if [ $# -ge 2 ]; then
	user=$2
fi

# TODO: run as a background process with a higher log level
celery_cmd="source $VENV_DIR/bin/activate; builtin cd $SRC_DIR; celery worker -B -A config -Q celery --loglevel=info --concurrency=$concurrency --maxtasksperchild=1024"

set -x
if [[ $USER == $user ]]; then
	rm -f $SRC_DIR/celerybeat-schedule
	"$celery_cmd"
else
	sudo rm -f $SRC_DIR/celerybeat-schedule
	sudo -u $user bash -c "$celery_cmd"
fi
