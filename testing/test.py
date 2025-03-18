import os
import subprocess
import xml.etree.ElementTree as ET


def find_base_path(start_path, target_dir):
    current = start_path
    while os.path.dirname(current) != current:
        if os.path.basename(current) == target_dir:
            return current
        child_path = os.path.join(current, target_dir)
        if os.path.exists(child_path) and os.path.isdir(child_path):
            return child_path
        current = os.path.dirname(current)
    return None


def is_parent_pom(pom_path):
    try:
        tree = ET.parse(pom_path)
        root = tree.getroot()
        ns = {'mvn': 'http://maven.apache.org/POM/4.0.0'}
        packaging = root.find('.//mvn:packaging', ns)
        parent = root.find('.//mvn:parent', ns)
        if (packaging is not None and packaging.text == 'pom') or parent is None:
            return True
        directory = os.path.dirname(pom_path)
        if os.path.basename(directory) == os.path.basename(os.path.dirname(directory)):
            return True
        return False
    except Exception:
        return True


def find_all_package_json():
    current_dir = os.getcwd()
    base_path = find_base_path(current_dir, "vultra")
    if not base_path:
        return []
    npm_path = os.path.join(base_path, "testing", "dep-files", "npm")
    if not os.path.exists(npm_path):
        return []
    package_paths = []
    try:
        project_dirs = os.listdir(npm_path)
        for project_name in project_dirs:
            project_dir = os.path.join(npm_path, project_name)
            if not os.path.isdir(project_dir):
                continue
            package_json_path = os.path.join(project_dir, "package.json")
            if os.path.exists(package_json_path):
                package_paths.append((project_name, package_json_path, "npm"))
    except Exception:
        return []
    return package_paths


def find_parent_pom_xml():
    current_dir = os.getcwd()
    base_path = find_base_path(current_dir, "vultra")
    if not base_path:
        return []
    mvn_path = os.path.join(base_path, "testing", "dep-files", "mvn")
    if not os.path.exists(mvn_path):
        return []
    pom_paths = []
    try:
        project_dirs = os.listdir(mvn_path)
        for project_name in project_dirs:
            project_dir = os.path.join(mvn_path, project_name)
            if not os.path.isdir(project_dir):
                continue
            pom_xml_path = os.path.join(project_dir, "pom.xml")
            if os.path.exists(pom_xml_path) and is_parent_pom(pom_xml_path):
                pom_paths.append((project_name, pom_xml_path, "mvn"))
    except Exception:
        return []
    return pom_paths


def call_main_py(framework, file_path):

    test_py_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(test_py_dir, "..", "src"))
    main_py_path = os.path.join(project_root, "main.py")
    print(main_py_path)

    if not os.path.exists(main_py_path):
        raise FileNotFoundError(f"main.py not found at expected location: {main_py_path}")

    try:
        result = subprocess.run(
            ["python", main_py_path, "--framework", framework, "--file", file_path],
            capture_output=True,
            text=True,
            check=True
        )

    except subprocess.CalledProcessError as e:
        print(f"\n=== Error for {framework} project ({file_path}) ===")
        print(f"Command failed with exit code {e.returncode}")
        print("STDOUT:\n", e.stdout)
        print("STDERR:\n", e.stderr)


def run_dependency_analysis():
    npm_results = find_all_package_json()
    mvn_results = find_parent_pom_xml()

    # Process npm projects
    for project_name, file_path, framework in npm_results:
        print(f"\nProcessing {framework} project: {project_name}")
        call_main_py(framework, file_path)

    # Process Maven projects
    for project_name, file_path, framework in mvn_results:
        print(f"\nProcessing {framework} project: {project_name}")
        call_main_py(framework, file_path)


def main():
    npm_results = find_all_package_json()
    mvn_results = find_parent_pom_xml()
    print("NPM Results:", npm_results)
    print("Maven Results:", mvn_results)


if __name__ == "__main__":
    main()
    run_dependency_analysis()
