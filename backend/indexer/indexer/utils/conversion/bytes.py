import json


''' Bytes Decoding, ASCII '''

def bytes_to_str(value: bytes) -> str:
    return value.decode('ascii')

def bytes_to_dict(value: bytes) -> dict:
    return json.loads(value)


''' Bytes Encoding, ASCII '''

def str_to_bytes(value: str) -> bytes:
    return value.encode('ascii')

def dict_to_bytes(value: dict) -> bytes:
    return json.dumps(value).encode('ascii')
