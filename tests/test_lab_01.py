from pathlib import Path
import os
import unittest


ROOT = Path(__file__).resolve().parents[1]
SITE = Path(os.environ.get("JEKYLL_DESTINATION", ROOT / "_site"))
BUILT_PAGE = SITE / "materials" / "lab-01" / "index.html"
INDEX = SITE / "index.html"
QR = SITE / "assets" / "qr-lab-01.svg"


class LabOnePublicationTests(unittest.TestCase):
    def test_assignment_page_states_student_facing_requirements(self):
        content = BUILT_PAGE.read_text(encoding="utf-8")

        self.assertRegex(content, r"<h1[^>]*>Лабораторная работа №\s?1")
        self.assertIn("каталогом книг", content)
        self.assertIn("ТОП-10 авторов", content)
        self.assertIn("SMS-уведомление", content)
        self.assertIn("Вопросы заказчику", content)
        self.assertIn("Проверяемые сценарии", content)
        for implementation_choice in ("Laravel", "Symfony", "Django", "PostgreSQL", "MySQL", "SQLite"):
            with self.subTest(implementation_choice=implementation_choice):
                self.assertNotIn(implementation_choice.lower(), content.lower())

    def test_catalogue_links_to_assignment(self):
        self.assertIn('href="materials/lab-01/"', INDEX.read_text(encoding="utf-8"))

    def test_qr_asset_encodes_canonical_assignment_url(self):
        content = QR.read_text(encoding="utf-8")

        self.assertIn("<svg", content)
        self.assertIn(
            "https://course.denrad.dev/materials/lab-01/",
            content,
        )


if __name__ == "__main__":
    unittest.main()
