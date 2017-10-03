#!/bin/bash

echo "Starting Monitoring Services."
mng="python manage.py"
# Clear out previously running jobs in the default queue.
echo "Resetting the job queue, you will need to disable/enable arrays to continue monitoring."
/usr/local/bin/rq empty failed
$mng runserver 0.0.0.0:8080 -v0 &>> flasharray/flash_stache.log &
$mng rqworker default -v0 &>> flasharray/flash_stache.log &
$mng rqscheduler -v0 --interval 1 &>> flasharray/flash_stache.log &
