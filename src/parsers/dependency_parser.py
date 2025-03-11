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