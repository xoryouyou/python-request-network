import subprocess
import sys

import setuptools
from setuptools.command.install import (
    install,
)

VERSION = "0.0.2"


with open("README.rst", "r") as fh:
    long_description = fh.read()


class VerifyVersionCommand(install):
    """Custom command to verify that the git tag matches our version"""
    description = 'verify that the git tag matches our version'

    def run(self):
        tag = subprocess.check_output(['git', 'describe', '--tags']).decode().rstrip('\n')

        if tag != 'v{}'.format(VERSION):
            info = "Git tag: {0} does not match the version of this app: {1}".format(
                tag, VERSION
            )
            sys.exit(info)


setuptools.setup(
    name="request-network",
    version=VERSION,
    author="Mike Ryan",
    author_email="mike@backtothelab.io",
    description="Python library for Request Network",
    entry_points={
        'console_scripts': [
            'request-network-qr-code = request_network.scripts.create_qr_code:main',
        ]
    },
    install_requires=[
        # TODO better version pinning
        "web3==4.4.1",
        "PyQRCode==1.2.1",
        "pypng==0.0.18",
        "eth-account==0.2.3",
        "ipfsapi==0.4.3"
    ],
    long_description=long_description,
    url="https://github.com/mikery/python-request-network",
    packages=setuptools.find_packages(exclude=["tests", "tests.*"]),
    include_package_data=True,
    classifiers=(
        "Development Status :: 2 - Pre-Alpha",
        "Programming Language :: Python :: 3",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ),
    cmdclass={
        'verify_git_tag': VerifyVersionCommand,
    }
)
