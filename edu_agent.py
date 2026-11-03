"""AI University Admissions Agent.

A LangChain agent powered by Google Gemini that answers course questions
and manages student enrollments in a local SQLite database.
"""

import os
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import MemorySaver

load_dotenv()

# ---------------------------------------------------------------------------
# 1. CONFIG
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "university.db"
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
API_KEY = os.getenv("GOOGLE_API_KEY")

if not API_KEY:
    raise SystemExit(
        "Missing GOOGLE_API_KEY. Copy .env.example to .env and add your Gemini API key."
    )

# ---------------------------------------------------------------------------
# 2. DATABASE
# ---------------------------------------------------------------------------
db = sqlite3.connect(DB_PATH, check_same_thread=False)
db.execute(
    """
    CREATE TABLE IF NOT EXISTS enrollments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_name TEXT UNIQUE NOT NULL COLLATE NOCASE,
        course_name TEXT,
        enrollment_date TEXT
    )
    """
)
db.commit()

COURSES_DB = {
    "computer science": {
        "fee": "$5000/semester",
        "duration": "4 Years",
        "prerequisites": "High School Math & Physics",
    },
    "business administration": {
        "fee": "$4500/semester",
        "duration": "4 Years",
        "prerequisites": "High School Diploma",
    },
    "data science bootcamp": {
        "fee": "$1200",
        "duration": "6 Months",
        "prerequisites": "Basic Python Programming",
    },
    "graphic design": {
        "fee": "$800",
        "duration": "3 Months",
        "prerequisites": "None",
    },
}


def _match_course(course_name: str):
    """Return the canonical course key matching the input, or None."""
    query = course_name.lower().strip()
    if not query:
        return None
    for key in COURSES_DB:
        if query in key or key in query:
            return key
    return None


# ---------------------------------------------------------------------------
# 3. TOOLS
# ---------------------------------------------------------------------------
@tool
def get_course_details(course_name: str) -> str:
    """Get tuition fees, duration, and prerequisites for a specific course."""
    key = _match_course(course_name)
    if key is None:
        return f"Course '{course_name}' not found. Ask to see all available courses."
    info = COURSES_DB[key]
    return (
        f"Course: {key.title()}\n"
        f"Fee: {info['fee']}\n"
        f"Duration: {info['duration']}\n"
        f"Prerequisites: {info['prerequisites']}"
    )


@tool
def show_all_courses() -> str:
    """List all available academic programs and courses."""
    result = "Available Courses & Programs:\n"
    for name in COURSES_DB:
        result += f"- {name.title()}\n"
    return result


@tool
def enroll_student(student_name: str, course_name: str, enrollment_date: str = "") -> str:
    """Register a new student for a course. enrollment_date is optional (YYYY-MM-DD); defaults to today."""
    name = student_name.strip()
    if not name:
        return "Enrollment failed. A student name is required."

    course_key = _match_course(course_name)
    if course_key is None:
        return f"Enrollment failed. Course '{course_name}' does not exist. Use show_all_courses to see options."

    date = enrollment_date.strip() or datetime.now().strftime("%Y-%m-%d")

    existing = db.execute(
        "SELECT course_name FROM enrollments WHERE LOWER(student_name) = ?",
        (name.lower(),),
    ).fetchone()
    if existing:
        return f"Enrollment failed. {name} is already enrolled in {existing[0]}."

    try:
        db.execute(
            "INSERT INTO enrollments (student_name, course_name, enrollment_date) VALUES (?, ?, ?)",
            (name, course_key.title(), date),
        )
        db.commit()
    except sqlite3.IntegrityError:
        return f"An enrollment record for {name} already exists."
    return f"{name} was successfully enrolled in {course_key.title()} on {date}."


@tool
def find_enrollment(student_name: str) -> str:
    """Retrieve an existing student's admission record."""
    record = db.execute(
        "SELECT id, student_name, course_name, enrollment_date FROM enrollments WHERE LOWER(student_name) = ?",
        (student_name.strip().lower(),),
    ).fetchone()
    if record:
        return f"ID: {record[0]} | Student: {record[1]} | Course: {record[2]} | Date: {record[3]}"
    return f"No enrollment record found for {student_name}."


@tool
def cancel_enrollment(student_name: str) -> str:
    """Cancel a student's course registration and remove them from the database."""
    result = db.execute(
        "DELETE FROM enrollments WHERE LOWER(student_name) = ?",
        (student_name.strip().lower(),),
    )
    db.commit()
    if result.rowcount == 0:
        return f"No active enrollment found for {student_name} to cancel."
    return f"Enrollment for {student_name} was canceled successfully."


@tool
def get_admission_criteria() -> str:
    """Get general university admission eligibility and deadlines."""
    return (
        "Admission Criteria:\n"
        "- Undergraduate: Minimum 60% in High School.\n"
        "- Bootcamps: Open enrollment, subject to specific prerequisites.\n"
        "- Fall Deadline: August 15th | Spring Deadline: December 10th."
    )


@tool
def get_institution_info() -> str:
    """Get campus office hours and contact details."""
    return (
        "Institution Info:\n"
        "- Admin Office Hours: Monday to Friday, 9:00 AM to 5:00 PM\n"
        "- Contact: admissions@ideouniversity.edu | +92-42-111-222-333\n"
        "- Location: Main Campus, Gulberg III, Lahore"
    )


TOOLS = [
    get_course_details,
    show_all_courses,
    enroll_student,
    find_enrollment,
    cancel_enrollment,
    get_admission_criteria,
    get_institution_info,
]

# ---------------------------------------------------------------------------
# 4. SYSTEM PROMPT
# ---------------------------------------------------------------------------
def build_system_prompt() -> str:
    current_date = datetime.now().strftime("%A, %B %d, %Y")
    return f"""
You are a friendly and professional AI Admissions Agent for an Educational Institution.
Today's date is: {current_date}. Always use this year for new enrollments.

You manage student inquiries and course enrollments using a SQLite database.

IMPORTANT RULES:
- ALWAYS use database tools when modifying enrollment information.
- Use `get_course_details` for tuition, duration, and prerequisites.
- Student names must be unique in the database.
- Do NOT just tell the user that you enrolled them. Actually call the `enroll_student` tool.
- Before cancelling an enrollment, confirm with the student first.
- After completing operations, give a short, friendly confirmation.
- Be concise and polite.
"""


# ---------------------------------------------------------------------------
# 5. AGENT
# ---------------------------------------------------------------------------
llm = ChatGoogleGenerativeAI(model=MODEL_NAME, temperature=0, google_api_key=API_KEY)

agent = create_agent(
    model=llm,
    tools=TOOLS,
    system_prompt=build_system_prompt(),
    checkpointer=MemorySaver(),
)


def extract_text(content) -> str:
    """Normalize a model message's content (str or list of blocks) into plain text."""
    if isinstance(content, str):
        return content
    parts = []
    for block in content:
        if isinstance(block, str):
            parts.append(block)
        elif isinstance(block, dict) and block.get("type", "text") == "text":
            parts.append(block.get("text", ""))
    return "".join(parts)


# ---------------------------------------------------------------------------
# 6. CHAT LOOP
# ---------------------------------------------------------------------------
def main() -> None:
    config = {"configurable": {"thread_id": f"student_inquiry_{uuid.uuid4().hex[:8]}"}}

    print("\n======================================")
    print("     AI UNIVERSITY ADMISSIONS BOT")
    print("======================================")
    print("Type 'exit' or 'quit' to stop.")

    while True:
        try:
            user_input = input("\nStudent: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nGoodbye! Best of luck with your studies.")
            break

        if user_input.lower() in ("exit", "quit"):
            print("\nGoodbye! Best of luck with your studies.")
            break
        if not user_input:
            continue

        try:
            response = agent.invoke(
                {"messages": [{"role": "user", "content": user_input}]},
                config=config,
            )
            print("\nAI:")
            print(extract_text(response["messages"][-1].content))
        except Exception as e:
            print("\nError:", e)


if __name__ == "__main__":
    main()
