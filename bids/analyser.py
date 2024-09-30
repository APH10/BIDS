# Copyright (C) 2024 APH10 Limited
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path
from bids.elf_utils import BIDSElf
from bids.callgraph import BIDSGraph
import os

class BIDSAnalyser:

    def __init__(self, options = {}):
        self.filename = None
        self.options = options
        self.global_symbols = []
        self.local_symbols = []
        self.dependencies = []

    def check_file(self, filename: str) -> None:
        """Parses a SBOM file

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

    def analyse(self, filename):
        self.check_file(filename)
        elf = BIDSElf(self.filename)
        if not self.options.get("dependency",False):
            self.dependencies = elf.get_dependencies()
        if not self.options.get("symbols",False):
            self.global_symbols, self.local_symbols = elf.get_symbols()


    def get_global_symbols(self):
        return self.global_symbols

    def get_local_symbols(self):
        return self.local_symbols

    def get_dependencies(self):
        return self.dependencies
