# Next steps

# Migrate music to server
1. Clear music files
2. Perform full scan on music server
3. Docker compose down
4. Docker compose up
5. Run migration

# End to end process

## Organize after downloading
    1. `python djmgmt/process_downloads.py sweep ~/Downloads/ /Users/zachvp/Music/downloads/`
    2. `python djmgmt/process_downloads.py extract ~/Music/downloads ~/Music/downloads`
    3. `python djmgmt/process_downloads.py flatten ~/Music/downloads ~/Music/downloads`

## Standardize file formats
    1. `python djmgmt/re_encode_tracks.py ~/Music/downloads/ ~/Music/downloads/re-encoded/ '.mp3' --store-path $ZPATH_SCRIPTS_WRITE --store-skipped`

## Process on client
    1. Organize 
```bash
python djmgmt/organize_library_dates.py generate /media/zachvp/SOL/data/mac-collection-12-06-2023.xml\
        --output /media/zachvp/SOL/music/DJing/ > logs/organize_latest.log
```
    2. python djmgmt/sort_hierarchy_from_tags.py sort /media/zachvp/SOL/music/DJing/ > logs/sort_latest.log
    3. python djmgmt/sort_hierarchy_from_tags.py validate /media/zachvp/SOL/music/DJing/ -i
    4. python djmgmt/populate_media_server.py /media/zachvp/SOL/music/DJing/ /media/zachvp/SOL/media-server/ -i

## Copy to server
* copy ~/Music/downloads -> remote@host:/media/zachvp/SOL/media-server/staging
* copy /path/to/latest/collection.xml -> remote@host/home/{USER}/backup/transfer

# Developer help

## Useful snippets
### XML sandbox
```xml
<?xml version="1.0" encoding="UTF-8"?>

<DJ_PLAYLISTS Version="1.0.0">
  <PRODUCT Name="rekordbox" Version="6.8.1" Company="AlphaTheta"/>
  <COLLECTION Entries="2708"></COLLECTION>
  <PLAYLISTS>
      <NODE Type="0" Name="ROOT" Count="4">
          <NODE Name="sol_reason" Type="0" Count="7">
              <NODE Name="core" Type="0" Count="4">
                <NODE Name="_pruned" Type="1" KeyType="0" Entries="2006"></NODE>
              </NODE>
          </NODE>
      </NODE>
  </PLAYLISTS>
</DJ_PLAYLISTS>
```