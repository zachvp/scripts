if __name__ == '__main__':
    from . import music
    # c = music.load_collection_xml('/Users/zachvp/Library/CloudStorage/OneDrive-Personal/Backups/rekordbox/collections/mac-collection-06-27-2025.xml')
    music.record_unrecorded_tracks('/Users/zachvp/Library/CloudStorage/OneDrive-Personal/Backups/rekordbox/collections/mac-collection-07-23-2025.xml',
                                 '/Users/zachvp/developer/scripts/djmgmt/state/test-unplayed.xml')
    # for t in r:
    #     print(t)
    pass