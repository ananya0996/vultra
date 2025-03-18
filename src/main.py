import argparse
import sys
import os
import json
from collections import defaultdict

# Importing project submodules
from datasources.ghsa import GHSAHandler
from datasources.nvd import NVDHandler
from parsers.mvn_parser import MvnParser
from parsers.npm_parser import NpmParser
from report import generate_html_report

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
    
    handler = init_handler_chain()
    vulnerabilities_list = []
    paths = []
    direct_dependencies = 0
    transitive_dependencies = 0
    direct_vulnerabilities = 0
    transitive_vulnerabilities = 0
    vuln_type_counts = defaultdict(int)  

    for dependency in unique_dependencies:

        artifact_id = dependency[0] 
        version = dependency[1]     
        is_direct_dependency = dependency[2]

        # Update dependency counters
        if is_direct_dependency:
            direct_dependencies += 1
        else:
            transitive_dependencies += 1

        result = handler.handle(artifact_id, version, args["framework"])
        if result:
            if is_direct_dependency:
                direct_vulnerabilities += 1
            else:
                transitive_vulnerabilities += 1
                paths = parser.find_paths_in_tree(dependency_tree, artifact_id, version)

            formatted_vulns = {
                "package_name": artifact_id,
                "version": version,
                "paths": paths,  # Placeholder for dependency paths (modify if needed)
                "vulnerabilities": []
            }

            for vuln in result:
                vuln_types = [cwe["cwe_name"] for cwe in vuln["vuln_status"].get("cwes", [])] or "N/A"

                # Update vuln_type frequency
                for vt in vuln_types:
                    vuln_type_counts[vt] += 1
                
                formatted_vulns["vulnerabilities"].append({
                    "cve": vuln["vuln_status"]["cve_id"],
                    "severity" : vuln["vuln_status"]["severity"],
                    "firstPatchedVersion": vuln["vuln_status"].get("firstPatchedVersion", "N/A"),
                    "vuln_types": vuln_types
                })

            vulnerabilities_list.append(formatted_vulns)

    # Prepare final JSON response
    final_result = {
        "direct_dependencies": direct_dependencies,
        "transitive_dependencies": transitive_dependencies,
        "direct_vulnerabilities": direct_vulnerabilities,
        "transitive_vulnerabilities": transitive_vulnerabilities,
        "vuln_type_counts": dict(vuln_type_counts)
    }

    # Uncomment this line to generate the HTML report of vulnerability analysis
    # generate_html_report(vulnerabilities_list)

    # Return the final JSON object
    return final_result
    

if __name__ == "__main__":
    main()