#/bin/bash

COREVEGA_FUNCTION=$1
COREVEGA_MUSIC_MEDIA_SOURCE=$2
COREVEGA_IP_ETHERNET="192.168.2.2"
COREVEGA_RSYNC_PORT=12000

## server: run rsync daemon
run_rsync_daemon()
{
    if [ "$EUID" -e 0 ]; then
        rsync --daemon --config ~/.config/rsync/default.conf -v
    else
        echo "this daemon requires running as super user"
    fi
}

## client: run rsync

### Preferred: direct ethernet+ssh+daemon transfer
run_rsync_transfer_daemon()
{
    COREVEGA_TRANSFER_DEST="rsync://zachvp@$COREVEGA_IP_ETHERNET:$COREVEGA_RSYNC_PORT/music"

    echo "transfer source: $COREVEGA_MUSIC_MEDIA_SOURCE"
    echo "transfer destination: $COREVEGA_TRANSFER_DEST"
	rsync $COREVEGA_MUSIC_MEDIA_SOURCE $COREVEGA_TRANSFER_DEST \
        --progress -rtvzi --exclude ".*"
}

### Simple setup: direct ethernet+ssh transfer
run_rsync_transfer()
{
	rsync $COREVEGA_MUSIC_MEDIA_SOURCE zachvp@$COREVEGA_IP_ETHERNET:/media/zachvp/SOL/transfer-rsync/rsync_default \
        --progress -rtvzi --exclude ".*"
}

## run container on host port 8000
run_docker_media_music_stream()
{
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

