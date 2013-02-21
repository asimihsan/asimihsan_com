#!/usr/bin/env python

import os
import sys
import subprocess
import shutil
import re
import gzip
import boto
import contextlib
import hashlib
from glob import glob
import posixpath
import jinja2

from ParsedConfig import ParsedConfig

# -----------------------------------------------------------------------------
#   Constants.
# -----------------------------------------------------------------------------
APP_NAME = "upload_notes"
CONFIG_DIRECTORY = os.path.abspath(os.path.join(__file__, os.pardir))
CONFIG_FILEPATH = os.path.join(CONFIG_DIRECTORY, "config.yaml")
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
#   Logging.
# -----------------------------------------------------------------------------
import logging
import logging.handlers
logger = logging.getLogger(APP_NAME)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)
# -----------------------------------------------------------------------------

def build_notes(config):
    logger = logging.getLogger("%s.build_notes" % APP_NAME)
    logger.debug("entry.")

    import ipdb; ipdb.set_trace()
    pass

def main():
    logger = logging.getLogger("%s.main" % APP_NAME)
    logger.debug("entry.")

    # -------------------------------------------------------------------------
    #   Validate assumptions.
    # -------------------------------------------------------------------------
    assert(os.path.isfile(CONFIG_FILEPATH))
    # -------------------------------------------------------------------------

    config = ParsedConfig(CONFIG_FILEPATH)
    build_notes(config)
    #copy_web_to_build(config)
    #fill_templates_in_build(config)
    #compress_files_in_build_directory(config)
    #generate_manifest_file_for_build_directory(config)
    #upload_build_directory_to_s3(config)

if __name__ == "__main__":
    main()
