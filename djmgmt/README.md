# Next steps
## Development
1. Re-sync outdated files:
    * determine file path pairs with changed metadata (DJ lib path, lossy lib path)
    * extract all date contexts from lossy lib paths
    * pass all date contexts as override param to sync
        * for each date context: re-encode and re-transfer
2. Discover unplayed tracks: read RB XML to determine played tracks in archive; create playlist of all tracks not in archive
3. Check if existing playlist has any previously played tracks
4. Convert existing TSV playlists to structured format
5. Read Rekordbox DB for unassigned Tags in _pruned
6. Use GitHub for project management

## Library remediation
1. Refactor genres: Move House/Techno to Techno/