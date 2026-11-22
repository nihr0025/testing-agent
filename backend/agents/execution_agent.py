import logging
import time
import subprocess
import os
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
from backend.config import REPORTS_DIR, SCREENSHOTS_DIR
from backend.database.db import save_execution_result, update_agent_status

logger = logging.getLogger("testing_platform.agent5_execution")

class TestExecutionAgent:
    """
    AGENT 5: TEST EXECUTION AND VALIDATION AGENT
    Responsibilities:
    1. Receive automation scripts from Agent 4.
    2. Execute scripts using pytest and Playwright or Selenium.
    3. Capture test execution status (Passed, Failed, Skipped).
    4. Capture failure screenshots, execution logs, and browser errors.
    5. Record execution duration for each test.
    6. Save logs and screenshots in the reports directory.
    7. Return structured execution results.
    """
    def __init__(self, run_id: str, framework: str = "playwright"):
        self.run_id = run_id
        self.framework = framework.lower()
        self.agent_name = "execution_agent"

    def execute(self, automation_scripts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        logger.info(f"[{self.run_id}] Agent 5: Executing {len(automation_scripts)} {self.framework.upper()} tests...")
        update_agent_status(self.run_id, self.agent_name, "RUNNING")

        try:
            if not automation_scripts:
                raise ValueError("No automation scripts provided to Test Execution Agent.")

            results = []
            python_exe = os.path.abspath(r"C:\Users\nihar\AppData\Local\Programs\Python\Python311\python.exe")

            for script_item in automation_scripts:
                case_id = script_item.get("case_id", "TC-01")
                title = script_item.get("title", f"Test {case_id}")
                script_path = script_item.get("script_path", "")

                start_time = time.time()
                status = "Passed"
                actual_result = f"Test {case_id} completed successfully."
                expected_result = f"Page loaded, verified elements, and satisfied assertions."
                error_msg = None
                log_output = ""
                screenshot_rel_path = None

                if not os.path.exists(script_path):
                    status = "Failed"
                    error_msg = f"Script file not found: {script_path}"
                    actual_result = error_msg
                else:
                    # Run pytest on the script
                    cmd = [python_exe, "-m", "pytest", script_path, "-v", "--tb=short"]
                    try:
                        proc = subprocess.run(
                            cmd,
                            capture_output=True,
                            text=True,
                            timeout=45,
                            cwd=os.path.dirname(script_path)
                        )
                        log_output = f"STDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"

                        if proc.returncode == 0:
                            status = "Passed"
                            actual_result = f"Automated assertions passed for {case_id}."
                        else:
                            status = "Failed"
                            error_msg = f"Pytest exit code {proc.returncode}.\n{proc.stdout[-500:]}"
                            actual_result = f"Test assertion or browser navigation failed."
                            # Capture failure screenshot placeholder/artifact
                            screenshot_name = f"fail_{self.run_id}_{case_id.lower()}.png"
                            screenshot_full = SCREENSHOTS_DIR / screenshot_name
                            self._generate_failure_screenshot(screenshot_full, case_id, title, error_msg)
                            screenshot_rel_path = f"/reports/screenshots/{screenshot_name}"

                    except subprocess.TimeoutExpired:
                        status = "Failed"
                        error_msg = f"Execution timed out after 45 seconds for {case_id}."
                        actual_result = "Test execution timeout."
                    except Exception as ex:
                        status = "Failed"
                        error_msg = f"Execution error: {str(ex)}"
                        actual_result = f"Execution failure: {str(ex)}"

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

            update_agent_status(self.run_id, self.agent_name, "COMPLETED", output_data=results)
            logger.info(f"[{self.run_id}] Agent 5: Finished execution of {len(results)} tests.")
            return results

        except Exception as e:
            err = f"Test execution failed: {str(e)}"
            logger.error(f"[{self.run_id}] Agent 5 error: {err}")
            update_agent_status(self.run_id, self.agent_name, "FAILED", error_message=err)
            raise RuntimeError(err)

    def _generate_failure_screenshot(self, target_path: Path, case_id: str, title: str, error_text: str):
        """Generates an informative diagnostic screenshot placeholder image if headless failed."""
        try:
            # We can create a simple 1280x720 PNG with error details using Pillow if available,
            # or a clean SVG/PNG byte stream.
            # Writing an SVG or minimal PNG
            # A valid 1x1 or minimal PNG or SVG text image:
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
            # Also save as svg or png
            svg_path = target_path.with_suffix(".svg")
            with open(svg_path, "w", encoding="utf-8") as f:
                f.write(svg_content)
            # If png requested, create standard png file
            # Write a minimal 1x1 red PNG if nothing else or copy
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
