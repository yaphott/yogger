#!/usr/bin/env python

import sys
import os


REQUIRED_PYTHON = (3, 9)
CURRENT_PYTHON = sys.version_info[:2]

if CURRENT_PYTHON < REQUIRED_PYTHON:
    sys.stderr.write(
        """
==========================
Unsupported Python version
==========================
This version of Yogger requires at least Python {}.{}, but you're trying to install it on Python {}.{}.
""".format(
            *(REQUIRED_PYTHON + CURRENT_PYTHON)
        )
    )
    sys.exit(1)

here = os.path.abspath(os.path.dirname(__file__))

if sys.argv[-1] == "publish":
    # Publish to PyPi
    status = os.system("python3 -m build")
    if status == 0:
        status = os.system("twine upload dist/yogger-*.tar.gz dist/yogger-*.whl")
    sys.exit(status)
elif sys.argv[-1] == "test":
    # Run tests
    import unittest

    # Default shared TestLoader instance
    test_loader = unittest.defaultTestLoader
    # Basic test runner that outputs to sys.stderr
    test_runner = unittest.TextTestRunner()
    # Discover all tests
    test_suite = test_loader.discover(os.path.join(here, "tests"))
    # Run the test suite
    test_runner.run(test_suite)
else:
    # Legacy install
    from setuptools import setup

    setup()
