#!/usr/bin/env python

import os
import sys
import subprocess
import shutil
import re
import boto
import contextlib
from glob import glob
import posixpath
import jinja2
import gzip

from ParsedConfig import ParsedConfig
from utilities import generator_for_filepaths_in_directory, \
                      RE_HTML, RE_HTML_CSS_JS, RE_MARKDOWN, \
                      calculate_hash,                       \
                      is_gzip_file                          \

# -----------------------------------------------------------------------------
#   Constants.
# -----------------------------------------------------------------------------
APP_NAME = "compress_combine"
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

def copy_web_to_build(config):
    logger = logging.getLogger("%s.copy_web_to_build" % APP_NAME)
    logger.debug("entry. config.web_directory: %s, config.build_directory: %s" % (config.web_directory, config.build_directory))

    # -------------------------------------------------------------------------
    #   Copy a fresh copy of the web directory to the build directory.
    # -------------------------------------------------------------------------
    if os.path.isdir(config.build_directory):
        shutil.rmtree(config.build_directory)
    shutil.copytree(config.web_directory, config.build_directory)
    # -------------------------------------------------------------------------

def fill_templates_in_build(config):
    logger = logging.getLogger("%s.fill_templates_in_build" % APP_NAME)
    logger.debug("entry. config.build_directory: %s" % config.build_directory)

    # -------------------------------------------------------------------------
    #   Validate assumptions.
    # -------------------------------------------------------------------------
    assert(os.path.isdir(config.templates_directory))
    assert(os.path.isfile(config.header_template_path))
    assert(os.path.isfile(config.footer_template_path))
    # -------------------------------------------------------------------------

    # -------------------------------------------------------------------------
    #   HTML files are all jinja2 templates. Fill in header and footer.
    # -------------------------------------------------------------------------
    with open(config.header_template_path) as f_in:
        header_contents = f_in.read()
    with open(config.footer_template_path) as f_in:
        footer_contents = f_in.read()
    for filepath in generator_for_filepaths_in_directory(RE_HTML, config.build_directory):
        logger.debug("rendering: '%s'" % filepath)
        with open(filepath) as f_in:
            template = jinja2.Template(f_in.read())
        output = template.render(header = header_contents,
                                 footer = footer_contents)
        with open(filepath, "w") as f_out:
            f_out.write(output)
    # -------------------------------------------------------------------------

def compress_files_in_build_directory(config):
    logger = logging.getLogger("%s.compress_files_in_build_directory" % APP_NAME)
    logger.debug("entry. config.build_directory: %s" % config.build_directory)

    RE_HTML = re.compile(".*\.(html|js|css)$")

    for root, dirs, files in os.walk(config.build_directory):
        for filename in files:
            filepath = os.path.join(root, filename)
            if not RE_HTML.search(filepath):
                continue
            logger.info("gzipping file: '%s'" % filepath)
            with open(filepath) as f_in:
                contents = f_in.read()
            with contextlib.closing(gzip.open(filepath, "wb")) as f_out:
                f_out.write(contents)

def upload_build_directory_to_s3(config):
    logger = logging.getLogger("%s.upload_build_directory_to_s3" % APP_NAME)
    logger.debug("entry. config.build_directory: %s, config.s3_bucket: %s" % (config.build_directory, config.s3_bucket))

    with contextlib.closing(boto.connect_s3()) as conn:
        with contextlib.closing(boto.connect_cloudfront()) as conn_cloudfront:
            cloudfront_distribution = [elem for elem in conn_cloudfront.get_all_distributions() if config.s3_bucket in elem.origin.dns_name][0]
            cloudfront_distribution = cloudfront_distribution.get_distribution()
            all_subpaths = []

            bucket = conn.get_bucket(config.s3_bucket)
            manifest_key = bucket.get_key(config.manifest_filename)
            existing_manifest_hashes = {}
            if not manifest_key:
                logger.debug("manifest does not exist, upload everything.")
            else:
                logger.debug("manifest exists, may be duplicate files.")
                manifest_contents = manifest_key.get_contents_as_string()
                for line in manifest_contents.splitlines():
                    (subpath, digest) = line.strip().split()
                    existing_manifest_hashes[subpath] = digest

            build_path_length = len(config.build_directory.split(os.sep))
            for root, dirs, files in os.walk(config.build_directory):
                for filename in files:
                    filepath = os.path.join(root, filename)
                    subpath = posixpath.join(*filepath.split(os.sep)[build_path_length:])
                    digest = calculate_hash(filepath)
                    if existing_manifest_hashes.get(subpath, None) == digest:
                        logger.debug("file '%s' already exists and is identical, skipping." % subpath)
                        continue
                    logger.debug("uploading subpath '%s'" % subpath)
                    all_subpaths.append(subpath)
                    key = bucket.delete_key(subpath)
                    key = bucket.new_key(subpath)
                    if is_gzip_file(filepath):
                        logger.debug("mark as a gzipped file")
                        key.set_metadata("Content-Encoding", "gzip")
                    key.set_contents_from_filename(filepath)
                    key.make_public()

            logger.debug("creating cloudfront invalidation request")
            conn_cloudfront.create_invalidation_request(cloudfront_distribution.id, all_subpaths)

def generate_manifest_file_for_build_directory(config):
    logger = logging.getLogger("%s.generate_manifest_file_for_build_directory" % APP_NAME)
    logger.debug("entry. config.build_directory: %s, config.manifest_filename: %s" % (config.build_directory, config.manifest_filename))

    manifest_path = os.path.join(config.build_directory, config.manifest_filename)
    logger.debug("manifest_path: %s" % manifest_path)
    build_path_length = len(config.build_directory.split(os.sep))
    with open(manifest_path, "w") as f_out:
        for root, dirs, files in os.walk(config.build_directory):
            for filename in files:
                filepath = os.path.join(root, filename)
                subpath = posixpath.join(*filepath.split(os.sep)[build_path_length:])
                digest = calculate_hash(filepath)
                logger.debug("subpath: %s, digest: %s" % (subpath, digest))
                f_out.write("%s\t%s\n" % (subpath, digest))

def main():
    logger = logging.getLogger("%s.main" % APP_NAME)
    logger.debug("entry.")

    # -------------------------------------------------------------------------
    #   Validate assumptions.
    # -------------------------------------------------------------------------
    assert(os.path.isfile(CONFIG_FILEPATH))
    # -------------------------------------------------------------------------

    config = ParsedConfig(CONFIG_FILEPATH)
    copy_web_to_build(config)
    fill_templates_in_build(config)
    compress_files_in_build_directory(config)
    generate_manifest_file_for_build_directory(config)
    upload_build_directory_to_s3(config)

if __name__ == "__main__":
    main()
