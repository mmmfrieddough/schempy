from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import nbtlib
import numpy as np
from nbtlib import Compound, File

from schempy.constants import DATA_VERSION, MINECRAFT_AIR
from schempy.schema.v2 import SpongeV2
from schempy.schema.v3 import SpongeV3
import schempy.utils as utils


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
            f"{key}={value}" for key, value in self.properties.items()) if self.properties else ''
        return f"{self.id}[{properties_str}]" if properties_str else self.id


@dataclass(frozen=True)
class BlockEntity:
    id: str
    x: int
    y: int
    z: int
    properties: Dict[str, str] = None


class Palette:
    def __init__(self):
        self._block_to_index: Dict[Block, int] = {}
        self._index_to_block: List[Block] = []

    def set_palette(self, palette: Dict[str, int]) -> None:
        # Parse each string into a Block object
        for block_str, index in palette.items():
            if '[' in block_str:
                id, properties_str = block_str.split('[')
                properties_str = properties_str[:-1]
                properties = {}
                for property_str in properties_str.split(','):
                    key, value = property_str.split('=')
                    properties[key] = value
                block = Block(id, properties)
            else:
                block = Block(block_str)
            self._block_to_index[block] = index
            self._index_to_block.append(block)

    def get_palette(self) -> Dict[str, int]:
        return {str(block): index for block, index in self._block_to_index.items()}

    def get_id(self, block: Block) -> int:
        if block not in self._block_to_index:
            self._block_to_index[block] = len(self._index_to_block)
            self._index_to_block.append(block)
        return self._block_to_index[block]

    def get_block(self, index: int) -> Block:
        return self._index_to_block[index]


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

        self._block_palette: Palette = Palette()
        self._block_palette.get_id(Block(MINECRAFT_AIR))
        self._block_data: np.ndarray = np.zeros(
            (self._length, self._height, self._width), dtype=int)
        self._block_entities: List[BlockEntity] = []
        self._biome_palette: Palette = Palette()
        self._biome_data: np.ndarray = np.zeros(
            (self._length, self._height, self._width), dtype=int)
        self._entities: List[Compound] = []

    def _check_coordinates(self, x: int, y: int, z: int) -> None:
        """Check that the coordinates are within the schematic bounds."""
        if not (0 <= x < self._width and 0 <= y < self._height and 0 <= z < self._length):
            raise ValueError("Coordinates out of range.")

    def get_block(self, x: int, y: int, z: int) -> Block:
        """Get the block at the specified coordinates."""
        self._check_coordinates(x, y, z)
        return self._block_palette.get_block(self._block_data[x, y, z])

    def set_block(self, x: int, y: int, z: int, block: Block):
        """Set the block at the specified coordinates."""
        self._check_coordinates(x, y, z)
        self._block_data[x, y, z] = self._block_palette.get_id(block)

    def add_block_entity(self, block_entity: BlockEntity):
        """Add a block entity."""
        self._check_coordinates(block_entity.x, block_entity.y, block_entity.z)
        self._block_entities.append(block_entity)

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

    def _save_to_file_v1(self) -> Dict:
        raise NotImplementedError(
            "Version 1 schematics are not supported.")

    def _save_to_file_v2(self) -> Dict:
        return SpongeV2(
            Version=2,
            DataVersion=self._data_version,
            Metadata={key: nbtlib.String(value)
                      for key, value in self._metadata.items()},
            Width=self._width,
            Height=self._height,
            Length=self._length,
            Offset=self._offset,
            PaletteMax=len(self._block_palette.get_palette()),
            Palette={key: nbtlib.Int(
                value) for key, value in self._block_palette.get_palette().items()},
            BlockData=self._block_data.reshape(
                (self._length*self._height*self._width, 1)),
            BlockEntities=nbtlib.List(),
            Entities=nbtlib.List(),
            BiomePaletteMax=len(self._block_palette.get_palette()),
            BiomePalette={key: nbtlib.Int(
                value) for key, value in self._block_palette.get_palette().items()},
            BiomeData=self._biome_data.reshape(
                (self._length*self._height*self._width, 1))
        )

    def _save_to_file_v3(self) -> Dict:
        # Get data ready
        metadata = self._prepare_metadata()
        block_palette = {key: nbtlib.Int(
            value) for key, value in self._block_palette.get_palette().items()}
        block_data = utils.numpy_array_to_varint_bytearray(self._block_data)
        block_entities = [{'Pos': [entity.x, entity.y, entity.z], 'Id': entity.id, 'Data': {key: nbtlib.String(
            value) for key, value in entity.properties.items()}} for entity in self._block_entities]
        biome_palette = {key: nbtlib.Int(
            value) for key, value in self._biome_palette.get_palette().items()}
        biome_data = utils.numpy_array_to_varint_bytearray(self._biome_data)
        entities = nbtlib.List()

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

        return data

    def save_to_file(self, file_path: Path, version: int = 3) -> None:
        if not file_path.parent.exists():
            raise FileNotFoundError(
                f"Directory {file_path.parent} does not exist.")

        if file_path.suffix != '.schem':
            raise ValueError(
                "Invalid file extension. Please use '.schem' extension.")

        # Create the data dictionary
        if version == 1:
            data = self._save_to_file_v1()
        elif version == 2:
            data = self._save_to_file_v2()
        elif version == 3:
            data = self._save_to_file_v3()
        else:
            raise ValueError("Invalid schematic version.")

        # Save the data to the file
        file = nbtlib.File(data)
        file.save(file_path, gzipped=True)

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
            schematic.offset = data['Offset']
            schematic.data_version = data['DataVersion']
        except KeyError:
            raise ValueError("Invalid schematic file.")

        # Get the optional fields
        if 'Metadata' in data:
            schematic.metadata = data['Metadata']
        shape = (schematic._length, schematic._height, schematic._width)
        if 'Palette' in data:
            schematic._block_palette.set_palette(data['Palette'])
        if 'BlockData' in data:
            schematic._block_data = utils.varint_bytearray_to_numpy_array(
                data['BlockData'], shape)
        if 'BiomeData' in data:
            schematic._biome_data = utils.varint_bytearray_to_numpy_array(
                data['BiomeData'], shape)

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
            schematic.offset = data['Offset']
            schematic.data_version = data['DataVersion']
        except KeyError:
            raise ValueError("Invalid schematic file.")

        # Get the optional fields
        if 'Metadata' in data:
            schematic.metadata = data['Metadata']
        shape = (schematic._length, schematic._height, schematic._width)
        if 'Blocks' in data:
            schematic._block_palette.set_palette(data['Blocks']['Palette'])
            schematic._block_data = utils.varint_bytearray_to_numpy_array(
                data['Blocks']['Data'], shape)
        if 'Biomes' in data:
            schematic._block_palette.set_palette(data['Biomes']['Palette'])
            schematic._biome_data = utils.varint_bytearray_to_numpy_array(
                data['Biomes']['Data'], shape)
        if 'Entities' in data:
            schematic._entities = data['Entities']

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
        if not file_path.exists():
            raise FileNotFoundError(f"File {file_path} does not exist.")

        if file_path.suffix != '.schem':
            raise ValueError(
                "Invalid file extension. Please use '.schem' extension.")

        file = nbtlib.load(file_path)
        return cls._parse_file(file)
