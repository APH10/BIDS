# Copyright (C) 2025 APH10 Limited
# SPDX-License-Identifier: Apache-2.0

"""
BIDS SBOM tests
"""

from pathlib import Path
import pytest
from bids.sbom4bids import main

class TestSBOM:
    """Tests the BIDS SBOM module"""

    TEST_PATH = Path(__file__).parent.resolve()
    SCRIPT_NAME = "sbom4bids"

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

    def test_input_command(self):
        """Test input command"""
        # Valid file
        test_file = f"{self.TEST_PATH}/test_assets/hello.json"
        with pytest.raises(SystemExit) as e:
            main([self.SCRIPT_NAME, "--input", test_file])
        assert e.value.args[0] == 0

    def test_missing_input_command(self):
        """Test input command"""
        # Invalid file
        test_file = f"{self.TEST_PATH}/test_assets/missing_file"
        with pytest.raises(SystemExit) as e:
            main([self.SCRIPT_NAME, "--input", test_file])
        assert e.value.args[0] == 1

    def test_cyclonedx_command(self):
        """Test debug command"""
        test_file = f"{self.TEST_PATH}/test_assets/hello.json"
        with pytest.raises(SystemExit) as e:
            # Format shoould get changed to Json
            main([self.SCRIPT_NAME, "--input", test_file, "--sbom", "cyclonedx", "--format", "tag"])
        assert e.value.args[0] == 0

    def test_debug_command(self):
        """Test debug command"""
        test_file = f"{self.TEST_PATH}/test_assets/hello.json"
        with pytest.raises(SystemExit) as e:
            main([self.SCRIPT_NAME, "--input", test_file, "--debug"])
        assert e.value.args[0] == 0
