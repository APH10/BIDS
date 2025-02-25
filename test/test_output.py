# Copyright (C) 2024 APH10 Limited
# SPDX-License-Identifier: Apache-2.0

"""
BIDS Output tests
"""
import json
from pathlib import Path

from bids.output import BIDSOutput


class TestOutput:
    """Tests the BIDS Output"""

    TEST_PATH = Path(__file__).parent.resolve()
    # Cache file used to ensure constant test results
    # deployed library will have dynamic values
    CACHE_FILE = f"{TEST_PATH}/test_assets/cache"

    def test_metadata(self):
        output_test = BIDSOutput(tool_version="1.0", cache=self.CACHE_FILE)
        output_test.create_metadata({"test": "data"})
        test_doc = output_test.get_document()
        assert "test" not in test_doc
        assert test_doc.get("test") is None
        assert "1.0" in test_doc["metadata"]["tool"]
        assert "metadata" in test_doc

    def test_components(self):
        output_test = BIDSOutput(tool_version="1.0", cache=self.CACHE_FILE)
        # output_test.create_metadata({"test": "data"})
        output_test.create_components([], [], [])
        test_doc = output_test.get_document()
        # Check top level items of components
        assert "dynamiclibrary" in test_doc["components"]
        assert "globalsymbol" in test_doc["components"]
        assert "localsymbols" not in test_doc["components"]

    def test_components_local(self):
        output_test = BIDSOutput(tool_version="1.0", cache=self.CACHE_FILE)
        # output_test.create_metadata({"test": "data"})
        output_test.create_components([], [], [], local=[])
        test_doc = output_test.get_document()
        # Check top level items of components
        assert "dynamiclibrary" in test_doc["components"]
        assert "globalsymbol" in test_doc["components"]
        assert "localsymbols" in test_doc["components"]

    def test_document(self):
        output_test = BIDSOutput(tool_version="1.0", cache=self.CACHE_FILE)
        output_test.create_metadata({"test": "data"})
        output_test.create_components([], [], [])
        test_doc = output_test.get_document()
        # Check top level components
        assert "metadata" in test_doc
        assert "components" in test_doc
        assert "callgraph" in test_doc
        assert "relationships" in test_doc

    def test_output(self, capsys):
        output_test = BIDSOutput(tool_version="1.0", cache=self.CACHE_FILE)
        output_test.create_metadata({"test": "data"})
        output_test.create_components([], [], [])
        output_test.generate_output(filename="")
        captured = capsys.readouterr()
        # Check top level components
        assert "metadata" in captured.out
        assert "components" in captured.out
        assert "callgraph" in captured.out
        assert "relationships" in captured.out

    def test_output2(self, capsys):
        output_test = BIDSOutput(tool_version="1.0", cache=self.CACHE_FILE)
        output_test.create_metadata({"test": "data"})
        output_test.create_components([], [], [])
        # Can't write to a directory so will be redirected to the console
        output_test.generate_output(filename="/")
        captured = capsys.readouterr()
        # Check top level components
        assert "metadata" in captured.out
        assert "components" in captured.out
        assert "callgraph" in captured.out
        assert "relationships" in captured.out

    def test_output_to_file(self):
        output_test = BIDSOutput(tool_version="1.0", cache=self.CACHE_FILE)
        output_test.create_metadata({"test": "data"})
        output_test.create_components([], [], [])
        TEST_OUTPUT_FILE = f"{self.TEST_PATH}/test_assets/test.json"
        output_test.generate_output(filename=TEST_OUTPUT_FILE)
        # Now check contents of file
        # bids_json = json.load(open(TEST_OUTPUT_FILE, "r", encoding="utf-8"))
        print(f"Open {TEST_OUTPUT_FILE}")
        with open(TEST_OUTPUT_FILE) as f:
            print(f)
            bids_json = json.load(f)

            # bids_json = json.load(open(TEST_OUTPUT_FILE, "r"))
            # Check top level components
            assert "metadata" in bids_json
            assert "components" in bids_json
            assert "callgraph" in bids_json
            assert "relationships" in bids_json
        Path(TEST_OUTPUT_FILE).unlink()

    def test_output_missing_library(self, capsys):
        output_test = BIDSOutput(tool_version="1.0", cache=self.CACHE_FILE)
        output_test.create_metadata({"test": "data"})
        output_test.create_components(["bad_library"], [], [])
        # Can't write to a directory so will be redirected to the console
        output_test.generate_output(filename="/")
        captured = capsys.readouterr()
        # Check top level components
        assert "metadata" in captured.out
        assert "components" in captured.out
        assert "callgraph" in captured.out
        assert "relationships" in captured.out

