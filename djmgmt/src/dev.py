if __name__ == '__main__':
    from . import music
    r = music.update_played_tracks('/Users/zachvp/Library/CloudStorage/OneDrive-Personal/Backups/rekordbox/collections/mac-collection-06-27-2025.xml')
    for t in r:
        print(t)
    pass