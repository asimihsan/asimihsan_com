import os
import yaml

class ParsedConfig(object):
    def __init__(self, config_filepath):
        with open(config_filepath) as f:
            config = yaml.safe_load(f)
        current_directory = os.path.abspath(os.path.join(config_filepath, os.pardir))
        self._source_directory = os.path.abspath(os.path.join(current_directory, config["source_directory"]))
        self._build_directory = os.path.abspath(os.path.join(current_directory, config["build_directory"]))

    @property
    def source_directory(self):
        return self._source_directory

    @property
    def build_directory(self):
        return self._build_directory

