# placeholders for missing file metadata
UNKNOWN_ARTIST = 'UNKNOWN_ARTIST'
UNKNOWN_ALBUM = 'UNKNOWN_ALBUM'

# mappings
MAPPING_MONTH = {
    1  : 'january',
    2  : 'february',
    3  : 'march',
    4  : 'april',
    5  : 'may',
    6  : 'june',
    7  : 'july',
    8  : 'august',
    9  : 'september',
    10 : 'october',
    11 : 'november',
    12 : 'december',
}

# delimiters
FILE_OPERATION_DELIMITER = '->'

# corevega server
COREVEGA_HOST = 'corevega.local'
COREVEGA_USER = 'zachvp'

RSYNC_PORT = '12000'
RSYNC_PROTOCOL = 'rsync://'
RSYNC_MODULE_NAVIDROME = 'navidrome'
RSYNC_URL = f"{RSYNC_PROTOCOL}{COREVEGA_USER}@{COREVEGA_HOST}:{RSYNC_PORT}"

# Rekordbox
ATTR_DATE_ADDED = 'DateAdded'
ATTR_PATH = 'Location'
ATTR_NAME = 'Name'
ATTR_ARTIST = 'Artist'
ATTR_ALBUM = 'Album'
ATTR_GENRE = 'Genre'
ATTR_KEY = 'Key'
ATTR_TRACK_ID = 'TrackID'

REKORDBOX_ROOT = 'file://localhost'
XPATH_COLLECTION = './/COLLECTION'
XPATH_PRUNED = './/NODE[@Name="_pruned"]'