#!/bin/bash
#
# This is my best attempt at uninstalling everything that the webserver sets
# up.  It's a big system, so it's likely that I forgot something.
#

DIR="$( builtin cd "$( dirname "$( readlink -f "${BASH_SOURCE[0]}" )" )" && pwd )"
source $DIR/load_config.sh
cd $REPO_DIR

echo ""
echo "This optionally backs up the database, deletes the database from disk, "
echo "shuts down the webserver, and deletes the webserver config."
echo ""
read -r -p "Are you sure? [y/N] " response

response=${response,,}    # tolower
if [[ $response =~ ^(y)$ ]]; then

	echo ""
	read -r -p "Back up database? [Y/n] " response
	if [[ $response =~ ^(n)$ ]]; then
		echo "Not backing up"
	else
		echo "Backing up database..."
		bash "$DIR/dump_database.sh"
	fi

	echo "Remove customization of memcached..."
	sed -r 's|^-m .*$|-m 64|g' /etc/memcached.conf | \
		sed -r 's|^-I .*$|-I 1M|g' \
		> _tmp.conf
	sudo mv -f _tmp.conf /etc/memcached.conf

	echo "Delete gunicorn/nginx/logrotate config..."
	bash "$DIR/make_private.sh"
	sudo rm -f /etc/nginx/sites-available/$PROJECT_NAME

	echo "Delete copies of static files..."
	sudo rm -rf $DATA_DIR/static

	echo "Delete opt and virtualenv..."
	sudo rm -rf \
		$REPO_DIR/opt \
		$VENV_DIR

	echo "Drop postgres database cluster..."
	sudo -u postgres pg_dropcluster --stop $PSQL_VERSION $DB_CLUSTER

	echo "$0: done"
	echo "-----------------------------------------------------------------"
	echo ""
	echo "Note: Ubuntu packages installed for this project were not removed"
	echo "You can see what was installed in:"
	echo "    $REPO_DIR/scripts/install/requirements-ubuntu.txt"
	echo ""
	echo "The following directories were also not deleted:"
	echo "(just in case you want the data)"
	echo "    $DATA_DIR/media     (local images/files saved by webserver)"
	echo "    $BACKUP_DIR         (database backups)"

else
	echo "Exiting (nothing was changed)"
	exit 1
fi
