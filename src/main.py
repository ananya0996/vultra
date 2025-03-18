import argparse
import sys

# Importing project submodules
from datasources import BaseDataSource
from datasources import GHSAHandler
from datasources import NVDHandler
from parsers.mvn_parser import MvnParser
from parsers.npm_parser import NpmParser

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

    return {
        "framework": args.framework,
        "file": args.file
    }

def get_parser(framework):
    parsers = {
        "mvn": MvnParser,
        "npm": NpmParser
    }

    if framework not in parsers:
        raise ValueError(f"Unsupported framework: {framework}")
    return parsers[framework]()

def init_handler_chain():
    ghsa_handler = GHSAHandler()
    nvd_handler = NVDHandler()
    ghsa_handler.set_next(nvd_handler)

def main():
    args = parse_cmd_line_args()
    parser = get_parser(args["framework"])
    dependency_tree = parser.get_dependency_tree(args["file"])
    unique_dependencies = parser.get_flat_dependency_set(dependency_tree)

    if not unique_dependencies:
        print("ERROR: No dependencies found or error in parsing.")
        sys.exit(1)
    
    vulnerabilities = []

    handler = init_handler_chain()

    for dependency in unique_dependencies:
        result = handler.handle(dependency["artifactIds"], dependency["version"], args["framework"])
        if result:
            vulnerabilities.append(result)

if __name__ == "__main__":
    main()
