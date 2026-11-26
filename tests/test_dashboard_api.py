import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

import api
from analytics_service import build_dashboard_analytics
from llm_service import analyze_video_dashboard
from transcript_service import TranscriptBlockedError, compact_segments, parse_pasted_transcript
from youtube_service import duration_to_seconds, fetch_video_metadata_smart, seconds_to_iso_duration

VID = "dQw4w9WgXcQ"


class LowApiPipelineTests(unittest.TestCase):
    def test_compact_segments_preserves_exact_start_timestamps(self):
        segs = [
            {"start": 2.0, "duration": 2.0, "text": "First short caption."},
            {"start": 4.5, "duration": 2.0, "text": "Second short caption."},
            {"start": 25.0, "duration": 3.0, "text": "Later section begins here."},
        ]
        compacted = compact_segments(segs, window_seconds=14.0)
        self.assertEqual(len(compacted), 2)
        self.assertEqual(compacted[0]["start"], 2.0)
        self.assertIn("First short caption. Second short caption.", compacted[0]["text"])
        self.assertEqual(compacted[1]["start"], 25.0)

    @patch("youtube_service.urlopen")
    def test_zero_key_oembed_fallback_uses_zero_youtube_api_calls(self, mock_urlopen):
        from unittest.mock import MagicMock

        mock_resp = MagicMock()
        mock_resp.__enter__.return_value = mock_resp
        mock_resp.read.return_value = json.dumps(
            {
                "title": "Zero Key Video",
                "author_name": "Tech Channel",
                "thumbnail_url": "https://i.ytimg.com/vi/dQw4w9WgXcQ/hqdefault.jpg",
            }
        ).encode("utf-8")
        mock_urlopen.return_value = mock_resp
        meta, yt_calls = fetch_video_metadata_smart(VID, api_key="")
        self.assertEqual(yt_calls, 0)
        self.assertEqual(meta["title"], "Zero Key Video")
        self.assertEqual(meta["channel"], "Tech Channel")
        self.assertEqual(meta["metadata_source"], "oembed")

    def test_duration_roundtrip(self):
        self.assertEqual(duration_to_seconds("PT18M42S"), 1122)
        self.assertEqual(seconds_to_iso_duration(1122), "PT18M42S")

    @patch("llm_service.OpenAI")
    def test_single_pass_dashboard_analysis_uses_one_llm_call_for_medium_long_video(self, mock_openai):
        dashboard_payload = {
            "tldr": "Core thesis in one sentence.",
            "content_type": "Technical Deep Dive",
            "summary": "Detailed overview of the entire video.",
            "premise": "Why this topic matters.",
            "core_breakdown": "Step-by-step walkthrough.",
            "topics": ["Transformers", "Attention"],
            "key_takeaways": ["Attention mixes context across tokens."],
            "chapters": [
                {"start_time": "00:01", "title": "Opening", "summary": "Intro"},
                {"start_time": "05:00", "title": "Main", "summary": "Body"},
            ],
            "timestamps": [
                {"time": "00:01", "explanation": "Opening claim"},
                {"time": "99:99", "explanation": "Hallucinated timestamp must be stripped"},
            ],
            "action_items": ["Apply temperature=0 for deterministic tasks."],
            "audience": "Engineers",
            "terminology": [{"term": "Attention", "explanation": "Context passing mechanism."}],
            "conclusion": "Final synthesis.",
        }
        mock_openai.return_value.chat.completions.create.return_value = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps(dashboard_payload)), finish_reason="stop")]
        )
        # 42,000 chars previously took 3 LLM calls; now fits in 1 single LLM call!
        segments = [
            {"start": 1.0, "duration": 10.0, "text": "Attention " * 2100},
            {"start": 300.0, "duration": 10.0, "text": "Transformers " * 1700},
        ]
        result, calls = analyze_video_dashboard({"title": "Demo"}, {"segments": segments}, "secret-key")
        self.assertEqual(calls, 1)
        self.assertEqual([t["time"] for t in result["timestamps"]], ["00:01"])
        self.assertEqual(len(result["chapters"]), 2)

    def test_analytics_computation_is_grounded(self):
        meta = {"id": VID, "title": "Demo", "duration": "PT2M", "view_count": 1000, "like_count": 80, "comment_count": 20}
        transcript = {
            "segments": [
                {"start": 0.0, "duration": 30.0, "text": "Neural networks use attention layers to model sequence tokens accurately."},
                {"start": 60.0, "duration": 30.0, "text": "Attention weights let tokens share context inside neural networks."},
            ],
            "language": "English",
            "language_code": "en",
            "is_generated": False,
        }
        analysis = {
            "tldr": "Short thesis.",
            "summary": "Summary text.",
            "premise": "Premise.",
            "core_breakdown": "Breakdown.",
            "conclusion": "Conclusion.",
            "topics": ["Attention"],
            "key_takeaways": ["Point 1"],
            "action_items": ["Step 1"],
            "terminology": [{"term": "Neural", "explanation": "Network"}],
            "chapters": [
                {"start_time": "00:00", "title": "Part 1", "summary": "First half"},
                {"start_time": "01:00", "title": "Part 2", "summary": "Second half"},
            ],
            "timestamps": [{"time": "01:00", "explanation": "Context sharing"}],
        }
        analytics = build_dashboard_analytics(meta, transcript, analysis)
        self.assertEqual(analytics["kpis"]["duration_seconds"], 120)
        self.assertEqual(analytics["kpis"]["engagement_rate"], 10.0)
        self.assertEqual(len(analytics["chapters"]), 2)
        self.assertEqual(analytics["chapters"][0]["share_pct"], 50.0)
        self.assertGreater(len(analytics["pace_series"]), 0)
        self.assertGreater(len(analytics["concept_frequency"]), 0)


class FastApiEndpointTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.orig_cache = api.cache
        api.cache = api.PersistentCache(Path(self.tmp.name) / "test_cache.sqlite")
        self.client = TestClient(api.app)

    def tearDown(self):
        api.cache = self.orig_cache
        self.tmp.cleanup()

    def test_samples_and_config_endpoints(self):
        res = self.client.get("/api/samples")
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertGreaterEqual(len(body["samples"]), 2)
        self.assertIn("analytics", body["default_sample"])

        cfg = self.client.get("/api/config")
        self.assertEqual(cfg.status_code, 200)
        self.assertTrue(cfg.json()["zero_yt_key_supported"])

    @patch("api.fetch_video_metadata_smart")
    @patch("api.get_transcript")
    @patch("api.analyze_video_dashboard")
    def test_analyze_endpoint_parallel_and_cached_zero_repeat_calls(self, mock_llm, mock_trans, mock_meta):
        mock_meta.return_value = (
            {
                "id": VID,
                "title": "Fast Video",
                "channel": "Creator",
                "description": "",
                "published_at": "2025-01-10T00:00:00Z",
                "thumbnail": "https://example.com/t.jpg",
                "duration": "PT3M",
                "duration_seconds": 180,
                "view_count": 5000,
                "like_count": 250,
                "comment_count": 25,
                "metadata_source": "oembed",
                "url": f"https://www.youtube.com/watch?v={VID}",
            },
            0,
        )
        mock_trans.return_value = {
            "segments": [{"start": 5.0, "duration": 4.0, "text": "FastAPI and React dashboard architecture."}],
            "language": "English",
            "language_code": "en",
            "is_generated": False,
        }
        mock_llm.return_value = (
            {
                "tldr": "Fast architecture.",
                "content_type": "Tutorial",
                "summary": "Summary.",
                "premise": "Premise.",
                "core_breakdown": "Breakdown.",
                "topics": ["FastAPI"],
                "key_takeaways": ["Single LLM call."],
                "chapters": [{"start_time": "00:05", "title": "Architecture", "summary": "Overview"}],
                "timestamps": [{"time": "00:05", "explanation": "Intro"}],
                "action_items": ["Deploy"],
                "audience": "Developers",
                "terminology": [{"term": "FastAPI", "explanation": "Python web framework"}],
                "conclusion": "Done.",
            },
            1,
        )

        with patch.dict(os.environ, {"YT_KEY": "", "OPENROUTER_API_KEY": ""}):
            first = self.client.post("/api/analyze", json={"url": f"https://youtu.be/{VID}", "api_key": "runtime-or-key"})
            self.assertEqual(first.status_code, 200)
            first_json = first.json()
            self.assertFalse(first_json["telemetry"]["cached"])
            self.assertEqual(first_json["telemetry"]["llm_calls"], 1)
            self.assertEqual(first_json["telemetry"]["youtube_api_calls"], 0)

            # Repeat call hits persistent cache -> 0 external API calls!
            second = self.client.post("/api/analyze", json={"url": f"https://youtu.be/{VID}", "api_key": "runtime-or-key"})
            self.assertEqual(second.status_code, 200)
            second_json = second.json()
            self.assertTrue(second_json["telemetry"]["cached"])
            self.assertEqual(second_json["telemetry"]["llm_calls"], 0)
            self.assertEqual(mock_llm.call_count, 1)
            self.assertEqual(mock_trans.call_count, 1)
            self.assertEqual(mock_meta.call_count, 1)

    @patch("api.fetch_video_metadata_smart")
    @patch("api.get_transcript")
    @patch("api.analyze_youtube_url_via_gemini")
    def test_cloud_ip_block_automatically_falls_back_to_gemini_direct_url(self, mock_gemini_direct, mock_trans, mock_meta):
        mock_meta.return_value = (
            {
                "id": VID,
                "title": "Render Cloud Video",
                "channel": "Creator",
                "description": "",
                "published_at": "",
                "thumbnail": "https://example.com/t.jpg",
                "duration": "PT2M",
                "duration_seconds": 120,
                "view_count": None,
                "like_count": None,
                "comment_count": None,
                "metadata_source": "oembed",
                "url": f"https://www.youtube.com/watch?v={VID}",
            },
            0,
        )
        mock_trans.side_effect = TranscriptBlockedError("YouTube blocked cloud IP")
        mock_gemini_direct.return_value = (
            {
                "tldr": "Direct Gemini bypass works on Render.",
                "content_type": "Deep Dive",
                "summary": "Summary from direct video ingestion.",
                "premise": "Cloud IPs are blocked by YouTube scraper.",
                "core_breakdown": "Gemini reads YouTube directly.",
                "topics": ["Cloud Deployment"],
                "key_takeaways": ["No proxy required with Gemini."],
                "chapters": [{"start_time": "00:00", "title": "Start", "summary": "Intro"}],
                "timestamps": [{"time": "00:10", "explanation": "Key point"}],
                "action_items": ["Set GEMINI_API_KEY"],
                "audience": "Teams",
                "terminology": [{"term": "Cloud IP", "explanation": "Datacenter network"}],
                "conclusion": "Solved.",
            },
            {
                "segments": [{"start": 0.0, "duration": 15.0, "text": "Direct Gemini audio transcript segment."}],
                "language": "English (Direct Audio/Video)",
                "language_code": "en",
                "is_generated": True,
            },
            1,
        )
        res = self.client.post(
            "/api/analyze",
            json={"url": f"https://youtu.be/{VID}", "provider": "gemini", "api_key": "gem-key", "force_refresh": True},
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["analysis"]["tldr"], "Direct Gemini bypass works on Render.")
        mock_gemini_direct.assert_called_once()

    def test_parse_pasted_transcript_handles_two_line_youtube_format(self):
        raw = "0:00\nWelcome everyone to the video briefing.\n0:14\nHere is the second spoken timestamped block."
        parsed = parse_pasted_transcript(raw)
        self.assertEqual(len(parsed["segments"]), 2)
        self.assertEqual(parsed["segments"][0]["start"], 0.0)
        self.assertEqual(parsed["segments"][1]["start"], 14.0)


if __name__ == "__main__":
    unittest.main()
