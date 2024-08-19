#/bin/bash

TIME=$1

while true; do
    DATE=$(date +%H:%M:%S)
	echo "$DATE: will sleep for $TIME seconds"
	sleep $TIME
done

