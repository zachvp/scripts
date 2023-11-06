#/bin/bash

COREVEGA_IP_ETHERNET="192.168.2.2"
COREVEGA_RSYNC_PORT=12000
COREVEGA_PATH_HOME="/home/zachvp"
COREVEGA_PATH_RSYNC_PID="$COREVEGA_PATH_HOME/developer/state/rsync/rsyncd.pid"
COREVEGA_USER="zachvp"

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
		ps_rsyncd
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
run_docker_media_music_stream()
{
    docker run -dti \
        --publish 8000:4040 \
        --name="subsonic_corevega_restore" \
        --hostname corevega-music \
        --network corevega-net \
        --dns 192.168.1.1 \
        -v /media/zachvp/SOL/transfer-rsync/daemon/music:/Users/zachvp/Library/CloudStorage/OneDrive-Personal/Backups/rekordbox/rekordbox_bak \
		-v /media/zachvp/SOL/transfer-rsync/daemon/music-prefs/subsonic/subsonic.properties:/var/subsonic/subsonic.properties \
    	-v /media/zachvp/SOL/transfer-rsync/daemon/music-prefs/subsonic/db:/var/subsonic/db \
        hydria/subsonic:latest

    docker ps
}

# ===

## CLIENT 
### run rsync

#### Preferred: direct ethernet+ssh+daemon transfer
run_rsync_transfer_daemon()
{
    COREVEGA_TRANSFER_DEST="rsync://$COREVEGA_USER@$COREVEGA_IP_ETHERNET:$COREVEGA_RSYNC_PORT"
    COREVEGA_ACTION=$2
    COREVEGA_MUSIC_SOURCE=$3
    COREVEGA_OPTIONS="--progress -rtvzi"

    while [[ $# -gt 0 ]]; do case "$COREVEGA_ACTION" in
            music)
                cv_echo "selected transfer music"
                cv_echo "transfer source: $COREVEGA_MUSIC_SOURCE"
                cv_echo "transfer destination: $COREVEGA_TRANSFER_DEST/music"
                
                cv_check_continue

                set -x
                time rsync "$COREVEGA_MUSIC_SOURCE/" "$COREVEGA_TRANSFER_DEST/music" \
                    $COREVEGA_OPTIONS \
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
                        $COREVEGA_OPTIONS \
                        --include 'db/' --include '*.properties' --exclude '*/' --exclude '*.log' --exclude '*.lck'
                    exit 0
                ;;
            *)
                cv_echo "Unknown argument '$COREVEGA_ACTION'. Usage: $0 run_rsync_transfer_daemon music | prefs <path>"
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
	time rsync $COREVEGA_MUSIC_MEDIA_SOURCE zachvp@$COREVEGA_IP_ETHERNET:/media/zachvp/SOL/transfer-rsync/rsync_default \
        --progress -rtvzi --exclude ".*"
}

# MAIN
cv_echo "$*"

# run the provided function argument
$1 $@

