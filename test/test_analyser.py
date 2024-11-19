# Copyright (C) 2024 APH10 Limited
# SPDX-License-Identifier: Apache-2.0

"""
BIDS Analyser tests
"""
from pathlib import Path

from bids.analyser import BIDSAnalyser


class TestAnalyser:
    """Tests the BIDS Analyser"""

    TEST_PATH = Path(__file__).parent.resolve()

    def test_get_global_symbols(self):
        filename = f"{self.TEST_PATH}/test_assets/hello"
        analyser_test = BIDSAnalyser()
        analyser_test.analyse(filename)
        data = analyser_test.get_global_symbols()
        assert len(data) > 0

    def test_get_local_symbols(self):
        filename = f"{self.TEST_PATH}/test_assets/hello"
        analyser_test = BIDSAnalyser()
        analyser_test.analyse(filename)
        data = analyser_test.get_local_symbols()
        assert len(data) > 0

    def test_get_dependencies(self):
        filename = f"{self.TEST_PATH}/test_assets/hello"
        analyser_test = BIDSAnalyser()
        analyser_test.analyse(filename)
        data = analyser_test.get_dependencies()
        assert len(data) > 0

    def test_get_callgraph(self):
        filename = f"{self.TEST_PATH}/test_assets/hello"
        analyser_test = BIDSAnalyser()
        analyser_test.analyse(filename)
        data = analyser_test.get_callgraph()
        assert len(data) == 0

    def test_get_header(self):
        filename = f"{self.TEST_PATH}/test_assets/hello"
        analyser_test = BIDSAnalyser()
        analyser_test.analyse(filename)
        data = analyser_test.get_header()
        assert len(data) > 0
