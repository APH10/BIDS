# Copyright (C) 2024 APH10 Limited
# SPDX-License-Identifier: Apache-2.0

"""
BIDS Library tests
"""
import shutil
from pathlib import Path

import pytest

from bids.library import DynamicLibrary


class TestLibrary:
    """Tests the BIDS Library module"""

    TEST_PATH = Path(__file__).parent.resolve()
    # Cache file used to esnure constant test results
    # deployed library will have dynamic values
    CACHE_FILE = f"{TEST_PATH}/test_assets/cache"
    BAD_CACHE_FILE = f"{TEST_PATH}/test_assets/badcache"

    def test_check_init(self):
        lib = DynamicLibrary(cache=self.CACHE_FILE)
        assert len(lib._get_library_cache()) > 0

    def test_check_missing_cache_file(self):
        # Used to test empty librry
        lib = DynamicLibrary(cache=self.BAD_CACHE_FILE)
        assert len(lib._get_library_cache()) == 0

    def test_get_invalid_library(self):
        lib = DynamicLibrary(cache=self.CACHE_FILE)
        library_details = lib.get_library("bad_library")
        assert library_details["version"] is None
        assert library_details["location"] is None
        assert library_details["checksum"] == {}

    def test_get_library(self):
        lib = DynamicLibrary(cache=self.CACHE_FILE)
        library_details = lib.get_library("libc.so.6")
        assert library_details["version"] is None
        assert library_details["location"] is not None

    def test_get_version(self):
        lib = DynamicLibrary(cache=self.CACHE_FILE)
        library_details = lib.version(["libc.so.6"])
        assert library_details is None

    def test_get_version_null_library(self):
        lib = DynamicLibrary(cache=self.CACHE_FILE)
        library_details = lib.version(None)
        assert library_details is None

    def test_show(self, capsys):
        lib = DynamicLibrary(cache=self.CACHE_FILE)
        lib.show()
        captured = capsys.readouterr()
        assert "libc.so.6" in captured.out

    def test_no_detect_version(self):
        lib = DynamicLibrary(cache=self.CACHE_FILE, detect_version=False)
        library_details = lib.version(["libc.so.6"])
        assert library_details is None

    def test_detect_version_with_cache(self):
        lib = DynamicLibrary(cache=self.CACHE_FILE, detect_version=True)
        library_details = lib.version(["libc.so.6"])
        assert library_details is None

    @pytest.mark.skipif(shutil.which("firejail") is None, reason="Requires sandbox")
    def test_detect_version(self):
        lib = DynamicLibrary(detect_version=True)
        library_details = lib.version(["/usr/lib32/libc.so.6"])
        assert library_details is not None
