import random

from .base import Generator, fake


class IP(Generator):

    def get_arguments(self, ipv4=True, ipv6=True, **kwargs):
        super(IP, self).get_arguments(**kwargs)
        self.ipv4 = ipv4
        self.ipv6 = ipv6

    def generate(self):
        if self.ipv4 and self.ipv6:
            return self.generate_both()
        elif self.ipv4:
            return self.generate_ipv4()
        else:
            return self.generate_ipv6()

    def generate_ipv4(self):
        while True:
            yield fake.ipv4()

    def generate_ipv6(self):
        while True:
            yield fake.ipv6()

    def generate_both(self):
        while True:
            if random.random() >= 0.5:
                yield fake.ipv4()
            else:
                yield fake.ipv6()
