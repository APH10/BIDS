import os
import subprocess
from pathlib import Path


class DynamicLibrary:

    def __init__(self, cache=None):
        self.lib_details = {}
        self.cache = cache
        self._load_cache(self.cache)

    def get_library(self, library):
        # Return details of a dynamic library
        library_name = self.lib_details.get(library)
        return {
            "location": library_name,
            "version": self.version(library_name),
        }

    def _load_cache(self, cache):
        # Load cache
        self.lib_details = {}
        if cache is None:
            lines = subprocess.run(["ldconfig", "-p"], capture_output=True, text=True)
            # print (lines.stdout.splitlines())
            for line in lines.stdout.splitlines()[1:]:
                if "=>" in line.strip():
                    libname, lib_architecture, _, lib_path = line.strip().split(" ")
                    # self.lib_details[libname] = lib_path
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
                    f = open(cache)
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
            try:
                lines = subprocess.run(library, capture_output=True, text=True)
                if len(lines.stdout.splitlines()) > 0:
                    version = lines.stdout.splitlines()[0].split(" ")[-1].strip()
                    if version[-1] == ".":
                        version = version[:-1]
                    return version
                return None
            except PermissionError:
                return None
        # No version if cache used
        return None

    def _get_library_cache(self):
        return self.lib_details
