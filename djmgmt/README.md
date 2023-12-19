#_ todo: turn into bash/python script

# On the fly plan
## TODO:
* combine `sort_hierarchy_from_tags` and `organize_library_dates`
* combine `populate_media_server` and `aggregate_tracks`

# End to end process

## Organize after batch downloading
    1. `python djmgmt/process_downloads.py sweep ~/Downloads/ /Users/zachvp/Music/downloads/`
    2. `python djmgmt/process_downloads.py extract ~/Music/downloads ~/Music/downloads`
    3. `python djmgmt/process_downloads.py flatten ~/Music/downloads ~/Music/downloads`

## Standardize file formats
    1. `python djmgmt/re_encode_tracks.py ~/Music/downloads/ ~/Music/downloads/re-encoded/ '.aiff' --store-path $ZPATH_SCRIPTS_WRITE --store-skipped`

## Copy to DJing source folder
    1. `rsync ~/Music/downloads /Volumes/ZVP-MUSIC/DJing --progress -auvzi --exclude ".*"`

## Copy to server
**TODO: likely use rsync daemon
**TODO: check if 'use chroot' is needed in ~/.config/rsync/
* copy ~/Music/downloads -> remote@host:/media/zachvp/SOL/media-server/staging
* copy /path/to/latest/collection.xml -> remote@host/home/{USER}/backup/transfer

## Process on server
    1. python djmgmt/organize_library_dates.py generate /media/zachvp/SOL/data/mac-collection-12-06-2023.xml\
        --output /media/zachvp/SOL/music/DJing/ > logs/organize_latest.log
    2. python djmgmt/sort_hierarchy_from_tags.py sort /media/zachvp/SOL/music/DJing/ > logs/sort_latest.log
    3. python djmgmt/sort_hierarchy_from_tags.py validate /media/zachvp/SOL/music/DJing/ -i
    4. python djmgmt/populate_media_server.py /media/zachvp/SOL/music/DJing/ /media/zachvp/SOL/media-server/ -i


# Ongoing process loops
## Update files on server from DJing source
    TODO: script to determine changes