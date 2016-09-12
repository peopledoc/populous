import random
import contextlib

try:
    from functools import lru_cache
except ImportError:
    from functools32 import lru_cache

from populous.exceptions import BackendError
from .base import Backend

try:
    import psycopg2
except ImportError:
    raise BackendError("You must install 'psycopg2' in order to use the "
                       "Postgresql backend")


class Postgres(Backend):
    def __init__(self, *args, **kwargs):
        super(Postgres, self).__init__(*args, **kwargs)

        self._current_cursor = None

        try:
            self.conn = psycopg2.connect(**kwargs)
        except psycopg2.DatabaseError as e:
            raise BackendError("Error connecting to Postgresql DB: {}"
                               .format(e))

    @property
    @contextlib.contextmanager
    def cursor(self):
        if self._current_cursor:
            yield self._current_cursor
        else:
            with self.conn.cursor() as cursor:
                yield cursor

    @contextlib.contextmanager
    def transaction(self):
        with self.conn:
            with self.conn.cursor() as cursor:
                self._current_cursor = cursor
                yield cursor
                self._current_cursor = None

    def write(self, item, objs):
        with self.cursor as cursor:
            stmt = "INSERT INTO {} ({}) VALUES {}".format(
                item.table,
                ", ".join(item.db_fields),
                ", ".join("({})".format(
                    ", ".join("%s" for _ in xrange(len(item.db_fields)))
                ) for _ in xrange(len(objs)))
            )

            try:
                cursor.execute(stmt, tuple(v for vs in objs for v in vs))
            except psycopg2.DatabaseError as e:
                raise BackendError("Error during the generation of "
                                   "'{}': {}".format(item.name, e.message))

    def get_next_pk(self, item, field):
        with self.cursor as cursor:
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

    @lru_cache()
    def count(self, table, where=None):
        with self.cursor as cursor:
            cursor.execute("SELECT count(*) FROM {table} {where}".format(
                table=table,
                where="WHERE ({})".format(where) if where else '',
            ))
            return cursor.fetchone()[0]

    def select_random(self, table, fields=None, where=None, max_rows=1000):
        with self.cursor as cursor:
            count = self.count(table, where=where)

            cursor.execute(
                "SELECT {fields} FROM {table} "
                "WHERE random() < {proportion} {extra_where} {limit}"
                .format(
                    table=table,
                    fields=', '.join(fields),
                    proportion=min(max_rows / float(count), 1.0),
                    extra_where="AND ({})".format(where) if where else '',
                    limit="LIMIT {}".format(max_rows)
                )
            )

            results = cursor.fetchall()
            random.shuffle(results)
            return results

    def close(self):
        if not self.closed:
            try:
                self.conn.close()
            finally:
                self.closed = True
