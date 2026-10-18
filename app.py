import os
import re
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from groq import Groq, APIConnectionError, APIStatusError, AuthenticationError, RateLimitError

load_dotenv()

MODEL = "openai/gpt-oss-120b"
DATA_DIR = Path("data")
PLANS_DIR = DATA_DIR / "plans"
DATA_DIR.mkdir(exist_ok=True)
PLANS_DIR.mkdir(exist_ok=True)
EVENTS_FILE = DATA_DIR / "events.csv"
TASKS_FILE = DATA_DIR / "tasks.csv"

EVENT_COLUMNS = ["event_name", "date", "lead", "status", "notes"]
TASK_COLUMNS = ["task", "event_name", "assigned_to", "deadline", "status"]

st.set_page_config(page_title="COMSATS Wah Welfare AI Manager", page_icon="🤝", layout="wide")

SYSTEM_PROMPT = """You are a careful planning assistant for the Welfare Society of COMSATS University Islamabad, Wah Campus, Pakistan.
You create realistic DRAFT plans that a student society can actually follow.

Always structure your answer with exactly these markdown sections:
## 1. Objectives
## 2. Step-by-step Checklist
## 3. Roles and Responsibilities
## 4. Timeline (relative deadlines, e.g. "T-14 days")
## 5. Materials and Resources
## 6. Budget Categories (a markdown table: Category | What to estimate | Notes)
## 7. Safety, Ethics and Permissions
## 8. Risks and Backup Plan
## 9. Success Measurement

Rules:
- University context: permission/NOC from the relevant office or advisor, society rules, transport and attendance approvals.
- Do NOT invent confirmed bookings, approvals, prices, phone numbers or commitments. Label assumptions clearly.
- For money, list categories to estimate, not verified prices.
- For activities involving children, vulnerable people, blood donation, food or travel: include child protection / consent, photography consent, hygiene or medical safety, supervision ratios and official permission.
- End with: "This is a draft. A society member must review it before any action.\""""


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip().lower()).strip("-")
    return slug[:40] or "plan"


def load_csv(path: Path, columns: list) -> pd.DataFrame:
    """Load a CSV or create it with the given columns if missing/corrupt."""
    try:
        if path.exists():
            return pd.read_csv(path)
    except Exception:
        st.warning(f"Could not read {path.name}; starting with an empty table.")
    df = pd.DataFrame(columns=columns)
    df.to_csv(path, index=False)
    return df


def save_csv(df: pd.DataFrame, path: Path) -> None:
    df.to_csv(path, index=False)


def generate_plan(api_key: str, activity: str, goal: str, timeframe: str, budget: str) -> str:
    """Call Groq and return the plan text. Raises Groq exceptions on failure."""
    user_prompt = (
        f"Activity: {activity}\n"
        f"Goal/context: {goal or 'Not specified'}\n"
        f"Target timeframe: {timeframe or 'Not specified'}\n"
        f"Budget limit: {budget or 'Not specified'}\n"
    )
    client = Groq(api_key=api_key, timeout=45.0)
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
    )
    return response.choices[0].message.content


def save_plan_file(activity: str, plan: str) -> Path:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    path = PLANS_DIR / f"{stamp}_{slugify(activity)}.md"
    path.write_text(f"# {activity}\n\n{plan}\n", encoding="utf-8")
    return path


events = load_csv(EVENTS_FILE, EVENT_COLUMNS)
tasks = load_csv(TASKS_FILE, TASK_COLUMNS)

# ---------- Sidebar ----------
with st.sidebar:
    st.header("About")
    st.write(
        "A management dashboard for the COMSATS Wah Welfare Society with an AI assistant "
        "that drafts event plans."
    )
    st.markdown(
        "**How to use**\n"
        "1. Add events and tasks.\n"
        "2. Use *AI Event Planner* to draft a plan.\n"
        "3. Review, download, and add it to Events."
    )
    st.caption(f"AI model: {MODEL}")

st.title("🤝 COMSATS Wah Welfare AI Manager")
st.caption("A practical management dashboard with an AI event-planning assistant.")

tab_dashboard, tab_events, tab_tasks, tab_ai = st.tabs(
    ["Dashboard", "Events", "Tasks", "AI Event Planner"]
)

# ---------- Dashboard ----------
with tab_dashboard:
    c1, c2, c3, c4 = st.columns(4)
    completed = int((tasks["status"].astype(str).str.lower() == "completed").sum()) if len(tasks) else 0
    blocked = int((tasks["status"].astype(str).str.lower() == "blocked").sum()) if len(tasks) else 0
    c1.metric("Events tracked", len(events))
    c2.metric("Tasks tracked", len(tasks))
    c3.metric("Tasks completed", completed)
    c4.metric("Tasks blocked", blocked)
    if len(tasks):
        st.progress(completed / len(tasks), text=f"Task completion: {completed}/{len(tasks)}")
    st.subheader("Upcoming / active events")
    st.dataframe(events, use_container_width=True, hide_index=True)
    st.subheader("Current tasks")
    st.dataframe(tasks, use_container_width=True, hide_index=True)

# ---------- Events ----------
with tab_events:
    st.subheader("Add an event")
    with st.form("event_form", clear_on_submit=True):
        event_name = st.text_input("Event name", placeholder="e.g. Orphanage visit")
        event_date = st.date_input("Planned date")
        lead = st.text_input("Event lead / club")
        status = st.selectbox("Status", ["Planning", "Approved", "In progress", "Completed", "On hold"])
        notes = st.text_area("Notes")
        submitted = st.form_submit_button("Save event")
    if submitted:
        if not event_name.strip():
            st.error("Please enter an event name.")
        else:
            events.loc[len(events)] = [event_name.strip(), str(event_date), lead.strip(), status, notes.strip()]
            save_csv(events, EVENTS_FILE)
            st.success("Event saved.")
            st.rerun()

    st.subheader("Edit event records")
    if len(events):
        edited_events = st.data_editor(
            events, use_container_width=True, num_rows="dynamic", hide_index=True, key="events_editor"
        )
        if st.button("Save event edits"):
            save_csv(edited_events, EVENTS_FILE)
            st.success("Event changes saved.")
            st.rerun()

# ---------- Tasks ----------
with tab_tasks:
    st.subheader("Add a task")
    event_options = events["event_name"].dropna().astype(str).tolist() if len(events) else []
    with st.form("task_form", clear_on_submit=True):
        task_name = st.text_input("Task", placeholder="e.g. Confirm transport")
        linked_event = st.selectbox("Related event", ["General"] + event_options)
        assigned_to = st.text_input("Assigned to")
        deadline = st.date_input("Deadline")
        task_status = st.selectbox("Task status", ["Not started", "In progress", "Completed", "Blocked"])
        task_submitted = st.form_submit_button("Save task")
    if task_submitted:
        if not task_name.strip():
            st.error("Please enter a task.")
        else:
            tasks.loc[len(tasks)] = [task_name.strip(), linked_event, assigned_to.strip(), str(deadline), task_status]
            save_csv(tasks, TASKS_FILE)
            st.success("Task saved.")
            st.rerun()

    st.subheader("Edit task records")
    if len(tasks):
        edited_tasks = st.data_editor(
            tasks, use_container_width=True, num_rows="dynamic", hide_index=True, key="tasks_editor"
        )
        if st.button("Save task edits"):
            save_csv(edited_tasks, TASKS_FILE)
            st.success("Task changes saved.")
            st.rerun()

# ---------- AI Event Planner ----------
with tab_ai:
    st.subheader("Generate an event plan")
    st.write("Describe an approved or proposed activity. The AI will suggest a draft plan for your team to review.")
    event_type = st.text_input("Activity", placeholder="e.g. Visit to a local orphanage")
    event_goal = st.text_area("Goal and context", placeholder="Purpose, expected participants, location constraints...")
    event_date_text = st.text_input("Target date or timeframe", placeholder="e.g. second-last week of October")
    budget = st.text_input("Budget limit (optional)", placeholder="e.g. PKR 15,000 or not decided")

    if st.button("Generate draft plan", type="primary"):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            st.error("GROQ_API_KEY is missing. Add it to your .env file and restart the app.")
        elif not event_type.strip():
            st.error("Enter an activity first.")
        else:
            try:
                with st.spinner("Creating a draft plan..."):
                    plan = generate_plan(api_key, event_type.strip(), event_goal.strip(),
                                         event_date_text.strip(), budget.strip())
                saved_path = save_plan_file(event_type.strip(), plan)
                # Keep in session_state so it survives reruns (download/add buttons)
                st.session_state["current_plan"] = {
                    "activity": event_type.strip(),
                    "timeframe": event_date_text.strip(),
                    "text": plan,
                    "file": saved_path.name,
                }
            except AuthenticationError:
                st.error("Your Groq API key is invalid. Check the key in your .env file.")
            except RateLimitError:
                st.error("Groq rate limit reached. Please wait a minute and try again.")
            except APIConnectionError:
                st.error("Could not reach Groq. Check your internet connection.")
            except APIStatusError as exc:
                st.error(f"AI service returned an error (status {exc.status_code}). Please try again.")
            except Exception as exc:
                st.error(f"Unexpected error: {exc}")

    current = st.session_state.get("current_plan")
    if current:
        st.divider()
        st.markdown(current["text"])
        st.info("AI output is a draft. Confirm permissions, safeguarding, dates, and costs with society leadership.")
        col_a, col_b = st.columns(2)
        col_a.download_button(
            "⬇️ Download plan (.md)",
            data=f"# {current['activity']}\n\n{current['text']}\n",
            file_name=current["file"],
            mime="text/markdown",
        )
        if col_b.button("➕ Add to Events as 'Planning'"):
            events.loc[len(events)] = [current["activity"], current["timeframe"] or "TBD", "", "Planning",
                                       "Draft AI plan generated; needs review."]
            save_csv(events, EVENTS_FILE)
            st.success("Added to Events.")

    # Saved plan history
    saved_plans = sorted(PLANS_DIR.glob("*.md"), reverse=True)
    if saved_plans:
        with st.expander(f"📁 Saved plans ({len(saved_plans)})"):
            choice = st.selectbox("Open a saved plan", saved_plans, format_func=lambda p: p.name)
            if choice:
                st.markdown(choice.read_text(encoding="utf-8"))

st.divider()
st.caption("Starter version: records are stored as local CSV files. Back up data regularly and do not store sensitive beneficiary information.")
