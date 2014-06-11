#!/bin/bash
#
# Creates a new Django app.  Note that this command can be run on top of
# existing apps to create any potentially missing directories.
#

DIR="$( builtin cd "$( dirname "$( readlink -f "${BASH_SOURCE[0]}" )" )" && pwd )"
source $DIR/load_config.sh

if [ $# -lt 1 ]; then
	echo "Usage: $0 <app_name>"
	exit 1
fi

builtin cd $SRC_DIR
if [ ! -d $1 ]; then
	./manage.py startapp $1
else
	echo "App $1 already exists"
fi

# set up the directory for management commands
mkdir -p $1/management/commands
touch $1/management/__init__.py
touch $1/management/commands/__init__.py
ln -sf management/commands $1/cmd

# set up templates
mkdir -p $1/templates/$1

# set up static directories and convenience shortucts
for f in js css img; do
	mkdir -p $1/static/$f/$1
	ln -sf static/$f/$1 $1/$f
done

# create defaults
if [ ! -s $1/tasks.py ]; then
	echo "# Write your celery tasks here" >> $1/tasks.py
fi

if [ ! -s $1/urls.py ]; then
	echo "# Register your URLs here" >> $1/urls.py
fi

echo ""
echo "$1: created!"
echo ""
echo "Make sure to add '$1' to INSTALLED_APPS in server/config/settings.py"
