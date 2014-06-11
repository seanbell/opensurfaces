#!/bin/bash
#
# Watch the web access log, continuously printing web requests to the screen
#

DIR="$( builtin cd "$( dirname "$( readlink -f "${BASH_SOURCE[0]}" )" )" && pwd )"
source $DIR/load_config.sh

sudo tail -f $REPO_DIR/run/nginx-access.log
