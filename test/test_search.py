# Copyright (C) 2025 APH10 Limited
# SPDX-License-Identifier: Apache-2.0

"""
BIDS Search tests
"""

from pathlib import Path
import pytest
from bids.search import main

class TestSearch:
    """Tests the BIDS Search module"""

    TEST_PATH = Path(__file__).parent.resolve()
    SCRIPT_NAME = "bids-search"

    def test_invalid_usage(self):
        """Test that no parameters results in error"""
        # No parameters will error
        with pytest.raises(SystemExit) as e:
            main([self.SCRIPT_NAME])
        assert e.value.args[0] == 1

    def test_usage(self):
        """Test that the usage returns 0"""
        with pytest.raises(SystemExit) as e:
            main([self.SCRIPT_NAME, "--help"])
        assert e.value.args[0] == 0

    def test_version(self):
        """Test that the version returns 0"""
        with pytest.raises(SystemExit) as e:
            main([self.SCRIPT_NAME, "--version"])
        assert e.value.args[0] == 0

    def test_invalid_parameter(self):
        """Test that invalid parameters exit with expected error code.
        ArgParse calls sys.exit(2) for all errors"""
        self.tempdir = "/tmp"

        # invalid command
        with pytest.raises(SystemExit) as e:
            main([self.SCRIPT_NAME, "non-existent"])
        assert e.value.args[0] == 2

        # bad parameter
        with pytest.raises(SystemExit) as e:
            main([self.SCRIPT_NAME, "--bad-param"])
        assert e.value.args[0] == 2

        # bad parameter (but good directory)
        with pytest.raises(SystemExit) as e:
            main([self.SCRIPT_NAME, "--bad-param", self.tempdir])
        assert e.value.args[0] == 2

        # worse parameter
        with pytest.raises(SystemExit) as e:
            main([self.SCRIPT_NAME, "--bad-param && cat hi", self.tempdir])
        assert e.value.args[0] == 2

        # bad parameter after directory
        with pytest.raises(SystemExit) as e:
            main([self.SCRIPT_NAME, self.tempdir, "--bad-param;cat hi"])
        assert e.value.args[0] == 2

    def test_index_command(self):
        """Test index command"""
        test_files = f"{self.TEST_PATH}/test_assets"
        with pytest.raises(SystemExit) as e:
            main([self.SCRIPT_NAME, "--index", test_files, "--debug"])
        assert e.value.args[0] == 0

    def test_search_command(self):
        """Test search command"""
        with pytest.raises(SystemExit) as e:
            main([self.SCRIPT_NAME, "--search", "libc"])
        assert e.value.args[0] == 0

    def test_search_command_noresults(self):
        """Test search command"""
        with pytest.raises(SystemExit) as e:
            main([self.SCRIPT_NAME, "--search", "not_available"])
        assert e.value.args[0] == 0

    def test_export_command(self):
        """Test export command"""
        export_file = "/tmp/bids_export"
        with pytest.raises(SystemExit) as e:
            main([self.SCRIPT_NAME, "--export", export_file])
        assert e.value.args[0] == 0
        # Check file exists
        assert Path(f"{export_file}.zip").is_file()

    def test_import_command(self):
        """Test import command"""
        test_import = f"{self.TEST_PATH}/test_assets/index.zip"
        with pytest.raises(SystemExit) as e:
            main([self.SCRIPT_NAME, "--import", test_import])
        assert e.value.args[0] == 0
        # Check contents

    def test_import_command_missing_file(self):
        """Test import command"""
        test_import = f"{self.TEST_PATH}/test_assets/import"
        with pytest.raises(SystemExit) as e:
            main([self.SCRIPT_NAME, "--import", test_import])
        assert e.value.args[0] == 1

    def test_debug_command(self):
        """Test debug command"""
        with pytest.raises(SystemExit) as e:
            main([self.SCRIPT_NAME, "--search", "libc", "--debug"])
        assert e.value.args[0] == 0

    def test_verbose_command(self):
        """Test debug command"""
        with pytest.raises(SystemExit) as e:
            main([self.SCRIPT_NAME, "--search", "libc", "--verbose"])
        assert e.value.args[0] == 0