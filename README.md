## 🤝 COMSATS Wah Welfare AI Manager
A management dashboard for the COMSATS Wah Welfare Society and its clubs, with an AI assistant that drafts event plans. Built with Streamlit and the Groq API.

<!-- Add screenshots to docs/ and uncomment: ![Dashboard](docs/dashboard.png) ![AI Event Planner](docs/ai-planner.png) -->
Features
Dashboard: live metrics, status charts, overdue tasks, next-30-days events, search, and a club filter.
Events and Tasks: add, edit and track activities; every task has one owner, one deadline and one status.
Team and Clubs: five proposed clubs with member records (role, skills, availability).
Budget: approved, received and spent amounts per activity, with remaining balance calculated automatically.
Impact Ledger: record real outcomes after each activity (problem addressed, volunteers, people reached, feedback, improvements).
AI Event Planner: generates a structured draft plan (objectives, checklist, roles, timeline, budget categories, safety and ethics, risks, success measures). Plans are saved and can be downloaded.
Optional password login and a branded theme.
Tech stack
Python, Streamlit, pandas, Groq API (llama-3.3-70b-versatile), python-dotenv. Data is stored in local CSV files.

Getting started
# 1. Clone and enter the project
git clone <your-repo-url>
cd comsats_welfare_ai_manager

# 2. (Recommended) create a virtual environment
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env      # Windows: copy .env.example .env
# edit .env and add your Groq API key (https://console.groq.com)

# 5. Run
streamlit run app.py
Environment variables
Variable	Required	Description
GROQ_API_KEY	Yes (for AI planner)	API key from the Groq Console
APP_PASSWORD	No	If set, the app asks for this password before opening
Project structure
comsats_welfare_ai_manager/
├── app.py                  # Streamlit app
├── requirements.txt
├── .env.example            # Template for secrets (copy to .env)
├── .gitignore
├── .streamlit/config.toml  # Theme colours
├── assets/logo.png         # Society logo
├── data/                   # Local CSV records (git-ignored)
└── docs/                   # Screenshots
Branding
Replace assets/logo.png with your logo, and edit SOCIETY_NAME, TAGLINE, CLUBS and CLUB_STYLE at the top of app.py.

# Privacy and responsible use
Records are stored locally in data/ and are not committed to Git.
Keep member records to names and roles; do not store phone numbers, CNICs or private beneficiary details.
Restrict finance records to authorized people and follow university policy.
AI output is a draft. A society member must review permissions, safeguarding, dates and costs before any action.
Get consent before sharing photos or personal details of children and beneficiaries.
# Roadmap
PDF / Word export of plans
Generate tasks automatically from an AI plan checklist
Role-based access for finance records
Move storage from CSV to a database
# License
Add a license of your choice (for example MIT) before making the repository public.
