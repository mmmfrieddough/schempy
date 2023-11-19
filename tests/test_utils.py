import unittest

import numpy as np
from nbtlib import (Byte, ByteArray, Compound, Double, Float, Int, IntArray,
                    List, Long, LongArray, Short, String)

from schempy.utils import (decode_varint_from, decode_varints, encode_varint,
                           encode_varints, from_unsigned_short, nbt_to_python,
                           numpy_array_to_varint_bytearray, python_to_nbt,
                           to_unsigned_short, varint_bytearray_to_numpy_array)


class TestUtils(unittest.TestCase):

    def test_to_unsigned_short_valid(self):
        self.assertEqual(to_unsigned_short(100), 100)
        self.assertEqual(to_unsigned_short(0), 0)
        self.assertEqual(to_unsigned_short(65535), 65535)

    def test_to_unsigned_short_invalid(self):
        with self.assertRaises(ValueError):
            to_unsigned_short(-1)
        with self.assertRaises(ValueError):
            to_unsigned_short(65536)

    def test_from_unsigned_short(self):
        self.assertEqual(from_unsigned_short(65535), 65535)
        self.assertEqual(from_unsigned_short(-1), 65535)

    def test_encode_single_varint(self):
        self.assertEqual(encode_varint(300), bytearray(b'\xac\x02'))

    def test_decode_single_varint(self):
        decoded_value, length = decode_varint_from(bytearray(b'\xac\x02'), 0)
        self.assertEqual(decoded_value, 300)
        self.assertEqual(length, 2)

    def test_encode_decode_varints(self):
        test_values = [0, 127, 128, 255, 16384, 2097151, 268435455]
        encoded = encode_varints(test_values)
        decoded = decode_varints(encoded)
        self.assertEqual(decoded, test_values)

    def test_encode_empty_list(self):
        self.assertEqual(encode_varints([]), bytearray())

    def test_decode_empty_bytearray(self):
        self.assertEqual(decode_varints(bytearray()), [])

    def test_encode_negative_number(self):
        with self.assertRaises(ValueError):
            encode_varint(-1)

    def test_decode_invalid_varint(self):
        with self.assertRaises(ValueError):
            decode_varint_from(bytearray(b'\x80'), 0)

    def test_encode_very_large_number(self):
        very_large_number = 2**64
        with self.assertRaises(ValueError):
            encode_varint(very_large_number)

    def test_decode_with_offset(self):
        encoded = bytearray(b'\xac\x02\x96\x01')
        decoded_value, length = decode_varint_from(encoded, 2)
        self.assertEqual(decoded_value, 150)
        self.assertEqual(length, 2)

    def test_encode_decode_with_large_numbers(self):
        large_numbers = [2**30, 2**31, 2**32]
        encoded = encode_varints(large_numbers)
        decoded = decode_varints(encoded)
        self.assertEqual(decoded, large_numbers)

    def test_decode_incomplete_varint(self):
        incomplete_varint = bytearray(b'\x80\x80\x80')
        with self.assertRaises(ValueError):
            decode_varints(incomplete_varint)

    def test_numpy_array_to_varint_bytearray(self):
        array = np.array([300, 150], dtype=np.int32)
        varint_bytearray = numpy_array_to_varint_bytearray(array)
        expected_bytearray = bytearray(b'\xac\x02\x96\x01')
        self.assertEqual(varint_bytearray, expected_bytearray)

    def test_varint_bytearray_to_numpy_array(self):
        byte_array = bytearray(b'\xac\x02\x96\x01')
        expected_array = np.array([300, 150], dtype=np.int32)
        numpy_array = varint_bytearray_to_numpy_array(byte_array, (2,))
        np.testing.assert_array_equal(numpy_array, expected_array)

    def test_round_trip_conversion(self):
        original_array = np.array(
            [0, 127, 128, 255, 16384, 2097151, 268435455], dtype=np.int32)
        varint_bytearray = numpy_array_to_varint_bytearray(original_array)
        round_trip_array = varint_bytearray_to_numpy_array(
            varint_bytearray, original_array.shape)
        np.testing.assert_array_equal(round_trip_array, original_array)

    def test_empty_numpy_array(self):
        empty_array = np.array([], dtype=np.int32)
        varint_bytearray = numpy_array_to_varint_bytearray(empty_array)
        self.assertEqual(varint_bytearray, bytearray())

    def test_empty_bytearray_to_numpy_array(self):
        empty_byte_array = bytearray()
        expected_array = np.array([], dtype=np.int32)
        numpy_array = varint_bytearray_to_numpy_array(empty_byte_array, (0,))
        np.testing.assert_array_equal(numpy_array, expected_array)

    def test_numpy_array_with_negative_numbers(self):
        array_with_negatives = np.array([-1, -128, -255], dtype=np.int32)
        with self.assertRaises(ValueError):
            numpy_array_to_varint_bytearray(array_with_negatives)

    def test_incorrect_shape(self):
        byte_array = bytearray(b'\xac\x02\x96\x01')
        with self.assertRaises(ValueError):
            varint_bytearray_to_numpy_array(
                byte_array, (3,))  # Incorrect shape

    def test_nbt_to_python(self):
        # Create a compound with various types
        nbt_compound = Compound({
            'byte': Byte(1),
            'short': Short(2),
            'int': Int(3),
            'long': Long(4),
            'float': Float(5.5),
            'double': Double(6.6),
            'string': String('test'),
            'byte_array': ByteArray([7, 8, 9]),
            'int_array': IntArray([10, 11, 12]),
            'long_array': LongArray([13, 14, 15]),
            'list': List([Int(16), Int(17)]),
            'compound': Compound({'nested': Int(18)})
        })

        # Convert to Python types
        python_data = nbt_to_python(nbt_compound)

        # Check the conversion
        self.assertEqual(python_data, {
            'byte': 1,
            'short': 2,
            'int': 3,
            'long': 4,
            'float': 5.5,
            'double': 6.6,
            'string': 'test',
            'byte_array': [7, 8, 9],
            'int_array': [10, 11, 12],
            'long_array': [13, 14, 15],
            'list': [16, 17],
            'compound': {'nested': 18}
        })

    def test_python_to_nbt(self):
        # Create a Python dictionary with various types
        python_dict = {
            'int': 32768,
            'long': 1234567890123456789,
            'double': 6.6,
            'string': 'test',
            'list': [16, 17],
            'compound': {'nested': 18}
        }

        # Convert to NBT types
        nbt_data = python_to_nbt(python_dict)

        # Check the conversion
        self.assertIsInstance(nbt_data['int'], Int)
        self.assertIsInstance(nbt_data['long'], Long)
        self.assertIsInstance(nbt_data['double'], Double)
        self.assertIsInstance(nbt_data['string'], String)
        self.assertIsInstance(nbt_data['list'], List)
        self.assertIsInstance(nbt_data['compound'], Compound)
        self.assertEqual(nbt_data['compound']['nested'], Int(18))


if __name__ == '__main__':
    unittest.main()
