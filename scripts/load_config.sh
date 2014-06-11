## (To be sourced by other scripts)
##
## Load configuration info stored in
##    $REPO_DIR/config/config.sh
##

if [[ -z "$BASH" ]]; then
	print "Error: this script expects to be sourced from the BASH shell"
	return
fi

function assert_no_space {
	if [[ "$1" != "${1/ /}" ]]; then
		echo "$2"
		exit 1
	fi
}

DIR="$( builtin cd "$( dirname "$( readlink -f "${BASH_SOURCE[0]}" )" )" && pwd )"
assert_no_space "$DIR" "Please move the repository to a path without spaces"

if [[ ! -s $DIR/config.sh ]]; then
	echo "$0: Configuration not yet set up ($DIR/config.sh)."
	echo "$0: Running $DIR/create_config.py"
	echo ""
	$DIR/create_config.py
	if [[ ! -s $DIR/config.sh ]]; then
		print "Error: configuration file ($DIR/config.sh) was not created"
		return
	fi
fi
source $DIR/config.sh

# make sure some fields are filled in properly

if [[ -z "$PROJECT_NAME" ]]; then
	echo "Please add a project name to $DIR/config.sh"
	echo "    PROJECT_NAME=$PROJECT_NAME"
	exit 1
fi

if [[ ! "$PROJECT_NAME" =~ ^[a-z][a-z0-9_]*$ ]]; then
	echo "The project name in $DIR/config.sh is not valid. It must contain only"
	echo "lowercase letters, digits, and underscores, and the first character must"
	echo "be a lowercase letter."
	echo "    PROJECT_NAME=$PROJECT_NAME"
	exit 1
fi

if [[ -z "$REPO_DIR" ]]; then
	echo "Please add the repository root directory to $DIR/config.sh"
	echo "    REPO_DIR=$REPO_DIR"
	exit 1
fi

if [[ -z "$BACKUP_DIR" ]] || [[ -z "$DATA_DIR" ]] || [[ -z "$SRC_DIR" ]] || [[ -z "$VENV_DIR" ]]; then
	echo "Please configure directories in $DIR/config.sh"
	echo "    BACKUP_DIR=$BACKUP_DIR"
	echo "    DATA_DIR=$DATA_DIR"
	echo "    VENV_DIR=$VENV_DIR"
	echo "    SRC_DIR=$SRC_DIR"
	exit 1
fi

if [[ "$BACKUP_DIR" != /* ]] || [[ "$DATA_DIR" != /* ]] || [[ "$SRC_DIR" != /* ]] || [[ "$VENV_DIR" != /* ]]; then
	echo "Please configure directories in $DIR/config.sh -- they must be absolute paths (note that they can be constructed from variables that are absolute paths, such as REPO_DIR)"
	echo "    BACKUP_DIR=$BACKUP_DIR"
	echo "    DATA_DIR=$DATA_DIR"
	echo "    VENV_DIR=$VENV_DIR"
	echo "    SRC_DIR=$SRC_DIR"
	exit 1
fi

if [[ "$VENV_DIR" != "$REPO_DIR/venv" ]]; then
	echo "Error: VENV_DIR (in $DIR/config) should be"
	echo "    VENV_DIR=\$REPO_DIR/venv"
	echo "Currently, it is:"
	echo "    VENV_DIR=$VENV_DIR"
	exit 1
fi

if [[ -z "$SERVER_NAME" ]] || [[ -z "$SERVER_IP" ]]; then
	echo "Please configure server info in $DIR/config.sh"
	echo "    SERVER_NAME=$SERVER_NAME"
	echo "    SERVER_IP=$SERVER_IP"
	exit 1
fi

if [[ ! "$SERVER_NAME" =~ ^(([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9\-]*[A-Za-z0-9])$ ]]; then
	echo "The server name is in $DIR/config.sh is not a valid hostname"
	echo "    SERVER_NAME=$SERVER_NAME"
	exit 1
fi

if [[ ! "$SERVER_IP" =~ ^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$ ]]; then
	echo "The server IP address is not valid in $DIR/config.sh"
	echo "    SERVER_IP=$SERVER_IP"
fi

if [[ -z "$SERVER_USER" ]] || [[ -z "$SERVER_GROUP" ]]; then
	echo "Please configure server user/group info in $DIR/config.sh"
	echo "    SERVER_USER=$SERVER_USER"
	echo "    SERVER_GROUP=$SERVER_GROUP"
	exit 1
fi

if [[ "$SERVER_USER" == "$USER" ]] || [[ "$SERVER_USER" == "root" ]]; then
	echo "The SERVER_USER cannot match the user (USER=$USER) or root"
	echo "Please fix this in $DIR/config.sh"
	echo "    SERVER_USER=$SERVER_USER"
	echo "    SERVER_GROUP=$SERVER_GROUP"
	exit 1
fi

if [[ -z "$ADMIN_NAME" ]] || [[ -z "$ADMIN_EMAIL" ]]; then
	echo "Please configure admin info in $DIR/config.sh"
	echo "    ADMIN_NAME=$ADMIN_NAME"
	echo "    ADMIN_EMAIL=$ADMIN_EMAIL"
	exit 1
fi

if [[ -z "$PSQL_VERSION" ]] || [[ -z "$PSQL_DUMP_FILE" ]] || [[ -z "$PSQL_SHARED_BUFFERS" ]]; then
	echo "Please configure PostgreSQL info in $DIR/config.sh"
	echo "    PSQL_VERSION=$PSQL_VERSION"
	echo "    PSQL_DUMP_FILE=$PSQL_DUMP_FILE"
	echo "    PSQL_SHARED_BUFFERS=$PSQL_SHARED_BUFFERS"
	exit 1
fi

if [[ -z "$PSQL_DUMP_URL" ]]; then
	echo "Please fill in PostgreSQL 'pg_dump' URL in $DIR/config.sh"
	echo "    PSQL_DUMP_URL=$PSQL_DUMP_URL"
	exit 1
fi

if [[ -z "$DB_CLUSTER" ]] || [[ -z "$DB_NAME" ]] || [[ -z "$DB_USER" ]]; then
	echo "Please fill in database info in $DIR/config.sh"
	echo "    DB_CLUSTER=$DB_CLUSTER"
	echo "    DB_NAME=$DB_NAME"
	echo "    DB_USER=$DB_USER"
	exit 1
fi

if [[ -z "$KERNEL_SHMMAX" ]] || [[ -z "$KERNEL_SHMALL" ]]; then
	echo "Please configure kernel memory settings in $DIR/config.sh"
	echo "    KERNEL_SHMMAX=$KERNEL_SHMMAX"
	echo "    KERNEL_SHMALL=$KERNEL_SHMALL"
	exit 1
fi

if [[ -f $VENV_DIR/bin/activate ]]; then
	source $VENV_DIR/bin/activate
else
	echo "Note: virtualenv ($VENV_DIR) not yet created"
fi

echo "$0: loaded $DIR/config.sh"
