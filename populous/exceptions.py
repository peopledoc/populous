class PopulousError(Exception):
    pass


class YAMLError(PopulousError):

    def __init__(self, filename, problem):
        super(YAMLError, self).__init__(
            "Error parsing '{}': {}".format(filename, problem)
        )


class ValidationError(PopulousError):
    pass


class BackendError(PopulousError):
    pass
