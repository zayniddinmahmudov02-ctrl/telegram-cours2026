import logging
from contextlib import contextmanager

import psycopg2
from psycopg2 import pool

from config import DATABASE_URL

logger = logging.getLogger(__name__)

db_pool = None

# =========================================================
# DATABASE POOL MANAGEMENT
# =========================================================
db_pool = None

def init_db_pool():
    global db_pool
    try:
        if db_pool:
            try:
                db_pool.closeall()
            except Exception:
                pass

        db_pool = pool.ThreadedConnectionPool(
            minconn=1,
            maxconn=20,
            dsn=DATABASE_URL
        )
        logger.info("Database connected ✅")
    except Exception as e:
        logger.error(f"Database pool error: {e}")
        raise

@contextmanager
def get_db():
    global db_pool
    conn = None
    try:
        if not db_pool:
            init_db_pool()

        try:
            conn = db_pool.getconn()
        except Exception as e:
            logger.error(f"Reconnect DB: {e}")
            init_db_pool()
            conn = db_pool.getconn()

        yield conn
        conn.commit()
    except Exception as e:
        if conn:
            try:
                conn.rollback()
            except Exception:
                pass
        logger.error(f"DB transaction error: {e}")
        raise
    finally:
        if conn and db_pool:
            try:
                db_pool.putconn(conn)
            except Exception as e:
                logger.error(f"Return connection error: {e}")

def db_execute(query, params=(), fetchone=False, fetchall=False):
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                if fetchone:
                    return cur.fetchone()
                if fetchall:
                    return cur.fetchall()
        return None
    except Exception as e:
        logger.error(f"DB execute error: {e}")
        return None
# =========================================================
# INIT TABLES
# =========================================================

def init_tables():

    # USERS TABLE
    db_execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            full_name TEXT,
            phone TEXT,
            course TEXT,
            approved INTEGER DEFAULT 0,

            score INTEGER DEFAULT 0,
            total_score INTEGER DEFAULT 0,
            daily_score INTEGER DEFAULT 0,

            unlocked_level TEXT DEFAULT 'A1',
            last_daily_reset DATE,

            vizu_a1_access INTEGER DEFAULT 0,
            vizu_a2_access INTEGER DEFAULT 0,
            vizu_b1_access INTEGER DEFAULT 0,
            vizu_b2_access INTEGER DEFAULT 0,
            vizu_c1_access INTEGER DEFAULT 0
        )
    """)

    # MULTI BOT SUPPORT
    db_execute("""
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS bot_name TEXT DEFAULT 'vizu_academy_bot'
    """)

    db_execute("""
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS accepted_tasks INTEGER DEFAULT 0
    """)

    db_execute("""
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS rejected_tasks INTEGER DEFAULT 0
    """)
# =========================================================
# W CERTIFICATES TABLE
# =========================================================

def init_w_certificates_table():
    db_execute(
        """
        CREATE TABLE IF NOT EXISTS w_certificates (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            level TEXT NOT NULL,
            rank TEXT NOT NULL,
            cert_id TEXT UNIQUE NOT NULL,
            percent REAL NOT NULL,
            score INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT NOW(),
            UNIQUE (user_id, level)
        )
        """
    )

    # LESSON PROGRESS
    db_execute("""
        CREATE TABLE IF NOT EXISTS lesson_progress (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            level TEXT NOT NULL,
            lesson INTEGER NOT NULL,
            completed BOOLEAN DEFAULT FALSE,
            completed_at TIMESTAMP DEFAULT NOW(),
            UNIQUE (user_id, level, lesson)
        )
    """)

    # ACTIVE LESSONS
    db_execute("""
        CREATE TABLE IF NOT EXISTS active_lessons (
            user_id BIGINT PRIMARY KEY,
            level TEXT NOT NULL,
            lesson INTEGER NOT NULL,
            updated_at TIMESTAMP DEFAULT NOW()
        )
    """)

    # LESSON TASK PROGRESS
    db_execute("""
        CREATE TABLE IF NOT EXISTS lesson_task_progress (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            level TEXT NOT NULL,
            lesson INTEGER NOT NULL,
            task_name TEXT NOT NULL,
            completed BOOLEAN DEFAULT FALSE,
            completed_at TIMESTAMP DEFAULT NOW(),
            UNIQUE (user_id, level, lesson, task_name)
        )
    """)
def init_lesson_scores_and_indexes():
    """Module yuklanishida emas, init vaqtida chaqiriladi."""
    # LESSON SCORES
    db_execute("""
        CREATE TABLE IF NOT EXISTS lesson_scores (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            level TEXT NOT NULL,
            lesson INTEGER NOT NULL,
            task_name TEXT NOT NULL,
            score INTEGER DEFAULT 0,
            rated_by BIGINT,
            rated_at TIMESTAMP DEFAULT NOW(),
            UNIQUE (user_id, level, lesson, task_name)
        )
    """)
    # LEVEL EXAMS
    db_execute("""
        CREATE TABLE IF NOT EXISTS level_exams (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            level TEXT NOT NULL,
            score INTEGER DEFAULT 0,
            final_exam_passed BOOLEAN DEFAULT FALSE,
            passed_at TIMESTAMP DEFAULT NOW(),
            UNIQUE (user_id, level)
        )
    """)
    # LESSON ANSWERS
    db_execute("""
        CREATE TABLE IF NOT EXISTS lesson_answers (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            level TEXT NOT NULL,
            lesson INTEGER NOT NULL,
            task_type TEXT,
            answer_text TEXT,
            answer_file TEXT,
            checked BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)
    # QUIZ PROGRESS
    db_execute("""
        CREATE TABLE IF NOT EXISTS quiz_progress (
            user_id BIGINT NOT NULL,
            level TEXT NOT NULL,
            block_number INTEGER NOT NULL,
            best_score INTEGER DEFAULT 0,
            PRIMARY KEY (user_id, level, block_number)
        )
    """)
# =========================================================
# VIZU ATTEMPTS TABLE
# =========================================================

def init_vizu_attempts_table():

    db_execute("""
        CREATE TABLE IF NOT EXISTS vizu_attempts (

            id SERIAL PRIMARY KEY,

            user_id BIGINT NOT NULL,

            level TEXT NOT NULL,

            attempted_at TIMESTAMP DEFAULT NOW()

        )
    """)

    logger.info(
        "VIZU ATTEMPTS TABLE READY ✅"
    )
    # VIZU CERTIFICATE REQUESTS
    db_execute("""
        CREATE TABLE IF NOT EXISTS vizu_requests (
            id SERIAL PRIMARY KEY,

            user_id BIGINT NOT NULL,
            level TEXT NOT NULL,

            status TEXT DEFAULT 'pending',

            approved_by BIGINT,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)
# =========================================================
# VIZU LESEN RESULTS TABLE
# =========================================================

def init_vizu_lesen_results_table():

    db_execute("""
        CREATE TABLE IF NOT EXISTS vizu_lesen_results (

            user_id BIGINT PRIMARY KEY,

            score INTEGER DEFAULT 0,

            completed_at TIMESTAMP DEFAULT NOW()

        )
    """)

    logger.info(
        "VIZU LESEN RESULTS READY ✅"
    )

# =========================================================
# VIZU HOREN RESULTS TABLE
# =========================================================

def init_vizu_horen_results_table():
    db_execute("""
        CREATE TABLE IF NOT EXISTS vizu_horen_results (
            user_id BIGINT PRIMARY KEY,
            score INTEGER DEFAULT 0,
            completed_at TIMESTAMP DEFAULT NOW()
        )
    """)
    logger.info("VIZU HOREN RESULTS READY ✅")
# =========================================================
# VIZU SCHREIBEN RESULTS TABLE
# =========================================================

def init_vizu_schreiben_results_table():

    db_execute("""
        CREATE TABLE IF NOT EXISTS
        vizu_schreiben_results (

            user_id BIGINT PRIMARY KEY,

            score INTEGER DEFAULT 0,

            completed_at TIMESTAMP DEFAULT NOW()

        )
    """)

    logger.info(
        "VIZU SCHREIBEN RESULTS READY ✅"
    )
# =========================================================
# VIZU SPRECHEN RESULTS TABLE
# =========================================================

def init_vizu_sprechen_results_table():

    db_execute("""
        CREATE TABLE IF NOT EXISTS
        vizu_sprechen_results (

            user_id BIGINT PRIMARY KEY,

            score INTEGER DEFAULT 0,

            completed_at TIMESTAMP DEFAULT NOW()

        )
    """)

    logger.info(
        "VIZU SPRECHEN RESULTS READY ✅"
    )
# =========================================================
# CERTIFICATES TABLE
# =========================================================

def init_certificate_table():

    db_execute("""
        CREATE TABLE IF NOT EXISTS
        certificates (

            user_id BIGINT PRIMARY KEY,

            total_score INTEGER,

            created_at TIMESTAMP DEFAULT NOW()

        )
    """)

    logger.info(
        "CERTIFICATES TABLE READY ✅"
    )
    # INDEXES
    db_execute("CREATE INDEX IF NOT EXISTS idx_users_score ON users(score)")
    db_execute("CREATE INDEX IF NOT EXISTS idx_users_total_score ON users(total_score)")
    db_execute("CREATE INDEX IF NOT EXISTS idx_users_daily_score ON users(daily_score)")
    db_execute("CREATE INDEX IF NOT EXISTS idx_users_course ON users(course)")
    db_execute("CREATE INDEX IF NOT EXISTS idx_users_approved ON users(approved)")
    db_execute("CREATE INDEX IF NOT EXISTS idx_quiz_progress_user ON quiz_progress(user_id)")

# =========================================================
# DATABASE INIT
# =========================================================

def init_database():

    init_db_pool()

    init_tables()

    init_w_certificates_table()

    init_lesson_scores_and_indexes()

    init_vizu_attempts_table()

    init_vizu_lesen_results_table()

    init_vizu_horen_results_table()

    init_vizu_schreiben_results_table()

    init_vizu_sprechen_results_table()

    init_certificate_table()

    logger.info("DATABASE READY ✅")
