#!/bin/bash
#
# Install Nodejs packages used by the server
#

# find the scripts directory (note the /..)
DIR="$( builtin cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"

source $DIR/load_config.sh
cd "$REPO_DIR"

#########################

echo "Installing node.js..."

# fix npm registry
echo "Uninstall old node"
sudo apt-get remove -y --purge nodejs npm
sudo rm -f /usr/bin/coffee /usr/local/bin/coffee
sudo rm -f /usr/bin/lessc /usr/local/bin/lessc

echo "Install node 0.10"
echo "Checking Ubuntu version: ${VERSION%%.*}"
if [[ ${VERSION%%.*} -ge 13 ]]; then
	# Ubuntu 13, 14.04
	sudo add-apt-repository -y ppa:chris-lea/node.js
	sudo apt-get update -y
	sudo apt-get install -y nodejs
	sudo npm install -g npm
else
	# Ubuntu 12.04
	sudo add-apt-repository -y ppa:richarvey/nodejs
	sudo apt-get update -y
	sudo apt-get install -y nodejs npm
	npm config set registry http://registry.npmjs.org/
fi

# fix node executable name
if [[ ! -f /usr/bin/node ]] && [[ -f /usr/bin/nodejs ]]; then
	sudo ln -s /usr/bin/nodejs /usr/bin/node
fi

echo "Install coffeescript"
sudo npm install -g 'coffee-script@1.8.0'
echo "Install less"
sudo npm install -g 'less@1.7.5'
