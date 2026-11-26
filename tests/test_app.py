import os
import unittest
from unittest.mock import patch
from streamlit.testing.v1 import AppTest

ID = "dQw4w9WgXcQ"
META = {"id": ID, "title": "Example", "channel": "Creator", "description": "Description", "published_at": "2024-01-01T00:00:00Z", "thumbnail": None, "duration": "PT1M", "url": "https://www.youtube.com/watch?v=" + ID}
TRANSCRIPT = {"segments": [{"start": 1, "duration": 1, "text": "Hello"}], "language": "English", "language_code": "en", "is_generated": False}
ANALYSIS = {"summary": "A grounded summary", "topics": ["Topic"], "key_takeaways": ["Takeaway"], "timestamps": [{"time": "00:01", "explanation": "Hello"}], "action_items": ["Act"], "audience": "Everyone", "terminology": [{"term": "Term", "explanation": "Meaning"}], "conclusion": "Done"}

class AppTests(unittest.TestCase):
    def test_no_keys(self):
        with patch.dict(os.environ, {"YT_KEY": "", "OPENROUTER_API_KEY": "", "LLM_PROVIDER": "openrouter"}):
            app = AppTest.from_file("../app.py").run()
            app.text_input[0].input("https://youtu.be/" + ID)
            app.button[0].click().run()
            self.assertFalse(app.exception)
            self.assertIn("YT_KEY", app.error[0].value)

    def test_full_mocked_flow(self):
        with patch.dict(os.environ, {"YT_KEY": "test-youtube", "OPENROUTER_API_KEY": "test-openrouter", "LLM_PROVIDER": "openrouter"}), patch("youtube_service.fetch_video_metadata", return_value=META) as metadata, patch("transcript_service.get_transcript", return_value=TRANSCRIPT) as transcript, patch("llm_service.analyze_video", return_value=ANALYSIS) as analysis:
            app = AppTest.from_file("../app.py").run()
            app.text_input[0].input("https://youtu.be/" + ID)
            app.button[0].click().run()
            self.assertFalse(app.exception)
            self.assertFalse(app.error)
            self.assertTrue(any("A grounded summary" in m.value for m in app.markdown))
            self.assertTrue(any("Transcript" in h.value for h in app.header))
            metadata.assert_called_once()
            transcript.assert_called_once()
            analysis.assert_called_once()

    def test_transcript_unavailable(self):
        from transcript_service import TranscriptError
        with patch.dict(os.environ, {"YT_KEY": "another-youtube", "OPENROUTER_API_KEY": "another-openrouter", "LLM_PROVIDER": "openrouter"}), patch("youtube_service.fetch_video_metadata", return_value=META), patch("transcript_service.get_transcript", side_effect=TranscriptError("Captions unavailable")), patch("llm_service.analyze_video") as analysis:
            app = AppTest.from_file("../app.py").run()
            app.text_input[0].input("https://youtu.be/abcdefghijk")
            app.button[0].click().run()
            self.assertFalse(app.exception)
            self.assertIn("Captions unavailable", app.error[0].value)
            analysis.assert_not_called()

    def test_gemini_provider_uses_gemini_key_and_model(self):
        with patch.dict(os.environ, {"YT_KEY": "yt-gemini-test", "GEMINI_API_KEY": "gemini-key", "GEMINI_MODEL": "gemini-custom", "OPENROUTER_API_KEY": "other-key", "LLM_PROVIDER": "gemini"}), patch("youtube_service.fetch_video_metadata", return_value=META), patch("transcript_service.get_transcript", return_value=TRANSCRIPT), patch("llm_service.analyze_video", return_value=ANALYSIS) as analysis:
            app = AppTest.from_file("../app.py").run()
            app.text_input[0].input("https://youtu.be/12345678901")
            app.button[0].click().run()
            self.assertFalse(app.exception)
            self.assertFalse(app.error)
            self.assertEqual(analysis.call_args.args[2:], ("gemini-key", "gemini-custom", "gemini"))

    def test_invalid_provider(self):
        with patch.dict(os.environ, {"YT_KEY": "yt", "LLM_PROVIDER": "wrong"}):
            app = AppTest.from_file("../app.py").run()
            app.text_input[0].input("https://youtu.be/" + ID)
            app.button[0].click().run()
            self.assertIn("LLM_PROVIDER", app.error[0].value)
