#!/bin/bash
#
# Sets up the public nginx/gunicorn server, if not configured
#
# This does the opposite of make_private.sh.
#

# Load config
DIR="$( builtin cd "$( dirname "$( readlink -f "${BASH_SOURCE[0]}" )" )" && pwd )"
source "$DIR/load_config.sh"

##
# static files

bash "$DIR/collect_static.sh"

##
# run/ directory

echo "Preparing run/ directory..."
sudo mkdir -p $REPO_DIR/run
sudo chown -R $SERVER_USER:$SERVER_GROUP $REPO_DIR/run
for f in gunicorn nginx-access nginx-error; do
	sudo -u $SERVER_USER touch $REPO_DIR/run/$f.log
done

##
# gunicorn

if [[ ! -f /etc/supervisor/conf.d/$PROJECT_NAME.conf ]]; then
	echo "Setting up gunicorn..."

	# fill in the config file
	sed -e "s|REPO_DIR|$REPO_DIR|g" \
		-e "s|SRC_DIR|$SRC_DIR|g" \
		-e "s|SERVER_USER|$SERVER_USER|g" \
		-e "s|SERVER_GROUP|$SERVER_GROUP|g" \
		-e "s|PROJECT_NAME|$PROJECT_NAME|g" \
		$SRC_DIR/config/supervisor_template.conf \
		> $REPO_DIR/_tmp.conf

	sudo mv $REPO_DIR/_tmp.conf \
		/etc/supervisor/conf.d/$PROJECT_NAME.conf

	sudo supervisorctl reread
	sudo supervisorctl update
else
	echo "gunicorn already set up"
fi
sudo supervisorctl start $PROJECT_NAME

##
# logrotate

if [[ ! -f /etc/logrotate.d/nginx-$PROJECT_NAME ]]; then
	echo "Setting up logrotate..."

	sed -e "s|REPO_DIR|$REPO_DIR|g" \
		-e "s|SERVER_USER|$SERVER_USER|g" \
		-e "s|SERVER_GROUP|$SERVER_GROUP|g" \
		$SRC_DIR/config/logrotate_template.conf \
		> $REPO_DIR/_tmp.conf

	sudo mv $REPO_DIR/_tmp.conf \
		/etc/logrotate.d/nginx-$PROJECT_NAME
fi

##
# nginx

if [[ ! -f /etc/nginx/sites-available/$PROJECT_NAME ]]; then
	echo "Setting up nginx..."

	# fill in the template config file
	sed -e "s|PROJECT_NAME|$PROJECT_NAME|g" \
		-e "s|REPO_DIR|$REPO_DIR|g" \
		-e "s|SRC_DIR|$SRC_DIR|g" \
		-e "s|DATA_DIR|$DATA_DIR|g" \
		-e "s|ADMIN_EMAIL|$ADMIN_EMAIL|g" \
		-e "s|SERVER_NAME|$SERVER_NAME|g" \
		-e "s|SERVER_USER|$SERVER_USER|g" \
		-e "s|SERVER_GROUP|$SERVER_GROUP|g" \
		$SRC_DIR/config/nginx_template.conf \
		> $REPO_DIR/_tmp.conf

	sudo mv $REPO_DIR/_tmp.conf \
		/etc/nginx/sites-available/$PROJECT_NAME

	# disable the default nginx site
	sudo rm -f /etc/nginx/sites-enabled/default
fi

if [[ ! -f /etc/nginx/sites-enabled/$PROJECT_NAME ]]; then
	echo "Enabling nginx site..."

	# activate our site
	sudo ln -f -s \
		/etc/nginx/sites-available/$PROJECT_NAME \
		/etc/nginx/sites-enabled/$PROJECT_NAME
else
	echo "nginx already set up"
fi

sudo service nginx restart
