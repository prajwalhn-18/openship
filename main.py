from fastapi import FastAPI, HTTPException
from services.syllabus_generator import generate_syllabus
from services.content_generator import create_content_for_next_10_days, start_content_generation
from services.newsletter_issuer import issue_todays_newsletters, send_first_email
from models.main import GenerateContentRequest, OnboardRequest

app = FastAPI(title="Lexi4 Automation API", version="1.0")

def initial_user_onboard_orchestrator(user_id: str, skill: str, days: int = 90, hours: int = 1, user_email: str = ""):
    syllabus_generated = generate_syllabus(user_id, skill, days, hours, user_email)
    if not syllabus_generated:
        raise HTTPException(status_code=500, detail=f"Failed to generate syllabus for {user_id} ({skill})")

    content_generated = start_content_generation(user_id)
    if not content_generated:
        raise HTTPException(status_code=500, detail=f"Failed to generate content for {user_id}")

    first_email_sent = send_first_email(user_id)
    if not first_email_sent:
        raise HTTPException(status_code=500, detail=f"Failed to send first email for {user_id}")

    return {
        "status": "success",
        "message": f"User {user_id} successfully onboarded for {skill}",
    }


@app.post("/onboard-user")
def onboard_user(payload: OnboardRequest):
    """
    Run full onboarding process:
      - Generate syllabus
      - Generate content
      - Send first email
    """
    result = initial_user_onboard_orchestrator(payload.user_id, payload.skill, payload.days, payload.hours, payload.user_email)
    return result


@app.post("/issue-newsletters")
def issue_newsletters():
    """
    Sends today's newsletters to all users.
    """
    try:
        issue_todays_newsletters()
        return {"status": "success", "message": "Today's newsletters issued successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate-next-10-days")
def generate_next_10_days(payload: GenerateContentRequest):
    """
    Generates next 10 days of content for a given user.
    """
    try:
        create_content_for_next_10_days()
        return {"status": "success", "message": f"Next 10 days of content generated for user {payload.user_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=3005, reload=True)