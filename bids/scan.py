# Copyright (C) 2025 APH10 Limited
# SPDX-License-Identifier: Apache-2.0

import argparse
import glob
import os
import sys
import textwrap
from collections import ChainMap
from pathlib import Path

from bids.analyser import BIDSAnalyser
from bids.output import BIDSOutput
from bids.version import VERSION

# CLI processing


def main(argv=None):

    argv = argv or sys.argv
    app_name = "bids-scan"
    parser = argparse.ArgumentParser(
        prog=app_name,
        description=textwrap.dedent(
            """
            bids-scan analyses ELF binaries in a directory and extracts dependency and symbolic information
            """
        ),
    )
    input_group = parser.add_argument_group("Input")
    input_group.add_argument(
        "--directory",
        action="store",
        default="",
        help="directory to scan",
    )
    input_group.add_argument(
        "--pattern",
        action="store",
        default="",
        help="files pattern (default is all files)",
    )

    output_group = parser.add_argument_group("Output")
    output_group.add_argument(
        "-d",
        "--debug",
        action="store_true",
        default=False,
        help="add debug information",
    )
    output_group.add_argument(
        "-o",
        "--output",
        action="store",
        default="",
        help="directory to store results",
    )

    parser.add_argument("-V", "--version", action="version", version=VERSION)

    defaults = {
        "directory": "",
        "pattern": "*",
        "output": "",
        "debug": False,
    }

    raw_args = parser.parse_args(argv[1:])
    args = {key: value for key, value in vars(raw_args).items() if value}
    args = ChainMap(args, defaults)

    # Validate CLI parameters

    files_to_analyse = args["directory"]
    if len(files_to_analyse) == 0:
        print("[ERROR] No directory specified.")
        sys.exit(1)

    if args["debug"]:
        print("Input directory:", args["directory"])
        print("File Pattern:", args["pattern"])
        print("Output directory:", args["output"])

    # Check output directory exists
    Path(args["output"]).mkdir(parents=True, exist_ok=True)

    analyser = BIDSAnalyser(debug=args["debug"])
    for filename in glob.glob(
        os.path.join(args["directory"], args["pattern"])
    ):  # Use glob for pattern matching
        if Path(filename).is_file():  # Ensure it's a file (not a directory)
            try:
                # Ignore non executable files
                if not os.access(filename, os.X_OK):
                    if args["debug"]:
                        print(f"{filename} is not executable, skipping.")
                    continue
                if args["debug"]:
                    print(f"Processing {filename}")
                analyser.analyse(filename)
                output = BIDSOutput(tool_version=VERSION)
                output.create_metadata(analyser.get_file_data())
                output.create_components(
                    analyser.get_dependencies(),
                    analyser.get_global_symbols(),
                    analyser.get_callgraph(),
                    local=analyser.get_local_symbols(),
                )
                output_file = os.path.join(
                    args["output"], f"{os.path.basename(filename)}.json"
                )
                output.generate_output(output_file)
            except Exception as e:
                print(f"[WARNING] Could not process {filename}. Error: {e}")
            except TypeError:
                print(f"[ERROR] {filename} - Only ELF files can be analysed.")
            except FileNotFoundError:
                print(f"[ERROR] {filename} not found.")

    sys.exit(0)


if __name__ == "__main__":
    sys.exit(main())
