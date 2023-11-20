import tempfile
import unittest
from datetime import datetime
from pathlib import Path

import nbtlib
from deepdiff import DeepDiff

from schempy import Block, Entity, Schematic
from schempy.constants import DATA_VERSION


class TestSchematic(unittest.TestCase):
    def setUp(self):
        self.width = 3
        self.height = 4
        self.length = 2
        self.offset = [1, 2, 3]
        self.data_version = DATA_VERSION
        self.name = "Test"
        self.author = "mmmfrieddough"
        self.date = datetime.fromtimestamp(1700356414574 / 1000)
        self.required_mods = ["mod1", "mod2"]
        self.metadata = {"test": {"test": "value",
                                  "number": 1, "list": ("one", "two")}}

        self.schematic = Schematic(self.width, self.height, self.length)
        self.schematic.offset = self.offset
        self.schematic.data_version = self.data_version
        self.schematic.name = self.name
        self.schematic.author = self.author
        self.schematic.date = self.date
        self.schematic.required_mods = self.required_mods
        self.schematic.metadata = self.metadata

        self.schematic.set_block(2, 0, 1, Block(
            "minecraft:grass_block", {"snowy": False}))
        self.schematic.set_block(1, 1, 1, Block("minecraft:stone"))
        self.schematic.set_block(0, 2, 1, Block("minecraft:chest", {
                                 "facing": "north", "type": "single", "waterlogged": False}))
        self.schematic.set_block(0, 3, 0, Block(
            "minecraft:oak_log", {"axis": "x"}))
        self.schematic.set_block(2, 3, 0, Block(
            "minecraft:oak_log", {"axis": "y"}))
        self.schematic.add_block_entity(Entity(
            "minecraft:chest", 0, 2, 1, {"Items": [{"Slot": 13, "id": "minecraft:torch", "Count": 1}]}))
        self.schematic.set_biome(0, 0, 0, "minecraft:plains")
        cow_properties = {
            "AbsorptionAmount": nbtlib.Float(0.0),
            "Age": 0,
            "Air": nbtlib.Short(300),
            "ArmorDropChances": [nbtlib.Float(0.085), nbtlib.Float(0.085), nbtlib.Float(0.085), nbtlib.Float(0.085)],
            "ArmorItems": [{}, {}, {}, {}],
            "Attributes": [{"Base": 0.20000000298023224, "Name": "minecraft:generic.movement_speed"}],
            "Brain": {"memories": {}},
            "CanPickUpLoot": False,
            "DeathTime": nbtlib.Short(0),
            "FallDistance": nbtlib.Float(0.0),
            "FallFlying": False,
            "Fire": nbtlib.Short(0),
            "ForcedAge": 0,
            "HandDropChances": [nbtlib.Float(0.085), nbtlib.Float(0.085)],
            "HandItems": [{}, {}],
            "Health": nbtlib.Float(10.0),
            "HurtByTimestamp": 0,
            "HurtTime": nbtlib.Short(0),
            "InLove": 0,
            "Invulnerable": False,
            "LeftHanded": False,
            "Motion": [0.0, 0.0, 0.0],
            "NoAI": True,
            "OnGround": False,
            "PersistenceRequired": False,
            "PortalCooldown": 0,
            "Pos": [0.5, 0.0, 0.5],
            "Rotation": [nbtlib.Float(0.0), nbtlib.Float(0.0)],
            "UUID": nbtlib.IntArray([-1442620014, 1817789528, -1877150187, -1746664296])
        }
        cow = Entity("minecraft:cow", 0.5, 0.0, 0.5, cow_properties)
        self.schematic.add_entity(cow)

        self.test_files_dir = Path('tests/fixtures/')
        self.test_files = {
            2: self.test_files_dir / 'test_v2.schem',
            3: self.test_files_dir / 'test_v3.schem'
        }

    def assertNBTFilesEqual(self, file_path1, file_path2):
        """Assert that two NBT files are equal by comparing their parsed contents."""
        with nbtlib.load(file_path1) as nbt_data1, nbtlib.load(file_path2) as nbt_data2:
            diff = DeepDiff(nbt_data1, nbt_data2, ignore_order=True)
            if diff:
                diff_message = f"NBT files {file_path1} and {
                    file_path2} do not match. Differences: {diff}"
                self.fail(diff_message)

    def test_initialization(self):
        self.assertEqual(self.schematic.width, self.width)
        self.assertEqual(self.schematic.height, self.height)
        self.assertEqual(self.schematic.length, self.length)
        self.assertEqual(self.schematic.offset, self.offset)
        self.assertEqual(self.schematic.data_version, self.data_version)
        self.assertEqual(self.schematic.name, self.name)
        self.assertEqual(self.schematic.author, self.author)
        self.assertEqual(self.schematic.date, self.date)
        self.assertEqual(self.schematic.required_mods, self.required_mods)
        self.assertEqual(self.schematic.metadata, self.metadata)

    def test_block_operations(self):
        block = Block("minecraft:stone")
        self.schematic.set_block(1, 1, 1, block)
        retrieved_block = self.schematic.get_block(1, 1, 1)
        self.assertEqual(retrieved_block, block)

    def test_block_entity_operations(self):
        block_entity = Entity("minecraft:chest", 1, 1, 1)
        self.schematic.add_block_entity(block_entity)
        self.assertIn(block_entity, self.schematic._block_entities)

    def test_metadata_preparation(self):
        self.schematic.metadata = {"TestKey": "TestValue"}
        metadata = self.schematic._prepare_metadata()
        self.assertIn('TestKey', metadata)
        self.assertEqual(metadata['TestKey'], nbtlib.String("TestValue"))

    def test_save_to_file(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            for version in self.test_files.keys():
                with self.subTest(version=version):
                    file_path = Path(tmp_dir) / f'test_save_v{version}.schem'
                    self.schematic.save_to_file(file_path, version=version)
                    self.assertTrue(file_path.exists())

    def test_file_not_found_error(self):
        with self.assertRaises(FileNotFoundError):
            Schematic.from_file(Path('nonexistent_file.schem'))

    def test_invalid_file_extension_error(self):
        with tempfile.NamedTemporaryFile(suffix='.txt') as tmp_file:
            with self.assertRaises(ValueError):
                self.schematic.save_to_file(Path(tmp_file.name))

    def test_out_of_bounds_error(self):
        with self.assertRaises(ValueError):
            self.schematic.set_block(-1, -1, -1, Block("minecraft:stone"))

    def test_load_schematic(self):
        for version, file_path in self.test_files.items():
            with self.subTest(version=version):
                # Remove tuple from metadata, as conversion from NBT to Python does not preserve tuple type
                self.metadata['test']['list'] = ["one", "two"]

                schematic = Schematic.from_file(file_path)
                self.assertEqual(schematic.width, self.width)
                self.assertEqual(schematic.height, self.height)
                self.assertEqual(schematic.length, self.length)
                self.assertEqual(schematic.offset, self.offset)
                self.assertEqual(schematic.data_version, self.data_version)
                self.assertEqual(schematic.name, self.name)
                self.assertEqual(schematic.author, self.author)
                self.assertEqual(schematic.date, self.date)
                self.assertCountEqual(
                    schematic.required_mods, self.required_mods)
                self.assertEqual(schematic.metadata, self.metadata)

    def test_create_schematic(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            for version, file_path in self.test_files.items():
                with self.subTest(version=version):
                    temp_file = Path(tmp_dir) / f'test_save_v{version}.schem'
                    self.schematic.save_to_file(temp_file, version=version)
                    print(f"Temporary file path: {temp_file}")
                    self.assertNBTFilesEqual(temp_file, file_path)

    def test_round_trip_schematic(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            for version, file_path in self.test_files.items():
                with self.subTest(version=version):
                    schematic = Schematic.from_file(file_path)
                    temp_file = Path(tmp_dir) / f'test_save_v{version}.schem'
                    schematic.save_to_file(temp_file, version=version)
                    self.assertNBTFilesEqual(temp_file, file_path)

    def test_cross_version_schematic(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            for version, file_path in self.test_files.items():
                for target_version in self.test_files.keys():
                    with self.subTest(version=version, target_version=target_version):
                        schematic = Schematic.from_file(file_path)
                        temp_file = Path(
                            tmp_dir) / f'test_cross_v{version}_to_v{target_version}.schem'
                        schematic.save_to_file(
                            temp_file, version=target_version)
                        self.assertNBTFilesEqual(
                            temp_file, self.test_files[target_version])

    def test_error_handling(self):
        # Test loading a non-existent file
        with self.assertRaises(FileNotFoundError):
            Schematic.from_file(self.test_files_dir / 'non_existent.schem')
        # Test saving with an unsupported version
        with self.assertRaises(ValueError):
            schematic = Schematic(width=10, height=10, length=10)
            schematic.save_to_file(
                self.test_files_dir / 'test_unsupported_version.schem', version=99)

    def test_iter_block_positions(self):
        # Define the dimensions of the schematic
        width, height, length = 3, 2, 4
        schematic = Schematic(width, height, length)

        # Create a list of all expected positions
        expected_positions = [(x, y, z) for x in range(width)
                              for y in range(height) for z in range(length)]

        # Convert the iterator to a list
        positions = list(schematic.iter_block_positions())

        # Check the total number of positions
        self.assertEqual(len(positions), width * height * length,
                         "The number of positions generated by iter_block_positions is incorrect.")

        # Compare with the expected list
        self.assertEqual(positions, expected_positions,
                         "The positions generated by iter_block_positions do not match the expected positions.")


if __name__ == '__main__':
    unittest.main()
