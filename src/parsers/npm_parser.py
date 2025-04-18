import json
import os
import subprocess

from parsers.dependency_parser import DependencyParser

class NpmParser(DependencyParser):
    def get_dependency_tree(self, package_json_path):
        package_json_path = os.path.abspath(package_json_path)
        current_directory = os.getcwd()
        project_directory = os.path.dirname(package_json_path)

        if not os.path.isfile(package_json_path):
            print(json.dumps({"ERROR": f"{package_json_path} does not exist."}))
            return

        json_filename = "dep-tree.json"
        json_output_file = os.path.join(project_directory, json_filename)

        try:
            os.chdir(project_directory)
            # package-lock.json is required
            install_result = subprocess.run(
                ['npm', 'install'],
                capture_output=True,
                text=True,
                cwd=project_directory
            )
            os.chdir(current_directory)
            if install_result.returncode != 0:
                print("ERROR CODE: " + str(install_result.returncode))
                print(install_result.stdout)
                print("--------------->" + str(install_result.stder))
                return None

            #  Run npm list --all --json to get the list of transitive and direct dependencies
            list_result = subprocess.run(
                ['npm', 'list', '--all', '--json'],
                capture_output=True,
                text=True,
                cwd=project_directory
            )

            if list_result.returncode != 0:
                print(json.dumps({"ERROR": "npm list failed", "details": list_result.stderr}))
                return None

            # write data to file for further processing
            with open(json_output_file, "w", encoding="utf-8") as f:
                f.write(list_result.stdout)

            # reading json file
            with open(json_output_file, "r", encoding="utf-8") as f:
                dependencies_json = json.load(f)

        except FileNotFoundError as e:
            print(json.dumps({"ERROR": f"{e}"}))

        os.remove(json_output_file)
        return dependencies_json

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
    
    def find_paths_in_tree(self, dependency_tree, package_name, package_version, path=""):
        results = []
        # Initialize path with the root package name if it's the first call
        if not path:
            current_path = dependency_tree['name']
        else:
            current_path = path

        # Check if the current node is the target package with correct version
        if current_path.split('->')[-1].strip() == package_name and dependency_tree.get('version', '') == package_version:
            results.append(current_path)

        # Recursively search in children if they exist
        if 'dependencies' in dependency_tree:
            for child_name, child_data in dependency_tree['dependencies'].items():
                # Build the new path including this child's name
                new_path = current_path + " -> " + child_name
                results.extend(self.find_paths_in_tree(child_data, package_name, package_version, new_path))

        return results
