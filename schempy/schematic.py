from dataclasses import dataclass
from datetime import datetime
from itertools import product
from pathlib import Path
from typing import Dict, Generic, List, Optional, TypeVar

import nbtlib
import numpy as np
from nbtlib import File

import schempy.utils as utils
from schempy.constants import DATA_VERSION, MINECRAFT_AIR
from schempy.schema.v2 import SpongeV2
from schempy.schema.v3 import SpongeV3


@dataclass(frozen=True)
class Block:
    id: str
    properties: Optional[Dict[str, str]] = None

    def __hash__(self):
        # Compute the hash based on a tuple of the ID and sorted properties items
        properties_items = tuple(
            sorted(self.properties.items())) if self.properties else ()
        return hash((self.id, properties_items))

    def __eq__(self, other):
        if not isinstance(other, Block):
            return NotImplemented
        return self.id == other.id and self.properties == other.properties

    def __str__(self):
        properties_str = ','.join(
            f"{key}={str(value).lower() if isinstance(value, bool) else value}" for key, value in self.properties.items()) if self.properties else ''
        return f"{self.id}[{properties_str}]" if properties_str else self.id


@dataclass(frozen=True)
class Entity:
    id: str
    x: float
    y: float
    z: float
    properties: Dict[str, str] = None


T = TypeVar('T')


class Palette(Generic[T]):
    def __init__(self):
        self._item_to_index: Dict[T, int] = {}
        self._index_to_item: List[T] = []

    def clear(self) -> None:
        self._item_to_index.clear()
        self._index_to_item.clear()

    def set_palette(self, palette: Dict[T, int]) -> None:
        self.clear()
        self._item_to_index = palette
        self._index_to_item = [None] * len(palette)
        for item, index in palette.items():
            self._index_to_item[index] = item

    def get_palette(self) -> Dict[T, int]:
        return self._item_to_index

    def get_id(self, item: T) -> int:
        if item not in self._item_to_index:
            self._item_to_index[item] = len(self._index_to_item)
            self._index_to_item.append(item)
        return self._item_to_index[item]

    def get_item(self, index: int) -> T:
        return self._index_to_item[index]


class BlockPalette(Palette[Block]):
    def set_palette(self, palette: Dict[str, int]) -> None:
        self.clear()
        # Parse each string into a Block object
        for block_str, index in palette.items():
            block = self._parse_block_str(block_str)
            self._item_to_index[block] = index
            self._index_to_item.append(block)

    @staticmethod
    def _parse_block_str(block_str: str) -> Block:
        if '[' in block_str:
            id, properties_str = block_str.split('[')
            properties_str = properties_str[:-1]
            properties = {}
            for property_str in properties_str.split(','):
                key, value = property_str.split('=')
                properties[key] = value
            return Block(id, properties)
        else:
            return Block(block_str)


class Schematic:
    def __init__(self, width: int, height: int, length: int):
        self._width: int = utils.to_unsigned_short(width)
        self._height: int = utils.to_unsigned_short(height)
        self._length: int = utils.to_unsigned_short(length)

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
            (self._height, self._length, self._width), dtype=int)
        self._block_entities: List[Entity] = []
        self._biome_palette: Palette = Palette()
        self._biome_data: np.ndarray = np.zeros(
            (self._height, self._length, self._width), dtype=int)
        self._entities: List[Entity] = []

    def _check_coordinates(self, x: int, y: int, z: int) -> None:
        """Check that the coordinates are within the schematic bounds."""
        if not (0 <= x < self._width and 0 <= y < self._height and 0 <= z < self._length):
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
        return product(range(self._width), range(self._height), range(self._length))

    def _prepare_metadata(self) -> Dict:
        """Prepare the metadata for saving."""
        metadata = {key: nbtlib.String(value)
                    for key, value in self.metadata.items()}
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
            'Width': self._width,
            'Height': self._height,
            'Length': self._length,
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
                'Width': self._width,
                'Height': self._height,
                'Length': self._length,
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
            shape = (schematic._height, schematic._length, schematic._width)
            schematic._block_data = utils.varint_bytearray_to_numpy_array(
                data['BlockData'], shape)
        if 'BlockEntities' in data:
            schematic._block_entities = [cls._parse_entity(
                entity, 2) for entity in data['BlockEntities']]
        if 'BiomeData' in data:
            schematic._biome_palette.set_palette(data['BiomePalette'])
            # Since version 2 schematics store biome data as a 2D array, we need to convert it to a 3D array
            shape = (schematic._length, schematic._width)
            biome_data = utils.varint_bytearray_to_numpy_array(
                data['BiomeData'], shape)
            schematic._biome_data = np.repeat(
                biome_data[np.newaxis, :, :], schematic._height, axis=0)
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
        shape = (schematic._height, schematic._length, schematic._width)
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
