#/bin/bash

COREVEGA_FUNCTION=$1
COREVEGA_IP_ETHERNET="192.168.2.2"
COREVEGA_RSYNC_PORT=12000
COREVEGA_HOME=/home/zachvp

## server: run rsync daemon
run_rsync_daemon()
{
    COREVEGA_DAEMON_CONFIG_FILE=$COREVEGA_HOME/.config/rsync/default.conf
	echo "function requires sudo access, continue? [y/N]"
	read CONTINUE
	if [ $CONTINUE == "y" ]; then
    	sudo rsync --daemon --config $COREVEGA_DAEMON_CONFIG_FILE -v

		COREVEGA_RSYNC_PID=`cat $COREVEGA_HOME/developer/state/rsync/rsyncd.pid`
		echo "daemon running, PID: $COREVEGA_RSYNC_PID"
		ps aux | grep 'rsync -v --daemon'
	else
		echo "user declined to continue"
	fi
}

## client: run rsync

### Preferred: direct ethernet+ssh+daemon transfer
run_rsync_transfer_daemon()
{
    COREVEGA_MUSIC_MEDIA_SOURCE=$2
    COREVEGA_TRANSFER_DEST="rsync://zachvp@$COREVEGA_IP_ETHERNET:$COREVEGA_RSYNC_PORT/music"

    echo "transfer source: $COREVEGA_MUSIC_MEDIA_SOURCE"
    echo "transfer destination: $COREVEGA_TRANSFER_DEST"
	time rsync $COREVEGA_MUSIC_MEDIA_SOURCE $COREVEGA_TRANSFER_DEST \
        --progress -rtvzi --exclude ".*"
}

### Simple setup: direct ethernet+ssh transfer
run_rsync_transfer()
{
    COREVEGA_MUSIC_MEDIA_SOURCE=$2
	time rsync $COREVEGA_MUSIC_MEDIA_SOURCE zachvp@$COREVEGA_IP_ETHERNET:/media/zachvp/SOL/transfer-rsync/rsync_default \
        --progress -rtvzi --exclude ".*"
}

## run container on host port 8000
run_docker_media_music_stream()
{
    echo "running subsonic_corevega"
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

# run the function argument
echo "running: $COREVEGA_FUNCTION"
$COREVEGA_FUNCTION

