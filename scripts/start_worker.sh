#!/usr/bin/env bash
#
# Start a celery worker
# Usage: ./start_worker.sh [concurrency=2] [queue=celery]
#
#  example: ./start_worker.sh 2
#  example: ./start_worker.sh 2 local_server
#

DIR="$( builtin cd "$( dirname "$( readlink -f "${BASH_SOURCE[0]}" )" )" && pwd )"
source $DIR/load_config.sh

concurrency=2
if [ $# -ge 1 ]; then
	concurrency=$1
fi

queue=celery
if [ $# -ge 1 ]; then
	queue=$2
fi

if [[ $queue == "celery" ]]; then
	# note: -B set
	celery_cmd="builtin cd $SRC_DIR; $VENV_DIR/bin/celery worker -B -A $queue -Q celery --loglevel=info --concurrency=$concurrency --maxtasksperchild=1024"

	set -x
	if [[ "$USER" == "$SERVER_USER" ]]; then
		rm -f $SRC_DIR/celerybeat-schedule
		bash -c "$celery_cmd"
	else
		sudo rm -f $SRC_DIR/celerybeat-schedule
		sudo -u $SERVER_USER bash -c "$celery_cmd"
	fi
else
	# note: -B not set
	celery_cmd="builtin cd $SRC_DIR; $VENV_DIR/bin/celery worker -A config -Q $queue --loglevel=info --concurrency=$concurrency --maxtasksperchild=1"
	if [[ "$USER" == "$SERVER_USER" ]]; then
		bash -c "$celery_cmd"
	else
		sudo -u $SERVER_USER bash -c "$celery_cmd"
	fi
fi
