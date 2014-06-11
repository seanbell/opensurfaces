#!/usr/bin/env bash
#
# This flushes the memcached cache
#

DIR="$( builtin cd "$( dirname "$( readlink -f "${BASH_SOURCE[0]}" )" )" && pwd )"
source $DIR/load_config.sh

echo "flushing..."
echo "flush_all" | /bin/netcat -q 2 127.0.0.1 11211
echo "done."
