from database import get_connection
import os

AI_LIMIT = int(os.getenv("AI_LIMIT", "100"))
REPO_LIMIT = int(os.getenv("REPO_LIMIT", "20"))


def ensure_quota_tables():
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS user_quotas (
                user_id UUID PRIMARY KEY REFERENCES app_users(id) ON DELETE CASCADE,
                ai_used INTEGER NOT NULL DEFAULT 0,
                repo_used INTEGER NOT NULL DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        connection.commit()
    finally:
        cursor.close()
        connection.close()


def usage_payload(ai_used: int, repo_used: int) -> dict:
    ai_used = max(0, int(ai_used))
    repo_used = max(0, int(repo_used))
    return {
        "ai_used": ai_used,
        "ai_limit": AI_LIMIT,
        "ai_remaining": max(0, AI_LIMIT - ai_used),
        "repo_used": repo_used,
        "repo_limit": REPO_LIMIT,
        "repo_remaining": max(0, REPO_LIMIT - repo_used),
    }


def get_usage(user_id: str) -> dict:
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO user_quotas (user_id)
            VALUES (%s)
            ON CONFLICT (user_id) DO NOTHING
            """,
            (user_id,),
        )
        cursor.execute(
            """
            SELECT ai_used, repo_used
            FROM user_quotas
            WHERE user_id = %s
            """,
            (user_id,),
        )
        row = cursor.fetchone()
        connection.commit()
    finally:
        cursor.close()
        connection.close()

    ai_used, repo_used = row if row else (0, 0)
    return usage_payload(ai_used, repo_used)


class QuotaExceeded(Exception):
    def __init__(self, kind: str, usage: dict):
        self.kind = kind
        self.usage = usage
        super().__init__(kind)


def reserve_usage(user_id: str, consume_repo: bool) -> dict:
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO user_quotas (user_id)
            VALUES (%s)
            ON CONFLICT (user_id) DO NOTHING
            """,
            (user_id,),
        )
        cursor.execute(
            """
            SELECT ai_used, repo_used
            FROM user_quotas
            WHERE user_id = %s
            FOR UPDATE
            """,
            (user_id,),
        )
        row = cursor.fetchone()
        ai_used, repo_used = row if row else (0, 0)

        if ai_used >= AI_LIMIT:
            connection.rollback()
            raise QuotaExceeded("ai", usage_payload(ai_used, repo_used))

        if consume_repo and repo_used >= REPO_LIMIT:
            connection.rollback()
            raise QuotaExceeded("repo", usage_payload(ai_used, repo_used))

        cursor.execute(
            """
            UPDATE user_quotas
            SET
                ai_used = ai_used + 1,
                repo_used = repo_used + %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE user_id = %s
            RETURNING ai_used, repo_used
            """,
            (1 if consume_repo else 0, user_id),
        )
        updated = cursor.fetchone()
        connection.commit()
    except QuotaExceeded:
        raise
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()

    return usage_payload(updated[0], updated[1])


def refund_usage(user_id: str, consume_repo: bool) -> dict:
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            UPDATE user_quotas
            SET
                ai_used = GREATEST(ai_used - 1, 0),
                repo_used = GREATEST(repo_used - %s, 0),
                updated_at = CURRENT_TIMESTAMP
            WHERE user_id = %s
            RETURNING ai_used, repo_used
            """,
            (1 if consume_repo else 0, user_id),
        )
        row = cursor.fetchone()
        connection.commit()
    finally:
        cursor.close()
        connection.close()

    if not row:
        return get_usage(user_id)
    return usage_payload(row[0], row[1])
