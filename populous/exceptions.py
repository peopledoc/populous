from .compat import PY2


class PopulousError(Exception):

    if PY2:
        def __unicode__(self):
            return str(self).decode('utf-8')


class YAMLError(PopulousError):

    def __init__(self, filename, problem):
        super(YAMLError, self).__init__(
            "Error parsing '{}': {}".format(filename, problem)
        )


class ValidationError(PopulousError):

    def __init__(self, *args, **kwargs):
        super(ValidationError, self).__init__(*args, **kwargs)
        self.filename = kwargs.pop('filename', None)

    def __str__(self):
        msg = super(ValidationError, self).__str__()
        if self.filename:
            return "File '{}': {}".format(self.filename, msg)
        else:
            return msg


class GenerationError(PopulousError):
    pass


class BackendError(PopulousError):
    pass
