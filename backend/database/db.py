import sqlite3
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from backend.config import DB_PATH

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS testing_runs (
        run_id TEXT PRIMARY KEY,
        created_at TEXT NOT NULL,
        status TEXT NOT NULL,
        website_url TEXT,
        jira_project TEXT,
        jira_issue_id TEXT,
        manual_requirements TEXT,
        automation_framework TEXT NOT NULL DEFAULT 'playwright',
        generation_mode TEXT NOT NULL DEFAULT 'ai',
        mode_reason TEXT DEFAULT '',
        total_tests INTEGER DEFAULT 0,
        passed_tests INTEGER DEFAULT 0,
        failed_tests INTEGER DEFAULT 0,
        skipped_tests INTEGER DEFAULT 0,
        pass_percentage REAL DEFAULT 0.0,
        summary TEXT,
        error_message TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS agent_states (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id TEXT NOT NULL,
        agent_name TEXT NOT NULL,
        display_name TEXT NOT NULL,
        step_order INTEGER NOT NULL,
        status TEXT NOT NULL, -- PENDING, RUNNING, COMPLETED, FAILED
        started_at TEXT,
        completed_at TEXT,
        output_json TEXT,
        error_message TEXT,
        UNIQUE(run_id, agent_name)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS requirements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id TEXT NOT NULL,
        req_id TEXT NOT NULL,
        description TEXT NOT NULL,
        acceptance_criteria TEXT,
        business_rules TEXT,
        testable_conditions TEXT,
        missing_information TEXT,
        priority TEXT DEFAULT 'Medium',
        generation_mode TEXT DEFAULT 'ai',
        source TEXT DEFAULT 'AI-Powered'
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS test_scenarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id TEXT NOT NULL,
        scenario_id TEXT NOT NULL,
        req_id TEXT NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        scenario_type TEXT NOT NULL, -- Functional, Negative, Boundary, Navigation, Integration
        priority TEXT DEFAULT 'Medium',
        expected_behavior TEXT,
        generation_mode TEXT DEFAULT 'ai',
        source TEXT DEFAULT 'AI-Powered'
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS test_cases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id TEXT NOT NULL,
        case_id TEXT NOT NULL,
        scenario_id TEXT NOT NULL,
        title TEXT NOT NULL,
        preconditions TEXT,
        test_data TEXT,
        execution_steps TEXT,
        expected_result TEXT NOT NULL,
        priority TEXT DEFAULT 'Medium',
        status TEXT DEFAULT 'Not Executed', -- Not Executed, Passed, Failed, Skipped
        framework TEXT DEFAULT 'playwright',
        script_path TEXT,
        code_snippet TEXT,
        generation_mode TEXT DEFAULT 'ai',
        source TEXT DEFAULT 'AI-Powered'
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS execution_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id TEXT NOT NULL,
        case_id TEXT NOT NULL,
        status TEXT NOT NULL, -- Passed, Failed, Skipped
        actual_result TEXT,
        expected_result TEXT,
        error_message TEXT,
        duration_sec REAL DEFAULT 0.0,
        screenshot_path TEXT,
        log_output TEXT,
        timestamp TEXT NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reports (
        run_id TEXT PRIMARY KEY,
        generated_at TEXT NOT NULL,
        summary_json TEXT NOT NULL,
        html_report_path TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS app_settings (
        setting_key TEXT PRIMARY KEY,
        setting_value TEXT NOT NULL
    )
    """)

    # Safe column migrations if database already existed
    migrations = [
        ("testing_runs", "generation_mode", "TEXT DEFAULT 'ai'"),
        ("testing_runs", "mode_reason", "TEXT DEFAULT ''"),
        ("requirements", "generation_mode", "TEXT DEFAULT 'ai'"),
        ("requirements", "source", "TEXT DEFAULT 'AI-Powered'"),
        ("test_scenarios", "generation_mode", "TEXT DEFAULT 'ai'"),
        ("test_scenarios", "source", "TEXT DEFAULT 'AI-Powered'"),
        ("test_cases", "generation_mode", "TEXT DEFAULT 'ai'"),
        ("test_cases", "source", "TEXT DEFAULT 'AI-Powered'"),
    ]
    for tbl, col, col_def in migrations:
        try:
            cursor.execute(f"ALTER TABLE {tbl} ADD COLUMN {col} {col_def}")
        except Exception:
            pass

    conn.commit()
    conn.close()

# Database helper functions

def create_testing_run(
    run_id: str,
    website_url: str,
    jira_project: str,
    jira_issue_id: str,
    manual_requirements: str,
    automation_framework: str = "playwright",
    generation_mode: str = "auto",
    mode_reason: str = ""
):
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    cursor.execute("""
        INSERT INTO testing_runs (
            run_id, created_at, status, website_url, jira_project,
            jira_issue_id, manual_requirements, automation_framework,
            generation_mode, mode_reason
        )
        VALUES (?, ?, 'PENDING', ?, ?, ?, ?, ?, ?, ?)
    """, (
        run_id, now, website_url, jira_project, jira_issue_id,
        manual_requirements, automation_framework, generation_mode, mode_reason
    ))

    # Initialize 6 agents
    agents = [
        ("requirement_agent", "Requirement Analysis Agent", 1),
        ("scenario_agent", "Test Scenario Generation Agent", 2),
        ("testcase_agent", "Test Case Design Agent", 3),
        ("automation_agent", "Test Automation Agent", 4),
        ("execution_agent", "Test Execution & Validation Agent", 5),
        ("orchestrator_agent", "Orchestration & Reporting Agent", 6),
    ]
    for agent_name, display_name, step_order in agents:
        cursor.execute("""
            INSERT INTO agent_states (run_id, agent_name, display_name, step_order, status)
            VALUES (?, ?, ?, ?, 'PENDING')
        """, (run_id, agent_name, display_name, step_order))

    conn.commit()
    conn.close()

def update_run_mode(run_id: str, generation_mode: str, mode_reason: str = ""):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE testing_runs
        SET generation_mode = ?, mode_reason = ?
        WHERE run_id = ?
    """, (generation_mode, mode_reason, run_id))
    conn.commit()
    conn.close()

def update_agent_status(run_id: str, agent_name: str, status: str,
                        output_data: Optional[Any] = None, error_message: Optional[str] = None):
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()

    output_json = json.dumps(output_data, default=str) if output_data is not None else None

    if status == "RUNNING":
        cursor.execute("""
            UPDATE agent_states
            SET status = ?, started_at = ?, error_message = NULL
            WHERE run_id = ? AND agent_name = ?
        """, (status, now, run_id, agent_name))
    elif status in ["COMPLETED", "FAILED"]:
        cursor.execute("""
            UPDATE agent_states
            SET status = ?, completed_at = ?, output_json = COALESCE(?, output_json), error_message = ?
            WHERE run_id = ? AND agent_name = ?
        """, (status, now, output_json, error_message, run_id, agent_name))

    conn.commit()
    conn.close()

def update_run_status(run_id: str, status: str, summary: Optional[str] = None,
                      error_message: Optional[str] = None,
                      total: int = 0, passed: int = 0, failed: int = 0, skipped: int = 0,
                      pass_pct: float = 0.0):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE testing_runs
        SET status = ?, summary = COALESCE(?, summary), error_message = ?,
            total_tests = ?, passed_tests = ?, failed_tests = ?, skipped_tests = ?,
            pass_percentage = ?
        WHERE run_id = ?
    """, (status, summary, error_message, total, passed, failed, skipped, pass_pct, run_id))
    conn.commit()
    conn.close()

def save_requirements(run_id: str, requirements: List[Dict[str, Any]], generation_mode: str = "ai"):
    conn = get_connection()
    cursor = conn.cursor()
    for req in requirements:
        cursor.execute("""
            INSERT INTO requirements (
                run_id, req_id, description, acceptance_criteria,
                business_rules, testable_conditions, missing_information, priority,
                generation_mode, source
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            run_id,
            req.get("req_id", "REQ-01"),
            req.get("description", ""),
            json.dumps(req.get("acceptance_criteria", [])),
            json.dumps(req.get("business_rules", [])),
            json.dumps(req.get("testable_conditions", [])),
            json.dumps(req.get("missing_information", [])),
            req.get("priority", "Medium"),
            req.get("generation_mode", generation_mode),
            req.get("source", "Basic Inspection Engine" if generation_mode == "basic" else "AI-Powered")
        ))
    conn.commit()
    conn.close()

def save_scenarios(run_id: str, scenarios: List[Dict[str, Any]], generation_mode: str = "ai"):
    conn = get_connection()
    cursor = conn.cursor()
    for sc in scenarios:
        cursor.execute("""
            INSERT INTO test_scenarios (
                run_id, scenario_id, req_id, title, description,
                scenario_type, priority, expected_behavior,
                generation_mode, source
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            run_id,
            sc.get("scenario_id", "SC-01"),
            sc.get("req_id", "REQ-01"),
            sc.get("title", ""),
            sc.get("description", ""),
            sc.get("scenario_type", "Functional"),
            sc.get("priority", "Medium"),
            sc.get("expected_behavior", ""),
            sc.get("generation_mode", generation_mode),
            sc.get("source", "Basic Scenario Engine" if generation_mode == "basic" else "AI-Powered")
        ))
    conn.commit()
    conn.close()

def save_test_cases(run_id: str, test_cases: List[Dict[str, Any]], framework: str = "playwright", generation_mode: str = "ai"):
    conn = get_connection()
    cursor = conn.cursor()
    for tc in test_cases:
        cursor.execute("""
            INSERT INTO test_cases (
                run_id, case_id, scenario_id, title, preconditions,
                test_data, execution_steps, expected_result, priority,
                status, framework, script_path, code_snippet,
                generation_mode, source
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'Not Executed', ?, ?, ?, ?, ?)
        """, (
            run_id,
            tc.get("case_id", "TC-01"),
            tc.get("scenario_id", "SC-01"),
            tc.get("title", ""),
            json.dumps(tc.get("preconditions", [])),
            json.dumps(tc.get("test_data", {})),
            json.dumps(tc.get("execution_steps", [])),
            tc.get("expected_result", ""),
            tc.get("priority", "Medium"),
            framework,
            tc.get("script_path", ""),
            tc.get("code_snippet", ""),
            tc.get("generation_mode", generation_mode),
            tc.get("source", "Basic Test Case Engine" if generation_mode == "basic" else "AI-Powered")
        ))
    conn.commit()
    conn.close()

def update_test_case_code(run_id: str, case_id: str, script_path: str, code_snippet: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE test_cases
        SET script_path = ?, code_snippet = ?
        WHERE run_id = ? AND case_id = ?
    """, (script_path, code_snippet, run_id, case_id))
    conn.commit()
    conn.close()

def save_execution_result(run_id: str, case_id: str, status: str, actual_result: str,
                          expected_result: str, error_message: str, duration_sec: float,
                          screenshot_path: str, log_output: str):
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    cursor.execute("""
        INSERT INTO execution_results (run_id, case_id, status, actual_result, expected_result,
                                       error_message, duration_sec, screenshot_path, log_output, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (run_id, case_id, status, actual_result, expected_result, error_message, duration_sec, screenshot_path, log_output, now))

    # Also update test_cases table status
    cursor.execute("""
        UPDATE test_cases SET status = ? WHERE run_id = ? AND case_id = ?
    """, (status, run_id, case_id))

    conn.commit()
    conn.close()

def save_report(run_id: str, summary_data: Dict[str, Any], html_path: str):
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    cursor.execute("""
        INSERT OR REPLACE INTO reports (run_id, generated_at, summary_json, html_report_path)
        VALUES (?, ?, ?, ?)
    """, (run_id, now, json.dumps(summary_data, default=str), html_path))
    conn.commit()
    conn.close()

def get_run(run_id: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM testing_runs WHERE run_id = ?", (run_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_all_runs(limit: int = 50) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM testing_runs ORDER BY created_at DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_agent_states(run_id: str) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM agent_states WHERE run_id = ? ORDER BY step_order ASC", (run_id,))
    rows = cursor.fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        if d.get("output_json"):
            try:
                d["output_data"] = json.loads(d["output_json"])
            except Exception:
                d["output_data"] = d["output_json"]
        else:
            d["output_data"] = None
        result.append(d)
    return result

def get_requirements(run_id: str) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM requirements WHERE run_id = ?", (run_id,))
    rows = cursor.fetchall()
    conn.close()
    res = []
    for r in rows:
        d = dict(r)
        for key in ["acceptance_criteria", "business_rules", "testable_conditions", "missing_information"]:
            if d.get(key):
                try:
                    d[key] = json.loads(d[key])
                except Exception:
                    pass
        res.append(d)
    return res

def get_scenarios(run_id: str) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM test_scenarios WHERE run_id = ?", (run_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_test_cases(run_id: str) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM test_cases WHERE run_id = ?", (run_id,))
    rows = cursor.fetchall()
    conn.close()
    res = []
    for r in rows:
        d = dict(r)
        for key in ["preconditions", "test_data", "execution_steps"]:
            if d.get(key):
                try:
                    d[key] = json.loads(d[key])
                except Exception:
                    pass
        res.append(d)
    return res

def get_execution_results(run_id: str) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM execution_results WHERE run_id = ? ORDER BY id ASC", (run_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_report(run_id: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM reports WHERE run_id = ?", (run_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    if d.get("summary_json"):
        try:
            d["summary"] = json.loads(d["summary_json"])
        except Exception:
            d["summary"] = d["summary_json"]
    return d

def get_dashboard_metrics() -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as total_runs FROM testing_runs")
    total_runs = cursor.fetchone()["total_runs"]

    cursor.execute("SELECT COUNT(*) as total_cases FROM test_cases")
    total_cases = cursor.fetchone()["total_cases"]

    cursor.execute("SELECT COUNT(*) as passed FROM test_cases WHERE status = 'Passed'")
    passed_cases = cursor.fetchone()["passed"]

    cursor.execute("SELECT COUNT(*) as failed FROM test_cases WHERE status = 'Failed'")
    failed_cases = cursor.fetchone()["failed"]

    cursor.execute("SELECT COUNT(*) as skipped FROM test_cases WHERE status = 'Skipped'")
    skipped_cases = cursor.fetchone()["skipped"]

    pass_pct = round((passed_cases / total_cases * 100), 1) if total_cases > 0 else 0.0

    cursor.execute("SELECT COUNT(*) as total_reqs FROM requirements")
    total_reqs = cursor.fetchone()["total_reqs"]

    cursor.execute("SELECT COUNT(DISTINCT req_id) as covered_reqs FROM test_scenarios")
    covered_reqs = cursor.fetchone()["covered_reqs"]

    cursor.execute("SELECT COUNT(*) as total_scenarios FROM test_scenarios")
    total_scenarios = cursor.fetchone()["total_scenarios"]

    conn.close()
    return {
        "total_runs": total_runs,
        "total_test_cases": total_cases,
        "passed_tests": passed_cases,
        "failed_tests": failed_cases,
        "skipped_tests": skipped_cases,
        "pass_percentage": pass_pct,
        "total_requirements": total_reqs,
        "covered_requirements": covered_reqs,
        "total_scenarios": total_scenarios
    }
