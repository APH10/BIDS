# Copyright (C) 2025 APH10 Limited
# SPDX-License-Identifier: Apache-2.0

"""
BIDS Index tests
"""
from pathlib import Path

from bids.index import BIDSIndexer


class TestIndex:
    """Tests the BIDS Index module"""

    TEST_PATH = Path(__file__).parent.resolve()
    # Cache file used to esnure constant test results
    # deployed library will have dynamic values
    INDEX_FILE = f"{TEST_PATH}/test_assets/index"
    BAD_INDEX_FILE = f"{TEST_PATH}/test_assets/badindex"

    def test_check_init(self):
        index_file = BIDSIndexer(index_path=self.INDEX_FILE)
        assert Path(self.INDEX_FILE).exists()
        assert index_file.get_index_path() == self.INDEX_FILE

    def test_check_default_init(self):
        index_file = BIDSIndexer()
        # Default directory
        assert "bids_index" in str(index_file.get_index_path())



