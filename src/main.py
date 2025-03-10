import argparse
import json

# Importing project submodules
from datasource import DataSource
from datasource import GHSAHandler
from datasource import NVDHandler
import dependency_parser

def main():
    frameworks = ["mvn", "npm"]
    parser = argparse.ArgumentParser(
        description = "Analyze security vulnerabilities in software projects.")
    parser.add_argument("--framework", choices = frameworks, required = True,
                        help = f"Options = {frameworks}")
    parser.add_argument("--file", required = True, help = "Path to the"
                    " dependency manifest file (eg: pom.xml for Maven,"
                    " package.json for NPM, etc.)")
    # TODO: parse arguments
    # args = parser.parse_args()

    dependencies = []
    if dependencies:
        print("Extracted Dependencies:")
        print(json.dumps(dependencies, indent = 4))
    else:
        print("ERROR: No dependencies found or error in parsing.")

main()