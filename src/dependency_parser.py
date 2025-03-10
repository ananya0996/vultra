import json
import xml.etree.ElementTree as ET
import argparse
import sys

def parse_package_json(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        dependencies = {}
        for dep_type in ["dependencies", "devDependencies", "peerDependencies", "optionalDependencies"]:
            if dep_type in data:
                dependencies.update(data[dep_type])
        
        return dependencies
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
        return {}

def parse_pom_xml(file_path):
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        ns = {"mvn": "http://maven.apache.org/POM/4.0.0"}
        
        dependencies = {}
        for dep in root.findall(".//mvn:dependency", ns):
            group_id = dep.find("mvn:groupId", ns).text if dep.find("mvn:groupId", ns) is not None else ""
            artifact_id = dep.find("mvn:artifactId", ns).text if dep.find("mvn:artifactId", ns) is not None else ""
            version = dep.find("mvn:version", ns).text if dep.find("mvn:version", ns) is not None else "LATEST"
            
            if artifact_id:
                key = f"{group_id}:{artifact_id}" if group_id else artifact_id
                dependencies[key] = version
        
        return dependencies
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
        return {}

def parse_manifest(file_path, framework):
    if framework == "npm":
        return parse_package_json(file_path)
    elif framework == "mvn":
        return parse_pom_xml(file_path)
    else:
        raise ValueError("Unsupported framework. Please specify either 'npm' or 'mvn'.")

def main():
    parser = argparse.ArgumentParser(description="Parse dependencies from package.json or pom.xml files")
    parser.add_argument("--dm", choices=["mvn", "npm"], required=True, help="Dependency manager framework (mvn or npm)")
    parser.add_argument("file", help="Path to the dependency manifest file")
    args = parser.parse_args()
    
    try:
        dependencies = parse_manifest(args.file, args.dm)
        if dependencies:
            print("Extracted Dependencies:")
            print(json.dumps(dependencies, indent=4))
        else:
            print("No dependencies found or error in parsing.")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
