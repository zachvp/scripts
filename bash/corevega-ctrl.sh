#/bin/bash

COREVEGA_FUNCTION=$1
COREVEGA_IP_ETHERNET="192.168.2.2"
COREVEGA_RSYNC_PORT=12000
COREVEGA_PATH_HOME=/home/zachvp
COREVEGA_PATH_RSYNC_PID="$COREVEGA_PATH_HOME/developer/state/rsync/rsyncd.pid"

## UTIL
cv_echo()
{
	PREFIX="corevega"
	echo "$PREFIX: $1"
}

## SERVER
ps_rsync_daemon()
{
	if [ -e "$COREVEGA_PATH_RSYNC_PID" ]; then
		cv_echo "daemon PID: $(cat $COREVEGA_PATH_RSYNC_PID)"
		ps aux | grep $(cat $COREVEGA_PATH_RSYNC_PID) | grep -v 'grep'
	else
		cv_echo "daemon is not running"
	fi
}

## run rsync daemon
start_rsync_daemon()
{
    COREVEGA_DAEMON_CONFIG_FILE=$COREVEGA_PATH_HOME/.config/rsync/default.conf
	cv_echo "function requires sudo access, continue? [y/N]"
	read CONTINUE
	if [ $CONTINUE == "y" ]; then
    	sudo rsync --daemon --config $COREVEGA_DAEMON_CONFIG_FILE -v
		ps_rsync_daemon
	else
		cv_echo "user declined to continue"
	fi
}

stop_rsync_daemon()
{
	if [ -e "$COREVEGA_PATH_RSYNC_PID" ]; then
		sudo kill "$(cat $COREVEGA_PATH_RSYNC_PID)"
	else
		cv_echo "rsync daemon not running, nothing to do"
	fi
}


## run container on host port 8000
run_docker_media_music_stream()
{
    cv_echo "running subsonic_corevega"
    docker run -dti \
        --publish 8000:4040 \
        --name="subsonic_corevega" \
        --hostname corevega-music \
        --network corevega-net \
        --dns 192.168.1.1 \
        -v /media/zachvp/SOL/transfer-rsync/daemon/transfer:/var/music \
        -v /home/zachvp/developer/state/subsonic:/var/subsonic \
        hydria/subsonic:latest
}

# ===

## CLIENT 
### run rsync
#### Preferred: direct ethernet+ssh+daemon transfer
run_rsync_transfer_daemon()
{
    COREVEGA_MUSIC_MEDIA_SOURCE=$2
    COREVEGA_TRANSFER_DEST="rsync://zachvp@$COREVEGA_IP_ETHERNET:$COREVEGA_RSYNC_PORT/music"

    echo "transfer source: $COREVEGA_MUSIC_MEDIA_SOURCE"
    echo "transfer destination: $COREVEGA_TRANSFER_DEST"
	time rsync $COREVEGA_MUSIC_MEDIA_SOURCE $COREVEGA_TRANSFER_DEST \
        --progress -rtvzi --exclude ".*"
}

#### Simple setup: direct ethernet+ssh transfer
run_rsync_transfer()
{
    COREVEGA_MUSIC_MEDIA_SOURCE=$2
	time rsync $COREVEGA_MUSIC_MEDIA_SOURCE zachvp@$COREVEGA_IP_ETHERNET:/media/zachvp/SOL/transfer-rsync/rsync_default \
        --progress -rtvzi --exclude ".*"
}

# MAIN
# run the function argument
cv_echo "$COREVEGA_FUNCTION"
$COREVEGA_FUNCTION

