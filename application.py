#!/usr/bin/env python

# Adding the current directory to the Python path is easy:
import os
import sys
this_dir = os.path.dirname(__file__)
sys.path.insert(0, this_dir)

# Now that the Python path includes the current directory, any
# application specific modules can be loaded just like this was
# in main.py.
#
# For example below is an application library used to add
# the virtualenv's site packages to the Python execution
# environment.
from lib.environment import Environment
Environment().add_virtualenv_site_packages_to_path(__file__)

# Flask supports the Python standard library's logging handlers
# and provides a method to attach a logger to the app.
#
# Here's the simplest example using the logging.FileHandler.
from app import app as application
if not application.debug:
    import logging
    this_dir = os.path.dirname(__file__)
    log_file = os.path.join(this_dir, 'production.log')
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.WARNING)
    application.logger.addHandler(file_handler)

