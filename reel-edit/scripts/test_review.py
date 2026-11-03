"""Regression checks for source-time cut review. Run with python -m unittest discover -s scripts -p test_review.py."""
import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import review


class CutReviewTests(unittest.TestCase):
    def setUp(self):
        self.clip = {"id": "take", "path": "raw.mov", "duration": 4,
                     "keeps": [{"src": 1, "frames": 60, "master": 0, "raw_from": 0.98, "raw_to": 2.96}]}
        lane = [{"clip": "take", "src": 1, "len": 60, "at": 0}]
        self.ai = {"fps": 30, "lanes": {"voice": lane, "screen": copy.deepcopy(lane)}}
        self.data = {"name": "test", "clips": [self.clip], "phrases": [], "output": "test.mp4",
                     "snapshot": "baseline.mp4", "baseline_sha256": "example"}

    def test_restored_handles_use_raw_and_original_keep_uses_finished_picture(self):
        parts = review.parts_for(self.clip, 0.9, 66, "baseline.mp4")
        self.assertEqual([p[0] for p in parts], ["raw.mov", "baseline.mp4", "raw.mov"])
        self.assertEqual([p[2] for p in parts], [3, 60, 3])
        self.assertAlmostEqual(parts[0][1], 0.88)
        self.assertAlmostEqual(parts[2][1], 2.96)

    def test_rounding_maps_back_to_original_fractional_endpoints(self):
        self.assertAlmostEqual(review.raw_time(self.clip, 1), 0.98)
        self.assertAlmostEqual(review.raw_time(self.clip, 3), 2.96)
        self.assertAlmostEqual(review.raw_time(self.clip, 1.1), 1.079)

    def test_save_rejects_unlinked_lanes_holes_and_outside_take(self):
        review.validate(self.ai, self.data)
        bad = copy.deepcopy(self.ai)
        bad["lanes"]["voice"][0]["src"] = 2
        with self.assertRaises(ValueError):
            review.validate(bad, self.data)
        for lane in bad["lanes"].values():
            lane[0]["at"] = 3
        with self.assertRaises(ValueError):
            review.validate(bad, self.data)
        for lane in bad["lanes"].values():
            lane[0].update(at=0, src=3)
        with self.assertRaises(ValueError):
            review.validate(bad, self.data)

    def test_internal_deletion_restoration_and_split_do_not_lose_ranges(self):
        self.assertEqual(review.subtract([[1, 3]], [[1, 1.5], [1.7, 3]]), [[1.5, 1.7]])
        split = [{"clip": "take", "src": 1, "len": 30, "at": 0},
                 {"clip": "take", "src": 2, "len": 30, "at": 30}]
        self.assertEqual(review.ranges(split), {"take": [[1, 3]]})

    def test_feedback_distinguishes_head_trim_and_restoration_and_export_history(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            review.write(folder / "review/project.json", self.data)
            review.write(folder / "review/timeline.ai.json", self.ai)
            cut = copy.deepcopy(self.ai)
            for lane in cut["lanes"].values():
                lane[0].update(src=1.1, len=57)
            result = review.feedback(folder, cut)
            self.assertEqual(result["state"], "draft")
            self.assertEqual(result["he_cut"][0]["edge"], "head")
            self.assertAlmostEqual(result["he_cut"][0]["source_from"], 0.98)
            self.assertAlmostEqual(result["he_cut"][0]["source_to"], 1.079)
            with patch.object(review, "SKILL", folder):
                review.feedback(folder, cut, folder / "reviewed.mp4")
            self.assertEqual(len(list((folder / "history").glob("*.json"))), 1)
            for lane in cut["lanes"].values():
                lane[0].update(src=0.9, len=63)
            result = review.feedback(folder, cut)
            self.assertAlmostEqual(result["he_restored"][0]["source_from"], 0.88)
            self.assertAlmostEqual(result["he_restored"][0]["source_to"], 0.98)

    def test_real_media_concatenation_preserves_frame_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, output = Path(tmp) / "source.mp4", Path(tmp) / "cut.mp4"
            review.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "testsrc2=s=90x160:r=30:d=1",
                        "-f", "lavfi", "-i", "sine=frequency=400:sample_rate=48000:duration=1",
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", str(source)])
            review.encode_parts([(source, 0.1, 6), (source, 0.6, 9)], output, width=90)
            self.assertEqual(review.nframes(output), 15)
            streams = review.probe(output)["streams"]
            self.assertLessEqual(abs(float(streams[0]["duration"]) - float(streams[1]["duration"])), 0.04)

    def test_phone_rotation_is_not_applied_twice_after_concat(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, rotated, output = [Path(tmp) / n for n in ("source.mp4", "phone.mp4", "cut.mp4")]
            review.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "testsrc2=s=160x90:r=30:d=1",
                        "-f", "lavfi", "-i", "sine=frequency=400:sample_rate=48000:duration=1",
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", str(source)])
            review.run(["ffmpeg", "-y", "-v", "error", "-display_rotation:v:0", "90", "-i", str(source),
                        "-c", "copy", str(rotated)])
            review.encode_parts([(rotated, 0, 6), (source, 0, 9)], output, width=90)
            stream = next(s for s in review.probe(output)["streams"] if s["codec_type"] == "video")
            self.assertEqual((stream["width"], stream["height"]), (90, 160))
            self.assertFalse(any(s.get("rotation", 0) for s in stream.get("side_data_list", [])))


if __name__ == "__main__":
    unittest.main()
