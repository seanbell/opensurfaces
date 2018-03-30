#!/bin/bash
#
# Set up SSL cert
#

# find the scripts directory (note the /..)
DIR="$( builtin cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
source $DIR/load_config.sh
cd "$REPO_DIR"

echo ""
echo "Acquiring an SSL certificate with certbot"
wget https://dl.eff.org/certbot-auto -O opt/certbot-auto
cd opt
chmod a+x certbot-auto
sudo ./certbot-auto --nginx
cd "$REPO_DIR"
CMD="echo 0 0,12 \* \* \* root "$REPO_DIR"/opt/certbot-auto renew > /etc/cron.d/certbot"
sudo sh -c "$CMD"

echo "$0: done"
