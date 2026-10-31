from pathlib import Path
from html import unescape
import os
import re
import unittest
from html.parser import HTMLParser
from urllib.parse import urlsplit
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[1]
SITE = Path(os.environ.get("JEKYLL_DESTINATION", ROOT / "_site"))
MATERIAL_IDS = [
    "lecture-01", "lecture-02", "agentic-development", "lecture-04", "lecture-05", "lecture-06",
    "lecture-07", "lecture-08", "lecture-09", "lecture-10", "testing", "lab-01",
    "lab-02", "lab-03", "lab-04", "lab-05", "lab-06", "lab-07",
    "lab-10",
]
ROUTE_IDS = [*MATERIAL_IDS, "lab-17"]
FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSdgdPOyAVhxgs54HWq-LN-gbz8miZepvuuwGyuDiCX-cMN_Cg/viewform"


class MaterialLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.material_ids = []
        self.form_links = []
        self.card_links = []

    def handle_starttag(self, tag, attrs):
        if tag != "a":
            return
        href = dict(attrs).get("href", "")
        if "card" in dict(attrs).get("class", "").split():
            self.card_links.append(href)
        if href.startswith("materials/") and href.endswith("/"):
            self.material_ids.append(href.removeprefix("materials/").removesuffix("/"))
        if href == FORM_URL:
            self.form_links.append(href)


class LocalReferences(HTMLParser):
    def __init__(self):
        super().__init__()
        self.references = []

    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if key in ("href", "src") and value:
                self.references.append(value)


class RenderedText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)


def markdown_text_lines(body):
    lines = []
    in_code_fence = False
    for line in body.splitlines():
        line = line.strip()
        if line.startswith("```"):
            in_code_fence = not in_code_fence
            continue
        if in_code_fence or not line or re.fullmatch(r"[-*_]{3,}", line):
            continue
        line = re.sub(r"^#{1,6}\s+", "", line)
        line = re.sub(r"^>\s?", "", line)
        line = re.sub(r"^(?:[-*+]\s+|\d+[.)]\s+)", "", line)
        if re.fullmatch(r"[-*_]{3,}", line):
            continue
        if re.search(r"!\[[^\]]*\]\([^)]+\)", line):
            continue
        line = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", line)
        line = re.sub(r"<[^>]+>", "", line)
        line = re.sub(r"[*_`~|]", "", line)
        if re.fullmatch(r"[-:]{3,}", line):
            continue
        line = " ".join(unescape(line).split())
        line = re.sub(r"\s+([,.;:!?])", r"\1", line)
        if line:
            lines.append(line)
    return lines


class SiteBuildTests(unittest.TestCase):
    def test_images_cannot_expand_material_pages_beyond_the_viewport(self):
        stylesheet = (ROOT / "assets/styles.css").read_text(encoding="utf-8")
        self.assertRegex(stylesheet, r"(?m)^img\s*\{[^}]*max-width:\s*100%")
        self.assertRegex(stylesheet, r"(?m)^img\s*\{[^}]*height:\s*auto")

    def test_build_contains_public_routes_and_assets(self):
        expected = (
            "index.html",
            "materials/lab-01/index.html",
            "materials/lecture-09/index.html",
            "CNAME",
            "assets/styles.css",
            "assets/qr-lab-01.svg",
            *(f"materials/{material_id}/index.html" for material_id in ROUTE_IDS),
        )
        missing = [path for path in expected if not (SITE / path).is_file()]
        self.assertEqual([], missing, f"Missing from Jekyll output: {missing}")

    def test_catalogue_keeps_all_materials_in_the_existing_order(self):
        parser = MaterialLinks()
        parser.feed((SITE / "index.html").read_text(encoding="utf-8"))
        self.assertEqual(MATERIAL_IDS, parser.material_ids)
        self.assertEqual([FORM_URL], parser.form_links)
        self.assertNotIn(FORM_URL, parser.card_links)

    def test_project_information_precedes_the_course_hero_and_links_both_forms(self):
        rendered = (SITE / "index.html").read_text(encoding="utf-8")
        project = rendered.index('id="project"')
        hero = rendered.index('class="hero"')
        materials = rendered.index('id="materials"')
        self.assertLess(project, hero)
        self.assertLess(project, materials)
        self.assertIn(FORM_URL, rendered)
        self.assertIn("https://forms.yandex.ru/cloud/6ae1ced56d2d7354508d63ec/", rendered)

    def test_testing_material_is_labeled_as_lecture_11(self):
        source = (ROOT / "materials/testing/index.html").read_text(encoding="utf-8")
        rendered = (SITE / "materials/testing/index.html").read_text(encoding="utf-8")
        self.assertIn('kind: "lecture"', source)
        self.assertIn('card_label: "11"', source)
        self.assertIn("Открыть презентацию лекции 11 о тестировании", source)
        self.assertIn('<span class="lecture-number">Лекция 11</span>', rendered)
        self.assertIn("<title>Лекция 11. Тестирование:", rendered)

    def test_geojson_practicum_is_numbered_as_lab_8(self):
        source = (ROOT / "materials/lab-10/index.md").read_text(encoding="utf-8")
        rendered = (SITE / "materials/lab-10/index.html").read_text(encoding="utf-8")
        self.assertIn('card_label: "Лабораторная работа №8"', source)
        self.assertIn("Лабораторная работа № 8", rendered)
        self.assertNotIn("Лабораторная работа № 10", rendered)

    def test_homepage_lists_lab_8_and_says_lab_9_is_upcoming(self):
        rendered = (SITE / "index.html").read_text(encoding="utf-8")
        self.assertIn("Лабораторная работа № 8 посвящена выбору места для офиса по геоданным", rendered)
        self.assertIn("лабораторная работа № 9 готовится", rendered)

    def test_material_pages_have_card_metadata_and_preserve_html_body(self):
        required = ("id", "kind", "title", "description", "order")
        expected_order = {material_id: order for order, material_id in enumerate(MATERIAL_IDS, start=1)}
        expected_order["lab-17"] = len(MATERIAL_IDS) + 1
        for material_id in ROUTE_IDS:
            with self.subTest(material=material_id):
                source_directory = ROOT / "materials" / material_id
                source = source_directory / "index.html"
                if not source.is_file():
                    source = source_directory / "index.md"
                output = SITE / "materials" / material_id / "index.html"
                self.assertTrue(source.is_file(), f"Missing source material: {source}")
                text = source.read_text(encoding="utf-8")
                self.assertTrue(text.startswith("---\n"), f"Missing front matter: {source}")
                front_matter, body = text.split("---\n", 2)[1:]
                for key in required:
                    self.assertRegex(front_matter, rf"(?m)^{key}:\s*.+$")
                self.assertRegex(front_matter, rf'(?m)^id: "{material_id}"$')
                self.assertIn(f"order: {expected_order[material_id]}", front_matter)
                rendered = output.read_text(encoding="utf-8")
                if source.suffix == ".html":
                    self.assertEqual(body, rendered)
                else:
                    parser = RenderedText()
                    parser.feed(rendered)
                    rendered_text = " ".join(" ".join(parser.parts).split())
                    rendered_text = re.sub(r"\s+([,.;:!?])", r"\1", rendered_text)
                    expected_lines = markdown_text_lines(body)
                    self.assertTrue(expected_lines, f"Markdown body is empty: {source}")
                    for line in expected_lines:
                        with self.subTest(material=material_id, markdown_line=line):
                            self.assertIn(line, rendered_text)

    def test_material_assets_are_copied_to_the_site(self):
        for source in (ROOT / "materials").rglob("*"):
            if source.is_file() and "assets" in source.parts:
                output = SITE / source.relative_to(ROOT)
                with self.subTest(asset=source.relative_to(ROOT)):
                    self.assertTrue(output.is_file())

    def test_local_html_references_resolve_in_the_built_site(self):
        for page in SITE.rglob("*.html"):
            parser = LocalReferences()
            parser.feed(page.read_text(encoding="utf-8"))
            for reference in parser.references:
                parsed = urlsplit(reference)
                if parsed.scheme or parsed.netloc or not parsed.path or parsed.path.startswith("#"):
                    continue
                if parsed.path.startswith("/"):
                    target = SITE / parsed.path.lstrip("/")
                else:
                    target = page.parent / parsed.path
                if parsed.path.endswith("/"):
                    target = target / "index.html"
                with self.subTest(page=page.relative_to(SITE), reference=reference):
                    self.assertTrue(target.is_file(), f"Unresolved local reference: {reference}")

    def test_markdown_material_uses_the_shared_layout_and_permalink(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "source"
            destination = Path(temporary) / "site"
            (source / "_layouts").mkdir(parents=True)
            (source / "assets").mkdir()
            (source / "materials").mkdir()
            (source / "_config.yml").write_text("url: https://course.denrad.dev\n", encoding="utf-8")
            (source / "_layouts" / "material.html").write_bytes(
                (ROOT / "_layouts" / "material.html").read_bytes()
            )
            (source / "assets" / "styles.css").write_bytes(
                (ROOT / "assets" / "styles.css").read_bytes()
            )
            (source / "materials" / "fixture.md").write_text(
                "---\nlayout: material\nid: fixture\nkind: lab\n"
                "title: Fixture\ndescription: Build fixture\norder: 99\n"
                "permalink: /materials/fixture/\n---\n# Fixture body\n\n{% raw %}{{ name }}{% endraw %}\n",
                encoding="utf-8",
            )
            subprocess.run(
                ["bundle", "exec", "jekyll", "build", "--source", str(source), "--destination", str(destination)],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            output = destination / "materials" / "fixture" / "index.html"
            self.assertTrue(output.is_file())
            rendered = output.read_text(encoding="utf-8")
            self.assertIn("<title>Fixture · Материалы курса</title>", rendered)
            self.assertIn('<h1 id="fixture-body">Fixture body</h1>', rendered)
            self.assertIn("{{ name }}", rendered)
        self.assertIn('href="/assets/styles.css?v=20261028-1"', rendered)


if __name__ == "__main__":
    unittest.main()
