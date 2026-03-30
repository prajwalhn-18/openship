import os
import sqlite3
from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.getenv("DB_PATH", "openship.db")

def execute_query_one(query, params=None):
    """Run a SELECT returning a single row."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute(query, params or ())
        row = cursor.fetchone()
        return row

    except sqlite3.Error as e:
        print(f"[DB ERROR] execute_query_one failed: {e}")
        return None

    finally:
        try:
            conn.close()
        except:
            pass

def execute_query_all(query, params=None):
    """Run a SELECT returning all rows."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute(query, params or ())
        rows = cursor.fetchall()
        return rows

    except sqlite3.Error as e:
        print(f"[DB ERROR] execute_query_all failed: {e}")
        return []

    finally:
        try:
            conn.close()
        except:
            pass

def execute_update(query, params=None):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute(query, params or ())
        conn.commit()

        return True

    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        return False

    except Exception as e:
        print(f"⚠️ Unexpected error: {e}")
        return False

    finally:
        try:
            conn.close()
        except:
            pass

def init_skills_table():
    execute_update("""
        CREATE TABLE IF NOT EXISTS skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            email TEXT NOT NULL,
            skill TEXT NOT NULL,
            days INTEGER DEFAULT 90,
            hours INTEGER DEFAULT 1,
            stop_sending INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # Migrate existing tables missing columns
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    existing_columns = {row[1] for row in cursor.execute("PRAGMA table_info(skills)")}
    migrations = {
        "days":  "ALTER TABLE skills ADD COLUMN days INTEGER DEFAULT 90",
        "hours": "ALTER TABLE skills ADD COLUMN hours INTEGER DEFAULT 1",
    }
    for col, sql in migrations.items():
        if col not in existing_columns:
            cursor.execute(sql)
    conn.commit()
    conn.close()

def skill_exists(email: str, skill: str) -> bool:
    row = execute_query_one(
        "SELECT id FROM skills WHERE email = ? AND skill = ?", (email, skill)
    )
    return row is not None

def create_skill(user_id: str, email: str, skill: str, days: int, hours: int) -> int | None:
    init_skills_table()
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO skills (user_id, email, skill, days, hours) VALUES (?, ?, ?, ?, ?)",
            (user_id, email, skill, days, hours),
        )
        conn.commit()
        return cursor.lastrowid
    except Exception as e:
        print(f"[DB ERROR] create_skill failed: {e}")
        return None
    finally:
        if conn:
            conn.close()

def get_skill(email: str, skill: str) -> dict | None:
    row = execute_query_one(
        "SELECT user_id, days, hours FROM skills WHERE email = ? AND skill = ?", (email, skill)
    )
    if row is None:
        return None
    return {"user_id": row[0], "days": row[1], "hours": row[2]}

def get_list_of_skill_ids():
    query = "SELECT id from skills where stop_sending = 0"
    rows = execute_query_all(query)

    skill_ids = []

    if rows:
        for row in rows:
            skill_ids.append(row[0])

    return skill_ids

def get_email_id_from_skill_id(skill_id):
    print(f"✅ Getting email id for {skill_id}")
    query = "SELECT email FROM skills WHERE id = ?"
    row = execute_query_one(query, (skill_id,))

    if row is None:
        return None

    email_id = row[0]
    return email_id

def get_tasks_based_on_skill_id(skill_id: int):
    query = """
        SELECT id, skill, topic, task, hours, day, newsletter, skill_id
        FROM daily_tasks
        WHERE skill_id = ?
          AND completed = 0
        ORDER BY day ASC
        LIMIT 1;
    """
    rows = execute_query_all(query, (skill_id,))

    # Convert to structured dict
    return [
        {"id": row[0], "skill": row[1], "topic": row[2], "task": row[3], "hours": row[4], "day": row[5], "newsletter": row[6], "skill_id": row[7]}
        for row in rows
    ]

def get_tasks_for_generating_newsletter(skill_id: int):
    print("✅ Getting task for generating newsletter...")
    query="""
        SELECT id, skill, topic, task, hours, day
        FROM daily_tasks
        WHERE skill_id = ?
          AND completed = 0
          AND newsletter IS NULL
        ORDER BY day ASC
        LIMIT 90;
    """
    rows = execute_query_all(query, (skill_id,))

    # Convert to structured dict
    return [
        {"id": row[0], "skill": row[1], "topic": row[2], "task": row[3], "hours": row[4], "day": row[5]}
        for row in rows
    ]

def add_content_to_db(newsletter, task_id):
    try:
        print(f"✅ Updating newsletter {task_id}...")
        query = """
            UPDATE daily_tasks
            SET newsletter = ?
            WHERE id = ?
        """

        rows = execute_update(query, (newsletter, task_id))

        if rows == None:
            return False

        return 
    except Exception as e:
        print(f"⚠️ Unexpected error in add_content_to_db: {e}")
        return False
