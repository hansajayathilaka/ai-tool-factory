"""Unit tests for core/. Run from the repo root: python -m unittest discover -s core/tests"""
from __future__ import annotations

import copy
import io
import json
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from core import cli, common, export, factory, insights, lifecycle, mcp, scaffold  # noqa: E402
from core.frontmatter import parse_frontmatter, read_item, sections, set_field, split_frontmatter  # noqa: E402
from core.sources import rss  # noqa: E402
from core.tool import Tool, check_manifest  # noqa: E402
from core.validate import validate_item  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures"
FACEBOOK = common.TOOLS_DIR / "facebook"
FB_MANIFEST = json.loads((FACEBOOK / "tool.json").read_text(encoding="utf-8"))

VALID_ITEM = """---
channel: demo
topic: Moon ocean
pillar: Space
item_type: news
language: en
created: 2026-10-01
published:
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


def quiet(fn, *args, **kwargs):
    with redirect_stdout(io.StringIO()):
        return fn(*args, **kwargs)


class ToolTestCase(unittest.TestCase):
    """Runs each test against a temporary copy of the facebook tool with one channel, 'demo'."""
    manifest = FB_MANIFEST

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        self.tool_dir = self.tmp / "facebook"
        shutil.copytree(FACEBOOK / "templates", self.tool_dir / "templates")
        (self.tool_dir / "tool.json").write_text(json.dumps(self.manifest), encoding="utf-8")
        self.channel = self.tool_dir / "channels" / "demo"
        for folder in common.CHANNEL_FOLDERS:
            (self.channel / folder).mkdir(parents=True)
        self.tool = Tool.load(self.tool_dir)

    def write_item(self, status="drafts", name="2026-10-01-moon-ocean.md", fact_check="pending",
                   caption=CAPTION, text=None):
        path = self.channel / status / name
        path.write_text(text or VALID_ITEM.format(fact_check=fact_check, caption=caption), encoding="utf-8")
        return path

    def validate(self, *args, **kwargs):
        return validate_item(self.tool, self.write_item(*args, **kwargs))


class FrontmatterTests(unittest.TestCase):
    def test_parse_item(self):
        block, body = split_frontmatter(VALID_ITEM.format(fact_check="pending", caption=CAPTION))
        fm = parse_frontmatter(block)
        self.assertEqual(fm["topic"], "Moon ocean")
        self.assertIsNone(fm["published"])
        self.assertEqual(len(fm["sources"]), 2)
        self.assertEqual(fm["sources"][0]["title"], "Moon may hide an ocean: new data")
        self.assertEqual(fm["sources"][0]["url"], "https://science.nasa.gov/some-article")
        self.assertEqual(fm["image"], {"kind": "stock", "idea": "icy moon illustration", "needs_ai_label": False})
        self.assertIn("Caption", sections(body))

    def test_parse_template_files(self):
        templates = [common.SHARED_DIR / "research_note.md", common.TOOL_TEMPLATE_DIR / "templates" / "item.md"]
        templates += [d / "templates" / "item.md" for d in factory.tool_dirs()]
        for path in templates:
            fm, _ = read_item(path)
            self.assertIsInstance(fm["sources"], list, path)

    def test_set_field_keeps_rest(self):
        text = VALID_ITEM.format(fact_check="pending", caption=CAPTION)
        new = set_field(text, "published", "2026-10-02")
        self.assertIn("published: 2026-10-02\n", new)
        self.assertEqual(new.replace("published: 2026-10-02", "published:"), text)
        self.assertIn("fact_check: passed", set_field(text, "fact_check", "passed"))


class ManifestTests(unittest.TestCase):
    def test_facebook_manifest_is_valid(self):
        self.assertEqual(check_manifest(FB_MANIFEST), [])

    def test_problems_are_reported(self):
        bad = copy.deepcopy(FB_MANIFEST)
        bad["name"] = "Face Book"
        bad["nouns"].pop("platform")
        bad["main_section"] = "Body"
        bad["sections"][0]["max_chars"] = "lots"
        bad["rules"]["image"] = "sometimes"
        bad["export"]["sections"] = ["Nope"]
        bad["colour"] = "blue"
        problems = "\n".join(check_manifest(bad))
        for expected in ("name must be", "nouns.platform", "main_section", "max_chars", "rules.image",
                         "export.sections", "unknown key: colour"):
            self.assertIn(expected, problems)

    def test_load_refuses_invalid_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "tool.json").write_text('{"name": "x"}', encoding="utf-8")
            with self.assertRaises(SystemExit) as ctx:
                Tool.load(Path(tmp))
            self.assertIn("has problems", str(ctx.exception))


class ValidateTests(ToolTestCase):
    def test_valid_draft(self):
        errors, warnings = self.validate()
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_template_is_invalid(self):
        path = self.channel / "drafts" / "2026-10-01-template.md"
        shutil.copy(self.tool.templates_dir / "item.md", path)
        errors, _ = validate_item(self.tool, path)
        self.assertTrue(any("placeholder" in e for e in errors), errors)
        self.assertTrue(any("created" in e for e in errors), errors)

    def test_finalized_needs_passed(self):
        errors, _ = self.validate(status="finalized")
        self.assertTrue(any("fact_check: passed" in e for e in errors), errors)

    def test_engagement_bait_warning(self):
        _, warnings = self.validate(caption="Big news! Share if you agree.")
        self.assertTrue(any("share if" in w for w in warnings), warnings)

    def test_bad_filename(self):
        errors, _ = self.validate(name="Moon Ocean.md")
        self.assertTrue(any("filename" in e for e in errors), errors)

    def test_blocked_domains_match_hosts(self):
        text = VALID_ITEM.format(fact_check="pending", caption=CAPTION)
        meta = text.replace("https://www.bbc.com/news/science-123", "https://m.facebook.com/page/posts/1")
        errors, _ = self.validate(text=meta)
        self.assertTrue(any("facebook.com" in e for e in errors), errors)
        lookalike = text.replace("https://www.bbc.com/news/science-123", "https://notfacebook.com.example.org/x")
        self.assertEqual(self.validate(text=lookalike)[0], [])

    def test_enums_and_booleans(self):
        text = VALID_ITEM.format(fact_check="pending", caption=CAPTION)
        text = text.replace("item_type: news", "item_type: rumour").replace("needs_ai_label: false", "needs_ai_label: maybe")
        errors, _ = self.validate(text=text)
        self.assertTrue(any(e.startswith("item_type must be one of") for e in errors), errors)
        self.assertTrue(any(e.startswith("image.needs_ai_label") for e in errors), errors)

    def test_channel_must_match_folder(self):
        text = VALID_ITEM.format(fact_check="pending", caption=CAPTION).replace("channel: demo", "channel: other")
        errors, _ = self.validate(text=text)
        self.assertTrue(any("does not match folder" in e for e in errors), errors)


class SchemaLimitTests(ToolTestCase):
    """The limits a non-Facebook tool would declare: chars, hashtags, word targets, required image."""
    manifest = copy.deepcopy(FB_MANIFEST)
    manifest["sections"][0].update(max_chars=60, min_words=5)
    manifest["sections"][1]["max_hashtags"] = 2
    manifest["rules"]["image"] = "required"
    manifest["rules"]["banned_phrases"] = ["Link in bio"]

    def test_limits(self):
        long_caption = "word " * 20
        text = VALID_ITEM.format(fact_check="pending", caption=long_caption)
        text = text.replace("#ScienceExplained", "#One #Two #Three").replace("kind: stock", "kind: none")
        errors, _ = self.validate(text=text)
        self.assertTrue(any("## Caption is" in e and "limit is 60" in e for e in errors), errors)
        self.assertTrue(any("3 hashtags" in e for e in errors), errors)
        self.assertTrue(any("needs an image" in e for e in errors), errors)

    def test_word_target_and_banned_phrase_warn(self):
        errors, warnings = self.validate(caption="Moon. Link in bio")
        self.assertEqual(errors, [])
        self.assertTrue(any("target is at least 5" in w for w in warnings), warnings)
        self.assertTrue(any("link in bio" in w for w in warnings), warnings)


class LifecycleTests(ToolTestCase):
    def move(self, *args, **kwargs):
        return quiet(lifecycle.move, self.tool, *args, **kwargs)

    def test_finalize_requires_approval_and_pass(self):
        path = self.write_item(fact_check="passed")
        with self.assertRaises(SystemExit):
            self.move("finalize", str(path))
        other = self.write_item(name="2026-10-01-other.md")
        with self.assertRaises(SystemExit):
            self.move("finalize", str(other), approved=True)
        self.move("finalize", str(path), approved=True)
        self.assertTrue((self.channel / "finalized" / path.name).is_file())
        self.assertFalse(path.exists())

    def test_full_lifecycle(self):
        path = self.write_item(fact_check="passed")
        self.move("finalize", path.name, approved=True)
        self.move("reopen", path.name)
        fm, _ = read_item(self.channel / "drafts" / path.name)
        self.assertEqual(fm["fact_check"], "pending")
        with self.assertRaises(SystemExit):  # a reopened item must pass the fact-check again
            self.move("finalize", path.name, approved=True)
        self.write_item(fact_check="passed")
        self.move("finalize", path.name, approved=True)
        self.move("publish", path.name, when="2026-10-03")
        published = self.channel / "published" / path.name
        fm, _ = read_item(published)
        self.assertEqual(fm["published"], "2026-10-03")
        self.assertEqual(validate_item(self.tool, published)[0], [])

    def test_publish_rejects_bad_dates(self):
        self.write_item(status="finalized", fact_check="passed")
        for bad in ("2026-13-01", "2026-09-01", "2999-01-01"):  # invalid; before created; future
            with self.assertRaises(SystemExit):
                self.move("publish", "2026-10-01-moon-ocean.md", when=bad)

    def test_refuses_wrong_folder(self):
        path = self.write_item(status="published", fact_check="passed")
        with self.assertRaises(SystemExit):
            self.move("finalize", str(path), approved=True)


class InsightsTests(ToolTestCase):
    def test_summary_matches_published_files(self):
        path = self.write_item(status="published", fact_check="passed")
        path.write_text(set_field(path.read_text(encoding="utf-8"), "published", "2026-10-01"), encoding="utf-8")
        rows = insights.read_rows(self.tool, FIXTURES / "meta_export.csv", {}, insights.load_published(self.tool, "demo"))
        self.assertEqual(len(rows), 3)  # description row skipped
        moon = rows[0]
        self.assertEqual(moon["file"], path.name)
        self.assertEqual(moon["groups"], {"pillar": "Space", "item_type": "news"})
        self.assertEqual(moon["reach"], 1200)
        self.assertEqual(moon["engagement"], 96)
        self.assertAlmostEqual(moon["rate"], 0.08)
        self.assertIsNone(rows[1]["file"])
        self.assertEqual(rows[1]["groups"], {"pillar": "(unmatched)", "item_type": "Photos"})
        report = insights.summarize(self.tool, "demo", FIXTURES / "meta_export.csv", rows)
        self.assertIn("| Space ⚠ small sample | 1 |", report)
        self.assertIn("## By post type", report)
        self.assertIn("Unmatched posts (2)", report)

    def test_missing_columns_explains(self):
        with self.assertRaises(SystemExit) as ctx:
            insights.detect_columns(["foo", "bar"], {})
        self.assertIn("CSV headers", str(ctx.exception))

    def test_manifest_columns_are_tried(self):
        cols = insights.detect_columns(["When", "Text", "People reached"], {},
                                       {"publish_time": ["When"], "caption": ["Text"], "reach": ["People reached"]})
        self.assertEqual(cols, {"publish_time": "When", "caption": "Text", "reach": "People reached"})


class RssTests(unittest.TestCase):
    def test_rss_and_atom(self):
        feed = b"""<rss><channel><item><title>A</title><link>https://a.example/1</link>
            <pubDate>Wed, 01 Oct 2026 10:00:00 GMT</pubDate><description>&lt;p&gt;Hi &amp;amp; bye&lt;/p&gt;</description>
            </item></channel></rss>"""
        items = rss.parse(feed)
        self.assertEqual(items[0]["title"], "A")
        self.assertEqual(items[0]["date"].year, 2026)
        self.assertEqual(items[0]["summary"], "Hi & bye")
        atom = b"""<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>B</title>
            <link href="https://b.example/2"/><updated>2026-10-02T08:00:00Z</updated></entry></feed>"""
        items = rss.parse(atom)
        self.assertEqual(items[0]["link"], "https://b.example/2")
        self.assertEqual(items[0]["date"].day, 2)

    def test_feeds_from_test_channel(self):
        feeds = rss.feeds_from_sources(Tool.load(FACEBOOK), "_test")
        self.assertTrue(feeds)
        self.assertTrue(all(url.startswith("https://") for _, url in feeds))


class ScaffoldTests(ToolTestCase):
    def test_new_channel(self):
        dest = scaffold.new_channel(self.tool, "lanka-garden", "Lanka Garden")
        profile = (dest / "profile.md").read_text(encoding="utf-8")
        self.assertIn("channel: lanka-garden", profile)
        self.assertIn("# Lanka Garden", profile)
        self.assertNotIn("{{", profile)
        for folder in common.CHANNEL_FOLDERS:
            self.assertTrue((dest / folder / ".gitkeep").is_file(), folder)
        with self.assertRaises(SystemExit):
            scaffold.new_channel(self.tool, "lanka-garden", "Again")
        with self.assertRaises(SystemExit):
            scaffold.new_channel(self.tool, "Bad Slug", "Bad")

    def test_new_tool_from_template(self):
        with mock.patch.object(scaffold, "TOOLS_DIR", self.tmp):
            dest = scaffold.new_tool("blog")
            with self.assertRaises(SystemExit):
                scaffold.new_tool("blog")
        manifest = json.loads((dest / "tool.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["name"], "blog")
        self.assertEqual(check_manifest(manifest), [], "the template manifest must be structurally valid")
        problems = factory.check_tool(dest)
        self.assertTrue(any("TODO" in p for p in problems), problems)
        self.assertTrue(any("fixture" in p for p in problems), problems)
        texts = [p.read_text(encoding="utf-8") for p in dest.rglob("*") if p.is_file()]
        self.assertFalse(any("{{tool}}" in t or "{{created}}" in t for t in texts))


class ExportTests(ToolTestCase):
    def test_txt_joins_export_sections(self):
        text = export.export_item(self.tool, self.write_item(), "txt")
        self.assertEqual(text, CAPTION + "\n\n#ScienceExplained")

    def test_markdown_to_html(self):
        md = "## Title\n\nSome **bold** & *soft* text\nnext line\n\n- one\n- [two](https://x.org/a)\n\n> quoted"
        out = export.markdown_to_html(md)
        self.assertIn("<h2>Title</h2>", out)
        self.assertIn("<p>Some <strong>bold</strong> &amp; <em>soft</em> text<br>\nnext line</p>", out)
        self.assertIn('<ul><li>one</li><li><a href="https://x.org/a">two</a></li></ul>', out)
        self.assertIn("<blockquote><p>quoted</p></blockquote>", out)


class CliTests(ToolTestCase):
    def test_check_command_exit_codes(self):
        good = self.write_item()
        with self.assertRaises(SystemExit) as ctx:
            quiet(cli.main, self.tool_dir, ["check", str(good)])
        self.assertEqual(ctx.exception.code, 0)
        bad = self.write_item(name="2026-10-01-bad.md", status="finalized")
        with self.assertRaises(SystemExit) as ctx:
            quiet(cli.main, self.tool_dir, ["check", "--channel", "demo"])
        self.assertEqual(ctx.exception.code, 1)
        self.assertTrue(bad.exists())

    def test_info_uses_tool_nouns(self):
        out = io.StringIO()
        with redirect_stdout(out):
            cli.main(self.tool_dir, ["info"])
        self.assertIn("item: post (posts); channel: page (pages)", out.getvalue())


class EveryToolTests(unittest.TestCase):
    """One check per tool in tools/: manifest, required files, and _test fixtures."""

    def test_tools_are_ready(self):
        dirs = factory.tool_dirs()
        self.assertIn(FACEBOOK, dirs)
        for tool_dir in dirs:
            with self.subTest(tool=tool_dir.name):
                self.assertEqual(factory.check_tool(tool_dir), [])

    def test_no_claude_md_in_tools(self):
        """A CLAUDE.md in tools/ itself would load in every tool session."""
        self.assertFalse((common.TOOLS_DIR / "CLAUDE.md").exists())

    def test_studio_is_consistent(self):
        """Root files, command frontmatter, unique command names, proxy agents and .mcp.json."""
        self.assertEqual(factory.check_studio(), [])


class StudioTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)

    def write(self, rel, text):
        path = self.tmp / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def test_check_skill(self):
        good = self.write("good/SKILL.md", "---\nname: good\ndescription: Does a thing.\n"
                                           "argument-hint: <x>\n---\n\nArgs: $ARGUMENTS\n")
        self.assertEqual(factory.check_skill(good), [])
        bad = self.write("bad/SKILL.md", "---\nname: other\n---\n\nArgs: $ARGUMENTS\nTODO fill\n")
        problems = " | ".join(factory.check_skill(bad))
        for expected in ("match its folder", "description", "argument-hint", "TODO"):
            self.assertIn(expected, problems)
        self.assertEqual(factory.check_skill(self.write("raw/SKILL.md", "no frontmatter")),
                         ["does not start with a --- frontmatter block"])

    def test_command_template_fails_until_filled(self):
        text = common.COMMAND_TEMPLATE.read_text(encoding="utf-8").replace("{{name}}", "demo")
        self.assertIn("still contains TODO", factory.check_skill(self.write("demo/SKILL.md", text)))

    def test_new_command(self):
        roots = {"root": self.tmp / "root", "studio": self.tmp / "studio", "shared": self.tmp / "shared"}
        self.write("shared/research/SKILL.md", "---\nname: research\n---\n")
        with mock.patch.object(factory, "skill_roots", return_value=roots):
            dest = factory.new_command("plan-week", "shared")
            self.assertIn("name: plan-week", dest.read_text(encoding="utf-8"))
            for name, where in (("research", "root"), ("plan-week", "root"), ("Bad Name", "root"), ("x", "nowhere")):
                with self.subTest(name=name, where=where), self.assertRaises(SystemExit):
                    factory.new_command(name, where)

    def test_proxy_agents_must_match(self):
        agents = self.tmp / "agents"
        self.write("agents/writer.md", "---\nname: writer\ntools: Read, Write\n---\n")
        self.write("agents/scout.md", "---\nname: scout\ntools: Read\n---\n")
        problems = " | ".join(factory.proxy_problems(agents))
        self.assertIn("writer.md must have name 'writer' and tools: Read, Write", problems)
        self.assertIn("no root proxy .claude/agents/scout.md", problems)
        self.assertEqual(factory.proxy_problems(self.tmp / "missing"), [])


class McpTests(unittest.TestCase):
    def test_config_problems(self):
        servers = {
            "drive": {"type": "http", "url": "https://mcp.example.com/mcp",
                      "headers": {"Authorization": "Bearer ${DRIVE_TOKEN}", "Accept": "application/json"}},
            "local": {"command": "npx", "args": ["-y", "some-server"], "env": {"API_KEY": "${API_KEY:-}"}},
        }
        self.assertEqual(mcp.check_servers(servers), [])
        bad = {
            "leaky": {"type": "http", "url": "https://mcp.example.com", "headers": {"Authorization": "Bearer abc123"}},
            "meta": {"type": "sse", "url": "https://graph.facebook.com/mcp"},
            "nocmd": {"type": "stdio"},
            "bad name": {"type": "ftp"},
        }
        problems = " | ".join(mcp.check_servers(bad))
        for expected in ("headers.Authorization looks secret", "Meta properties", "needs a command",
                         "name must be", "type must be"):
            self.assertIn(expected, problems)

    def test_load_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / ".mcp.json"
            self.assertEqual(mcp.load_config(path), ({}, []))
            path.write_text("{not json", encoding="utf-8")
            self.assertIn("invalid JSON", mcp.load_config(path)[1][0])
            path.write_text('{"servers": {}}', encoding="utf-8")
            self.assertIn("mcpServers", mcp.load_config(path)[1][0])

    def test_target_hides_secrets(self):
        self.assertEqual(mcp.target({"type": "http", "url": "https://x.example.com/mcp?key=secret"}),
                         "https://x.example.com/mcp")
        self.assertEqual(mcp.target({"command": "npx", "args": ["-y", "pkg"], "env": {"TOKEN": "x"}}), "npx -y pkg")

    def test_tool_servers(self):
        manifest = dict(FB_MANIFEST, mcp=["drive", "claude_ai_Gmail", "nowhere"])
        self.assertEqual(check_manifest(manifest), [])
        self.assertTrue(check_manifest(dict(FB_MANIFEST, mcp="drive")))
        self.assertTrue(check_manifest(dict(FB_MANIFEST, mcp=["bad name"])))
        tool = Tool(FACEBOOK, manifest)
        servers = {"drive": {"command": "x"}}
        self.assertEqual(mcp.status("drive", servers), "configured in .mcp.json")
        self.assertIn("claude.ai connector", mcp.status("claude_ai_Gmail", servers))
        problems = mcp.tool_problems(tool, servers)
        self.assertEqual(len(problems), 1)
        self.assertIn("'nowhere'", problems[0])


if __name__ == "__main__":
    unittest.main()
