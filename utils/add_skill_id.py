import sqlite3
from datetime import datetime

DB_PATH = "../lexi.db"

email_dict = {
    "sample": "sample@gmail.com",
}

def get_skills():
    print("✅ Getting task")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, email, skill FROM skills 
    """)


    tasks = cursor.fetchall()
    conn.close()

    # Convert to structured dict
    return [
        {"id": row[0], "email": row[1], "skill": row[2] }
        for row in tasks
    ]

def get_skills_from_daily_tasks():
    print("✅ Getting skills from daily_tasks")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT user_id, skill FROM daily_tasks GROUP by skill
    """)


    tasks = cursor.fetchall()
    conn.close()

    # Convert to structured dict
    return [
        {"user_id": row[0], "skill": row[1] }
        for row in tasks
    ]

def update_skill_id_in_daily_tasks(skill, skill_id):
    print(f"{skill}:{skill_id}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE daily_tasks SET skill_id = ? WHERE skill = ?", (skill_id, skill))
    conn.commit()
    conn.close()

    return True

if __name__ == "__main__":
    skills = get_skills()
    skill_and_skill_id_mapping = {}

    for skill in skills:
        enrolled_skill = skill["skill"]
        enrolled_skill_id = skill["id"]

        update_skill_id_in_daily_tasks(enrolled_skill, enrolled_skill_id)

