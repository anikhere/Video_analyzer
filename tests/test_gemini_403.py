"""Regression tests for the Gemini 403 (PERMISSION_DENIED) fix.

Covers: AQ. keys defaulting to AI Studio (not Vertex), explicit Vertex
opt-in via env, one retry on the other surface after a 403, mismatched-key
validation, model normalization, and actionable 403 error messages.
"""
import json
import os
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from llm_service import (
    GEMINI_DEFAULT_MODEL,
    AnalysisError,
    _clean_api_key,
    _handle_llm_exception,
    _is_model_not_found_error,
    _make_gemini_client,
    _normalize_gemini_model,
    _validate_provider_key,
    analyze_video,
    analyze_video_dashboard,
)


def _gemini_result():
    return {
        "summary": "A summary",
        "topics": ["Topic"],
        "key_takeaways": ["Point"],
        "timestamps": [{"time": "00:01", "explanation": "Hello"}],
        "action_items": [],
        "audience": "Everyone",
        "terminology": [],
        "conclusion": "Done",
    }


def _dashboard_result():
    return {
        "tldr": "Thesis.",
        "content_type": "Tutorial",
        "summary": "Summary.",
        "premise": "Premise.",
        "core_breakdown": "Breakdown.",
        "topics": ["Topic"],
        "key_takeaways": ["Point"],
        "chapters": [{"start_time": "00:01", "title": "Intro", "summary": "Start"}],
        "timestamps": [{"time": "00:01", "explanation": "Hello"}],
        "action_items": [],
        "audience": "Everyone",
        "terminology": [],
        "conclusion": "Done",
    }


def _not_found(message="model not found"):
    return type("NotFoundError", (Exception,), {"code": 404, "status": "NOT_FOUND", "message": message})(message)


def _forbidden(message="403 PERMISSION_DENIED. Requests to this API aiplatform.googleapis.com are blocked."):
    return type("ClientError", (Exception,), {"code": 403, "status": "PERMISSION_DENIED", "message": message})(message)


class ClientSurfaceTests(unittest.TestCase):
    @patch("llm_service.genai.Client")
    def test_aq_key_defaults_to_ai_studio_not_vertex(self, mock_client):
        with patch.dict(os.environ, {}, clear=False):
            for var in ("GOOGLE_GENAI_USE_ENTERPRISE", "GOOGLE_GENAI_USE_VERTEXAI", "GEMINI_USE_VERTEXAI", "GEMINI_USE_ENTERPRISE"):
                os.environ.pop(var, None)
            _make_gemini_client("AQ.test-key")
        mock_client.assert_called_once_with(vertexai=False, api_key="AQ.test-key")

    @patch("llm_service.genai.Client")
    def test_aiza_key_defaults_to_ai_studio(self, mock_client):
        with patch.dict(os.environ, {}, clear=False):
            for var in ("GOOGLE_GENAI_USE_ENTERPRISE", "GOOGLE_GENAI_USE_VERTEXAI", "GEMINI_USE_VERTEXAI", "GEMINI_USE_ENTERPRISE"):
                os.environ.pop(var, None)
            _make_gemini_client("AIza.test-key")
        mock_client.assert_called_once_with(vertexai=False, api_key="AIza.test-key")

    @patch("llm_service.genai.Client")
    def test_vertex_opt_in_via_env(self, mock_client):
        with patch.dict(os.environ, {"GOOGLE_GENAI_USE_VERTEXAI": "true"}):
            _make_gemini_client("AQ.test-key")
        mock_client.assert_called_once_with(vertexai=True, api_key="AQ.test-key")

    @patch("llm_service.genai.Client")
    def test_key_is_cleaned_before_use(self, mock_client):
        with patch.dict(os.environ, {}, clear=False):
            for var in ("GOOGLE_GENAI_USE_ENTERPRISE", "GOOGLE_GENAI_USE_VERTEXAI", "GEMINI_USE_VERTEXAI", "GEMINI_USE_ENTERPRISE"):
                os.environ.pop(var, None)
            _make_gemini_client('  "AIza.clean-key"  ')
        mock_client.assert_called_once_with(vertexai=False, api_key="AIza.clean-key")

    def test_clean_api_key(self):
        self.assertEqual(_clean_api_key("  Bearer AIza.x  "), "AIza.x")
        self.assertEqual(_clean_api_key("'AQ.y'"), "AQ.y")
        self.assertEqual(_clean_api_key(""), "")

    def test_normalize_model(self):
        self.assertEqual(_normalize_gemini_model("models/gemini-3.5-flash-lite"), "gemini-3.5-flash-lite")
        self.assertEqual(_normalize_gemini_model(""), GEMINI_DEFAULT_MODEL)
        self.assertEqual(_normalize_gemini_model(" gemini-3.8-flash "), "gemini-3.8-flash")
        self.assertEqual(GEMINI_DEFAULT_MODEL, "gemini-3.5-flash-lite")


class KeyValidationTests(unittest.TestCase):
    def test_openrouter_key_rejected_for_gemini(self):
        with self.assertRaisesRegex(AnalysisError, "OpenRouter.*not a Gemini key"):
            _validate_provider_key("gemini", "sk-or-v1-abc")

    def test_gemini_key_rejected_for_openrouter(self):
        with self.assertRaisesRegex(AnalysisError, "Gemini key.*not an OpenRouter key"):
            _validate_provider_key("openrouter", "AIza.abc")
        with self.assertRaisesRegex(AnalysisError, "Gemini key"):
            _validate_provider_key("openrouter", "AQ.abc")

    def test_missing_key(self):
        with self.assertRaisesRegex(AnalysisError, "Missing GEMINI_API_KEY"):
            _validate_provider_key("gemini", "")

    def test_valid_keys_pass(self):
        self.assertEqual(_validate_provider_key("gemini", "AQ.valid"), "AQ.valid")
        self.assertEqual(_validate_provider_key("gemini", "AIza.valid"), "AIza.valid")
        self.assertEqual(_validate_provider_key("openrouter", "sk-or-v1-valid"), "sk-or-v1-valid")


class ErrorMessageTests(unittest.TestCase):
    def test_403_service_disabled_is_actionable(self):
        exc = _forbidden("Gemini API has not been used in project my-proj before or it is disabled.")
        msg = str(_handle_llm_exception(exc, "gemini", model="gemini-2.5-flash"))
        self.assertIn("403", msg)
        self.assertIn("Generative Language API", msg)
        self.assertIn("Cloud Console", msg)

    def test_403_invalid_key_is_actionable(self):
        exc = _forbidden("API key not valid. Please pass a valid API key.")
        msg = str(_handle_llm_exception(exc, "gemini"))
        self.assertIn("invalid", msg.lower())
        self.assertIn("aistudio.google.com", msg)

    def test_403_surface_blocked_is_actionable(self):
        exc = _forbidden("API_KEY_SERVICE_BLOCKED: Requests to this API aiplatform.googleapis.com are blocked.")
        msg = str(_handle_llm_exception(exc, "gemini"))
        self.assertIn("API_KEY_SERVICE_BLOCKED", msg)
        self.assertIn("API restrictions", msg)

    def test_403_never_leaks_key(self):
        exc = _forbidden("403 PERMISSION_DENIED")
        msg = str(_handle_llm_exception(exc, "gemini"))
        self.assertNotIn("AQ.secret", msg)


class SurfaceFallbackTests(unittest.TestCase):
    @patch("llm_service.genai.Client")
    def test_403_retries_on_other_surface_once(self, mock_client):
        primary = MagicMock()
        primary.vertexai = False
        primary.models.generate_content.side_effect = _forbidden()
        fallback = MagicMock()
        fallback.vertexai = True
        fallback.models.generate_content.return_value = SimpleNamespace(text=json.dumps(_gemini_result()))
        mock_client.side_effect = [primary, fallback]
        transcript = {"segments": [{"start": 1, "duration": 1, "text": "Hello"}]}
        with patch.dict(os.environ, {}, clear=False):
            for var in ("GOOGLE_GENAI_USE_ENTERPRISE", "GOOGLE_GENAI_USE_VERTEXAI", "GEMINI_USE_VERTEXAI", "GEMINI_USE_ENTERPRISE"):
                os.environ.pop(var, None)
            result = analyze_video({"title": "T"}, transcript, "AQ.key", "gemini-2.5-flash", "gemini")
        self.assertEqual(result["summary"], "A summary")
        self.assertEqual(mock_client.call_count, 2)
        # First AI Studio, then Vertex Express.
        self.assertEqual(mock_client.call_args_list[0].kwargs.get("vertexai"), False)
        self.assertEqual(mock_client.call_args_list[1].kwargs.get("vertexai"), True)

    @patch("llm_service.genai.Client")
    def test_429_does_not_retry_on_other_surface(self, mock_client):
        primary = MagicMock()
        primary.vertexai = False
        primary.models.generate_content.side_effect = type("RateError", (Exception,), {"code": 429, "status": "RESOURCE_EXHAUSTED", "message": "quota"})("quota")
        mock_client.return_value = primary
        transcript = {"segments": [{"start": 1, "duration": 1, "text": "Hello"}]}
        with self.assertRaisesRegex(AnalysisError, "rate limit"):
            analyze_video({"title": "T"}, transcript, "AIza.key", "gemini-2.5-flash", "gemini")
        mock_client.assert_called_once()

    @patch("llm_service.genai.Client")
    def test_dashboard_aq_key_uses_ai_studio(self, mock_client):
        mock_client.return_value.models.generate_content.return_value = SimpleNamespace(text=json.dumps(_dashboard_result()))
        segments = [{"start": 1.0, "duration": 10.0, "text": "Hello world"}]
        with patch.dict(os.environ, {}, clear=False):
            for var in ("GOOGLE_GENAI_USE_ENTERPRISE", "GOOGLE_GENAI_USE_VERTEXAI", "GEMINI_USE_VERTEXAI", "GEMINI_USE_ENTERPRISE"):
                os.environ.pop(var, None)
            result, calls = analyze_video_dashboard({"title": "T"}, {"segments": segments}, "AQ.key", "gemini-2.5-flash", "gemini")
        self.assertEqual(calls, 1)
        self.assertEqual(result["tldr"], "Thesis.")
        mock_client.assert_called_once_with(vertexai=False, api_key="AQ.key")

    @patch("llm_service.genai.Client")
    def test_404_retired_model_falls_back_to_current_model(self, mock_client):
        """gemini-2.5-flash is retired for new keys -> retry with a current model."""
        client = MagicMock()
        client.vertexai = False

        def _generate(model, **kwargs):
            if model == "gemini-2.5-flash":
                raise _not_found(
                    "This model models/gemini-2.5-flash is no longer available to new users. "
                    "Please update your code to use models/gemini-3.8-flash."
                )
            return SimpleNamespace(text=json.dumps(_gemini_result()))

        client.models.generate_content.side_effect = _generate
        mock_client.return_value = client
        transcript = {"segments": [{"start": 1, "duration": 1, "text": "Hello"}]}
        with patch.dict(os.environ, {}, clear=False):
            for var in ("GOOGLE_GENAI_USE_ENTERPRISE", "GOOGLE_GENAI_USE_VERTEXAI", "GEMINI_USE_VERTEXAI", "GEMINI_USE_ENTERPRISE"):
                os.environ.pop(var, None)
            result = analyze_video({"title": "T"}, transcript, "AIza.key", "gemini-2.5-flash", "gemini")
        self.assertEqual(result["summary"], "A summary")
        used = [c.kwargs["model"] for c in client.models.generate_content.call_args_list]
        self.assertEqual(used[0], "gemini-2.5-flash")
        self.assertIn("gemini-3.5-flash-lite", used)

    @patch("llm_service.genai.Client")
    def test_404_all_models_missing_reports_404(self, mock_client):
        client = MagicMock()
        client.vertexai = False
        client.models.generate_content.side_effect = _not_found("models/gemini-9 not found")
        mock_client.return_value = client
        transcript = {"segments": [{"start": 1, "duration": 1, "text": "Hello"}]}
        with self.assertRaisesRegex(AnalysisError, "404") as ctx:
            analyze_video({"title": "T"}, transcript, "AIza.key", "gemini-9", "gemini")
        self.assertIn("GEMINI_MODEL", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
