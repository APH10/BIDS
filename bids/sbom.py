# Copyright (C) 2025 APH10 Limited
# SPDX-License-Identifier: Apache-2.0

import argparse
import json
import os
import sys
from collections import ChainMap
from pathlib import Path

from lib4sbom.data.document import SBOMDocument
from lib4sbom.data.package import SBOMPackage
from lib4sbom.data.relationship import SBOMRelationship
from lib4sbom.generator import SBOMGenerator
from lib4sbom.sbom import SBOM

import bids.util as util
from bids.version import VERSION


PROJECT_NAME = "Bids_Application"
def main(argv=None):

    argv = argv or sys.argv
    app_name = "sbom4bids"
    parser = argparse.ArgumentParser(
        prog=app_name,
        description="Generates a Software Bill of Materials (SBOM) from a Bids JSON file",
    )
    input_group = parser.add_argument_group("Input")
    input_group.add_argument(
        "-i",
        "--input",
        action="store",
        default="",
        help="name of Bids file",
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
        "--sbom",
        action="store",
        default="spdx",
        choices=["spdx", "cyclonedx"],
        help="specify type of sbom to generate (default: spdx)",
    )
    output_group.add_argument(
        "--format",
        action="store",
        default="tag",
        choices=["tag", "json", "yaml"],
        help="specify format of software bill of materials (sbom) (default: tag)",
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
        "input": "",
        "output_file": "",
        "sbom": "spdx",
        "debug": False,
        "format": "tag",
    }

    raw_args = parser.parse_args(argv[1:])
    args = {key: value for key, value in vars(raw_args).items() if value}
    args = ChainMap(args, defaults)

    # Validate CLI parameters

    # Ensure format is aligned with type of SBOM
    bom_format = args["format"]
    if args["sbom"] == "cyclonedx":
        # Only JSON format valid for CycloneDX
        if bom_format != "json":
            bom_format = "json"

    if args["debug"]:
        print("Input file", args["input"])
        print("SBOM type:", args["sbom"])
        print("Format:", bom_format)
        print("Output file:", args["output_file"])

    if len(args["input"]) > 0:
        try:
            sbom_packages, sbom_relationships = process_file(args["input"])
            if args["debug"]:
                print("Packages", sbom_packages)
                print("Relationships", sbom_relationships)
        except FileNotFoundError:
            print(f"[ERROR] {args['input']} not found.")
            sys.exit(1)
    else:
        print("[ERROR] Nothing to process")
        sys.exit(1)

    # Generate SBOM
    create_sbom(
        sbom_type=args["sbom"],
        sbom_format=args["format"],
        packages=sbom_packages,
        relationships=sbom_relationships,
        output_file=args["output_file"],
    )

    sys.exit(0)


def create_sbom(sbom_type, sbom_format, packages, relationships, output_file):
    # Generate SBOM
    bids_sbom = SBOM()
    bids_sbom.set_type(sbom_type)
    bids_doc = SBOMDocument()
    bids_doc.set_value("lifecycle", "build")
    bids_sbom.add_document(bids_doc.get_document())
    bids_sbom.add_packages(packages)
    bids_sbom.add_relationships(relationships)
    sbom_generator = SBOMGenerator(
        False,
        sbom_type,
        sbom_format,
        application="sbom4bids",
        version=VERSION,
    )
    sbom_generator.generate(
        project_name=PROJECT_NAME,
        sbom_data=bids_sbom.get_sbom(),
        filename=output_file,
    )


def process_file(bids_file):
    # Check file exists
    invalid_file = True
    if len(bids_file) > 0:
        # Check path
        filePath = Path(bids_file)
        # Check path exists, a valid file and not empty file
        if filePath.exists() and filePath.is_file() and filePath.stat().st_size > 0:
            # Assume that processing can proceed
            invalid_file = False
    if invalid_file:
        raise FileNotFoundError
    # Parse file
    data = json.load(open(os.path.realpath(bids_file), encoding="utf-8"))

    sbom_packages = {}
    sbom_relationships = []
    # Create parent package
    bids_package = SBOMPackage()
    bids_package.set_type("application")
    bids_package.set_name(os.path.basename(data["metadata"]["binary"]["filename"]))
    bids_package.set_value("release_date", data["metadata"]["binary"]["filedate"])
    if "version" in data["metadata"]["binary"]:
        bids_package.set_version(data["metadata"]["binary"]["version"])

    bids_package.set_evidence(data["metadata"]["binary"]["filename"])
    for checksum_data in data["metadata"]["binary"]["checksum"]:
        for algorithm in util.get_checksum_algorithms():
            if algorithm in checksum_data["algorithm"]:
                checksum = checksum_data["value"]
                bids_package.set_checksum(algorithm.upper(), checksum)

    for package_property in ["class", "architecture", "bits", "os"]:
        bids_package.set_property(
            package_property, data["metadata"]["binary"][package_property]
        )
    if "description" in data["metadata"]["binary"]:
        bids_package.set_description(data["metadata"]["binary"]["description"])
    # Add local symbols
    if "localsymbols" in data["components"]:
        symbol_id = 1
        for symbol in data["components"]["localsymbols"]:
            bids_package.set_property(f"localsymbol_{symbol_id}", symbol)
            symbol_id += 1

    sbom_packages[(bids_package.get_name(), bids_package.get_value("version"))] = (
        bids_package.get_package()
    )

    dependency_relationship = SBOMRelationship()
    dependency_relationship.set_relationship(
        PROJECT_NAME, "DESCRIBES", bids_package.get_name()
    )
    sbom_relationships.append(dependency_relationship.get_relationship())

    # Now look at dependencies
    for library in data["components"]["dynamiclibrary"]:
        # Create package
        dependency_package = SBOMPackage()
        dependency_package.set_type("library")
        dependency_package.set_name(library["name"])
        dependency_package.set_evidence(library["location"])
        if "version" in library:
            dependency_package.set_value("version", library["version"])
        dependency_package.set_value("release_date", library["filedate"])
        for checksum_data in library["checksum"]:
            for algorithm in util.get_checksum_algorithms():
                if algorithm in checksum_data["algorithm"]:
                    checksum = checksum_data["value"]
                    dependency_package.set_checksum(algorithm.upper(), checksum)
        # Get functions
        func_id = 1
        # Check that there are functions for library
        if dependency_package.get_name() in data["relationships"]:
            for function in data["relationships"][dependency_package.get_name()]:
                dependency_package.set_property(f"function_{func_id}", function)
                func_id += 1
            sbom_packages[
                (dependency_package.get_name(), dependency_package.get_value("version"))
            ] = dependency_package.get_package()

        # Create relationship with parent application
        #dependency_relationship = SBOMRelationship()
        dependency_relationship.initialise()
        dependency_relationship.set_relationship(
            bids_package.get_name(), "DEPENDS_ON", dependency_package.get_name()
        )
        sbom_relationships.append(dependency_relationship.get_relationship())
        sbom_packages[
            (dependency_package.get_name(), dependency_package.get_value("version"))
        ] = dependency_package.get_package()

    return sbom_packages, sbom_relationships


if __name__ == "__main__":
    sys.exit(main())
