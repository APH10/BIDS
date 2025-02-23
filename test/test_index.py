# Copyright (C) 2025 APH10 Limited
# SPDX-License-Identifier: Apache-2.0

"""
BIDS Index tests
"""
import os
from pathlib import Path

from unittest import mock

from bids.index import BIDSIndexer


class TestIndex:
    """Tests the BIDS Index module"""

    TEST_PATH = Path(__file__).parent.resolve()
    # Cache file used to ensure constant test results
    # deployed library will have dynamic values
    INDEX_FILE = f"{TEST_PATH}/test_assets/index"
    ENV_INDEX_FILE = f"/tmp"
    BAD_INDEX_FILE = f"{TEST_PATH}/test_assets/badindex"

    def test_check_init(self):
        index_file = BIDSIndexer(index_path=self.INDEX_FILE)
        assert Path(self.INDEX_FILE).exists()
        assert index_file.get_index_path() == self.INDEX_FILE

    def test_check_default_init(self):
        index_file = BIDSIndexer()
        # Default directory
        assert "bids_index" in str(index_file.get_index_path())

    def test_debug_command(self):
        """Test debug command"""
        index_file = BIDSIndexer(debug=True)
        # Default directory
        assert "bids_index" in str(index_file.get_index_path())

    @mock.patch.dict(os.environ, {"BIDS_DATASET": ENV_INDEX_FILE})
    def test_index_set_using_env_variable(self):
        index_file = BIDSIndexer()
        # Default directory
        assert "bids_index" in str(index_file.get_index_path())

    def test_check_if_bids_file(self):
        index_file = BIDSIndexer()
        file_path = f"{self.TEST_PATH}/test_assets/hello.json"
        assert index_file.is_bids_file(file_path) == True
        file_path = f"{self.TEST_PATH}/test_assets/badfile.json"
        assert index_file.is_bids_file(file_path) == False
        file_path = f"{self.TEST_PATH}/test_assets/hello.c"
        assert index_file.is_bids_file(file_path) == False

    def test_reinitialise(self):
        # Create an inded
        index_file = BIDSIndexer()
        # Will include files in directory
        index_file.reinitialise_index()
        # Check if the index has been reset
        assert "bids_index" in str(index_file.get_index_path())




