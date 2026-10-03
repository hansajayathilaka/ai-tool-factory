"""Unit tests for utils/. Run from app/: python -m unittest discover -s utils/tests"""
from __future__ import annotations

import io
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

UTILS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(UTILS))

import common  # noqa: E402
import insights_summary  # noqa: E402
import move_post  # noqa: E402
import rss_fetch  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures"

VALID_POST = """---
page: demo
topic: Moon ocean
pillar: Space
post_type: news
language: en
created: 2026-10-01
posted:
sources:
  - url: https://science.nasa.gov/some-article
    title: "Moon may hide an ocean: new data"
    accessed: 2026-10-01
  - url: https://www.bbc.com/news/science-123
    title: BBC report
    accessed: 2026-10-01
image:
  kind: stock
  idea: icy moon illustration # keywords
  needs_ai_label: false
fact_check: {fact_check}
---

## Caption
{caption}

## Hashtags
#ScienceExplained

## Alternatives
Shorter: Water on a tiny moon?

## Reviewer notes
- "liquid water may exist" → [1]
"""
CAPTION = ("A tiny moon may be hiding an ocean. Scientists studying new telescope images "
           "think there could be liquid water.")


class PageTestCase(unittest.TestCase):
    """Runs each test against a temporary facebook_pages/ folder."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.page = self.tmp / "demo"
        for folder in (*common.STATUS_FOLDERS, "research", "insights"):
            (self.page / folder).mkdir(parents=True)
        patcher = mock.patch.object(common, "PAGES_DIR", self.tmp)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(shutil.rmtree, self.tmp)

    def write_post(self, status="drafts", name="2026-10-01-moon-ocean.md", fact_check="pending", caption=CAPTION):
        path = self.page / status / name
        path.write_text(VALID_POST.format(fact_check=fact_check, caption=caption), encoding="utf-8")
        return path


class FrontmatterTests(unittest.TestCase):
    def test_parse_post(self):
        block, body = common.split_frontmatter(VALID_POST.format(fact_check="pending", caption=CAPTION))
        fm = common.parse_frontmatter(block)
        self.assertEqual(fm["topic"], "Moon ocean")
        self.assertIsNone(fm["posted"])
        self.assertEqual(len(fm["sources"]), 2)
        self.assertEqual(fm["sources"][0]["title"], "Moon may hide an ocean: new data")
        self.assertEqual(fm["sources"][0]["url"], "https://science.nasa.gov/some-article")
        self.assertEqual(fm["image"], {"kind": "stock", "idea": "icy moon illustration", "needs_ai_label": False})
        self.assertIn("Caption", common.sections(body))

    def test_parse_template_files(self):
        for name in ("post.md", "research_note.md"):
            fm, _ = common.read_post(common.TEMPLATES_DIR / name)
            self.assertIsInstance(fm["sources"], list, name)

    def test_set_field_keeps_rest(self):
        text = VALID_POST.format(fact_check="pending", caption=CAPTION)
        new = common.set_field(text, "posted", "2026-10-02")
        self.assertIn("posted: 2026-10-02\n", new)
        self.assertEqual(new.replace("posted: 2026-10-02", "posted:"), text)
        self.assertIn("fact_check: passed", common.set_field(text, "fact_check", "passed"))


class ValidateTests(PageTestCase):
    def test_valid_draft(self):
        errors, warnings = common.validate_post(self.write_post())
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_template_is_invalid(self):
        path = self.page / "drafts" / "2026-10-01-template.md"
        shutil.copy(common.TEMPLATES_DIR / "post.md", path)
        errors, _ = common.validate_post(path)
        self.assertTrue(any("placeholder" in e for e in errors), errors)
        self.assertTrue(any("created" in e for e in errors), errors)

    def test_finalized_needs_passed(self):
        errors, _ = common.validate_post(self.write_post(status="finalized"))
        self.assertTrue(any("fact_check: passed" in e for e in errors), errors)

    def test_engagement_bait_warning(self):
        _, warnings = common.validate_post(self.write_post(caption="Big news! Share if you agree."))
        self.assertTrue(any("share if" in w for w in warnings), warnings)

    def test_bad_filename(self):
        errors, _ = common.validate_post(self.write_post(name="Moon Ocean.md"))
        self.assertTrue(any("filename" in e for e in errors), errors)


class MovePostTests(PageTestCase):
    def run_move(self, *argv):
        with mock.patch.object(sys, "argv", ["move_post.py", *argv]), redirect_stdout(io.StringIO()):
            move_post.main()

    def test_finalize_requires_approval_and_pass(self):
        path = self.write_post(fact_check="passed")
        with self.assertRaises(SystemExit):
            self.run_move("finalize", str(path))
        self.write_post(name="2026-10-01-other.md")
        with self.assertRaises(SystemExit):
            self.run_move("finalize", str(self.page / "drafts" / "2026-10-01-other.md"), "--approved")
        self.run_move("finalize", str(path), "--approved")
        self.assertTrue((self.page / "finalized" / path.name).is_file())
        self.assertFalse(path.exists())

    def test_full_lifecycle(self):
        path = self.write_post(fact_check="passed")
        self.run_move("finalize", path.name, "--approved")
        self.run_move("reopen", path.name)
        fm, _ = common.read_post(self.page / "drafts" / path.name)
        self.assertEqual(fm["fact_check"], "pending")
        with self.assertRaises(SystemExit):  # a reopened post must pass the fact-check again
            self.run_move("finalize", path.name, "--approved")
        (self.page / "drafts" / path.name).write_text(
            VALID_POST.format(fact_check="passed", caption=CAPTION), encoding="utf-8")
        self.run_move("finalize", path.name, "--approved")
        self.run_move("posted", path.name, "--date", "2026-10-03")
        posted = self.page / "posted" / path.name
        fm, _ = common.read_post(posted)
        self.assertEqual(fm["posted"], "2026-10-03")
        self.assertEqual(common.validate_post(posted)[0], [])

    def test_posted_rejects_bad_dates(self):
        self.write_post(status="finalized", fact_check="passed")
        for bad in ("2026-13-01", "2026-09-01"):  # invalid; before created
            with self.assertRaises(SystemExit):
                self.run_move("posted", "2026-10-01-moon-ocean.md", "--date", bad)

    def test_refuses_wrong_folder(self):
        path = self.write_post(status="posted", fact_check="passed")
        with self.assertRaises(SystemExit):
            self.run_move("finalize", str(path), "--approved")


class InsightsTests(PageTestCase):
    def test_summary_matches_posted_files(self):
        path = self.write_post(status="posted", fact_check="passed")
        path.write_text(common.set_field(path.read_text(encoding="utf-8"), "posted", "2026-10-01"), encoding="utf-8")
        rows = insights_summary.read_rows(FIXTURES / "meta_export.csv", {}, insights_summary.load_posted("demo"))
        self.assertEqual(len(rows), 3)  # description row skipped
        moon = rows[0]
        self.assertEqual(moon["file"], path.name)
        self.assertEqual(moon["pillar"], "Space")
        self.assertEqual(moon["reach"], 1200)
        self.assertEqual(moon["engagement"], 96)
        self.assertAlmostEqual(moon["rate"], 0.08)
        self.assertIsNone(rows[1]["file"])
        report = insights_summary.summarize("demo", FIXTURES / "meta_export.csv", rows)
        self.assertIn("| Space ⚠ small sample | 1 |", report)
        self.assertIn("Unmatched posts (2)", report)

    def test_missing_columns_explains(self):
        with self.assertRaises(SystemExit) as ctx:
            insights_summary.detect_columns(["foo", "bar"], {})
        self.assertIn("CSV headers", str(ctx.exception))


class RssTests(unittest.TestCase):
    def test_rss_and_atom(self):
        rss = b"""<rss><channel><item><title>A</title><link>https://a.example/1</link>
            <pubDate>Wed, 01 Oct 2026 10:00:00 GMT</pubDate><description>&lt;p&gt;Hi &amp;amp; bye&lt;/p&gt;</description>
            </item></channel></rss>"""
        items = rss_fetch.parse(rss)
        self.assertEqual(items[0]["title"], "A")
        self.assertEqual(items[0]["date"].year, 2026)
        self.assertEqual(items[0]["summary"], "Hi & bye")
        atom = b"""<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>B</title>
            <link href="https://b.example/2"/><updated>2026-10-02T08:00:00Z</updated></entry></feed>"""
        items = rss_fetch.parse(atom)
        self.assertEqual(items[0]["link"], "https://b.example/2")
        self.assertEqual(items[0]["date"].day, 2)

    def test_feeds_from_test_page(self):
        feeds = rss_fetch.feeds_from_sources("_test")
        self.assertTrue(feeds)
        self.assertTrue(all(url.startswith("https://") for _, url in feeds))


if __name__ == "__main__":
    unittest.main()
