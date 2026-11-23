import json
import time
import random
import re
import logging
from typing import Dict, Any, List, Optional, Tuple, Union
from backend.config import config

logger = logging.getLogger("testing_platform.gemini_engine")

class GeminiExecutionError(RuntimeError):
    """Structured exception raised when Gemini execution fails after all retries and alternatives."""
    def __init__(
        self,
        message: str,
        selected_model: str,
        actual_model: Optional[str] = None,
        models_attempted: Optional[List[str]] = None,
        total_retries: int = 0,
        error_category: str = "UnknownError",
        actionable_advice: str = ""
    ):
        super().__init__(message)
        self.selected_model = selected_model
        self.actual_model = actual_model
        self.models_attempted = models_attempted or []
        self.total_retries = total_retries
        self.error_category = error_category
        self.actionable_advice = actionable_advice

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error": str(self),
            "selected_model": self.selected_model,
            "actual_model": self.actual_model,
            "models_attempted": self.models_attempted,
            "total_retries": self.total_retries,
            "error_category": self.error_category,
            "actionable_advice": self.actionable_advice
        }


class GeminiExecutionEngine:
    """
    CENTRALIZED GEMINI EXECUTION ENGINE (Phase 2 Reliability)
    
    Responsibilities:
    1. Centralize all Gemini API interactions across the six agents.
    2. Enforce up to 3 retries with exponential backoff, jitter, and Retry-After support.
    3. Retry temporary errors: 503, 429, 500, 504, and network timeouts.
    4. Refuse retries on permanent errors: 401 (Auth), 403 (Permission), 400 (Bad Request).
    5. Handle 404 (Retired/Unavailable model) by immediately trying configured Gemini alternatives.
    6. Seamlessly failover to user-configured alternative Gemini models if primary fails.
    7. Strictly prohibit switching to OpenAI or Basic Mode.
    8. Record selected vs actual models, total retries, and attempted models.
    9. Emit structured observability logs for each execution attempt.
    """

    def __init__(
        self,
        max_retries_per_model: int = 3,
        base_delay_seconds: float = 1.0,
        max_delay_seconds: float = 30.0,
        jitter_factor: float = 0.5
    ):
        self.max_retries_per_model = max_retries_per_model
        self.base_delay_seconds = base_delay_seconds
        self.max_delay_seconds = max_delay_seconds
        self.jitter_factor = jitter_factor
        self._client = None

    def _get_client(self):
        if not self._client:
            from google import genai
            api_key = config.GEMINI_API_KEY or config.GOOGLE_API_KEY
            if not api_key:
                raise GeminiExecutionError(
                    message="GEMINI_API_KEY is not configured in backend .env.",
                    selected_model="",
                    error_category="MissingCredentials",
                    actionable_advice="Add GEMINI_API_KEY=your_key to backend/.env and restart."
                )
            self._client = genai.Client(api_key=api_key)
        return self._client

    def classify_error(self, exc: Exception) -> Tuple[bool, str, Optional[float], str]:
        """
        Classifies an exception into:
        (is_transient, error_category, retry_after_seconds, actionable_advice)
        """
        err_str = str(exc)
        err_type = type(exc).__name__
        
        # 1. Parse Retry-After or quota delay if present
        retry_after = self._extract_retry_after(exc, err_str)

        # 2. Check for permanent authentication or permission errors (Do NOT retry)
        if "401" in err_str or "API_KEY_INVALID" in err_str or "UNAUTHENTICATED" in err_str:
            return (
                False,
                "AuthenticationError",
                None,
                "The Gemini API key is invalid or revoked. Check GEMINI_API_KEY in backend/.env."
            )

        if "403" in err_str or "PermissionDenied" in err_type or "Forbidden" in err_str or "not allowed by policy" in err_str:
            return (
                False,
                "PermissionDenied",
                None,
                "Gemini API request not allowed by policy. Ensure the Generative Language API is enabled in Google Cloud Console and no IP/referrer restrictions block server calls."
            )

        if "404" in err_str or "NOT_FOUND" in err_str or "no longer available" in err_str.lower():
            return (
                False,  # Not transient for this model, but caller can switch to alternative Gemini model
                "ModelNotFound",
                None,
                "The selected Gemini model is not available or has been retired by Google. Select an active model or configure alternative Gemini models."
            )

        if "400" in err_str or "INVALID_ARGUMENT" in err_str:
            return (
                False,
                "InvalidArgument",
                None,
                "The request prompt or schema was rejected by Google Gemini as malformed."
            )

        # 3. Check for transient errors (Retryable with exponential backoff & jitter)
        if "503" in err_str or "UNAVAILABLE" in err_str or "high demand" in err_str.lower():
            return (
                True,
                "ServiceUnavailable",
                retry_after,
                "Google Gemini servers are experiencing temporary high demand (503). Retrying with backoff."
            )

        if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "rate limit" in err_str.lower() or "quota" in err_str.lower():
            return (
                True,
                "QuotaExceeded",
                retry_after,
                "Gemini API rate limit or quota exceeded (429). Retrying after backoff."
            )

        if "504" in err_str or "GATEWAY_TIMEOUT" in err_str or "DEADLINE_EXCEEDED" in err_str:
            return (
                True,
                "GatewayTimeout",
                retry_after,
                "Gemini gateway timed out waiting for response (504). Retrying."
            )

        if "500" in err_str or "INTERNAL" in err_str or "InternalServerError" in err_type:
            return (
                True,
                "ServerError",
                retry_after,
                "Google Gemini encountered an internal server error (500). Retrying."
            )

        if any(term in err_str.lower() or term in err_type.lower() for term in [
            "timeout", "connectionerror", "remotedisconnected", "connecttimeout", "network", "reset by peer"
        ]):
            return (
                True,
                "NetworkError",
                retry_after,
                "Network connection to generativelanguage.googleapis.com failed or timed out. Retrying."
            )

        # Default fallback: treat unknown errors as transient once up to retry limit
        return (
            True,
            "TransientError",
            retry_after,
            f"Encountered unexpected error: {err_str[:120]}. Retrying with backoff."
        )

    def _extract_retry_after(self, exc: Exception, err_str: str) -> Optional[float]:
        """Extracts seconds from HTTP Retry-After headers or error messages."""
        # Check response headers if present on exception
        response = getattr(exc, "response", None)
        if response and hasattr(response, "headers"):
            ra = response.headers.get("Retry-After") or response.headers.get("retry-after")
            if ra:
                try:
                    return float(ra)
                except (ValueError, TypeError):
                    pass

        # Check for retryDelay in Google error details
        details = getattr(exc, "details", None)
        if details and isinstance(details, dict):
            retry_info = details.get("retry_info") or details.get("retryDelay")
            if retry_info:
                delay_str = str(retry_info)
                match = re.search(r"(\d+(?:\.\d+)?)s?", delay_str)
                if match:
                    try:
                        return float(match.group(1))
                    except ValueError:
                        pass

        # Check regex in error message string like "retry after 5.2s" or "quota resets in 4s"
        match = re.search(r"retry\s+(?:after|in)\s+(\d+(?:\.\d+)?)s?", err_str, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                pass

        return None

    def calculate_backoff(self, attempt: int, retry_after: Optional[float] = None) -> float:
        """Calculates exponential backoff with randomized jitter and respects Retry-After."""
        if retry_after is not None and retry_after > 0:
            return min(retry_after, self.max_delay_seconds)

        # Exponential backoff: base_delay * 2^attempt
        delay = self.base_delay_seconds * (2 ** attempt)
        # Add random jitter between 0 and (jitter_factor * delay)
        jitter = random.uniform(0.05, max(0.1, self.jitter_factor * delay))
        total_delay = min(delay + jitter, self.max_delay_seconds)
        return round(total_delay, 2)

    def execute(
        self,
        prompt: str,
        system_instruction: str = "",
        primary_model: str = "",
        alternative_models: Optional[List[str]] = None,
        json_output: bool = True,
        run_id: str = "SYSTEM",
        agent_name: str = "orchestrator",
        temperature: float = 0.2
    ) -> Dict[str, Any]:
        """
        Executes a prompt against Gemini with intelligent retries and configured alternatives.
        
        Args:
            prompt: User/task prompt.
            system_instruction: Role/persona system instruction.
            primary_model: The user's chosen primary Gemini model.
            alternative_models: List of optional Gemini model IDs to try if primary fails.
            json_output: If True, enforces structured JSON output.
            run_id: Associated testing run ID for structured logs.
            agent_name: Which of the 6 agents is calling.
            temperature: Generation temperature (default 0.2).
            
        Returns:
            Dict containing:
                - "data": Parsed JSON object (if json_output=True) or response text string.
                - "selected_model": Primary model requested.
                - "actual_model": The model that actually succeeded.
                - "retries_count": Total retries performed.
                - "models_attempted": List of all model IDs attempted.
                - "latency_ms": Round-trip latency in milliseconds.
                - "failover_occurred": True if an alternative model was used.
        """
        if not primary_model or not primary_model.strip():
            raise GeminiExecutionError(
                message="No Gemini primary model was specified. An explicit model ID is strictly required.",
                selected_model="",
                error_category="InvalidModelSelection",
                actionable_advice="Select a dynamically discovered Gemini model from the model dropdown."
            )

        client = self._get_client()

        # Build candidate model pipeline: primary model first, followed by deduplicated alternatives
        clean_primary = primary_model.strip()
        if clean_primary.startswith("models/"):
            clean_primary = clean_primary[len("models/"):]

        candidate_models = [clean_primary]
        if alternative_models:
            for alt in alternative_models:
                clean_alt = alt.strip()
                if clean_alt.startswith("models/"):
                    clean_alt = clean_alt[len("models/"):]
                if clean_alt and clean_alt not in candidate_models:
                    candidate_models.append(clean_alt)

        models_attempted = []
        total_retries = 0
        last_error = None
        last_category = "UnknownError"
        last_advice = ""

        from google.genai import types

        for model_idx, current_model in enumerate(candidate_models):
            models_attempted.append(current_model)
            is_alternative = (current_model != clean_primary)

            if is_alternative:
                logger.warning(
                    f"[{run_id}] [{agent_name}] Primary Gemini model '{clean_primary}' exhausted or retired. "
                    f"Failing over to configured Gemini alternative model: '{current_model}'."
                )

            # Up to max_retries_per_model for this model
            for attempt in range(self.max_retries_per_model + 1):
                start_time = time.time()
                config_obj = types.GenerateContentConfig(
                    system_instruction=system_instruction or None,
                    response_mime_type="application/json" if json_output else "text/plain",
                    temperature=temperature
                )

                logger.info(
                    f"[{run_id}] [{agent_name}] Invoking Gemini model '{current_model}' "
                    f"(attempt {attempt + 1}/{self.max_retries_per_model + 1}, json={json_output})"
                )

                try:
                    response = client.models.generate_content(
                        model=current_model,
                        contents=prompt,
                        config=config_obj
                    )

                    latency_ms = int((time.time() - start_time) * 1000)
                    raw_text = response.text or ""

                    # Parse output
                    if json_output:
                        parsed_data = self._clean_and_parse_json(raw_text)
                    else:
                        parsed_data = raw_text

                    logger.info(
                        f"[{run_id}] [{agent_name}] Gemini model '{current_model}' SUCCEEDED in {latency_ms}ms "
                        f"(total retries so far: {total_retries}, failover: {is_alternative})"
                    )

                    return {
                        "data": parsed_data,
                        "selected_model": clean_primary,
                        "actual_model": current_model,
                        "retries_count": total_retries,
                        "models_attempted": models_attempted,
                        "latency_ms": latency_ms,
                        "failover_occurred": is_alternative
                    }

                except Exception as exc:
                    latency_ms = int((time.time() - start_time) * 1000)
                    is_transient, category, retry_after, advice = self.classify_error(exc)
                    last_error = exc
                    last_category = category
                    last_advice = advice

                    logger.warning(
                        f"[{run_id}] [{agent_name}] Model '{current_model}' attempt {attempt + 1} FAILED "
                        f"({category}, latency {latency_ms}ms): {str(exc)[:140]}"
                    )

                    # If model is retired / not found (404), break immediately to next alternative model
                    if category == "ModelNotFound":
                        logger.warning(
                            f"[{run_id}] [{agent_name}] Model '{current_model}' is not available (404). "
                            f"Skipping remaining retries on this model."
                        )
                        break

                    # If permanent authentication or permission error, abort immediately!
                    if not is_transient:
                        logger.error(
                            f"[{run_id}] [{agent_name}] Permanent error encountered on model '{current_model}': {category}. "
                            f"Aborting without retrying."
                        )
                        raise GeminiExecutionError(
                            message=f"Gemini execution permanently failed on model '{current_model}' ({category}): {str(exc)}",
                            selected_model=clean_primary,
                            actual_model=None,
                            models_attempted=models_attempted,
                            total_retries=total_retries,
                            error_category=category,
                            actionable_advice=advice
                        )

                    # Transient error: check if we have retries left on this model
                    if attempt < self.max_retries_per_model:
                        total_retries += 1
                        delay = self.calculate_backoff(attempt, retry_after)
                        logger.info(
                            f"[{run_id}] [{agent_name}] Backing off for {delay}s before retry {attempt + 2} "
                            f"(jitter applied, Retry-After={retry_after})..."
                        )
                        time.sleep(delay)
                    else:
                        logger.warning(
                            f"[{run_id}] [{agent_name}] Max retries ({self.max_retries_per_model}) exhausted on model '{current_model}'."
                        )

        # If all candidates and retries exhausted
        logger.error(
            f"[{run_id}] [{agent_name}] ALL candidate Gemini models exhausted ({models_attempted}) "
            f"with total {total_retries} retries. STRICT POLICY: No fallback to OpenAI or Basic Mode."
        )

        raise GeminiExecutionError(
            message=(
                f"Gemini execution failed after {total_retries} retries across attempted models {models_attempted}. "
                f"Last error ({last_category}): {str(last_error)}"
            ),
            selected_model=clean_primary,
            actual_model=None,
            models_attempted=models_attempted,
            total_retries=total_retries,
            error_category=last_category,
            actionable_advice=last_advice or "Try selecting a different Gemini model from the dropdown or verify quota."
        )

    def _clean_and_parse_json(self, raw_text: str) -> Union[Dict[str, Any], List[Any]]:
        """Strips markdown code fences and parses valid JSON."""
        clean = (raw_text or "").strip()
        if clean.startswith("```json"):
            clean = clean[7:]
        elif clean.startswith("```"):
            clean = clean[3:]
        if clean.endswith("```"):
            clean = clean[:-3]
        clean = clean.strip()
        try:
            return json.loads(clean)
        except json.JSONDecodeError as e:
            # Fallback regex search for outer {...} or [...]
            match = re.search(r"(\{|\[).+(\}|\])", clean, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except Exception:
                    pass
            raise ValueError(f"Failed to parse structured JSON from Gemini response: {e}. Raw content: {clean[:200]}")

# Global singleton
gemini_engine = GeminiExecutionEngine()
