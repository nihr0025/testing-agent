import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from backend.config import REPORTS_DIR, SCREENSHOTS_DIR

router = APIRouter(prefix="/api/reports", tags=["Reports & Artifacts"])

@router.get("/{run_id}/html")
def download_html_report(run_id: str):
    file_path = REPORTS_DIR / f"report_{run_id}.html"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="HTML report not found.")
    return FileResponse(
        path=str(file_path),
        filename=f"test_report_{run_id}.html",
        media_type="text/html"
    )

@router.get("/screenshots/{filename}")
def get_screenshot(filename: str):
    # Sanitize filename
    safe_filename = os.path.basename(filename)
    file_path = SCREENSHOTS_DIR / safe_filename
    if not file_path.exists():
        # Check SVG
        svg_path = file_path.with_suffix(".svg")
        if svg_path.exists():
            return FileResponse(path=str(svg_path), media_type="image/svg+xml")
        raise HTTPException(status_code=404, detail="Screenshot not found.")
    return FileResponse(path=str(file_path), media_type="image/png")
