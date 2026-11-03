# 🎓 AI University Admissions Agent

A conversational admissions assistant built with **LangChain** and **Google Gemini**. It answers questions about courses, fees, and admission criteria, and manages student enrollments in a local **SQLite** database.

## Features

- 📚 Course details: fees, duration, prerequisites
- 📝 Enroll, look up, and cancel student enrollments
- 🏫 Admission criteria, deadlines, and campus contact info
- 💬 Conversation memory within a session
- 🔒 API key kept out of the code via `.env`

## Project Structure

```
edu-admissions-agent/
├── edu_agent.py        # Agent, tools, and chat loop
├── requirements.txt    # Python dependencies
├── .env.example        # Template for your API key
├── .gitignore
├── LICENSE
└── README.md
```

## Setup

1. Install Python 3.10 or newer.
2. Install the dependencies listed in `requirements.txt`.
3. Copy `.env.example` to `.env` and set your Gemini API key:

   ```
   GOOGLE_API_KEY=your_gemini_api_key_here
   ```

   Get a key at [Google AI Studio](https://aistudio.google.com/apikey).
4. Run `edu_agent.py`.

The `university.db` database file is created automatically on first run.

## Configuration

| Variable | Required | Description |
|---|---|---|
| `GOOGLE_API_KEY` | Yes | Your Gemini API key |
| `GEMINI_MODEL` | No | Gemini model name (default set in `edu_agent.py`) |

## Example

```
Student: What courses do you offer?
AI: We offer Computer Science, Business Administration, Data Science Bootcamp, and Graphic Design.

Student: Enroll Ali Khan in Graphic Design
AI: Ali Khan has been enrolled in Graphic Design. 🎉
```

## Available Tools

| Tool | Purpose |
|---|---|
| `get_course_details` | Fees, duration, prerequisites |
| `show_all_courses` | List all programs |
| `enroll_student` | Register a student (validates the course exists) |
| `find_enrollment` | Look up a student's record |
| `cancel_enrollment` | Remove a student's enrollment |
| `get_admission_criteria` | Eligibility and deadlines |
| `get_institution_info` | Office hours and contact |

## License

Released under the [MIT License](LICENSE).
