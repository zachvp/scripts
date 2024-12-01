#!/bin/bash

COREVEGA_IP="192.168.50.84"
COREVEGA_PATH_HOME="/home/zachvp"

COREVEGA_USER="zachvp"
COREVEGA_RSYNC_PORT=12000
COREVEGA_RSYNC_OPTIONS="--progress -auvzi"
COREVEGA_PATH_RSYNC_PID="$COREVEGA_PATH_HOME/developer/state/rsync/rsyncd.pid"

# set +x

## UTIL
cv_echo()
{
	echo "corevega: $1"
}

cv_check_continue()
{
    cv_echo "continue [y/N]?"
    read COREVEGA_CONTINUE
    if [ "$COREVEGA_CONTINUE" != "y" ]; then
        cv_echo "exiting"
        exit 2
    fi
}

## SERVER
ps_rsyncd()
{
	if [ -e "$COREVEGA_PATH_RSYNC_PID" ]; then
		cv_echo "daemon PID: $(cat $COREVEGA_PATH_RSYNC_PID)"
		ps aux | grep $(cat $COREVEGA_PATH_RSYNC_PID) | grep -v 'grep'
	else
		cv_echo "daemon is not running"
	fi
}

## run rsync daemon
start_rsyncd()
{
    COREVEGA_DAEMON_CONFIG_FILE=$COREVEGA_PATH_HOME/.config/rsync/default.conf
	cv_echo "function requires sudo access, continue? [y/N]"
	read COREVEGA_CONTINUE
	if [ $COREVEGA_CONTINUE == "y" ]; then
    	sudo rsync --daemon --config $COREVEGA_DAEMON_CONFIG_FILE -v
		cv_echo "started daemon with config $COREVEGA_DAEMON_CONFIG_FILE"
	else
		cv_echo "user declined to continue"
	fi
}

stop_rsyncd()
{
	if [ -e "$COREVEGA_PATH_RSYNC_PID" ]; then
		sudo kill "$(cat $COREVEGA_PATH_RSYNC_PID)"
	else
		cv_echo "rsync daemon not running, nothing to do"
	fi
}


## run container on host port 8000
# NOTE: this is kept as a reference only, airsonic dockerfile is preferred
run_docker_media_music_stream()
{
    docker run -dti \
        --publish 8000:4040 \
        --name="$2" \
        --hostname corevega-music \
        --network corevega-net \
        --dns 192.168.1.1 \
        -v /media/zachvp/SOL/music/media-server:/var/music \
		-v /home/zachvp/subsonic:/var/subsonic \
        hydria/subsonic:latest

	# link the container's transcoding lib to the path subsonic expects
	# this is required because /var/subsonic is mounted to the host
	docker exec -d "$2" sh -c "ln -s /usr/bin/ffmpeg /var/subsonic/transcode/ffmpeg"
    docker ps
}

# ===

## CLIENT 
### run rsync

#### Preferred: direct ethernet+ssh+daemon transfer
run_rsync_transfer_daemon()
{
    COREVEGA_TRANSFER_DEST="rsync://$COREVEGA_USER@$COREVEGA_IP:$COREVEGA_RSYNC_PORT"
    COREVEGA_ACTION=$2
    COREVEGA_MUSIC_SOURCE=$3

    while [[ $# -gt 0 ]]; do case "$COREVEGA_ACTION" in
            music)
                cv_echo "selected transfer music"
                cv_echo "transfer source: $COREVEGA_MUSIC_SOURCE"
                cv_echo "transfer destination: $COREVEGA_TRANSFER_DEST/music"
                
                cv_check_continue

                set -x
                time rsync "$COREVEGA_MUSIC_SOURCE/" "$COREVEGA_TRANSFER_DEST/music" \
                    $COREVEGA_RSYNC_OPTIONS \
                    --exclude '.*'
                exit 0

                ;;
            prefs)
                cv_echo "selected transfer prefs"
                cv_echo "transfer source: $COREVEGA_MUSIC_SOURCE"
                cv_echo "transfer destination: $COREVEGA_TRANSFER_DEST/music-prefs/subsonic"
                
                cv_check_continue

                set -x
                # include subsonic.backup      subsonic.data        subsonic.lck         subsonic.log         subsonic.properties  subsonic.script
                time rsync "$COREVEGA_MUSIC_SOURCE/" "$COREVEGA_TRANSFER_DEST/music-prefs/subsonic" \
                        $COREVEGA_RSYNC_OPTIONS \
                        --include 'db/' --include '*.properties' --exclude '*/' --exclude '*.log' --exclude '*.lck'
                    exit 0
                ;;
            *)
                cv_echo "Unknown argument '$COREVEGA_ACTION'. Usage: $0 run_rsync_transfer_daemon (music | prefs) <path>"
                set +x
                exit 1
                ;;
        esac
        shift
    done

    set +x
}

#### Simple setup: direct ethernet+ssh transfer
run_rsync_transfer()
{
    COREVEGA_MUSIC_MEDIA_SOURCE=$2
	time rsync $COREVEGA_MUSIC_MEDIA_SOURCE zachvp@$COREVEGA_IP:/media/zachvp/SOL/transfer-rsync/rsync_default \
        $COREVEGA_RSYNC_OPTIONS --exclude ".*"
}

# MAIN
cv_echo "$*"

# run the provided function argument
$1 $@
