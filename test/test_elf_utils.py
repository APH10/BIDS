# Copyright (C) 2024 APH10 Limited
# SPDX-License-Identifier: Apache-2.0

"""
BIDS CLI tests
"""
from pathlib import Path
import pytest

from bids.elf_utils import BIDSElf


class TestElf_Utils:
    """Tests the BIDS Elf Utils"""

    TEST_PATH = Path(__file__).parent.resolve()

    def test_check_nonELF_file(self):
        filename=f"{self.TEST_PATH}/test_assets/hello.c"
        with pytest.raises(TypeError) as e:
            elf = BIDSElf(filename)
        assert str(e.value) == "Not an ELF file"

    def test_check_ELF_file(self):
        filename=f"{self.TEST_PATH}/test_assets/hello"
        elf = BIDSElf(filename)
        assert elf is not None

    def test_get_symbols(self):
        filename=f"{self.TEST_PATH}/test_assets/hello"
        elf = BIDSElf(filename)
        global_symbols, local_symbols = elf.get_symbols()
        assert len(global_symbols) > 0

    def test_get_dependencies(self):
        filename=f"{self.TEST_PATH}/test_assets/hello"
        elf = BIDSElf(filename)
        dependency = elf.get_dependencies()
        assert len(dependency) > 0