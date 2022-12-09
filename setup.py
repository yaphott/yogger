#!/usr/bin/env python

import sys
import os
import setuptools


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


def _globals_from_py(filepath: str) -> dict:
    __globals = {}
    with open(filepath, mode="r", encoding="utf-8") as rf:
        exec(rf.read(), __globals)

    return __globals


here = os.path.abspath(os.path.dirname(__file__))
version = _globals_from_py(os.path.join(here, "yogger", "__version__.py"))
with open(os.path.join(here, "README.md"), mode="r", encoding="utf-8") as rf:
    long_description = rf.read()


# Publish to PyPi using 'python3 setup.py publish'
if sys.argv[-1] == "publish":
    os.system("python3 setup.py sdist bdist_wheel")
    os.system("twine upload dist/yogger-*.tar.gz dist/yogger-*.whl")
    sys.exit()


# Run tests
if sys.argv[-1] == "test":
    import unittest

    # Default shared TestLoader instance
    test_loader = unittest.defaultTestLoader
    # Basic test runner that outputs to sys.stderr
    test_runner = unittest.TextTestRunner()
    # Discover all tests
    test_suite = test_loader.discover(os.path.join(here, "tests"))
    # Run the test suite
    test_runner.run(test_suite)

setuptools.setup(
    name=version["__title__"],
    version=version["__version__"],
    author=version["__author__"],
    author_email=version["__author_email__"],
    description=version["__description__"],
    long_description=long_description,
    long_description_content_type="text/markdown",
    url=version["__url__"],
    packages=["yogger"],
    package_data={"": ["LICENSE", "NOTICE"]},
    package_dir={"yogger": "yogger"},
    include_package_data=True,
    python_requires=">=3.9, <4",
    install_requires=[],
    license=version["__license__"],
    zip_safe=False,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3 :: Only",
        "Topic :: Utilities",
        "Topic :: System :: Logging",
        "Topic :: Software Development",
        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    extras_require={},
    entry_points={},
    keywords=["logging", "inspect", "trace", "stack", "dump", "dumps", "locals", "yogger"],
    project_urls={
        "Homepage": "https://github.com/yaphott/yogger",
    },
    setup_requires=["setuptools>=42", "wheel"],
)
