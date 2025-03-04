import os
import json
import argparse
import subprocess
from pathlib import Path
from typing import Dict, Any, Set
import xml.etree.ElementTree as ET


def parse_package_json(file_path: Path) -> Dict[str, Any]:
    """Parse package.json and extract dependencies."""
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


def parse_pom_xml(file_path: Path) -> Dict[str, Any]:
    """Parse pom.xml and extract dependencies using mvn dependency:tree."""
    try:
        result = subprocess.run(
            ['mvn', 'dependency:tree', '-DoutputType=text', '-f', str(file_path)],
            capture_output=True,
            text=True,
            check=True,
            cwd=file_path.parent
        )
        return parse_maven_tree(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error running Maven for {file_path}: {e.stderr}")
        return {}


def parse_maven_tree(output: str) -> Dict[str, Any]:
    """Parse Maven's dependency:tree text output into a structured format."""
    tree = {}
    stack = []  # Track hierarchy (each item: (current_depth, node))

    for line in output.split('\n'):
        if '[INFO] ' not in line or ('+- ' not in line and '\\- ' not in line):
            continue

        line = line.split('[INFO] ')[1].strip()
        curr_depth = line.count('|  ')

        dep = line.replace('+- ', '').replace('\\- ', '').replace('|  ', '')
        parts = dep.split(':')
        if len(parts) < 4:
            continue

        group, artifact, packaging, version = parts[:4]
        key = f"{group}:{artifact}"

        node = {
            'group': group,
            'artifact': artifact,
            'version': version,
            'children': []
        }

        while stack and stack[-1][0] >= curr_depth:
            stack.pop()

        if not stack:
            tree[key] = node
        else:
            parent_depth, parent_node = stack[-1]
            parent_node['children'].append(node)

        stack.append((curr_depth, node))

    return tree


def run_npm_list(file_path: Path) -> Dict[str, Any]:
    """Run 'npm list' to extract dependencies."""
    try:
        result = subprocess.run(
            ['npm', 'list', '--all', '--json'],
            capture_output=True,
            text=True,
            check=True,
            cwd=file_path.parent
        )
        data = json.loads(result.stdout)
        return parse_npm_tree(data)
    except subprocess.CalledProcessError as e:
        print(f"Error running npm for {file_path}: {e.stderr}")
        return {}


def parse_npm_tree(data: Dict[str, Any], depth: int = 0, max_depth: int = 3) -> Dict[str, Any]:
    """Recursively parse npm's JSON output into a structured tree."""
    if depth > max_depth:
        return {}

    tree = {}
    for name, dep in data.get('dependencies', {}).items():
        version = dep.get('version', 'unknown')
        resolved = dep.get('resolved', '')

        children = parse_npm_tree(dep, depth + 1, max_depth) if 'dependencies' in dep else {}

        node = {
            'package': name,
            'version': version,
            'resolved': resolved,
            'children': children
        }
        tree[name] = node

    return tree


def extract_flat_dependencies(tree: Dict[str, Any], flat_set: Set[str]):
    """Extract dependencies in a flat format."""
    for name, node in tree.items():
        if not isinstance(node, dict):
            continue

        group = node.get('group', '')
        artifact = node.get('artifact', '')
        package = node.get('package', name)
        version = node.get('version', 'unknown')

        if artifact:
            flat_set.add(f"{group}:{artifact}@{version}")
        else:
            flat_set.add(f"{package}@{version}")

        children = node.get('children', {})
        if isinstance(children, dict):
            extract_flat_dependencies(children, flat_set)
        elif isinstance(children, list):
            for child in children:
                if isinstance(child, dict):
                    extract_flat_dependencies({child.get('artifact', child.get('package')): child}, flat_set)


def print_tree(tree: Dict[str, Any], indent: int = 0, depth: int = 0, max_depth: int = 3) -> None:
    """Recursively print the dependency tree."""
    if isinstance(tree, dict):
        for name, node in tree.items():
            if not isinstance(node, dict):
                continue

            key_name = node.get('group', node.get('package', name))
            artifact_name = node.get('artifact', '')
            version = node.get('version', 'unknown')

            prefix = '└── ' if indent == 0 else '├── '
            if artifact_name:
                print(f"{' ' * indent}{prefix}{key_name}:{artifact_name}@{version}")
            else:
                print(f"{' ' * indent}{prefix}{key_name}@{version}")

            children = node.get('children')
            if children and depth < max_depth:
                if isinstance(children, list):
                    new_children = {f"{child.get('group', '')}:{child.get('artifact', '')}": child for child in children if isinstance(child, dict)}
                    print_tree(new_children, indent + 4, depth + 1, max_depth)
                elif isinstance(children, dict):
                    print_tree(children, indent + 4, depth + 1, max_depth)


def parse_manifest(file_path: Path) -> Dict[str, Any]:
    """Determine file type and parse dependencies accordingly."""
    if file_path.suffix == ".xml":
        return parse_pom_xml(file_path)
    elif file_path.suffix == ".json":
        return run_npm_list(file_path)
    else:
        raise ValueError("Unsupported file type. Please use a pom.xml or package.json file.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Dependency Analyzer")
    parser.add_argument("file", type=str, help="Path to dependency file (pom.xml or package.json)")
    parser.add_argument("--depth", type=int, default=3, help="Depth of dependencies to show (default: 3)")
    args = parser.parse_args()

    file_path = Path(args.file)
    if not file_path.exists():
        print(f"Error: File not found - {file_path}")
        return

    print(f"\nAnalyzing {file_path.name}...")

    try:
        tree = parse_manifest(file_path)

        if tree:
            print("\nDependency Tree:")
            print_tree(tree, max_depth=args.depth)

            flat_dependencies = set()
            extract_flat_dependencies(tree, flat_dependencies)

            print("\nFlat Dependency Set:")
            for dep in sorted(flat_dependencies):
                print(dep)
        else:
            print("No dependencies found or error occurred.")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
