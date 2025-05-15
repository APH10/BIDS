# Copyright (C) 2024 APH10 Limited
# SPDX-License-Identifier: Apache-2.0

from elftools.elf.dynamic import DynamicSection
from elftools.elf.elffile import ELFFile
from elftools.elf.gnuversions import (
    GNUVerDefSection,
    GNUVerNeedSection,
    GNUVerSymSection,
)
from elftools.elf.sections import SymbolTableSection
from typecode import contenttype

"""
Functions and objects to extract information from binary Elf files using pyelftools.
Based on code by: Eli Bendersky (eliben@gmail.com): "This code is in the public domain"

For a good introduction on readelf and ELF see:
    http://www.linuxforums.org/misc/understanding_elf_using_readelf_and_objdump.html
"""


class BIDSElf:

    def __init__(self, file, debug=False):
        T = contenttype.get_type(file)
        if not T.is_elf:
            raise TypeError("Not an ELF file")
        f = open(file, "rb")
        self.elffile = ELFFile(f)
        self._versioninfo = None
        self._init_versioninfo()
        self.debug = debug

    def get_header(self):
        header = self.elffile.header
        return header

    def get_dependencies(self):
        dependency = []
        for section in self.elffile.iter_sections():
            if not isinstance(section, DynamicSection):
                continue
            for tag in section.iter_tags():
                if tag.entry.d_tag == "DT_NEEDED":
                    dependency.append(tag.needed)
        return dependency

    def _init_versioninfo(self):
        """Search and initialise information about version related sections
        and the kind of versioning used (GNU or Solaris).
        """
        if self._versioninfo is not None:
            return

        self._versioninfo = {
            "versym": None,
            "verdef": None,
            "verneed": None,
            "type": None,
        }

        try:
            for section in self.elffile.iter_sections():
                if isinstance(section, GNUVerSymSection):
                    self._versioninfo["versym"] = section
                elif isinstance(section, GNUVerDefSection):
                    self._versioninfo["verdef"] = section
                elif isinstance(section, GNUVerNeedSection):
                    self._versioninfo["verneed"] = section
                elif isinstance(section, DynamicSection):
                    for tag in section.iter_tags():
                        if tag["d_tag"] == "DT_VERSYM":
                            self._versioninfo["type"] = "GNU"
                            break
        except OSError:
            if self.debug:
                print("OSError - Unable to process versioninfo")
            pass

        if not self._versioninfo["type"] and (
            self._versioninfo["verneed"] or self._versioninfo["verdef"]
        ):
            self._versioninfo["type"] = "Solaris"

    def _symbol_version(self, nsym):
        """Return a dict containing information on the version
        or None if no version information is available
        """
        self._init_versioninfo()

        symbol_version = dict.fromkeys(("index", "name", "filename", "hidden"))

        try:
            if (
                not self._versioninfo["versym"]
                or nsym >= self._versioninfo["versym"].num_symbols()
            ):
                return None
        except ZeroDivisionError:
            if self.debug:
                print("ZeroDivsionError - Unable to process symbol version")
            return None

        symbol = self._versioninfo["versym"].get_symbol(nsym)
        index = symbol.entry["ndx"]
        if index not in ("VER_NDX_LOCAL", "VER_NDX_GLOBAL"):
            try:
                index = int(index)
            except TypeError:
                if self.debug:
                    print("TypeError - Unable to process symbol")
                return None

            if self._versioninfo["type"] == "GNU":
                # In GNU versioning mode, the highest bit is used to
                # store whether the symbol is hidden or not
                if index & 0x8000:
                    index &= ~0x8000
                    symbol_version["hidden"] = True

            if (
                self._versioninfo["verdef"]
                and index <= self._versioninfo["verdef"].num_versions()
            ):
                _, verdaux_iter = self._versioninfo["verdef"].get_version(index)
                symbol_version["name"] = next(verdaux_iter).name
            else:
                try:
                    verneed, vernaux = self._versioninfo["verneed"].get_version(index)
                    symbol_version["name"] = vernaux.name
                    symbol_version["filename"] = verneed.name
                except AttributeError:
                    if self.debug:
                        print("AttributionError - Unable to process symbol name")
                    pass
                except TypeError:
                    if self.debug:
                        print("TypeError - Unable to process symbol name")
                    pass

        symbol_version["index"] = index
        return symbol_version

    def get_symbols(self):
        symbol_tables = [
            (idx, s)
            for idx, s in enumerate(self.elffile.iter_sections())
            if isinstance(s, SymbolTableSection)
        ]
        global_symbols = []
        local_symbols = []
        for section_index, section in symbol_tables:
            if not isinstance(section, SymbolTableSection):
                continue

            if section["sh_entsize"] > 0:
                for nsym, symbol in enumerate(section.iter_symbols()):

                    if (
                        section["sh_type"] == "SHT_DYNSYM"
                        and self._versioninfo["type"] == "GNU"
                    ):
                        version = self._symbol_version(nsym)
                        if self.debug:
                            print(version, symbol.name)
                        try:
                            if version["name"] != symbol.name and version["index"] not in (
                                "VER_NDX_LOCAL",
                                "VER_NDX_GLOBAL",
                            ):
                                # Just external symbols
                                if version["filename"]:
                                    # external symbol consists of a name
                                    # e.g. GLIBC_2.9 and a filename e.g. libc.so.6
                                    global_symbols.append(
                                        [version["filename"], version["name"], symbol.name]
                                    )
                                else:
                                    local_symbols.append(symbol.name)
                            else:
                                if symbol.name != "":
                                    local_symbols.append(symbol.name)
                        except TypeError:
                            if self.debug:
                                print ("TypeError - Unable to process symbols")
                            return None
                    elif self.debug:
                        print(
                            f"Type: {section['sh_type']} "
                            f"Name: {symbol.name} Version: "
                            f"{self._symbol_version(nsym)}"
                        )
        return global_symbols, local_symbols
