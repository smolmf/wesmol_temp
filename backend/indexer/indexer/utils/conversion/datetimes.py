from datetime import datetime

from indexer.indexer.model.types import DateTimeStr, HexInt

''' String with following format, '2024-07-01T01:18:57Z' '''
def timestr_to_datetime(datetime_string: DateTimeStr) -> datetime:
    datetime_object = datetime.strptime(datetime_string, '%Y-%m-%dT%H:%M:%SZ')
    return datetime_object

def hex_to_datetime(hex_string: HexInt) -> datetime:
    """Converts a hexadecimal Unix timestamp to a datetime object."""
    try:
        timestamp_int = int(hex_string, 16)
        datetime_object = datetime.fromtimestamp(timestamp_int)
        return datetime_object
    except ValueError:
        return "Invalid hexadecimal timestamp"
