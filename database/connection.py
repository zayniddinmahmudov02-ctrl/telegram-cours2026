import asyncio
import functools
import logging
from contextlib import contextmanager
from concurrent.futures import ThreadPoolExecutor

from psycopg2 import pool
from psycopg2.extras import RealDictCursor

from config import DATABASE_URL

logger = logging.getLogger(__name__)

_connection_pool = None

# =========================================================
# CONNECTION POOL
# =========================================================
# ThreadedConnectionPool (not SimpleConnectionPool) is required
# here: db_execute() below dispatches every query onto a worker
# thread (see _DB_EXECUTOR), so multiple threads call
# getconn()/putconn() concurrently. SimpleConnectionPool is
# documented as not safe for that; ThreadedConnectionPool is.

_POOL_MINCONN = 2
_POOL_MAXCONN = 20

# One executor dedicated to DB I/O, sized to the pool so a burst
# of concurrent queries can never queue up more threads than
# there are connections to serve them (each thread borrows at
# most one connection for the lifetime of a single query).
_DB_EXECUTOR = ThreadPoolExecutor(
    max_workers=_POOL_MAXCONN,
    thread_name_prefix="db",
)


def init_connection_pool(
    minconn: int = _POOL_MINCONN,
    maxconn: int = _POOL_MAXCONN,
):
    global _connection_pool

    if _connection_pool is None:
        _connection_pool = pool.ThreadedConnectionPool(
            minconn=minconn,
            maxconn=maxconn,
            dsn=DATABASE_URL,
        )

        logger.info(
            "✅ PostgreSQL connection pool initialized"
        )


# =========================================================
# GET CONNECTION
# =========================================================

@contextmanager
def get_connection():
    global _connection_pool

    if _connection_pool is None:
        init_connection_pool()

    conn = _connection_pool.getconn()

    try:
        yield conn

    finally:
        _connection_pool.putconn(conn)


# =========================================================
# DATABASE EXECUTE (blocking body - always run on a worker
# thread, never directly on the event loop)
# =========================================================

def _db_execute_sync(
    query,
    params=None,
    *,
    fetchone=False,
    fetchall=False,
):
    with get_connection() as conn:
        try:
            with conn.cursor(
                cursor_factory=RealDictCursor
            ) as cur:

                cur.execute(query, params)

                result = None

                if fetchone:
                    result = cur.fetchone()

                elif fetchall:
                    result = cur.fetchall()

                conn.commit()

                return result

        except Exception as e:
            conn.rollback()

            logger.exception(
                "Database query failed: %s",
                e,
            )

            raise


# =========================================================
# DATABASE EXECUTE (async-facing) - offloads the blocking
# psycopg2 call to _DB_EXECUTOR so it never blocks the asyncio
# event loop, letting other users' updates keep being processed
# concurrently while a query is in flight.
# =========================================================

async def db_execute(
    query,
    params=None,
    *,
    fetchone=False,
    fetchall=False,
):
    loop = asyncio.get_running_loop()

    return await loop.run_in_executor(
        _DB_EXECUTOR,
        functools.partial(
            _db_execute_sync,
            query,
            params,
            fetchone=fetchone,
            fetchall=fetchall,
        ),
    )


# =========================================================
# CLOSE CONNECTION POOL
# =========================================================

def close_pool():
    global _connection_pool

    if _connection_pool is not None:
        _connection_pool.closeall()
        _connection_pool = None

        logger.info(
            "✅ PostgreSQL connection pool closed"
        )
