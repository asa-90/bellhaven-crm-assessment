import sqlite3
from pathlib import Path
from datetime import datetime, timezone


BASE_DIR = Path(__file__).resolve().parent.parent

DB_PATH = (
    BASE_DIR
    / "data"
    / "review.db"
)


def get_connection():
    DB_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    connection = sqlite3.connect(
        DB_PATH
    )

    connection.row_factory = sqlite3.Row

    return connection


def initialize_db():

    connection = get_connection()

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS review_decisions (
            proposal_id TEXT PRIMARY KEY,

            website_name TEXT NOT NULL,

            crm_account_id TEXT,

            original_classification TEXT,

            decision TEXT NOT NULL,

            reviewer_note TEXT,

            approved_changes TEXT,

            decided_at TEXT NOT NULL
        )
        """
    )

    connection.commit()
    connection.close()


def get_decision(proposal_id):

    connection = get_connection()

    row = connection.execute(
        """
        SELECT *
        FROM review_decisions
        WHERE proposal_id = ?
        """,
        (proposal_id,),
    ).fetchone()

    connection.close()

    return row


def save_decision(
    proposal_id,
    website_name,
    crm_account_id,
    original_classification,
    decision,
    reviewer_note="",
    approved_changes="",
):

    connection = get_connection()

    decided_at = datetime.now(
        timezone.utc
    ).isoformat()

    connection.execute(
        """
        INSERT OR REPLACE INTO review_decisions (
            proposal_id,
            website_name,
            crm_account_id,
            original_classification,
            decision,
            reviewer_note,
            approved_changes,
            decided_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            proposal_id,
            website_name,
            crm_account_id,
            original_classification,
            decision,
            reviewer_note,
            approved_changes,
            decided_at,
        ),
    )

    connection.commit()
    connection.close()


def get_all_decisions():

    connection = get_connection()

    rows = connection.execute(
        """
        SELECT *
        FROM review_decisions
        ORDER BY decided_at DESC
        """
    ).fetchall()

    connection.close()

    return rows