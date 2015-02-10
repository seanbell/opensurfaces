#!/bin/bash
# Completely clears the database of all tables and records.  You will have to
# run migrate_database.sh after this (or import initial data).

DIR="$( builtin cd "$( dirname "$( readlink -f "${BASH_SOURCE[0]}" )" )" && pwd )"
source $DIR/load_config.sh


echo "This completely destroys all data and tables in the database."
echo "You need to either import data or run scripts/migrate_database.sh to"
echo "create tables."
read -r -p "Are you sure? [y/N] " response
response=${response,,}    # tolower
if [[ $response =~ ^(yes|y)$ ]]; then
	set -x -e
	DB_PORT=$($DIR/pg_port.sh)
	dropdb -p $DB_PORT $DB_NAME
	createdb -p $DB_PORT --owner=$DB_USER --encoding=UTF8 $DB_NAME
fi
