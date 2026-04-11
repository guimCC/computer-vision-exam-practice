from __future__ import annotations
import hashlib
import html
import json
import random
import re
import sqlite3
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import streamlit as st


APP_DIR = Path(__file__).resolve().parent
BANK_PATH = APP_DIR / "question_bank.json"
REPORT_PATH = APP_DIR / "build_report.json"
DB_PATH = APP_DIR / "progress.sqlite3"
LETTERS = "abcdefghijklmnopqrstuvwxyz"
LOCAL_USER_ID = "__local_guest__"
LOCAL_USER_NAME = "Local guest"
INLINE_MATH_RE = re.compile(r"\\\((.*?)\\\)")
BLOCK_MATH_RE = re.compile(r"\\\[(.*?)\\\]", re.DOTALL)


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def inject_css() -> None:
    st.markdown(
        """
        <style>
        :root {
            --app-bg: #070b10;
            --app-bg-soft: #0d131c;
            --panel: rgba(14, 20, 29, 0.86);
            --panel-strong: rgba(18, 26, 38, 0.96);
            --panel-muted: rgba(24, 35, 50, 0.86);
            --border: #223243;
            --border-strong: #2f455d;
            --text: #eef4fb;
            --muted: #9cb0c5;
            --accent: #8dd4c5;
            --accent-strong: #76c8ef;
            --accent-text: #051019;
            --warm: #f3c77f;
            --success: #8fd0a8;
            --shadow: 0 16px 44px rgba(0, 0, 0, 0.32);
        }
        .stApp {
            background:
                radial-gradient(circle at top left, rgba(118, 200, 239, 0.16) 0%, transparent 26%),
                radial-gradient(circle at top right, rgba(141, 212, 197, 0.12) 0%, transparent 22%),
                linear-gradient(180deg, #0e141d 0%, var(--app-bg) 42%, #05070b 100%);
            color: var(--text);
        }
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0b1118 0%, #090e14 100%);
            border-right: 1px solid var(--border);
        }
        [data-testid="stSidebar"] * {
            color: var(--text) !important;
        }
        .block-container {
            max-width: 1024px;
            padding-top: 1.35rem;
            padding-bottom: 2.6rem;
        }
        .hero {
            background: linear-gradient(135deg, rgba(118, 200, 239, 0.14) 0%, rgba(141, 212, 197, 0.08) 100%);
            border: 1px solid var(--border-strong);
            border-radius: 22px;
            padding: 1.5rem 1.7rem;
            margin-bottom: 0.9rem;
            box-shadow: var(--shadow);
            backdrop-filter: blur(8px);
        }
        .hero h1 {
            margin: 0 0 0.45rem 0;
            font-size: 2.2rem;
            line-height: 1.1;
            color: var(--text);
        }
        .hero p {
            margin: 0;
            color: var(--muted);
            font-size: 1rem;
            line-height: 1.62;
        }
        .section-kicker {
            text-transform: uppercase;
            letter-spacing: 0.12em;
            font-size: 0.82rem;
            font-weight: 700;
            color: var(--accent-strong);
            margin-bottom: 0.28rem;
        }
        .section-title {
            font-size: 1.8rem;
            font-weight: 700;
            margin-bottom: 0.2rem;
            color: var(--text);
        }
        .section-subtitle {
            color: var(--muted);
            font-size: 0.98rem;
            margin-bottom: 0.9rem;
        }
        .badge-row {
            margin: 0.25rem 0 0.9rem 0;
        }
        .badge {
            display: inline-block;
            padding: 0.36rem 0.7rem;
            border-radius: 999px;
            margin: 0 0.45rem 0.45rem 0;
            border: 1px solid var(--border);
            background: rgba(22, 31, 44, 0.78);
            color: var(--text);
            font-size: 0.83rem;
            font-weight: 600;
        }
        .badge.cool {
            background: rgba(118, 200, 239, 0.14);
            border-color: rgba(118, 200, 239, 0.35);
            color: #b4e3f7;
        }
        .badge.warm {
            background: rgba(243, 199, 127, 0.14);
            border-color: rgba(243, 199, 127, 0.34);
            color: #ffdca7;
        }
        .badge.success {
            background: rgba(143, 208, 168, 0.14);
            border-color: rgba(143, 208, 168, 0.34);
            color: #bbe7ca;
        }
        [data-testid="stMetric"] {
            background: var(--panel);
            border: 1px solid var(--border);
            border-radius: 18px;
            padding: 0.75rem 0.9rem;
            box-shadow: none;
        }
        [data-testid="stMetricValue"] {
            color: var(--text);
        }
        [data-testid="stMetricLabel"],
        [data-testid="stMetricDelta"],
        [data-testid="stCaptionContainer"] {
            color: var(--muted) !important;
        }
        [data-testid="stVerticalBlockBorderWrapper"] {
            background: var(--panel);
            border: 1px solid var(--border);
            border-radius: 18px;
            box-shadow: none;
        }
        [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stMarkdownContainer"] p,
        [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stMarkdownContainer"] li {
            font-size: 1rem;
            line-height: 1.72;
            color: var(--text);
        }
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] li,
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] p {
            color: var(--text) !important;
        }
        div[data-baseweb="radio"] > div label,
        div[data-baseweb="checkbox"] > div label {
            background: rgba(17, 25, 36, 0.78);
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 0.72rem 0.86rem;
            margin-bottom: 0.48rem;
        }
        div[data-baseweb="radio"] > div label:hover,
        div[data-baseweb="checkbox"] > div label:hover {
            border-color: var(--accent-strong);
            background: rgba(28, 43, 62, 0.9);
        }
        div[data-baseweb="radio"] > div label p,
        div[data-baseweb="checkbox"] > div label p {
            font-size: 0.98rem;
            line-height: 1.45;
            color: var(--text) !important;
        }
        [data-testid="stButton"] button,
        [data-testid="stFormSubmitButton"] button {
            background: linear-gradient(135deg, var(--accent) 0%, var(--accent-strong) 100%);
            color: var(--accent-text) !important;
            border: none;
            border-radius: 14px;
            font-weight: 700;
            min-height: 2.8rem;
            box-shadow: 0 12px 28px rgba(15, 27, 39, 0.24);
        }
        [data-testid="stButton"] button:hover,
        [data-testid="stFormSubmitButton"] button:hover {
            background: linear-gradient(135deg, #9fe0d2 0%, #88d2f7 100%);
            color: #031019 !important;
            transform: translateY(-1px);
        }
        [data-testid="stButton"] button:focus,
        [data-testid="stFormSubmitButton"] button:focus {
            box-shadow: 0 0 0 0.16rem rgba(136, 210, 247, 0.32);
        }
        [data-testid="stButton"] button:disabled,
        [data-testid="stFormSubmitButton"] button:disabled {
            background: rgba(79, 92, 107, 0.46);
            color: rgba(226, 234, 243, 0.56) !important;
            box-shadow: none;
            transform: none;
        }
        [data-testid="stSelectbox"] label,
        [data-testid="stRadio"] label,
        [data-testid="stMultiSelect"] label {
            color: var(--text) !important;
        }
        [data-testid="stSelectbox"] [data-baseweb="select"] > div,
        [data-testid="stMultiSelect"] [data-baseweb="select"] > div {
            background: rgba(17, 25, 36, 0.86);
            border-color: var(--border);
        }
        h1, h2, h3, h4, h5, h6 {
            color: var(--text);
        }
        a {
            color: #9dd7ff !important;
        }
        .resume-callout {
            border: 1px solid rgba(141, 212, 197, 0.34);
            background: linear-gradient(135deg, rgba(141, 212, 197, 0.12) 0%, rgba(118, 200, 239, 0.08) 100%);
            border-radius: 18px;
            padding: 0.95rem 1rem;
            margin-bottom: 0.85rem;
        }
        .resume-callout strong {
            color: var(--text);
        }
        .mcq-review-option {
            padding: 0.78rem 0.9rem;
            border-radius: 14px;
            border: 1px solid var(--border);
            background: rgba(14, 20, 29, 0.88);
            margin-bottom: 0.58rem;
        }
        .mcq-review-option.correct {
            border-color: rgba(143, 208, 168, 0.52);
            background: rgba(143, 208, 168, 0.12);
        }
        .mcq-review-option.selected {
            border-color: rgba(243, 199, 127, 0.46);
            background: rgba(243, 199, 127, 0.10);
        }
        .mcq-review-option.correct.selected {
            border-color: rgba(118, 200, 239, 0.54);
            background: rgba(118, 200, 239, 0.12);
        }
        .mcq-review-tags {
            margin-top: 0.42rem;
        }
        .mcq-review-tag {
            display: inline-block;
            margin-right: 0.4rem;
            padding: 0.16rem 0.48rem;
            border-radius: 999px;
            font-size: 0.76rem;
            font-weight: 700;
            border: 1px solid var(--border);
            color: var(--text);
        }
        .mcq-review-tag.correct {
            border-color: rgba(143, 208, 168, 0.52);
            color: #bbe7ca;
        }
        .mcq-review-tag.selected {
            border-color: rgba(243, 199, 127, 0.46);
            color: #ffdca7;
        }
        .llm-copy-shell {
            display: flex;
            justify-content: flex-end;
            align-items: center;
            min-height: 2rem;
        }
        .llm-copy-button {
            width: 2rem;
            height: 2rem;
            border-radius: 999px;
            border: 1px solid var(--border);
            background: rgba(17, 25, 36, 0.92);
            color: var(--muted);
            display: inline-flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: all 120ms ease;
            padding: 0;
        }
        .llm-copy-button:hover {
            border-color: var(--accent-strong);
            color: var(--text);
            background: rgba(28, 43, 62, 0.95);
        }
        .llm-copy-button.copied {
            border-color: rgba(143, 208, 168, 0.52);
            color: #bbe7ca;
            background: rgba(143, 208, 168, 0.12);
        }
        .llm-copy-glyph {
            font-size: 1rem;
            line-height: 1;
            font-weight: 700;
            transform: translateY(-0.02rem);
        }
        .topic-meta {
            color: var(--muted);
            font-size: 0.95rem;
            line-height: 1.55;
            margin-bottom: 0.45rem;
        }
        .topic-progress {
            width: 100%;
            height: 0.58rem;
            display: flex;
            overflow: hidden;
            border-radius: 999px;
            background: rgba(16, 24, 36, 0.92);
            border: 1px solid rgba(34, 50, 67, 0.75);
            margin: 0.2rem 0 0.2rem 0;
        }
        .topic-progress-fill {
            height: 100%;
        }
        .topic-progress-fill.is-mastered {
            background: linear-gradient(135deg, rgba(141, 212, 197, 0.98) 0%, rgba(118, 200, 239, 0.95) 100%);
        }
        .topic-progress-fill.is-failed {
            background: linear-gradient(135deg, rgba(235, 110, 110, 0.98) 0%, rgba(211, 73, 73, 0.95) 100%);
        }
        .topic-progress-fill.is-unseen {
            background: rgba(23, 33, 46, 0.98);
        }
        .sticky-anchor {
            display: none;
        }
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.sticky-anchor) {
            position: sticky;
            top: 0.65rem;
            z-index: 20;
            backdrop-filter: blur(10px);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def auth_is_configured() -> bool:
    try:
        auth_section = st.secrets.get("auth", {})
    except Exception:
        return False
    return bool(auth_section)


def current_user_context() -> dict[str, Any]:
    if not auth_is_configured():
        return {
            "requires_login": False,
            "authenticated": False,
            "user_id": LOCAL_USER_ID,
            "display_name": LOCAL_USER_NAME,
            "email": None,
        }

    if not getattr(st.user, "is_logged_in", False):
        return {
            "requires_login": True,
            "authenticated": False,
            "user_id": None,
            "display_name": None,
            "email": None,
        }

    user_data = st.user.to_dict()
    email = (user_data.get("email") or "").strip().casefold() or None
    user_id = email or str(user_data.get("sub") or user_data.get("name") or "authenticated-user")
    display_name = user_data.get("name") or email or "Authenticated user"
    return {
        "requires_login": False,
        "authenticated": True,
        "user_id": user_id,
        "display_name": display_name,
        "email": email,
    }


def render_login_gate() -> None:
    st.markdown(
        """
        <div class="hero">
            <h1>Sign in to keep your own progress</h1>
            <p>
                Use your personal account so your phone and laptop share the same study status
                while staying separate from everyone else in the class.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    with st.container(border=True):
        st.markdown("### Login required")
        st.write("This hosted app stores progress per signed-in user inside the app database.")
        st.write("Sign in with your own account to load your bookmarks, mistakes, and confidence ratings.")
        st.button("Log in", width="stretch", on_click=st.login)
    st.stop()


def ensure_progress_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS progress (
            user_id TEXT NOT NULL,
            question_id TEXT NOT NULL,
            attempts INTEGER NOT NULL DEFAULT 0,
            correct_count INTEGER NOT NULL DEFAULT 0,
            incorrect_count INTEGER NOT NULL DEFAULT 0,
            last_result INTEGER,
            first_seen_at TEXT,
            last_seen_at TEXT,
            bookmarked INTEGER NOT NULL DEFAULT 0,
            confidence_level INTEGER,
            confidence_updated_at TEXT,
            notes_text TEXT,
            notes_updated_at TEXT,
            PRIMARY KEY (user_id, question_id)
        )
        """
        )


def ensure_user_state_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS user_state (
            user_id TEXT PRIMARY KEY,
            last_section TEXT,
            last_mcq_category TEXT,
            last_mcq_mode TEXT,
            last_mcq_question_id TEXT,
            last_problem_category TEXT,
            last_problem_filter TEXT,
            last_problem_question_id TEXT,
            updated_at TEXT NOT NULL
        )
        """
    )


def ensure_mcq_session_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS mcq_session (
            user_id TEXT PRIMARY KEY,
            category TEXT NOT NULL,
            mode TEXT NOT NULL,
            queue_json TEXT NOT NULL,
            current_index INTEGER NOT NULL DEFAULT 0,
            answers_json TEXT NOT NULL DEFAULT '{}',
            started_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )


def init_db(default_user_id: str = LOCAL_USER_ID) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        table_exists = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'progress'"
        ).fetchone()

        if not table_exists:
            ensure_progress_table(conn)
        else:
            table_info = list(conn.execute("PRAGMA table_info(progress)"))
            columns = {row[1] for row in table_info}
            primary_key_columns = [row[1] for row in sorted(table_info, key=lambda row: row[5]) if row[5]]

            if "user_id" not in columns or primary_key_columns != ["user_id", "question_id"]:
                conn.execute("ALTER TABLE progress RENAME TO progress_legacy")
                ensure_progress_table(conn)

                legacy_columns = {row[1] for row in conn.execute("PRAGMA table_info(progress_legacy)")}

                def legacy_col(name: str, fallback: str) -> str:
                    return name if name in legacy_columns else fallback

                conn.execute(
                    f"""
                    INSERT INTO progress (
                        user_id,
                        question_id,
                        attempts,
                        correct_count,
                        incorrect_count,
                        last_result,
                        first_seen_at,
                        last_seen_at,
                        bookmarked,
                        confidence_level,
                        confidence_updated_at,
                        notes_text,
                        notes_updated_at
                    )
                    SELECT
                        ?,
                        question_id,
                        {legacy_col("attempts", "0")},
                        {legacy_col("correct_count", "0")},
                        {legacy_col("incorrect_count", "0")},
                        {legacy_col("last_result", "NULL")},
                        {legacy_col("first_seen_at", "NULL")},
                        {legacy_col("last_seen_at", "NULL")},
                        {legacy_col("bookmarked", "0")},
                        {legacy_col("confidence_level", "NULL")},
                        {legacy_col("confidence_updated_at", "NULL")},
                        {legacy_col("notes_text", "NULL")},
                        {legacy_col("notes_updated_at", "NULL")}
                    FROM progress_legacy
                    """,
                    (default_user_id,),
                )
                conn.execute("DROP TABLE progress_legacy")

        columns = {row[1] for row in conn.execute("PRAGMA table_info(progress)")}
        if "confidence_level" not in columns:
            conn.execute("ALTER TABLE progress ADD COLUMN confidence_level INTEGER")
        if "confidence_updated_at" not in columns:
            conn.execute("ALTER TABLE progress ADD COLUMN confidence_updated_at TEXT")
        if "notes_text" not in columns:
            conn.execute("ALTER TABLE progress ADD COLUMN notes_text TEXT")
        if "notes_updated_at" not in columns:
            conn.execute("ALTER TABLE progress ADD COLUMN notes_updated_at TEXT")
        ensure_user_state_table(conn)
        ensure_mcq_session_table(conn)


def load_bank() -> list[dict[str, Any]]:
    if not BANK_PATH.exists():
        return []
    return json.loads(BANK_PATH.read_text(encoding="utf-8"))


def load_report() -> dict[str, Any]:
    if not REPORT_PATH.exists():
        return {}
    return json.loads(REPORT_PATH.read_text(encoding="utf-8"))


def load_progress(user_id: str) -> dict[str, dict[str, Any]]:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM progress WHERE user_id = ?", (user_id,)).fetchall()
    return {row["question_id"]: dict(row) for row in rows}


def load_user_state(user_id: str) -> dict[str, Any]:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM user_state WHERE user_id = ?", (user_id,)).fetchone()
    return dict(row) if row else {}


def load_mcq_session(user_id: str) -> dict[str, Any] | None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM mcq_session WHERE user_id = ?", (user_id,)).fetchone()

    if not row:
        return None

    session = dict(row)
    try:
        session["queue_ids"] = json.loads(session.pop("queue_json") or "[]")
    except json.JSONDecodeError:
        session["queue_ids"] = []
    try:
        session["answers"] = json.loads(session.pop("answers_json") or "{}")
    except json.JSONDecodeError:
        session["answers"] = {}
    session["current_index"] = max(0, int(session.get("current_index", 0) or 0))
    return session


def save_mcq_session(
    user_id: str,
    category: str,
    mode: str,
    queue_ids: list[str],
    current_index: int,
    answers: dict[str, Any],
    *,
    started_at: str | None = None,
) -> dict[str, Any]:
    now = utc_now()
    started_at = started_at or now
    current_index = max(0, min(current_index, max(len(queue_ids) - 1, 0))) if queue_ids else 0
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO mcq_session (
                user_id,
                category,
                mode,
                queue_json,
                current_index,
                answers_json,
                started_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                category = excluded.category,
                mode = excluded.mode,
                queue_json = excluded.queue_json,
                current_index = excluded.current_index,
                answers_json = excluded.answers_json,
                started_at = excluded.started_at,
                updated_at = excluded.updated_at
            """,
            (
                user_id,
                category,
                mode,
                json.dumps(queue_ids, ensure_ascii=False),
                current_index,
                json.dumps(answers, ensure_ascii=False),
                started_at,
                now,
            ),
        )

    return {
        "user_id": user_id,
        "category": category,
        "mode": mode,
        "queue_ids": queue_ids,
        "current_index": current_index,
        "answers": answers,
        "started_at": started_at,
        "updated_at": now,
    }


def clear_mcq_session(user_id: str) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM mcq_session WHERE user_id = ?", (user_id,))


def save_user_state(user_id: str, **updates: Any) -> None:
    allowed_fields = {
        "last_section",
        "last_mcq_category",
        "last_mcq_mode",
        "last_mcq_question_id",
        "last_problem_category",
        "last_problem_filter",
        "last_problem_question_id",
    }
    payload = {key: value for key, value in updates.items() if key in allowed_fields}
    if not payload:
        return

    now = utc_now()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO user_state (user_id, updated_at) VALUES (?, ?) ON CONFLICT(user_id) DO NOTHING",
            (user_id, now),
        )
        assignments = ", ".join(f"{field} = ?" for field in payload)
        conn.execute(
            f"UPDATE user_state SET {assignments}, updated_at = ? WHERE user_id = ?",
            [*payload.values(), now, user_id],
        )


def ensure_progress_row(user_id: str, question_id: str) -> None:
    now = utc_now()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO progress (user_id, question_id, first_seen_at, last_seen_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id, question_id) DO NOTHING
            """,
            (user_id, question_id, now, now),
        )


def record_attempt(user_id: str, question_id: str, is_correct: bool) -> None:
    ensure_progress_row(user_id, question_id)
    now = utc_now()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            UPDATE progress
            SET attempts = attempts + 1,
                correct_count = correct_count + ?,
                incorrect_count = incorrect_count + ?,
                last_result = ?,
                first_seen_at = COALESCE(first_seen_at, ?),
                last_seen_at = ?
            WHERE user_id = ? AND question_id = ?
            """,
            (
                1 if is_correct else 0,
                0 if is_correct else 1,
                1 if is_correct else 0,
                now,
                now,
                user_id,
                question_id,
            ),
        )


def set_bookmark(user_id: str, question_id: str, bookmarked: bool) -> None:
    ensure_progress_row(user_id, question_id)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "UPDATE progress SET bookmarked = ?, last_seen_at = ? WHERE user_id = ? AND question_id = ?",
            (1 if bookmarked else 0, utc_now(), user_id, question_id),
        )


def set_confidence(user_id: str, question_id: str, confidence_level: int) -> None:
    ensure_progress_row(user_id, question_id)
    now = utc_now()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            UPDATE progress
            SET confidence_level = ?,
                confidence_updated_at = ?,
                last_seen_at = ?
            WHERE user_id = ? AND question_id = ?
            """,
            (confidence_level, now, now, user_id, question_id),
        )


def save_notes(user_id: str, question_id: str, notes_text: str) -> None:
    ensure_progress_row(user_id, question_id)
    now = utc_now()
    normalized = notes_text.strip()
    stored_notes = normalized or None
    stored_updated_at = now if stored_notes else None
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            UPDATE progress
            SET notes_text = ?,
                notes_updated_at = ?,
                last_seen_at = ?
            WHERE user_id = ? AND question_id = ?
            """,
            (stored_notes, stored_updated_at, now, user_id, question_id),
        )


def clear_mcq_topic_progress(user_id: str, bank: list[dict[str, Any]], category: str) -> None:
    question_ids = [
        item["id"]
        for item in bank
        if item["type"] == "multiple_choice" and primary_category(item) == category
    ]
    if not question_ids:
        return

    placeholders = ", ".join("?" for _ in question_ids)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            f"DELETE FROM progress WHERE user_id = ? AND question_id IN ({placeholders})",
            (user_id, *question_ids),
        )


def render_rich_text(text: str) -> None:
    if not text:
        return
    text = BLOCK_MATH_RE.sub(lambda match: f"\n\n$$ {match.group(1).strip()} $$\n\n", text)
    text = INLINE_MATH_RE.sub(lambda match: f"${match.group(1).strip()}$", text)
    st.markdown(text)


def render_preserved_text(text: str) -> None:
    if not text:
        return
    text = BLOCK_MATH_RE.sub(lambda match: f"\n\n$$ {match.group(1).strip()} $$\n\n", text)
    text = INLINE_MATH_RE.sub(lambda match: f"${match.group(1).strip()}$", text)
    paragraphs = [block.strip() for block in text.split("\n\n") if block.strip()]
    if not paragraphs:
        return

    for block in paragraphs:
        lines = [line.rstrip() for line in block.splitlines()]
        markdown_like = all(
            line.startswith(("* ", "- "))
            or re.match(r"^\d+\.\s", line)
            or re.match(r"^[a-zA-Z]\)\s", line)
            for line in lines
            if line.strip()
        )
        rendered = block if markdown_like else block.replace("\n", "  \n")
        st.markdown(rendered)


def render_question_notes(item: dict[str, Any], q_progress: dict[str, Any], user_id: str) -> None:
    note_key = f"notes-editor-{item['id']}"
    note_sync_key = f"{note_key}-sync"
    persisted_notes = q_progress.get("notes_text") or ""
    persisted_marker = q_progress.get("notes_updated_at") or ""
    sync_payload = (persisted_notes, persisted_marker)
    if st.session_state.get(note_sync_key) != sync_payload:
        st.session_state[note_key] = persisted_notes
        st.session_state[note_sync_key] = sync_payload

    with st.expander("My notes"):
        st.caption("Write short reminders for your future self. These notes are private to your account.")
        if q_progress.get("notes_updated_at"):
            st.caption(f"Last saved: {q_progress['notes_updated_at']}")
        st.text_area(
            "Notes",
            key=note_key,
            height=140,
            placeholder="Why was this tricky? What should you remember next time?",
            label_visibility="collapsed",
        )
        save_col, clear_col = st.columns(2)
        if save_col.button("Save notes", key=f"save-notes-{item['id']}", width="stretch"):
            save_notes(user_id, item["id"], st.session_state[note_key])
            st.rerun()
        if clear_col.button("Clear notes", key=f"clear-notes-{item['id']}", width="stretch"):
            st.session_state[note_key] = ""
            save_notes(user_id, item["id"], "")
            st.rerun()


def render_saved_notes_summary(q_progress: dict[str, Any]) -> None:
    notes_text = (q_progress.get("notes_text") or "").strip()
    if not notes_text:
        return
    with st.container(border=True):
        st.markdown("### Your notes")
        render_preserved_text(notes_text)


def render_item_images(item: dict[str, Any]) -> None:
    image_paths = item.get("image_paths") or []
    if not image_paths:
        return
    st.markdown("**Associated images**")
    for image_path in image_paths:
        full_path = APP_DIR / image_path
        if full_path.exists():
            left, mid, right = st.columns([1.1, 1.45, 1.1])
            with mid:
                st.image(str(full_path), width=320)


def llm_copy_text(item: dict[str, Any], answer_state: dict[str, Any] | None = None) -> str:
    lines = [f"Type: {'Multiple choice' if item['type'] == 'multiple_choice' else 'Open response'}", ""]

    if item["type"] == "multiple_choice":
        lines.append("Question:")
        lines.append(item["question"])
        lines.append("")
        lines.append("Options:")
        for letter in [option_letter(i) for i in range(len(item["options"]))]:
            lines.append(choice_label(item, letter))
        if answer_state:
            selected_letters = [letter for letter in answer_state.get("selected_letters", []) if letter in LETTERS]
            if selected_letters:
                lines.append("")
                lines.append("My answer:")
                for letter in selected_letters:
                    lines.append(choice_label(item, letter))
            lines.append("")
            lines.append(f"Result: {'Correct' if answer_state.get('is_correct') else 'Incorrect'}")
        lines.append("")
        lines.append("Correct answer:")
        for letter in item["answer_letters"]:
            if letter in LETTERS:
                lines.append(choice_label(item, letter))
    else:
        lines.append("Problem:")
        lines.append(item["question"])
        if item.get("solution_text"):
            lines.append("")
            lines.append("Stored answer:")
            lines.append(item["solution_text"])

    if item.get("solution_text") and item["type"] == "multiple_choice":
        lines.append("")
        lines.append("Explanation / solution:")
        lines.append(item["solution_text"])

    lines.append("")
    lines.append(f"Source: {source_label(item)}")
    return "\n".join(lines).strip()


def render_llm_copy_popover(item: dict[str, Any], answer_state: dict[str, Any] | None = None) -> None:
    copy_text = llm_copy_text(item, answer_state)
    button_id = "copy-" + hashlib.sha1(
        f"{item['id']}::{json.dumps(answer_state, sort_keys=True) if answer_state else 'blank'}".encode("utf-8")
    ).hexdigest()[:10]
    st.html(
        f"""
        <div class="llm-copy-shell">
            <button
                id="{button_id}"
                class="llm-copy-button"
                type="button"
                title="Copy question and answers as text"
                aria-label="Copy question and answers as text"
            >
                <span class="llm-copy-glyph" aria-hidden="true">⧉</span>
            </button>
        </div>
        <script>
        (() => {{
            const button = document.getElementById({json.dumps(button_id)});
            if (!button || button.dataset.bound === "1") return;
            button.dataset.bound = "1";
            const payload = {json.dumps(copy_text)};
            button.addEventListener("click", async () => {{
                try {{
                    await navigator.clipboard.writeText(payload);
                    button.classList.add("copied");
                    const originalTitle = button.title;
                    button.title = "Copied";
                    window.setTimeout(() => {{
                        button.classList.remove("copied");
                        button.title = originalTitle;
                    }}, 1200);
                }} catch (error) {{
                    button.title = "Copy failed";
                    window.setTimeout(() => {{
                        button.title = "Copy question and answers as text";
                    }}, 1600);
                }}
            }});
        }})();
        </script>
        """,
        width="content",
        unsafe_allow_javascript=True,
    )


def progress_for(progress: dict[str, dict[str, Any]], question_id: str) -> dict[str, Any]:
    return progress.get(
        question_id,
        {
            "attempts": 0,
            "correct_count": 0,
            "incorrect_count": 0,
            "last_result": None,
            "bookmarked": 0,
            "confidence_level": None,
            "confidence_updated_at": None,
            "notes_text": None,
            "notes_updated_at": None,
        },
    )


def has_outstanding_failure(row: dict[str, Any]) -> bool:
    return row.get("incorrect_count", 0) > 0 and row.get("last_result") != 1


def mcq_bank_map(bank: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {item["id"]: item for item in bank if item["type"] == "multiple_choice"}


def normalize_mcq_session(
    session: dict[str, Any] | None,
    bank_map: dict[str, dict[str, Any]],
) -> tuple[dict[str, Any] | None, bool]:
    if not session:
        return None, False

    queue_ids = [question_id for question_id in session.get("queue_ids", []) if question_id in bank_map]
    answers = {
        question_id: answer
        for question_id, answer in session.get("answers", {}).items()
        if question_id in queue_ids
    }
    current_index = session.get("current_index", 0)
    if queue_ids:
        current_index = max(0, min(int(current_index or 0), len(queue_ids) - 1))
    else:
        current_index = 0

    normalized = {
        **session,
        "queue_ids": queue_ids,
        "answers": answers,
        "current_index": current_index,
    }
    changed = (
        queue_ids != session.get("queue_ids", [])
        or answers != session.get("answers", {})
        or current_index != session.get("current_index", 0)
    )
    return normalized, changed


def mcq_session_answer(session: dict[str, Any] | None, question_id: str) -> dict[str, Any] | None:
    if not session:
        return None
    answer = session.get("answers", {}).get(question_id)
    return answer if isinstance(answer, dict) else None


def mcq_session_remaining(session: dict[str, Any] | None) -> int:
    if not session:
        return 0
    answered = {question_id for question_id in session.get("answers", {}) if question_id in set(session.get("queue_ids", []))}
    return sum(1 for question_id in session.get("queue_ids", []) if question_id not in answered)


def mcq_session_complete(session: dict[str, Any] | None) -> bool:
    return bool(session and session.get("queue_ids")) and mcq_session_remaining(session) == 0


def build_mcq_session_queue(
    items: list[dict[str, Any]],
    progress: dict[str, dict[str, Any]],
    category: str,
    mode: str,
) -> list[str]:
    pool = build_mcq_pool(items, progress, mode, category)
    return [item["id"] for item in pool]


def create_mcq_session(
    user_id: str,
    bank: list[dict[str, Any]],
    progress: dict[str, dict[str, Any]],
    category: str,
    mode: str,
    *,
    question_id: str | None = None,
) -> dict[str, Any]:
    queue_ids = build_mcq_session_queue(bank, progress, category, mode)
    current_index = 0
    if question_id and question_id in queue_ids:
        current_index = queue_ids.index(question_id)
    return save_mcq_session(
        user_id,
        category,
        mode,
        queue_ids,
        current_index,
        {},
    )


def persist_mcq_answer(
    user_id: str,
    session: dict[str, Any],
    question_id: str,
    selected_letters: list[str],
    is_correct: bool,
) -> dict[str, Any]:
    answers = dict(session.get("answers", {}))
    answers[question_id] = {
        "selected_letters": selected_letters,
        "is_correct": is_correct,
        "answered_at": utc_now(),
    }
    queue_ids = list(session.get("queue_ids", []))
    current_index = int(session.get("current_index", 0))
    if session.get("mode") == "Failed in topic" and is_correct and question_id in queue_ids:
        answers.pop(question_id, None)
        resolved_index = queue_ids.index(question_id)
        queue_ids.pop(resolved_index)
        current_index = min(resolved_index, len(queue_ids) - 1) if queue_ids else 0
    return save_mcq_session(
        user_id,
        session["category"],
        session["mode"],
        queue_ids,
        current_index,
        answers,
        started_at=session.get("started_at"),
    )


def persist_mcq_index(user_id: str, session: dict[str, Any], current_index: int) -> dict[str, Any]:
    return save_mcq_session(
        user_id,
        session["category"],
        session["mode"],
        list(session.get("queue_ids", [])),
        current_index,
        dict(session.get("answers", {})),
        started_at=session.get("started_at"),
    )


def option_letter(index: int) -> str:
    return LETTERS[index]


def choice_label(item: dict[str, Any], letter: str) -> str:
    index = LETTERS.index(letter)
    return f"{letter}) {item['options'][index]}"


def source_label(item: dict[str, Any]) -> str:
    source = item["sources"][0]
    kind = source.get("kind")
    if kind == "exam_theory":
        return f"Exam {source.get('year')} · Theory Q{source.get('question_number')}"
    if kind == "exam_problem":
        return f"Exam {source.get('year')} · Problem {source.get('problem_number')}"
    if kind == "quiz_html":
        return f"{source.get('title', 'Quiz')} · Q{source.get('question_number')}"
    return source.get("path", "Source")


def source_group(item: dict[str, Any]) -> str:
    kind = item["sources"][0].get("kind")
    if kind == "quiz_html":
        return "Quiz"
    if kind in {"exam_theory", "exam_problem"}:
        return "Exam"
    return "Other"


def year_label(item: dict[str, Any]) -> str | None:
    for tag in item.get("tags", []):
        if tag.startswith("year:"):
            return tag.split(":", 1)[1]
    return None


def item_categories(item: dict[str, Any]) -> list[str]:
    if item.get("categories"):
        return item["categories"]
    if item.get("primary_category"):
        return [item["primary_category"]]
    return ["Miscellaneous concepts"]


def primary_category(item: dict[str, Any]) -> str:
    return item.get("primary_category") or item_categories(item)[0]


def all_categories(bank: list[dict[str, Any]]) -> list[str]:
    counts = Counter(primary_category(item) for item in bank)
    return [category for category, _ in sorted(counts.items(), key=lambda entry: (-entry[1], entry[0]))]


def all_years(bank: list[dict[str, Any]]) -> list[str]:
    years = sorted({year for item in bank if (year := year_label(item))})
    return years


def item_has_activity(progress_row: dict[str, Any]) -> bool:
    return bool(
        progress_row["attempts"]
        or progress_row["bookmarked"]
        or progress_row["confidence_level"] is not None
    )


def matches_category_filter(item: dict[str, Any], selected_categories: list[str]) -> bool:
    return not selected_categories or bool(set(item_categories(item)) & set(selected_categories))


def prompt_preview(text: str, limit: int = 110) -> str:
    compact = " ".join(text.split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 1].rstrip() + "…"


def browser_option_label(item: dict[str, Any]) -> str:
    kind = "MCQ" if item["type"] == "multiple_choice" else "Problem"
    return f"{kind} · {primary_category(item)} · {source_label(item)}"


def confidence_label(value: int | None) -> str:
    labels = {
        1: "1 · No clue",
        2: "2 · Shaky",
        3: "3 · Partial",
        4: "4 · Solid",
        5: "5 · Ready",
    }
    return labels.get(value, "Unrated")


def render_badges(labels: list[tuple[str, str]]) -> None:
    if not labels:
        return
    html = '<div class="badge-row">' + "".join(
        f'<span class="badge {tone}">{label}</span>' for label, tone in labels
    ) + "</div>"
    st.markdown(html, unsafe_allow_html=True)


def render_topic_progress(row: dict[str, Any]) -> None:
    total = max(int(row.get("Total", 0) or 0), 1)
    failed = max(min(int(row.get("Failed", 0) or 0), total), 0)
    answered = max(min(int(row.get("Answered", 0) or 0), total), 0)
    unseen = max(min(int(row.get("Unseen", total - answered) or 0), total), 0)
    mastered = max(answered - failed, 0)

    segments = [
        ("is-mastered", mastered),
        ("is-failed", failed),
        ("is-unseen", unseen),
    ]
    fills = "".join(
        f'<div class="topic-progress-fill {css_class}" style="width:{(count / total) * 100:.4f}%"></div>'
        for css_class, count in segments
        if count > 0
    )
    st.markdown(f'<div class="topic-progress">{fills}</div>', unsafe_allow_html=True)


def build_mcq_pool(
    items: list[dict[str, Any]],
    progress: dict[str, dict[str, Any]],
    mode: str,
    selected_category: str | None,
) -> list[dict[str, Any]]:
    pool = [item for item in items if item["type"] == "multiple_choice"]
    if selected_category:
        pool = [item for item in pool if primary_category(item) == selected_category]

    if mode == "Unseen only":
        pool = [item for item in pool if progress_for(progress, item["id"])["attempts"] == 0]
    elif mode == "Failed in topic":
        pool = [item for item in pool if has_outstanding_failure(progress_for(progress, item["id"]))]
    elif mode == "Bookmarked in topic":
        pool = [item for item in pool if progress_for(progress, item["id"])["bookmarked"]]

    rng = random.Random(st.session_state.mcq_seed)
    pool = list(pool)
    rng.shuffle(pool)
    return pool


def problem_sort_key(item: dict[str, Any]) -> tuple[Any, ...]:
    source = item["sources"][0]
    year = source.get("year", "9999")
    number = source.get("problem_number", 999)
    return (year, number, item["question"])


def build_problem_pool(
    items: list[dict[str, Any]],
    progress: dict[str, dict[str, Any]],
    mode: str,
    selected_categories: list[str],
) -> list[dict[str, Any]]:
    pool = [item for item in items if item["type"] == "open_response"]
    pool = [item for item in pool if matches_category_filter(item, selected_categories)]

    if mode == "No confidence yet":
        pool = [item for item in pool if progress_for(progress, item["id"])["confidence_level"] is None]
    elif mode == "Low confidence (1-2)":
        pool = [item for item in pool if (progress_for(progress, item["id"])["confidence_level"] or 99) <= 2]
    elif mode == "Bookmarked":
        pool = [item for item in pool if progress_for(progress, item["id"])["bookmarked"]]
    elif mode == "With images":
        pool = [item for item in pool if item.get("image_paths")]
    elif mode == "With stored solution":
        pool = [item for item in pool if item.get("solution_text")]

    return sorted(pool, key=problem_sort_key)


def init_session_state() -> None:
    defaults = {
        "nav_section": "Overview",
        "mcq_active_category": None,
        "mcq_sidebar_topic": "MCQ Home",
        "mcq_session_request": None,
        "bootstrapped_navigation": False,
        "problem_mode": "All problems",
        "problem_categories": [],
        "browser_preset": "Custom",
        "browser_type": "All",
        "browser_sources": [],
        "browser_years": [],
        "browser_categories": [],
        "browser_progress": "All",
        "browser_search": "",
        "browser_current_id": None,
        "mcq_seed": random.randrange(1_000_000_000),
        "mcq_reset_confirm_category": None,
        "problem_index": 0,
        "problem_pool_signature": "",
        "problem_current_id": None,
        "problem_show_solution_for": None,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def reset_mcq(clear_subset: bool) -> None:
    st.session_state.mcq_seed = random.randrange(1_000_000_000)
    if clear_subset:
        st.session_state.mcq_session_request = None


def reset_problem() -> None:
    st.session_state.problem_index = 0
    st.session_state.problem_show_solution_for = None


def go_to_section(section: str) -> None:
    st.session_state.nav_section = section


def go_to_failed_mcq() -> None:
    st.session_state.nav_section = "Multiple choice"


def open_mcq_focus(question_id: str, category: str) -> None:
    st.session_state.nav_section = "Multiple choice"
    st.session_state.mcq_active_category = category
    st.session_state.mcq_session_request = {
        "category": category,
        "mode": "All in topic",
        "question_id": question_id,
    }
    st.session_state.mcq_seed = random.randrange(1_000_000_000)


def open_problem_focus(question_id: str) -> None:
    st.session_state.nav_section = "Problems"
    st.session_state.problem_mode = "All problems"
    st.session_state.problem_categories = []
    st.session_state.problem_current_id = question_id
    st.session_state.problem_index = 0
    st.session_state.problem_show_solution_for = None


def open_active_mcq_session(category: str | None) -> None:
    st.session_state.nav_section = "Multiple choice"
    st.session_state.mcq_active_category = category


def open_mcq_home() -> None:
    st.session_state.nav_section = "Multiple choice"
    st.session_state.mcq_active_category = None
    st.session_state.mcq_reset_confirm_category = None


def arm_mcq_topic_reset(category: str) -> None:
    st.session_state.mcq_reset_confirm_category = category


def cancel_mcq_topic_reset() -> None:
    st.session_state.mcq_reset_confirm_category = None


def start_mcq_topic(category: str, mode: str, question_id: str | None = None) -> None:
    st.session_state.nav_section = "Multiple choice"
    st.session_state.mcq_active_category = category
    st.session_state.mcq_reset_confirm_category = None
    st.session_state.mcq_session_request = {
        "category": category,
        "mode": mode,
        "question_id": question_id,
    }
    st.session_state.mcq_seed = random.randrange(1_000_000_000)


def sync_problem_state(pool: list[dict[str, Any]]) -> None:
    pool_signature = "|".join(item["id"] for item in pool)
    if pool_signature != st.session_state.problem_pool_signature:
        current_id = st.session_state.problem_current_id
        st.session_state.problem_pool_signature = pool_signature
        if current_id and current_id in {item["id"] for item in pool}:
            st.session_state.problem_index = [item["id"] for item in pool].index(current_id)
        else:
            st.session_state.problem_index = 0
            st.session_state.problem_show_solution_for = None

    if pool:
        st.session_state.problem_index = max(0, min(st.session_state.problem_index, len(pool) - 1))
        st.session_state.problem_current_id = pool[st.session_state.problem_index]["id"]
    else:
        st.session_state.problem_current_id = None
        st.session_state.problem_show_solution_for = None


def inventory_rows(bank: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    years = Counter()
    quizzes = Counter()

    for item in bank:
        item_type = "MCQ" if item["type"] == "multiple_choice" else "Problem"
        year = year_label(item)
        if year:
            years[(year, item_type)] += 1
        for tag in item.get("tags", []):
            if tag.startswith("quiz:test-"):
                quizzes[(tag.removeprefix("quiz:test-"), item_type)] += 1

    year_rows: list[dict[str, Any]] = []
    for year in sorted({year for year, _ in years}):
        year_rows.append(
            {
                "Year": year,
                "MCQ": years.get((year, "MCQ"), 0),
                "Problems": years.get((year, "Problem"), 0),
            }
        )

    quiz_rows: list[dict[str, Any]] = []
    for test in sorted({test for test, _ in quizzes}, key=lambda value: float(value)):
        quiz_rows.append(
            {
                "Quiz test": test,
                "Unique MCQ tagged": quizzes.get((test, "MCQ"), 0),
            }
        )

    return year_rows, quiz_rows


def category_rows(bank: list[dict[str, Any]], progress: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    counters: dict[str, Counter[str]] = {}

    for item in bank:
        category = primary_category(item)
        bucket = counters.setdefault(category, Counter())
        bucket["total"] += 1
        if item["type"] == "multiple_choice":
            bucket["mcq"] += 1
        else:
            bucket["problems"] += 1

        q_progress = progress_for(progress, item["id"])
        if item_has_activity(q_progress):
            bucket["started"] += 1
        if has_outstanding_failure(q_progress):
            bucket["incorrect"] += 1
        if q_progress["bookmarked"]:
            bucket["bookmarked"] += 1

    rows: list[dict[str, Any]] = []
    for category, bucket in sorted(counters.items(), key=lambda entry: (-entry[1]["total"], entry[0])):
        rows.append(
            {
                "Category": category,
                "Questions": bucket["total"],
                "MCQ": bucket["mcq"],
                "Problems": bucket["problems"],
                "Started": bucket["started"],
                "Incorrect MCQ": bucket["incorrect"],
                "Bookmarked": bucket["bookmarked"],
            }
        )
    return rows


def mcq_topic_rows(bank: list[dict[str, Any]], progress: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    counters: dict[str, Counter[str]] = {}
    for item in bank:
        if item["type"] != "multiple_choice":
            continue
        category = primary_category(item)
        bucket = counters.setdefault(category, Counter())
        row = progress_for(progress, item["id"])
        bucket["total"] += 1
        if row["attempts"] > 0:
            bucket["answered"] += 1
        else:
            bucket["unseen"] += 1
        if has_outstanding_failure(row):
            bucket["failed"] += 1
        if row["bookmarked"]:
            bucket["bookmarked"] += 1

    rows: list[dict[str, Any]] = []
    for category, bucket in sorted(counters.items(), key=lambda entry: (-entry[1]["total"], entry[0])):
        total = bucket["total"]
        answered = bucket["answered"]
        rows.append(
            {
                "Category": category,
                "Total": total,
                "Answered": answered,
                "Unseen": bucket["unseen"],
                "Failed": bucket["failed"],
                "Bookmarked": bucket["bookmarked"],
                "Completion": answered / total if total else 0.0,
            }
        )
    return rows


def topic_stats(topic_rows: list[dict[str, Any]], category: str | None) -> dict[str, Any] | None:
    if not category:
        return None
    return next((row for row in topic_rows if row["Category"] == category), None)


def resume_candidate(active_session: dict[str, Any] | None, topic_rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not active_session:
        return None
    category = active_session.get("category")
    row = topic_stats(topic_rows, category)
    if not row:
        return None
    return {
        "category": category,
        "unseen": row["Unseen"],
        "answered": row["Answered"],
        "mode": active_session.get("mode"),
        "question_id": active_session.get("queue_ids", [None])[active_session.get("current_index", 0)] if active_session.get("queue_ids") else None,
        "session_remaining": mcq_session_remaining(active_session),
        "session_total": len(active_session.get("queue_ids", [])),
    }


def filter_browser_items(
    bank: list[dict[str, Any]],
    progress: dict[str, dict[str, Any]],
    current_mcq_category: str | None,
    active_mcq_session: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    items = list(bank)
    preset = st.session_state.browser_preset

    if preset == "Unseen in current topic" and current_mcq_category:
        items = [
            item
            for item in items
            if item["type"] == "multiple_choice"
            and primary_category(item) == current_mcq_category
            and progress_for(progress, item["id"])["attempts"] == 0
        ]
        return sorted(
            items,
            key=lambda item: (primary_category(item), source_label(item), item["question"]),
        )

    if preset == "Resume current MCQ session" and active_mcq_session:
        bank_map = mcq_bank_map(bank)
        ordered_items = [bank_map[question_id] for question_id in active_mcq_session.get("queue_ids", []) if question_id in bank_map]
        return ordered_items

    if st.session_state.browser_type == "Multiple choice":
        items = [item for item in items if item["type"] == "multiple_choice"]
    elif st.session_state.browser_type == "Problems":
        items = [item for item in items if item["type"] == "open_response"]

    if st.session_state.browser_sources:
        selected = set(st.session_state.browser_sources)
        items = [item for item in items if source_group(item) in selected]

    if st.session_state.browser_years:
        selected_years = set(st.session_state.browser_years)
        items = [item for item in items if year_label(item) in selected_years]

    if st.session_state.browser_categories:
        items = [item for item in items if matches_category_filter(item, st.session_state.browser_categories)]

    query = st.session_state.browser_search.strip().casefold()
    if query:
        items = [item for item in items if query in item["question"].casefold()]

    progress_mode = st.session_state.browser_progress
    if progress_mode == "No activity yet":
        items = [item for item in items if not item_has_activity(progress_for(progress, item["id"]))]
    elif progress_mode == "Started":
        items = [item for item in items if item_has_activity(progress_for(progress, item["id"]))]
    elif progress_mode == "Incorrect MCQ":
        items = [item for item in items if has_outstanding_failure(progress_for(progress, item["id"]))]
    elif progress_mode == "Bookmarked":
        items = [item for item in items if progress_for(progress, item["id"])["bookmarked"]]
    elif progress_mode == "Low confidence problems":
        items = [
            item
            for item in items
            if item["type"] == "open_response" and (progress_for(progress, item["id"])["confidence_level"] or 99) <= 2
        ]
    elif progress_mode == "Unrated problems":
        items = [item for item in items if item["type"] == "open_response" and progress_for(progress, item["id"])["confidence_level"] is None]

    return sorted(
        items,
        key=lambda item: (
            item["type"],
            primary_category(item),
            source_label(item),
            item["question"],
        ),
    )


def render_page_heading(kicker: str, title: str, subtitle: str) -> None:
    st.markdown(
        (
            f'<div class="section-kicker">{kicker}</div>'
            f'<div class="section-title">{title}</div>'
            f'<div class="section-subtitle">{subtitle}</div>'
        ),
        unsafe_allow_html=True,
    )


def render_stats(bank: list[dict[str, Any]], progress: dict[str, dict[str, Any]]) -> None:
    mcq_items = [item for item in bank if item["type"] == "multiple_choice"]
    problem_items = [item for item in bank if item["type"] == "open_response"]
    seen_count = sum(1 for item in mcq_items if progress_for(progress, item["id"])["attempts"] > 0)
    failed_count = sum(1 for item in mcq_items if has_outstanding_failure(progress_for(progress, item["id"])))
    bookmarked_count = sum(1 for row in progress.values() if row["bookmarked"])
    rated_problems = [progress_for(progress, item["id"])["confidence_level"] for item in problem_items]
    rated_values = [value for value in rated_problems if value is not None]

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("MCQ bank", len(mcq_items))
    col2.metric("Problems", len(problem_items))
    col3.metric("Seen MCQ", seen_count)
    col4.metric("Failed MCQ", failed_count)
    if rated_values:
        avg_confidence = sum(rated_values) / len(rated_values)
        col5.metric("Problem confidence", f"{avg_confidence:.1f}/5")
    else:
        col5.metric("Problem confidence", "Unrated")
    st.caption(f"Bookmarked items: {bookmarked_count}")


def render_overview(
    bank: list[dict[str, Any]],
    progress: dict[str, dict[str, Any]],
    report: dict[str, Any],
    user_context: dict[str, Any],
    active_mcq_session: dict[str, Any] | None,
) -> None:
    summary = report.get("summary", {})
    mcq_items = [item for item in bank if item["type"] == "multiple_choice"]
    problem_items = [item for item in bank if item["type"] == "open_response"]
    problem_images = sum(1 for item in problem_items if item.get("image_paths"))
    problem_solutions = sum(1 for item in problem_items if item.get("solution_text"))
    topic_rows = mcq_topic_rows(bank, progress)
    candidate = resume_candidate(active_mcq_session, topic_rows)
    save_user_state(user_context["user_id"], last_section="Overview")

    st.markdown(
        """
        <div class="hero">
            <h1>Exam study workspace</h1>
            <p>
                Start here, see the whole bank at a glance, then move into either multiple-choice practice
                or open-ended problem study. The app keeps your mistakes, bookmarks, and problem confidence locally.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    render_stats(bank, progress)
    if user_context["authenticated"]:
        st.caption(f"Progress account: {user_context['display_name']} ({user_context['email']})")
    else:
        st.caption("Progress account: local guest mode")

    if candidate:
        st.markdown(
            (
                '<div class="resume-callout"><strong>Resume ready.</strong> '
                f"{candidate['category']} session has {candidate['session_remaining']} question(s) left to answer."
                "</div>"
            ),
            unsafe_allow_html=True,
        )
        st.button(
            f"Resume {candidate['category']} · {candidate['session_remaining']} remaining",
            width="stretch",
            on_click=open_active_mcq_session,
            args=(candidate["category"],),
        )

    render_page_heading(
        "Overview",
        "Bank snapshot",
        "This page is the starting point. Use it to decide what to study next instead of landing inside a question immediately.",
    )

    quick1, quick2, quick3 = st.columns(3)
    with quick1:
        st.button(
            "Open MCQ topics",
            width="stretch",
            on_click=open_mcq_home,
        )
    with quick2:
        if candidate:
            st.button(
                "Resume last MCQ topic",
                width="stretch",
                on_click=open_active_mcq_session,
                args=(candidate["category"],),
            )
        else:
            st.button("Open question browser", width="stretch", on_click=go_to_section, args=("Question browser",))
    with quick3:
        st.button("Open problems", width="stretch", on_click=go_to_section, args=("Problems",))
    st.caption("Use these buttons as the primary mobile entry points. The sidebar stays available, but you should not need it to start studying.")

    info_left, info_right = st.columns([1.2, 1])
    with info_left:
        with st.container(border=True):
            st.markdown("### What is in the bank")
            st.write(f"- {len(mcq_items)} unique multiple-choice questions")
            st.write(f"- {len(problem_items)} open-ended problems")
            st.write(f"- {problem_images} problems with extracted images")
            st.write(f"- {problem_solutions} problems with stored solution text")
            if summary:
                st.caption(
                    f"Built from {summary.get('quiz_files', 0)} quiz HTML files and "
                    f"{summary.get('exam_pdf_files', 0)} exam PDFs. "
                    f"Current build warnings: {summary.get('warnings', 0)}."
                )
    with info_right:
        with st.container(border=True):
            st.markdown("### Suggested flow")
            st.write("1. Use multiple choice for spaced repetition and failed-question loops.")
            st.write("2. Use problems for slower study with images and reveal-on-demand answers.")
            st.write("3. Mark bookmarks and confidence so the next session starts where you are weakest.")

    year_rows, quiz_rows = inventory_rows(bank)
    category_summary = [
        {
            "Category": row["Category"],
            "MCQ total": row["Total"],
            "Answered": row["Answered"],
            "Unseen": row["Unseen"],
            "Failed": row["Failed"],
            "Bookmarked": row["Bookmarked"],
            "Completion %": round(row["Completion"] * 100),
        }
        for row in topic_rows
    ]
    inv_left, inv_right = st.columns(2)
    with inv_left:
        with st.container(border=True):
            st.markdown("### Exam inventory")
            st.caption("Unique bank items grouped by exam year.")
            st.dataframe(year_rows, width="stretch", hide_index=True)
    with inv_right:
        with st.container(border=True):
            st.markdown("### Quiz inventory")
            st.caption("Unique MCQ tagged by optional online quiz number.")
            st.dataframe(quiz_rows, width="stretch", hide_index=True)

    with st.container(border=True):
        st.markdown("### Category overview")
        st.caption("Primary MCQ topic buckets with answered, unseen, and failed counts for your account.")
        st.dataframe(category_summary, width="stretch", hide_index=True)


def render_browser_page(
    bank: list[dict[str, Any]],
    progress: dict[str, dict[str, Any]],
    user_context: dict[str, Any],
    active_mcq_session: dict[str, Any] | None,
) -> None:
    categories = all_categories(bank)
    years = all_years(bank)
    save_user_state(user_context["user_id"], last_section="Question browser")

    st.sidebar.subheader("Question browser")
    st.sidebar.selectbox("Quick preset", ["Custom", "Unseen in current topic", "Resume current MCQ session"], key="browser_preset")
    st.sidebar.selectbox("Question type", ["All", "Multiple choice", "Problems"], key="browser_type")
    st.sidebar.multiselect("Categories", categories, key="browser_categories")
    st.sidebar.multiselect("Years", years, key="browser_years")
    st.sidebar.multiselect("Sources", ["Exam", "Quiz"], key="browser_sources")
    st.sidebar.selectbox(
        "Progress filter",
        ["All", "No activity yet", "Started", "Incorrect MCQ", "Bookmarked", "Low confidence problems", "Unrated problems"],
        key="browser_progress",
    )
    st.sidebar.text_input("Search text", key="browser_search", placeholder="Search in question text")

    current_topic = st.session_state.mcq_active_category or (active_mcq_session.get("category") if active_mcq_session else None)
    filtered_items = filter_browser_items(bank, progress, current_topic, active_mcq_session)

    render_page_heading(
        "Question browser",
        "All questions and progress",
        "Filter by topic, source, year, or progress status, then preview any item without entering study mode.",
    )

    started_count = sum(1 for item in filtered_items if item_has_activity(progress_for(progress, item["id"])))
    incorrect_count = sum(1 for item in filtered_items if has_outstanding_failure(progress_for(progress, item["id"])))
    bookmarked_count = sum(1 for item in filtered_items if progress_for(progress, item["id"])["bookmarked"])
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Filtered questions", len(filtered_items))
    col2.metric("Started", started_count)
    col3.metric("Incorrect MCQ", incorrect_count)
    col4.metric("Bookmarked", bookmarked_count)

    if st.session_state.browser_preset != "Custom":
        st.caption(f"Quick preset active: {st.session_state.browser_preset}")

    if not filtered_items:
        st.info("No questions match the current browser filters.")
        return

    rows = []
    for item in filtered_items:
        q_progress = progress_for(progress, item["id"])
        rows.append(
            {
                "Ref": source_label(item),
                "Type": "MCQ" if item["type"] == "multiple_choice" else "Problem",
                "Category": primary_category(item),
                "Year": year_label(item) or "—",
                "Source": source_group(item),
                "Prompt": prompt_preview(item["question"]),
                "Attempts": q_progress["attempts"],
                "Missed": q_progress["incorrect_count"],
                "Sources": item.get("source_count", len(item.get("sources", []))),
                "Confidence": confidence_label(q_progress["confidence_level"]) if item["type"] == "open_response" else "—",
                "Bookmarked": "Yes" if q_progress["bookmarked"] else "",
            }
        )

    with st.container(border=True):
        st.markdown("### Filtered bank")
        st.dataframe(rows, width="stretch", hide_index=True, height=360)

    item_map = {item["id"]: item for item in filtered_items}
    item_ids = list(item_map)
    if st.session_state.browser_current_id not in item_map:
        st.session_state.browser_current_id = item_ids[0]

    selected_id = st.selectbox(
        "Preview question",
        options=item_ids,
        index=item_ids.index(st.session_state.browser_current_id),
        format_func=lambda question_id: browser_option_label(item_map[question_id]),
    )
    st.session_state.browser_current_id = selected_id
    item = item_map[selected_id]
    q_progress = progress_for(progress, item["id"])

    badges = [
        (source_label(item), "cool"),
        (primary_category(item), ""),
    ]
    if item.get("source_count", 1) > 1:
        badges.append((f"Seen in {item['source_count']} sources", "cool"))
    if q_progress["bookmarked"]:
        badges.append(("Bookmarked", "success"))
    if item["type"] == "multiple_choice" and q_progress["incorrect_count"] > 0:
        badges.append((f"Missed {q_progress['incorrect_count']}", "warm"))
    if item["type"] == "open_response" and q_progress["confidence_level"] is not None:
        badges.append((confidence_label(q_progress["confidence_level"]), "success"))
    render_badges(badges)
    st.caption("All categories: " + " | ".join(item_categories(item)))

    preview_left, preview_right = st.columns([1.35, 0.85])
    with preview_left:
        with st.container(border=True):
            header_left, header_right = st.columns([1, 0.3])
            with header_left:
                st.markdown("### Question")
            with header_right:
                render_llm_copy_popover(item)
            render_preserved_text(item["question"])
            render_item_images(item)
    with preview_right:
        with st.container(border=True):
            st.markdown("### Progress")
            st.write(f"- Source: {source_group(item)}")
            st.write(f"- Year: {year_label(item) or '—'}")
            st.write(f"- Attempts: {q_progress['attempts']}")
            st.write(f"- Incorrect: {q_progress['incorrect_count']}")
            st.write(f"- Bookmarked: {'Yes' if q_progress['bookmarked'] else 'No'}")
            if item["type"] == "open_response":
                st.write(f"- Confidence: {confidence_label(q_progress['confidence_level'])}")

            if item["type"] == "multiple_choice":
                st.button(
                    "Study this MCQ only",
                    width="stretch",
                    on_click=open_mcq_focus,
                    args=(item["id"], primary_category(item)),
                )
            else:
                st.button(
                    "Open this problem",
                    width="stretch",
                    on_click=open_problem_focus,
                    args=(item["id"],),
                )

    with st.expander("Show stored answer", expanded=False):
        if item["type"] == "multiple_choice":
            st.markdown("**Options**")
            for letter in [option_letter(i) for i in range(len(item["options"]))]:
                st.write(choice_label(item, letter))
            st.markdown("**Correct answer**")
            for letter in item["answer_letters"]:
                st.write(choice_label(item, letter))
        elif item.get("solution_text"):
            render_preserved_text(item["solution_text"])
        else:
            st.info("No stored solution text is available for this problem yet.")


def show_mcq_feedback(item: dict[str, Any], answer_state: dict[str, Any] | None) -> None:
    if not answer_state:
        return

    if answer_state["is_correct"]:
        st.success("Correct.")
    else:
        st.error("Incorrect.")

    selected_letters = [letter for letter in answer_state.get("selected_letters", []) if letter in LETTERS]
    st.markdown("**All options**")
    for letter in [option_letter(i) for i in range(len(item["options"]))]:
        if letter not in LETTERS:
            continue
        labels: list[str] = []
        classes: list[str] = []
        if letter in item["answer_letters"]:
            labels.append('<span class="mcq-review-tag correct">Correct</span>')
            classes.append("correct")
        if letter in selected_letters:
            labels.append('<span class="mcq-review-tag selected">Your answer</span>')
            classes.append("selected")
        class_attr = " ".join(["mcq-review-option", *classes])
        st.markdown(
            (
                f'<div class="{class_attr}">'
                f"<strong>{letter})</strong> {html.escape(item['options'][LETTERS.index(letter)])}"
                f'<div class="mcq-review-tags">{"".join(labels)}</div>'
                "</div>"
            ),
            unsafe_allow_html=True,
        )

    if item.get("solution_text"):
        st.markdown("**Explanation / solution**")
        render_rich_text(item["solution_text"])


def render_mcq_home(
    bank: list[dict[str, Any]],
    topic_rows: list[dict[str, Any]],
    candidate: dict[str, Any] | None,
    active_session: dict[str, Any] | None,
    user_id: str,
) -> None:
    if active_session:
        save_user_state(
            user_id,
            last_section="Multiple choice",
            last_mcq_category=None,
            last_mcq_mode=active_session.get("mode"),
            last_mcq_question_id=None,
        )
    else:
        save_user_state(
            user_id,
            last_section="Multiple choice",
            last_mcq_category=None,
            last_mcq_mode=None,
            last_mcq_question_id=None,
        )

    render_page_heading(
        "Multiple choice",
        "MCQ home",
        "Pick one topic, see how much is already done, and jump back in without opening the sidebar.",
    )
    st.caption(
        "Reset topic progress is only available from this topics screen. It is intentionally kept out of the active question view because it deletes study state."
    )

    if candidate:
        st.markdown(
            (
                '<div class="resume-callout"><strong>Resume last topic.</strong> '
                f"{candidate['category']} session has {candidate['session_remaining']} question(s) left to answer.</div>"
            ),
            unsafe_allow_html=True,
        )
        st.button(
            f"Resume {candidate['category']} · {candidate['session_remaining']} remaining",
            width="stretch",
            on_click=open_active_mcq_session,
            args=(candidate["category"],),
        )

    for row in topic_rows:
        completion_pct = int(round(row["Completion"] * 100))
        default_mode = "Unseen only" if row["Unseen"] > 0 else "All in topic"
        with st.container(border=True):
            st.markdown(f"### {row['Category']}")
            st.markdown(
                (
                    '<div class="topic-meta">'
                    f"{row['Answered']} answered · {row['Unseen']} unseen · "
                    f"{row['Failed']} failed · {row['Bookmarked']} bookmarked"
                    "</div>"
                ),
                unsafe_allow_html=True,
            )
            render_topic_progress(row)
            meta_left, meta_right = st.columns(2)
            meta_left.caption(f"{row['Total']} total")
            meta_right.caption(f"{completion_pct}% complete")
            if active_session and active_session.get("category") == row["Category"]:
                session_remaining = mcq_session_remaining(active_session)
                st.caption(
                    f"Active session · {active_session.get('mode')} · {session_remaining} remaining"
                )
                show_failed_action = row["Failed"] > 0 and active_session.get("mode") != "Failed in topic"
                action_columns = st.columns(3 if show_failed_action else 2)
                action_left = action_columns[0]
                action_right = action_columns[1]
                action_left.button(
                    "Resume session",
                    key=f"mcq-resume-{row['Category']}",
                    width="stretch",
                    on_click=open_active_mcq_session,
                    args=(row["Category"],),
                )
                action_right.button(
                    "Start fresh unseen",
                    key=f"mcq-fresh-{row['Category']}",
                    width="stretch",
                    on_click=start_mcq_topic,
                    args=(row["Category"], "Unseen only"),
                )
                if show_failed_action:
                    action_columns[2].button(
                        "Reattempt failed",
                        key=f"mcq-failed-{row['Category']}",
                        width="stretch",
                        on_click=start_mcq_topic,
                        args=(row["Category"], "Failed in topic"),
                    )
            else:
                if row["Failed"] > 0:
                    open_col, failed_col = st.columns(2)
                    open_col.button(
                        f"Open topic · {'resume unseen' if row['Unseen'] > 0 else 'review all'}",
                        key=f"mcq-topic-{row['Category']}",
                        width="stretch",
                        on_click=start_mcq_topic,
                        args=(row["Category"], default_mode),
                    )
                    failed_col.button(
                        "Reattempt failed",
                        key=f"mcq-failed-{row['Category']}",
                        width="stretch",
                        on_click=start_mcq_topic,
                        args=(row["Category"], "Failed in topic"),
                    )
                else:
                    st.button(
                        f"Open topic · {'resume unseen' if row['Unseen'] > 0 else 'review all'}",
                        key=f"mcq-topic-{row['Category']}",
                        width="stretch",
                        on_click=start_mcq_topic,
                        args=(row["Category"], default_mode),
                    )

            has_resettable_progress = bool(row["Answered"] or row["Failed"] or row["Bookmarked"])
            if has_resettable_progress:
                if st.session_state.mcq_reset_confirm_category == row["Category"]:
                    st.warning(
                        f"Topic reset will permanently delete your MCQ attempts, failed-review state, and bookmarks for {row['Category']}."
                    )
                    st.caption("Use this only if you want to restudy this topic from zero.")
                    reset_left, reset_right = st.columns(2)
                    if reset_left.button(
                        "Confirm topic reset",
                        key=f"confirm-reset-{row['Category']}",
                        width="stretch",
                    ):
                        clear_mcq_topic_progress(user_id, bank, row["Category"])
                        if active_session and active_session.get("category") == row["Category"]:
                            clear_mcq_session(user_id)
                        open_mcq_home()
                        st.rerun()
                    reset_right.button(
                        "Cancel",
                        key=f"cancel-reset-{row['Category']}",
                        width="stretch",
                        on_click=cancel_mcq_topic_reset,
                    )
                else:
                    st.button(
                        "Reset topic progress",
                        key=f"arm-reset-{row['Category']}",
                        width="stretch",
                        on_click=arm_mcq_topic_reset,
                        args=(row["Category"],),
                    )


def render_mcq_page(
    bank: list[dict[str, Any]],
    progress: dict[str, dict[str, Any]],
    report: dict[str, Any],
    user_id: str,
    user_state: dict[str, Any],
) -> None:
    del report
    bank_map = mcq_bank_map(bank)
    topic_rows = mcq_topic_rows(bank, progress)
    categories = [row["Category"] for row in topic_rows]

    active_session, session_dirty = normalize_mcq_session(load_mcq_session(user_id), bank_map)
    if active_session and session_dirty:
        active_session = save_mcq_session(
            user_id,
            active_session["category"],
            active_session["mode"],
            active_session["queue_ids"],
            active_session["current_index"],
            active_session["answers"],
            started_at=active_session.get("started_at"),
        )

    pending_request = st.session_state.get("mcq_session_request")
    if pending_request:
        active_session = create_mcq_session(
            user_id,
            bank,
            progress,
            pending_request["category"],
            pending_request["mode"],
            question_id=pending_request.get("question_id"),
        )
        st.session_state.mcq_session_request = None
        st.session_state.mcq_active_category = active_session["category"]

    candidate = resume_candidate(active_session, topic_rows)
    expected_sidebar_topic = st.session_state.mcq_active_category or "MCQ Home"
    if st.session_state.get("mcq_sidebar_topic") != expected_sidebar_topic:
        st.session_state.mcq_sidebar_topic = expected_sidebar_topic

    st.sidebar.subheader("Multiple choice")
    st.sidebar.selectbox("Jump to topic", ["MCQ Home", *categories], key="mcq_sidebar_topic")
    chosen_topic = st.session_state.mcq_sidebar_topic
    if chosen_topic == "MCQ Home" and st.session_state.mcq_active_category is not None:
        open_mcq_home()
        st.rerun()
    if chosen_topic != "MCQ Home" and chosen_topic != st.session_state.mcq_active_category:
        default_mode = "Unseen only"
        stats = topic_stats(topic_rows, chosen_topic)
        if stats and stats["Unseen"] == 0:
            default_mode = "All in topic"
        start_mcq_topic(chosen_topic, default_mode)
        st.rerun()

    if st.sidebar.button("Start fresh current topic", width="stretch", disabled=st.session_state.mcq_active_category is None):
        active_category = st.session_state.mcq_active_category
        if active_category is not None:
            start_mcq_topic(active_category, active_session["mode"] if active_session else "Unseen only")
            st.rerun()

    if st.sidebar.button("Clear active MCQ session", width="stretch", disabled=active_session is None):
        clear_mcq_session(user_id)
        open_mcq_home()
        st.rerun()

    if st.session_state.mcq_active_category is None:
        render_mcq_home(bank, topic_rows, candidate, active_session, user_id)
        return

    if not active_session or active_session.get("category") != st.session_state.mcq_active_category:
        start_mcq_topic(st.session_state.mcq_active_category, "Unseen only")
        st.rerun()

    active_category = active_session["category"]
    queue_ids = active_session.get("queue_ids", [])
    current_index = int(active_session.get("current_index", 0))
    topic_row = topic_stats(topic_rows, active_category)

    if not queue_ids:
        empty_subtitle = "There is no active queue in this topic right now."
        if active_session["mode"] == "Failed in topic":
            empty_subtitle = "You have cleared the failed-question queue for this topic."
        render_page_heading(
            "Multiple choice",
            active_category,
            empty_subtitle,
        )
        if active_session["mode"] == "Failed in topic":
            st.success("No failed questions are left in this topic right now.")
        else:
            st.info("This session has no questions left. Start a fresh unseen session or review the full topic.")
        empty_left, empty_mid, empty_right = st.columns(3)
        empty_left.button(
            "Start fresh unseen",
            key=f"mcq-empty-fresh-{active_category}",
            width="stretch",
            on_click=start_mcq_topic,
            args=(active_category, "Unseen only"),
        )
        empty_mid.button(
            "Review all in topic",
            key=f"mcq-empty-review-{active_category}",
            width="stretch",
            on_click=start_mcq_topic,
            args=(active_category, "All in topic"),
        )
        empty_right.button(
            "Back to topics",
            key=f"mcq-empty-topics-{active_category}",
            width="stretch",
            on_click=open_mcq_home,
        )
        save_user_state(
            user_id,
            last_section="Multiple choice",
            last_mcq_category=active_category,
            last_mcq_mode=active_session["mode"],
            last_mcq_question_id=None,
        )
        return

    item = bank_map[queue_ids[current_index]]
    answer_state = mcq_session_answer(active_session, item["id"])
    save_user_state(
        user_id,
        last_section="Multiple choice",
        last_mcq_category=active_category,
        last_mcq_mode=active_session["mode"],
        last_mcq_question_id=item["id"],
    )

    render_page_heading(
        "Multiple choice",
        active_category,
        "Topic-focused MCQ practice with a frozen session queue that survives reloads and weak connections.",
    )

    with st.container(border=True):
        st.markdown('<div class="sticky-anchor"></div>', unsafe_allow_html=True)
        controls = st.columns([0.95, 1.1, 1, 1, 1])
        with controls[0]:
            st.button("Topics", key=f"mcq-topics-{active_category}", width="stretch", on_click=open_mcq_home)
        with controls[1]:
            st.button(
                "Start fresh unseen",
                key=f"mcq-fresh-{active_category}",
                width="stretch",
                on_click=start_mcq_topic,
                args=(active_category, "Unseen only"),
            )
        with controls[2]:
            st.button(
                "All in topic",
                key=f"mcq-all-{active_category}",
                width="stretch",
                on_click=start_mcq_topic,
                args=(active_category, "All in topic"),
            )
        with controls[3]:
            st.button(
                "Failed in topic",
                key=f"mcq-failed-mode-{active_category}",
                width="stretch",
                on_click=start_mcq_topic,
                args=(active_category, "Failed in topic"),
            )
        with controls[4]:
            st.button(
                "Bookmarked in topic",
                key=f"mcq-bookmarked-{active_category}",
                width="stretch",
                on_click=start_mcq_topic,
                args=(active_category, "Bookmarked in topic"),
            )
        st.caption(f"Current session mode: {active_session['mode']}")

    if topic_row:
        summary1, summary2, summary3, summary4 = st.columns(4)
        summary1.metric("Answered", topic_row["Answered"])
        summary2.metric("Unseen", topic_row["Unseen"])
        summary3.metric("Failed", topic_row["Failed"])
        summary4.metric("Bookmarked", topic_row["Bookmarked"])

    session_remaining = mcq_session_remaining(active_session)
    st.caption(
        " | ".join(
            [
                f"Session position {current_index + 1}/{len(queue_ids)}",
                f"Session remaining {session_remaining}",
                f"Topic unseen overall {topic_row['Unseen'] if topic_row else 0}",
            ]
        )
    )

    q_progress = progress_for(progress, item["id"])
    badges = [
        (source_label(item), "cool"),
        (primary_category(item), ""),
        (f"Session {current_index + 1} / {len(queue_ids)}", ""),
        (f"Attempts {q_progress['attempts']}", ""),
    ]
    if item.get("source_count", 1) > 1:
        badges.append((f"Seen in {item['source_count']} sources", "cool"))
    if q_progress["incorrect_count"]:
        badges.append((f"Missed {q_progress['incorrect_count']}", "warm"))
    if q_progress["bookmarked"]:
        badges.append(("Bookmarked", "success"))
    if q_progress.get("notes_text"):
        badges.append(("Notes", "success"))
    render_badges(badges)

    nav1, nav2, nav3 = st.columns([1, 1, 1])
    with nav1:
        if st.button("Previous", disabled=current_index == 0, width="stretch"):
            persist_mcq_index(user_id, active_session, current_index - 1)
            st.rerun()
    with nav2:
        bookmark_label = "Remove bookmark" if q_progress["bookmarked"] else "Bookmark"
        if st.button(bookmark_label, width="stretch"):
            set_bookmark(user_id, item["id"], not bool(q_progress["bookmarked"]))
            st.rerun()
    with nav3:
        if st.button("Next", disabled=current_index >= len(queue_ids) - 1, width="stretch"):
            persist_mcq_index(user_id, active_session, current_index + 1)
            st.rerun()

    with st.container(border=True):
        header_left, header_right = st.columns([1, 0.3])
        with header_left:
            st.markdown("### Question")
        with header_right:
            render_llm_copy_popover(item, answer_state)
        render_rich_text(item["question"])
    render_question_notes(item, q_progress, user_id)

    if answer_state:
        with st.container(border=True):
            st.markdown("### Review")
            show_mcq_feedback(item, answer_state)
            st.caption("This question is locked for the current session so you can review it without losing your place.")
        render_saved_notes_summary(q_progress)
    else:
        is_multi_answer = len(item["answer_letters"]) > 1
        with st.container(border=True):
            st.markdown("### Choose your answer")
            with st.form(key=f"mcq-form-{item['id']}"):
                if is_multi_answer:
                    selection = st.multiselect(
                        "Select all correct answers",
                        options=[option_letter(i) for i in range(len(item["options"]))],
                        format_func=lambda letter: choice_label(item, letter),
                    )
                else:
                    selection = st.radio(
                        "Select one answer",
                        options=[option_letter(i) for i in range(len(item["options"]))],
                        format_func=lambda letter: choice_label(item, letter),
                        index=None,
                    )

                submitted = st.form_submit_button("Check answer", width="stretch")
                if submitted:
                    chosen = selection if isinstance(selection, list) else ([selection] if selection else [])
                    if not chosen:
                        st.warning("Select an answer before submitting.")
                    else:
                        is_correct = set(chosen) == set(item["answer_letters"])
                        record_attempt(user_id, item["id"], is_correct)
                        persist_mcq_answer(user_id, active_session, item["id"], chosen, is_correct)
                        st.rerun()

    if mcq_session_complete(active_session):
        with st.container(border=True):
            st.markdown("### Session complete")
            st.success("You have answered every question in this frozen session.")
            done1, done2, done3 = st.columns(3)
            done1.button(
                "Start fresh unseen",
                key=f"mcq-done-fresh-{active_category}",
                width="stretch",
                on_click=start_mcq_topic,
                args=(active_category, "Unseen only"),
            )
            done2.button(
                "Review all in topic",
                key=f"mcq-done-review-{active_category}",
                width="stretch",
                on_click=start_mcq_topic,
                args=(active_category, "All in topic"),
            )
            done3.button(
                "Back to topics",
                key=f"mcq-done-topics-{active_category}",
                width="stretch",
                on_click=open_mcq_home,
            )


def render_problem_page(
    bank: list[dict[str, Any]],
    progress: dict[str, dict[str, Any]],
    user_id: str,
) -> None:
    st.sidebar.subheader("Problems")
    st.sidebar.selectbox(
        "Problem filter",
        ["All problems", "No confidence yet", "Low confidence (1-2)", "Bookmarked", "With images", "With stored solution"],
        key="problem_mode",
    )
    st.sidebar.multiselect("Categories", all_categories(bank), key="problem_categories")

    if st.sidebar.button("Reset problem position", width="stretch"):
        reset_problem()
        st.rerun()

    pool = build_problem_pool(bank, progress, st.session_state.problem_mode, st.session_state.problem_categories)
    sync_problem_state(pool)

    render_page_heading(
        "Problems",
        "Open-ended study",
        "Work a problem first, reveal the stored answer only when you want it, then rate your confidence.",
    )
    status = [f"{len(pool)} problems in current view", f"Filter: {st.session_state.problem_mode}"]
    if st.session_state.problem_categories:
        status.append("Categories: " + ", ".join(st.session_state.problem_categories))
    st.caption(" | ".join(status))

    if not pool:
        save_user_state(user_id, last_section="Problems", last_problem_filter=st.session_state.problem_mode)
        st.info("No problems match the current filters.")
        return

    item = pool[st.session_state.problem_index]
    q_progress = progress_for(progress, item["id"])
    show_solution = st.session_state.problem_show_solution_for == item["id"]
    save_user_state(
        user_id,
        last_section="Problems",
        last_problem_category=primary_category(item),
        last_problem_filter=st.session_state.problem_mode,
        last_problem_question_id=item["id"],
    )

    badges = [
        (source_label(item), "cool"),
        (primary_category(item), ""),
        (f"Problem {st.session_state.problem_index + 1} / {len(pool)}", ""),
    ]
    if item.get("image_paths"):
        badges.append((f"{len(item['image_paths'])} image(s)", "warm"))
    if q_progress["bookmarked"]:
        badges.append(("Bookmarked", "success"))
    if q_progress["confidence_level"] is not None:
        badges.append((confidence_label(q_progress["confidence_level"]), "success"))
    if q_progress.get("notes_text"):
        badges.append(("Notes", "success"))
    render_badges(badges)

    nav1, nav2, nav3, nav4 = st.columns([1, 1.2, 1, 1])
    with nav1:
        if st.button("Previous", disabled=st.session_state.problem_index == 0, width="stretch"):
            st.session_state.problem_index -= 1
            st.session_state.problem_show_solution_for = None
            st.rerun()
    with nav2:
        toggle_label = "Hide answer" if show_solution else "Show answer"
        if st.button(toggle_label, width="stretch"):
            st.session_state.problem_show_solution_for = None if show_solution else item["id"]
            st.rerun()
    with nav3:
        bookmark_label = "Remove bookmark" if q_progress["bookmarked"] else "Bookmark"
        if st.button(bookmark_label, width="stretch"):
            set_bookmark(user_id, item["id"], not bool(q_progress["bookmarked"]))
            st.rerun()
    with nav4:
        if st.button("Next", disabled=st.session_state.problem_index >= len(pool) - 1, width="stretch"):
            st.session_state.problem_index += 1
            st.session_state.problem_show_solution_for = None
            st.rerun()

    with st.container(border=True):
        header_left, header_right = st.columns([1, 0.3])
        with header_left:
            st.markdown("### Problem statement")
        with header_right:
            render_llm_copy_popover(item)
        render_preserved_text(item["question"])
        render_item_images(item)
    render_question_notes(item, q_progress, user_id)

    if show_solution:
        with st.container(border=True):
            st.markdown("### Stored answer")
            if item.get("solution_text"):
                render_preserved_text(item["solution_text"])
            else:
                st.info("No stored solution text is available for this problem yet.")
        render_saved_notes_summary(q_progress)

        with st.container(border=True):
            st.markdown("### Confidence")
            st.caption("Rate how confident you felt before looking at the stored answer.")
            slider_key = f"problem-confidence-{item['id']}"
            if slider_key not in st.session_state:
                st.session_state[slider_key] = q_progress["confidence_level"] or 3
            st.select_slider(
                "Confidence",
                options=[1, 2, 3, 4, 5],
                format_func=confidence_label,
                key=slider_key,
            )
            if st.button("Save confidence", width="stretch"):
                set_confidence(user_id, item["id"], int(st.session_state[slider_key]))
                st.rerun()


def bootstrap_navigation(user_state: dict[str, Any], active_mcq_session: dict[str, Any] | None) -> None:
    if st.session_state.bootstrapped_navigation:
        return

    last_section = user_state.get("last_section")
    if last_section in {"Overview", "Question browser", "Problems"}:
        st.session_state.nav_section = last_section

    if (
        last_section == "Multiple choice"
        and active_mcq_session
        and user_state.get("last_mcq_question_id")
    ):
        st.session_state.nav_section = "Multiple choice"
        st.session_state.mcq_active_category = active_mcq_session["category"]
        st.session_state.mcq_sidebar_topic = active_mcq_session["category"]

    st.session_state.bootstrapped_navigation = True


def main() -> None:
    st.set_page_config(page_title="Exam Practice", layout="wide")
    inject_css()
    user_context = current_user_context()
    if user_context["requires_login"]:
        render_login_gate()

    init_db(user_context["user_id"])
    init_session_state()

    bank = load_bank()
    report = load_report()

    if not bank:
        st.error("`question_bank.json` is missing. Run `./.venv/bin/python study_tool/build_bank.py` first.")
        return

    progress = load_progress(user_context["user_id"])
    user_state = load_user_state(user_context["user_id"])
    active_mcq_session, session_dirty = normalize_mcq_session(load_mcq_session(user_context["user_id"]), mcq_bank_map(bank))
    if active_mcq_session and session_dirty:
        active_mcq_session = save_mcq_session(
            user_context["user_id"],
            active_mcq_session["category"],
            active_mcq_session["mode"],
            active_mcq_session["queue_ids"],
            active_mcq_session["current_index"],
            active_mcq_session["answers"],
            started_at=active_mcq_session.get("started_at"),
        )

    bootstrap_navigation(user_state, active_mcq_session)

    st.sidebar.header("Navigation")
    if user_context["authenticated"]:
        st.sidebar.caption(f"Signed in as {user_context['display_name']}")
        if user_context["email"]:
            st.sidebar.caption(user_context["email"])
        st.sidebar.button("Log out", width="stretch", on_click=st.logout)
    else:
        st.sidebar.caption("Local guest mode")
        st.sidebar.caption("Configure Streamlit auth in secrets to sync progress across devices.")
    st.sidebar.caption("Start on the overview, then move into the section you want to drill.")
    selected_section = st.sidebar.radio(
        "Section",
        ["Overview", "Question browser", "Multiple choice", "Problems"],
        index=["Overview", "Question browser", "Multiple choice", "Problems"].index(st.session_state.nav_section),
    )
    if selected_section != st.session_state.nav_section:
        st.session_state.nav_section = selected_section

    if st.session_state.nav_section == "Overview":
        render_overview(bank, progress, report, user_context, active_mcq_session)
    elif st.session_state.nav_section == "Question browser":
        render_browser_page(bank, progress, user_context, active_mcq_session)
    elif st.session_state.nav_section == "Multiple choice":
        render_mcq_page(bank, progress, report, user_context["user_id"], user_state)
    else:
        render_problem_page(bank, progress, user_context["user_id"])


if __name__ == "__main__":
    main()
