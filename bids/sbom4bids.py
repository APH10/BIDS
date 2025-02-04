from lib4sbom.data.document import SBOMDocument
from lib4sbom.data.package import SBOMPackage
from lib4sbom.generator import SBOMGenerator
from lib4sbom.data.relationship import SBOMRelationship
from lib4sbom.sbom import SBOM
import os
from bids.version import VERSION

import sys
import argparse
from collections import ChainMap
import json

def main(argv=None):

    argv = argv or sys.argv
    app_name = "sbom4bids"
    parser = argparse.ArgumentParser(
        prog=app_name,
        description="Generates a Software Bill of Materials (SBOM) from a Bids JSON file"
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
        sbom_packages, sbom_relationships = create_sbom(args["input"],"binary")
    else:
        print("[ERROR] Nothing to process")
        return -1

    # Generate SBOM
    bids_sbom = SBOM()
    bids_sbom.set_type(sbom_type=args["sbom"])
    bids_doc = SBOMDocument()
    bids_doc.set_value("lifecycle", "build")
    bids_sbom.add_document(bids_doc.get_document())
    bids_sbom.add_packages(sbom_packages)
    bids_sbom.add_relationships(sbom_relationships)
    sbom_generator = SBOMGenerator(False, sbom_type=args["sbom"], format=args["format"], application=app_name, version=VERSION)
    sbom_generator.generate(project_name="BIDS_Application", sbom_data=bids_sbom.get_sbom(),filename=args["output_file"])

    return 0

def create_sbom(bids_file, appname):
    # Parse file
    data = json.load(open(bids_file, "r", encoding="utf-8"))

    sbom_packages = {}
    sbom_relationships = []
    # Create parent package
    bids_package = SBOMPackage()
    bids_package.set_type("application")
    bids_package.set_name(os.path.basename(data["metadata"]["binary"]["filename"]))
    bids_package.set_value(
        "release_date", data["metadata"]["binary"]["filedate"]
    )

    bids_package.set_evidence(data["metadata"]["binary"]["filename"])
    # Add evidence details relating to filename and filesize
    checksum_algorithm = data["metadata"]["binary"]["checksum"]["algorithm"]
    checksum = data["metadata"]["binary"]["checksum"]["value"]
    bids_package.set_checksum(checksum_algorithm, checksum)
    for property in ["class", "architecture", "bits", "os"]:
        bids_package.set_property(property, data["metadata"]["binary"][property])
    if "description" in data["metadata"]:
        bids_package.set_description(data["metadata"]["description"])
    sbom_packages[
        (bids_package.get_name(), bids_package.get_value("version"))
    ] = bids_package.get_package()

    # TODO Describes relationship
    dependency_relationship = SBOMRelationship()
    dependency_relationship.set_relationship(
        appname, "DESCRIBES", bids_package.get_name()
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
        sbom_packages[
            (dependency_package.get_name(), dependency_package.get_value("version"))
        ] = dependency_package.get_package()

        # Create relationship with parent application
        dependency_relationship = SBOMRelationship()
        dependency_relationship.set_relationship(
            bids_package.get_name(), "DEPENDS_ON", dependency_package.get_name()
        )
        sbom_relationships.append(dependency_relationship.get_relationship())

    return sbom_packages, sbom_relationships

if __name__ == "__main__":
    sys.exit(main())

