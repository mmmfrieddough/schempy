from dataclasses import dataclass
from typing import Dict, Generic, List, Optional, TypeVar


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
                if property_str == '':
                    continue
                key, value = property_str.split('=')
                properties[key] = value
            return Block(id, properties)
        else:
            return Block(block_str)
