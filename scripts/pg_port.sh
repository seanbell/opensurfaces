#!/bin/bash
#
# Prints the port used by the database
#

DIR="$( builtin cd "$( dirname "$( readlink -f "${BASH_SOURCE[0]}" )" )" && pwd )"
source $DIR/load_config.sh >/dev/null

echo $(sudo pg_lsclusters | grep $PSQL_VERSION | grep "$DB_DIR" | grep $DB_CLUSTER | awk '{print $3}')
