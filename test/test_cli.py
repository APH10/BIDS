# Copyright (C) 2024 APH10 Limited
# SPDX-License-Identifier: Apache-2.0

"""
BIDS CLI tests
"""
from pathlib import Path

import pytest

from bids.cli import main


class TestCLI:
    """Tests the BIDS CLI"""

    TEST_PATH = Path(__file__).parent.resolve()
    SCRIPT_NAME = "bids-analyser"

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
            main([self.SCRIPT_NAME, "non-existant"])
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

    def test_file_command(self):
        """Test file command"""
        # Valid file
        test_file = f"{self.TEST_PATH}/test_assets/hello"
        with pytest.raises(SystemExit) as e:
            main([self.SCRIPT_NAME, "--file", test_file])
        assert e.value.args[0] == 0

    def test_missing_file_command(self):
        """Test file command"""
        # Invalid file
        test_file = f"{self.TEST_PATH}/test_assets/missing_file"
        with pytest.raises(SystemExit) as e:
            main([self.SCRIPT_NAME, "--file", test_file])
        assert e.value.args[0] == 1

    def test_debug_command(self):
        """Test debug command"""
        test_file = f"{self.TEST_PATH}/test_assets/hello"
        with pytest.raises(SystemExit) as e:
            main([self.SCRIPT_NAME, "--file", test_file, "--debug"])
        assert e.value.args[0] == 0

    def test_description_command(self):
        """Test debug command"""
        test_file = f"{self.TEST_PATH}/test_assets/hello"
        with pytest.raises(SystemExit) as e:
            main(
                [
                    self.SCRIPT_NAME,
                    "--file",
                    test_file,
                    "--description",
                    "This is a test file",
                ]
            )
        assert e.value.args[0] == 0

    def test_check_nonELF_file(self, capsys):
        filename = f"{self.TEST_PATH}/test_assets/hello.c"
        with pytest.raises(SystemExit) as e:
            main([self.SCRIPT_NAME, "--file", filename])
        assert e.value.args[0] == 1
        captured = capsys.readouterr()
        assert "Only ELF files can be analysed" in captured.out
