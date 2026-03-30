# API Reference

Base URL: `http://localhost:3005`

---

## POST /subscribe

Register a user's email and skill. Stores their learning preferences (`days`, `hours`) for syllabus generation later.

**Request Body**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `email` | string | yes | — | User's email address |
| `skill` | string | yes | — | Skill the user wants to learn |
| `days` | integer | no | `90` | Total number of days for the learning plan |
| `hours` | integer | no | `1` | Hours per day the user will study |

**curl**

```bash
curl -X POST http://localhost:3005/subscribe \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "skill": "Python",
    "days": 90,
    "hours": 2
  }'
```

**Response**

```json
{
  "status": "success",
  "message": "Subscribed user@example.com to 'Python'",
  "user_id": "a3f2c1d4-5e6b-7890-abcd-ef1234567890"
}
```

**Error Responses**

| Status | Reason |
|--------|--------|
| `409` | Email is already subscribed to this skill |
| `500` | Failed to create subscription in database |

---

## POST /generate-syllabus

Generate the Month → Week → Day learning syllabus for a subscribed user using the Gemini API. Run this after `/subscribe`.

**Request Body**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `email` | string | yes | Email used during subscription |
| `skill` | string | yes | Skill to generate the syllabus for |

**curl**

```bash
curl -X POST http://localhost:3005/generate-syllabus \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "skill": "Python"
  }'
```

**Response**

```json
{
  "status": "success",
  "message": "Syllabus generated for 'Python'"
}
```

**Error Responses**

| Status | Reason |
|--------|--------|
| `404` | No subscription found for this email/skill combination |
| `500` | Gemini API failed to generate the syllabus |

---

## POST /generate-content

Generate AI-written newsletter content for the next 10 days across all active subscribers. Run this after `/generate-syllabus` and periodically to keep content ahead of the daily send.

**Request Body**

None.

**curl**

```bash
curl -X POST http://localhost:3005/generate-content
```

**Response**

```json
{
  "status": "success",
  "message": "Content generated for next 10 days"
}
```

**Error Responses**

| Status | Reason |
|--------|--------|
| `500` | Content generation failed |

---

## POST /issue-newsletters

Send today's learning newsletter to all active subscribers. Marks each sent task as completed. Intended to be run once daily (e.g. via a cron job).

**Request Body**

None.

**curl**

```bash
curl -X POST http://localhost:3005/issue-newsletters
```

**Response**

```json
{
  "status": "success",
  "message": "Today's newsletters issued successfully"
}
```

**Error Responses**

| Status | Reason |
|--------|--------|
| `500` | Newsletter delivery failed |

---

## Typical Flow

```
1. POST /subscribe          — register user with email, skill, days, hours
2. POST /generate-syllabus  — generate the full Month > Week > Day plan
3. POST /generate-content   — pre-generate newsletter content for first 10 days
4. POST /issue-newsletters  — send today's email (run daily via cron)
5. POST /generate-content   — run periodically to keep content ahead of sends
```
