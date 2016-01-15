import contextlib


class Backend(object):

    def __init__(self, *args, **kwargs):
        self.closed = False

    @contextlib.contextmanager
    def transaction(self):
            yield

    def generate(self, item, transaction):
        raise NotImplementedError()

    def get_next_pk(self, item, field):
        return None

    def close(self):
        self.closed = True

    def __del__(self):
        if not self.closed:
            try:
                self.close()
            except Exception:
                pass
