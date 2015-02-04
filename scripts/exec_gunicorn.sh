#!/bin/bash
#
# This starts gunicorn (the worker framework that runs django code).
# Incoming web requests go to nginx, which are then fowarded to gunicorn.
#
# NOTE: while you can start this script, by default it is set up to be called
# by supervisorctl.
#
# This config is based on:
# http://michal.karzynski.pl/blog/2013/06/09/django-nginx-gunicorn-virtualenv-supervisor/

DIR="$( builtin cd "$( dirname "$( readlink -f "${BASH_SOURCE[0]}" )" )" && pwd )"
source $DIR/load_config.sh

SOCKFILE=$REPO_DIR/run/gunicorn.sock              # we will communicte using this unix socket
NUM_WORKERS=8                                     # how many worker processes should Gunicorn spawn
DJANGO_SETTINGS_MODULE=config.settings            # which settings file should Django use
DJANGO_WSGI=config.wsgi                           # which settings file should Django use

# Set up environment
builtin cd $SRC_DIR
export DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE
export PYTHONPATH=$SRC_DIR:$PYTHONPATH

# Create the run directory if it doesn't exist
RUN_DIR=$(dirname $SOCKFILE)
test -d $RUN_DIR || mkdir -p $RUN_DIR

# remove old sockfile
rm -f $SOCKFILE

# Notes:
# - exec is necessary to properly kill gunicorn instances
# - programs meant to be run under supervisor should not daemonize
#   themselves (do not use --daemon)
exec gunicorn ${DJANGO_WSGI}:application \
  --name $PROJECT_NAME \
  --workers $NUM_WORKERS \
  --user=$SERVER_USER \
  --group=$SERVER_GROUP \
  --bind=unix:$SOCKFILE \
  --log-level=debug \
  --timeout 600
