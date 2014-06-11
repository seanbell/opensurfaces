#!/bin/bash
#
# Prints the number of jobs waiting in the celery queue
#

sudo rabbitmqctl list_queues | grep celery | grep -v pidbox
