''' Hexadecimal Decoding '''

def hexstr_to_int(hexstr: str) -> int:
    ''' requires 0x prefix. able to self detect base with 0 as second param '''
    return int(hexstr, 0)

def hash_to_address(hash: str) -> str:
    ''' requires full 64 char with '0x' prefix. Trims to 40 char address '''
    return '0x' + hash[26:66]

def str256_to_address(str256: str) -> str:
    ''' requires full 64 char with '0x' prefix. Trims to 40 char address '''
    return '0x' + str256[24:64]


''' Hexadecimal Encoding '''

def int_to_hexstr(int: int) -> str:
    return hex(int)

def intstr_to_hexstr(intstr: str) -> str:
    return int_to_hexstr(int(intstr))
