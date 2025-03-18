import json
import os
import subprocess

from parsers.dependency_parser import DependencyParser

class NpmParser(DependencyParser):
    def get_dependency_tree(self, package_json_path):
        pom_path = os.path.abspath(package_json_path)
        if not os.path.isfile(package_json_path):
            print(json.dumps({"error": f"{package_json_path} does not exist."}))
            return

        project_dir = os.path.dirname(package_json_path)
        json_filename = "dep-tree.json"
        json_output_file = os.path.join(project_dir, json_filename)

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
                return None

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
                return None

            # write data to file for further processing
            with open(json_output_file, "w", encoding="utf-8") as f:
                f.write(list_result.stdout)

            # reading json file
            with open(json_output_file, "r", encoding="utf-8") as f:
                dependencies_json = json.load(f)

        except FileNotFoundError:
            print(json.dumps({"error": "npm is not found. Ensure it is installed and added to the system PATH."}))

        os.remove(json_output_file)
        return dependencies_json
    
    def get_flat_dependency_set(self, dependencies_json):
        dependency_set = set()
        stack = [{"name": key, "version": value.get("version", "unknown"), "dependencies": value.get("dependencies", {})}
                for key, value in dependencies_json.get("dependencies", {}).items()]

        while stack:
            dependency = stack.pop()
            dependency_set.add((dependency["name"], dependency["version"]))

            stack.extend([
                {"name": key, "version": value.get("version", "unknown"), "dependencies": value.get("dependencies", {})}
                for key, value in dependency["dependencies"].items()
            ])

        return dependency_set
