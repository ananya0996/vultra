
import os
import subprocess
import json

def load_config(config_path="config.json"):
    with open(config_path, "r") as file:
        return json.load(file)

def parse_dependency_tree_maven(dependencies_json):
    dependency_set = set()
    stack = [dependencies_json]

    while stack:
        dependency = stack.pop()
        dependency_set.add((f"{dependency['groupId']}.{dependency['artifactId']}", dependency['version']))
        stack.extend(dependency.get('children', []))

    return dependency_set


# takes the file path and gives us dependency tree in JSON format
def get_maven_dependencies(pom_path):
    if not os.path.isfile(pom_path):
        print(json.dumps({"error": f"{pom_path} does not exist."}))
        return

    project_dir = os.path.dirname(pom_path)

    if not os.path.isdir(project_dir):
        print(json.dumps({"error": f"The directory {project_dir} does not exist."}))
        return

    print(f"Processing: {pom_path}")
    # output will be written to dep-tree.json within the repo
    json_output_file = os.path.join(project_dir, "dep-tree.json")

    try:
        # Run the  Maven command to get the dependency tree
        result = subprocess.run(
            [
                "mvn", "-f", pom_path,
                "org.apache.maven.plugins:maven-dependency-plugin:3.8.1:tree",
                "-DoutputFile=dep-tree.json",
                "-DoutputType=json"
            ],
            cwd=project_dir,
            capture_output=True,
            text=True,
            shell=True
        )

        if result.returncode == 0:
            # check if the dep-tree.json is created after running the maven command
            if os.path.exists(json_output_file):
                with open(json_output_file, "r", encoding="utf-8") as f:
                    dependencies_json = json.load(f)
                    dependencies_list = parse_dependency_tree_maven(dependencies_json)
                    print(dependencies_list)
                # print(json.dumps(dependencies_json, indent=4))
            else:
                print(json.dumps({"error": "dep-tree.json output file was not created by Maven."}))
        else:
            print(json.dumps({"error": "Error while running Maven.", "details": result.stderr}))

    except FileNotFoundError:
        print(json.dumps({"error": "mvn or java is not found. Ensure it is installed and added to the system PATH."}))
    except Exception as e:
        print(json.dumps({"error": "Exception occurred.", "details": str(e)}))


if __name__ == '__main__':
    config = load_config()

    for pom_file in config["pom_files"]:
        get_maven_dependencies(pom_file)

