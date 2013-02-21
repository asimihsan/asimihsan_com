import os
import yaml

class ParsedConfig(object):
    def __init__(self, config_filepath):
        with open(config_filepath) as f:
            config = yaml.safe_load(f)
        current_directory = os.path.abspath(os.path.join(config_filepath, os.pardir))
        self._web_directory = os.path.abspath(os.path.join(current_directory, config["web_directory"]))
        self._build_directory = os.path.abspath(os.path.join(current_directory, config["build_directory"]))
        self._templates_directory = os.path.abspath(os.path.join(current_directory, config["templates_directory"]))
        self._header_template = config["header_template"]
        self._footer_template = config["footer_template"]
        self._yuicompress_path = os.path.abspath(config["yuicompress_path"])
        self._pandoc_path = os.path.abspath(config["pandoc_path"])
        self._s3_bucket = config["s3_bucket"]
        self._manifest_filename = config["manifest_filename"]

        self._notes_build_directory = os.path.abspath(os.path.join(current_directory, config["notes_build_directory"]))
        self._notes_source_directory = os.path.abspath(os.path.join(current_directory, config["notes_source_directory"]))
        self._notes_s3_bucket = config["notes_s3_bucket"]
        self._notes_input_to_output = config["notes_input_to_output"]

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

    @property
    def templates_directory(self):
        return self._templates_directory

    @property
    def header_template_path(self):
        return os.path.abspath(os.path.join(self._templates_directory, self._header_template))

    @property
    def footer_template_path(self):
        return os.path.abspath(os.path.join(self._templates_directory, self._footer_template))

    # -------------------------------------------------------------------------
    #   upload_notes properties.
    # -------------------------------------------------------------------------
    @property
    def notes_build_directory(self):
        return self._notes_build_directory

    @property
    def notes_source_directory(self):
        return self._notes_source_directory

    @property
    def notes_s3_bucket(self):
        return self._notes_s3_bucket

    @property
    def notes_input_to_output(self):
        output = {}
        for elem in self._notes_input_to_output:
            output.update(elem)
        return output

