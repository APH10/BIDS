# Copyright (C) 2024 APH10 Limited
# SPDX-License-Identifier: Apache-2.0

import argparse
import os
import sys
import textwrap
from collections import ChainMap

import bids.util as util
from bids.analyser import BIDSAnalyser
from bids.output import BIDSOutput
from bids.version import VERSION

# CLI processing


def main(argv=None):

    argv = argv or sys.argv
    app_name = "bids-analyser"
    parser = argparse.ArgumentParser(
        prog=app_name,
        description=textwrap.dedent(
            """
            bids-analyser analyses a binary application in ELF format and extracts
            dependency, symbolic and call graph information into a JSON data stream
            """
        ),
    )
    input_group = parser.add_argument_group("Input")
    input_group.add_argument(
        "-f",
        "--file",
        action="store",
        default="",
        help="identity of binary file",
    )
    input_group.add_argument(
        "--description",
        action="store",
        default="",
        help="description of file",
    )
    input_group.add_argument(
        "--library-path",
        action="store",
        default="",
        help="path to search for library files",
    )
    input_group.add_argument(
        "--exclude-dependency",
        action="store_true",
        help="suppress reporting of dependencies",
    )
    input_group.add_argument(
        "--exclude-symbol",
        action="store_true",
        default=False,
        help="suppress reporting of symbols",
    )
    input_group.add_argument(
        "--exclude-callgraph",
        action="store_true",
        default=False,
        help="suppress reporting of call graph",
    )
    input_group.add_argument(
        "--detect-version",
        action="store_true",
        default=False,
        help="detect version of component",
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
        "--output-file",
        action="store",
        default="",
        help="output filename (default: output to stdout)",
    )

    parser.add_argument("-V", "--version", action="version", version=VERSION)

    defaults = {
        "file": "",
        "description": "",
        "library_path": "",
        "exclude_dependency": False,
        "exclude_symbol": False,
        "exclude_callgraph": False,
        "detect_version": False,
        "output_file": "",
        "debug": False,
    }

    raw_args = parser.parse_args(argv[1:])
    args = {key: value for key, value in vars(raw_args).items() if value}
    args = ChainMap(args, defaults)

    # Validate CLI parameters

    binary_file = args["file"]

    if len(binary_file) == 0:
        print("[ERROR] File not provided")
        sys.exit(1)

    if args["debug"]:
        print("File", binary_file)
        print("Description", args["description"])
        print("Library path:", args["library_path"])
        print("Exclude Dependencies:", args["exclude_dependency"])
        print("Exclude Symbols:", args["exclude_symbol"])
        print("Exclude Call Graph:", args["exclude_callgraph"])
        print("Detect Version:", args["detect_version"])
        print("Output file:", args["output_file"])

    # Use cache if provided in environment variable
    cache = None
    if os.getenv("BIDS_CACHE") is not None:
        cache = os.getenv("BIDS_CACHE")

    # Do stuff
    options = {
        "dependency": args["exclude_dependency"],
        "symbol": args["exclude_symbol"],
        "callgraph": args["exclude_callgraph"],
        "detect_version": args["detect_version"],
    }

    # Wanr if no sandbox detected when detecting component versions
    if args["detect_version"] and util.check_sandbox() is None:
        print("[WARNING] Sandbox not available.")

    analyser = BIDSAnalyser(
        options, description=args["description"], debug=args["debug"]
    )
    try:
        # Analyse file
        analyser.analyse(binary_file)

        if args["debug"]:
            print(f"Dependencies: {analyser.get_dependencies()}")
            print(f"Imports: {analyser.get_global_symbols()}")
            print(f"Exports: {sorted(analyser.get_local_symbols())}")

        # Create report
        output = BIDSOutput(
            tool_version=VERSION,
            cache=cache,
            library_path=args["library_path"],
            detect_version=args["detect_version"],
        )
        output.create_metadata(analyser.get_file_data())
        output.create_components(
            analyser.get_dependencies(),
            analyser.get_global_symbols(),
            analyser.get_callgraph(),
            local=analyser.get_local_symbols(),
        )
        output.generate_output(args["output_file"])
        sys.exit(0)
    except TypeError:
        print("[ERROR] Only ELF files can be analysed.")
    except FileNotFoundError:
        print(f"[ERROR] {binary_file} not found.")

    sys.exit(1)


if __name__ == "__main__":
    sys.exit(main())
