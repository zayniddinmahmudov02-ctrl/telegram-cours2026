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

    create_films_table()

    create_books_table()

    create_music_table()

    create_videos_table()

    create_user_scores_table()

    create_xp_events_table()

    create_weekly_champions_table()

    create_monthly_champions_table()

    create_hall_of_fame_table()

    # Safe migrations for columns added after the initial deploy
    migrate_schema()
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

            is_blocked BOOLEAN DEFAULT FALSE,

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

            full_name TEXT,

            phone TEXT,

            username TEXT,

            course TEXT NOT NULL,

            amount INTEGER NOT NULL,

            receipt_file_id TEXT,

            file_type TEXT,

            status VARCHAR(20) DEFAULT 'pending',

            channel_id BIGINT,

            channel_message_id BIGINT,

            approved_by BIGINT,

            approved_at TIMESTAMP,

            rejected_by BIGINT,

            rejected_at TIMESTAMP,

            is_deleted BOOLEAN DEFAULT FALSE,

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
# =========================================================
# LEADERBOARD
# =========================================================

def create_user_scores_table():
    db_execute(
        """
        CREATE TABLE IF NOT EXISTS user_scores(

            user_id BIGINT PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,

            daily_score INTEGER DEFAULT 0,

            weekly_score INTEGER DEFAULT 0,

            monthly_score INTEGER DEFAULT 0,

            global_score INTEGER DEFAULT 0,

            correct_answers INTEGER DEFAULT 0,

            wrong_answers INTEGER DEFAULT 0,

            current_streak INTEGER DEFAULT 0,

            best_streak INTEGER DEFAULT 0,

            updated_at TIMESTAMP DEFAULT NOW()

        );
        """
    )


# =========================================================
# XP EVENTS
# =========================================================
# Per-event XP ledger. Lets daily/weekly/monthly rankings be
# computed with timestamp filtering (WHERE created_at >= ...)
# instead of periodically resetting a running counter.

def create_xp_events_table():
    db_execute(
        """
        CREATE TABLE IF NOT EXISTS xp_events(

            id SERIAL PRIMARY KEY,

            user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,

            xp INTEGER NOT NULL,

            created_at TIMESTAMP DEFAULT NOW()

        );
        """
    )

    db_execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_xp_events_user
        ON xp_events(user_id)
        """
    )

    db_execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_xp_events_created
        ON xp_events(created_at)
        """
    )


# =========================================================
# WEEKLY CHAMPIONS
# =========================================================

def create_weekly_champions_table():
    db_execute(
        """
        CREATE TABLE IF NOT EXISTS weekly_champions(

            id SERIAL PRIMARY KEY,

            year INTEGER NOT NULL,

            week INTEGER NOT NULL,

            user_id BIGINT NOT NULL,

            full_name TEXT,

            score INTEGER DEFAULT 0,

            created_at TIMESTAMP DEFAULT NOW()

        );
        """
    )
# =========================================================
# MONTHLY CHAMPIONS
# =========================================================

def create_monthly_champions_table():
    db_execute(
        """
        CREATE TABLE IF NOT EXISTS monthly_champions(

            id SERIAL PRIMARY KEY,

            year INTEGER NOT NULL,

            month INTEGER NOT NULL,

            user_id BIGINT NOT NULL,

            full_name TEXT,

            score INTEGER DEFAULT 0,

            created_at TIMESTAMP DEFAULT NOW()

        );
        """
    )


# =========================================================
# HALL OF FAME
# =========================================================

def create_hall_of_fame_table():
    db_execute(
        """
        CREATE TABLE IF NOT EXISTS hall_of_fame(

            id SERIAL PRIMARY KEY,

            year INTEGER NOT NULL,

            month INTEGER NOT NULL,

            champion_id INTEGER REFERENCES monthly_champions(id) ON DELETE CASCADE,

            created_at TIMESTAMP DEFAULT NOW()

        );
        """
    )


# =========================================================
# SAFE MIGRATIONS
# =========================================================
# CREATE TABLE IF NOT EXISTS above is a no-op on databases that
# already have these tables from before these columns existed.
# ADD COLUMN IF NOT EXISTS brings existing databases up to date
# without touching any existing rows.

def migrate_schema():

    # ---------------------------------------------------
    # USERS
    # ---------------------------------------------------

    db_execute(
        """
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS is_blocked BOOLEAN DEFAULT FALSE
        """
    )

    # ---------------------------------------------------
    # PAYMENTS
    # ---------------------------------------------------

    for column_sql in (
        "full_name TEXT",
        "phone TEXT",
        "username TEXT",
        "file_type TEXT",
        "channel_id BIGINT",
        "channel_message_id BIGINT",
        "approved_by BIGINT",
        "rejected_by BIGINT",
        "rejected_at TIMESTAMP",
        "is_deleted BOOLEAN DEFAULT FALSE",
    ):
        db_execute(
            f"""
            ALTER TABLE payments
            ADD COLUMN IF NOT EXISTS {column_sql}
            """
        )

    # ---------------------------------------------------
    # INDEXES
    # ---------------------------------------------------

    db_execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_users_is_blocked
        ON users(is_blocked)
        """
    )

    db_execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_payments_user_id
        ON payments(user_id)
        """
    )

    db_execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_payments_status
        ON payments(status)
        """
    )

    db_execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_user_scores_daily
        ON user_scores(daily_score DESC)
        """
    )

    db_execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_user_scores_weekly
        ON user_scores(weekly_score DESC)
        """
    )

    db_execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_user_scores_monthly
        ON user_scores(monthly_score DESC)
        """
    )

    db_execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_user_scores_global
        ON user_scores(global_score DESC)
        """
    )