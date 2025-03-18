from abc import ABC, abstractmethod

# This class can be extended to add support for new
# dependency management frameworks.
class DependencyParser(ABC):
    
    # Extract the dependency tree from a specified dependency file.
    @abstractmethod
    def get_dependency_tree(self, filepath):
        pass
    
    # Flatten the dependency tree.
    @abstractmethod
    def get_flat_dependency_set(self, dependencies_json):
        pass

    # Find all paths to a package (and version) in a dependency tree.
    @abstractmethod
    def find_paths_in_tree(self, dependency_tree, package_name, package_version, path=""):
        pass
