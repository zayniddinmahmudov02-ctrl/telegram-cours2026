from .connection import db_execute
from .homework import seed_homework_categories

# =========================================================
# DATABASE INITIALIZATION
# =========================================================

async def init_database():
    """Create all database tables."""

    await create_users_table()

    await create_quiz_progress_table()

    await create_certificates_table()

    await create_payments_table()

    await create_films_table()

    await create_books_table()

    await create_music_table()

    await create_videos_table()

    await create_favorite_music_table()

    await create_homework_categories_table()

    await create_homework_memberships_table()

    await create_homework_submissions_table()

    await create_homework_submission_files_table()

    await create_homework_evaluations_table()

    await seed_homework_categories()

    await create_user_scores_table()

    await create_xp_events_table()

    await create_daily_champions_table()

    await create_weekly_champions_table()

    await create_monthly_champions_table()

    await create_hall_of_fame_table()

    # Safe migrations for columns added after the initial deploy
    await migrate_schema()
# =========================================================
# USERS
# =========================================================

async def create_users_table():
    await db_execute(
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

async def create_quiz_progress_table():
    await db_execute(
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

async def create_certificates_table():
    await db_execute(
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

async def create_payments_table():
    await db_execute(
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

async def create_films_table():
    await db_execute(
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

async def create_books_table():
    await db_execute(
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

async def create_music_table():
    await db_execute(
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

async def create_videos_table():
    await db_execute(
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
# MEDIA - FAVORITE MUSIC
# =========================================================
# Personal per-user favorites for the Musik gallery. message_id
# is the same Musik.csv/MUSIC_CHANNEL_ID message id used to play
# the song, not a foreign key to the (unused) music table above.

async def create_favorite_music_table():
    await db_execute(
        """
        CREATE TABLE IF NOT EXISTS favorite_music(

            id SERIAL PRIMARY KEY,

            telegram_id BIGINT NOT NULL,

            message_id INTEGER NOT NULL,

            created_at TIMESTAMP DEFAULT NOW(),

            UNIQUE(telegram_id, message_id)

        );
        """
    )

    await db_execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_favorite_music_telegram_id
        ON favorite_music(telegram_id)
        """
    )


# =========================================================
# HAUSAUFGABEN - CATEGORIES
# =========================================================
# code is the stable key used by config.HOMEWORK_CATEGORIES to
# seed/refresh these rows on startup (see database.homework.
# seed_homework_categories). password_hash/salt are NULL until an
# admin sets one via the Admin Panel - a category with no password
# set simply can't be unlocked yet (see services.homework).

async def create_homework_categories_table():
    await db_execute(
        """
        CREATE TABLE IF NOT EXISTS homework_categories(

            id SERIAL PRIMARY KEY,

            code VARCHAR(20) UNIQUE NOT NULL,

            name TEXT NOT NULL,

            channel_id BIGINT NOT NULL,

            password_hash TEXT,

            password_salt TEXT,

            is_active BOOLEAN DEFAULT TRUE,

            created_at TIMESTAMP DEFAULT NOW(),

            updated_at TIMESTAMP DEFAULT NOW()

        );
        """
    )


# =========================================================
# HAUSAUFGABEN - MEMBERSHIPS (per-user, per-category profile
# + access grant - a row existing means the user unlocked that
# category and never needs the password again)
# =========================================================

async def create_homework_memberships_table():
    await db_execute(
        """
        CREATE TABLE IF NOT EXISTS homework_memberships(

            id SERIAL PRIMARY KEY,

            user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,

            category_id INTEGER NOT NULL REFERENCES homework_categories(id) ON DELETE CASCADE,

            first_name TEXT NOT NULL,

            last_name TEXT NOT NULL,

            level VARCHAR(5) NOT NULL,

            lesson_number INTEGER NOT NULL,

            created_at TIMESTAMP DEFAULT NOW(),

            updated_at TIMESTAMP DEFAULT NOW(),

            UNIQUE(user_id, category_id)

        );
        """
    )

    await db_execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_homework_memberships_user
        ON homework_memberships(user_id)
        """
    )

    await db_execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_homework_memberships_category
        ON homework_memberships(category_id)
        """
    )


# =========================================================
# HAUSAUFGABEN - SUBMISSIONS
# =========================================================
# first_name/last_name/level/lesson_number here are an immutable
# snapshot taken from the membership at submission time - if the
# user later edits their profile, past submissions must keep
# showing what was true when they were made.

async def create_homework_submissions_table():
    await db_execute(
        """
        CREATE TABLE IF NOT EXISTS homework_submissions(

            id SERIAL PRIMARY KEY,

            submission_uid VARCHAR(20) UNIQUE NOT NULL,

            user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,

            category_id INTEGER NOT NULL REFERENCES homework_categories(id) ON DELETE CASCADE,

            first_name TEXT NOT NULL,

            last_name TEXT NOT NULL,

            level VARCHAR(5) NOT NULL,

            lesson_number INTEGER NOT NULL,

            status VARCHAR(20) NOT NULL DEFAULT 'draft',

            channel_id BIGINT,

            channel_message_id BIGINT,

            created_at TIMESTAMP DEFAULT NOW(),

            submitted_at TIMESTAMP,

            evaluated_at TIMESTAMP

        );
        """
    )

    for index_sql in (
        "idx_homework_submissions_user ON homework_submissions(user_id)",
        "idx_homework_submissions_category ON homework_submissions(category_id)",
        "idx_homework_submissions_lesson ON homework_submissions(lesson_number)",
        "idx_homework_submissions_status ON homework_submissions(status)",
        "idx_homework_submissions_created ON homework_submissions(created_at)",
    ):
        await db_execute(f"CREATE INDEX IF NOT EXISTS {index_sql}")


# =========================================================
# HAUSAUFGABEN - SUBMISSION FILES
# =========================================================
# One row per uploaded file OR per text message in a submission,
# ordered by `position` - this is what lets a submission mix
# audio -> image -> pdf -> text and still be replayed to the
# channel in the exact order the user sent it.

async def create_homework_submission_files_table():
    await db_execute(
        """
        CREATE TABLE IF NOT EXISTS homework_submission_files(

            id SERIAL PRIMARY KEY,

            submission_id INTEGER NOT NULL REFERENCES homework_submissions(id) ON DELETE CASCADE,

            file_type VARCHAR(20) NOT NULL,

            file_id TEXT,

            file_name TEXT,

            mime_type TEXT,

            file_size BIGINT,

            text_content TEXT,

            position INTEGER NOT NULL,

            created_at TIMESTAMP DEFAULT NOW()

        );
        """
    )

    await db_execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_homework_submission_files_submission
        ON homework_submission_files(submission_id)
        """
    )


# =========================================================
# HAUSAUFGABEN - EVALUATIONS
# =========================================================
# UNIQUE(submission_id) is what makes "one current score per
# submission" structural rather than a convention to remember -
# database.homework_evaluations always UPSERTs on this constraint,
# so re-scoring updates the one row in place and SUM(score) across
# this table can never double-count a submission.

async def create_homework_evaluations_table():
    await db_execute(
        """
        CREATE TABLE IF NOT EXISTS homework_evaluations(

            id SERIAL PRIMARY KEY,

            submission_id INTEGER UNIQUE NOT NULL REFERENCES homework_submissions(id) ON DELETE CASCADE,

            score SMALLINT NOT NULL CHECK (score BETWEEN 1 AND 5),

            result_status VARCHAR(20) NOT NULL,

            evaluator_id BIGINT NOT NULL,

            created_at TIMESTAMP DEFAULT NOW(),

            updated_at TIMESTAMP DEFAULT NOW()

        );
        """
    )


# =========================================================
# LEADERBOARD
# =========================================================

async def create_user_scores_table():
    await db_execute(
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
#
# created_at is TIMESTAMPTZ (not plain TIMESTAMP) on purpose:
# it stores an unambiguous absolute instant, so day/week/month
# boundary queries can convert it to a specific timezone
# (see get_top() in database/leaderboard.py) and get correct
# results regardless of the database server's own configured
# timezone. A plain TIMESTAMP column has no such guarantee -
# its stored value silently depends on whatever session
# timezone was active at INSERT time.

async def create_xp_events_table():
    await db_execute(
        """
        CREATE TABLE IF NOT EXISTS xp_events(

            id SERIAL PRIMARY KEY,

            user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,

            xp INTEGER NOT NULL,

            created_at TIMESTAMPTZ DEFAULT NOW()

        );
        """
    )

    await db_execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_xp_events_user
        ON xp_events(user_id)
        """
    )

    await db_execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_xp_events_created
        ON xp_events(created_at)
        """
    )


# =========================================================
# DAILY CHAMPIONS
# =========================================================

async def create_daily_champions_table():
    await db_execute(
        """
        CREATE TABLE IF NOT EXISTS daily_champions(

            id SERIAL PRIMARY KEY,

            champion_date DATE NOT NULL,

            user_id BIGINT NOT NULL,

            full_name TEXT,

            score INTEGER DEFAULT 0,

            created_at TIMESTAMP DEFAULT NOW()

        );
        """
    )

    await db_execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS
        idx_daily_champions_date
        ON daily_champions(champion_date)
        """
    )


# =========================================================
# WEEKLY CHAMPIONS
# =========================================================

async def create_weekly_champions_table():
    await db_execute(
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

    await db_execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS
        idx_weekly_champions_period
        ON weekly_champions(year, week)
        """
    )
# =========================================================
# MONTHLY CHAMPIONS
# =========================================================

async def create_monthly_champions_table():
    await db_execute(
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

    await db_execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS
        idx_monthly_champions_period
        ON monthly_champions(year, month)
        """
    )


# =========================================================
# HALL OF FAME
# =========================================================

async def create_hall_of_fame_table():
    await db_execute(
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

async def migrate_schema():

    # ---------------------------------------------------
    # USERS
    # ---------------------------------------------------

    await db_execute(
        """
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS is_blocked BOOLEAN DEFAULT FALSE
        """
    )

    for column_sql in (
        "first_name TEXT",
        "last_name TEXT",
        "username TEXT",
        "language_code VARCHAR(10)",
        "is_premium BOOLEAN DEFAULT FALSE",
        "is_deleted BOOLEAN DEFAULT FALSE",
        "last_seen TIMESTAMPTZ",
        "updated_at TIMESTAMPTZ DEFAULT NOW()",
    ):
        await db_execute(
            f"""
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS {column_sql}
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
        await db_execute(
            f"""
            ALTER TABLE payments
            ADD COLUMN IF NOT EXISTS {column_sql}
            """
        )

    # ---------------------------------------------------
    # INDEXES
    # ---------------------------------------------------

    await db_execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_users_is_blocked
        ON users(is_blocked)
        """
    )

    await db_execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_users_is_deleted
        ON users(is_deleted)
        """
    )

    await db_execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_users_last_seen
        ON users(last_seen)
        """
    )

    await db_execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_users_created_at
        ON users(created_at)
        """
    )

    await db_execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_payments_user_id
        ON payments(user_id)
        """
    )

    await db_execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_payments_status
        ON payments(status)
        """
    )

    await db_execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_user_scores_daily
        ON user_scores(daily_score DESC)
        """
    )

    await db_execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_user_scores_weekly
        ON user_scores(weekly_score DESC)
        """
    )

    await db_execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_user_scores_monthly
        ON user_scores(monthly_score DESC)
        """
    )

    await db_execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_user_scores_global
        ON user_scores(global_score DESC)
        """
    )

    # ---------------------------------------------------
    # XP_EVENTS - upgrade created_at to TIMESTAMPTZ
    # ---------------------------------------------------
    # Safe/idempotent: only fires once, the first time this
    # runs against a database created before created_at was
    # made timezone-aware. Existing values are assumed to have
    # been written as UTC wall-clock (Postgres/NOW() default),
    # which is the same assumption a fresh TIMESTAMPTZ column
    # makes going forward - no XP values are changed, only the
    # column's timezone-awareness.

    await db_execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_name = 'xp_events'
                AND column_name = 'created_at'
                AND data_type = 'timestamp without time zone'
            ) THEN
                ALTER TABLE xp_events
                ALTER COLUMN created_at
                TYPE TIMESTAMPTZ
                USING created_at AT TIME ZONE 'UTC';
            END IF;
        END $$;
        """
    )
