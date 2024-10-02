# Copyright (C) 2024 APH10 Limited
# SPDX-License-Identifier: Apache-2.0

import argparse
import sys
import textwrap
from collections import ChainMap

from bids.analyser import BIDSAnalyser
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
        "exclude_dependency": False,
        "exclude_symbol": False,
        "exclude_callgraph": False,
        "system": False,
        "output_file": "",
        "debug": False,
    }

    raw_args = parser.parse_args(argv[1:])
    args = {key: value for key, value in vars(raw_args).items() if value}
    args = ChainMap(args, defaults)

    # Validate CLI parameters

    binary_file = args["file"]

    if len(binary_file) == 0:
        # print ("File not provided")
        sys.exit(10)

    if args["debug"]:
        print("File", binary_file)
        print("Exclude Dependencies:", args["exclude_dependency"])
        print("Exclude Symbols:", args["exclude_symbol"])
        print("Exclude Call Graph:", args["exclude_callgraph"])
        print("Output file:", args["output_file"])

    # Do stuff
    options = {
        "dependency": args["exclude_dependency"],
        "symbol": args["exclude_symbol"],
        "callgraph": args["exclude_callgraph"],
    }
    analyser = BIDSAnalyser(options)
    analyser.analyse(binary_file)

    # print (f"Dependencies: {analyser.get_dependencies()}")
    # print (f"Symbols: {analyser.get_symbols()}")

    if len(analyser.get_dependencies()) > 0:
        print("GLOBAL")
        for dependency in analyser.get_dependencies():
            library = {}
            for symbol in analyser.get_global_symbols():
                if symbol[0] == dependency:
                    if library.get(symbol[1]) is not None:
                        library[symbol[1]].append(symbol[2])
                    else:
                        library[symbol[1]] = [symbol[2]]

            print(f"Dependency: {dependency}")
            for lib, functions in library.items():
                print(lib, sorted(functions))

    # print ("LOCAL")
    # # Local
    # library = {}
    # for symbol in analyser.get_local_symbols():
    #     if library.get(symbol[0]) is not None:
    #         library[symbol[0]].append(symbol[1])
    #     else:
    #         library[symbol[0]] = [symbol[1]]
    #
    # for lib, functions in library.items():
    #     print(lib, sorted(functions))

    sys.exit(0)


if __name__ == "__main__":
    sys.exit(main())
