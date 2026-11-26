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
        with patch.dict(os.environ, {"YT_KEY": "", "GEMINI_API_KEY": ""}):
            app = AppTest.from_file("../app.py").run()
            app.text_input[0].input("https://youtu.be/" + ID)
            app.button[0].click().run()
            self.assertFalse(app.exception)
            self.assertIn("YT_KEY", app.error[0].value)

    def test_full_mocked_flow(self):
        with patch.dict(os.environ, {"YT_KEY": "test-youtube", "GEMINI_API_KEY": "test-gemini"}), patch("youtube_service.fetch_video_metadata", return_value=META) as metadata, patch("transcript_service.get_transcript", return_value=TRANSCRIPT) as transcript, patch("llm_service.analyze_video", return_value=ANALYSIS) as analysis:
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
        with patch.dict(os.environ, {"YT_KEY": "another-youtube", "GEMINI_API_KEY": "another-gemini"}), patch("youtube_service.fetch_video_metadata", return_value=META), patch("transcript_service.get_transcript", side_effect=TranscriptError("Captions unavailable")), patch("llm_service.analyze_video") as analysis:
            app = AppTest.from_file("../app.py").run()
            app.text_input[0].input("https://youtu.be/abcdefghijk")
            app.button[0].click().run()
            self.assertFalse(app.exception)
            self.assertIn("Captions unavailable", app.error[0].value)
            analysis.assert_not_called()
