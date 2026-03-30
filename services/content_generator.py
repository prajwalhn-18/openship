import os
import requests
import json
import time
from typing import Any
from dotenv import load_dotenv
from services.db_service import get_list_of_skill_ids, get_tasks_for_generating_newsletter, add_content_to_db
from services.user_emails import email_dict

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
API_URL = os.getenv("GEMINI_API_URL")
DB_PATH = os.getenv("DB_PATH", "openship.db")

def generate_syllabus_content(task_description: str, task_title: str, skill: str):
    if not API_KEY:
        raise ValueError("Missing GEMINI_API_KEY environment variable.")

    system_prompt = (
        "You are a senior technical educator and blog writer. "
        "Write a detailed, beginner-friendly blog explaining the concept or task described. "
        "Focus on practical explanation, step-by-step instructions, examples, and insights. "
        "Return the response as clean HTML content no css (no extra headers or metadata). This HTML content is sent via email, so do not create anything that is malicious, keep HTML to standard gmail format."
        "While taking examples, take examples relevant to the industry or skill that is given."
    )

    user_prompt = f"Write a detailed blog about the following title: {task_title} for skill {skill} for task:\n\n{task_description} "

    payload = {
        "contents": [
            {"parts": [{"text": user_prompt}]}
        ],
        "systemInstruction": {
            "parts": [{"text": system_prompt}]
        }
    }

    print("✅ Generating newsletter")
    response = requests.post(
        f"{API_URL}?key={API_KEY}",
        data=json.dumps(payload),
        timeout=(10, 120)
    )
    response.raise_for_status()
    result = response.json()

    try:
        html_content = result["candidates"][0]["content"]["parts"][0]["text"]
        return html_content
    except (KeyError, IndexError):
        print("Unexpected API response structure:")
        print(json.dumps(result, indent=2))
        return False
        
def start_content_generation(skill_id: str):
    try:
        tasks = get_tasks_for_generating_newsletter(skill_id)

        for i, task in enumerate[dict[str, Any]](tasks, 1):
            try:

                task_id = task['id']
                print(f"Newsletter ID: {task['id']} | Topic: {task["topic"]}")
                task_description = task['task']
                task_title = task["topic"]
                skill = task['skill']
                blog_html = generate_syllabus_content(task_description, task_title, skill)
                add_content_to_db(newsletter=blog_html, task_id=task_id)
                time.sleep(5)
            except Exception as e:
                print(e)
                continue
        
        return True
    except ValueError:
        print("Error in start_content_generation")
        return False

def create_content_for_newsletters():
    try:
        skill_ids = get_list_of_skill_ids()

        for skill_id in skill_ids:
            start_content_generation(skill_id)

        return True
    except ValueError:
        print()
        return False