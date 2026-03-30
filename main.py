import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from services.syllabus_generator import generate_syllabus, init_db
from services.content_generator import create_content_for_newsletters, start_content_generation, generate_content_for_task
from services.newsletter_issuer import issue_todays_newsletters, send_newsletter
from services.refresh_token import get_new_jwt_token
from services.db_service import skill_exists, create_skill, get_skill, get_all_syllabi, get_syllabus_detail, get_chapter_content, get_email_id_from_skill_id
from models.main import SubscribeRequest, GenerateSyllabusRequest, GenerateContentRequest, GenerateChapterContentRequest, SendChapterEmailRequest

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(title="Openship Automation API", version="1.0", lifespan=lifespan)


@app.post("/subscribe")
def subscribe(payload: SubscribeRequest):
    """
    Register a user's email and skill for daily learning newsletters.
    """
    if skill_exists(payload.email, payload.skill):
        raise HTTPException(status_code=409, detail=f"{payload.email} is already subscribed to '{payload.skill}'")

    user_id = str(uuid.uuid4())
    skill_id = create_skill(user_id, payload.email, payload.skill, payload.days, payload.hours)
    if skill_id is None:
        raise HTTPException(status_code=500, detail="Failed to create subscription")

    return {"status": "success", "message": f"Subscribed {payload.email} to '{payload.skill}'", "user_id": user_id}


@app.get("/syllabi")
def list_syllabi():
    """
    Return all active subscriptions with task progress stats.
    """
    return get_all_syllabi()


@app.get("/syllabi/{skill_id}")
def get_syllabus(skill_id: int):
    """
    Return the full chapter breakdown (months → weeks → days) for a syllabus.
    """
    detail = get_syllabus_detail(skill_id)
    if detail is None:
        raise HTTPException(status_code=404, detail=f"Syllabus {skill_id} not found")
    return detail


@app.post("/generate-syllabus")
def generate_syllabus_endpoint(payload: GenerateSyllabusRequest):
    """
    Generate the learning syllabus for a subscribed user.
    """
    skill = get_skill(payload.email, payload.skill)
    if skill is None:
        raise HTTPException(status_code=404, detail=f"No subscription found for {payload.email} / '{payload.skill}'")

    success = generate_syllabus(skill["user_id"], payload.skill, skill["days"], skill["hours"], payload.email)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to generate syllabus")

    return {"status": "success", "message": f"Syllabus generated for '{payload.skill}'"}


@app.post("/generate-content")
def generate_content(payload: GenerateContentRequest):
    """
    Generate content for the next 10 days for a specific skill.
    """
    try:
        start_content_generation(payload.skill_id)
        return {"status": "success", "message": f"Content generated for skill {payload.skill_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate-content/chapter")
def generate_chapter_content(payload: GenerateChapterContentRequest):
    """
    Generate newsletter content for a single chapter (task).
    """
    success = generate_content_for_task(payload.task_id)
    if not success:
        raise HTTPException(status_code=500, detail=f"Failed to generate content for task {payload.task_id}")
    return {"status": "success", "message": f"Content generated for task {payload.task_id}"}


@app.get("/chapter/{task_id}")
def get_chapter(task_id: int):
    """
    Return the full content (newsletter HTML) for a single chapter.
    """
    chapter = get_chapter_content(task_id)
    if chapter is None:
        raise HTTPException(status_code=404, detail=f"Chapter {task_id} not found")
    return chapter


@app.post("/send-email/chapter")
def send_chapter_email(payload: SendChapterEmailRequest):
    """
    Send the newsletter email for a single chapter and mark it completed.
    """
    chapter = get_chapter_content(payload.task_id)
    if chapter is None:
        raise HTTPException(status_code=404, detail=f"Chapter {payload.task_id} not found")
    if not chapter["newsletter"]:
        raise HTTPException(status_code=400, detail="No content generated for this chapter yet")

    email = get_email_id_from_skill_id(chapter["skill_id"])
    if not email:
        raise HTTPException(status_code=404, detail="Could not find email for this skill")

    token = get_new_jwt_token()
    title = f"Day {chapter['day']} - {chapter['skill']}: {chapter['topic']}"
    send_newsletter.__globals__["TOKEN"] = token
    send_newsletter(email_to=email, title=title, content=chapter["newsletter"])

    from services.db_service import execute_update
    execute_update("UPDATE daily_tasks SET completed = 1 WHERE id = ?", (payload.task_id,))

    return {"status": "success", "message": f"Email sent to {email} for Day {chapter['day']}"}


@app.post("/issue-newsletters")
def issue_newsletters():
    """
    Send today's newsletter to all active subscribers.
    """
    try:
        issue_todays_newsletters()
        return {"status": "success", "message": "Today's newsletters issued successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=3005, reload=True)
