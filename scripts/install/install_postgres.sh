#!/bin/bash
#
# This script configures PostgreSQL, generates passwords,
# and stores the generated database info into
# $REPO_DIR/server/config/settings.py

## Load configuration

# find the scripts directory (note the /..)
DIR="$( builtin cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
source $DIR/load_config.sh
cd "$REPO_DIR"

echo "Setting up PostgreSQL ($PSQL_VERSION)..."

## Generate random passwords

DB_PASS=$(< /dev/urandom tr -dc A-Z-a-z-0-9 | head -c16)
USER_PSQL_PASS=$(< /dev/urandom tr -dc A-Z-a-z-0-9 | head -c16)
SECRET_KEY=$(< /dev/urandom tr -dc A-Z-a-z-0-9 | head -c64)

# increase OS shared memory
sudo sed -e "/^# Patched by labelmaterial installer:/d" \
		 -e "/^kernel.shmall/d" \
         -e "/^kernel.shmmax/d" \
		 /etc/sysctl.conf > tmp.conf
sudo mv tmp.conf /etc/sysctl.conf
echo "# Patched by labelmaterial installer:" >> /etc/sysctl.conf
echo "kernel.shmall = $KERNEL_SHMALL" >> /etc/sysctl.conf
echo "kernel.shmmax = $KERNEL_SHMMAX" >> /etc/sysctl.conf

# apply new settings to kernel
sudo sysctl -p

# set up new cluster if it's not already there
if [ "$(sudo pg_lsclusters | grep $PSQL_VERSION | grep -c $DB_CLUSTER)" -lt "1" ]; then
	if [[ -z "$DB_DIR" ]]; then
		# default directory
		sudo pg_createcluster $PSQL_VERSION $DB_CLUSTER
	else
		# custom directory
		sudo mkdir -p $DB_DIR
		sudo chown postgres:postgres $DB_DIR
		sudo pg_createcluster -d $DB_DIR $PSQL_VERSION $DB_CLUSTER
	fi
fi

# start if not already started
set +e
sudo pg_ctlcluster $PSQL_VERSION $DB_CLUSTER start
set -e

# find port
DB_PORT=$(sudo pg_lsclusters | grep $PSQL_VERSION | grep $DB_CLUSTER | awk '{print $3}')
if [[ -z "$DB_PORT" ]]; then
	sudo pg_lsclusters
	echo "Error: cannot find PostgreSQL port"
else
	echo "PostgreSQL running on port $DB_PORT"
fi

# find config
POSTGRESQL_CONF=/etc/postgresql/$PSQL_VERSION/$DB_CLUSTER/postgresql.conf
if [[ ! -s "$POSTGRESQL_CONF" ]]; then
	echo "Error: cannot find PostgreSQL config file: \"$POSTGRESQL_CONF\""
	exit 1
fi

# comment out old configuration
sudo sed -r "s/^(\s*client_encoding\s*=.*)$/#\1/" $POSTGRESQL_CONF | \
	sudo sed -r "s/^#+\s*client_encoding\s*=\s*'UTF8'\s*$//" | \
	sudo sed -r "s/^(\s*default_transaction_isolation\s*=.*)$/#\1/" | \
	sudo sed -r "s/^#+\s*default_transaction_isolation\s*=\s*'read committed'\s*$//" | \
	sudo sed -r "s/^(\s*timezone\s*=.*)$/#\1/" | \
	sudo sed -r "s/^#+\s*timezone\s*=\s*'UTC'\s*$//" | \
	sudo sed -r "s/^# config for $PROJECT_NAME:$//" | \
	sudo sed -r '/^$/N;/\n$/D' \
> tmp.conf

# add django configuration
echo "# config for $PROJECT_NAME:" >> tmp.conf
echo "client_encoding = 'UTF8'" >> tmp.conf
echo "default_transaction_isolation = 'read committed'" >> tmp.conf
echo "timezone = 'UTC'" >> tmp.conf
sudo mv -f tmp.conf $POSTGRESQL_CONF

# increase memory from the small default of 24MB
sudo sed -r "s/^shared_buffers\s+=.*/shared_buffers = $PSQL_SHARED_BUFFERS/" $POSTGRESQL_CONF > tmp.conf
sudo mv -f tmp.conf $POSTGRESQL_CONF
sudo grep shared_buffers $POSTGRESQL_CONF

# restart postgres with updated shared_buffers
if sudo service postgresql restart; then
	echo "success"
else
	echo "Could not restart the database server.  To fix this, you can try:"
	echo "Edit the config file:"
	echo "    $DIR/config.sh"
	echo "and decrease the value of PSQL_SHARED_BUFFERS ($PSQL_SHARED_BUFFERS)."
	echo "Re-run the installer to try again."
	exit 1
fi

# setup pgpass password file
rm -f ~/.pgpass
echo "*:*:$DB_NAME:$DB_USER:$DB_PASS" >> ~/.pgpass
echo "*:*:*:$USER:$USER_PSQL_PASS" >> ~/.pgpass
chmod 600 ~/.pgpass

# create $USER as a superuser if it does not exist
echo "Creating a PostgreSQL superuser to match your username ($USER)."
echo "CREATE USER \"$USER\" WITH SUPERUSER LOGIN PASSWORD '$USER_PSQL_PASS'" | sudo -u postgres psql -p $DB_PORT
echo "ALTER USER \"$USER\" WITH SUPERUSER LOGIN PASSWORD '$USER_PSQL_PASS'" | sudo -u postgres psql -p $DB_PORT
set +e # this will complain if run a second time, so ignore the error
createdb -p $DB_PORT $USER --encoding=UTF8
set -e

# create project user if it does not exist
echo "CREATE USER \"$DB_USER\" WITH LOGIN PASSWORD '$DB_PASS'" | psql -p $DB_PORT
echo "ALTER USER \"$DB_USER\" WITH LOGIN PASSWORD '$DB_PASS'" | psql -p $DB_PORT

# create database
echo "Destroying any existing database with name '$DB_NAME'"
set +e # this will complain if run a second time, so ignore the error
dropdb -p $DB_PORT $DB_NAME
set -e
createdb -p $DB_PORT --owner=$DB_USER --encoding=UTF8 $DB_NAME

# set up hba conf
HBA_CONF=$(sudo ls -1 /etc/postgresql/$PSQL_VERSION/$DB_CLUSTER/pg_hba.conf | tail -n 1)
if [[ ! -s "$HBA_CONF" ]]; then
	echo "Error: cannot find PostgreSQL config file: \"$HBA_CONF\""
	exit 1
fi

if [[ $(sudo grep -cE "local\s+$DB_NAME\s+$DB_USER\s+md5" $HBA_CONF) -eq 0 ]]; then
	sudo bash -c "echo '' >> $HBA_CONF"
	sudo bash -c "echo 'local    $DB_NAME    $DB_USER    md5' >> $HBA_CONF"
fi

# correct 'all' permissions in hbaconf
if [[ $(sudo grep -cE 'local\s+all\s+all\s+peer' $HBA_CONF) -eq 1 ]]; then
	sudo sed -r 's/local\s+all\s+all\s+peer/local    all    all    md5/' $HBA_CONF > tmp.conf
	sudo mv -f tmp.conf $HBA_CONF
fi

# show resulting conf file
sudo tail $HBA_CONF

# restart postgres with new settings
sudo service postgresql restart

# load initial database data
echo "Loading initial data..."
if [[ ! -s "$PSQL_DUMP_FILE" ]]; then
	echo "Downloading data: $PSQL_DUMP_URL --> $PSQL_DUMP_FILE..."
	wget $PSQL_DUMP_URL -O "$PSQL_DUMP_FILE"
fi

if [[ -s "$PSQL_DUMP_FILE" ]]; then
	gunzip -c "$PSQL_DUMP_FILE" | psql -p $DB_PORT $DB_NAME $DB_USER
else
	echo "Note: could not find pg_dump file \"$PSQL_DUMP_FILE\""
fi


##
## Fill in settings
##

echo "Filling in Django settings..."

# Set up settings_local.py
sed -e "s|'ADMIN_NAME'|'$ADMIN_NAME'|g" \
	-e "s|'ADMIN_EMAIL'|'$ADMIN_EMAIL'|g" \
	-e "s|'DB_NAME'|'$DB_NAME'|g" \
	-e "s|'DB_USER'|'$DB_USER'|g" \
	-e "s|'DB_PASS'|'$DB_PASS'|g" \
	-e "s|'DB_PORT'|'$DB_PORT'|g" \
	-e "s|'SRC_DIR'|'$SRC_DIR'|g" \
	-e "s|'DATA_DIR'|'$DATA_DIR'|g" \
	-e "s|'PROJECT_NAME'|'$PROJECT_NAME'|g" \
	-e "s|'SERVER_NAME'|'$SERVER_NAME'|g" \
	-e "s|'SERVER_IP'|'$SERVER_IP'|g" \
	-e "s|'TIME_ZONE'|'$TIME_ZONE'|g" \
	-e "s|'SECRET_KEY'|'$SECRET_KEY'|g" \
	$SRC_DIR/config/settings_local_template.py > \
	$SRC_DIR/config/settings_local.py


# (this has to be after settings_local.py is set up)
echo "Running migrations..."
bash "$DIR/migrate_database.sh"

echo "Setting up database cache..."
set +e
$VENV_DIR/bin/python $SRC_DIR/manage.py createcachetable db-cache
set -e

echo "$0: done"
