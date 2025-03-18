import argparse
import sys
import os
import json

# Importing project submodules
from datasources.ghsa import GHSAHandler
from datasources.nvd import NVDHandler
from parsers.mvn_parser import MvnParser
from parsers.npm_parser import NpmParser

def parse_cmd_line_args(args = None):
    frameworks = ["mvn", "npm"]
    parser = argparse.ArgumentParser(
        description = "Analyze security vulnerabilities in software projects.")
    parser.add_argument("--framework", choices = frameworks, required = True,
                        help = f"Options = {frameworks}")
    parser.add_argument("--file", required = True, help = "Path to the"
                    " dependency manifest file (eg: pom.xml for Maven,"
                    " package.json for NPM, etc.)")

    args = parser.parse_args(args)

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
    return ghsa_handler

def main(args = None):
    args = parse_cmd_line_args(args)
    parser = get_parser(args["framework"])

    dependency_tree = parser.get_dependency_tree(args["file"])
    unique_dependencies = parser.get_flat_dependency_set(dependency_tree)

    if not unique_dependencies:
        print("ERROR: No dependencies found or error in parsing.")
        sys.exit(1)
    
    vulnerabilities_list = []

    handler = init_handler_chain()

    for dependency in unique_dependencies:
        # Access tuple elements by index, not by key
        artifact_id = dependency[0]  # This is the "group.artifact"
        version = dependency[1]     # This is the "version"
        # inser vuln_type here, change to direct/trans from true/false
        result = handler.handle(artifact_id, version, args["framework"])
        if result:
            formatted_vulns = {
                "package_name": artifact_id,
                "version": version,
                "paths": [],  # Placeholder for dependency paths (modify if needed)
                "vulnerabilities": []
            }

            for vuln in result:
                vuln_types = [cwe["cwe_name"] for cwe in vuln["vuln_status"].get("cwes", [])] or "N/A"
                
                formatted_vulns["vulnerabilities"].append({
                    "cve": vuln["vuln_status"]["cve_id"],
                    "severity" : vuln["vuln_status"]["severity"],
                    "firstPatchedVersion": vuln["vuln_status"].get("firstPatchedVersion", "N/A"),
                    "vuln_types": vuln_types
                })

            vulnerabilities_list.append(formatted_vulns)

    output_path = os.path.join(os.getcwd(), "vulnerabilities.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(vulnerabilities_list, f, indent=4)

    print(f"Vulnerability data saved to {output_path}")

if __name__ == "__main__":
    main()