# Copyright (C) 2024 APH10 Limited
# SPDX-License-Identifier: Apache-2.0

import os
from pathlib import Path

import bids.util as util


class DynamicLibrary:

    def __init__(self, cache=None, library_path=""):
        self.lib_details = {}
        self.cache = cache
        self._load_cache(self.cache)
        self.library_path = library_path

    def get_library(self, library):
        # Return details of a dynamic library
        library_name = self.lib_details.get(library)
        if library_name is not None:
            checksum = util.calculate_checksum(library_name)
            version = self.version([library_name])
        elif self.library_path != "":
            # Check for library in library path
            for path in self.library_path.split(","):
                lib_path = os.path.join(path.strip(), library)
                if os.path.isfile(lib_path):
                    library_name = os.path.realpath(lib_path)
                    checksum = util.calculate_checksum(lib_path)
                    version = self.version([lib_path])
                    break
        if library_name is None:
            checksum = {}
            version = None
        return {
            "location": library_name,
            "version": version,
            "checksum": checksum,
        }

    def _load_cache(self, cache):

        # Load cache
        self.lib_details = {}
        if cache is None:
            lines = util.run_process(["ldconfig", "-p"])
            for line in lines.stdout.splitlines()[1:]:
                if "=>" in line.strip():
                    libname, lib_architecture, _, lib_path = line.strip().split(" ")
                    self.lib_details[libname] = os.path.realpath(lib_path)
        else:
            # read file
            # Check file exists
            if len(cache) > 0:
                # Check path
                filePath = Path(cache)
                # Check path exists, a valid file and not empty file
                if (
                    filePath.exists()
                    and filePath.is_file()
                    and filePath.stat().st_size > 0
                ):
                    with open(cache, encoding="utf-8") as f:
                        lines = f.readlines()
                    for line in lines[1:]:
                        if "=>" in line.strip():
                            libname, lib_architecture, _, lib_path = line.strip().split(
                                " "
                            )
                            # self.lib_details[libname] = lib_path
                            self.lib_details[libname] = os.path.realpath(lib_path)

    def show(self):
        for name, path in self.lib_details.items():
            print(name, path)

    def version(self, library):
        if library is None:
            return None
        if self.cache is None:
            return util.get_version(library)
        # No version if cache used
        return None

    def _get_library_cache(self):
        return self.lib_details
