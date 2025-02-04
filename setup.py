from setuptools import find_packages, setup

from bids.version import VERSION

# Copyright (C) 2024 APH10 Limited
# SPDX-License-Identifier: Apache-2.0


with open("README.md", encoding="utf-8") as f:
    readme = f.read()

with open("requirements.txt", encoding="utf-8") as f:
    requirements = f.read().split("\n")

setup_kwargs = dict(
    name="bids-analyser",
    version=VERSION,
    description="Analyser for ELF files",
    long_description=readme,
    long_description_content_type="text/markdown",
    url="https://github.com/aph10/BIDS",
    author="Anthony Harrison",
    author_email="anthony@aph10.com",
    maintainer="Anthony Harrison",
    maintainer_email="anthony@aph10.com",
    license="Apache-2.0",
    keywords=["security", "tools", "ELF", "Dependency", "Symbols", "Binary Analsyis"],
    install_requires=requirements,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
    ],
    python_requires=">=3.9",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "bids-analyser = bids.cli:main",
            "sbom4bids = bids.sbom4bids:main",
            "bids-search = bids.search:main",
            "bids-scan = bids.scan:main"
        ],
    },
)

setup(**setup_kwargs)
