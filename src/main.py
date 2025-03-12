import argparse
import json

# Importing project submodules
from datasources import BaseDataSource
from datasources import GHSAHandler
from datasources import NVDHandler

def parse_cmd_line_args():
    frameworks = ["mvn", "npm"]
    parser = argparse.ArgumentParser(
        description = "Analyze security vulnerabilities in software projects.")
    parser.add_argument("--framework", choices = frameworks, required = True,
                        help = f"Options = {frameworks}")
    parser.add_argument("--file", required = True, help = "Path to the"
                    " dependency manifest file (eg: pom.xml for Maven,"
                    " package.json for NPM, etc.)")
    args = parser.parse_args()

def main():
    parse_cmd_line_args()

    dependencies = []
    if dependencies:
        print("Extracted Dependencies:")
        print(json.dumps(dependencies, indent = 4))
    else:
        print("ERROR: No dependencies found or error in parsing.")

main()