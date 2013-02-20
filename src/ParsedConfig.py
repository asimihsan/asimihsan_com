import os
import yaml

class ParsedConfig(object):
    def __init__(self, config_filepath):
        with open(config_filepath) as f:
            config = yaml.safe_load(f)
        current_directory = os.path.abspath(os.path.join(config_filepath, os.pardir))
        self._web_directory = os.path.abspath(os.path.join(current_directory, config["web_directory"]))
        self._build_directory = os.path.abspath(os.path.join(current_directory, config["build_directory"]))
        self._yuicompress_path = os.path.abspath(config["yuicompress_path"])
        self._pandoc_path = os.path.abspath(config["pandoc_path"])
        self._s3_bucket = config["s3_bucket"]
        self._manifest_filename = config["manifest_filename"]

    @property
    def web_directory(self):
        return self._web_directory

    @property
    def build_directory(self):
        return self._build_directory

    @property
    def yuicompress_path(self):
        return self._yuicompress_path

    @property
    def pandoc_path(self):
        return self._pandoc_path

    @property
    def s3_bucket(self):
        return self._s3_bucket

    @property
    def manifest_filename(self):
        return self._manifest_filename

