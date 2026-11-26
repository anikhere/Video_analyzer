import json
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from youtube_service import extract_video_id, fetch_video_metadata, format_duration, YouTubeError
from transcript_service import get_transcript, chunk_transcript, TranscriptError
from llm_service import analyze_video, AnalysisError

ID = "dQw4w9WgXcQ"

class URLTests(unittest.TestCase):
    def test_urls(self):
        for url in [f"youtube.com/watch?v={ID}&t=25", f"https://youtu.be/{ID}?si=x", f"https://www.youtube.com/shorts/{ID}?si=x", f"https://youtube.com/embed/{ID}"]:
            with self.subTest(url=url): self.assertEqual(extract_video_id(url), ID)

    def test_invalid(self):
        for url in ["", "https://youtube.com.evil.com/watch?v=" + ID, "https://evil.com/youtube.com/watch?v=" + ID, f"https://youtube.com/watch?v={ID}&v={ID}", "javascript://youtube.com/watch?v=" + ID, "https://youtu.be/short", f"https://youtube.com/channel/{ID}", f"https://user@youtube.com/watch?v={ID}"]:
            with self.subTest(url=url):
                with self.assertRaises(ValueError): extract_video_id(url)

    def test_duration(self):
        self.assertEqual(format_duration("PT1H2M3S"), "1:02:03")
        self.assertEqual(format_duration("PT3M4S"), "3:04")
        self.assertEqual(format_duration("P1DT1H"), "25:00:00")
        self.assertEqual(format_duration(""), "Unknown")

class YouTubeTests(unittest.TestCase):
    @patch("youtube_service.build")
    def test_metadata(self, build):
        build.return_value.videos.return_value.list.return_value.execute.return_value = {"items": [{"snippet": {"title": "Hello", "channelTitle": "Channel", "thumbnails": {"high": {"url": "https://example.com/image"}}}, "contentDetails": {"duration": "PT10S"}}]}
        data = fetch_video_metadata(ID, "key")
        self.assertEqual(data["title"], "Hello")
        self.assertEqual(data["description"], "")
        self.assertEqual(data["thumbnail"], "https://example.com/image")
        build.return_value.videos.return_value.list.assert_called_once_with(part="snippet,contentDetails", id=ID)

    @patch("youtube_service.build")
    def test_missing_video(self, build):
        build.return_value.videos.return_value.list.return_value.execute.return_value = {"items": []}
        with self.assertRaises(YouTubeError): fetch_video_metadata(ID, "key")

class TranscriptTests(unittest.TestCase):
    @patch("transcript_service.YouTubeTranscriptApi")
    def test_fetch_and_clean(self, api):
        track = api.return_value.list.return_value.find_transcript.return_value
        track.language, track.language_code, track.is_generated = "English", "en", True
        track.fetch.return_value = [SimpleNamespace(text="Hello\n&amp; world", start=1.9, duration=2)]
        data = get_transcript(ID)
        self.assertEqual(data["segments"][0], {"text": "Hello & world", "start": 1.9, "duration": 2.0})
        api.return_value.list.assert_called_once_with(ID)

    @patch("transcript_service.YouTubeTranscriptApi")
    def test_empty(self, api):
        api.return_value.list.return_value.find_transcript.return_value.fetch.return_value = []
        with self.assertRaises(TranscriptError): get_transcript(ID)

    def test_chunks_are_bounded_and_preserve_timestamps(self):
        segments = [{"start": 65, "text": "a" * 200, "duration": 1}, {"start": 70, "text": "last", "duration": 1}]
        chunks = chunk_transcript(segments, max_chars=50)
        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(len(c) <= 50 for c in chunks))
        self.assertIn("[01:05]", chunks[0])
        self.assertIn("[01:10] last", chunks[-1])

class GeminiTests(unittest.TestCase):
    def result(self):
        return {"summary": "A summary", "topics": ["Topic"], "key_takeaways": ["Point"], "timestamps": [{"time": "00:01", "explanation": "Hello"}, {"time": "02:00", "explanation": "Made up"}], "action_items": [], "audience": "Everyone", "terminology": [], "conclusion": "Done"}

    @patch("llm_service.genai.Client")
    def test_single_and_sdk_arguments(self, client):
        client.return_value.models.generate_content.return_value.text = json.dumps(self.result())
        transcript = {"segments": [{"start": 1, "duration": 1, "text": "Hello"}]}
        result = analyze_video({"title": "Title"}, transcript, "secret", "gemini-2.5-flash", "gemini")
        self.assertEqual([t["time"] for t in result["timestamps"]], ["00:01"])
        args = client.return_value.models.generate_content.call_args.kwargs
        self.assertEqual(args["model"], "gemini-2.5-flash")
        self.assertEqual(args["config"].response_mime_type, "application/json")
        self.assertIn("[00:01] Hello", args["contents"])

    @patch("llm_service.genai.Client")
    def test_multi_chunk(self, client):
        client.return_value.models.generate_content.side_effect = [SimpleNamespace(text=json.dumps({"notes": "[00:01] First"})), SimpleNamespace(text=json.dumps({"notes": "[00:02] Second"})), SimpleNamespace(text=json.dumps(self.result()))]
        transcript = {"segments": [{"start": 1, "duration": 1, "text": "a" * 21000}, {"start": 2, "duration": 1, "text": "b" * 21000}]}
        result = analyze_video({}, transcript, "key", "gemini-2.5-flash", "gemini")
        self.assertEqual(result["summary"], "A summary")
        self.assertEqual(client.return_value.models.generate_content.call_count, 3)
        self.assertIn("[00:02] Second", client.return_value.models.generate_content.call_args.kwargs["contents"])

    @patch("llm_service.genai.Client")
    def test_rate_limit(self, client):
        client.return_value.models.generate_content.side_effect = type("RateError", (Exception,), {"code": 429})("secret")
        with self.assertRaisesRegex(AnalysisError, "rate limit") as raised:
            analyze_video({}, {"segments": [{"start": 1, "text": "hi"}]}, "secret", "gemini-2.5-flash", "gemini")
        self.assertNotIn("secret", str(raised.exception))

class OpenRouterTests(unittest.TestCase):
    def completion(self, value, finish_reason="stop"):
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps(value)), finish_reason=finish_reason)])

    def transcript(self):
        return {"segments": [{"start": 1, "duration": 1, "text": "Hello"}]}

    @patch("llm_service.OpenAI")
    def test_openrouter_request_and_result(self, client):
        client.return_value.chat.completions.create.return_value = self.completion(GeminiTests().result())
        result = analyze_video({"title": "Example"}, self.transcript(), "secret")
        client.assert_called_once_with(base_url="https://openrouter.ai/api/v1", api_key="secret", timeout=120.0, max_retries=0)
        kwargs = client.return_value.chat.completions.create.call_args.kwargs
        self.assertEqual(kwargs["model"], "openrouter/free")
        self.assertEqual(kwargs["response_format"], {"type": "json_object"})
        self.assertIn("JSON Schema", kwargs["messages"][0]["content"])
        self.assertIn("[00:01] Hello", kwargs["messages"][1]["content"])
        self.assertEqual([t["time"] for t in result["timestamps"]], ["00:01"])

    @patch("llm_service.OpenAI")
    def test_chunked_openrouter(self, client):
        client.return_value.chat.completions.create.side_effect = [self.completion({"notes": "[00:01] First"}), self.completion({"notes": "[00:02] Second"}), self.completion(GeminiTests().result())]
        segments = [{"start": 1, "text": "a" * 21000}, {"start": 2, "text": "b" * 21000}]
        self.assertEqual(analyze_video({}, {"segments": segments}, "key")["summary"], "A summary")
        self.assertEqual(client.return_value.chat.completions.create.call_count, 3)
        self.assertIn("[00:02] Second", client.return_value.chat.completions.create.call_args.kwargs["messages"][1]["content"])

    @patch("llm_service.OpenAI")
    def test_status_code_takes_precedence_over_sdk_code(self, client):
        err = type("APIError", (Exception,), {"status_code": 401, "code": "invalid_api_key"})("sensitive")
        client.return_value.chat.completions.create.side_effect = err
        with self.assertRaisesRegex(AnalysisError, "API key.*401") as raised:
            analyze_video({}, self.transcript(), "secret")
        self.assertNotIn("sensitive", str(raised.exception))
        self.assertNotIn("secret", str(raised.exception))

    @patch("llm_service.OpenAI")
    def test_invalid_and_truncated_response(self, client):
        client.return_value.chat.completions.create.return_value = self.completion({"unexpected": 1})
        with self.assertRaisesRegex(AnalysisError, "invalid analysis format"):
            analyze_video({}, self.transcript(), "key")
        client.return_value.chat.completions.create.return_value = self.completion({}, "length")
        with self.assertRaisesRegex(AnalysisError, "truncated"):
            analyze_video({}, self.transcript(), "key")

    def test_invalid_provider(self):
        with self.assertRaisesRegex(AnalysisError, "LLM_PROVIDER"):
            analyze_video({}, self.transcript(), "key", provider="other")

if __name__ == "__main__": unittest.main()
