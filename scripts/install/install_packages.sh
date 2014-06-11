#!/bin/bash
#
# Install all the packages used by the server
#

# find the scripts directory (note the /..)
DIR="$( builtin cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"

source $DIR/load_config.sh
cd "$REPO_DIR"

#########################

echo "Installing Ubuntu packages..."

# increase sudo timeout
sudo -v

# install ubuntu packages
sudo apt-get update -y
sudo apt-get install -y $(cat $DIR/install/requirements-ubuntu.txt)

sudo apt-get install -y \
	postgresql-$PSQL_VERSION \
	postgresql-contrib-$PSQL_VERSION \
	postgresql-server-dev-$PSQL_VERSION

# install dependencies for numpy/scipy
sudo apt-get build-dep -y python-numpy python-scipy

# make sure the image libraries are in /usr/lib
[[ -f /usr/lib/libfreetype.so ]] || sudo ln -s /usr/lib/`uname -i`-linux-gnu/libfreetype.so /usr/lib/
[[ -f /usr/lib/libjpeg.so ]] || sudo ln -s /usr/lib/`uname -i`-linux-gnu/libjpeg.so /usr/lib/
[[ -f /usr/lib/libz.so ]] || sudo ln -s /usr/lib/`uname -i`-linux-gnu/libz.so /usr/lib/
[[ -f /usr/lib/liblcms.so ]] || sudo ln -s /usr/lib/`uname -i`-linux-gnu/liblcms.so /usr/lib/

#########################

echo "Installing node.js..."

# fix npm registry
echo "Uninstall old node"
sudo apt-get remove -y nodejs npm
sudo rm -f /usr/bin/coffee /usr/local/bin/coffee
sudo rm -f /usr/bin/lessc /usr/local/bin/lessc

echo "Install newest node"
#sudo add-apt-repository ppa:chris-lea/node.js
sudo add-apt-repository -y ppa:richarvey/nodejs
sudo apt-get update -y
sudo apt-get install -y nodejs npm
echo "Node version:"
node -v

npm config set registry http://registry.npmjs.org/
echo "Install coffeescript"
sudo npm install -g coffee-script
echo "Install less"
sudo npm install -g less

#########################

echo "$0: done"
