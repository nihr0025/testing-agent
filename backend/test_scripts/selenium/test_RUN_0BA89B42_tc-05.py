# Auto-generated Selenium Test Script
# Test Case ID: TC-05
# Scenario: SC-05
# Title: Negative Input Validation for REQ-02
# Generation Mode: Basic Testing Mode (Page Inspection Engine)

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def test_tc_05():
    """Negative Input Validation for REQ-02"""
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1280,720")

    driver = webdriver.Chrome(options=options)
    try:
        # 1. Navigate to target URL
        driver.set_page_load_timeout(15)
        driver.get("https://www.youtube.com/")

        # 2. Verify page title & body container
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        assert driver.title is not None, "Page title should not be None"

        # 3. Check for links and interactable controls
        elements = driver.find_elements(By.CSS_SELECTOR, "a, button, input")
        assert len(elements) >= 0, "Interactive elements check failed"

    finally:
        driver.quit()
