import json
import time
import requests
import os
import sqlite3
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

# --- Configuration ---
# NOTE: Replace the placeholder with your actual Gemini API Key.
# If running outside a canvas environment, you must provide your key.
API_KEY = os.getenv("GEMINI_API_KEY")
API_URL = os.getenv("GEMINI_API_URL")
DB_PATH = os.getenv("DB_PATH", "openship.db")
# --- JSON Schema Definition (Ensures structured output) ---
# This schema enforces the exact 'Month > Week > Day' structure requested.
SYLLABUS_SCHEMA = {
    "type": "ARRAY",
    "items": {
        "type": "OBJECT",
        "properties": {
            "month": { "type": "INTEGER", "description": "The month number (1, 2, 3, etc.)." },
            "title": { "type": "STRING", "description": "A descriptive title for the month's learning phase." },
            "goal": { "type": "STRING", "description": "The main learning goal for this month." },
            "weeks": {
                "type": "ARRAY",
                "items": {
                    "type": "OBJECT",
                    "properties": {
                        "week": { "type": "INTEGER", "description": "The week number within the total duration." },
                        "title": { "type": "STRING", "description": "A title summarizing the week's topics." },
                        "days_range": { "type": "STRING", "description": "The range of days covered in this week (e.g., 'Days 1-7')." },
                        "daily_plan": {
                            "type": "ARRAY",
                            "items": {
                                "type": "OBJECT",
                                "properties": {
                                    "day": { "type": "INTEGER", "description": "The day number in the overall plan (1 to total_days)." },
                                    "topic": { "type": "STRING", "description": "The main topic or concept for this specific day." },
                                    "task": { "type": "STRING", "description": "A specific, actionable, and detailed learning task for the daily hours." }
                                },
                                "propertyOrdering": ["day", "topic", "task"]
                            }
                        }
                    },
                    "propertyOrdering": ["week", "title", "days_range", "daily_plan"]
                }
            }
        },
        "propertyOrdering": ["month", "title", "goal", "weeks"]
    }
}

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            skill TEXT NOT NULL,
            skill_id INTEGER,
            month INTEGER,
            week INTEGER,
            day INTEGER,
            topic TEXT,
            task TEXT,
            hours INTEGER,
            newsletter TEXT,
            completed INTEGER DEFAULT 0,
            stop_sending INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    # Migrate existing tables missing columns
    existing_columns = {row[1] for row in cursor.execute("PRAGMA table_info(daily_tasks)")}
    migrations = {
        "skill_id":     "ALTER TABLE daily_tasks ADD COLUMN skill_id INTEGER",
        "newsletter":   "ALTER TABLE daily_tasks ADD COLUMN newsletter TEXT",
        "completed":    "ALTER TABLE daily_tasks ADD COLUMN completed INTEGER DEFAULT 0",
        "stop_sending": "ALTER TABLE daily_tasks ADD COLUMN stop_sending INTEGER DEFAULT 0",
    }
    for col, sql in migrations.items():
        if col not in existing_columns:
            cursor.execute(sql)
    conn.commit()
    conn.close()

def start_syllabus_generation(skill: str, days: int, hours: int):
    """
    Generates a structured learning syllabus using the Gemini API.
    """
    if not API_KEY:
        print("ERROR: API_KEY is missing. Please set your Gemini API key.")
        return

    # System instruction to guide the model's persona and logic
    system_prompt = (
        "You are an expert curriculum designer and career mentor. "
        "Your task is to create an in-depth, structured learning roadmap for the requested skill. "
        "The plan must strictly adhere to the provided JSON schema. "
        "The total duration must match the requested number of days. "
        "Ensure the daily tasks are specific, actionable, and cover the necessary depth for the given skill and time commitment."
    )

    # User prompt containing all input variables
    user_query = (
        f"Create a comprehensive learning syllabus to master the skill '{skill}'. "
        f"The total plan must span exactly {days} days, with an expected time commitment of {hours} hours per day. "
        "Please generate the complete roadmap using the required JSON schema."
    )

    # Construct the API Payload
    payload = {
        "contents": [
            {"parts": [{"text": user_query}]}
        ],
        "systemInstruction": {
            "parts": [{"text": system_prompt}]
        },
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": SYLLABUS_SCHEMA
        }
    }

    headers = {
        'Content-Type': 'application/json'
    }

    print(f"Generating syllabus for '{skill}' over {days} days...")

    # Implement exponential backoff for robustness
    max_retries = 5
    delay = 1  # starting delay in seconds

    for attempt in range(max_retries):
        try:
            response = requests.post(
                f"{API_URL}?key={API_KEY}",
                headers=headers,
                data=json.dumps(payload),
                timeout=(10, 120)  # Timeout after 30 seconds
            )
            response.raise_for_status()  # Raises HTTPError for bad responses (4xx or 5xx)

            result = response.json()

            # Process and extract the JSON response
            if (result.get('candidates') and
                result['candidates'][0].get('content') and
                result['candidates'][0]['content'].get('parts')):
                
                # The structured JSON is inside the 'text' field of the part
                json_string = result['candidates'][0]['content']['parts'][0]['text']
                
                # Parse and return the generated JSON object
                return json.loads(json_string)

            else:
                print("API returned an unexpected structure.")
                print(json.dumps(result, indent=2))
                return None

        except requests.exceptions.RequestException as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                print(f"Retrying in {delay} seconds...")
                time.sleep(delay)
                delay *= 2  # Exponential backoff
            else:
                print("Max retries reached. Failed to generate syllabus.")
                return None
        except json.JSONDecodeError:
            print("Failed to decode JSON from API response. Check raw response for errors.")
            print(response.text)
            return None

def get_skill_id_using_email_and_skill(email, skill):
    print(f"✅ Getting skill id for email: {email}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM skills WHERE email = ? and skill = ?", (email, skill))
    
    row = cursor.fetchone()
    conn.close()

    if row is None:
        return None

    skill_id = row[0]
    return skill_id

def store_syllabus_in_db(user_id: str, skill: str, syllabus_data: list, hours: int, skill_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    for month_obj in syllabus_data:
        month = month_obj.get("month")
        for week_obj in month_obj.get("weeks", []):
            week = week_obj.get("week")
            for day_obj in week_obj.get("daily_plan", []):
                day = day_obj.get("day")
                topic = day_obj.get("topic")
                task = day_obj.get("task")

                cursor.execute("""
                    INSERT INTO daily_tasks (user_id, skill, month, week, day, topic, task, hours, skill_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (user_id, skill, month, week, day, topic, task, hours, skill_id))

    conn.commit()
    conn.close()
    print(f"Syllabus for '{skill}' stored successfully in database.")

def get_tasks_for_day(user_id: str, day: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT skill, topic, task, hours
        FROM daily_tasks
        WHERE user_id = ?
        AND day = ?
        ORDER BY skill
        LIMIT 4;
    """, (user_id, day))

    tasks = cursor.fetchall()
    conn.close()

    # Convert to structured dict
    return [
        {"skill": row[0], "topic": row[1], "task": row[2], "hours": row[3]}
        for row in tasks
    ]

def generate_syllabus(user_id: str, skill: str, days: int, hours: int, user_email: str):
    print("--- Custom Syllabus Generator (with SQLite Storage) ---")
    init_db()

    syllabus_data = start_syllabus_generation(skill, days, hours)
    skill_id = get_skill_id_using_email_and_skill(user_email, skill)

    if skill_id == None:
        print("❌ Failed to generate syllabus as there is no matching skill for the user")
        return None

    print(f"skill_id: {skill_id}")
    
    if syllabus_data:
        store_syllabus_in_db(user_id, skill, syllabus_data, hours, skill_id)
        print("Syllabus stored successfully.")
        return True
    else:
        return False
