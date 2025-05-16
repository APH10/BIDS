# Copyright (C) 2025 APH10 Limited
# SPDX-License-Identifier: Apache-2.0

import hashlib
import os
import shutil
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


def check_sandbox():
    # Check that sandbox exists
    sandbox = os.getenv("BIDS_SANDBOX") or "firejail"
    return shutil.which(sandbox) if sandbox is not None else None


def run_process(command):
    sandbox_path = check_sandbox()
    # Use sandbox if available
    if sandbox_path:
        run_command = [sandbox_path] + command
    else:
        run_command = command
    return subprocess.run(
        run_command,
        capture_output=True,
        text=True,
        timeout=COMMAND_TIMEOUT,
    )


def get_version(application):
    try:
        lines = run_process(application)
        if len(lines.stdout.splitlines()) > 0:
            version = lines.stdout.splitlines()[0].split(" ")[-1].strip()
            if version[-1] == ".":
                version = version[:-1]
            # Check at least one number is in version
            if any(char.isdigit() for char in version):
                return version
            return None
    except PermissionError:
        return None
    except subprocess.TimeoutExpired:
        return None
