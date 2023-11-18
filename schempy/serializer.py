from pathlib import Path

from schempy.schematic import Schematic


class SchematicSaver:
    def __init__(self, schematic: Schematic):
        self.schematic = schematic

    def save(self, file_path: Path):
        raise NotImplementedError(
            "This method should be implemented by subclasses.")


class Version1Saver(SchematicSaver):
    def save(self, file_path: Path):
        raise NotImplementedError(
            "Saving for Version 1 schematics is not supported.")


class Version2Saver(SchematicSaver):
    def save(self, file_path: Path):
        raise NotImplementedError(
            "Saving for Version 2 schematics is not supported.")


class Version3Saver(SchematicSaver):
    def save(self, file_path: Path):
        # Implement the saving logic for version 3 schematics
        # This is where you would convert the schematic's data into the format
        # required by version 3 and then write it to the file.
        pass


class SchematicSaverFactory:
    @staticmethod
    def get_saver(schematic: 'Schematic', version: int):
        savers = {
            1: Version1Saver,
            2: Version2Saver,
            3: Version3Saver
        }
        saver_class = savers.get(version, SchematicSaver)
        return saver_class(schematic)
