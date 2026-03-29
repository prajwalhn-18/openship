from pydantic import BaseModel, Field

class OnboardRequest(BaseModel):
    user_id: str = Field(..., description="Unique user ID")
    user_email: str = Field(..., description="User email is required")
    skill: str = Field(..., description="Skill user wants to learn")
    days: int = Field(90, gt=0, description="Number of days for syllabus")
    hours: int = Field(1, gt=0, description="Hours per day user will study")

class GenerateContentRequest(BaseModel):
    user_id: str = Field(..., description="User ID to generate content for")