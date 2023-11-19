import dataclasses
import unittest

from schempy import Block


class TestBlock(unittest.TestCase):
    def setUp(self):
        self.block1 = Block("stone", {"hardness": "1.5", "resistance": "10"})
        # Same as block1 but properties are reversed
        self.block2 = Block("stone", {"resistance": "10", "hardness": "1.5"})
        self.block3 = Block("dirt", {"hardness": "0.5"})
        self.block4 = Block("stone")  # No properties
        self.block5 = Block("stone", {})  # Empty properties

    def test_block_equality(self):
        # Blocks with the same id and properties should be equal
        self.assertEqual(self.block1, self.block2)
        # Blocks with different ids or properties should not be equal
        self.assertNotEqual(self.block1, self.block3)
        self.assertNotEqual(self.block1, self.block4)

    def test_block_hash(self):
        # Blocks with the same id and properties should have the same hash
        self.assertEqual(hash(self.block1), hash(self.block2))
        # Blocks with different ids or properties should have different hashes
        self.assertNotEqual(hash(self.block1), hash(self.block3))
        self.assertNotEqual(hash(self.block1), hash(self.block4))

    def test_block_str(self):
        # Test the string representation of the block
        self.assertEqual(str(self.block1), "stone[hardness=1.5,resistance=10]")
        self.assertEqual(str(self.block3), "dirt[hardness=0.5]")
        self.assertEqual(str(self.block4), "stone")
        self.assertEqual(str(self.block5), "stone")

    def test_block_properties_immutable(self):
        block = Block("stone", {"hardness": "1.5", "resistance": "10"})
        # Check that we cannot replace the 'properties' dictionary
        with self.assertRaises(dataclasses.FrozenInstanceError):
            block.properties = {"hardness": "2.0"}


if __name__ == '__main__':
    unittest.main()
