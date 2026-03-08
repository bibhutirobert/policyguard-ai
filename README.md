# 🛡️ PolicyGuard AI — v2.0
### Insurance Complaint Intelligence System

> A production-grade AI analytics platform that transforms raw customer
> complaints into structured operational intelligence — built for insurance
> operations and compliance teams.

---

## 📸 What It Does

Paste any customer complaint and PolicyGuard AI returns a full intelligence report in seconds:

| Field | Example |
|---|---|
| **Sentiment** | Very Negative |
| **Complaint Category** | Claim Delay |
| **Urgency Level** | High |
| **Escalation Risk** | High |
| **Risk Score** | 84 / 100 |
| **Key Issues** | Pending claim; No callback; Two months wait; Unresponsive team |
| **Recommended Response** | Escalate to claims processing manager immediately. Schedule priority callback within 4 hours and issue interim acknowledgement letter. |
| **Est. Resolution** | 3 business days |
| **AI Confidence** | 91% |

---

## ✨ Features

### 🔍 Complaint Analyser
- Single complaint analysis with full structured output
- Load random samples from the built-in dataset
- Colour-coded sentiment, urgency, and escalation badges
- Animated risk score gauge (0–100)
- Key issues pill tags
- Recommended response strategy block
- Raw JSON expander for developer inspection

### 📊 Analytics Dashboard (7 charts)
- Complaint category distribution — horizontal bar
- Sentiment distribution — donut chart
- Urgency level breakdown — vertical bar
- Risk score histogram
- Escalation risk breakdown — pie chart
- Average risk score by category — heat-scaled bar
- Risk score trend over time — area line chart

### 📋 Complaint Log
- Full filter bar: category, urgency, sentiment, escalation, risk score range
- Sortable data table (highest risk first)
- Separate filtered and full CSV exports
- Top 5 Escalation Risk spotlight cards

### 🚀 Batch Processing
- Upload any CSV with a `complaint_text` column
- Real-time progress bar per complaint
- Automatic policy type extraction from CSV if column present
- Results appended to session log

### 💾 Data Persistence
- Save log to `complaints_log.csv` (appends across sessions)
- Reload previous session data from sidebar
- Schema migration — handles column additions gracefully

---

## 🏗️ Architecture

```
policyguard-ai/
├── app.py                      # Streamlit UI — page layout & interactions only
├── requirements.txt
├── README.md
├── sample_complaints.csv       # 25 labelled insurance complaints
├── complaints_log.csv          # Auto-created on first save
│
└── utils/
    ├── __init__.py             # Clean flat public API for the package
    ├── config.py               # ALL constants, enums, colours, AI prompt
    ├── analysis.py             # OpenAI API — calls, parsing, retry logic
    ├── data_manager.py         # DataFrame I/O, KPIs, filtering, persistence
    └── visualization.py        # Plotly chart builders + HTML component helpers
```

### Why this structure?

| Module | Responsibility | Benefit |
|---|---|---|
| `config.py` | Single source of truth for all constants | Change a label or colour in one place |
| `analysis.py` | All OpenAI logic isolated | Swap models or mock in tests without touching UI |
| `data_manager.py` | All pandas operations | DataFrame schema enforced in one place |
| `visualization.py` | Pure chart functions: DataFrame → Figure | Independently testable, reusable |
| `app.py` | Streamlit structure & user events only | Thin, readable, easy to extend |

---

## 🛠️ Tech Stack

| Layer | Technology | Version |
|---|---|---|
| Frontend | Streamlit | ≥ 1.32 |
| AI Engine | OpenAI GPT-3.5-turbo | via openai ≥ 1.12 |
| Charts | Plotly | ≥ 5.18 |
| Data | Pandas | ≥ 2.0 |
| Config | python-dotenv | ≥ 1.0 |
| Language | Python | 3.9+ |

---

## ⚙️ Installation

### 1. Clone or download the project

```bash
git clone https://github.com/yourname/policyguard-ai.git
cd policyguard-ai
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv

# macOS / Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure your OpenAI API key

**Option A — `.env` file (recommended for local dev):**

```bash
echo "OPENAI_API_KEY=sk-your-key-here" > .env
```

**Option B — Sidebar input (no file needed):**
Paste your key into the sidebar field when the app loads.

**Option C — Shell environment variable:**

```bash
# macOS / Linux
export OPENAI_API_KEY=sk-your-key-here

# Windows PowerShell
$env:OPENAI_API_KEY="sk-your-key-here"
```

> Get your key at [platform.openai.com/api-keys](https://platform.openai.com/api-keys).
> GPT-3.5-turbo access on a free-tier account is sufficient.

---

## ▶️ Running the App

```bash
streamlit run app.py
```

Opens automatically at **http://localhost:8501**

---

## 🧪 5-Minute Demo

1. `streamlit run app.py`
2. Enter API key in sidebar (or use `.env`)
3. Click **📂 Load Sample** → a real complaint appears
4. Click **⚡ Analyse** → full AI report renders on the right
5. Repeat 5–6 times to populate the dashboard
6. Switch to **📈 Analytics Dashboard** — all 7 charts update live
7. Switch to **📋 Complaint Log** — filter, export, view Top 5 risks
8. Click **💾 Save Log to CSV** in sidebar to persist results

---

## 📁 Sample Dataset

`sample_complaints.csv` — 25 real-world style complaints across 5 policy types:

| Type | Topics |
|---|---|
| Health | Cashless denial, TPA rejection, maternity clause, claim delay |
| Life | Death claim delay, mis-selling, nominee update failure |
| Motor | Workshop delay, total loss dispute, NCD certificate |
| Property | Burglary claim, flood damage undervaluation |
| Travel | Flight cancellation rejection |

**Schema:** `id, complaint_text, date_submitted, policy_type`

---

## 🔐 Security Practices

- API key is **never hardcoded** anywhere in the codebase
- Key is read exclusively from environment variable `OPENAI_API_KEY`
- Sidebar key input uses Streamlit's `type="password"` — masked in UI
- Key is stored only in process memory for the session duration
- `.env` file should be added to `.gitignore` before committing

```bash
echo ".env" >> .gitignore
echo "complaints_log.csv" >> .gitignore
```

---

## 📊 Risk Score Reference

| Score | Level | Action |
|---|---|---|
| 1–30 | 🟢 Low | Standard SLA; no escalation |
| 31–60 | 🟡 Medium | Supervisor review within 3 days |
| 61–85 | 🟠 High | Prompt action; possible regulatory exposure |
| 86–100 | 🔴 Critical | Immediate escalation; churn / litigation risk |

---

## 🔧 Customisation

### Switch to GPT-4 for higher accuracy

In `utils/config.py`:

```python
OPENAI_MODEL = "gpt-4"        # was "gpt-3.5-turbo"
OPENAI_MAX_TOKENS = 800       # GPT-4 may need more tokens
```

### Add a new complaint category

In `utils/config.py`, add to `CATEGORY_OPTIONS` and update `ANALYSIS_SYSTEM_PROMPT` to include the new value in the allowed list.

### Change the colour palette

All colours are centralised in `utils/config.py` under `SENTIMENT_COLOURS`, `URGENCY_COLOURS`, and `ESCALATION_COLOURS`.

---

## 🚀 Roadmap

- [ ] PostgreSQL persistence — cross-session complaint history
- [ ] Role-based access — analyst vs manager views
- [ ] Slack / email alerts — auto-notify on Critical risk score
- [ ] SLA tracker — flag complaints approaching deadline
- [ ] Trend analysis — week-over-week complaint volume & sentiment
- [ ] Multi-language support — analyse complaints in regional languages
- [ ] FastAPI backend — decouple AI engine as a standalone microservice
- [ ] PDF report export — one-click dashboard summary
- [ ] Fine-tuned model — train on resolved complaint history
- [ ] Agent notes — allow ops team to annotate each complaint record

---

## 🤝 Contributing

1. Fork the repo
2. Create a feature branch: `git checkout -b feature/my-improvement`
3. Commit your changes: `git commit -m "Add: my improvement"`
4. Push and open a Pull Request

---

## 📄 Licence

MIT — free to use, modify, and distribute.

---

*PolicyGuard AI — turning customer complaints into operational clarity.*
