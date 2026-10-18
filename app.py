import os
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
EVENTS_FILE = DATA_DIR / "events.csv"
TASKS_FILE = DATA_DIR / "tasks.csv"

st.set_page_config(page_title="COMSATS Wah Welfare AI Manager", page_icon="🤝", layout="wide")

def load_csv(path, columns):
    if path.exists():
        return pd.read_csv(path)
    df = pd.DataFrame(columns=columns)
    df.to_csv(path, index=False)
    return df

def save_csv(df, path):
    df.to_csv(path, index=False)

events = load_csv(EVENTS_FILE, ["event_name", "date", "lead", "status", "notes"])
tasks = load_csv(TASKS_FILE, ["task", "event_name", "assigned_to", "deadline", "status"])

st.title("🤝 COMSATS Wah Welfare AI Manager")
st.caption("A practical management dashboard with an AI event-planning assistant.")

tab_dashboard, tab_events, tab_tasks, tab_ai = st.tabs(
    ["Dashboard", "Events", "Tasks", "AI Event Planner"]
)

with tab_dashboard:
    c1, c2, c3 = st.columns(3)
    c1.metric("Events tracked", len(events))
    c2.metric("Tasks tracked", len(tasks))
    if len(tasks) and "status" in tasks:
        completed = int((tasks["status"].astype(str).str.lower() == "completed").sum())
    else:
        completed = 0
    c3.metric("Tasks completed", completed)
    st.subheader("Upcoming / active events")
    st.dataframe(events, use_container_width=True, hide_index=True)
    st.subheader("Current tasks")
    st.dataframe(tasks, use_container_width=True, hide_index=True)

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
        edited_events = st.data_editor(events, use_container_width=True, num_rows="dynamic", hide_index=True, key="events_editor")
        if st.button("Save event edits"):
            save_csv(edited_events, EVENTS_FILE)
            st.success("Event changes saved.")
            st.rerun()

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
        edited_tasks = st.data_editor(tasks, use_container_width=True, num_rows="dynamic", hide_index=True, key="tasks_editor")
        if st.button("Save task edits"):
            save_csv(edited_tasks, TASKS_FILE)
            st.success("Task changes saved.")
            st.rerun()

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
            st.error("Add GROQ_API_KEY to your .env file (local run) or environment secrets before using AI.")
        elif not event_type.strip():
            st.error("Enter an activity first.")
        else:
            prompt = f"""
You are a practical planning assistant for COMSATS Wah Welfare Society in Pakistan.
Create a realistic, concise DRAFT plan for this activity.
Activity: {event_type}
Goal/context: {event_goal or "Not specified"}
Target timeframe: {event_date_text or "Not specified"}
Budget limit: {budget or "Not specified"}
Include: objectives, step-by-step checklist, suggested responsible roles, relative deadlines,
materials/resources, safety/permissions considerations, and a short success/impact measurement section.
Do not invent confirmed bookings, approvals, prices, or commitments. Label assumptions clearly.
For money, provide categories to estimate rather than pretending exact prices are verified.
Require a society member to review the plan before action.
"""
            try:
                client = Groq(api_key=api_key)
                with st.spinner("Creating a draft plan..."):
                    response = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[
                            {"role": "system", "content": "You create actionable, cautious plans for student welfare activities."},
                            {"role": "user", "content": prompt},
                        ],
                        temperature=0.3,
                    )
                st.markdown(response.choices[0].message.content)
                st.info("AI output is a draft. Confirm permissions, safeguarding, dates, and costs with society leadership.")
            except Exception as exc:
                st.error(f"AI request failed: {exc}")

st.divider()
st.caption("Starter version: records are stored as local CSV files. Back up data regularly and do not store sensitive beneficiary information.")
