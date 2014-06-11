#!/bin/bash
#
# Backs up the server postgres database
#

DIR="$( builtin cd "$( dirname "$( readlink -f "${BASH_SOURCE[0]}" )" )" && pwd )"
source $DIR/load_config.sh

if [ $# -ge 1 ]; then
	PSQL_OUT=$1
else
	# make sure field is filled in
	if [[ -z "$BACKUP_DIR" ]]; then
		echo "Please add a backup directory to $DIR/config.sh"
		echo "BACKUP_DIR=$BACKUP_DIR"
		exit 1
	fi
	PSQL_OUT=$BACKUP_DIR/$(date +%Y-%m-%dT%H-%M-%S -d "now").sql.gz
fi

# store
mkdir -p $(dirname $PSQL_OUT)
echo "pg_dump to $PSQL_OUT..."
pg_dump -p $($DIR/pg_port.sh) -U $DB_USER $DB_NAME | gzip > $PSQL_OUT
echo "pg_dump... done."

# update dumpfile
echo "updating dumpfile ($PSQL_DUMP_FILE)..."
mkdir -p $(dirname $PSQL_DUMP_FILE)
cp -f $PSQL_OUT $PSQL_DUMP_FILE

echo "updating dumpfile... done."
