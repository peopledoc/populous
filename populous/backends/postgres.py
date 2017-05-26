import os
import random
import contextlib
import uuid

try:
    from functools import lru_cache
except ImportError:
    from functools32 import lru_cache

from populous.compat import range
from populous.exceptions import BackendError
from .base import Backend

try:
    import psycopg2
    import psycopg2.extras
except ImportError:
    raise BackendError("You must install 'psycopg2' in order to use the "
                       "Postgresql backend")


class Postgres(Backend):
    def __init__(self, *args, **kwargs):
        super(Postgres, self).__init__(*args, **kwargs)

        self._current_cursor = None

        dbname = kwargs.pop('db', None) or os.environ.get('PGDATABASE')
        try:
            self.conn = psycopg2.connect(dbname=dbname, **kwargs)
        except psycopg2.DatabaseError as e:
            raise BackendError("Error connecting to Postgresql DB: {}"
                               .format(e))

        # authorize uuids objects in queries
        psycopg2.extras.register_uuid()
        # authorize dicts objects for hstore in queries
        try:
            psycopg2.extras.register_hstore(self.conn)
        except psycopg2.ProgrammingError:
            # this probably means that the hstore extension is not
            # installed in the db, no need to register it then
            pass

    @property
    def json_adapter(self):
        from psycopg2.extras import Json
        return Json

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
            stmt = "INSERT INTO {} ({}) VALUES {} RETURNING {}".format(
                item.table,
                ", ".join(item.db_fields),
                ", ".join("({})".format(
                    ", ".join("%s" for _ in range(len(item.db_fields)))
                ) for _ in range(len(objs))),
                self.get_pk_column(item.table)
            )

            try:
                cursor.execute(stmt, tuple(v for vs in objs for v in vs))
            except psycopg2.DatabaseError as e:
                raise BackendError("Error during the generation of "
                                   "'{}': {}".format(item.name, e))

            return tuple(e[0] for e in cursor.fetchall())

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

    def select(self, table, fields):
        with self.conn.cursor(str(uuid.uuid4())) as cursor:
            cursor.execute(
                "SELECT {fields} FROM {table}"
                .format(
                    fields=', '.join(fields),
                    table=table
                )
            )

            for value in cursor:
                yield value

    @lru_cache()
    def get_pk_column(self, table):
        with self.cursor as cursor:
            cursor.execute(
                """
SELECT a.attname FROM pg_index i
JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
WHERE i.indrelid = %s::regclass AND i.indisprimary;
                """,
                (table,)
            )
            return cursor.fetchone()[0]

    def close(self):
        if not self.closed:
            try:
                self.conn.close()
            finally:
                self.closed = True
