# Copyright (C) 2025 APH10 Limited
# SPDX-License-Identifier: Apache-2.0

import hashlib
import subprocess
import time
from pathlib import Path

COMMAND_TIMEOUT = 5  # Seconds
CHECKSUM_ALGORITHMS = ["sha256", "sha384", "sha512", "sha3-256", "sha3-384", "sha3-512"]


def get_checksum_algorithms():
    return CHECKSUM_ALGORITHMS


def calculate_checksum(filename):
    # Calculate checksum for specified file
    checksum = {}

    with open(filename, "rb") as f:
        contents = f.read()
        checksum["size"] = len(contents)
        checksum["date"] = time.ctime(Path(filename).stat().st_mtime)
        # Although MD5 and SHA1 are valid checksums for SBOMs, they are considered insecure
        checksum["sha256"] = hashlib.sha256(contents).hexdigest()
        checksum["sha384"] = hashlib.sha384(contents).hexdigest()
        checksum["sha512"] = hashlib.sha512(contents).hexdigest()
        checksum["sha3-256"] = hashlib.sha3_256(contents).hexdigest()
        checksum["sha3-384"] = hashlib.sha3_384(contents).hexdigest()
        checksum["sha3-512"] = hashlib.sha3_512(contents).hexdigest()
    return checksum


def run_process(command):
    return subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=COMMAND_TIMEOUT,
    )
