# Openship

Openship is an AI-powered personalized learning platform that generates a custom curriculum for any skill and delivers daily learning content directly to your inbox.

## How it works

1. **Onboard** — provide your skill goal, experience level, and available time commitment
2. **Generate** — Gemini AI creates a structured Month → Week → Day learning syllabus tailored to you
3. **Learn** — receive a daily newsletter with AI-written, beginner-friendly content for that day's topic

## Features

- Personalized syllabus generation using Google Gemini (structured 3-level hierarchy: month/week/day)
- Automated daily newsletter delivery via email
- Content generation with HTML-formatted, educator-style writing
- Progress tracking per skill with task completion status
- Background content pre-generation for upcoming days

## Tech Stack

- **FastAPI** — async REST API backend
- **Google Gemini API** — syllabus and content generation (structured JSON output)
- **SQLite** — user, skill, and task storage

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/onboard-user` | Register a user and kick off syllabus + content generation |
| `POST` | `/issue-newsletters` | Send today's learning content to all active users |
| `POST` | `/generate-content` | Pre-generate content for newsletter |

## Getting Started

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env  # add your Gemini API key, Linkifyi credentials, etc.

# Run the server
uvicorn main:app --reload
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `GEMINI_API_KEY` | Google Gemini API key |
| `LINKIFYI_API_KEY` | Linkifyi email service API key |
| `SENTRY_DSN` | (Optional) Sentry DSN for error tracking |
