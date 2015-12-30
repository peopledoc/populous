import collections

import yaml


def load_yaml(*filenames):
    """
    Parse the given files as if they were a single YAML file.
    """
    with ChainedFileObject(*filenames) as f:
        return yaml.load(f)


class ChainedFileObject(object):
    """
    A file-like object behaving like if all the given filenames were a single
    file.

    Note that you never get content from several files during a single call to
    ``read``, even if the length of the requested buffer if longer that the
    remaining bytes in the current file. You have to call ``read`` again in
    order to get content from the next file.

    Can be used as a context manager (in a ``with`` statement).

    Example::
        >>> f = ChainedFileObject('foo.txt', 'bar.txt')
        >>> f.read()
        "I'm the content of foo.txt"
        >>> f.read(1024)
        "I'm the content of bar.txt"
        >>> f.read()
        ''
        >>> f.close()
    """

    def __init__(self, *filenames):
        self.filenames = collections.deque(filenames)
        self.current = None

        self.nextfile()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return self.close()

    def nextfile(self):
        current = self.current
        self.current = None

        try:
            if current:
                current.close()
        finally:
            try:
                self.current = open(self.filenames.popleft())
            except IndexError:
                self.current = None

    def read(self, n=None):
        if not self.current:
            return ''

        output = self.current.read()

        if not output:
            self.nextfile()
            return self.read()

        return output

    def close(self):
        current = self.current
        self.current = None

        if current:
            current.close()
