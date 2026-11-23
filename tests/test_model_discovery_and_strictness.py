import os
import re
import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
from fastapi.testclient import TestClient

from backend.main import app
from backend.config import config
from backend.services.model_registry import model_registry
from backend.services.model_discovery_service import model_discovery_service
from backend.services.ai_service import ai_service
from backend.database.db import get_run, get_requirements, get_scenarios, get_test_cases

client = TestClient(app)

# ------------------------------------------------------------------------------
# 1. NO HARDCODED KEYS OR MODEL IDS IN SOURCE CODE
# ------------------------------------------------------------------------------
def test_1_no_hardcoded_keys_or_model_ids():
    """Verify that zero hardcoded model IDs or secret keys exist in backend or frontend src."""
    forbidden_patterns = [
        re.compile(r'gemini-2\.5-flash', re.I),
        re.compile(r'gemini-2\.0-flash', re.I),
        re.compile(r'gemini-3\.5-flash', re.I),
        re.compile(r'gpt-4o-mini', re.I),
        re.compile(r'gpt-4o\b', re.I),
        re.compile(r'sk-[a-zA-Z0-9]{20,}', re.I),
        re.compile(r'AIza[a-zA-Z0-9_-]{20,}', re.I),
    ]

    root = Path(__file__).resolve().parent.parent
    checked_files = 0

    scan_dirs = [root / "backend", root / "frontend" / "src"]
    for s_dir in scan_dirs:
        for file_path in s_dir.rglob("*"):
            if file_path.suffix in [".py", ".js", ".jsx"]:
                checked_files += 1
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                for p in forbidden_patterns:
                    matches = p.findall(content)
                    assert not matches, (
                        f"Forbidden hardcoded pattern '{p.pattern}' found in {file_path}: {matches}"
                    )

    assert checked_files > 15, f"Expected to scan at least 15 source files, scanned {checked_files}"

# ------------------------------------------------------------------------------
# 2. NO RUNTIME MODEL ID DEFAULT
# ------------------------------------------------------------------------------
def test_2_no_runtime_model_default():
    """Verify that absence of model selection raises an error, not a silent default."""
    # When preferred_mode is openai or gemini, model_name=None must raise ValueError
    with pytest.raises(ValueError, match="No AI model was specified"):
        ai_service.generate_requirements(
            website_url="http://test.local",
            preferred_mode="openai",
            model_name=None,
            allow_fallback=False
        )

    with pytest.raises(ValueError, match="No AI model was specified"):
        ai_service.generate_requirements(
            website_url="http://test.local",
            preferred_mode="gemini",
            model_name="",
            allow_fallback=False
        )

# ------------------------------------------------------------------------------
# 3. GEMINI MODEL DISCOVERY USES AUTHENTICATED API
# ------------------------------------------------------------------------------
def test_3_gemini_discovery_filters_models():
    """Verify that Gemini model discovery calls API and filters out embeddings/non-generative models."""
    class FakeGeminiModel:
        def __init__(self, name, display_name="", supported_actions=None):
            self.name = name
            self.display_name = display_name
            self.description = "Test model"
            self.supported_actions = supported_actions or ["generateContent"]

    mock_client = MagicMock()
    mock_client.models.list.return_value = [
        FakeGeminiModel("models/custom-test-gemini", "Custom Test Gemini"),
        FakeGeminiModel("models/text-embedding-004", "Embedding Model", ["embedContent"]),
        FakeGeminiModel("models/imagen-3.0", "Imagen Model", ["generateImage"]),
    ]

    gem_provider = model_registry.get_provider("gemini")
    with patch.object(gem_provider, "_get_client", return_value=mock_client):
        discovered = gem_provider.discover_models_from_api()
        ids = [m["id"] for m in discovered]
        assert "custom-test-gemini" in ids
        assert "text-embedding-004" not in ids
        assert "imagen-3.0" not in ids

# ------------------------------------------------------------------------------
# 4. OPENAI MODEL DISCOVERY USES AUTHENTICATED API
# ------------------------------------------------------------------------------
def test_4_openai_discovery_filters_models():
    """Verify that OpenAI model discovery queries API and filters out embeddings/audio/moderation."""
    class FakeOpenAIModel:
        def __init__(self, id_):
            self.id = id_

    mock_client = MagicMock()
    mock_client.models.list.return_value = [
        FakeOpenAIModel("gpt-custom-model-v1"),
        FakeOpenAIModel("text-embedding-3-small"),
        FakeOpenAIModel("whisper-1"),
        FakeOpenAIModel("tts-1"),
        FakeOpenAIModel("text-moderation-latest"),
    ]

    oai_provider = model_registry.get_provider("openai")
    with patch.object(oai_provider, "_get_client", return_value=mock_client):
        discovered = oai_provider.discover_models_from_api()
        ids = [m["id"] for m in discovered]
        assert "gpt-custom-model-v1" in ids
        assert "text-embedding-3-small" not in ids
        assert "whisper-1" not in ids
        assert "tts-1" not in ids

# ------------------------------------------------------------------------------
# 5. EMPTY MODEL DISCOVERY DOES NOT TRIGGER HARDCODED FALLBACK
# ------------------------------------------------------------------------------
def test_5_empty_discovery_no_fallback():
    """Verify that empty provider response or API failure returns empty list with error, NO fallback."""
    mock_client = MagicMock()
    mock_client.models.list.side_effect = Exception("HTTP 403: Forbidden - Invalid API key")

    gem_provider = model_registry.get_provider("gemini")
    model_discovery_service.clear_cache("gemini")

    with patch.object(gem_provider, "_get_client", return_value=mock_client), \
         patch.object(gem_provider, "is_configured", return_value=True):
        res = model_discovery_service.discover_models("gemini", force_refresh=True)
        assert res["models"] == [], "Expected empty model list on discovery failure!"
        assert res["error_type"] == "PermissionDenied"
        assert "403" in res["error"]

# ------------------------------------------------------------------------------
# 6. INVALID / MISSING MODEL SELECTION REJECTED BY API
# ------------------------------------------------------------------------------
def test_6_start_run_requires_model_selection():
    """Verify that starting an AI run without selecting a model returns HTTP 400."""
    # Attempting to start OpenAI run without ai_model
    with patch("backend.config.config.is_openai_configured", return_value=True):
        res = client.post("/api/testing/start", json={
            "website_url": "http://127.0.0.1:8000/demo",
            "ai_provider": "openai",
            "ai_model": ""  # empty
        })
        assert res.status_code == 400
        assert "No OpenAI model was selected" in res.json()["detail"]

    # Attempting to start Gemini run without ai_model
    with patch("backend.config.config.is_gemini_configured", return_value=True):
        res = client.post("/api/testing/start", json={
            "website_url": "http://127.0.0.1:8000/demo",
            "ai_provider": "gemini",
            "ai_model": None  # None
        })
        assert res.status_code == 400
        assert "No Gemini model was selected" in res.json()["detail"]

# ------------------------------------------------------------------------------
# 7. EXACT SELECTED MODEL REACHES ALL SIX AGENTS
# ------------------------------------------------------------------------------
def test_7_exact_selected_model_propagates_to_agents():
    """Verify that the exact user-selected model is passed to all agents and recorded in DB."""
    from backend.agents.orchestrator_agent import OrchestrationAgent

    mock_model_id = "user-selected-model-alpha-100"
    run_id = "TEST-RUN-MODEL-PROPAGATE"

    # Mock provider generation methods
    gem_provider = model_registry.get_provider("gemini")
    mock_reqs = ([{"req_id": "REQ-1", "description": "Test", "priority": "High"}], "gemini", None)
    mock_scenarios = [{"scenario_id": "SC-1", "req_id": "REQ-1", "title": "Scen 1", "scenario_type": "Functional", "priority": "High"}]
    mock_cases = [{"case_id": "TC-1", "scenario_id": "SC-1", "title": "Case 1", "priority": "High", "preconditions": [], "test_data": {}, "execution_steps": [], "expected_result": "Success", "status": "Not Executed"}]

    with patch.object(gem_provider, "generate_requirements", return_value=mock_reqs) as mock_gen_req, \
         patch.object(gem_provider, "generate_scenarios", return_value=mock_scenarios) as mock_gen_sc, \
         patch.object(gem_provider, "generate_test_cases", return_value=mock_cases) as mock_gen_tc, \
         patch("backend.agents.execution_agent.TestExecutionAgent.execute", return_value=[{"case_id": "TC-1", "status": "Passed", "duration_sec": 0.5}]), \
         patch("backend.agents.automation_agent.TestAutomationAgent.execute", return_value=[]), \
         patch.object(gem_provider, "is_configured", return_value=True):

        orch = OrchestrationAgent(run_id)
        report = orch.run_workflow(
            website_url="http://127.0.0.1:8000/demo",
            manual_requirements="Test",
            automation_framework="playwright",
            generation_mode="gemini",
            ai_model=mock_model_id
        )

        # Check call arguments
        mock_gen_req.assert_called_once()
        assert mock_gen_req.call_args[1].get("model_name") == mock_model_id

        mock_gen_sc.assert_called_once()
        assert mock_gen_sc.call_args[1].get("model_name") == mock_model_id

        mock_gen_tc.assert_called_once()
        assert mock_gen_tc.call_args[1].get("model_name") == mock_model_id

        # Verify DB records
        req_records = get_requirements(run_id)
        assert req_records[0]["ai_model"] == mock_model_id

        sc_records = get_scenarios(run_id)
        assert sc_records[0]["ai_model"] == mock_model_id

        tc_records = get_test_cases(run_id)
        assert tc_records[0]["ai_model"] == mock_model_id

        assert report["ai_model"] == mock_model_id

# ------------------------------------------------------------------------------
# 8. FAILED MODEL DOES NOT SILENTLY TRIGGER DIFFERENT MODEL OR FALLBACK
# ------------------------------------------------------------------------------
def test_8_failed_model_does_not_silently_fallback():
    """Verify that when a model fails, it raises an error and does NOT silently switch to Basic or another model."""
    gem_provider = model_registry.get_provider("gemini")

    with patch.object(gem_provider, "is_configured", return_value=True), \
         patch.object(gem_provider, "_call_gemini_json", side_effect=RuntimeError("QuotaExceeded: 429")):

        with pytest.raises(RuntimeError, match="Requirement generation failed on provider 'gemini' with selected model 'my-model'"):
            ai_service.generate_requirements(
                website_url="http://test.local",
                preferred_mode="gemini",
                model_name="my-model",
                allow_fallback=False  # default
            )

# ------------------------------------------------------------------------------
# 9. BASIC MODE WORKS INDEPENDENTLY WITHOUT ANY API KEYS
# ------------------------------------------------------------------------------
def test_9_basic_mode_without_keys():
    """Verify Basic Mode operates deterministically with zero credentials."""
    with patch("backend.config.config.OPENAI_API_KEY", ""), \
         patch("backend.config.config.GEMINI_API_KEY", ""):

        reqs, prov, fallback = ai_service.generate_requirements(
            website_url="http://127.0.0.1:8000/demo",
            manual_reqs="Test login and cart",
            preferred_mode="basic",
            model_name=None
        )
        assert prov == "basic"
        assert fallback is None
        assert len(reqs) > 0

# ------------------------------------------------------------------------------
# 10. NO SECRETS IN API RESPONSES
# ------------------------------------------------------------------------------
def test_10_no_secrets_in_responses():
    """Verify that credentials never appear in API responses."""
    endpoints = [
        "/api/settings",
        "/api/ai/providers",
        "/api/ai/configuration/status",
        "/api/health"
    ]
    secret_fingerprint = "test-api-key-not-real"
    for ep in endpoints:
        res = client.get(ep)
        assert res.status_code == 200
        text = res.text
        assert secret_fingerprint not in text, f"Secret key leaked in endpoint {ep}!"
