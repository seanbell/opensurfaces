#!/bin/bash
#
# Destroy all existing data and replace it with the most recent backup.
#

DIR="$( builtin cd "$( dirname "$( readlink -f "${BASH_SOURCE[0]}" )" )" && pwd )"
source $DIR/load_config.sh

if [[ $# -ge 1 ]]; then
	PSQL_DUMP_FILE=$1
fi

if [[ ! -s $PSQL_DUMP_FILE ]]; then
	echo "Error: dumpfile '$PSQL_DUMP_FILE' does not exist"
	exit 1
fi

# load in new data
echo ""
echo "====================== NOTE =========================="
echo "This restarts the database server, completely destroys"
echo "all data in the database, and replaces all data with"
echo "the backup file:"
echo "    $PSQL_DUMP_FILE"
echo "The website and all workers should be turned off."
echo ""
echo "         >> THIS OPERATION CANNOT BE UNDONE <<"
echo "====================== NOTE =========================="
echo ""
read -r -p "Are you sure? [y/N] " response
response=${response,,}    # tolower
if [[ $response =~ ^(y)$ ]]; then
	set -x -e
	DB_PORT=$($DIR/pg_port.sh)

	# force-quit all existing sessions
	sudo /etc/init.d/postgresql restart

	# kill database and create it from scratch again
	dropdb -p $DB_PORT $DB_NAME
	createdb -p $DB_PORT --owner=$DB_USER --encoding=UTF8 $DB_NAME
	gunzip -c $PSQL_DUMP_FILE | psql -p $DB_PORT $DB_NAME $DB_USER

	$DIR/migrate_database.sh
	$DIR/flush_memcached.sh
else
	echo "Exiting (nothing was changed)"
	exit 1
fi
