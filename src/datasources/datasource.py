class BaseDataSource:
    def __init__(self):
        self.next_handler = None

    def set_next(self, handler):
        self.next_handler = handler
        return handler

    def handle(self, package_name, package_version, ecosystem):
        raise NotImplementedError("This method should be overridden by subclasses")
