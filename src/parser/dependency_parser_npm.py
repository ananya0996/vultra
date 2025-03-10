import os
import subprocess
import json


def load_config(config_path="config.json"):
    with open(config_path, "r") as file:
        return json.load(file)

# parse npm json to get the direct and transitive dependencies
def parse_npm_json_create_list_of_transitive_direct_dependencies(npm_json):
    dependency_set = set()
    stack = [{"name": key, "version": value.get("version", "unknown"), "dependencies": value.get("dependencies", {})}
             for key, value in npm_json.get("dependencies", {}).items()]

    while stack:
        dependency = stack.pop()
        dependency_set.add((dependency["name"], dependency["version"]))

        stack.extend([
            {"name": key, "version": value.get("version", "unknown"), "dependencies": value.get("dependencies", {})}
            for key, value in dependency["dependencies"].items()
        ])

    return dependency_set
def get_npm_dependencies(package_json_path):
    if not os.path.isfile(package_json_path):
        print(json.dumps({"error": f"{package_json_path} does not exist."}))
        return

    project_dir = os.path.dirname(package_json_path)
    if not os.path.isdir(project_dir):
        print(json.dumps({"error": f"The directory {project_dir} does not exist."}))
        return

    json_output_file = os.path.join(project_dir, "npm.json")

    try:
        # package-lock.json is required
        install_result = subprocess.run(
            ['npm', 'install'],
            capture_output=True,
            text=True,
            shell=True,
            cwd=project_dir
        )

        if install_result.returncode != 0:
            print(json.dumps({"error": "npm install failed", "details": install_result.stderr}))
            return

        #  Run npm list --all --json to get the list of transitive and direct dependencies
        list_result = subprocess.run(
            ['npm', 'list', '--all', '--json'],
            capture_output=True,
            text=True,
            shell=True,
            cwd=project_dir
        )

        if list_result.returncode != 0:
            print(json.dumps({"error": "npm list failed", "details": list_result.stderr}))
            return

        # write data to npm.json for further processing
        with open(json_output_file, "w", encoding="utf-8") as f:
            f.write(list_result.stdout)

        # reading npm.json
        with open(json_output_file, "r", encoding="utf-8") as f:
            dependencies_json_npm = json.load(f)

        dependencies_list = parse_npm_json_create_list_of_transitive_direct_dependencies(dependencies_json_npm)
        print(dependencies_list)


    except FileNotFoundError:
        print(json.dumps({"error": "npm is not found. Ensure it is installed and added to the system PATH."}))


if __name__ == '__main__':
    config = load_config()


    for package_json_path in config["package_jsons"]:
        get_npm_dependencies(package_json_path)