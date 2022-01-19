class PopulousError(Exception):
    pass

class YAMLError(PopulousError):

    def __init__(self, filename, problem):
        super().__init__(
            f"Error parsing '{filename}': {problem}"
        )


class ValidationError(PopulousError):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filename = kwargs.pop('filename', None)

    def __str__(self):
        msg = super().__str__()
        if self.filename:
            return f"File '{self.filename}': {msg}"
        else:
            return msg


class GenerationError(PopulousError):
    pass


class BackendError(PopulousError):
    pass
