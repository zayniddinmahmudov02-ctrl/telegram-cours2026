from database import db_execute


def reset_daily_scores():
    db_execute(
        """
        UPDATE users
        SET daily_score = 0
        """
    )