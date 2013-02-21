import os
import sys
import re
import gzip
import hashlib
import contextlib

# -----------------------------------------------------------------------------
#   Constants.
# -----------------------------------------------------------------------------
RE_HTML_CSS_JS = re.compile(".*\.(html|css|js)$")
RE_HTML = re.compile(".*\.html$")
RE_MARKDOWN = re.compile(".*\.(md|markdown)$")
# -----------------------------------------------------------------------------

def generator_for_filepaths_in_directory(regexp, directory):
    for root, dirs, files in os.walk(directory):
        for filename in files:
            filepath = os.path.join(root, filename)
            if not regexp.search(filepath):
                continue
            yield filepath

def calculate_hash(filepath, algorithm=hashlib.md5, length=16*1024):
    m = algorithm()
    with open(filepath) as f_in:
        while True:
            buf = f_in.read(length)
            if not buf:
                break
            m.update(buf)
    return m.hexdigest()

def is_gzip_file(filepath):
    try:
        with contextlib.closing(gzip.open(filepath, "rb")) as f_in:
            f_in.readline()
    except IOError:
        return False
    else:
        return True

def compress_file_inplace(filepath):
    with open(filepath) as f_in:
        contents = f_in.read()
    with contextlib.closing(gzip.open(filepath, "wb")) as f_out:
        f_out.write(contents)

