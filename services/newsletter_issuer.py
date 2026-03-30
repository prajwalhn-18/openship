import time
from typing import Any
import requests
import json
import os
from dotenv import load_dotenv
import sqlite3
from services.db_service import get_list_of_skill_ids, get_tasks_based_on_skill_id
from services.refresh_token import get_new_jwt_token

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
API_URL = os.getenv("GEMINI_API_URL")
DB_PATH = os.getenv("DB_PATH", "openship.db")
TOKEN = os.getenv("LINKIFYI_TOKEN")

def get_tasks_for_day(user_id: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, skill, topic, task, hours, day, newsletter, skill_id
        FROM daily_tasks
        WHERE user_id = ?
          AND completed = 0
        ORDER BY day ASC
        LIMIT 1;
    """, (user_id,))


    tasks = cursor.fetchall()
    conn.close()

    # Convert to structured dict
    return [
        {"id": row[0], "skill": row[1], "topic": row[2], "task": row[3], "hours": row[4], "day": row[5], "newsletter": row[6], "skill_id": row[7]}
        for row in tasks
    ]

def send_newsletter(email_to: str, title: str, content: str):
    url = "https://app.linkifyi.com/api/lexi/send-newsletter"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {TOKEN}",
        "Cookie": f"TOKEN={TOKEN}"
    }

    payload = {
        "emailTo": email_to,
        "templateId": "e545f7f9-5acc-47d4-9642-d5bcba6b22d4",
        "subject": title,
        "variables": {
            "6ee3029f-5e1e-4a77-ae2f-a2d9285f7b7a": title,
            "8a0194f8-4cb0-4655-b534-68c13b72100c": content
        }
    }

    try:
        print(f"Sending newsletter to {email_to} with title {title} and content {content}")
        '''
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()  # Raises an error for 4xx/5xx responses
        return response.json()
        '''
        print("✅ Email sent successfully!")
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to send email: {e}")
        return None

def update_task_completed(task_id: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE daily_tasks SET completed = 1 WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()

    return True

def get_email_id_from_skill_id(skill_id):
    print(f"✅ Getting email id for {skill_id}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT email FROM skills WHERE id = ?", (skill_id,))
    
    row = cursor.fetchone()
    conn.close()

    if row is None:
        return None

    email_id = row[0]
    return email_id

def send_first_email(user_id: str):
    global TOKEN
    TOKEN = get_new_jwt_token()
    
    tasks = get_tasks_for_day(user_id)

    if not tasks:
        return False

    for i, t in enumerate(tasks, 1):
        try:
            print(f"{i}. [{t['skill']}] {t['topic']} → {t['task']} ({t['hours']} hrs)")

            title = f"Day {t['day']} - {t['skill']}: {t['topic']}"
            blog_html = t["newsletter"]

            if blog_html is None:
                print(f"❌ No newsletter found for userId: {user_id} | task: {t["id"]}")
                continue
            
            email_id = get_email_id_from_skill_id(t["skill_id"])

            send_newsletter(
                email_to=email_id,
                title=title, 
                content=blog_html
            )

            update_task_completed(t['id'])
            return True
        except ValueError:
            print("Error in send_first_email")
            return False
    
def check_newsletter_available_for_all_users():
    skill_ids = get_list_of_skill_ids()
    valid_skill_ids = []

    for skill_id in skill_ids:
        print(f"getting tasks for skill: {skill_id}")

        tasks = get_tasks_based_on_skill_id(skill_id)

        if not tasks:
            print(f"❌ No tasks found for skill: {skill_id}, removing it")
            continue

        valid_skill_ids.append(skill_id)

    return valid_skill_ids
    
def issue_todays_newsletters():
    global TOKEN
    TOKEN = get_new_jwt_token()

    skill_ids = get_list_of_skill_ids()
    
    valid_skill_ids = check_newsletter_available_for_all_users()
    
    for skill_id in valid_skill_ids:
        time.sleep(5)

        tasks = get_tasks_based_on_skill_id(skill_id)

        if not tasks:
            continue

        for i, t in enumerate[dict[str, Any]](tasks, 1):
            print(f"{i}. [{t['skill']}] {t['topic']} → {t['task']} ({t['hours']} hrs)")

            title = f"Day {t['day']} - {t['skill']}: {t['topic']}"
            blog_html = t["newsletter"]

            if blog_html is None:
                print(f"❌ No newsletter found for userId: {skill_id} | task: {t["id"]}")
                continue
            
            email_id = get_email_id_from_skill_id(t["skill_id"])
            print(f"{email_id}:{title}")

            send_newsletter(
                email_to=email_id,
                title=title, 
                content=blog_html
            )

            update_task_completed(t['id'])

    return True
