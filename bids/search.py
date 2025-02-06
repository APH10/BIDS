# See https://github.com/ajitesh123/codesearch/tree/main/codesearch

import argparse
import json
import sys
from collections import ChainMap

from bids.index import BIDSIndexer
from bids.version import VERSION


def main(argv=None):

    argv = argv or sys.argv
    app_name = "bids-search"

    MAX_RESULTS = 10
    # TODO rewrite
    parser = argparse.ArgumentParser(prog=app_name, description="BIDS Search Tool")

    input_group = parser.add_argument_group("Input")
    input_group.add_argument(
        "--initialise",
        action="store_true",
        help="initialise dataset",
    )
    input_group.add_argument(
        "--index",
        action="store",
        default="",
        help="directory to index",
    )
    input_group.add_argument(
        "--search",
        action="store",
        default="",
        help="search query",
    )
    input_group.add_argument(
        "--verbose",
        action="store_true",
        help="verbose reporting",
    )
    output_group = parser.add_argument_group("Output")
    output_group.add_argument(
        "--debug",
        action="store_true",
        default=False,
        help="add debug information",
    )
    output_group.add_argument(
        "--results",
        action="store",
        default=MAX_RESULTS,
        help=f"Maximum number of results to return (default {MAX_RESULTS})",
    )

    # Import /export index
    database_group = parser.add_argument_group("Database Management")
    database_group.add_argument(
        "--export",
        action="store",
        help="export database filename",
        default="",
    )
    database_group.add_argument(
        "--import",
        action="store",
        help="import database filename",
        default="",
    )

    parser.add_argument("-V", "--version", action="version", version=VERSION)

    defaults = {
        "initialise": False,
        "index": "",
        "search": "",
        "import": "",
        "export": "",
        "results": MAX_RESULTS,
        "verbose": False,
        "debug": False,
    }

    raw_args = parser.parse_args(argv[1:])
    args = {key: value for key, value in vars(raw_args).items() if value}
    args = ChainMap(args, defaults)

    # Create indexer

    indexer = BIDSIndexer(debug=args["debug"])

    if args["initialise"]:
        indexer.reinitialise_index()
    if args["index"] != "":
        # Index the specified directory
        print(f'Indexing files in {args["index"]}...')
        indexer.index_files(args["index"])
        print("Indexing complete!")
    elif args["import"] != "":
        if indexer.import_data(args["import"]):
            print("Import complete!")
        else:
            print("Import failed")
            sys.exit(1)
    elif args["export"] != "":
        indexer.export_data(args["export"])
    elif args["search"] != "":
        # Search the index
        print(f'Searching for: {args["search"]}')
        results = indexer.search(args["search"], limit=int(args["results"]))

        if not results:
            print("No results found.")
        else:
            print("\nSearch Results:")
            print("-" * 80)
            for i, result in enumerate(results, 1):
                # print(f"{i}. {result['file_path']} (Score: {result['score']:.2f})")
                print(f"{i}. Score: {result['score']:.4f}")
                json_data = json.loads(result["content"])
                print(f'   File: {json_data["metadata"]["binary"]["filename"]}')
                if "description" in json_data["metadata"]["binary"]:
                    print(
                        f'   Description: {json_data["metadata"]["binary"]["description"]}'
                    )
                if args["verbose"]:
                    print(f"   Content: {json.dumps(json_data,indent=2)}\n")
            print("-" * 80)
    else:
        print("[ERROR] Must specify a command")
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
