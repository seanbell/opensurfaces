#!/bin/bash
# Set up Memcached

# find the scripts directory (note the /..)
DIR="$( builtin cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
source $DIR/load_config.sh
cd "$REPO_DIR"

echo "Setting up memcached..."

sed -r 's|^-m .*$|-m 256|g' /etc/memcached.conf | \
	sed -r 's|^-I .*$|-I 4M|g' \
	> tmp.conf

if [[ $(grep -c '^-I' /etc/memcached.conf) -eq 0 ]]; then
	# '-I' not yet specified
	echo "" >> tmp.conf
	echo "# Maximum file size limit" >> tmp.conf
	echo "-I 4M" >> tmp.conf
fi

sudo mv -f tmp.conf /etc/memcached.conf

echo "Restarting memcached..."
sudo service memcached restart

echo "$0: done"
