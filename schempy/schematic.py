from datetime import datetime
from itertools import product
from pathlib import Path
from typing import Dict, List

import nbtlib
import numpy as np
from nbtlib import File

from . import utils
from .components import Block, BlockPalette, Entity, Palette
from .constants import DATA_VERSION, MINECRAFT_AIR
from .schema.v2 import SpongeV2
from .schema.v3 import SpongeV3


class Schematic:
    def __init__(self, width: int, height: int, length: int):
        self.width: int = utils.to_unsigned_short(width)
        self.height: int = utils.to_unsigned_short(height)
        self.length: int = utils.to_unsigned_short(length)

        self.offset: List[int] = [0, 0, 0]
        self.data_version: int = DATA_VERSION

        self.name: str = 'My Schematic'
        self.author: str = 'SchemPy'
        self.date: datetime = datetime.now()
        self.required_mods: List[str] = []
        self.metadata: dict = {}

        self._block_palette: BlockPalette = BlockPalette()
        self._block_palette.get_id(Block(MINECRAFT_AIR))
        self._block_data: np.ndarray = np.zeros(
            (self.height, self.length, self.width), dtype=int)
        self._block_entities: List[Entity] = []
        self._biome_palette: Palette = Palette()
        self._biome_data: np.ndarray = np.zeros(
            (self.height, self.length, self.width), dtype=int)
        self._entities: List[Entity] = []

    def _check_coordinates(self, x: int, y: int, z: int) -> None:
        """Check that the coordinates are within the schematic bounds."""
        if not (0 <= x < self.width and 0 <= y < self.height and 0 <= z < self.length):
            raise ValueError("Coordinates out of range.")

    def get_block(self, x: int, y: int, z: int) -> Block:
        """Get the block at the specified coordinates."""
        self._check_coordinates(x, y, z)
        return self._block_palette.get_item(self._block_data[y, z, x])

    def set_block(self, x: int, y: int, z: int, block: Block):
        """Set the block at the specified coordinates."""
        self._check_coordinates(x, y, z)
        self._block_data[y, z, x] = self._block_palette.get_id(block)

    def add_block_entity(self, block_entity: Entity):
        """Add a block entity."""
        self._check_coordinates(block_entity.x, block_entity.y, block_entity.z)
        self._block_entities.append(block_entity)

    def get_biome(self, x: int, y: int, z: int) -> str:
        """Get the biome at the specified coordinates."""
        self._check_coordinates(x, y, z)
        return self._biome_palette.get_item(self._biome_data[y, z, x])

    def set_biome(self, x: int, y: int, z: int, biome: str):
        """Set the biome at the specified coordinates."""
        self._check_coordinates(x, y, z)
        self._biome_data[y, z, x] = self._biome_palette.get_id(biome)

    def add_entity(self, entity: Entity):
        """Add an entity."""
        self._check_coordinates(entity.x, entity.y, entity.z)
        self._entities.append(entity)

    def iter_block_positions(self):
        """Iterator over every block position in the schematic, yielding (x, y, z) tuples."""
        return product(range(self.width), range(self.height), range(self.length))

    def _prepare_metadata(self) -> Dict:
        """Prepare the metadata for saving."""
        metadata = utils.python_to_nbt(self.metadata)
        metadata.update({
            'Name': nbtlib.String(self.name),
            'Author': nbtlib.String(self.author),
            'Date': nbtlib.Long(self.date.timestamp() * 1000),
            'RequiredMods': nbtlib.List([nbtlib.String(mod) for mod in self.required_mods])
        })
        return metadata

    def _save_to_file_v1(self) -> File:
        raise NotImplementedError(
            "Version 1 schematics are not supported.")

    def _save_to_file_v2(self) -> File:
        # Get data ready
        metadata = self._prepare_metadata()
        block_palette = {str(key): nbtlib.Int(value)
                         for key, value in self._block_palette.get_palette().items()}
        block_data = utils.numpy_array_to_varint_bytearray(self._block_data)
        block_entities = [{'Pos': [entity.x, entity.y, entity.z], 'Id': entity.id, **
                           utils.python_to_nbt(entity.properties)} for entity in self._block_entities]
        biome_palette = {key: nbtlib.Int(
            value) for key, value in self._biome_palette.get_palette().items()}
        biome_data = utils.numpy_array_to_varint_bytearray(self._biome_data[0])
        entities = [{'Pos': [entity.x, entity.y, entity.z], 'Id': entity.id, **
                     utils.python_to_nbt(entity.properties)} for entity in self._entities]

        # Insert into schema
        data = SpongeV2({
            'Version': 2,
            'DataVersion': self.data_version,
            'Metadata': metadata,
            'Width': self.width,
            'Height': self.height,
            'Length': self.length,
            'Offset': self.offset,
            'PaletteMax': len(self._block_palette.get_palette()),
            'Palette': block_palette,
            'BlockData': block_data,
            'BlockEntities': block_entities
        })

        # Insert optional fields
        if len(entities) > 0:
            data['Entities'] = entities
        if len(biome_palette) > 0:
            data['BiomePaletteMax'] = len(self._biome_palette.get_palette())
            data['BiomePalette'] = biome_palette
            data['BiomeData'] = biome_data

        return nbtlib.File(data, root_name='Schematic')

    def _save_to_file_v3(self) -> File:
        # Get data ready
        metadata = self._prepare_metadata()
        block_palette = {str(key): nbtlib.Int(value)
                         for key, value in self._block_palette.get_palette().items()}
        block_data = utils.numpy_array_to_varint_bytearray(self._block_data)
        block_entities = [utils.python_to_nbt(
            {'Pos': [entity.x, entity.y, entity.z], 'Id': entity.id, 'Data': entity.properties}) for entity in self._block_entities]
        biome_palette = {key: nbtlib.Int(
            value) for key, value in self._biome_palette.get_palette().items()}
        biome_data = utils.numpy_array_to_varint_bytearray(self._biome_data)
        entities = [utils.python_to_nbt({'Pos': [entity.x, entity.y, entity.z], 'Id': entity.id, 'Data': {
                                        'Pos': [entity.x, entity.y, entity.z], **entity.properties}}) for entity in self._entities]

        # Insert into schema
        data = SpongeV3({
            'Schematic': {
                'Version': 3,
                'DataVersion': self.data_version,
                'Metadata': metadata,
                'Width': self.width,
                'Height': self.height,
                'Length': self.length,
                'Offset': self.offset,
                'Blocks': {
                    'Palette': block_palette,
                    'Data': block_data,
                    'BlockEntities': block_entities
                }
            }
        })

        # Insert optional fields
        if len(biome_palette) > 0:
            data['Schematic']['Biomes'] = {
                'Palette': biome_palette,
                'Data': biome_data
            }
        if len(entities) > 0:
            data['Schematic']['Entities'] = entities

        return nbtlib.File(data)

    def save_to_file(self, file_path: Path, version: int = 3) -> None:
        if not isinstance(file_path, Path):
            raise TypeError("File path must be a Path object.")
        if not file_path.parent.exists():
            raise FileNotFoundError(
                f"Directory {file_path.parent} does not exist.")

        if file_path.suffix != '.schem':
            raise ValueError(
                "Invalid file extension. Please use '.schem' extension.")

        # Create the data dictionary
        if version == 1:
            file = self._save_to_file_v1()
        elif version == 2:
            file = self._save_to_file_v2()
        elif version == 3:
            file = self._save_to_file_v3()
        else:
            raise ValueError("Invalid schematic version.")

        # Save the data to the file
        file.save(file_path, gzipped=True)

    def _parse_metadata(self, metadata: dict) -> None:
        """Parse the metadata from the file."""
        metadata = utils.nbt_to_python(metadata)
        if 'Name' in metadata:
            self.name = metadata['Name']
            del metadata['Name']
        if 'Author' in metadata:
            self.author = metadata['Author']
            del metadata['Author']
        if 'Date' in metadata:
            self.date = datetime.fromtimestamp(metadata['Date'] / 1000)
            del metadata['Date']
        if 'RequiredMods' in metadata:
            self.required_mods = [str(value)
                                  for value in metadata['RequiredMods']]
            del metadata['RequiredMods']
        self.metadata = metadata

    def _parse_entity(entity: dict, version: int) -> Entity:
        """Parse an entity from the file."""
        id = utils.nbt_to_python(entity['Id'])
        del entity['Id']
        x, y, z = utils.nbt_to_python(entity['Pos'][0]), utils.nbt_to_python(
            entity['Pos'][1]), utils.nbt_to_python(entity['Pos'][2])
        del entity['Pos']
        properties = utils.nbt_to_python(
            entity['Data'] if version == 3 else entity)
        return Entity(id, x, y, z, properties)

    @classmethod
    def _parse_file_v1(cls, file: File) -> 'Schematic':
        raise NotImplementedError(
            "Version 1 schematics are not supported.")

    @classmethod
    def _parse_file_v2(cls, file: File) -> 'Schematic':
        data = SpongeV2(file)

        # Get the required fields
        try:
            schematic = Schematic(
                width=utils.from_unsigned_short(data['Width']),
                height=utils.from_unsigned_short(data['Height']),
                length=utils.from_unsigned_short(data['Length']),
            )
            schematic.offset = [int(value) for value in data['Offset']]
            schematic.data_version = data['DataVersion']
        except KeyError:
            raise ValueError("Invalid schematic file.")

        # Get the optional fields
        if 'Metadata' in data:
            schematic._parse_metadata(data['Metadata'])
        if 'BlockData' in data:
            schematic._block_palette.set_palette(data['Palette'])
            shape = (schematic.height, schematic.length, schematic.width)
            schematic._block_data = utils.varint_bytearray_to_numpy_array(
                data['BlockData'], shape)
        if 'BlockEntities' in data:
            schematic._block_entities = [cls._parse_entity(
                entity, 2) for entity in data['BlockEntities']]
        if 'BiomeData' in data:
            schematic._biome_palette.set_palette(data['BiomePalette'])
            # Since version 2 schematics store biome data as a 2D array, we need to convert it to a 3D array
            shape = (schematic.length, schematic.width)
            biome_data = utils.varint_bytearray_to_numpy_array(
                data['BiomeData'], shape)
            schematic._biome_data = np.repeat(
                biome_data[np.newaxis, :, :], schematic.height, axis=0)
        if 'Entities' in data:
            schematic._entities = [cls._parse_entity(
                entity, 2) for entity in data['Entities']]

        return schematic

    @classmethod
    def _parse_file_v3(cls, file: File) -> 'Schematic':
        data = SpongeV3(file)['Schematic']

        # Get the required fields
        try:
            schematic = Schematic(
                width=utils.from_unsigned_short(data['Width']),
                height=utils.from_unsigned_short(data['Height']),
                length=utils.from_unsigned_short(data['Length']),
            )
            schematic.offset = [int(value) for value in data['Offset']]
            schematic.data_version = data['DataVersion']
        except KeyError:
            raise ValueError("Invalid schematic file.")

        # Get the optional fields
        if 'Metadata' in data:
            schematic._parse_metadata(data['Metadata'])
        shape = (schematic.height, schematic.length, schematic.width)
        if 'Blocks' in data:
            schematic._block_palette.set_palette(data['Blocks']['Palette'])
            schematic._block_data = utils.varint_bytearray_to_numpy_array(
                data['Blocks']['Data'], shape)
            schematic._block_entities = [cls._parse_entity(
                entity, 3) for entity in data['Blocks']['BlockEntities']]
        if 'Biomes' in data:
            schematic._biome_palette.set_palette(data['Biomes']['Palette'])
            schematic._biome_data = utils.varint_bytearray_to_numpy_array(
                data['Biomes']['Data'], shape)
        if 'Entities' in data:
            schematic._entities = [cls._parse_entity(
                entity, 3) for entity in data['Entities']]

        return schematic

    @classmethod
    def _parse_file(cls, file: File) -> 'Schematic':
        # Attempt to retrieve the version from the top level
        version = file.get('Version')
        if version is None:
            # If not found, try to get the version from under the 'Schematic' root element
            schematic_data = file.get('Schematic')
            if schematic_data is not None:
                version = schematic_data.get('Version')

        if version is None:
            raise ValueError("Invalid schematic file: Version not found.")

        if version == 1:
            return cls._parse_file_v1(file)
        elif version == 2:
            return cls._parse_file_v2(file)
        elif version == 3:
            return cls._parse_file_v3(file)
        else:
            raise ValueError("Invalid schematic version.")

    @classmethod
    def from_file(cls, file_path: Path) -> 'Schematic':
        if not isinstance(file_path, Path):
            raise TypeError("File path must be a Path object.")
        if not file_path.exists():
            raise FileNotFoundError(f"File {file_path} does not exist.")

        if file_path.suffix != '.schem':
            raise ValueError(
                "Invalid file extension. Please use '.schem' extension.")

        file = nbtlib.load(file_path)
        return cls._parse_file(file)
