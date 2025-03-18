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

            dependencies_list = self.get_flat_dependency_set(dependencies_json)

        except FileNotFoundError:
            print(json.dumps({"error": "npm is not found. Ensure it is installed and added to the system PATH."}))

        os.remove(json_output_file)
        return dependencies_list
    
    def get_flat_dependency_set(self, dep_json):
        result = set()

        def traverse_dependencies(dependencies, is_direct_dependency):
            for package_name, package_info in dependencies.items():
                if 'version' in package_info:
                    package_version = package_info['version']
                    package_entry = (package_name, package_version, is_direct_dependency)
                    result.add(package_entry)

                if 'dependencies' in package_info:
                    traverse_dependencies(package_info['dependencies'], False)

        if 'dependencies' in dep_json:
            traverse_dependencies(dep_json['dependencies'], True)

        return result
