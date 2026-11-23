import logging
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
from backend.services.ai_service import ai_service

from backend.config import REPORTS_DIR
from backend.database.db import (
    get_run,
    update_run_status,
    update_run_mode,
    update_agent_status,
    save_report
)
from backend.agents.requirement_agent import RequirementAnalysisAgent
from backend.agents.scenario_agent import TestScenarioGenerationAgent
from backend.agents.testcase_agent import TestCaseDesignAgent
from backend.agents.automation_agent import TestAutomationAgent
from backend.agents.execution_agent import TestExecutionAgent

logger = logging.getLogger("testing_platform.orchestrator")

class OrchestrationAgent:
    """
    AGENT 6: ORCHESTRATION AND REPORTING AGENT
    Responsibilities:
    1. Coordinate all six agents in workflow sequence for both AI and Basic Testing Mode.
    2. Pass structured JSON outputs from each agent to the next.
    3. Track real-time execution status of each agent.
    4. Handle API errors (quota/invalid keys) by explaining the error and offering/engaging Basic Mode.
    5. Consolidate actual test execution results from pytest.
    6. Generate comprehensive HTML and JSON test reports with clear mode differentiation.
    7. Update workflow state and testing run records.
    """
    def __init__(self, run_id: str):
        self.run_id = run_id
        self.agent_name = "orchestrator_agent"

    def run_workflow(
        self,
        website_url: str = "",
        manual_requirements: str = "",
        jira_project: str = "",
        jira_issue_id: str = "",
        automation_framework: str = "playwright",
        generation_mode: str = "basic",
        ai_model: Optional[str] = None,
        alternative_models: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        logger.info(
            f"[{self.run_id}] Orchestrator starting workflow with {automation_framework.upper()} "
            f"(Mode: {generation_mode.upper()}, Model: {ai_model or 'default'}, Alternatives: {alternative_models or []})..."
        )
        update_run_status(self.run_id, "RUNNING")
        update_agent_status(self.run_id, self.agent_name, "RUNNING")

        current_stage = "Initialization"
        requirements = []
        scenarios = []
        test_cases = []
        automation_scripts = []
        execution_results = []
        actual_model_used = ai_model or ""
        total_orchestrator_retries = 0

        try:
            # -------------------------------------------------------------
            # STAGE 1: Requirement Analysis Agent
            # -------------------------------------------------------------
            current_stage = "Requirement Analysis"
            req_agent = RequirementAnalysisAgent(self.run_id)
            requirements, actual_mode, fallback_reason = req_agent.execute(
                website_url=website_url,
                manual_requirements=manual_requirements,
                jira_project=jira_project,
                jira_issue_id=jira_issue_id,
                generation_mode=generation_mode,
                ai_model=ai_model,
                alternative_models=alternative_models
            )

            meta1 = ai_service.last_execution_metadata or {}
            if meta1.get("actual_model"):
                actual_model_used = meta1.get("actual_model")
            total_orchestrator_retries += meta1.get("retries_count", 0)

            # Update run mode in case actual model or provider adjusted
            update_run_mode(
                self.run_id,
                actual_mode,
                fallback_reason or "",
                ai_provider=actual_mode,
                ai_model=actual_model_used
            )

            # -------------------------------------------------------------
            # STAGE 2: Test Scenario Generation Agent
            # -------------------------------------------------------------
            current_stage = "Scenario Generation"
            sc_agent = TestScenarioGenerationAgent(self.run_id)
            scenarios = sc_agent.execute(
                requirements,
                generation_mode=actual_mode,
                ai_model=actual_model_used,
                alternative_models=alternative_models
            )

            meta2 = ai_service.last_execution_metadata or {}
            if meta2.get("actual_model"):
                actual_model_used = meta2.get("actual_model")
            total_orchestrator_retries += meta2.get("retries_count", 0)

            # -------------------------------------------------------------
            # STAGE 3: Test Case Design Agent
            # -------------------------------------------------------------
            current_stage = "Test Case Design"
            tc_agent = TestCaseDesignAgent(self.run_id, framework=automation_framework)
            test_cases = tc_agent.execute(
                scenarios,
                generation_mode=actual_mode,
                ai_model=actual_model_used,
                alternative_models=alternative_models
            )

            meta3 = ai_service.last_execution_metadata or {}
            if meta3.get("actual_model"):
                actual_model_used = meta3.get("actual_model")
            total_orchestrator_retries += meta3.get("retries_count", 0)

            # -------------------------------------------------------------
            # STAGE 4: Test Automation Agent (Playwright or Selenium)
            # -------------------------------------------------------------
            current_stage = "Test Automation"
            auto_agent = TestAutomationAgent(self.run_id, framework=automation_framework)
            automation_scripts = auto_agent.execute(
                test_cases,
                target_url=website_url,
                generation_mode=actual_mode,
                ai_model=actual_model_used,
                alternative_models=alternative_models
            )

            # -------------------------------------------------------------
            # STAGE 5: Test Execution and Validation Agent
            # -------------------------------------------------------------
            current_stage = "Test Execution"
            exec_agent = TestExecutionAgent(self.run_id, framework=automation_framework)
            execution_results = exec_agent.execute(
                automation_scripts,
                generation_mode=actual_mode,
                ai_model=actual_model_used,
                alternative_models=alternative_models
            )

            # -------------------------------------------------------------
            # STAGE 6: Reporting and Consolidation
            # -------------------------------------------------------------
            current_stage = "Reporting & Analytics"
            total_tests = len(execution_results)
            passed_tests = sum(1 for r in execution_results if r.get("status") == "Passed")
            failed_tests = sum(1 for r in execution_results if r.get("status") == "Failed")
            skipped_tests = sum(1 for r in execution_results if r.get("status") == "Skipped")
            pass_percentage = round((passed_tests / total_tests * 100), 1) if total_tests > 0 else 0.0

            if actual_mode == "gemini":
                mode_label = f"Google Gemini API Mode ({actual_model_used})" if actual_model_used else "Google Gemini API Mode"
            elif actual_mode == "openai":
                mode_label = f"OpenAI API Mode ({actual_model_used})" if actual_model_used else "OpenAI API Mode"
            else:
                mode_label = "Basic Testing Mode (Deterministic & Page Inspection Engine)"

            summary_text = (
                f"Multi-agent testing workflow completed in {mode_label} using {automation_framework.upper()}. "
                f"Executed {total_tests} actual test cases ({passed_tests} Passed, {failed_tests} Failed, {skipped_tests} Skipped) "
                f"with an overall pass rate of {pass_percentage}%."
            )
            if fallback_reason:
                summary_text += f" [Mode Notice: {fallback_reason}]"

            # Optional AI Executive Report synthesis via Gemini
            ai_quality_report = None
            if actual_mode == "gemini" and actual_model_used:
                try:
                    rep_data, rep_meta = ai_service.generate_quality_report(
                        metrics={
                            "total_requirements": len(requirements),
                            "total_scenarios": len(scenarios),
                            "total_tests": total_tests,
                            "passed_tests": passed_tests,
                            "failed_tests": failed_tests,
                            "pass_percentage": pass_percentage
                        },
                        execution_results=execution_results,
                        mode=actual_mode,
                        model_name=actual_model_used,
                        alternative_models=alternative_models,
                        run_id=self.run_id
                    )
                    if rep_data:
                        ai_quality_report = rep_data
                        if rep_data.get("executive_summary"):
                            summary_text += f"\n\nExecutive Assessment: {rep_data['executive_summary']}"
                except Exception as rep_err:
                    logger.warning(f"[{self.run_id}] Stage 6: AI quality report synthesis warning: {rep_err}")

            recommendations = self._generate_recommendations(failed_tests, pass_percentage, automation_framework, actual_mode)
            if ai_quality_report and ai_quality_report.get("actionable_recommendations"):
                recommendations.extend(ai_quality_report["actionable_recommendations"])

            report_data = {
                "run_id": self.run_id,
                "timestamp": datetime.now().isoformat(),
                "website_url": website_url,
                "jira_project": jira_project,
                "jira_issue_id": jira_issue_id,
                "automation_framework": automation_framework,
                "generation_mode": actual_mode,
                "ai_provider": actual_mode,
                "ai_model": actual_model_used,
                "selected_model": ai_model or "",
                "actual_model": actual_model_used,
                "mode_label": mode_label,
                "mode_fallback_reason": fallback_reason,
                "metrics": {
                    "total_requirements": len(requirements),
                    "total_scenarios": len(scenarios),
                    "total_tests": total_tests,
                    "passed_tests": passed_tests,
                    "failed_tests": failed_tests,
                    "skipped_tests": skipped_tests,
                    "pass_percentage": pass_percentage
                },
                "summary": summary_text,
                "recommendations": recommendations,
                "ai_quality_report": ai_quality_report,
                "requirements": requirements,
                "scenarios": scenarios,
                "test_cases": test_cases,
                "execution_results": execution_results
            }

            # Generate HTML report
            html_report_path = self._generate_html_report(report_data)

            # Save report in DB
            save_report(self.run_id, report_data, str(html_report_path))

            # Finalize run status
            update_run_status(
                run_id=self.run_id,
                status="COMPLETED",
                summary=summary_text,
                total=total_tests,
                passed=passed_tests,
                failed=failed_tests,
                skipped=skipped_tests,
                pass_pct=pass_percentage,
                actual_model=actual_model_used,
                retries_count=total_orchestrator_retries
            )
            update_agent_status(
                self.run_id,
                self.agent_name,
                "COMPLETED",
                output_data=report_data,
                retries_count=total_orchestrator_retries,
                selected_model=ai_model or "",
                actual_model=actual_model_used
            )

            logger.info(f"[{self.run_id}] Workflow completed successfully in {actual_mode.upper()} mode.")
            return report_data

        except Exception as e:
            err_msg = f"Orchestrator failed during {current_stage}: {str(e)}"
            error_cat = getattr(e, "error_category", "ExecutionError")
            logger.error(f"[{self.run_id}] {err_msg}")
            
            # Isolate failure: Record run status as FAILED while preserving previously saved outputs
            update_run_status(
                run_id=self.run_id,
                status="FAILED",
                error_message=err_msg,
                total=len(execution_results),
                passed=sum(1 for r in execution_results if r.get("status") == "Passed"),
                failed=sum(1 for r in execution_results if r.get("status") == "Failed"),
                skipped=sum(1 for r in execution_results if r.get("status") == "Skipped"),
                pass_pct=0.0,
                actual_model=actual_model_used,
                retries_count=total_orchestrator_retries
            )
            update_agent_status(
                self.run_id,
                self.agent_name,
                "FAILED",
                error_message=err_msg,
                retries_count=total_orchestrator_retries,
                selected_model=ai_model or "",
                actual_model=actual_model_used,
                error_category=error_cat
            )
            raise RuntimeError(err_msg)

    def _execute_with_retry(self, fn, stage_name: str, max_retries: int = 2):
        last_error = None
        for attempt in range(max_retries + 1):
            try:
                return fn()
            except Exception as e:
                last_error = e
                logger.warning(f"[{self.run_id}] {stage_name} attempt {attempt + 1} failed: {e}")
        raise last_error

    def _generate_recommendations(self, failed_count: int, pass_pct: float, framework: str, mode: str) -> list[str]:
        recs = []
        if failed_count == 0:
            recs.append("All automated tests passed successfully. The web build is stable for QA sign-off.")
            recs.append(f"Consider integrating {framework.upper()} regression suite into CI/CD pipelines.")
        else:
            recs.append(f"{failed_count} tests failed. Review execution logs and failure screenshots for root cause.")
            recs.append("Verify network timeouts and ensure required elements are rendered before assertion.")
        if mode == "basic":
            recs.append("Basic Mode executed using live HTML inspection. Configure an OPENAI_API_KEY to unlock advanced AI-powered exploratory test design.")
        else:
            recs.append("AI-Powered Mode generated comprehensive scenario coverage across user journeys.")
        recs.append("Expand coverage to include mobile viewport testing and cross-browser suites.")
        return recs

    def _generate_html_report(self, report_data: Dict[str, Any]) -> Path:
        filename = f"report_{self.run_id}.html"
        out_path = REPORTS_DIR / filename

        metrics = report_data["metrics"]
        results = report_data.get("execution_results", [])
        mode = report_data.get("generation_mode", "ai")
        mode_badge_color = "#38bdf8" if mode == "ai" else "#f59e0b"
        mode_text = "AI-POWERED MODE" if mode == "ai" else "BASIC TESTING MODE (INSPECTED)"

        results_rows = "".join([
            f"""
            <tr style="border-bottom: 1px solid #1e293b;">
                <td style="padding: 12px; font-weight: 600; color: #38bdf8;">{r.get('case_id')}</td>
                <td style="padding: 12px; color: #f8fafc;">{r.get('title', 'N/A')}</td>
                <td style="padding: 12px;">
                    <span style="padding: 4px 10px; border-radius: 9999px; font-size: 12px; font-weight: 600; background: {'rgba(34, 197, 94, 0.2)' if r.get('status') == 'Passed' else 'rgba(239, 68, 68, 0.2)'}; color: {'#4ade80' if r.get('status') == 'Passed' else '#f87171'};">
                        {r.get('status')}
                    </span>
                </td>
                <td style="padding: 12px; color: #94a3b8;">{r.get('duration_sec', 0)}s</td>
                <td style="padding: 12px; color: #cbd5e1; font-size: 13px;">{r.get('actual_result', '')[:100]}</td>
            </tr>
            """ for r in results
        ])

        fallback_banner = ""
        if report_data.get("mode_fallback_reason"):
            fallback_banner = f"""
            <div style="background: rgba(245, 158, 11, 0.15); border: 1px solid #f59e0b; padding: 12px 16px; border-radius: 8px; margin-bottom: 20px; color: #fbbf24; font-size: 13px;">
                <strong>Mode Transition Notice:</strong> {report_data['mode_fallback_reason']}
            </div>
            """

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Multi-Agent Test Automation Report - {self.run_id}</title>
    <style>
        body {{
            background-color: #0b0f19;
            color: #e2e8f0;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            margin: 0;
            padding: 30px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        .header {{
            background: linear-gradient(135deg, #1e1b4b 0%, #0f172a 100%);
            border: 1px solid #312e81;
            padding: 24px;
            border-radius: 12px;
            margin-bottom: 24px;
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }}
        .card {{
            background-color: #111827;
            border: 1px solid #1f2937;
            border-radius: 10px;
            padding: 18px;
        }}
        .card h4 {{
            margin: 0 0 8px 0;
            color: #94a3b8;
            font-size: 13px;
            text-transform: uppercase;
        }}
        .card .val {{
            font-size: 28px;
            font-weight: bold;
            color: #f8fafc;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            background-color: #111827;
            border-radius: 10px;
            overflow: hidden;
            border: 1px solid #1f2937;
        }}
        th {{
            background-color: #1f2937;
            color: #94a3b8;
            text-align: left;
            padding: 12px;
            font-size: 13px;
        }}
        .badge {{
            display: inline-block;
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 11px;
            font-weight: bold;
            font-family: monospace;
        }}
        .btn-print {{
            background: #2563eb;
            color: white;
            border: none;
            padding: 10px 18px;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
            float: right;
        }}
        @media print {{
            .btn-print {{ display: none; }}
            body {{ background: white; color: black; }}
            .card, table, .header {{ background: #fff !important; border: 1px solid #ccc !important; color: #000 !important; }}
            th {{ background: #f0f0f0 !important; color: #000 !important; }}
            td {{ color: #000 !important; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <button class="btn-print" onclick="window.print()">Print / Save PDF</button>
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                <h1 style="margin: 0; color: #38bdf8;">TraceAI Studio — Test Automation Report</h1>
                <span class="badge" style="background: rgba(56, 189, 248, 0.15); color: {mode_badge_color}; border: 1px solid {mode_badge_color};">
                    {mode_text}
                </span>
            </div>
            <p style="margin: 0; color: #94a3b8;">
                Run ID: <strong>{self.run_id}</strong> | Generated: {report_data['timestamp']} | Framework: <strong style="color: #a855f7;">{report_data['automation_framework'].upper()}</strong>
            </p>
            <p style="margin: 8px 0 0 0; color: #cbd5e1;">Target URL: <a href="{report_data['website_url']}" style="color: #38bdf8;" target="_blank">{report_data['website_url'] or 'N/A'}</a></p>
        </div>

        {fallback_banner}

        <div class="grid">
            <div class="card">
                <h4>Total Test Cases</h4>
                <div class="val">{metrics['total_tests']}</div>
            </div>
            <div class="card">
                <h4>Passed Tests</h4>
                <div class="val" style="color: #4ade80;">{metrics['passed_tests']}</div>
            </div>
            <div class="card">
                <h4>Failed Tests</h4>
                <div class="val" style="color: #f87171;">{metrics['failed_tests']}</div>
            </div>
            <div class="card">
                <h4>Pass Rate</h4>
                <div class="val" style="color: #38bdf8;">{metrics['pass_percentage']}%</div>
            </div>
        </div>

        <div class="card" style="margin-bottom: 24px;">
            <h3 style="margin-top: 0; color: #f8fafc;">Executive Summary</h3>
            <p style="color: #cbd5e1; line-height: 1.6;">{report_data['summary']}</p>
            <h4 style="color: #94a3b8; margin-top: 16px;">Testing Insights &amp; Recommendations</h4>
            <ul>
                {"".join([f"<li style='color: #cbd5e1; margin-bottom: 6px;'>{rec}</li>" for rec in report_data.get('recommendations', [])])}
            </ul>
        </div>

        <h3 style="color: #f8fafc; margin-bottom: 12px;">Detailed Test Execution Results</h3>
        <table>
            <thead>
                <tr>
                    <th>Test Case ID</th>
                    <th>Test Title</th>
                    <th>Status</th>
                    <th>Duration</th>
                    <th>Actual Result</th>
                </tr>
            </thead>
            <tbody>
                {results_rows}
            </tbody>
        </table>
    </div>
</body>
</html>
"""
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        return out_path
