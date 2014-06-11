#!/bin/bash
# Analyze the web access log

DIR="$( builtin cd "$( dirname "$( readlink -f "${BASH_SOURCE[0]}" )" )" && pwd )"
source $DIR/load_config.sh

sudo goaccess -f $REPO_DIR/run/nginx-access.log
