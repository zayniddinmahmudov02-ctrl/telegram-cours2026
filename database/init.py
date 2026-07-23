from .connection import db_execute


# =========================================================
# DATABASE INITIALIZATION
# =========================================================

def init_database():
    """Create all database tables."""

    create_users_table()

    create_quiz_progress_table()

    create_certificates_table()

    create_payments_table()

    create_homework_table()

    create_films_table()

    create_books_table()

    create_music_table()

    create_videos_table()


# =========================================================
# USERS
# =========================================================

def create_users_table():
    db_execute(
        """
        CREATE TABLE IF NOT EXISTS users(

            user_id BIGINT PRIMARY KEY,

            full_name TEXT,

            phone TEXT,

            approved BOOLEAN DEFAULT FALSE,

            unlocked_level VARCHAR(5) DEFAULT 'A1',

            total_score INTEGER DEFAULT 0,

            daily_score INTEGER DEFAULT 0,

            last_daily_reset DATE,

            created_at TIMESTAMP DEFAULT NOW()

        );
        """
    )


# =========================================================
# WORD GAME
# =========================================================

def create_quiz_progress_table():
    db_execute(
        """
        CREATE TABLE IF NOT EXISTS quiz_progress(

            user_id BIGINT,

            level VARCHAR(5),

            block_number INTEGER,

            best_score INTEGER DEFAULT 0,

            PRIMARY KEY(user_id, level, block_number)

        );
        """
    )


# =========================================================
# CERTIFICATES
# =========================================================

def create_certificates_table():
    db_execute(
        """
        CREATE TABLE IF NOT EXISTS certificates(

            id SERIAL PRIMARY KEY,

            certificate_id VARCHAR(32) UNIQUE NOT NULL,

            user_id BIGINT NOT NULL,

            certificate_type VARCHAR(30) NOT NULL,

            level VARCHAR(5) NOT NULL,

            score INTEGER,

            percent REAL,

            rank VARCHAR(20),

            created_at TIMESTAMP DEFAULT NOW(),

            UNIQUE(user_id, certificate_type, level)

        );
        """
    )


# =========================================================
# PAYMENTS
# =========================================================

def create_payments_table():
    db_execute(
        """
        CREATE TABLE IF NOT EXISTS payments(

            id SERIAL PRIMARY KEY,

            user_id BIGINT NOT NULL,

            course TEXT NOT NULL,

            amount INTEGER NOT NULL,

            receipt_file_id TEXT,

            status VARCHAR(20) DEFAULT 'pending',

            approved_at TIMESTAMP,

            created_at TIMESTAMP DEFAULT NOW()

        );
        """
    )


# =========================================================
# HOMEWORK
# =========================================================

def create_homework_table():
    db_execute(
        """
        CREATE TABLE IF NOT EXISTS homework(

            id SERIAL PRIMARY KEY,

            user_id BIGINT NOT NULL,

            level VARCHAR(5),

            lesson INTEGER,

            homework_type TEXT,

            file_id TEXT,

            status VARCHAR(20) DEFAULT 'pending',

            score INTEGER,

            teacher_comment TEXT,

            checked_at TIMESTAMP,

            created_at TIMESTAMP DEFAULT NOW()

        );
        """
    )


# =========================================================
# MEDIA - FILMS
# =========================================================

def create_films_table():
    db_execute(
        """
        CREATE TABLE IF NOT EXISTS films(

            id SERIAL PRIMARY KEY,

            title TEXT NOT NULL,

            description TEXT,

            telegram_file_id TEXT,

            created_at TIMESTAMP DEFAULT NOW()

        );
        """
    )


# =========================================================
# MEDIA - BOOKS
# =========================================================

def create_books_table():
    db_execute(
        """
        CREATE TABLE IF NOT EXISTS books(

            id SERIAL PRIMARY KEY,

            title TEXT NOT NULL,

            author TEXT,

            telegram_file_id TEXT,

            created_at TIMESTAMP DEFAULT NOW()

        );
        """
    )


# =========================================================
# MEDIA - MUSIC
# =========================================================

def create_music_table():
    db_execute(
        """
        CREATE TABLE IF NOT EXISTS music(

            id SERIAL PRIMARY KEY,

            title TEXT NOT NULL,

            artist TEXT,

            telegram_file_id TEXT,

            created_at TIMESTAMP DEFAULT NOW()

        );
        """
    )


# =========================================================
# MEDIA - VIDEOS
# =========================================================

def create_videos_table():
    db_execute(
        """
        CREATE TABLE IF NOT EXISTS videos(

            id SERIAL PRIMARY KEY,

            title TEXT NOT NULL,

            description TEXT,

            telegram_file_id TEXT,

            created_at TIMESTAMP DEFAULT NOW()

        );
        """
    )