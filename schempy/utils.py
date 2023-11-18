from typing import List, Tuple

import numpy as np


def to_unsigned_short(value):
    """Convert an integer to an unsigned short, ensuring it's within range."""
    if not (0 <= value <= 65535):
        raise ValueError("Value must be between 0 and 65535.")
    return value


def from_unsigned_short(value):
    """Convert an NBT short to an unsigned short by interpreting it as positive."""
    return value & 0xFFFF  # Bitwise AND with 0xFFFF ensures the value is treated as unsigned


def encode_varint(value: int) -> bytearray:
    """Encode an integer as a varint."""
    varint = bytearray()
    while True:
        byte = value & 0b01111111
        value >>= 7
        if value:
            varint.append(byte | 0b10000000)
        else:
            varint.append(byte)
            break
    return varint


def decode_varint(byte_array: bytearray) -> List[int]:
    """Decode a bytearray of varint encoded numbers into a list of integers."""
    numbers = []
    current = 0
    bit_offset = 0

    for byte in byte_array:
        has_next = (byte & 0b10000000) != 0
        current |= (byte & 0b01111111) << bit_offset
        bit_offset += 7

        if not has_next:
            numbers.append(current)
            current = 0
            bit_offset = 0

    return numbers


def numpy_array_to_varint_bytearray(array: np.ndarray) -> bytearray:
    """Convert a NumPy array of integers to a varint-encoded bytearray."""
    flat_array = array.ravel()
    varint_encoded = bytearray()
    for number in flat_array:
        varint_encoded.extend(encode_varint(number))
    return varint_encoded


def varint_bytearray_to_numpy_array(byte_array: bytearray, shape: Tuple[int, ...]) -> np.ndarray:
    """Convert a varint-encoded bytearray back to a NumPy array with the given shape."""
    decoded_numbers = decode_varint(byte_array)
    return np.array(decoded_numbers).reshape(shape)
