import json
import os
import subprocess

from parsers.dependency_parser import DependencyParser

class MvnParser(DependencyParser):
    def get_dependency_tree(self, pom_path):
        pom_path = os.path.abspath(pom_path)
        if not os.path.isfile(pom_path):
            print(json.dumps({"ERROR": f"{pom_path} does not exist."}))
            return None

        project_dir = os.path.dirname(pom_path)
        json_filename = "dep-tree.json"
        json_output_file = os.path.join(project_dir, json_filename)
        dependencies_json = None

        try:
            result = subprocess.run(
                [
                    "mvn", "-f", pom_path,
                    "org.apache.maven.plugins:maven-dependency-plugin:3.8.1:tree",
                    f"-DoutputFile={json_output_file}",
                    "-DoutputType=json"
                ],
                cwd=project_dir,
                capture_output=True,
                text=True,
                shell=True
            )

            if result.returncode == 0:
                # check if <json_filename> is created after running the maven command
                if os.path.exists(json_output_file):
                    with open(json_output_file, "r", encoding="utf-8") as f:
                        dependencies_json = json.load(f)
                else:
                    print(json.dumps({f"ERROR": "{json_filename} output file was not created by Maven."}))
            else:
                print(json.dumps({"ERROR": "Error while running Maven.", "details": result.stderr}))

        except FileNotFoundError:
            print(json.dumps({"ERROR": "mvn or java is not found. Ensure it is installed and added to the system PATH."}))
        except Exception as e:
            print(json.dumps({"ERROR": "Exception occurred.", "details": str(e)}))
        
        if os.path.exists(json_output_file):
            os.remove(json_output_file)
            
        return dependencies_json
    
    def get_flat_dependency_set(self, dep_json):
        result = set()

        def traverse_dependencies(node, is_direct_dependency):
            if 'groupId' in node and 'artifactId' in node and 'version' in node:
                package_name = f"{node['groupId']}:{node['artifactId']}"
                package_version = node['version']
                package_entry = (package_name, package_version, is_direct_dependency)
                result.add(package_entry)

            if 'children' in node:
                for child in node['children']:
                    traverse_dependencies(child, False)

        # Root node in dep_json is the actual project itself. Direct dependencies
        # are its first-level children.
        # Only pass True for direct dependency status to the first level children.
        if 'children' in dep_json:
            for child in dep_json['children']:
                traverse_dependencies(child, True)

        return result

    def find_paths_in_tree(self, dependency_tree, package_name, package_version, path=""):
        results = []
        current_path = path + "->" + f"{dependency_tree['groupId']}:{dependency_tree['artifactId']}" if path else f"{dependency_tree['groupId']}:{dependency_tree['artifactId']}"

        if f"{dependency_tree['groupId']}:{dependency_tree['artifactId']}" == package_name and dependency_tree['version'] == package_version:
            results.append(current_path)

        if 'children' in dependency_tree:
            for child in dependency_tree['children']:
                results.extend(self.find_paths_in_tree(child, package_name, package_version, current_path))

        return results
