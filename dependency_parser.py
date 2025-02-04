import json
import xml.etree.ElementTree as ET

def parse_package_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    dependencies = {}
    for dep_type in ['dependencies', 'devDependencies', 'peerDependencies', 'optionalDependencies']:
        if dep_type in data:
            dependencies.update(data[dep_type])
    
    return dependencies

def parse_pom_xml(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()
    ns = {'mvn': 'http://maven.apache.org/POM/4.0.0'}  
    
    dependencies = {}
    for dep in root.findall('.//mvn:dependency', ns):
        group_id = dep.find('mvn:groupId', ns).text if dep.find('mvn:groupId', ns) is not None else ''
        artifact_id = dep.find('mvn:artifactId', ns).text if dep.find('mvn:artifactId', ns) is not None else ''
        version = dep.find('mvn:version', ns).text if dep.find('mvn:version', ns) is not None else 'LATEST'
        
        if artifact_id:
            key = f"{group_id}:{artifact_id}" if group_id else artifact_id
            dependencies[key] = version
    
    return dependencies

def parse_manifest(file_path):
    # Identifies the manifest type and parses it accordingly
    if file_path.endswith('package.json'):
        return parse_package_json(file_path)
    elif file_path.endswith('pom.xml'):
        return parse_pom_xml(file_path)
    else:
        raise ValueError("Unsupported manifest file. Please provide a package.json or pom.xml.")

if __name__ == "__main__":
    # insert file path below
    file_path = ""
    try:
        dependencies = parse_manifest(file_path)
        print("Extracted Dependencies:")
        print(json.dumps(dependencies, indent=4))
    except Exception as e:
        print(f"Error: {e}")
