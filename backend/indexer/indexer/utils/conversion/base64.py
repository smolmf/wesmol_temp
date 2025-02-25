import base64


''' Base64 Encoding '''

def str_to_base64(string: str) -> str:
    data_bytes = string.encode('ascii')
    b64_bytes = base64.b64encode(data_bytes)
    return b64_bytes.decode('ascii')


''' Base64 Decoding '''

def base64_to_str(b64_str: str) -> str:
    b64_bytes = b64_str.encode('ascii')
    data_bytes = base64.b64decode(b64_bytes)
    return data_bytes.decode('ascii')
