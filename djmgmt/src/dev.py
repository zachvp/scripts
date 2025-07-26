if __name__ == '__main__':
    from . import music, library
    # c = music.load_collection_xml('/Users/zachvp/Library/CloudStorage/OneDrive-Personal/Backups/rekordbox/collections/mac-collection-06-27-2025.xml')
    # music.record_unplayed_tracks('/Users/zachvp/Library/CloudStorage/OneDrive-Personal/Backups/rekordbox/collections/mac-collection-07-23-2025.xml',
    #                              '/Users/zachvp/developer/scripts/djmgmt/state/test-unplayed.xml')
    r = library.find_collection_backup('/Users/zachvp/Library/CloudStorage/OneDrive-Personal/Backups/rekordbox/collections/')
    print(r)
    pass