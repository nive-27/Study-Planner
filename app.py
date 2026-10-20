
import json
from pathlib import Path
from datetime import datetime
import time
import sys
import streamlit as st

# ---------- CONFIGURATION ----------

st.set_page_config()
    
st.markdown("""
<style>
.stApp {
    background-color: #100D1C;
    color: #F5F0FF;
}

[data-testid="stSidebar"] {
    background-color: #1B1530;
}

h1, h2, h3 {
    color: #C7A7FF !important;
}

div[data-testid="stMetric"] {
    background-color: #211A38;
    padding: 20px;
    border-radius: 14px;
    border: 1px solid #49366F;
}

div[data-testid="stVerticalBlockBorderWrapper"] {
    border-color: #49366F;
    border-radius: 14px;
}

.stButton button {
    border-radius: 10px;
}

</style>
""", unsafe_allow_html=True)

page_title="Study Planner",
page_icon="📚",
layout="wide"


TASKS_FILE = Path(__file__).with_name("tasks.json")


# ---------- DATA STORAGE ----------

def load_tasks():
    if not TASKS_FILE.exists():
        return []

    try:
        with TASKS_FILE.open("r", encoding="utf-8") as file:
            tasks = json.load(file)

        if isinstance(tasks, list):
            return tasks

        st.error("Invalid task data in tasks.json.")
        return []

    except (json.JSONDecodeError, OSError):
        st.error("Could not read tasks.json. Check your saved file.")
        return []


def save_tasks(tasks):
    try:
        with TASKS_FILE.open("w", encoding="utf-8") as file:
            json.dump(tasks, file, indent=4)
    except OSError:
        st.error("Could not save tasks. Check file permissions.")

STUDY_LOG_FILE = Path(__file__).with_name("study_log.json")


def load_study_log():
    if not STUDY_LOG_FILE.exists():
        return []

    try:
        with STUDY_LOG_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)

        return data if isinstance(data, list) else []

    except (json.JSONDecodeError, OSError):
        st.error("Could not read study_log.json.")
        return []


def save_study_log(sessions):
    try:
        with STUDY_LOG_FILE.open("w", encoding="utf-8") as file:
            json.dump(sessions, file, indent=4)
    except OSError:
        st.error("Could not save study history.")



# ---------- INITIALIZE SESSION ----------

if "tasks" not in st.session_state:
    st.session_state.tasks = load_tasks()


# ---------- HEADER ----------

st.title("📚 Study Planner")
st.caption("Plan smarter. Study better.")

tasks = st.session_state.tasks


# ---------- ADD TASK ----------

st.sidebar.header("➕ Add a Task")

with st.sidebar.form("task_form"):
    title = st.text_input("Task name")

    subject = st.selectbox(
        "Subject",
        [
            "Python",
            "C Programming",
            "Mathematics",
            "Statistics",
            "English",
            "Other"
        ]
    )

    priority = st.selectbox(
        "Priority",
        ["High", "Medium", "Low"]
    )

    deadline = st.date_input("Deadline")

    submitted = st.form_submit_button("Add Task")

    if submitted:
        if title.strip():
            tasks.append({
                "title": title.strip(),
                "subject": subject,
                "priority": priority,
                "deadline": deadline.strftime("%d-%m-%Y"),
                "completed": False
            })

            save_tasks(tasks)
            st.success("Task added successfully!")
            st.rerun()
        else:
            st.warning("Please enter a task name.")


# ---------- DASHBOARD ----------

today = __import__("datetime").date.today()

completed = sum(
    1 for task in tasks if task.get("completed", False)
)

total = len(tasks)
pending = total - completed

overdue = 0

from datetime import datetime

for task in tasks:
    if not task.get("completed", False):
        try:
            due_date = datetime.strptime(
                task["deadline"], "%d-%m-%Y"
            ).date()

            if due_date < today:
                overdue += 1
        except (ValueError, KeyError):
            pass

st.subheader("📊 Your Dashboard")

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Tasks", total)
col2.metric("Completed", completed)
col3.metric("Pending", pending)
col4.metric("Overdue", overdue)

progress = completed / total if total else 0

st.progress(progress, text=f"Completion: {progress:.0%}")


# ---------- SEARCH AND FILTER ----------

st.divider()
st.subheader("📝 Your Tasks")

search = st.text_input("🔍 Search tasks by title")

status_filter = st.selectbox(
    "Filter tasks",
    ["All", "Pending", "Completed", "Overdue"]
)

priority_order = {"High": 1, "Medium": 2, "Low": 3}

visible_tasks = []

for i, task in enumerate(tasks):
    if search.lower() not in task.get("title", "").lower():
        continue

    is_completed = task.get("completed", False)

    try:
        due_date = datetime.strptime(
            task["deadline"], "%d-%m-%Y"
        ).date()
        is_overdue = due_date < today and not is_completed
    except (ValueError, KeyError):
        is_overdue = False

    if status_filter == "Pending" and is_completed:
        continue

    if status_filter == "Completed" and not is_completed:
        continue

    if status_filter == "Overdue" and not is_overdue:
        continue

    visible_tasks.append((i, task))

visible_tasks.sort(
    key=lambda item: priority_order.get(
        item[1].get("priority", "Medium"), 2
    )
)


# ---------- DISPLAY TASKS ----------

if not visible_tasks:
    st.info("No matching tasks. Add a task using the sidebar!")

for i, task in visible_tasks:
    is_completed = task.get("completed", False)

    with st.container(border=True):
        left, right = st.columns([4, 1])

        with left:
            st.markdown(f"### {task.get('title', 'Untitled')}")

            st.write(
                f"**Subject:** {task.get('subject', 'Other')}"
            )

            st.write(
                f"**Priority:** {task.get('priority', 'Medium')}"
            )

            st.write(
                f"**Deadline:** {task.get('deadline', 'Not set')}"
            )

            if is_completed:
                st.success("Completed ✅")
            elif is_overdue:
                st.error("Overdue 🔴")
            else:
                st.info("Pending 📌")

        with right:
            with st.expander("✏️ Edit task"):
                try:
                    current_deadline = datetime.strptime(
                        task.get("deadline", ""), "%d-%m-%Y"
                    ).date()
                except (ValueError, TypeError):
                    current_deadline = today

                with st.form(f"edit_task_form_{i}"):
                    edited_title = st.text_input(
                        "Task name",
                        value=task.get("title", ""),
                        key=f"edit_title_{i}"
                    )

                    subjects = [
                        "Python", "C Programming", "Mathematics",
                        "Statistics", "English", "Other"
                    ]
                    current_subject = task.get("subject", "Other")
                    subject_index = (
                        subjects.index(current_subject)
                        if current_subject in subjects else subjects.index("Other")
                    )
                    edited_subject = st.selectbox(
                        "Subject",
                        subjects,
                        index=subject_index,
                        key=f"edit_subject_{i}"
                    )

                    priorities = ["High", "Medium", "Low"]
                    current_priority = task.get("priority", "Medium")
                    priority_index = (
                        priorities.index(current_priority)
                        if current_priority in priorities else 1
                    )
                    edited_priority = st.selectbox(
                        "Priority",
                        priorities,
                        index=priority_index,
                        key=f"edit_priority_{i}"
                    )
                    edited_deadline = st.date_input(
                        "Deadline",
                        value=current_deadline,
                        key=f"edit_deadline_{i}"
                    )
                    edit_submitted = st.form_submit_button("Save changes")

                if edit_submitted:
                    if edited_title.strip():
                        task["title"] = edited_title.strip()
                        task["subject"] = edited_subject
                        task["priority"] = edited_priority
                        task["deadline"] = edited_deadline.strftime("%d-%m-%Y")
                        save_tasks(tasks)
                        st.success("Task updated successfully!")
                        st.rerun()
                    else:
                        st.warning("Task name cannot be empty.")

            new_status = st.checkbox(
                "Completed",
                value=is_completed,
                key=f"completed_{i}"
            )

            if new_status != is_completed:
                task["completed"] = new_status
                save_tasks(tasks)
                st.rerun()

            if st.button("🗑️ Delete", key=f"delete_{i}"):
                tasks.pop(i)
                save_tasks(tasks)
                st.rerun()

# ---------- STUDY TIME TRACKER ----------

if "study_sessions" not in st.session_state:
    st.session_state.study_sessions = load_study_log()

st.divider()
st.header("⏱️ Study Time Tracker")

with st.form("study_session_form"):
    study_subject = st.selectbox(
        "What did you study?",
        [
            "Python",
            "C Programming",
            "Mathematics",
            "Statistics",
            "English",
            "Other"
        ],
        key="study_subject"
    )

    study_minutes = st.number_input(
        "Minutes studied",
        min_value=1,
        max_value=1440,
        value=25,
        step=5
    )

    session_submitted = st.form_submit_button(
        "Save Study Session"
    )

    if session_submitted:
        session = {
            "subject": study_subject,
            "minutes": int(study_minutes),
            "date": datetime.now().strftime("%d-%m-%Y %H:%M")
        }

        st.session_state.study_sessions.append(session)
        save_study_log(st.session_state.study_sessions)
        st.success("Study session saved! 🎉")
        st.rerun()


# ---------- STUDY HISTORY ----------

sessions = st.session_state.study_sessions
total_minutes = sum(s["minutes"] for s in sessions)

st.subheader("📊 Study Statistics")
col1, col2 = st.columns(2)

col1.metric("Total Study Time", f"{total_minutes // 60}h {total_minutes % 60}m")
col2.metric("Sessions Completed", len(sessions))

if sessions:
    st.subheader("📚 Study History")

    for session in reversed(sessions):
        st.write(
            f"**{session['subject']}** — "
            f"{session['minutes']} minutes · {session['date']}"
        )

    subject_totals = {}

    for session in sessions:
        subject = session["subject"]
        subject_totals[subject] = (
            subject_totals.get(subject, 0) + session["minutes"]
        )

    st.subheader("Time by Subject")
    st.bar_chart(subject_totals)
else:
    st.info("Your study history will appear here after your first session.")

# ---------- WEEKLY STUDY ANALYTICS ----------

st.divider()
st.header("📈 Weekly Study Analytics")

from datetime import date, timedelta

sessions = st.session_state.study_sessions
today = date.today()
week_start = today - timedelta(days=6)

daily_minutes = {}
subject_minutes = {}

for i in range(7):
    day = week_start + timedelta(days=i)
    daily_minutes[day.strftime("%a, %d")] = 0

for session in sessions:
    try:
        session_date = datetime.strptime(
            session["date"], "%d-%m-%Y %H:%M"
        ).date()

        minutes = int(session["minutes"])
        subject = session.get("subject", "Other")

        if week_start <= session_date <= today:
            day_label = session_date.strftime("%a, %d")
            daily_minutes[day_label] += minutes

            subject_minutes[subject] = (
                subject_minutes.get(subject, 0) + minutes
            )

    except (ValueError, KeyError, TypeError):
        continue

weekly_total = sum(daily_minutes.values())

col1, col2 = st.columns(2)

with col1:
    st.metric(
        "Study Time — Last 7 Days",
        f"{weekly_total // 60}h {weekly_total % 60}m"
    )

with col2:
    study_days = sum(
        1 for minutes in daily_minutes.values() if minutes > 0
    )
    st.metric("Days Studied", f"{study_days}/7")

st.subheader("📅 Daily Study Time")
st.bar_chart(
    {
        "Study minutes": daily_minutes
    }
)

st.subheader("📚 Time by Subject")

if subject_minutes:
    st.bar_chart(subject_minutes)

    top_subject = max(
        subject_minutes, key=subject_minutes.get
    )

    st.success(
        f"Most-studied subject: {top_subject} "
        f"({subject_minutes[top_subject]} minutes)"
    )
else:
    st.info(
        "Complete a study session to see your weekly analytics!"
    )


# ---------- LIVE STUDY TIMER ----------

st.divider()
st.header("⏳ Focus Timer")

if "timer_running" not in st.session_state:
    st.session_state.timer_running = False
if "timer_paused" not in st.session_state:
    st.session_state.timer_paused = False
if "timer_end" not in st.session_state:
    st.session_state.timer_end = None
if "timer_remaining" not in st.session_state:
    st.session_state.timer_remaining = 0
if "timer_subject" not in st.session_state:
    st.session_state.timer_subject = "Python"
if "timer_duration" not in st.session_state:
    st.session_state.timer_duration = 25
if "timer_saved" not in st.session_state:
    st.session_state.timer_saved = False

timer_subject = st.selectbox(
    "Focus subject",
    ["Python", "C Programming", "Mathematics",
     "Statistics", "English", "Other"],
    key="live_timer_subject"
)

timer_minutes = st.number_input(
    "Timer length (minutes)",
    min_value=1,
    max_value=180,
    value=25,
    step=5,
    key="live_timer_minutes"
)

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("▶️ Start / Restart"):
        st.session_state.timer_subject = timer_subject
        st.session_state.timer_duration = int(timer_minutes)
        st.session_state.timer_remaining = int(timer_minutes) * 60
        st.session_state.timer_end = time.time() + int(timer_minutes) * 60
        st.session_state.timer_running = True
        st.session_state.timer_paused = False
        st.session_state.timer_saved = False
        st.rerun()

with col2:
    if st.button("⏸️ Pause"):
        if st.session_state.timer_running:
            st.session_state.timer_remaining = max(
                0, int(st.session_state.timer_end - time.time())
            )
            st.session_state.timer_running = False
            st.session_state.timer_paused = True
            st.rerun()

with col3:
    if st.button("⏹️ Stop"):
        st.session_state.timer_running = False
        st.session_state.timer_paused = False
        st.session_state.timer_end = None
        st.session_state.timer_remaining = 0
        st.session_state.timer_saved = False
        st.info("Timer stopped. Session not saved.")
        st.rerun()

if st.session_state.timer_paused:
    if st.button("▶️ Resume"):
        st.session_state.timer_end = (
            time.time() + st.session_state.timer_remaining
        )
        st.session_state.timer_running = True
        st.session_state.timer_paused = False
        st.rerun()

if st.session_state.timer_running:
    remaining = max(
        0, int(st.session_state.timer_end - time.time())
    )

    mins, secs = divmod(remaining, 60)
    st.subheader(f"⏱️ {mins:02d}:{secs:02d}")

    duration_seconds = st.session_state.timer_duration * 60
    progress = 1 - remaining / duration_seconds
    st.progress(min(1.0, max(0.0, progress)))

    if remaining <= 0:
        st.session_state.timer_running = False
        st.session_state.timer_paused = False

        if not st.session_state.timer_saved:
            session = {
                "subject": st.session_state.timer_subject,
                "minutes": st.session_state.timer_duration,
                "date": datetime.now().strftime("%d-%m-%Y %H:%M")
            }

            st.session_state.study_sessions.append(session)
            save_study_log(st.session_state.study_sessions)
            st.session_state.timer_saved = True

        st.success("🎉 Session complete! Study time saved.")
    else:
        time.sleep(1)
        st.rerun()

elif st.session_state.timer_paused:
    mins, secs = divmod(st.session_state.timer_remaining, 60)
    st.subheader(f"⏸️ Paused — {mins:02d}:{secs:02d}")


