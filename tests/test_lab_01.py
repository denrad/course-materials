from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "materials" / "lab-01" / "index.html"
INDEX = ROOT / "index.html"
QR = ROOT / "assets" / "qr-lab-01.svg"


class LabOnePublicationTests(unittest.TestCase):
    def test_assignment_page_states_student_facing_requirements(self):
        content = PAGE.read_text(encoding="utf-8")

        self.assertIn("<h1 id=\"page-title\">Лабораторная работа № 1", content)
        self.assertIn("каталогом книг", content)
        self.assertIn("ТОП-10 авторов", content)
        self.assertIn("SMS-уведомление", content)
        self.assertIn("Вопросы заказчику", content)
        self.assertIn("Проверяемые сценарии", content)
        self.assertNotIn("фреймворк", content.lower())
        self.assertNotIn("база данных", content.lower())

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
