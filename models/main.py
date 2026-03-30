from pydantic import BaseModel, Field

class SubscribeRequest(BaseModel):
    email: str = Field(..., description="User email address")
    skill: str = Field(..., description="Skill the user wants to learn")
    days: int = Field(90, gt=0, description="Number of days for the syllabus")
    hours: int = Field(1, gt=0, description="Hours per day the user will study")

class GenerateSyllabusRequest(BaseModel):
    email: str = Field(..., description="User email address")
    skill: str = Field(..., description="Skill to generate syllabus for")
