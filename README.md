# EduGenie — AI Educational Assistant

EduGenie is a lightweight educational web application built with **FastAPI + HTML/CSS/JavaScript + Google Gemini**.

## Features

- Ask AI educational questions
- Generate 1–10 multiple-choice quiz questions
- Automatically score quizzes
- Summarize educational text
- Generate a personalized learning path
- Responsive dashboard
- Gemini AI integration
- Local fallback mode when no Gemini API key is configured
- One FastAPI server can serve both the API and frontend

## Project structure

```text
EduGenie/
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
├── backend/
│   ├── __init__.py
│   └── main.py
└── frontend/
    ├── index.html
    ├── script.js
    └── style.css
```

## Requirements

- Python 3.10 or newer
- VS Code
- Internet connection for Gemini AI
- A Gemini API key only if you want live Gemini responses

## 1. Open the project in VS Code

Extract the ZIP, then open the **EduGenie** folder in VS Code.

Open:

`Terminal → New Terminal`

## 2. Create a virtual environment

### Windows

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, use Command Prompt:

```cmd
.venv\Scripts\activate
```

### macOS/Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## 3. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 4. Configure Gemini (optional)

Copy:

`.env.example`

to:

`.env`

Then replace:

```text
GEMINI_API_KEY=your_api_key_here
```

with your Gemini API key.

You can also change:

```text
GEMINI_MODEL=gemini-2.5-flash
```

Do **not** upload `.env` to GitHub.

If you do not configure an API key, EduGenie still works using built-in fallback responses.

## 5. Start EduGenie

From the project root:

```bash
uvicorn backend.main:app --reload
```

Open:

http://127.0.0.1:8000

The same server provides both the frontend and backend, so you do not need a second web server.

## 6. Test the API

Open:

http://127.0.0.1:8000/health

You should see JSON similar to:

```json
{
  "status": "ok",
  "service": "EduGenie API",
  "gemini_configured": false
}
```

You can also open:

http://127.0.0.1:8000/docs

This is FastAPI's interactive API documentation.

## 7. Test the website

### Ask AI

Try:

`Which is the largest ocean?`

### Quiz

Try:

`Pythagoras Theorem`

Choose 5 questions and click **Generate Quiz**.

### Summarizer

Paste a few educational sentences and click **Summarize**.

### Learning Path

Try:

`Java`

Choose `Beginner` and click **Create My Learning Path**.

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/` | Web application |
| GET | `/health` | Server/configuration health |
| POST | `/api/ask` | Answer a question |
| POST | `/api/quiz` | Generate quiz questions |
| POST | `/api/summarize` | Summarize text |
| POST | `/api/learning-path` | Generate learning plan |
| GET | `/docs` | Interactive API documentation |

## Troubleshooting

### `python` is not recognized

Install Python 3.10+ and make sure **Add Python to PATH** was selected during installation.

### PowerShell says scripts are disabled

Use Command Prompt instead:

```cmd
.venv\Scripts\activate
```

### Port 8000 is already in use

Run:

```bash
uvicorn backend.main:app --reload --port 8001
```

Then open:

http://127.0.0.1:8001

### Gemini is not responding

Check that `.env` exists in the **EduGenie root folder** and contains a valid `GEMINI_API_KEY`.

The app will automatically fall back to local responses if Gemini is unavailable.

### CORS

When the frontend is served by the same FastAPI application, CORS is not normally needed. The configuration also permits common local development origins such as ports 5500 and 8000.

## Important security notes

- Never place your Gemini API key in `frontend/script.js`.
- Never commit `.env`.
- For production, replace permissive development settings with a specific allowed-origin list.
- Add authentication, rate limiting, logging, and persistent storage before exposing the service publicly.

## Development command

```bash
uvicorn backend.main:app --reload
```
