#!/bin/bash
#
# This script completely sets up the OpenSurfaces database and server
#
# Usage: ./install_all.sh
#

# load configuration info
set -e
DIR="$( builtin cd "$( dirname "$( readlink -f "${BASH_SOURCE[0]}" )" )/.." && pwd )"
source "$DIR/load_config.sh"

# make sure everything is set up
source "$DIR/install/check_setup.sh"

# print debug info
set -x

# install each component
source "$DIR/install/install_packages.sh"
source "$DIR/install/install_python.sh"
source "$DIR/install/install_dirs.sh"
source "$DIR/install/install_postgres.sh"
source "$DIR/install/install_memcached.sh"
source "$DIR/install/install_nginx.sh"

# add superuser
echo ""
echo "===================================================================="
echo "Now creating a superuser.  Use this account to log into the website."
builtin cd "$SRC_DIR"
set +e
./manage.py createsuperuser
set -e

# build sphinx documentation in docs/
builtin cd "$REPO_DIR/docs"
sudo make clean
source "$DIR/build_docs.sh"

# visit main pages for a faster first load
bash "$DIR/warm_cache.sh"

set +e
set +x

# exit message
echo "$0: done!"
echo ""
echo "===================================================================="

url="http://$SERVER_NAME/"
echo ""
echo "You should be able to visit the site at:"
echo "    $url"

if [[ "$SERVER_NAME" != "localhost" ]]; then
	echo "(assuming that you set up the DNS for $SERVER_NAME to point"
	echo "to this machine)."
fi

# try to open website in a browser
if command -v google-chrome >/dev/null 2>&1; then
	echo "Visiting $url with chrome ..."
	google-chrome "$url" &
elif command -v xdg-open >/dev/null 2>&1; then
	echo "Visiting $url with default browser ..."
	xdg-open "$url" &
fi
