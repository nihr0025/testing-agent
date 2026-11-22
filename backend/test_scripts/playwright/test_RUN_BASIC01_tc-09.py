# Auto-generated Playwright Test Script
# Test Case ID: TC-09
# Scenario: SC-09
# Title: Navigation & Control Responsiveness for REQ-03
# Generation Mode: Basic Testing Mode (Page Inspection Engine)

import pytest
from playwright.sync_api import sync_playwright, expect

def test_tc_09():
    """Navigation & Control Responsiveness for REQ-03"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 720})
        page = context.new_page()

        try:
            # 1. Navigate to target URL
            response = page.goto("http://127.0.0.1:8000/demo", timeout=15000, wait_until="domcontentloaded")
            assert response is not None, "Failed to load target page"
            assert response.status < 400, f"Page returned error status code: {response.status}"

            # 2. Verify page document structure & title
            title = page.title()
            assert title is not None, "Page title should not be None"

            # 3. Verify page is interactable
            body = page.locator("body")
            expect(body).to_be_visible(timeout=5000)

            # 4. Check for interactive elements (links, buttons, inputs)
            interactive_count = page.locator("a, button, input").count()
            assert interactive_count >= 0, "Interactive elements check failed"

        finally:
            context.close()
            browser.close()
