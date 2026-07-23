import logging
from contextlib import contextmanager

import psycopg2
from psycopg2 import pool

from config import DATABASE_URL

logger = logging.getLogger(__name__)


_connection_pool = None


def init_connection_pool(minconn: int = 1, maxconn: int = 10):
    global _connection_pool

    if _connection_pool is None:
        _connection_pool = pool.SimpleConnectionPool(
            minconn,
            maxconn,
            DATABASE_URL,
        )
        logger.info("✅ PostgreSQL connection pool initialized")


@contextmanager
def get_connection():
    if _connection_pool is None:
        init_connection_pool()

    conn = _connection_pool.getconn()

    try:
        yield conn
    finally:
        _connection_pool.putconn(conn)


def db_execute(
    query,
    params=None,
    *,
    fetchone=False,
    fetchall=False,
):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)

            if fetchone:
                return cur.fetchone()

            if fetchall:
                return cur.fetchall()

            conn.commit()


def close_pool():
    global _connection_pool

    if _connection_pool:
        _connection_pool.closeall()
        logger.info("✅ PostgreSQL pool closed")