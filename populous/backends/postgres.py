import contextlib

from itertools import islice

from populous.exceptions import BackendError
from .base import Backend

try:
    import psycopg2
except ImportError:
    raise BackendError("You must install 'psycopg2' in order to use the "
                       "Postgresql backend")


BATCH_SIZE = 10000


def batches(generator, length):
    for _ in xrange(length // BATCH_SIZE):
        yield BATCH_SIZE, islice(generator, BATCH_SIZE)

    if length % BATCH_SIZE:
        yield length % BATCH_SIZE, islice(generator, BATCH_SIZE)


class Postgres(Backend):
    def __init__(self, *args, **kwargs):
        super(Postgres, self).__init__(*args, **kwargs)

        try:
            self.conn = psycopg2.connect(**kwargs)
        except psycopg2.DatabaseError as e:
            raise BackendError("Error connecting to Postgresql DB: {}"
                               .format(e))

    @contextlib.contextmanager
    def transaction(self):
        with self.conn:
            yield self.conn.cursor()

    def generate(self, item, cursor):
        for size, batch in batches(item.generate(), item.total):
            stmt = "INSERT INTO {} ({}) VALUES {}".format(
                item.table,
                ", ".join(item.fields.keys()),
                ", ".join("({})".format(
                    ", ".join("%s" for _ in xrange(len(item.fields)))
                ) for _ in xrange(size))
            )

            try:
                cursor.execute(stmt, tuple(v for vs in batch for v in vs))
            except psycopg2.DatabaseError as e:
                raise BackendError("Error during the generation of "
                                   "'{}': {}".format(item.name, e.message))

            yield size

    def get_next_pk(self, item, field):
        with self.conn.cursor() as cursor:
            cursor.execute(
                "SELECT nextval(pg_get_serial_sequence(%s, %s))",
                (item.table, field)
            )
            next_pk = cursor.fetchone()[0]
            # reset the counter to avoid holes
            cursor.execute(
                "SELECT setval(pg_get_serial_sequence(%s, %s), %s, false)",
                (item.table, field, next_pk)
            )
            return next_pk

    def close(self):
        if not self.closed:
            try:
                self.conn.close()
            finally:
                self.closed = True
