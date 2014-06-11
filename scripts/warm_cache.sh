#!/bin/bash
#
# Fill up the cache by visiting the outermost links of the website.
#

# Load config
DIR="$( builtin cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $DIR/load_config.sh
builtin cd "$REPO_DIR"

if [[ "$ENABLE_SSL" == "true" ]]; then
	SERVER_URL="https://$SERVER_NAME/"
else
	SERVER_URL="http://$SERVER_NAME/"
fi

# walk the outermost links of the website to fill up the cache
echo "Warming cache"
wget --no-check-certificate --spider -nd --recursive --level=2 --reject "*/static/*" --ignore-tags=img -e robots=off $SERVER_URL
echo "Done warming cache"
