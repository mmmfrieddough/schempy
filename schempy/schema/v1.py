from nbtlib import (ByteArray, Compound, Int, IntArray, List, Short, String,
                    schema)

TileEntity = schema('TileEntity', {
    'ContentVersion': Int,
    'Pos': IntArray,
    'Id': String
}, strict=True)

SpongeV1 = schema('Sponge', {
    'Version': Int,
    'Metadata': Compound,
    'Width': Short,
    'Height': Short,
    'Length': Short,
    'Offset': IntArray,
    'PaletteMax': Int,
    'Palette': Compound,
    'BlockData': ByteArray,
    'TileEntities': List[TileEntity]
}, strict=True)
