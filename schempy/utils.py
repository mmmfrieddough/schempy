from typing import List, Tuple

import numpy as np
from nbtlib import (Byte, ByteArray, Compound, Double, Float, Int, IntArray,
                    List, Long, LongArray, Short, String)


def to_unsigned_short(value):
    """Convert an integer to an unsigned short, ensuring it's within range."""
    if not (0 <= value <= 65535):
        raise ValueError("Value must be between 0 and 65535.")
    return value


def from_unsigned_short(value):
    """Convert an NBT short to an unsigned short by interpreting it as positive."""
    return value & 0xFFFF  # Bitwise AND with 0xFFFF ensures the value is treated as unsigned


def encode_varints(values: List[int]) -> bytearray:
    """Encode a list of integers into a bytearray of varints."""
    varint_array = bytearray()
    for value in values:
        varint_array.extend(encode_varint(value))
    return varint_array


def encode_varint(value: int) -> bytearray:
    """Encode an integer as a varint."""
    if value < 0:
        raise ValueError("Cannot encode negative numbers as varints.")
    if value >= 1 << 64:
        raise ValueError(
            "Cannot encode numbers larger than 2^64 - 1 as varints.")
    varint = bytearray()
    while value > 127:
        varint.append((value & 0x7F) | 0x80)
        value >>= 7
    varint.append(value & 0x7F)
    return varint


def decode_varints(data: bytearray) -> List[int]:
    """Decode a sequence of varints from a bytearray."""
    results = []
    i = 0
    while i < len(data):
        result, length = decode_varint_from(data, i)
        results.append(result)
        i += length
    return results


def decode_varint_from(data: bytearray, offset: int = 0) -> Tuple[int, int]:
    """Decode a varint from a bytearray starting at the given offset."""
    shift = 0
    result = 0
    length = 0
    for i in range(offset, len(data)):
        byte = data[i]
        result |= (byte & 0x7F) << shift
        shift += 7
        length += 1
        if not (byte & 0x80):
            return result, length
    raise ValueError(
        "Bytearray does not contain valid varints at the given offset.")


def numpy_array_to_varint_bytearray(array: np.ndarray) -> bytearray:
    """Convert a NumPy array of integers to a varint-encoded bytearray."""
    flat_array = array.ravel()
    return encode_varints(flat_array)


def varint_bytearray_to_numpy_array(byte_array: bytearray, shape: Tuple[int, ...]) -> np.ndarray:
    """Convert a varint-encoded bytearray back to a NumPy array with the given shape."""
    decoded_numbers = decode_varints(byte_array)
    return np.array(decoded_numbers).reshape(shape)


def nbt_to_python(nbt_data):
    """Convert nbtlib types to Python types, only when unambiguous."""
    if isinstance(nbt_data, Int):
        return int(nbt_data)
    if isinstance(nbt_data, String):
        return str(nbt_data)
    elif isinstance(nbt_data, Compound):
        return {key: nbt_to_python(value) for key, value in nbt_data.items()}
    elif isinstance(nbt_data, List):
        return [nbt_to_python(element) for element in nbt_data]
    else:
        # For NBT numeric types, leave as is to preserve type information
        return nbt_data


def python_to_nbt(data):
    """Convert Python types to nbtlib types."""
    if isinstance(data, (Byte, Short, Int, Long, Float, Double, ByteArray, IntArray, LongArray, String)):
        # Already NBT type, so leave as is
        return data
    elif isinstance(data, dict):
        return Compound({key: python_to_nbt(value) for key, value in data.items()})
    elif isinstance(data, list) or isinstance(data, tuple):
        return List([python_to_nbt(element) for element in data])
    elif isinstance(data, bool):
        return Byte(1) if data else Byte(0)
    elif isinstance(data, int):
        # For new integers, choose an NBT type based on the value range
        if -2147483648 <= data <= 2147483647:
            return Int(data)
        else:
            return Long(data)
    elif isinstance(data, float):
        return Double(data)
    elif isinstance(data, str):
        return String(data)
    else:
        # Raise error for unsupported types
        raise TypeError(f"Unsupported type: {type(data)}")
