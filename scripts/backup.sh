#!/bin/bash
#
# Backs up the server
#

DIR="$( builtin cd "$( dirname "$( readlink -f "${BASH_SOURCE[0]}" )" )" && pwd )"
source $DIR/load_config.sh

PG_OUT=$BACKUP_DIR/$(date +%Y-%m-%dT%H-%M-%S -d "now").sql.gz
$DIR/dump_database.sh $PG_OUT

tar czvf $BACKUP_DIR/$(date +%Y-%m-%dT%H-%M-%S -d "now").tar.gz $DATA_DIR $PG_OUT
