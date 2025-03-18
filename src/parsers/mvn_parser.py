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
        dependencies_json = None  # Initialize variable outside the try block

        try:
            # Run the Maven command to get the dependency tree
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
        
        # Clean up the file if it exists
        if os.path.exists(json_output_file):
            os.remove(json_output_file)
            
        return dependencies_json
    
    def get_flat_dependency_set(self, dependencies_json):
        dependency_set = set()
        stack = [dependencies_json]

        while stack:
            dependency = stack.pop()
            dependency_set.add((f"{dependency['groupId']}:{dependency['artifactId']}", dependency['version']))
            stack.extend(dependency.get('children', []))
        # TODO: Return in a standard dictionary format for each package manager to give client class a uniform interface
        return dependency_set
