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
# USERS MIGRATION
# =========================================================

db_execute("""
    ALTER TABLE users
    ADD COLUMN IF NOT EXISTS course TEXT
""")

db_execute("""
    ALTER TABLE users
    ADD COLUMN IF NOT EXISTS approved INTEGER DEFAULT 0
""")

db_execute("""
    ALTER TABLE users
    ADD COLUMN IF NOT EXISTS score INTEGER DEFAULT 0
""")

db_execute("""
    ALTER TABLE users
    ADD COLUMN IF NOT EXISTS total_score INTEGER DEFAULT 0
""")

db_execute("""
    ALTER TABLE users
    ADD COLUMN IF NOT EXISTS daily_score INTEGER DEFAULT 0
""")

db_execute("""
    ALTER TABLE users
    ADD COLUMN IF NOT EXISTS unlocked_level TEXT DEFAULT 'A1'
""")

db_execute("""
    ALTER TABLE users
    ADD COLUMN IF NOT EXISTS last_daily_reset DATE
""")

db_execute("""
    ALTER TABLE users
    ADD COLUMN IF NOT EXISTS vizu_a1_access INTEGER DEFAULT 0
""")

db_execute("""
    ALTER TABLE users
    ADD COLUMN IF NOT EXISTS vizu_a2_access INTEGER DEFAULT 0
""")

db_execute("""
    ALTER TABLE users
    ADD COLUMN IF NOT EXISTS vizu_b1_access INTEGER DEFAULT 0
""")

db_execute("""
    ALTER TABLE users
    ADD COLUMN IF NOT EXISTS vizu_b2_access INTEGER DEFAULT 0
""")

db_execute("""
    ALTER TABLE users
    ADD COLUMN IF NOT EXISTS vizu_c1_access INTEGER DEFAULT 0
""")
# =========================================================
# HOMEWORK CATEGORIES
# =========================================================

def init_homework_categories():

    db_execute("""
        CREATE TABLE IF NOT EXISTS homework_categories (

            id SERIAL PRIMARY KEY,

            code TEXT UNIQUE NOT NULL,

            title TEXT NOT NULL,

            access_type TEXT NOT NULL,

            price INTEGER DEFAULT 0,

            active BOOLEAN DEFAULT TRUE,

            created_at TIMESTAMP DEFAULT NOW()

        )
        
    """)
    db_execute("""
    INSERT INTO homework_categories
    (code,title,access_type,price)

    VALUES
    ('online','Online Kurs','promo',0),
    ('video','Video Kurs','payment',0),
    ('speaking','Speaking Kurs','promo_payment',49000)

    ON CONFLICT (code) DO NOTHING
    """)
    logger.info("HOMEWORK CATEGORIES READY ✅")

# =========================================================
# HOMEWORK ACCESS
# =========================================================

def init_homework_access():

    db_execute("""
        CREATE TABLE IF NOT EXISTS homework_access(

            id SERIAL PRIMARY KEY,

            user_id BIGINT NOT NULL,

            category_code TEXT NOT NULL,

            active BOOLEAN DEFAULT TRUE,

            source TEXT NOT NULL,

            activated_at TIMESTAMP DEFAULT NOW(),

            expires_at TIMESTAMP,

            UNIQUE(user_id, category_code)

        )
    """)

    db_execute("""
        CREATE INDEX IF NOT EXISTS idx_homework_access_user
        ON homework_access(user_id)
    """)

    db_execute("""
        CREATE INDEX IF NOT EXISTS idx_homework_access_category
        ON homework_access(category_code)
    """)

    logger.info("HOMEWORK ACCESS READY ✅")

# =========================================================
# ACCESS CODES
# =========================================================

def init_access_codes():

    db_execute("""
        CREATE TABLE IF NOT EXISTS access_codes(

            id SERIAL PRIMARY KEY,

            code TEXT UNIQUE NOT NULL,

            category_code TEXT NOT NULL,

            max_activations INTEGER DEFAULT 1,

            used_count INTEGER DEFAULT 0,

            active BOOLEAN DEFAULT TRUE,

            created_at TIMESTAMP DEFAULT NOW()

        )
    """)

    logger.info("ACCESS CODES READY ✅")
# =========================================================
# HOMEWORK ASSIGNMENTS
# =========================================================

def init_homework_assignments():

    db_execute("""
    CREATE TABLE IF NOT EXISTS homework_assignments(

        id SERIAL PRIMARY KEY,

        category_code TEXT NOT NULL,

        level TEXT,

        lesson INTEGER,

        competency TEXT NOT NULL,

        title TEXT NOT NULL,

        description TEXT,

        allow_text BOOLEAN DEFAULT TRUE,
        allow_photo BOOLEAN DEFAULT TRUE,
        allow_audio BOOLEAN DEFAULT TRUE,
        allow_voice BOOLEAN DEFAULT TRUE,
        allow_pdf BOOLEAN DEFAULT TRUE,
        allow_document BOOLEAN DEFAULT TRUE,

        max_files INTEGER DEFAULT 20,

        active BOOLEAN DEFAULT TRUE,

        created_at TIMESTAMP DEFAULT NOW()
    )
    """)

    logger.info("HOMEWORK ASSIGNMENTS READY ✅")
    # =========================================================
# HOMEWORK SUBMISSIONS
# =========================================================

def init_homework_submissions():

    db_execute("""
    CREATE TABLE IF NOT EXISTS homework_submissions(

        id SERIAL PRIMARY KEY,

        user_id BIGINT NOT NULL,

        assignment_id INTEGER NOT NULL,

        category_code TEXT NOT NULL,

        level TEXT,

        lesson INTEGER,

        competency TEXT,

        status TEXT DEFAULT 'submitted',

        created_at TIMESTAMP DEFAULT NOW(),

        UNIQUE(user_id,assignment_id)
    )
    """)

    logger.info("HOMEWORK SUBMISSIONS READY ✅")

    # =========================================================
# HOMEWORK FILES
# =========================================================

def init_homework_files():

    db_execute("""
    CREATE TABLE IF NOT EXISTS homework_files(

        id SERIAL PRIMARY KEY,

        submission_id INTEGER NOT NULL,

        file_id TEXT,

        file_type TEXT,

        file_name TEXT,

        telegram_message_id BIGINT,

        created_at TIMESTAMP DEFAULT NOW()
    )
    """)

    logger.info("HOMEWORK FILES READY ✅")
    # =========================================================
# HOMEWORK SCORES
# =========================================================

def init_homework_scores():

    db_execute("""
    CREATE TABLE IF NOT EXISTS homework_scores(

        id SERIAL PRIMARY KEY,

        submission_id INTEGER UNIQUE NOT NULL,

        teacher_id BIGINT,

        score INTEGER,

        feedback TEXT,

        scored_at TIMESTAMP DEFAULT NOW()
    )
    """)

    logger.info("HOMEWORK SCORES READY ✅")
    # =========================================================
# TEACHER QUESTIONS
# =========================================================

def init_teacher_questions():

    db_execute("""
    CREATE TABLE IF NOT EXISTS teacher_questions(

        id SERIAL PRIMARY KEY,

        user_id BIGINT NOT NULL,

        category_code TEXT,

        level TEXT,

        lesson INTEGER,

        status TEXT DEFAULT 'OPEN',

        created_at TIMESTAMP DEFAULT NOW()
    )
    """)

    logger.info("TEACHER QUESTIONS READY ✅")
    # =========================================================
# TEACHER QUESTION FILES
# =========================================================

def init_teacher_question_files():

    db_execute("""
    CREATE TABLE IF NOT EXISTS teacher_question_files(

        id SERIAL PRIMARY KEY,

        question_id INTEGER NOT NULL,

        file_id TEXT,

        file_type TEXT,

        file_name TEXT,

        telegram_message_id BIGINT,

        created_at TIMESTAMP DEFAULT NOW()
    )
    """)

    logger.info("TEACHER QUESTION FILES READY ✅")
    # =========================================================
# TEACHER ANSWERS
# =========================================================

def init_teacher_answers():

    db_execute("""
    CREATE TABLE IF NOT EXISTS teacher_answers(

        id SERIAL PRIMARY KEY,

        question_id INTEGER UNIQUE NOT NULL,

        teacher_id BIGINT,

        answer TEXT,

        created_at TIMESTAMP DEFAULT NOW()
    )
    """)

    logger.info("TEACHER ANSWERS READY ✅")
    # =========================================================
# SUBMISSION LOGS
# =========================================================

def init_submission_logs():

    db_execute("""
    CREATE TABLE IF NOT EXISTS submission_logs(

        id SERIAL PRIMARY KEY,

        submission_id INTEGER,

        action TEXT,

        actor_id BIGINT,

        created_at TIMESTAMP DEFAULT NOW()
    )
    """)

    logger.info("SUBMISSION LOGS READY ✅")
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

# =========================================================
# INDEXES
# =========================================================

db_execute("""
CREATE INDEX IF NOT EXISTS idx_users_score
ON users(score)
""")

db_execute("""
CREATE INDEX IF NOT EXISTS idx_users_total_score
ON users(total_score)
""")

db_execute("""
CREATE INDEX IF NOT EXISTS idx_users_daily_score
ON users(daily_score)
""")

db_execute("""
CREATE INDEX IF NOT EXISTS idx_users_course
ON users(course)
""")

db_execute("""
CREATE INDEX IF NOT EXISTS idx_users_approved
ON users(approved)
""")

db_execute("""
CREATE INDEX IF NOT EXISTS idx_users_level
ON users(unlocked_level)
""")

db_execute("""
CREATE INDEX IF NOT EXISTS idx_quiz_progress_user
ON quiz_progress(user_id)
""")

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

    init_homework_categories()

    init_homework_access()

    init_access_codes()
    init_homework_assignments()
    init_homework_submissions()
    init_homework_files()
    init_homework_scores()

    init_teacher_questions()
    init_teacher_question_files()
    init_teacher_answers()

    init_submission_logs()
    logger.info("DATABASE READY ✅")

# =========================================================
# HOMEWORK HELPERS
# =========================================================

def has_homework_access(user_id, category):
    row = db_execute(
        """
        SELECT active
        FROM homework_access
        WHERE user_id=%s
          AND category_code=%s
        """,
        (user_id, category),
        fetchone=True
    )

    return bool(row and row[0])


def grant_homework_access(user_id, category, source):
    db_execute(
        """
        INSERT INTO homework_access
            (user_id, category_code, source)

        VALUES
            (%s, %s, %s)

        ON CONFLICT (user_id, category_code)

        DO UPDATE SET
            active = TRUE,
            source = EXCLUDED.source,
            activated_at = NOW()
        """,
        (user_id, category, source)
    )


def revoke_homework_access(user_id, category):
    db_execute(
        """
        UPDATE homework_access

        SET
            active = FALSE

        WHERE
            user_id = %s
            AND category_code = %s
        """,
        (user_id, category)
    )


def get_homework_access(user_id):
    return db_execute(
        """
        SELECT
            category_code,
            active,
            source,
            activated_at,
            expires_at

        FROM homework_access

        WHERE user_id=%s

        ORDER BY category_code
        """,
        (user_id,),
        fetch=True
    )


def get_user_homework_categories(user_id):
    rows = db_execute(
        """
        SELECT category_code

        FROM homework_access

        WHERE
            user_id=%s
            AND active=TRUE
        """,
        (user_id,),
        fetch=True
    )

    return [row[0] for row in rows] if rows else []

def get_access_code(code):

    return db_execute(
        """
        SELECT *

        FROM access_codes

        WHERE code=%s
        """,
        (code,),
        fetchone=True
    )
def increase_access_code_usage(code):
    db_execute(
        """
        UPDATE access_codes

        SET used_count=used_count+1

        WHERE code=%s
        """,
        (code,)
    )


def create_access_code(code, category):

    db_execute(
        """
        INSERT INTO access_codes

        (code,category_code)

        VALUES(%s,%s)

        ON CONFLICT(code)

        DO NOTHING
        """,
        (code, category)
    )