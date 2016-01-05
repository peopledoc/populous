

class Backend(object):

    def __init__(self, *args, **kwargs):
        self.closed = False

    def generate(self, blueprint):
        raise NotImplementedError()

    def close(self):
        self.closed = True

    def __del__(self):
        if not self.closed:
            try:
                self.close()
            except Exception:
                pass
