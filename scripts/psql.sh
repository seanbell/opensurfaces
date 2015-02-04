#!/bin/bash
#
# Start a psql database shell.
#

DIR="$( builtin cd "$( dirname "$( readlink -f "${BASH_SOURCE[0]}" )" )" && pwd )"
source $DIR/load_config.sh

DB_PORT=$($DIR/pg_port.sh)

psql -p $DB_PORT $DB_NAME $DB_USER
