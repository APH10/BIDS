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


class BIDSElf:

    def __init__(self, file):
        T = contenttype.get_type(file)
        if not T.is_elf:
            raise TypeError("Not an ELF file")
        f = open(file, "rb")
        self.elffile = ELFFile(f)
        self._versioninfo = None
        self._init_versioninfo()

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

        if (
            not self._versioninfo["versym"]
            or nsym >= self._versioninfo["versym"].num_symbols()
        ):
            return None

        symbol = self._versioninfo["versym"].get_symbol(nsym)
        index = symbol.entry["ndx"]
        if index not in ("VER_NDX_LOCAL", "VER_NDX_GLOBAL"):
            index = int(index)

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
                verneed, vernaux = self._versioninfo["verneed"].get_version(index)
                symbol_version["name"] = vernaux.name
                symbol_version["filename"] = verneed.name

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
                        print(version, symbol.name)
                        if version["name"] != symbol.name and version["index"] not in (
                            "VER_NDX_LOCAL",
                            "VER_NDX_GLOBAL",
                        ):
                            # Just external symbols
                            if version["filename"]:
                                # external symbol
                                # name e.g. GLIBC_2.9
                                # filename e.g. libc.so.6
                                global_symbols.append(
                                    [version["filename"], version["name"], symbol.name]
                                )
                            else:
                                local_symbols.append([version["name"], symbol.name])
                        else:
                            local_symbols.append([version["name"], symbol.name])

        return global_symbols, local_symbols

    def get_text(self):
        pass
