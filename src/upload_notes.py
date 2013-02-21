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
from string import Template

from ParsedConfig import ParsedConfig
from utilities import generator_for_filepaths_in_directory, \
                      RE_HTML, RE_HTML_CSS_JS, RE_MARKDOWN, \
                      calculate_hash,                       \
                      is_gzip_file,                         \
                      compress_file_inplace

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

def copy_notes_to_build(config):
    logger = logging.getLogger("%s.copy_notes_to_build" % APP_NAME)
    logger.debug("entry. config.notes_source_directory: %s" % config.notes_source_directory)

    # -------------------------------------------------------------------------
    #   Make sure the build directory exists and is empty.
    # -------------------------------------------------------------------------
    if os.path.isdir(config.notes_build_directory):
        shutil.rmtree(config.notes_build_directory)
    os.makedirs(config.notes_build_directory)
    # -------------------------------------------------------------------------

    # -------------------------------------------------------------------------
    #   Copy all required Markdown files from the source directory to the
    #   destination directory.
    # -------------------------------------------------------------------------
    all_markdown_filepaths = generator_for_filepaths_in_directory(RE_MARKDOWN, config.notes_source_directory)
    markdown_filepaths_to_copy = (filepath for filepath in all_markdown_filepaths
                                  if os.path.basename(filepath) in config.notes_input_to_output)
    for source_filepath in markdown_filepaths_to_copy:
        logger.debug("will copy: '%s'" % source_filepath)
        destination_filepath = os.path.join(config.notes_build_directory, os.path.basename(source_filepath))
        shutil.copy(source_filepath, destination_filepath)
    # -------------------------------------------------------------------------

def build_notes(config):
    logger = logging.getLogger("%s.build_notes" % APP_NAME)
    logger.debug("entry. config.notes_build_directory: %s" % config.notes_build_directory)

    for filepath in generator_for_filepaths_in_directory(RE_MARKDOWN, config.notes_build_directory):
        logger.debug("will build: '%s'" % filepath)

        # ---------------------------------------------------------------------
        #   Render the Markdown file as HTML, then compress it.
        # ---------------------------------------------------------------------
        filename = os.path.basename(filepath)
        assert(filename in config.notes_input_to_output)
        output_filepath = os.path.normpath(os.path.join(config.notes_build_directory, config.notes_input_to_output[filename]))
        os.makedirs(os.path.split(output_filepath)[0])

        cmd = Template(config.notes_pandoc_command_template).substitute(
                  input_filepath = filepath,
                  output_filepath = output_filepath,
                  header_filepath = config.header_template_path,
                  footer_filepath = config.footer_template_path,
              )
        logger.debug("executing: '%s'" % cmd)
        output = subprocess.check_output(cmd, shell=True)
        compress_file_inplace(output_filepath)
        # ---------------------------------------------------------------------

        # ---------------------------------------------------------------------
        #   And also copy CSS file there, then compress it.
        # ---------------------------------------------------------------------
        source_filepath = config.notes_css_filepath
        destination_filepath = os.path.join(os.path.split(output_filepath)[0], os.path.basename(source_filepath))
        logger.debug("copying '%s' to '%s'" % (source_filepath, destination_filepath))
        shutil.copy(source_filepath, destination_filepath)
        compress_file_inplace(destination_filepath)
        # ---------------------------------------------------------------------

def upload_notes_build_directory_to_s3(config):
    """ !!AI TODO need a manifest, and a saner way of tracking files."""

    logger = logging.getLogger("%s.upload_notes_build_directory_to_s3" % APP_NAME)
    logger.debug("entry. config.notes_build_directory: %s, config.notes_s3_bucket: %s" % (config.notes_build_directory, config.notes_s3_bucket))

    with contextlib.closing(boto.connect_s3()) as conn:
        with contextlib.closing(boto.connect_cloudfront()) as conn_cloudfront:
            cloudfront_distribution = [elem for elem in conn_cloudfront.get_all_distributions() if config.s3_bucket in elem.origin.dns_name][0]
            cloudfront_distribution = cloudfront_distribution.get_distribution()
            bucket = conn.get_bucket(config.notes_s3_bucket)

            output_subpaths = []
            for subpath in sorted(config.notes_input_to_output.values()):
                posix_subpath = posixpath.join(*subpath.split(os.sep))
                posix_subdirectory = posixpath.split(posix_subpath)[0]
                output_subpaths.append(subpath)
                output_subpaths.append(posixpath.join(posix_subdirectory, "_pandoc.css"))
            output_filepaths = [os.path.normpath(os.path.join(config.notes_build_directory, subpath)) for subpath in output_subpaths]

            for (subpath, filepath) in zip(output_subpaths, output_filepaths):
                logger.debug("uploading subpath: '%s'" % subpath)
                key = bucket.delete_key(subpath)
                key = bucket.new_key(subpath)
                if is_gzip_file(filepath):
                    logger.debug("mark as a gzipped file")
                    key.set_metadata("Content-Encoding", "gzip")
                key.set_contents_from_filename(filepath)
                key.make_public()

            logger.debug("creating cloudfront invalidation request")
            conn_cloudfront.create_invalidation_request(cloudfront_distribution.id, output_subpaths)

def main():
    logger = logging.getLogger("%s.main" % APP_NAME)
    logger.debug("entry.")

    # -------------------------------------------------------------------------
    #   Validate assumptions.
    # -------------------------------------------------------------------------
    assert(os.path.isfile(CONFIG_FILEPATH))
    # -------------------------------------------------------------------------

    config = ParsedConfig(CONFIG_FILEPATH)
    copy_notes_to_build(config)
    build_notes(config)
    upload_notes_build_directory_to_s3(config)

if __name__ == "__main__":
    main()
