# Copyright (C) 2024 APH10 Limited
# SPDX-License-Identifier: Apache-2.0

# import hashlib
import os
from pathlib import Path

import bids.util as util
from bids.elf_utils import BIDSElf


class BIDSAnalyser:

    COMMAND_TIMEOUT = 5  # Seconds

    def __init__(self, options={}, description="", debug=False):
        self.filename = None
        self.options = options
        self.header = []
        self.global_symbols = []
        self.local_symbols = []
        self.dependencies = []
        self.callgraph = []
        self.application = {}
        self.description = description
        self.debug = debug

    def check_file(self, filename: str) -> None:
        """Check file exists

        Parameters
        ----------
        filename : string
            The filename of the binary file
        """
        # Check file exists
        invalid_file = True
        if len(filename) > 0:
            # Check path
            filePath = Path(filename)
            # Check path exists, a valid file and not empty file
            if filePath.exists() and filePath.is_file() and filePath.stat().st_size > 0:
                # Assume that processing can proceed
                invalid_file = False

        if invalid_file:
            raise FileNotFoundError
        self.filename = os.path.realpath(filename)
        # Store some relevant info related to file
        # self.application["size"] = filePath.stat().st_size
        # self.application["date"] = time.ctime(filePath.stat().st_mtime)
        self.application["location"] = self.filename
        # Calculate checksum and assoicated file data
        checksum = util.calculate_checksum(filename)
        self.application["checksum"] = checksum
        if len(self.description) > 0:
            self.application["description"] = self.description
        # Try to find version
        app_version = self.app_version(self.filename)
        if app_version is not None:
            self.application["version"] = app_version

    def app_version(self, application):
        try:
            lines = util.run_process([application, "--version"])
            version = lines.stdout.splitlines()[0].split(" ")[-1].strip()
            if version[-1] == ".":
                version = version[:-1]
            elif version == "--version":
                version = None
            return version
        except Exception:
            # print(f"[ERROR] Unable to find version for {application}")
            return None

    def analyse(self, filename):
        self.check_file(filename)
        elf = BIDSElf(self.filename, debug=self.debug)
        self.header = elf.get_header()
        if not self.options.get("dependency", False):
            self.dependencies = elf.get_dependencies()
        if not self.options.get("symbol", False):
            self.global_symbols, self.local_symbols = elf.get_symbols()

    def get_global_symbols(self):
        return self.global_symbols

    def get_local_symbols(self):
        return self.local_symbols

    def get_dependencies(self):
        return self.dependencies

    def get_callgraph(self):
        return self.callgraph

    def get_header(self):
        return self.header

    def get_file_data(self):
        return self.application
