import contextlib


class Backend(object):

    def __init__(self, *args, **kwargs):
        self.closed = False

    @property
    def json_adapter(self):
        import json
        return json.dumps

    @contextlib.contextmanager
    def transaction(self):
        yield

    def write(self, item, objs):
        pass

    def select_random(self, table, fields=None, where=None, max_rows=None):
        raise NotImplementedError()

    def select(self, table, fields):
        raise NotImplementedError()

    def close(self):
        self.closed = True

    def __del__(self):
        if not self.closed:
            try:
                self.close()
            except Exception:
                pass
