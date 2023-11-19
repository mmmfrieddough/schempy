import unittest
from typing import Type

from schempy import Block
from schempy.components import BlockPalette, Palette


class PaletteTestSuite(unittest.TestCase):
    # This will be overridden by the subclasses
    PaletteType: Type[Palette] = Palette

    def setUp(self):
        self.palette = self.PaletteType()
        self.block_air = Block("minecraft:air")
        self.block_stone = Block("minecraft:stone", {"variant": "granite"})
        self.block_dirt = Block("minecraft:dirt")

    def test_set_and_get_palette(self):
        test_palette = {
            self.block_air: 0,
            self.block_stone: 1,
            self.block_dirt: 2
        }
        self.palette.set_palette(test_palette)
        self.assertEqual(self.palette.get_palette(), test_palette)

    def test_get_id_new_block(self):
        # Get the next available ID which should be assigned to the new block
        next_id = len(self.palette.get_palette())
        # Add a new block that is not in the initial palette
        new_block = Block("minecraft:gold_block")
        block_id = self.palette.get_id(new_block)
        # Check that the new block gets the next available ID
        self.assertEqual(block_id, next_id)

    def test_get_id_existing_block(self):
        # Get the next available ID which should be assigned to the new block
        next_id = len(self.palette.get_palette())
        # Add a new block that is not in the initial palette
        new_block = Block("minecraft:gold_block")
        self.palette.get_id(new_block)
        block_id = self.palette.get_id(new_block)
        # Check that the new block gets the next available ID
        self.assertEqual(block_id, next_id)

    def test_get_block(self):
        block_id = self.palette.get_id(self.block_dirt)
        retrieved_block = self.palette.get_item(block_id)
        self.assertEqual(retrieved_block, self.block_dirt)

    def test_get_block_invalid_id(self):
        with self.assertRaises(IndexError):
            self.palette.get_item(99)


class TestPalette(PaletteTestSuite):
    PaletteType = Palette

    def setUp(self):
        super().setUp()
        self.test_palette = {
            "minecraft:air": 0,
            "minecraft:stone[variant=granite]": 1,
            "minecraft:dirt": 2
        }
        self.palette.set_palette(self.test_palette)

    def test_set_and_get_palette(self):
        self.assertEqual(self.palette.get_palette(), self.test_palette)


class TestBlockPalette(PaletteTestSuite):
    PaletteType = BlockPalette

    def setUp(self):
        super().setUp()
        self.test_palette = {
            "minecraft:air": 0,
            "minecraft:stone[variant=granite]": 1,
            "minecraft:dirt": 2
        }
        self.palette.set_palette(self.test_palette)

    def test_set_and_get_palette(self):
        # Overriding to test the string parsing logic
        expected_palette = {
            self.block_air: 0,
            self.block_stone: 1,
            self.block_dirt: 2
        }
        self.assertEqual(self.palette.get_palette(), expected_palette)


if __name__ == '__main__':
    unittest.main()
