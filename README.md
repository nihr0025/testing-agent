# AI Multi-Agent Software Testing Automation Platform (TraceAI Studio)

> A modern, full-stack, AI-driven software testing automation platform powered by six collaborating specialized agents. Automate test discovery, design, script generation (Playwright & Selenium), execution, and reporting for websites, Jira user stories, or manual requirements.

---

## 🌟 Key Features

### 1. Dual Testing Intelligence Modes (AI-Powered vs. Basic Mode)
TraceAI Studio features two distinct, fully-functional operational modes:
- **🤖 AI-Powered Testing Mode**:
  - Leverages OpenAI (`gpt-4o-mini` or user-configured model) to perform exploratory discovery and synthesis of edge-case scenarios.
  - Automatically enabled when `OPENAI_API_KEY` is provided.
- **⚡ Basic Testing Mode (API-Independent)**:
  - **100% Free, Offline-Capable, and Token-Independent**.
  - Automatically offered when `OPENAI_API_KEY` is missing, invalid (401), or quota is exhausted (429).
  - **All six agents participate fully**:
    - **Agent 1**: Directly inspects accessible website information (HTML title, forms, inputs, buttons, and links).
    - **Agent 2**: Synthesizes Functional, Negative, and Navigation testing scenarios using predefined Python QA logic.
    - **Agent 3**: Creates structured test cases with preconditions and test data matching discovered controls.
    - **Agent 4**: Generates executable Playwright or Selenium scripts targeting real element locators.
    - **Agent 5**: Executes tests using `pytest` (genuine executions, no simulation).
    - **Agent 6**: Consolidates actual pytest results and formats executive reports.
  - Clearly distinguishes AI-generated results from template/inspection-generated results with distinct UI badges (`🤖 AI-Generated` vs `⚡ Basic Mode (Inspected)`).

### 2. Six Collaborating Specialized Agents
1. **Requirement Analysis Agent**: Analyzes web applications, inspects accessible DOM structures in Basic Mode, extracts Jira user stories via MCP, and decomposes requirements into acceptance criteria and testable conditions.
2. **Test Scenario Generation Agent**: Synthesizes Functional, Negative, Boundary, and Navigation scenarios with full requirement traceability.
3. **Test Case Design Agent**: Translates scenarios into detailed test cases with preconditions, test data, execution steps, and expected results.
4. **Test Automation Agent**: Dynamically generates readable, robust Python test automation scripts with reliable locators.
5. **Test Execution & Validation Agent**: Executes automation scripts via `pytest`, captures test durations, console errors, and failure screenshots.
6. **Orchestration & Reporting Agent**: Maintains state in SQLite, handles recoverable retries, consolidates test metrics, and exports reports.

### 3. Selectable Automation Framework
- Seamlessly switch between **Playwright** and **Selenium WebDriver** from the UI before running tests or via Settings.
- Automatically generates framework-specific Python code and locators.

### 4. Model Context Protocol (MCP) Jira Integration
- Independently configurable Atlassian Jira integration via MCP Server or direct Jira REST API to retrieve user stories, acceptance criteria, and project backlogs in both AI and Basic mode.

### 5. TraceAI Studio Dashboard
- Dark-navy theme styled with cyan, blue, and purple accents.
- Real-time Recharts visualizations: stacked execution status bar charts and requirement coverage donut charts.
- Interactive code inspector, live terminal logs, failure screenshot previewer, and downloadable HTML/PDF reports.

### 6. Built-in Demo Sandbox Target
- Ships with an embedded target web store at `/demo` for instant local testing without needing third-party internet access.

---

## 🏗️ Architecture

```
                  +----------------------------------------------+
                  |         TraceAI Studio (React 18 + Vite)     |
                  +----------------------------------------------+
                                         |  REST API & Polling
                                         v
                  +----------------------------------------------+
                  |           FastAPI Application Backend        |
                  +----------------------------------------------+
                                         |
     +-----------------------------------+-----------------------------------+
     |                                   |                                   |
     v                                   v                                   v
+------------------------+  +--------------------------+  +--------------------------+
|  SQLite Database       |  |  Jira MCP Client         |  |  Dual Intelligence Engine|
|  (State & Traceability)|  |  (Issues & User Stories) |  |  • AI Mode (OpenAI)      |
+------------------------+  +--------------------------+  |  • Basic Mode (Inspector)|
                                                          +--------------------------+
                                         |
                   +--------------------------------------------+
                   |          6-Agent Orchestration Engine      |
                   +--------------------------------------------+
                   | 1. Requirement Analysis Agent              |
                   | 2. Test Scenario Generation Agent          |
                   | 3. Test Case Design Agent                  |
                   | 4. Test Automation Agent (Playwright/Sel)  |
                   | 5. Test Execution & Validation Agent       |
                   | 6. Reporting & Consolidation Agent         |
                   +--------------------------------------------+
                                         |
                       +-----------------+-----------------+
                       |                                   |
                       v                                   v
             [ Playwright Engine ]               [ Selenium WebDriver ]
             - Chromium headless                 - Chrome WebDriver
             - Pytest test runner                - Pytest test runner
             - Failure screenshots               - Failure screenshots
```

---

## 🛠️ Technology Stack

- **Frontend**: React 18, Vite, Tailwind CSS, Lucide React icons, Recharts data visualization.
- **Backend**: Python 3.11+, FastAPI, Pydantic v2, SQLite3, Uvicorn.
- **AI Engine**: OpenAI API (`gpt-4o-mini`) with structured JSON schema outputs and resilient deterministic fallback.
- **Inspection Engine**: Python `html.parser` & `requests` for DOM element discovery.
- **Automation Engines**:
  - **Playwright**: `playwright` Python library + Chromium browser.
  - **Selenium**: `selenium` 4.x + Selenium Manager.
  - **Runner**: `pytest` for genuine test execution and validation.
- **Integration**: Model Context Protocol (MCP) Jira Client.

---

## 🚀 Getting Started

### 1. Prerequisites

- Python 3.11+
- Node.js 18+ (Node 20+ recommended)
- Google Chrome or Chromium installed

### 2. Backend Setup

1. Open your terminal in the project root:
   ```bash
   cd c:/Users/nihar/ideaprojects/testing-agents
   ```

2. Install Python dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```

3. Install Playwright browser binaries:
   ```bash
   python -m playwright install chromium
   ```

### 3. Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   npm install
   ```

2. Build the frontend assets:
   ```bash
   npm run build
   ```

---

## ⚙️ Configuration (.env)

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Edit `.env` to configure your API keys (optional):

```env
# OpenAI Configuration (Optional - Basic Mode works without API key)
OPENAI_API_KEY=sk-your-openai-api-key
OPENAI_MODEL=gpt-4o-mini

# Jira Configuration (Optional for Jira User Story Testing)
JIRA_URL=https://your-domain.atlassian.net
JIRA_EMAIL=qa-engineer@example.com
JIRA_API_TOKEN=your-jira-api-token

# Default Automation Framework (playwright or selenium)
DEFAULT_AUTOMATION_FRAMEWORK=playwright

# Server Settings
BACKEND_HOST=127.0.0.1
BACKEND_PORT=8000
FRONTEND_PORT=5173
```

> **Note**: If `OPENAI_API_KEY` is not provided, the platform automatically utilizes **Basic Testing Mode**. You can test websites immediately, and enter or verify your OpenAI API key anytime in the **Settings** page!

---

## ▶️ Running the Application

### Option A: All-in-One (FastAPI serves both Frontend & Backend)

The FastAPI backend automatically serves the compiled React dashboard at `http://127.0.0.1:8000`:

```bash
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

Open your browser at:
- **Dashboard**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Interactive Swagger Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Demo Test Application**: [http://127.0.0.1:8000/demo](http://127.0.0.1:8000/demo)

### Option B: Separate Frontend Development Server (with Hot Reloading)

1. Start FastAPI Backend in terminal 1:
   ```bash
   python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
   ```

2. Start Vite Dev Server in terminal 2:
   ```bash
   cd frontend
   npm run dev
   ```

Open your browser at: [http://localhost:5173](http://localhost:5173)

---

## 🧪 Example Workflow Walkthrough

1. Open the platform at [http://127.0.0.1:8000](http://127.0.0.1:8000).
2. Click **New Testing Run** in the sidebar or navbar.
3. Select your **Testing Intelligence Mode**:
   - `⚡ Basic Testing Mode (API-Independent)` or `🤖 AI-Powered Testing Mode`.
4. Select your preferred **Automation Framework**:
   - `Playwright` or `Selenium WebDriver`.
5. Enter target:
   - Click **"Use Built-In Demo Target"** to test `http://127.0.0.1:8000/demo`, or enter any public URL (e.g., `https://example.com`).
   - (Optional) Enter a Jira Issue key (e.g. `ECOM-101`) or manual requirements.
6. Click **"Start Multi-Agent Testing Run"**.
7. The app automatically redirects to the **Agent Workflow** page:
   - Watch Agent 1 inspect accessible website elements.
   - Watch Agent 2 synthesize Functional, Negative, and Navigation scenarios.
   - Watch Agent 3 design test cases.
   - Watch Agent 4 generate Playwright or Selenium scripts.
   - Watch Agent 5 execute tests with `pytest` and record logs.
   - Watch Agent 6 consolidate metrics and publish the report.
8. Click **"Inspect"** on any agent to inspect its structured JSON output.
9. Browse **Test Cases** to view the auto-generated automation Python scripts.
10. Open **Reports** to view the executive summary or click **Download HTML Report** / **Print / Save PDF**.

---

## ❓ Common Errors & Solutions

| Error | Cause | Solution |
|---|---|---|
| `OpenAI Authentication Error (401)` | API key is invalid or expired | The platform automatically transitions to Basic Testing Mode and runs the complete 6-agent suite. You can update your key in Settings. |
| `OpenAI Rate Limit / Quota Exceeded (429)` | Out of OpenAI credits | The platform automatically transitions to Basic Testing Mode with page inspection so your testing never fails. |
| `Playwright Host Not Found / Browser missing` | Playwright Chromium binaries not installed | Run `python -m playwright install chromium` |
| `Selenium WebDriver Exception / Session not created` | Chrome is not installed or version mismatch | Selenium 4.x uses Selenium Manager automatically. Ensure Google Chrome is installed on the host. |
| `SSRF Blocked: restricted cloud metadata endpoint` | Attempted to test `169.254.169.254` | Protected by default. Use public websites or `http://127.0.0.1:8000/demo`. |

---

## 📄 License

MIT License. Built with ❤️ for QA Engineers, Developers, and AI Enthusiasts.
