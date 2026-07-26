import logging
from contextlib import contextmanager

from psycopg2 import pool
from psycopg2.extras import RealDictCursor

from config import DATABASE_URL

logger = logging.getLogger(__name__)

_connection_pool = None


# =========================================================
# CONNECTION POOL
# =========================================================

def init_connection_pool(
    minconn: int = 1,
    maxconn: int = 10,
):
    global _connection_pool

    if _connection_pool is None:
        _connection_pool = pool.SimpleConnectionPool(
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
# DATABASE EXECUTE
# =========================================================

def db_execute(
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