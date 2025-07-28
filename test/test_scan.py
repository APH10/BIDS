# Copyright (C) 2025 APH10 Limited
# SPDX-License-Identifier: Apache-2.0

"""
BIDS Scan tests
"""

from pathlib import Path

import pytest

from bids.scan import main


class TestScan:
    """Tests the BIDS Scan module"""

    TEST_PATH = Path(__file__).parent.resolve()
    SCRIPT_NAME = "bids-scan"

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

    def test_directory_command(self):
        """Test directory command"""
        # Valid file
        test_files = f"{self.TEST_PATH}/test_assets"
        output_dir = "/tmp"
        with pytest.raises(SystemExit) as e:
            main([self.SCRIPT_NAME, "--directory", test_files, "--output", output_dir])
        assert e.value.args[0] == 0

    def test_missing_directory_command(self):
        """Test directory command"""
        # Invalid file
        test_file = f"{self.TEST_PATH}/test_assets/missing_file"
        with pytest.raises(SystemExit) as e:
            main([self.SCRIPT_NAME, "--directory", test_file])
        assert e.value.args[0] == 0

    def test_debug_command(self):
        """Test debug command"""
        test_file = f"{self.TEST_PATH}/test_assets"
        output_dir = "/tmp"
        with pytest.raises(SystemExit) as e:
            main(
                [
                    self.SCRIPT_NAME,
                    "--directory",
                    test_file,
                    "--debug",
                    "--output",
                    output_dir,
                ]
            )
        assert e.value.args[0] == 0

    def test_not_elf_file(self):
        test_files = f"{self.TEST_PATH}/test_assets/notelf"
        output_dir = "/tmp"
        with pytest.raises(SystemExit) as e:
            main([self.SCRIPT_NAME, "--directory", test_files, "--output", output_dir])
        assert e.value.args[0] == 0
