# Copyright (C) 2024 APH10 Limited
# SPDX-License-Identifier: Apache-2.0

import json
import platform
import sys
import uuid
from datetime import datetime

from bids.library import DynamicLibrary


class _OutputManager:
    """Helper class for managing output to file and console."""

    def __init__(self, out_type="file", filename=None):
        self.out_type = out_type
        self.filename = filename
        if self.out_type == "file" and self.filename != "":
            try:
                self.file_handle = open(filename, "w", encoding="utf-8")
            except (FileNotFoundError, IsADirectoryError) as e:
                # Unable to create file, so send output to console
                self.out_type = "console"
                self.file_handle = None
        else:
            self.out_type = "console"
            self.file_handle = None

    def close(self):
        if self.out_type == "file":
            self.file_handle.close()

    def file_out(self, message):
        self.file_handle.write(message + "\n")

    def console_out(self, message):
        print(message)

    def show(self, message):
        if self.out_type == "file":
            self.file_out(message)
        else:
            self.console_out(message)


class BIDSOutput:

    def __init__(self, tool="bids_generator", tool_version="1.0", cache=None):
        self.bids_document = {}
        self.tool = tool
        self.tool_version = tool_version
        self.dl = DynamicLibrary(cache)

    def generateTime(self):
        # Generate data/time label in format YYYY-MM-DDThh:mm:ssZ
        return datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")

    def generate_id(self):
        return str(uuid.uuid4())

    def create_metadata(self, application):
        metadata = {}
        metadata["docFormat"] = "BIDS"
        metadata["specVersion"] = "1.0"
        metadata["id"] = self.generate_id()
        metadata["version"] = 1
        metadata["timestamp"] = self.generateTime()
        metadata["tool"] = f"{self.tool}:{self.tool_version}"
        # Add details of component
        component = {}
        component["class"] = "ELF64" if sys.maxsize > 2**32 else "ELF32"
        component["architecture"] = platform.machine()
        component["bits"] = 64 if sys.maxsize > 2**32 else 32
        component["os"] = sys.platform
        if application.get("location") is not None:
            component["filename"] = application["location"]
        if application.get("version") is not None:
            component["version"] = application["version"]
        if application.get("size") is not None:
            component["filesize"] = application["size"]
        if application.get("date") is not None:
            component["filedate"] = application["date"]
        hash = {}
        hash["algorithm"] = "SHA256"
        if application.get("checksum") is not None:
            hash["value"] = application["checksum"]
        component["checksum"] = hash
        if application.get("description") is not None:
            component["description"] = application["description"]
        metadata["binary"] = component
        self.bids_document["metadata"] = metadata

    def create_components(self, dependencies, symbols, callgraph, local=None):
        components = {}
        dependency = []
        relationships = {}
        for d in dependencies:
            info = {}
            info["name"] = d
            library_info = self.dl.get_library(d)
            if library_info["location"] is not None:
                info["location"] = library_info["location"]
            if library_info["version"] is not None:
                info["version"] = library_info["version"]
            dependency.append(info)
        components["dynamiclibrary"] = dependency
        symbol = []
        for s in symbols:
            symbol.append(s[2])
            if relationships.get(s[0]) is not None:
                relationships[s[0]].append(s[2])
            else:
                relationships[s[0]] = [s[2]]
        components["globalsymbol"] = sorted(symbol)
        if local is not None:
            local_symbols = []
            for local_sym in local:
                local_symbols.append(local_sym)
            components["localsymbols"] = sorted(local_symbols)
        self.bids_document["components"] = components
        self.bids_document["callgraph"] = callgraph
        self.bids_document["relationships"] = relationships

    def get_document(self):
        return self.bids_document

    def generate_output(self, filename):
        json_data = json.dumps(self.bids_document, indent=2)
        self.output_manager = _OutputManager("file", filename)
        self.output_manager.show(json_data)
        self.output_manager.close()
