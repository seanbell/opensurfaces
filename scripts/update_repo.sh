#!/bin/bash
#
# Watches the $BARE_REPO_DIR and keeps the repository synchronized to that
#

# Make sure bare repo exists
if [ ! -d $REPO_BARE_DIR ]; then
	echo "Error: bare repository \"$REPO_BARE_DIR\" does not exist"
fi

# Run script as root
if [ ! $( id -u ) -eq 0 ]; then
    exec sudo bash $0 $USER
    exit $?
elif [ $# -ge 1 ]; then
	LOCAL_USER=$1
	echo "Running as $USER, delegating to $LOCAL_USER"
else
	LOCAL_USER=$USER
	echo "Running as $USER"
fi

# Load config
DIR="$( builtin cd "$( dirname "$( readlink -f "${BASH_SOURCE[0]}" )" )" && pwd )"
source $DIR/load_config.sh

# Update repo and force an update
function update() {
	sudo -u $LOCAL_USER git pull

	# clean docs
	p="$(pwd)"
	builtin cd "$REPO_DIR/docs"
	sudo make clean
	cd "$p"

	# mark site as changed
	$DIR/files_changed.sh $LOCAL_USER
}

# update loop
while inotifywait $REPO_BARE_DIR; do
	sleep 2
	update
	while sudo -u $LOCAL_USER git pull | grep -q -v 'Already up-to-date.'; do
		update
	done
	date
done
