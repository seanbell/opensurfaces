#!/bin/bash
#
# Marks the site as changed and flushes the cache to display the newest version.
#
# You should call this after every time you change files and want to visit the
# site.
#

# pass the username as the first argument (useful if using sudo)
LOCAL_USER=$USER
if [ $# -ge 1 ]; then
	LOCAL_USER=$1
fi

# Load config
DIR="$( builtin cd "$( dirname "$( readlink -f "${BASH_SOURCE[0]}" )" )" && pwd )"
source "$DIR/load_config.sh"

echo ""
echo "$0: mark site as changed"
sudo touch "$SRC_DIR/config/wsgi.py"

echo ""
echo "$0: update static files"
bash "$DIR/collect_static.sh"

# only necessary when offline compression is enabled
if grep -E '^\s*COMPRESS_OFFLINE\s*=\s*True' "$SRC_DIR/config/settings_local.py"; then
	echo ""
	echo "$0: update compressor offline files"
	sudo -u $SERVER_USER bash -c "builtin cd $SRC_DIR; ./manage.py compress"
fi

# if a file is deleted but still referenced in Python code, we want to generate
# an error, not use the .pyc version.
echo ""
echo "$0: clear cached python files"
sudo find . -type f -name '*.pyc' -exec rm {} \;

# commenting out since the data directory can get big and this takes ages.
#echo ""
#echo "$0: fix permissions"
#$DIR/fix_permissions.sh $LOCAL_USER

echo ""
if [[ -f /etc/supervisor/conf.d/$PROJECT_NAME.conf ]]; then
	echo "$0: gracefully restart gunicorn"
	sudo supervisorctl pid $PROJECT_NAME | sudo xargs kill -HUP
	sudo supervisorctl start $PROJECT_NAME
else
	echo "$0: gunicorn not set up yet, skipping"
fi

echo ""
echo "$0: flush cache"
bash "$DIR/flush_memcached.sh"

echo "$0: rebuild docs"
bash "$DIR/build_docs.sh"

echo ""
echo "$0: done"
