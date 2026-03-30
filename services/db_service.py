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

def get_syllabus_detail(skill_id: int) -> dict | None:
    skill_row = execute_query_one(
        "SELECT id, user_id, email, skill, days, hours, created_at FROM skills WHERE id = ?",
        (skill_id,)
    )
    if skill_row is None:
        return None

    tasks = execute_query_all("""
        SELECT id, day, month, week, topic, task, hours, completed, newsletter IS NOT NULL
        FROM daily_tasks
        WHERE skill_id = ?
        ORDER BY month ASC, week ASC, day ASC
    """, (skill_id,))

    months: dict = {}
    for row in tasks:
        task_id, day, month, week, topic, task, hours, completed, has_content = row
        m = months.setdefault(month, {})
        w = m.setdefault(week, [])
        w.append({
            "id": task_id,
            "day": day,
            "topic": topic,
            "task": task,
            "hours": hours,
            "completed": bool(completed),
            "has_content": bool(has_content),
        })

    return {
        "skill_id": skill_row[0],
        "user_id": skill_row[1],
        "email": skill_row[2],
        "skill": skill_row[3],
        "days": skill_row[4],
        "hours": skill_row[5],
        "created_at": skill_row[6],
        "months": [
            {
                "month": m,
                "weeks": [
                    {"week": w, "tasks": tasks_list}
                    for w, tasks_list in sorted(weeks.items())
                ],
            }
            for m, weeks in sorted(months.items())
        ],
    }

def get_chapter_content(task_id: int) -> dict | None:
    row = execute_query_one(
        """SELECT id, skill, skill_id, topic, task, day, hours, completed, newsletter
           FROM daily_tasks WHERE id = ?""",
        (task_id,)
    )
    if row is None:
        return None
    return {
        "id": row[0], "skill": row[1], "skill_id": row[2], "topic": row[3],
        "task": row[4], "day": row[5], "hours": row[6],
        "completed": bool(row[7]), "newsletter": row[8],
    }

def get_all_syllabi():
    query = """
        SELECT
            s.id, s.user_id, s.email, s.skill, s.days, s.hours, s.created_at,
            COUNT(dt.id) as total_tasks,
            SUM(CASE WHEN dt.completed = 1 THEN 1 ELSE 0 END) as completed_tasks
        FROM skills s
        LEFT JOIN daily_tasks dt ON dt.skill_id = s.id
        WHERE s.stop_sending = 0
        GROUP BY s.id
        ORDER BY s.created_at DESC
    """
    rows = execute_query_all(query)
    return [
        {
            "skill_id": row[0],
            "user_id": row[1],
            "email": row[2],
            "skill": row[3],
            "days": row[4],
            "hours": row[5],
            "created_at": row[6],
            "total_tasks": row[7] or 0,
            "completed_tasks": int(row[8] or 0),
        }
        for row in rows
    ]

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
