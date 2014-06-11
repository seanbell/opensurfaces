#!/bin/bash
#
# Kills the public nginx/gunicorn server, if running.
#
# This does the opposite of make_public.sh.
#

# Load config
DIR="$( builtin cd "$( dirname "$( readlink -f "${BASH_SOURCE[0]}" )" )" && pwd )"
source "$DIR/load_config.sh"

if [[ -f /etc/nginx/sites-enabled/$PROJECT_NAME ]]; then
	echo "Disabling nginx site..."

	sudo rm -f /etc/nginx/sites-enabled/$PROJECT_NAME
	sudo service nginx restart
else
	echo "nginx already disabled"
fi

if [[ -f /etc/logrotate.d/nginx-$PROJECT_NAME ]]; then
	echo "Deleting nginx logrotate config..."

	sudo rm -f /etc/logrotate.d/nginx-$PROJECT_NAME
else
	echo "nginx logrotate already disabled"
fi

if [[ -f /etc/supervisor/conf.d/$PROJECT_NAME.conf ]]; then
	echo "Shutting down gunicorn..."

	sudo supervisorctl stop $PROJECT_NAME
	sudo supervisorctl remove $PROJECT_NAME

	sudo rm -f /etc/supervisor/conf.d/$PROJECT_NAME.conf
	sudo supervisorctl reread
	sudo supervisorctl update
else
	echo "gunicorn already disabled"
fi

sudo rm -f $REPO_DIR/run/gunicorn.sock
