from nbtlib import (ByteArray, Compound, Double, Int, IntArray, List, Short,
                    String, schema)

BlockEntity = schema('BlockEntity', {
    'Pos': IntArray,
    'Id': String
})

Entity = schema('EntityObject', {
    'Pos': List[Double],
    'Id': String
})

SpongeV2 = schema('Sponge', {
    'Version': Int,
    'DataVersion': Int,
    'Metadata': Compound,
    'Width': Short,
    'Height': Short,
    'Length': Short,
    'Offset': IntArray,
    'PaletteMax': Int,
    'Palette': Compound,
    'BlockData': ByteArray,
    'BlockEntities': List[BlockEntity],
    'Entities': List[Entity],
    'BiomePaletteMax': Int,
    'BiomePalette': Compound,
    'BiomeData': ByteArray
}, strict=True)
