from nbtlib import (ByteArray, Compound, Double, Int, IntArray, List, Short,
                    String, schema)

BlockEntity = schema('BlockEntity', {
    'Pos': IntArray,
    'Id': String,
    'Data': Compound
}, strict=True)

BlockContainer = schema('BlockContainer', {
    'Palette': Compound,
    'Data': ByteArray,
    'BlockEntities': List[BlockEntity]
}, strict=True)

BiomeContainer = schema('BiomeContainer', {
    'Palette': Compound,
    'Data': ByteArray,
}, strict=True)

Entity = schema('EntityObject', {
    'Pos': List[Double],
    'Id': String,
    'Data': Compound
}, strict=True)

SpongeV3 = schema('Sponge', {
    'Schematic': schema('Schematic', {
        'Version': Int,
        'DataVersion': Int,
        'Metadata': Compound,
        'Width': Short,
        'Height': Short,
        'Length': Short,
        'Offset': IntArray,
        'Blocks': BlockContainer,
        'Biomes': BiomeContainer,
        'Entities': List[Entity]
    })
}, strict=True)
