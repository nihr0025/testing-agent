import logging
import time
import subprocess
import os
import sys
import shutil
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime
from backend.config import REPORTS_DIR, SCREENSHOTS_DIR, BASE_DIR
from backend.database.db import save_execution_result, update_agent_status
from backend.services.ai_service import ai_service

logger = logging.getLogger("testing_platform.agent5_execution")

class TestExecutionAgent:
    """
    AGENT 5: TEST EXECUTION AND VALIDATION AGENT
    Responsibilities:
    1. Pre-validate Python, pytest, and browser automation environments.
    2. Receive automation scripts from Agent 4.
    3. Execute scripts using active sys.executable -m pytest runner.
    4. Capture test execution status (Passed, Failed, Skipped).
    5. Capture failure screenshots, execution logs, and browser errors.
    6. Record execution duration for each test.
    7. Save logs and screenshots in the reports directory.
    8. Return structured execution results without confusing infrastructure errors.
    """
    def __init__(self, run_id: str, framework: str = "playwright"):
        self.run_id = run_id
        self.framework = framework.lower()
        self.agent_name = "execution_agent"

    def _get_python_executable(self) -> str:
        """Finds and validates the active Python interpreter executable."""
        candidates = [
            sys.executable,
            shutil.which("python"),
            shutil.which("python3"),
            shutil.which("py")
        ]
        for c in candidates:
            if c and os.path.isfile(c) and os.access(c, os.X_OK):
                return os.path.abspath(c)
        if sys.executable and os.path.isfile(sys.executable):
            return os.path.abspath(sys.executable)
        raise FileNotFoundError(
            "Python executable not found. Unable to spawn test runner subprocess. "
            "Please ensure Python 3.10+ is installed and present in PATH."
        )

    def _validate_pytest_installed(self, python_exe: str) -> None:
        """Validates that pytest is installed in the active Python environment."""
        try:
            res = subprocess.run(
                [python_exe, "-m", "pytest", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if res.returncode != 0:
                raise RuntimeError(
                    f"pytest check returned non-zero code {res.returncode}: {res.stderr or res.stdout}"
                )
        except (subprocess.SubprocessError, FileNotFoundError, OSError) as e:
            raise RuntimeError(
                f"pytest is not installed or not functional in Python environment '{python_exe}'. "
                f"Install with: {python_exe} -m pip install pytest"
            ) from e

    def _validate_browser_environment(self) -> Tuple[bool, str]:
        """Pre-validates that browser automation engine (Playwright or Selenium) is ready."""
        if self.framework == "playwright":
            try:
                from playwright.sync_api import sync_playwright
                with sync_playwright() as p:
                    # Test launching headless chromium
                    browser = p.chromium.launch(headless=True)
                    browser.close()
                return True, "Playwright Chromium browser is verified and ready."
            except Exception as e:
                err_msg = str(e)
                fix_cmd = f"{sys.executable} -m playwright install chromium"
                return False, (
                    f"Playwright Chromium browser is not installed or cannot launch ({err_msg[:120]}). "
                    f"Run this command to install: {fix_cmd}"
                )

        elif self.framework == "selenium":
            try:
                import selenium
                # Verify Selenium Chrome options and NO_PROXY
                os.environ["NO_PROXY"] = "localhost,127.0.0.1,::1"
                os.environ["no_proxy"] = "localhost,127.0.0.1,::1"
                from selenium import webdriver
                from selenium.webdriver.chrome.options import Options
                opts = Options()
                opts.add_argument("--headless=new")
                opts.add_argument("--no-sandbox")
                opts.add_argument("--disable-dev-shm-usage")
                opts.add_argument("--remote-allow-origins=*")
                driver = webdriver.Chrome(options=opts)
                driver.quit()
                return True, "Selenium Chrome browser driver is verified and ready."
            except Exception as e:
                err_msg = str(e)
                return False, (
                    f"Selenium Chrome WebDriver could not be initialized ({err_msg[:120]}). "
                    f"Ensure Google Chrome is installed on the host system."
                )

        return True, "Browser environment check skipped."

    def execute(
        self,
        automation_scripts: List[Dict[str, Any]],
        generation_mode: str = "basic",
        ai_model: Optional[str] = None,
        alternative_models: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        logger.info(
            f"[{self.run_id}] Agent 5: Executing {len(automation_scripts)} {self.framework.upper()} tests "
            f"(Mode: {generation_mode.upper()}, Model: {ai_model or 'default'})..."
        )
        update_agent_status(self.run_id, self.agent_name, "RUNNING")

        try:
            if not automation_scripts:
                raise ValueError("No automation scripts provided to Test Execution Agent.")

            # Ensure output directories exist
            REPORTS_DIR.mkdir(parents=True, exist_ok=True)
            SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

            # 1. Validate Python executable
            python_exe = self._get_python_executable()
            logger.info(f"[{self.run_id}] Active Python runner: {python_exe}")

            # 2. Validate pytest is available
            self._validate_pytest_installed(python_exe)

            # 3. Pre-validate browser runtime
            browser_ok, browser_msg = self._validate_browser_environment()
            if not browser_ok:
                logger.error(f"[{self.run_id}] Browser environment error: {browser_msg}")
                raise RuntimeError(f"Browser environment check failed: {browser_msg}")

            # 4. Prepare execution environment variables
            exec_env = os.environ.copy()
            exec_env["NO_PROXY"] = "localhost,127.0.0.1,::1"
            exec_env["no_proxy"] = "localhost,127.0.0.1,::1"
            exec_env["PYTHONPATH"] = str(BASE_DIR) + os.pathsep + exec_env.get("PYTHONPATH", "")
            exec_env["PYTHONIOENCODING"] = "utf-8"

            results = []

            for script_item in automation_scripts:
                case_id = script_item.get("case_id", "TC-01")
                title = script_item.get("title", f"Test {case_id}")
                raw_script_path = script_item.get("script_path", "")

                start_time = time.time()
                status = "Passed"
                actual_result = f"Test {case_id} completed successfully."
                expected_result = "Page loaded, verified elements, and satisfied assertions."
                error_msg = None
                log_output = ""
                screenshot_rel_path = None

                script_path = Path(raw_script_path).resolve()

                if not script_path.exists() or not script_path.is_file():
                    status = "Failed"
                    error_msg = f"Automation script file does not exist on disk: {script_path}"
                    actual_result = error_msg
                    log_output = f"INFRASTRUCTURE ERROR: Script file not found: {script_path}"
                else:
                    cmd = [
                        python_exe,
                        "-m",
                        "pytest",
                        str(script_path),
                        "-v",
                        "--tb=short",
                        "--capture=no"
                    ]

                    working_dir = str(script_path.parent) if script_path.parent.exists() else str(BASE_DIR)

                    try:
                        proc = subprocess.run(
                            cmd,
                            capture_output=True,
                            text=True,
                            timeout=60,
                            cwd=working_dir,
                            env=exec_env
                        )

                        stdout = proc.stdout or ""
                        stderr = proc.stderr or ""
                        log_output = f"COMMAND: {' '.join(cmd)}\n\nSTDOUT:\n{stdout}\n\nSTDERR:\n{stderr}"

                        if proc.returncode == 0:
                            status = "Passed"
                            actual_result = f"Automated assertions passed for {case_id}."
                        else:
                            status = "Failed"
                            error_summary = stdout[-600:] if stdout else stderr[-600:]
                            error_msg = f"Pytest exit code {proc.returncode}.\n{error_summary}"
                            actual_result = f"Test assertion or browser navigation failed."

                            # Capture failure screenshot / diagnostic image
                            screenshot_name = f"fail_{self.run_id}_{case_id.lower().replace('-', '_')}.png"
                            screenshot_full = SCREENSHOTS_DIR / screenshot_name
                            self._generate_failure_screenshot(screenshot_full, case_id, title, error_msg)
                            screenshot_rel_path = f"/reports/screenshots/{screenshot_name}"

                    except subprocess.TimeoutExpired:
                        status = "Failed"
                        error_msg = f"Execution timed out after 60 seconds for {case_id}."
                        actual_result = "Test execution timeout."
                        log_output = f"TIMEOUT: Script {script_path} exceeded 60s execution limit."

                    except FileNotFoundError as fnf:
                        status = "Failed"
                        error_msg = f"Process spawning error: {str(fnf)}. Executable '{python_exe}' could not be started."
                        actual_result = f"Infrastructure failure: {str(fnf)}"
                        log_output = f"SPAWN_ERROR: {str(fnf)}"

                    except Exception as ex:
                        status = "Failed"
                        error_msg = f"Execution error ({type(ex).__name__}): {str(ex)}"
                        actual_result = f"Execution failure: {str(ex)}"
                        log_output = f"EXCEPTION: {str(ex)}"

                duration = round(time.time() - start_time, 2)

                # Persist to database
                save_execution_result(
                    run_id=self.run_id,
                    case_id=case_id,
                    status=status,
                    actual_result=actual_result,
                    expected_result=expected_result,
                    error_message=error_msg,
                    duration_sec=duration,
                    screenshot_path=screenshot_rel_path or "",
                    log_output=log_output
                )

                results.append({
                    "case_id": case_id,
                    "title": title,
                    "status": status,
                    "actual_result": actual_result,
                    "expected_result": expected_result,
                    "error_message": error_msg,
                    "duration_sec": duration,
                    "screenshot_path": screenshot_rel_path,
                    "log_output": log_output,
                    "timestamp": datetime.now().isoformat()
                })

            # AI-Powered Execution Triage & Flaky Test Prediction (in Gemini Mode)
            ai_insights = None
            selected_model = ai_model or ""
            actual_model = ai_model or ""
            retries_count = 0
            models_attempted = [ai_model] if ai_model else []

            if generation_mode == "gemini" and ai_model:
                try:
                    insights_data, meta = ai_service.analyze_execution(
                        execution_results=results,
                        framework=self.framework,
                        mode=generation_mode,
                        model_name=ai_model,
                        alternative_models=alternative_models,
                        run_id=self.run_id
                    )
                    if insights_data:
                        ai_insights = insights_data
                        if meta:
                            selected_model = meta.get("selected_model", selected_model)
                            actual_model = meta.get("actual_model", actual_model)
                            retries_count = meta.get("retries_count", 0)
                            models_attempted = meta.get("models_attempted", models_attempted)
                except Exception as ex:
                    logger.warning(f"[{self.run_id}] Agent 5: AI execution triage warning: {ex}")

            output_payload = {
                "results": results,
                "ai_insights": ai_insights,
                "total_executed": len(results),
                "passed": sum(1 for r in results if r.get("status") == "Passed"),
                "failed": sum(1 for r in results if r.get("status") == "Failed"),
                "skipped": sum(1 for r in results if r.get("status") == "Skipped"),
                "selected_model": selected_model,
                "actual_model": actual_model,
                "retries_count": retries_count,
                "models_attempted": models_attempted
            }

            update_agent_status(
                self.run_id,
                self.agent_name,
                "COMPLETED",
                output_data=output_payload,
                retries_count=retries_count,
                selected_model=selected_model,
                actual_model=actual_model,
                models_attempted=models_attempted
            )
            logger.info(f"[{self.run_id}] Agent 5: Finished execution of {len(results)} tests (Model: {actual_model}, Retries: {retries_count}).")
            return results

        except Exception as e:
            err = f"Test execution failed: {str(e)}"
            error_cat = getattr(e, "error_category", "ExecutionError")
            attempted = getattr(e, "models_attempted", [ai_model] if ai_model else [])
            retries = getattr(e, "total_retries", 0)
            logger.error(f"[{self.run_id}] Agent 5 error: {err}")
            update_agent_status(
                self.run_id,
                self.agent_name,
                "FAILED",
                error_message=err,
                retries_count=retries,
                selected_model=ai_model or "",
                models_attempted=attempted,
                error_category=error_cat
            )
            raise RuntimeError(err)

    def _generate_failure_screenshot(self, target_path: Path, case_id: str, title: str, error_text: str):
        """Generates an informative diagnostic screenshot placeholder image if headless browser crashed or assertion failed."""
        try:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            svg_content = f'''<svg xmlns="http://www.w3.org/2000/svg" width="800" height="450" viewBox="0 0 800 450">
  <rect width="100%" height="100%" fill="#0f172a"/>
  <rect x="20" y="20" width="760" height="410" rx="8" fill="#1e293b" stroke="#ef4444" stroke-width="2"/>
  <text x="50" y="70" fill="#ef4444" font-family="sans-serif" font-size="22" font-weight="bold">TEST EXECUTION FAILURE</text>
  <text x="50" y="110" fill="#94a3b8" font-family="sans-serif" font-size="14">Test Case: {case_id} - {title[:60]}</text>
  <text x="50" y="140" fill="#f87171" font-family="monospace" font-size="12">Timestamp: {datetime.now().isoformat()}</text>
  <rect x="50" y="160" width="700" height="230" rx="4" fill="#090d16"/>
  <text x="70" y="195" fill="#e2e8f0" font-family="monospace" font-size="12">Diagnostics &amp; Failure Trace:</text>
  <text x="70" y="230" fill="#fca5a5" font-family="monospace" font-size="11">{error_text[:200].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")}</text>
</svg>'''
            svg_path = target_path.with_suffix(".svg")
            with open(svg_path, "w", encoding="utf-8") as f:
                f.write(svg_content)

            import struct, zlib
            def make_png(width, height, r, g, b):
                raw = b"".join(b"\x00" + bytes([r, g, b]) * width for _ in range(height))
                compressed = zlib.compress(raw)
                def chunk(tag, data):
                    return struct.pack("!I", len(data)) + tag + data + struct.pack("!I", zlib.crc32(tag + data))
                return (
                    b"\x89PNG\r\n\x1a\n"
                    + chunk(b"IHDR", struct.pack("!2I5B", width, height, 8, 2, 0, 0, 0))
                    + chunk(b"IDAT", compressed)
                    + chunk(b"IEND", b"")
                )
            with open(target_path, "wb") as f:
                f.write(make_png(320, 180, 239, 68, 68))
        except Exception as e:
            logger.warning(f"Could not generate failure placeholder image: {e}")
