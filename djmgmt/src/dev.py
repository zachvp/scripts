if __name__ == '__main__':
    from . import music
    c = music.load_collection_xml('/Users/zachvp/Library/CloudStorage/OneDrive-Personal/Backups/rekordbox/collections/mac-collection-06-27-2025.xml')
    r = music.get_played_tracks(c)
    for t in r:
        print(t)
    pass