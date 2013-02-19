#!/usr/bin/env python

import os
import sys
import subprocess

from ParsedConfig import ParsedConfig

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

def main():
    logger = logging.getLogger("%s.main" % APP_NAME)
    logger.debug("entry.")

    # -------------------------------------------------------------------------
    #   Validate assumptions.
    # -------------------------------------------------------------------------
    assert(os.path.isfile(CONFIG_FILEPATH))
    # -------------------------------------------------------------------------

    config = ParsedConfig(CONFIG_FILEPATH)

    import ipdb; ipdb.set_trace()

if __name__ == "__main__":
    main()
