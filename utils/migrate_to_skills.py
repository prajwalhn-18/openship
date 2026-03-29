import sqlite3
from datetime import datetime

DB_PATH = "../lexi.db"

email_dict = {
   "sample": "sample@gmail.com"
}

def get_skills():
    print("✅ Getting task")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, user_id, skill FROM daily_tasks GROUP BY skill order by day ASC
    """)


    tasks = cursor.fetchall()
    conn.close()

    # Convert to structured dict
    return [
        {"id": row[0], "user_id": row[1], "skill": row[2] }
        for row in tasks
    ]

def insert_skill_record(user_id, email, skill):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO skills (name, email, phone, skill, skill_reminder_time, created_at, updated_at)
        VALUES (NULL, ?, NULL, ?, ?, ?, ?)
    """, (
        email,                      # email
        skill,                      # skill
        "09:00",                    # skill_reminder_time
        datetime.now(),             # created_at
        datetime.now()              # updated_at
    ))

    conn.commit()
    conn.close()

if __name__ == "__main__":
    tasks = get_skills()

    for task in tasks:
        username = task["user_id"]
        user_email = email_dict[username]
        skill = task["skill"]
        insert_skill_record(username, user_email, skill)

        print(f"{user_email}: {skill}")

