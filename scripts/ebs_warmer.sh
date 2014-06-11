#!/bin/bash
#
# This script touches every block on a disk.  When using a new EBS volume on
# Amazon EC2, this forces the system to prepare the block for use.  Otherwise,
# each block is not ready until it is accessed for the first time.  This can
# lead to slow performance.
#

if [ -z "$1" ]; then
  echo "Usage: sudo $0 /dev/sdh1"
  exit 1;
fi

dd if=$1 of=/dev/null & pid=$!
while true; do
  ps -p$pid --no-heading || break;
  echo "-- $(date) ------------------";
  kill -USR1 $pid;
  sleep 60s;
done
echo "-- $(date) ------------------";
echo "DONE \o/"
